import shitler_core.core as sh
import random
from backend.errors import *


class AsyncioEventManager(sh.EventManager):
    def __init__(self, game, lobby):
        super(AsyncioEventManager, self).__init__(game)
        self.lobby = lobby

    def send_event(self, event, player, wait_for_ack=False):
        data = event.to_dict()
        name = "EVENT_" + data.pop("name")
        data["lobby_id"] = self.lobby.id
        player.send(name, data, nowait=True)

    def send_input_request(self, request):
        player = request.target
        player.send("INPUT_REQUEST", {"type": request.type, "id": request.id, "description": request.description}, nowait=True)
        player.last_event_manager = self


class Lobby:
    new_id = 78600

    def __init__(self, name, options):
        self.name = name
        self.id = str(self.new_id)
        Lobby.new_id += 1
        self.options = options
        self.users = set()
        self.started = False
        self.running = False
        self.ended = False
        self.game = None
        self.event_manager = None

    async def user_join(self, user):
        if not self.started:
            if user not in self.users:
                self.users.add(user)
                await user.send("joined_game", {"lobby": self.to_dict()})
        else:
            raise GameManagerError("Game already started")


    def user_leave(self, user):
        if not self.started:
            self.users.remove(user)

    def start(self):
        self.game = sh.Game(self.name, self.options)
        self.event_manager = WebEventManager(self.game, self)
        self.game.play(self.users)

    def to_dict(self):
        ret = {}
        for k in ("id", "name", "started", "running", "ended"):
            ret[k] = self.__getattribute__(k)
        ret["options"] = self.options.to_dict()
        return ret


class GameManager:
    def __init__(self):
        self.lobbies = {}

    def get_lobby(self, name):
        game = self.lobbies.get(name)
        if not game:
            raise GameDoesntExist(f"Game with name {name} is not registered")
        return game

    def create_lobby(self, options):
        lobby = Lobby(options.pop("name", f"lobby-n-{random.randrange(10000)}"), sh.GameOptions(options))
        self.lobbies[lobby.id] = lobby
        return lobby

    async def user_join(self, user, lobby):
        if not isinstance(lobby, Lobby):
            lobby = self.get_lobby(lobby)
        await lobby.user_join(user)

