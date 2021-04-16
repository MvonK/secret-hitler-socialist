import eventlet
import shitler_core.core as sh
import random
from backend.errors import *


class GameManager:
    def __init__(self):
        self.games = {}

    def get_game(self, name):
        game = self.games.get(name)
        if not game:
            raise GameDoesntExist
        return game

    def create_game(self, creator):
        new_game = sh.Game(f"Game({random.randrange(10000)})")
        self.games[new_game.name] = new_game
        self.player_join(creator, new_game.name)

    def player_join(self, player, game_name):
        game = self.get_game(game_name)
        pl = sh.Player(player)
        game.player_join(pl)

