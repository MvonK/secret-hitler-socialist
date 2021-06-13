import traceback

from .events import *
from .models import *
import shitler_core.powers as powers
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
        # self.options.setup_roles(len(self.players))
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
        self.log.info("Players created, informing clients")

        # Distribute roles
        for p in self.players:
            if p.alignment.party is Team.FAS and p.alignment.role != "Hitler":
                for f in self.fascists:
                    self.send_event(PartyRevealed(f, f.alignment, True), p)
                #self.send_event(PartyRevealed(self.hitler, p.alignment, True), p)
            elif p.alignment.role == "Hitler":
                self.send_event(PartyRevealed(self.hitler, p.alignment, True), p)
            else:
                self.send_event(PartyRevealed(p, p.alignment, True), p)

    async def play(self, users, event_manager):
        self.event_manager = event_manager
        try:
            await self._play(users)
        except Exception:
            self.log.error(f"Game error! {traceback.format_exc()}")

    async def _play(self, users):
        # setup
        # self.players = list_of_players
        self.init_from_options(users)
        self.log.debug("Init from options completed successfully")

        end = None

        self.running = True

        # actual game
        self.log.info("Starting the actual game")
        self.broadcast_event(GameStart())

        while end == None:
            self.shuffle()
            if await self.elect_government():
                await self.policy_playing()
        return end

    def end(self, winning_team, reason):
        self.running = False
        self.ended = True
        self.broadcast_event(GameEnd(winning_team, reason))

    def broadcast_event(self, event):
        self.event_manager.broadcast_event(event, self.players)

    def send_event(self, event, user, wait_for_ack=False):
        return self.event_manager.send_event(event, user, wait_for_ack)

    def request_input(self, request: InputRequest):
        self.log.debug(f"Input request sent to {request.target.name}, asking for {request.type}")
        return self.event_manager.input(request)

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

    async def add_fail(self, chancellor=None):
        if chancellor is None:
            chancellor = self.chancellor
        self.failed_governments += 1
        self.log.info("One more failed government")
        self.broadcast_event(GovernmentRejected(self.president, chancellor, self.failed_governments))
        if self.failed_governments == 3:
            self.log.info("Topdeck")
            topdecked = self.draw_deck.pop(0)
            self.broadcast_event(TopDeck())
            self.broadcast_deck_size()
            await self.chosen_policy(self.draw_deck[0])

    def shuffle(self):
        if len(self.draw_deck) < 3:
            self.log.info("Shuffling deck")
            self.draw_deck += self.discard_deck
            random.shuffle(self.draw_deck)
            self.discard_deck = []

    async def elect_government(self, advance_president=True):
        previous_president = self.president
        if advance_president:
            self.presindex = (self.presindex + 1) % len(self.players)
        while True:
            chosen_chancellor = await self.request_input(InputRequest(InputType.PLAYER, self.president, "Pick your chancellor", exclude=(self.president, previous_president, self.chancellor)))

            if chosen_chancellor != self.president and chosen_chancellor != self.chancellor:
                break
            self.log.warning("Invalid chancellor chosen")

        self.broadcast_event(GovernmentProposed(president=self.president, chancellor=chosen_chancellor))
        reqs = []
        for p in self.players:
            reqs.append(
                self.request_input(InputRequest(InputType.VOTE, p, "Vote for government")))

        self.log.info("Gathering votes...")
        votes = [await r for r in reqs]

        jas = votes.count(True)
        neins = votes.count(False)

        if jas >= neins:
            self.chancellor = chosen_chancellor
            if self.chairman_allowed:
                self.chairman = await self.request_input(
                    InputRequest(InputType.PLAYER, self.chancellor, "Pick your chairman"))
            else:
                self.chairman = None
            self.broadcast_event(GovernmentAccepted(self.president, self.chancellor, self.chairman))
            self.log.info("Government passed")
            if self.chancellor.alignment.role == "Hitler" and self.hitler_zone:
                # TODO: Hitler won victory ending idk
                return
            self.failed_governments = 0
            return True

        else:
            await self.add_fail(chosen_chancellor)
        return False

    async def chosen_policy(self, policy):
        self.board[policy] += 1
        track = self.board_format[policy]
        self.broadcast_event(PolicyPlayed(policy))

        self.log.info(f"{policy} was elected")
        if len(track) == self.board[policy]:
            return

        for action in track[self.board[policy] - 1]:
            if action is not None:
                log.info(f"Executing action {action}")
                action_callback = getattr(powers, action)
                await action_callback(self)

    async def policy_playing(self):
        hand = [self.draw_deck.pop(0) for i in range(3)]
        self.broadcast_deck_size()
        if self.chairman_allowed:
            seen = random.choice(hand)
            self.log.info(f"Chairman saw {seen} policy")
            self.send_event(CardPeeked(seen), self.chairman)

        discarded = await self.request_input(
            InputRequest(InputType.PICK_POLICY, self.president, "Discard a policy", choices=hand))
        hand.remove(discarded)
        self.discard_deck.append(discarded)

        if self.veto:
            chancellor_veto = await self.request_input(
                InputRequest(InputType.VOTE, self.chancellor, "Do you want to initiate a VETO?"))
            if chancellor_veto:
                self.broadcast_event(ChancellorVetoProposed())
                pres_veto = await self.request_input(
                    InputRequest(InputType.VOTE, self.president, "Do you want to accept the VETO?"))
                if pres_veto:
                    self.broadcast_event(VetoPassed())
                    await self.add_fail(self.chancellor)
                    return
                else:
                    self.broadcast_event(VetoRejected())

        discarded = await self.request_input(
            InputRequest(InputType.PICK_POLICY, self.chancellor, "Discard a policy", choices=hand))
        hand.remove(discarded)
        self.discard_deck.append(discarded)

        self.broadcast_deck_size()
        return await self.chosen_policy(hand.pop(0))


if __name__ == "__main__":
    logscope = logging.INFO
    logging.basicConfig(level=logscope)
