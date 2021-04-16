import flask_socketio as fsio
from flask import request, session
import string
import redis
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
    def __init__(self, user_manager, game_manager, get_game=False):
        self.sid = request.sid
        uid = session.get("uid")
        if uid is None:
            raise NotLoggedIn("You are not logged in")

        user = user_manager.get_user(uid)
        if user is None:
            del session["uid"]
            raise UserDoesntExist("That user does not exist")

        self.rooms = set()

        self.user = user
        self.game = None
        if get_game:
            self.get_game(game_manager)

    def get_game(self, game_manager):
        game = game_manager.get_users_game(self.user)
        if game is None:
            raise UserNotInGame("You are not in any game")
        self.game = game

    def reconnect(self):
        self.sid = request.sid
        for r in self.rooms:
            r.user_join(self)


class ChatRoom:
    def __init__(self, name):
        self.name = name

    def send(self, author="server", content="empty content"):
        log.debug(f"room {self.name} sending out message {author}: {content}")
        fsio.emit("chatMessageCreate", {"author":author, "content": content, "room": self.name}, room=self.name)

    def user_join(self, ctx):
        ctx.rooms.add(self)
        fsio.join_room(self.name, sid=ctx.sid)

    def user_leave(self, ctx):
        ctx.rooms.remove(self)
        fsio.leave_room(self.name, sid=ctx.sid)

    def close(self):
        fsio.close_room(self.name)


def error_wrap():
    def wrapgen(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except UserNotInRoom as e:
                fsio.emit("chatMessageCreate", {"author": "server", "content": str(e), "room": "general"})
        return wrapper
    return wrapgen


class GameNamespace(fsio.Namespace):
    def __init__(self, path, user_manager, game_manager):
        super().__init__(path)
        self.user_manager = user_manager
        self.game_manager = game_manager
        self.active_sessions = {}
        self.chat_rooms = {"general": ChatRoom("general")}

    def get_user_context(self, get_game=False):
        if request.sid in self.active_sessions:
            active_session = self.active_sessions[request.sid]
            if not get_game or active_session.game is not None:
                return active_session
            else:
                active_session.get_game(self.game_manager)
        ctx = UserContext(self.user_manager, self.game_manager, get_game=get_game)
        self.active_sessions[request.sid] = ctx
        return ctx

    def attempt_reconnect(self):
        if session.get("uid"):
            for k, v in self.active_sessions.items():
                if v.user.uid == session["uid"]:
                    self.active_sessions[request.sid] = v
                    del self.active_sessions[k]
                    v.reconnect()
                    log.info(f"User {v.user.uid} has been reconnected!")
                    return True

        return False

    def on_connect(self):
        log.info("Client trying to connect omg")
        session["uid"] = "uid-1000020"

        fsio.emit("chatMessageCreate", {"author": "server", "content": "Ur trying to connect omggg"})
        if not self.attempt_reconnect():
            try:
                ctx = self.get_user_context()
                self.chat_rooms["general"].user_join(ctx)
            except (NotLoggedIn, UserDoesntExist):
                raise ConnectionRefusedError("Not logged in")

    @error_wrap()
    def on_chatMessageSend(self, message):
        log.debug(f"Message received: {message}")
        ctx = self.get_user_context()

        room_name = message.get("room", "default")
        target_room = self.chat_rooms.get(room_name)
        if target_room not in ctx.rooms:
            log.debug(f"User is in rooms '{self.rooms(ctx.sid)}' and tried to send to {room_name}")
            raise UserNotInRoom(f"You are not in the room {room_name} so you can't send messages there")

        target_room.send(author=ctx.user.name, content=message["content"])

