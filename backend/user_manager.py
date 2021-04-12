import redis
import json
import logging

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

    def __setattr__(self, key, value):
        self[key] = value
        self.user._update()

    def _from_data(self, data):
        for f in self.fields:
            self.__setattr__(f, data.pop(f, 0))
        for unknown_key in data:
            log.warning(f"Unknown stats key `{unknown_key}` with value `{data[unknown_key]}`. Ignored.")


stats_template = {
    "lib_wins": 0,
    "lib_games": 0,
    "fas_wins": 0,
    "fas_games": 0,
    "soc_wins": 0,
    "soc_games": 0,
    "hitler_wins": 0,
    "hitler_games": 0,

    "times_recruited": 0,
    "times_shot": 0,

    ""
}

class User:
    all_props = ("uid", "name", "password", "elo", "stats",)
    _static_props = ("uid",)

    def __init__(self, manager, data=None, **kwargs):
        if data is None:
            data = {}
        data.update(kwargs)
        self._manager = manager
        self._from_data(data)

    def _update(self):
        self._manager._update_user_date(self._uid, self)

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

    def edit(self, **kwargs):
        """
        Edits the user data and saves them
        :param kwargs: You can change parameters specified in `User.all_props`.
        :return:
        """
        for p in self._static_props:
            kwargs.pop(p)
        self.from_data(kwargs)
        self._update()

    def _from_data(self, data):
        for p in self.all_props:
            self.__setattr__(f"_{p}", data.get(p, self.__dict__.get(p)))

        if isinstance(self._stats, dict):
            self._stats = StatsDict(self, **self._stats)


    def to_dict(self):
        return {k: self.__getattribute__(k) for k in self.all_props}


class UserManager:
    def __init__(self, redis_pool):
        self.redis = redis.Redis(connection_pool=redis_pool)
        self.user_cache = {}

    def _get_user_data(self, uid):
        return self.redis.get(f"user-{uid}")

    def _set_user_data(self, uid, json_data):
        self.redis.set(uid, json_data)

    def get_user(self, uid):
        """
        Returns the User object. Returns None if the user does not exist.
        :param uid: UID of the user
        :return: Optional[:class:`User`]
        """
        if uid in self.user_cache:
            return self.user_cache[uid]

        data = json.loads(self._get_user_data(uid))
        user = User(self, data)
        self.user_cache[uid] = user
        return user

    def create_user(self, name, password):
        """
        Creates a new user and saves it into db.
        :param name: Name of the user
        :param password: User's password
        :return: User created
        """
        unique_id = self.redis.incr("unique_id")
        user = User(manager=self,
                    name=name,
                    password=password,
                    uid=unique_id,
                    elo=1500,
                    stats={}
                    )
        self.user_cache[unique_id] = user
        self._update_user_data(unique_id, user)
        return user

    def _update_user_data(self, uid, user):
        data = json.dumps(user.to_dict())
        self._set_user_data(uid, data)
