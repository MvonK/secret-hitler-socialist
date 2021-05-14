import logging
from collections import Iterable
from enum import Enum

import eventlet


class InputType(Enum):
    PLAYER = "player"
    VOTE = "vote"
    PICK_POLICY = "policy"

    def __str__(self):
        return self.value


class InputRequest:
    def __init__(self, type: InputType, target, description="Empty description", choices=(), exclude=()):
        self.type = type
        self.description = description
        self.target = target
        self.sent = False

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
        self.sent = True

    def set_data(self, data):  # TODO: Some data validation and parsing
        self.data = data
        return True


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
        req.set_data(data)
        del self.events[id]
        self.received_events[id] = req

    def broadcast_event(self, event, users):
        for u in users:
            self.send_event(event, u)

    def input(self, input_request, wait_for_result=True):
        self.event_id += 1
        my_id = self.event_id
        self.events[my_id] = input_request
        input_request.send(self, my_id)
        thread = self.wait_for_input(my_id)
        if wait_for_result:
            return thread.wait().data
        else:
            return thread

    def wait_for_input(self, id):
        return eventlet.spawn(self._wait_for_input, id)

    def _wait_for_input(self, id):
        while True:
            if id in self.received_events:
                return self.received_events.pop(id)
            eventlet.sleep(0.2)


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


class Event:
    name = "EMPTY_EVENT"
    fields = ["name"]

    def __init__(self, *args, **kwargs):
        args = list(args)
        self.data = {}
        if "name" not in self.fields:
            self.fields.append("name")
        kwargs["name"] = kwargs.get("name", False) or event_name_from_class(self.__class__.__name__)

        for field in self.fields:
            try:
                self.data[field] = kwargs.pop(field)
            except KeyError:
                if len(args) > 0:
                    self.data[field] = args.pop(0)
                else:
                    raise TypeError(f"Event missing required field {field}")

        if len(args) > 0:
            logging.warning(f"Event args had unrecognized parameter with values {args}")
        if len(kwargs) > 0:
            logging.warning(f"Event kwargs had unrecognized parameters: {kwargs}")

    def __dir__(self):
        return self.fields

    def to_dict(self):
        return self.data


class GameStart(Event):
    pass


class GameEnd(Event):
    fields = ["reason"]


class RoleUpdate(Event):
    fields = ["changes"]


class GovernmentProposed(Event):
    fields = ["president", "chancellor"]


class GovernmentAccepted(Event):
    fields = ["president", "chancellor", "chairman"]


class GovernmentRejected(Event):
    fields = ["president", "chancellor", "attempts"]


class PresidentDiscardingPolicy(Event):
    pass


class ChancellorDiscardingPolicy(Event):
    pass


class PolicyPlayed(Event):
    fields = ["policy"]


class TopDeck(Event):
    pass


class PowerActivated(Event):
    fields = ["power"]


class PowerExecuted(Event):
    fields = ["power", "power_params"]


class PresidentClaim(Event):
    fields = ["lib", "fas", "soc", "discarded"]


class ChancellorClaim(Event):
    fields = ["lib", "fas", "soc", "discarded"]


class ChairmanClaim(Event):
    fields = ["seen"]


class CardPeeked(Event):
    fields = ["card"]


class ChancellorVetoProposed(Event):
    pass


class VetoPassed(Event):
    pass


class VetoRejected(Event):
    pass


class PartyRevealed(Event):
    fields = ["player", "party"]


class PlayerShot(Event):
    fields = ["player"]


class DeckCountUpdate(Event):
    fields = ["draw_size", "discard_size"]
