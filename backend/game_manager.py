import asyncio
import logging
import random

import shitler_core.core as sh
from backend.errors import *
from backend.models import *


class AsyncioEventManager(sh.EventManager):
    def __init__(self, game, lobby):
        super(AsyncioEventManager, self).__init__(game)
        self.lobby = lobby

    def send_event(self, event, player, wait_for_ack=False):
        player.user.send_game_event(event)

    def send_input_request(self, request):
        player = request.target
        player.user.send_input_request(request)
        player.last_event_manager = self


class Lobby:
    new_id = 78600

    def __init__(self, game_manager, name, options):
        self.name = name
        self.id = str(self.new_id)
        Lobby.new_id += 1
        self.options = options
        self.users = set()
        self.started = False
        self.running = False
        self.ended = False
        self.game = None
        self.game_manager = game_manager
        self.event_manager = None
        self.autostart_task = None

        game_manager.app.chatrooms.setdefault(self.id, ChatRoom(self.id))
        game_manager.app.broadcast("lobby_created", self)

    def user_join(self, user):
        if not self.started:
            if user not in self.users:
                self.users.add(user)
                user.join_lobby(self)
                self.try_autostart()
                self.notify_update()
                return self
        else:
            raise GameManagerError("Game already started")

    def user_leave(self, user):
        if not self.started:
            self.users.remove(user)
            self.notify_update()
        else:
            raise GameManagerError("Can't leave, the game has already started")

    def notify_update(self):
        self.game_manager.app.broadcast("lobby_changed", self)

    def try_autostart(self, delay=3):
        if len(self.users) == len(self.options.roles):
            if not self.autostart_task:
                logging.debug(f"Lobby {self.name} trying to autostart")
                self.autostart_task = asyncio.create_task(self._try_autostart(delay))
        else:
            if self.autostart_task:
                if not self.autostart_task.cancelled():
                    self.autostart_task.cancel()

    async def _try_autostart(self, delay):
        try:
            await asyncio.sleep(delay)
            if len(self.users) == len(self.options.roles):
                await self.start()
        except asyncio.CancelledError:
            self.autostart_task = None
            raise asyncio.CancelledError

    def start(self):
        self.game = sh.Game(self.name, self.options)
        self.event_manager = AsyncioEventManager(self.game, self)
        self.started = True
        self.running = True
        return asyncio.create_task(self.game.play(self.users, self.event_manager), name=f"Game-{self.name}")

    def to_dict(self, context_user=None):
        ret = {}
        for k in ("id", "name", "started", "running", "ended"):
            ret[k] = self.__getattribute__(k)
        ret["options"] = self.options.to_dict()
        ret["users"] = [u.uid for u in self.users]

        if self.game:
            ret["game"] = self.dictify_game(self.game)

        if context_user:
            ret["private"] = {}
            ret["private"]["joined"] = context_user in self.users
        return ret

    @staticmethod
    def dictify_game(game):
        return {}


class GameManager:
    def __init__(self, app):
        self._lobbies = {}
        self.app = app

    @property
    def lobbies(self):
        return list(self._lobbies.values())

    def get_lobby(self, name):
        game = self._lobbies.get(name)
        if not game:
            raise GameDoesntExist(f"Lobby with name {name} does not exist")
        return game

    def create_lobby(self, options):
        game_options = sh.GameOptions(options)
        lobby = Lobby(self, options.pop("name", f"lobby-n-{random.randrange(10000)}"), game_options)
        self._lobbies[lobby.id] = lobby

        return lobby

    def user_join(self, user, lobby):
        if not isinstance(lobby, Lobby):
            lobby = self.get_lobby(lobby)

        return lobby.user_join(user)
