"""Shared legal-choice dispatch, visible-card lookup and typed Energy checks."""
from collections import Counter

from .sdk import load_sdk, metadata, validate_selection


class BaseAgent:
    """Common mechanics; each deck supplies its own scoring and effect choices."""

    def __init__(self, deck):
        self.deck = list(deck)
        self.cards, self.attacks = metadata()
        api, _ = load_sdk()
        self.O, self.C, self.A = api.OptionType, api.SelectContext, api.AreaType

    def __call__(self, obs):
        if obs.get("select") is None:
            return list(self.deck)
        select = obs["select"]
        if not select["option"]:
            action = []
        elif select["context"] == self.C.MAIN:
            action = [max(range(len(select["option"])),
                          key=lambda i: self.main_score(obs, select["option"][i]))]
        else:
            action = self.select_effect(obs)
        validate_selection(obs, action)
        return action

    @staticmethod
    def players(obs):
        state = obs["current"]
        return state["players"][state["yourIndex"]], state["players"][1 - state["yourIndex"]]

    @staticmethod
    def field(player):
        return [p for p in player["active"] + player["bench"] if p is not None]

    def resolve(self, obs, option):
        """Resolve only cards exposed in this observation; facedown stays None."""
        state = obs["current"]
        player = state["players"][option.get("playerIndex", state["yourIndex"])]
        area = option.get("area", self.A.HAND if option["type"] == self.O.PLAY else None)
        index = option.get("index")
        areas = {self.A.HAND: player["hand"], self.A.DISCARD: player["discard"],
                 self.A.ACTIVE: player["active"], self.A.BENCH: player["bench"],
                 self.A.PRIZE: player["prize"], self.A.DECK: obs["select"].get("deck"),
                 self.A.LOOKING: state.get("looking"), self.A.STADIUM: state["stadium"]}
        values = areas.get(area)
        if values is None or index is None or not 0 <= index < len(values):
            return None
        card = values[index]
        if card and option["type"] in (self.O.ENERGY_CARD, self.O.ENERGY):
            return card["energyCards"][option["energyIndex"]]
        if card and option["type"] == self.O.TOOL_CARD:
            return card["tools"][option["toolIndex"]]
        return card

    def target(self, obs, option):
        me, _ = self.players(obs)
        area = option.get("inPlayArea")
        group = me["active"] if area == self.A.ACTIVE else me["bench"]
        index = option.get("inPlayIndex")
        return group[index] if index is not None and index < len(group) else None

    def can_pay(self, pokemon, attack_id):
        available = Counter(pokemon["energies"])
        costs = self.attacks[attack_id].energies
        # Use the effective energy types supplied by the engine.
        if len(pokemon["energies"]) < len(costs):
            return False
        return all(available[t] >= count for t, count in Counter(costs).items() if t != 0)

    def ready_score(self, obs, pokemon):
        scores = [self.attack_score(obs, aid, pokemon) for aid in self.cards[pokemon["id"]].attacks
                  if self.can_pay(pokemon, aid)]
        return max(scores, default=-10)
