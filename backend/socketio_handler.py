import asyncio
import string
import redis
import inspect
import aiohttp
from aiohttp import web
from backend.errors import *

import logging

log = logging.getLogger("namespaces")


def validate_username(username):
    valid_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + "_-"
    for s in username:
        if s not in valid_chars:
            return False
    return True


class UserContext:
    def __init__(self, user_manager, game_manager, get_lobby=False):
        self.sid = fl.request.sid
        uid = fl.session.get("uid")
        if uid is None:
            raise NotLoggedIn("You are not logged in")

        user = user_manager.get_user(uid)
        if user is None:
            del fl.session["uid"]
            raise UserDoesntExist("That user does not exist")

        self.rooms = set()

        self.user = user
        self.lobby = None
        if get_lobby:
            self.get_lobby(game_manager)

    def send(self, event_name, data):
        log.debug(f"Sending {event_name} to {self.user.name}")
        fsio.emit(event_name, data, room=self.user.name)

    def get_lobby(self, game_manager):
        lobby = game_manager.get_users_game(self.user)
        if lobby is None:
            raise UserNotInGame("You are not in any lobby")
        self.lobby = lobby

    def reconnect(self):
        self.sid = fl.request.sid
        for r in self.rooms:
            r.user_join(self)

    def disconnect(self):
        log.debug(f"User {self.user.uid} disconnecting")
        fsio.disconnect(self.sid, namespace="/")
        return bool(self.lobby)


class ChatRoom:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Chatroom({self.name})"

    def send(self, author="server", content="empty content"):
        log.debug(f"room {self.name} sending out message {author}: {content}")
        fsio.emit("chat_message_create", {"author":author, "content": content, "room": self.name}, room=self.name)

    def user_join(self, ctx):
        ctx.rooms.add(self)
        fsio.join_room(self.name, sid=ctx.sid)

    def user_leave(self, ctx):
        ctx.rooms.remove(self)
        fsio.leave_room(self.name, sid=ctx.sid)

    def close(self):
        fsio.close_room(self.name)


def event_wrap(get_context=True, get_context_lobby=False):
    def wrapgen(fn):
        def wrapper(*args, **kwargs):
            if get_context:
                try:
                    ctx = args[0].get_user_context(get_context_lobby)
                except (NotLoggedIn, UserDoesntExist):
                    ctx = None
                args = list(args)
                args.insert(1, ctx)
            try:
                return fn(*args, **kwargs)
            except UserNotInRoom as e:
                fsio.emit("chat_message_create", {"author": "server", "content": str(e), "room": "general"})
        return wrapper
    return wrapgen







class GameNamespace():
    def __init__(self, path, user_manager, game_manager, sio):
        super().__init__(path)
        self.user_manager = user_manager
        self.game_manager = game_manager
        self.sio = sio
        self.active_sessions = {}  # format is `SID: user context`
        self.resting_sessions = []  # list of user contexts
        self.chat_rooms = {"general": ChatRoom("general")}

    def get_user_context(self, get_lobby=False):
        if fl.request.sid in self.active_sessions:
            active_session = self.active_sessions[fl.request.sid]
            if not get_lobby or active_session.game is not None:
                return active_session
            else:
                active_session.get_lobby(self.game_manager)
        ctx = UserContext(self.user_manager, self.game_manager, get_lobby=get_lobby)
        self.active_sessions[fl.request.sid] = ctx
        return ctx

    def attempt_reconnect(self):
        if fl.session.get("uid"):
            for v in self.resting_sessions:
                if v.user.uid == fl.session["uid"]:
                    self.active_sessions[fl.request.sid] = v
                    self.resting_sessions.remove(v)
                    v.reconnect()
                    log.info(f"User {v.user.uid} has been reconnected!")
                    return True
        return False

    def on_error(self, error):
        log.error(f"Error happened: {error}")

    def disconnect_user(self, uid):
        for k, v in self.active_sessions.items():
            if v.user.uid == uid:
                self._disconnect(v)
                break

    def _disconnect(self, ctx):
        if not ctx:
            log.debug("Disconnecting from empty context?")
            return
        log.debug(f"SIO disconnecting user {ctx.user.uid}")
        del self.active_sessions[ctx.sid]
        if ctx.disconnect():
            log.debug("Putting that user to rest for future reconnects")
            self.resting_sessions.append(ctx)

    def on_connect(self):
        log.info(f"Client trying to connect {dict(fl.session)}")
        # session["uid"] = "uid-1000020"

        fsio.emit("chat_message_create", {"author": "server", "content": "Ur connected omggg yasss", "room": "general"})

        if not self.attempt_reconnect():
            try:
                ctx = self.get_user_context()
                self.chat_rooms["general"].user_join(ctx)
                self.on_fetch_login_info()

                for l in self.game_manager.lobbies.values():  # Send all lobby info
                    fsio.emit("lobby_create", {"lobby": l.to_dict()})

                log.debug(f"User {ctx.user.name} now connected successfully. Uid stored in session is {fl.session.get('uid')}")
            except (NotLoggedIn, UserDoesntExist):
                self.active_sessions.pop(fl.request.sid, None)
                raise ConnectionRefusedError("Not logged in")

    @event_wrap()
    def on_disconnect(self, ctx):
        self._disconnect(ctx)

    @event_wrap()
    def on_chat_message_send(self, ctx, message):
        log.debug(f"Message received: {message}")

        room_name = message.get("room", "default")
        target_room = self.chat_rooms.get(room_name)
        if target_room not in ctx.rooms:
            log.debug(f"User is in rooms '{self.rooms(ctx.sid)}' and tried to send to {room_name}")
            raise UserNotInRoom(f"You are not in the room {room_name} so you can't send messages there")

        target_room.send(author=ctx.user.name, content=message["content"])

    @event_wrap()
    def on_fetch_login_info(self, ctx):
        log.debug(f"User {ctx.user.name} fetching login info")
        fsio.emit("login_info", {"user": ctx.user.to_dict(include_password=False)})

    @event_wrap()
    def on_create_lobby(self, ctx, options={}):
        lobby = self.game_manager.create_lobby(options)
        self.game_manager.user_join(ctx, lobby.id)
        self.chat_rooms[lobby.id] = ChatRoom(lobby.id)
        fsio.emit("lobby_create", {"lobby": lobby.to_dict()}, broadcast=True)

    @event_wrap()
    def on_join_lobby(self, ctx, info={}):
        log.debug(f"User {ctx.user.name} joining the lobby {info.get('lobby_id')}")
        self.game_manager.user_join(ctx, info.get("lobby_id"))

    @event_wrap()
    def on_join_chatroom(self, ctx, data={}):
        name = data.get("name", "general")
        log.debug(f"{ctx.user.name} wants to join the room {name}")
        room = self.chat_rooms.get(name)
        if room is not None:
            room.user_join(ctx)
        else:
            log.error(f"Chatroom {name} doesnt exist")

    @event_wrap()
    def on_leave_chatroom(self, ctx, data={}):
        name = data.get("name", "general")
        room = self.chat_rooms.get(name)
        room.user_leave(ctx)
