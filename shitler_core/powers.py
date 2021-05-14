import random

from .events import *
from .models import *


def investigate(game):
    inved = game.request_input(InputRequest(InputType.PLAYER, game.president, "who you gonna investigate owo"))
    game.send_event(PartyRevealed(inved, inved.alignment.party))


def shoot(game):
    victim = game.request_input(InputRequest(InputType.PLAYER, game.president, "Who you gonna shoot???", exclude=()))

    if victim.alignment.role == "Hitler":
        pass
        # TODO: End game

    game.broadcast_event(PlayerShot(victim))


def allow_veto(game):
    game.log.info("VETO allowed")
    game.veto = True


def allow_hitler_overtake(game):
    game.hitler_can_overtake = True


def special_election(game):
    game.log.info("Special election")
    lastpres = game.president

    special_pres = game.request_input(InputRequest(InputType.PLAYER, lastpres, "Pick a special election president"))
    game.president = special_pres
    game.shuffle()
    if game.elect_government(advance_president=False):
        game.policy_playing()
    game.president = lastpres


def recruitment(game):
    game.log.info("Socialist recruiting...")

    socs = game.socialists
    recrooter = random.choice(socs)

    recruited = game.request_input(InputRequest(InputType.PLAYER, recrooter, "Recruit someone!", exclude=socs))
    recruited.alignment.party = Team.SOC

    game.send_event(PartyRevealed(recruited, Team.SOC))


def five_year_plan(game):
    game.log.info("Five year plan")
    game.draw_deck += [Team.SOC, Team.SOC, Team.LIB]
    random.shuffle(game.draw_deck)
    game.broadcast_deck_size()


def censorship(game):
    game.log.info("Censorship")
    game.chairman_allowed = False
    game.chairman = None


def bugging(game):
    game.log.info("Socialist bugging...")
    raise NotImplemented

    msg = game.public_channel.send("Socialist is bugging someone. Wait for him...")
    socs = []
    for p in game.players:
        if p.party == "Socialist":
            socs.append(p)

    bugger = random.choice(socs)
    bugged = bugger.input(bugger.playerparse, True,
                          "Hey, socialist. You are chosen to bug one of other players. Type number of player with dollar before.")
    game.log.info(bugger.name + " bugged " + bugged.name)
    seen_party = bugged.party
    if seen_party == "Hitler":
        seen_party = "Fascist"
    for s in socs:
        s.send(bugger.name + " bugged " + bugged.name + ". He is " + seen_party)


def congress(game):
    game.log.info("Congress")
    for s in game.socialists:
        game.send_event(PartyRevealed(s, Team.SOC), s)


def confession(game):
    target = game.request_input(InputRequest(InputType.PLAYER, game.president, "Who do you confess your identity to", exclude=[game.president]))
    revealed = "Hitler" if target.alignment.role == "Hitler" else target.alignment.party
    game.send_event(PartyRevealed(game.president, revealed), target)
