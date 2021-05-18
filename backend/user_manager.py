import json
import logging
import hashlib
import datetime

"""
User should not be instantiated directly, you should use UserManager instead. Ideally, there will only be one instance
of UserManager, to prevent conflicts. 
"""

log = logging.getLogger("user-manager")


class StatsDict(dict):
    fields = (
        "lib_wins",
        "lib_games",
        "fas_wins",
        "fas_games",
        "soc_wins",
        "soc_games",
        "hitler_wins",
        "hitler_games",

        "times_recruited",
        "times_shot"
    )

    def __init__(self, user, **kwargs):
        super().__init__()
        self.user = user
        self._from_data(kwargs)
        self.auto_update = True

    def __setattr__(self, key, value):
        if key in self.fields:
            self[key] = value
            if self.auto_update:
                self.user._update()
        else:
            super().__setattr__(key, value)

    def _from_data(self, data):
        self.auto_update = False
        for f in self.fields:
            self.__setattr__(f, data.pop(f, 0))
        for unknown_key in data:
            log.warning(f"Unknown stats key `{unknown_key}` with value `{data[unknown_key]}`. Ignored.")
        self.auto_update = True
        self.user._update()


class User:
    all_props = ("uid", "name", "password", "elo", "stats",)
    _static_props = ("uid",)

    def __init__(self, manager, data=None, **kwargs):
        if data is None:
            data = {}
        data.update(kwargs)
        self._manager = manager
        self.update_on = False
        self._from_data(data)
        self.update_on = True

    def _update(self):
        if self.update_on:
            log.debug("Updating user")
            self._manager._update_user_data(self._uid, self)
        else:
            log.log(5, "User update blocked")

    @property
    def name(self):
        return self._name

    @property
    def password(self):
        return self._password

    @property
    def elo(self):
        return self._elo

    @property
    def stats(self):
        return self._stats

    @property
    def uid(self):
        return self._uid

    def edit(self, **kwargs):
        """
        Edits the user data and saves them
        :param kwargs: You can change parameters specified in `User.all_props`.
        :return:
        """
        for p in self._static_props:
            kwargs.pop(p)
        self._from_data(kwargs)
        self._update()

    def _from_data(self, data):
        for p in self.all_props:
            self.__setattr__(f"_{p}", data.get(p, self.__dict__.get(p)))

        if isinstance(self._stats, dict):
            self._stats = StatsDict(self, **self._stats)

        self._update()

    def to_dict(self, include_password=True):
        d = {k: self.__getattribute__(k) for k in self.all_props}
        if not include_password:
            d.pop("password")
        d["stats"] = dict(d["stats"])
        return d


class UserManager:
    def __init__(self, redis_pool):
        self.redis = redis_pool
        self.user_cache = {}

    @staticmethod
    def _get_key_from_name(name):
        return f"nick-{name}"

    def _get_user_data(self, uid):
        log.debug(f"Retrieving user {uid} from db")
        return self.redis.execute("get", f"{uid}")

    def _set_user_data(self, uid, json_data):
        log.debug(f"Setting user {uid} with data: {json_data}")
        return self.redis.execute("set", uid, json_data)

    def _update_user_nick(self, user):
        # self.redis.delete(self._get_key_from_name(user.name))
        return self.redis.execute("set", self._get_key_from_name(user.name), user.uid)

    async def get_uid(self, username):
        uid = await self.redis.execute("get", self._get_key_from_name(username))
        if uid:
            return uid.decode()
        return None

    async def get_user(self, uid):
        """
        Returns the User object. Returns None if the user does not exist.
        :param uid: UID of the user
        :return: Optional[:class:`User`]
        """
        if uid in self.user_cache:
            return self.user_cache[uid]

        raw_data = await self._get_user_data(uid)
        if raw_data is None:
            return None
        data = json.loads(raw_data.decode())
        user = User(self, data)
        self.user_cache[uid] = user
        return user

    async def create_user(self, name, password):
        """
        Creates a new user and saves it into db.
        :param name: Name of the user
        :param password: User's password
        :return: User created
        """
        unique_id = (await self.redis.execute("incr", "incremental_id")) * 7 + 999999
        #hsh = hashlib.md5(f"{unique_id}-{datetime.datetime.now()}")
        uid = f"uid-{unique_id}"
        user = User(manager=self,
                    name=name,
                    password=password,
                    uid=uid,
                    elo=1500,
                    stats={}
                    )
        self.user_cache[uid] = user
        await self._update_user_data(uid, user)
        await self._update_user_nick(user)
        return user

    def _update_user_data(self, uid, user: User):
        data = json.dumps(user.to_dict())
        return self._set_user_data(uid, data)

