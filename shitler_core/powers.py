import random

from .events import *
from .models import *


async def investigate(game):
    inved = await game.request_input(InputRequest(InputType.PLAYER, game.president, "who you gonna investigate owo", exclude=game.president))
    game.send_event(PartyRevealed(inved, inved.alignment, False), game.president)


async def shoot(game):
    victim = await game.request_input(InputRequest(InputType.PLAYER, game.president, "Who you gonna shoot???", exclude=()))

    if victim.alignment.role == "Hitler":
        pass
        # TODO: End game

    game.broadcast_event(PlayerShot(victim))


async def allow_veto(game):
    game.log.info("VETO allowed")
    game.veto = True


async def hitler_zone_start(game):
    game.hitler_zone = True


async def special_election(game):
    game.log.info("Special election")
    lastpres = game.presindex

    special_pres = await game.request_input(InputRequest(InputType.PLAYER, game.president, "Pick a special election president"))
    game.presindex = game.players.index(special_pres)
    game.shuffle()
    if await game.elect_government(advance_president=False):
        await game.policy_playing()
    game.presindex = lastpres


async def recruitment(game):
    game.log.info("Socialist recruiting...")

    socs = game.socialists
    recrooter = random.choice(socs)

    recruited = await game.request_input(InputRequest(InputType.PLAYER, recrooter, "Recruit someone!", exclude=socs))
    recruited.alignment.party = Team.SOC

    for s in game.socialists:
        game.send_event(PartyRevealed(recruited, recruited.alignment, False), s)


async def five_year_plan(game):
    game.log.info("Five year plan")
    game.draw_deck += [Team.SOC, Team.SOC, Team.LIB]
    random.shuffle(game.draw_deck)
    game.broadcast_deck_size()


async def censorship(game):
    game.log.info("Censorship")
    game.chairman_allowed = False
    game.chairman = None


async def bugging(game):
    game.log.info("Socialist bugging...")
    raise NotImplemented


async def congress(game):
    game.log.info("Congress")
    for s in game.socialists:
        for revealed in game.socialists:
            game.send_event(PartyRevealed(revealed, revealed.alignment, False), s)


async def confession(game):
    target = await game.request_input(InputRequest(InputType.PLAYER, game.president, "Who do you confess your identity to", exclude=[game.president]))
    game.send_event(PartyRevealed(game.president, game.president.alignment, True), target)
