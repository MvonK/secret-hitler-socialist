import logging
from enum import Enum


class Player:
    def __init__(self, user, game, alignment):
        self.user = user
        self.parent_game = game
        self.log = logging.getLogger("game." + game.name + "." + self.name)
        self.alignment = alignment


class Power:
    def __init__(self, name, game, callback):
        self.name = name
        self.game = game
        self.callback = callback

    def invoke(self):
        self.callback()


class Team(Enum):
    LIB = "Liberal"
    FAS = "Fascist"
    SOC = "Socialist"

    @staticmethod
    def from_string(val):
        if val == "Liberal":
            target = Team.LIB
        elif val == "Fascist":
            target = Team.FAS
        elif val == "Socialist":
            target = Team.SOC
        else:
            raise ValueError
        return target

    def __str__(self):
        return self.value


class PartyAlignment:
    def __init__(self, party: Team, role):
        self.party = party
        self.role = role


class GameOptions:
    def __init__(self, data):  # string balance
        self.log = logging.getLogger("optionslog")
        self.mode = data.pop("mode", "n")  # "s" is for socialist, anything else for regular
        self.from_balance(0, mode=self.mode)

        self.chairman_allowed = data.pop("chairman", self.chairman_allowed)

        for team, n in data.pop("deck_contents", {}).items():
            target = Team.from_string(team)
            self.deck_contents[target] = n

        for team, powers in data.pop("board_format", {}).items():
            target = Team.from_string(team)
            for p in range(powers):
                if powers[p] is not None:
                    assert isinstance(powers[p], list)
                    self.board_format[target][p] = powers[p]

        for team, n in data.pop("starting_policies", {}).items():
            target = Team.from_string(team)
            self.board[target] = n

        if len(data) > 0:
            self.log.warning(f"Unrecognized parameters for initializing GameOptions: {' '.join(data.keys())}")
        self.roles = None

    def from_balance(self, table_size, mode=None):
        # Balance has two parts, mode and number of players
        if not mode:
            mode = self.mode

        if mode == 's':
            self.roles = None
            self.parties_playing = ["Liberal", "Fascist", "Socialist"]
            self.chairman_allowed = True
            self.deck_contents = {
                Team.LIB: 5,
                Team.FAS: 10,
                Team.SOC: 8
            }
            self.board_format = {
                Team.LIB: [[], [], [], []],
                Team.FAS: [[], ["investigate"], ["special_election", "hitler_zone_start"], ["shoot"],
                            ["shoot", "start_veto_zone"]],
                Team.SOC: [[], ["recruitment"], ["fiveyearplan", "censorship"], ["congress"]]
            }
            self.board = {
                Team.LIB: 0,
                Team.FAS: 0,
                Team.SOC: 0
            }
            self.setup_roles(table_size)
        else:
            self.roles = None
            self.chairman_allowed = False
            self.parties_playing = ["Liberal", "Fascist"]
            self.deck_contents = {
                Team.LIB: 6,
                Team.FAS: 11,
            }
            self.board_format = {  # at the end is always party victory
                Team.LIB: [[None], [None], [None], [None]],
                Team.FAS: [[None], ["investigate"], ["special_election", "hitler_zone_start"], ["shoot"],
                            ["shoot", "start_veto_zone"]],
            }
            self.board = {
                Team.LIB: 0,
                Team.FAS: 0,
            }
            self.setup_roles(table_size)

        self.log.info("Setupped settings by balance code " + mode)
        return True

    def setup_roles(self, table_size):
        if table_size == 0:
            return
        mode = self.mode
        if len(self.roles) == table_size:
            return
        if mode == "s":
            self.roles = ["Hitler"] + [Team.FAS] * ((table_size - 2) // 3) + [Team.SOC] * (
                        (table_size - 1) // 4) + [Team.LIB] * (table_size // 2)
            if table_size == 7:
                self.roles.append(Team.LIB)
        else:
            self.roles = ["Hitler"] + [Team.FAS] * ((table_size - 3) // 2) + [Team.LIB] * (table_size // 2 + 1)

    def to_dict(self):
        ret = {}
        for k in ("mode", "roles", "parties_playing", "deck_contents", "board_format", "board"):
            val = self.__getattribute__(k)
            if isinstance(val, dict):
                for dict_k in list(val.keys()):
                    if isinstance(dict_k, Team):
                        val[str(dict_k)] = val[dict_k]
                        del val[dict_k]
            ret[k] = val
        return ret