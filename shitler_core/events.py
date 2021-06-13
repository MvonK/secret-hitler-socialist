import logging
from collections import Iterable
from enum import Enum
import asyncio
from dataclasses import dataclass, asdict, field, Field
from .models import *
from backend.utils import dictify

class InputType(Enum):
    PLAYER = "player"
    VOTE = "vote"
    PICK_POLICY = "policy"

    to_dict = str

    def __str__(self):
        return self.value


class InputRequest:
    def __init__(self, type: InputType, target, description="Empty description", choices=(), exclude=()):
        self.type = type
        self.description = description
        self.target = target
        self.sent = False
        self.exclude = exclude

        if not isinstance(exclude, Iterable):
            self.exclude = (exclude,)

        self.choices = [c for c in choices if c not in exclude]

    def send(self, manager, id):
        if self.sent:
            raise ValueError

        if len(self.choices) == 0:
            if self.type is InputType.PLAYER:
                self.choices = [p for p in manager.game.players if p not in self.exclude]
            elif self.type is InputType.VOTE:
                self.choices = [True, False]

        self._event_manager = manager
        self.id = id
        self._future = asyncio.get_event_loop().create_future()
        self.sent = True

        manager.send_input_request(self)
        return self._future

    def set_data(self, data):
        if self.type is InputType.PLAYER:
            for p in self.choices:
                if data == p.uid:
                    self.data = p
        elif self.type is InputType.VOTE:
            self.data = bool(data)
        elif self.type is InputType.PICK_POLICY:
            try:
                self.data = Team.from_string(data)
            except ValueError:
                return False
        else:
            return False

        self._future.set_result(self.data)
        return True

    def to_dict(self):
        to_ret = {"id": self.id, "description": self.description}
        to_ret["choices"] = dictify(self.choices)
        to_ret["type"] = str(self.type)
        return to_ret


class EventManager:
    event_id = 0

    def __init__(self, game):
        self.game = game
        self.events = {}
        self.received_events = {}

    def send_event(self, event, player, wait_for_ack=False):
        raise NotImplemented

    def send_input_request(self, request):
        raise NotImplemented

    def receive_input_response(self, id, data):
        req = self.events[id]
        if req.set_data(data):
            del self.events[id]
            self.received_events[id] = req
        else:
            raise ValueError("Invalid input!")

    def broadcast_event(self, event, users):
        for u in users:
            self.send_event(event, u)

    def input(self, input_request):
        self.event_id += 1
        my_id = self.event_id
        self.events[my_id] = input_request
        future = input_request.send(self, my_id)

        return future


'''class EventType(Enum):  # What events will server send to clients
    GAME_START = 0
    GAME_END = 1

    GOVERNMENT_ACCEPTED = 23
    GOVERNMENT_REJECTED = 24
    PRESIDENT_DISCARDING_POLICY = 25
    CHANCELLOR_DISCARDING_POLICY = 26
    POLICY_PLAYED = 27
    TOP_DECK = 28
    POWER_ACTIVATED = 29  # This event should be accompanied with relevant POWER information
    POWER_EXECUTED = 30  # Should contain power and any parameters chosen, like player to be shot

    PRESIDENT_CLAIM = 70
    CHANCELLOR_CLAIM = 71
    PRESIDENT_MAKE_CLAIM = 72
    CHANCELLOR_MAKE_CLAIM = 73'''


def event_name_from_class(classname):
    letters = list(classname)
    ret = [letters[0].upper()]
    for l in letters[1:]:
        if l.isupper():
            ret.append("_")
        ret.append(l)
    return "".join(ret).upper()


@dataclass()
class Event:
    def to_dict(self):
        to_ret = {"name": self.name}
        for f in self.__dataclass_fields__.keys():
            attr = self.__getattribute__(f)
            if isinstance(attr, Player):
                to_ret[f] = attr.user.uid
            elif isinstance(attr, Team):
                to_ret[f] = str(attr)
            elif isinstance(attr, PartyAlignment):
                to_ret[f] = attr.party if attr.role != "Hitler" else "Hitler"
            else:
                to_ret[f] = attr
        return to_ret

    def __post_init__(self):
        self.name = event_name_from_class(self.__class__.__name__)


@dataclass()
class GameStart(Event):
    pass


@dataclass()
class GameEnd(Event):
    winning_team: Team
    reason: str


@dataclass()
class GovernmentProposed(Event):
    president: Player
    chancellor: Player


@dataclass()
class GovernmentAccepted(Event):
    president: Player
    chancellor: Player
    chairman: Player or None


@dataclass()
class GovernmentRejected(Event):
    president: Player
    chancellor: Player
    attempts: int


@dataclass()
class PresidentDiscardingPolicy(Event):
    pass


@dataclass()
class ChancellorDiscardingPolicy(Event):
    pass


@dataclass()
class PolicyPlayed(Event):
    policy: Team


@dataclass()
class TopDeck(Event):
    pass


@dataclass()
class PowerActivated(Event):
    power: str


@dataclass()
class PresidentClaim(Event):
    policy1: Team
    policy2: Team
    discarded_policy: Team


@dataclass()
class ChancellorClaim(Event):
    discarded_policy: Team
    played_policy: Team


@dataclass()
class ChairmanClaim(Event):
    seen: Team


@dataclass()
class CardPeeked(Event):
    policy: Team


@dataclass()
class ChancellorVetoProposed(Event):
    pass


@dataclass()
class VetoPassed(Event):
    pass


@dataclass()
class VetoRejected(Event):
    pass


@dataclass()
class PartyRevealed(Event):
    player: Player
    party: PartyAlignment
    reveal_role: bool

    def to_dict(self):
        return {"name": self.name,
                "player": self.player,
                "party": "Hitler" if self.party.role == "Hitler" and self.reveal_role else self.party.party}


@dataclass()
class PlayerShot(Event):
    player: Player


@dataclass()
class DeckCountUpdate(Event):
    draw_deck_size: int
    discard_deck_size: int


if __name__ == "__main__":
    a = VetoRejected()
    print(a.to_dict())
