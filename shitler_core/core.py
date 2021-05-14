from .events import *
from .models import *
import random

log = logging.getLogger("gamelog")


class Game:
    def __init__(self, name, options: GameOptions):
        self.name = name
        self.log = logging.getLogger("game." + name)
        self.started = False
        self.running = False
        self.ended = False
        self.players = []
        self.options = options
        self.event_manager = None

        self.veto = False
        self.hitler_zone = False

        self.draw_deck = []
        self.discard_deck = []
        self.failed_governments = 0
        self.presindex = 0

        self.chairman_allowed = True
        self.chancellor = None
        self.chairman = None

    def init_from_options(self, users):
        self.options.setup_roles(len(self.players))
        self.chairman_allowed = self.options.chairman_allowed
        self.board = self.options.board
        self.board_format = self.options.board_format

        for key in self.options.deck_contents:
            self.draw_deck += ([key for _ in range(self.options.deck_contents[key])])
        random.shuffle(self.draw_deck)

        # The following section assigns roles, but this shitty, should be rewritten
        users = list(users)
        random.shuffle(users)
        self.log.info("Assigning roles")
        for u in users:
            role = random.choice(self.options.roles)
            self.options.roles.remove(role)
            alignment = PartyAlignment(role, "regular")
            if role == "Hitler":
                alignment = PartyAlignment(Team.FAS, "Hitler")

            self.players.append(Player(u, self, alignment))

        random.shuffle(self.players)

        # Distribute roles
        for p in self.players:
            if p.alignment.party is Team.FAS and p.alignment.role != "Hitler":
                for f in self.fascists:
                    self.send_event(PartyRevealed(f, Team.FAS), p)
            else:
                self.send_event(PartyRevealed(p, p.alignment.party), p)
            if p.alignment.party is Team.FAS:
                self.send_event(PartyRevealed(self.hitler, "Hitler"), p)

    def play(self, users):
        # setup
        # self.players = list_of_players
        self.init_from_options(users)

        end = None

        self.running = True

        # actual game
        self.log.info("Starting the actual game")
        self.broadcast_event(GameStart())

        for p in self.players:
            self.send_event(PartyRevealed(p, p.alignment.party), p)

        while end == None:
            self.shuffle()
            if self.elect_government():
                self.policy_playing()
        return end

    def broadcast_event(self, event):
        self.event_manager.broadcast_event(event, self.players)

    def send_event(self, event, user, wait_for_ack=False):
        return self.event_manager.send_event(event, user, wait_for_ack)

    def request_input(self, request, wait_for_result=True):
        return self.event_manager.input(request, wait_for_result)

    @property
    def president(self):
        return self.players[self.presindex]

    @property
    def socialists(self):
        return [p for p in self.players if p.alignment.party is Team.SOC]

    @property
    def liberals(self):
        return [p for p in self.players if p.alignment.party is Team.LIB]

    @property
    def fascists(self):
        return [p for p in self.players if p.alignment.party is Team.FAS]

    @property
    def hitler(self):
        return [p for p in self.players if p.alignment.role == "Hitler"][0]

    def broadcast_deck_size(self):
        self.broadcast_event(DeckCountUpdate(len(self.draw_deck), len(self.discard_deck)))

    def add_fail(self, chancellor=None):
        if chancellor is None:
            chancellor = self.chancellor
        self.failed_governments += 1
        self.log.info("One more failed government")
        self.broadcast_event(GovernmentRejected(self.president, chancellor, self.failed_governments))
        if self.failed_governments:
            self.log.info("Topdeck")
            topdecked = self.draw_deck.pop(0)
            self.broadcast_event(TopDeck())
            self.broadcast_deck_size()
            self.chosen_policy(self.draw_deck[0])

    def shuffle(self):
        if len(self.draw_deck) < 3:
            self.log.info("Shuffling deck")
            self.draw_deck += self.discard_deck
            random.shuffle(self.draw_deck)
            self.discard_deck = []

    def elect_government(self, advance_president=True):
        if advance_president:
            self.presindex = (self.presindex + 1) % len(self.players)
        while True:
            chosen_chancellor = self.request_input(
                InputRequest(InputType.PLAYER, self.president, "Pick your chancellor"))
            if chosen_chancellor != self.president and chosen_chancellor != self.chancellor:
                break
            self.log.warning("Invalid chancellor chosen")

        self.broadcast_event(GovernmentProposed(president=self.president, chancellor=chosen_chancellor))
        reqs = []
        for p in self.players:
            reqs.append(
                self.request_input(InputRequest(InputType.VOTE, p, "Vote for government"), wait_for_result=False))

        self.log.info("Gathering votes...")
        votes = [r.wait() for r in reqs]

        jas = votes.count(True)
        neins = votes.count(False)

        if jas >= neins:
            self.chancellor = chosen_chancellor
            if self.chairman_allowed:
                self.chairman = self.request_input(
                    InputRequest(InputType.PLAYER, self.chancellor, "Pick your chairman"))
            else:
                self.chairman = None
            self.broadcast_event(GovernmentAccepted(self.president, self.chancellor, self.chairman))
            self.log.info("Government passed")
            if self.chancellor.alignment.role == "Hitler" and self.hitler_can_overtake:
                # TODO: Hitler won victory ending idk
                return
            self.failed_governments = 0
            return True

        else:
            self.add_fail(chosen_chancellor)
        return False

    def chosen_policy(self, policy):
        self.board[policy] += 1
        track = self.board_format[policy]
        self.broadcast_event(PolicyPlayed(policy))

        self.log.info(policy + " was elected")
        if len(track) == self.board[policy]:
            self.end = policy + " victory by laws!"
            return

        for action in track[self.board[policy] - 1]:
            log.info(f"Executing action {action.__name__}")
            action()

    def policy_playing(self):
        hand = [self.draw_deck.pop(0) for i in range(3)]
        self.broadcast_deck_size()
        hand.sort()
        if self.chairman_allowed:
            seen = random.choice(hand)
            self.log.info("Chairman saw " + seen + " policy")
            self.send_event(CardPeeked(seen), self.chairman)

        discarded = self.request_input(
            InputRequest(InputType.PICK_POLICY, self.president, "Discard a policy", choices=hand))
        hand.remove(discarded)
        self.discard_deck.append(discarded)

        if self.veto:
            chancellor_veto = self.request_input(
                InputRequest(InputType.VOTE, self.chancellor, "Do you want to initiate a VETO?"))
            if chancellor_veto:
                self.broadcast_event(ChancellorVetoProposed())
                pres_veto = self.request_input(
                    InputRequest(InputType.VOTE, self.president, "Do you want to accept the VETO?"))
                if pres_veto:
                    self.broadcast_event(VetoPassed())
                    self.add_fail(self.chancellor)
                    return
                else:
                    self.broadcast_event(VetoRejected())

        discarded = self.request_input(
            InputRequest(InputType.PICK_POLICY, self.chancellor, "Discard a policy", choices=hand))
        hand.remove(discarded)
        self.discard_deck.append(discarded)

        self.broadcast_deck_size()
        return self.chosen_policy(hand.pop(0))


if __name__ == "__main__":
    logscope = logging.INFO
    logging.basicConfig(level=logscope)
