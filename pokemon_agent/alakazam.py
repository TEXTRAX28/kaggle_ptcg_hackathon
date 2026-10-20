"""One-Prize Alakazam/Dudunsparce pilot using only its legal observation.

Powerful Hand scales with hand size, not discarded Energy. The Abomasnow base
supplies selection validation and visible-card resolution; strategy is replaced.
"""
from collections import Counter

from .policy import AbomasnowAgent
from .sdk import ROOT, read_deck

ABRA, KADABRA, ALAKAZAM, DUNSPARCE, DUDUNSPARCE = 741, 742, 743, 65, 66
PSYCHIC, TELEPATH = 5, 19
POFFIN, CANDY, PAD, DAWN, HILDA = 1086, 1079, 1152, 1231, 1225
LILLIE, BOSS, LANA, STRETCHER, CAGE, RED_CARD = 1227, 1182, 1184, 1097, 1264, 1413
DECK_PATH = ROOT / "decks/alakazam.csv"


class AlakazamAgent(AbomasnowAgent):
    """Grow a hand through evolution/draw and trade one-Prize attackers."""

    def __init__(self, deck=None):
        # Basic Psychic and Telepath each supply one Psychic in engine energies;
        # the inherited typed-cost check therefore handles both correctly.
        super().__init__(read_deck(DECK_PATH) if deck is None else deck)

    def lines(self, player):
        counts = Counter(p["id"] for p in self.field(player))
        return counts[ABRA] + counts[KADABRA] + counts[ALAKAZAM], counts[DUNSPARCE] + counts[DUDUNSPARCE]

    def attack_score(self, obs, attack_id, attacker=None, defender=None, hand_count=None):
        me, opponent = self.players(obs)
        attacker = attacker or next(iter(me["active"]), None)
        defender = defender or next(iter(opponent["active"]), None)
        if not attacker or not defender:
            return -10
        attack = self.attacks[attack_id]
        if attack_id == 1072:
            damage = 20 * (len(me["hand"]) if hand_count is None else hand_count)
        else:
            damage = max(0, attack.damage)
            target = self.cards[defender["id"]]
            if damage and target.weakness == self.cards[attacker["id"]].energyType:
                damage *= 2
            if damage and target.resistance == self.cards[attacker["id"]].energyType:
                damage = max(0, damage - 30)
        target = self.cards[defender["id"]]
        prizes = 3 if target.megaEx else 2 if target.ex else 1
        winning = prizes >= len(me["prize"]) or len(self.field(opponent)) == 1
        if damage >= defender["hp"]:
            return 1800 * prizes + (6000 if winning else 0)
        return 200 + min(damage, defender["hp"]) * 0.4 if damage else -1

    def energy_priority(self, obs, pokemon):
        if not pokemon or pokemon["energies"] or pokemon["id"] not in (ABRA, KADABRA, ALAKAZAM):
            return -10
        me, _ = self.players(obs)
        active = bool(me["active"] and pokemon["serial"] == me["active"][0]["serial"])
        return {ALAKAZAM: 140, KADABRA: 100, ABRA: 90}.get(pokemon["id"], -10) + (20 if active else 0)

    def card_value(self, obs, card, chosen):
        if card is None:
            return 1
        me, _ = self.players(obs)
        cid = card["id"]
        hand = Counter(c["id"] for c in me["hand"])
        field = Counter(p["id"] for p in self.field(me))
        basics, draws = self.lines(me)
        if cid == ALAKAZAM:
            return 110 if hand[cid] + chosen[cid] < max(1, field[KADABRA] + field[ABRA]) else 15
        if cid == KADABRA:
            return 100 if hand[cid] + chosen[cid] < max(1, field[ABRA]) else 15
        if cid == ABRA:
            return 95 if basics + hand[cid] + chosen[cid] < 3 else 15
        if cid == DUNSPARCE:
            return 85 if draws + hand[cid] + chosen[cid] < 2 else 15
        if cid == DUDUNSPARCE:
            return 90 if hand[cid] + chosen[cid] < max(1, field[DUNSPARCE]) else 15
        if cid in (PSYCHIC, TELEPATH):
            have = hand[PSYCHIC] + hand[TELEPATH] + chosen[PSYCHIC] + chosen[TELEPATH]
            return (105 if have == 0 else 40) + (5 if cid == TELEPATH and basics < 3 else 0)
        return {CANDY: 80 if field[ABRA] and hand[ALAKAZAM] else 30,
                DAWN: 75, HILDA: 70, POFFIN: 65, PAD: 60, LANA: 50,
                LILLIE: 50 if len(me["hand"]) < 6 else 5}.get(cid, 20)

    def main_score(self, obs, option):
        me, opponent = self.players(obs)
        kind = option["type"]
        hand = Counter(c["id"] for c in me["hand"])
        basics, draws = self.lines(me)
        if kind == self.O.ATTACK:
            return self.attack_score(obs, option["attackId"])
        if kind == self.O.END:
            return 0
        if kind == self.O.EVOLVE:
            card, target = self.resolve(obs, option), self.target(obs, option)
            if card["id"] == DUDUNSPARCE and len(self.field(me)) == 1:
                return -10
            if me["deckCount"] <= 3:
                return 10 if card["id"] == ALAKAZAM else -10
            return (1250 if card["id"] == ALAKAZAM else 1100) + max(0, self.energy_priority(obs, target))
        if kind == self.O.ATTACH:
            card, target = self.resolve(obs, option), self.target(obs, option)
            priority = self.energy_priority(obs, target)
            return 1000 + priority + (25 if card["id"] == TELEPATH and basics < 3 else 0) if priority > 0 else -10
        if kind == self.O.RETREAT:
            active = max((self.attack_score(obs, o["attackId"]) for o in obs["select"]["option"]
                          if o["type"] == self.O.ATTACK), default=-10)
            bench = max((self.ready_score(obs, p) for p in me["bench"]), default=-10)
            return 1600 if bench > active + 50 else -10
        if kind == self.O.ABILITY:
            card = self.resolve(obs, option)
            if card and card["id"] == DUDUNSPARCE:
                return 950 if len(self.field(me)) > 1 and me["deckCount"] > 3 else -10
            return -10
        if kind != self.O.PLAY:
            return -10
        card = self.resolve(obs, option)
        cid = card["id"]
        if cid == ABRA:
            return 1200 if basics < 3 else -10
        if cid == DUNSPARCE:
            return 1000 if draws < 2 else -10
        if cid == CANDY:
            eligible = any(p["id"] == ABRA and not p["appearThisTurn"] for p in self.field(me))
            if not eligible or not hand[ALAKAZAM]:
                return -10
            return 1350 if not any(p["id"] == ALAKAZAM for p in self.field(me)) else 500
        if cid == POFFIN:
            return 1050 if basics < 2 or draws < 1 else 700 if basics < 3 or draws < 2 else -10
        if cid == PAD:
            return 900 if basics < 2 or draws < 1 or any(p["id"] in (ABRA, KADABRA) for p in self.field(me)) else -10
        if cid in (DAWN, HILDA):
            return (850 if cid == DAWN else 800) if me["deckCount"] > 4 else -10
        if cid == LILLIE:
            count = 8 if len(me["prize"]) == 6 else 6
            return 880 if len(me["hand"]) < count - 1 and me["deckCount"] > count else -10
        if cid == LANA:
            available = sum(self.cards[c["id"]].cardType in (0, 5) for c in me["discard"])
            return 860 if available >= 2 else -10
        if cid == STRETCHER:
            return 880 if any(self.card_value(obs, c, Counter()) >= 85 for c in me["discard"]) else -10
        if cid == CAGE:
            return 700 if any(p["id"] in (121, 132, 133) for p in self.field(opponent)) else -10
        if cid == RED_CARD:
            return 700 if opponent["handCount"] > 5 else -10
        if cid == BOSS:
            if not me["active"] or me["active"][0]["id"] != ALAKAZAM or not self.can_pay(me["active"][0], 1072):
                return -10
            current = self.attack_score(obs, 1072)
            best = max((self.attack_score(obs, 1072, defender=p, hand_count=len(me["hand"])-1)
                        for p in opponent["bench"]), default=-10)
            return best + 20 if best >= 1800 and best > current else -10
        return -10

    def select_effect(self, obs):
        select = obs["select"]
        context, options = select["context"], select["option"]
        me, opponent = self.players(obs)
        chosen, indices = Counter(), []
        discard = context in (self.C.DISCARD, self.C.DISCARD_CARD_OR_ATTACHED_CARD,
                              self.C.DISCARD_ENERGY_CARD, self.C.DISCARD_ENERGY, self.C.DISCARD_TOOL_CARD)

        def score(index):
            option = options[index]
            kind = option["type"]
            if kind in (self.O.YES, self.O.NO):
                yes = context != self.C.MULLIGAN
                if context == self.C.ACTIVATE:
                    source = select.get("contextCard") or {}
                    draw = {KADABRA: 2, ALAKAZAM: 3}.get(source.get("id"), 0)
                    yes = me["deckCount"] > draw
                return 10 if (kind == self.O.YES) == yes else -1
            if kind == self.O.NUMBER:
                return min(option["number"], max(0, me["deckCount"]-1)) - .01*option["number"]
            if kind == self.O.ATTACK:
                return self.attack_score(obs, option["attackId"])
            if kind == self.O.EVOLVE:
                target = self.target(obs, option)
                return 100 + (60 if target["energies"] else 0) + (30 if option["inPlayArea"] == self.A.ACTIVE else 0)
            card = self.resolve(obs, option)
            if context == self.C.SETUP_ACTIVE_POKEMON:
                return 100 if card and card["id"] == DUNSPARCE else 80
            if context in (self.C.SWITCH, self.C.TO_ACTIVE) and card and "energies" in card:
                if option.get("playerIndex", obs["current"]["yourIndex"]) != obs["current"]["yourIndex"]:
                    return self.attack_score(obs, 1072, defender=card)
                return self.ready_score(obs, card) + (40 if card["id"] == DUNSPARCE else 0)
            if context == self.C.ATTACH_FROM and card and "energies" in card:
                return self.energy_priority(obs, card)
            if context in (self.C.SETUP_BENCH_POKEMON, self.C.TO_BENCH, self.C.TO_FIELD) and card:
                basics, draws = self.lines(me)
                if card["id"] == ABRA:
                    return 100 if basics + chosen[ABRA] < 3 else -10
                if card["id"] == DUNSPARCE:
                    return 90 if draws + chosen[DUNSPARCE] < 2 else -10
            value = self.card_value(obs, card, chosen)
            return -value if discard else value

        cap = select["minCount"] if discard else select["maxCount"]
        for _ in range(cap):
            remaining = [i for i in range(len(options)) if i not in indices]
            best = max(remaining, key=score)
            if score(best) <= 0 and len(indices) >= select["minCount"]:
                break
            indices.append(best)
            card = self.resolve(obs, options[best])
            if card:
                chosen[card["id"]] += 1
        return indices
