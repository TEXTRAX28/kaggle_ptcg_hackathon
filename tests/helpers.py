"""Small visible-observation fixtures shared by pilot and runtime tests."""
from pokemon_agent.sdk import read_deck


def card(cid, serial, owner=0):
    return {"id": cid, "serial": serial, "playerIndex": owner}


def pokemon(cid, serial, hp, energies=0, owner=0):
    return dict(card(cid, serial, owner), hp=hp, maxHp=hp, appearThisTurn=False,
                energies=[3] * energies, energyCards=[card(3, serial * 100 + i, owner) for i in range(energies)],
                tools=[], preEvolution=[])


def observation(options, context=0, minimum=1, maximum=1):
    def player(owner):
        return {"active": [pokemon(723, 10 + owner, 350, 3, owner)], "bench": [], "benchMax": 5,
                "deckCount": 30, "discard": [], "prize": [None] * 6,
                "handCount": 1, "hand": [card(3, 50)] if owner == 0 else None,
                "poisoned": False, "burned": False, "asleep": False, "paralyzed": False, "confused": False}
    return {"select": {"type": 0, "context": context, "minCount": minimum, "maxCount": maximum,
                       "remainDamageCounter": 0, "remainEnergyCost": 0, "option": options,
                       "deck": None, "contextCard": None, "effect": None},
            "logs": [], "search_begin_input": "DO NOT READ HIDDEN NATIVE STATE",
            "current": {"turn": 5, "turnActionCount": 0, "yourIndex": 0, "firstPlayer": 0,
                        "supporterPlayed": False, "stadiumPlayed": False, "energyAttached": False,
                        "retreated": False, "result": -1, "stadium": [], "looking": None,
                        "players": [player(0), player(1)]}}


def config():
    return {"game": 1, "agent_seat": 0, "agent": "abomasnow", "opponent": "random",
            "agent_deck": read_deck(), "opponent_deck": read_deck(), "first_player": 1,
            "policy_seed": 123, "max_decisions": 5000, "decision_timeout": 1}
