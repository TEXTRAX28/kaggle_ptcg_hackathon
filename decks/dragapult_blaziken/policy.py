"""A visible-only benchmark pilot for Dipam's observed deck, not his source.

This hand-written proxy exercises Item lock, typed Energy, draw, counter spread
and Energy recycling. Results against it must never be labeled Dipam win rates.
"""
from collections import Counter
from pokemon_agent.base import BaseAgent
from pokemon_agent.sdk import ROOT, read_deck

DECK_PATH = ROOT / "decks/dragapult_blaziken/deck.csv"
DREEPY, DRAKLOAK, DRAGAPULT, TORCHIC, COMBUSKEN, BLAZIKEN = 119, 120, 121, 410, 411, 326
MUNKI, FEZ, BUDEW, CLEFAIRY, SHAYMIN, MEOWTH = 112, 140, 235, 272, 343, 1071


class DragapultBenchmarkAgent(BaseAgent):
    """Exact observed list with a deliberately disclosed approximate pilot."""

    def __init__(self, deck=None):
        super().__init__(read_deck(DECK_PATH) if deck is None else deck)

    def cage(self, obs):
        return any(c["id"] == 1264 for c in obs["current"]["stadium"])

    def damage(self, obs, aid, attacker, defender):
        me, _ = self.players(obs)
        value = self.attacks[aid].damage
        if aid == 371:
            value = 20 + 20 * sum(len(p["bench"]) for p in obs["current"]["players"])
        if aid == 20 and obs["current"]["stadium"]:
            value += 60
        target, source = self.cards[defender["id"]], self.cards[attacker["id"]]
        weakness = 5 if target.energyType == 9 and any(p["id"] == CLEFAIRY for p in self.field(me)) else target.weakness
        if weakness == source.energyType:
            value *= 2
        if target.resistance == source.energyType:
            value = max(0, value - 30)
        return value

    def attack_score(self, obs, aid, attacker=None, defender=None):
        me, other = self.players(obs)
        attacker = attacker or next(iter(me["active"]), None)
        defender = defender or next(iter(other["active"]), None)
        if not attacker or not defender:
            return -10
        value = self.damage(obs, aid, attacker, defender)
        target = self.cards[defender["id"]]
        prizes = 3 if target.megaEx else 2 if target.ex else 1
        score = 1800 * prizes if value >= defender["hp"] else 200 + value * .5
        if value >= defender["hp"] and (prizes >= len(me["prize"]) or len(self.field(other)) == 1):
            score += 6000
        if aid == 154 and not self.cage(obs):
            victims = sorted(other["bench"], key=lambda p: p["hp"])
            counters = 60
            for p in victims:
                if p["hp"] <= counters:
                    counters -= p["hp"]
                    score += 1800 * (2 if self.cards[p["id"]].ex else 1)
            score += 40
        if aid == 20 and self.cage(obs):
            score += 120
        return score

    def need_energy(self, pokemon, energy_id=None):
        energies = Counter(pokemon["energies"])
        if pokemon["id"] in (DREEPY, DRAKLOAK, DRAGAPULT):
            return 150 if (energy_id in (None, 2) and not energies[2]) or (energy_id in (None, 5) and not energies[5]) else -10
        if pokemon["id"] in (TORCHIC, COMBUSKEN, BLAZIKEN):
            return 100 if (energy_id in (None, 2) and not energies[2]) or len(pokemon["energies"]) < 2 else -10
        if pokemon["id"] == MUNKI:
            return 90 if energy_id in (None, 7) and not energies[7] else -10
        if pokemon["id"] == CLEFAIRY:
            return 80 if (energy_id in (None, 5) and not energies[5]) or len(pokemon["energies"]) < 2 else -10
        return -10

    def card_value(self, obs, card, chosen):
        if not card:
            return 0
        me, _ = self.players(obs)
        hand = Counter(c["id"] for c in me["hand"])
        field = Counter(p["id"] for p in self.field(me))
        cid = card["id"]
        if cid == DREEPY:
            return 150 if sum(field[c] for c in (DREEPY, DRAKLOAK, DRAGAPULT)) + chosen[cid] < 3 else 10
        if cid == TORCHIC:
            return 135 if not sum(field[c] for c in (TORCHIC, COMBUSKEN, BLAZIKEN)) + chosen[cid] else 10
        if cid in (DRAKLOAK, DRAGAPULT, COMBUSKEN, BLAZIKEN):
            root = {DRAKLOAK: DREEPY, DRAGAPULT: DRAKLOAK, COMBUSKEN: TORCHIC, BLAZIKEN: COMBUSKEN}[cid]
            return 140 if field[root] and not hand[cid] + chosen[cid] else 50
        if cid in (2, 5, 7):
            return 125 if not hand[cid] + chosen[cid] else 20
        if cid == BUDEW:
            return 120 if not field[cid] + chosen[cid] and not field[DRAGAPULT] else 10
        if cid == MUNKI:
            return 100 if field[cid] + chosen[cid] < 2 else 10
        return {1079: 110, 1198: 115, 1227: 90, 1231: 100, 1182: 70}.get(cid, 30)

    def main_score(self, obs, option):
        me, other = self.players(obs)
        kind = option["type"]
        card = self.resolve(obs, option)
        cid = card["id"] if card else None
        field = Counter(p["id"] for p in self.field(me))
        if kind == self.O.ATTACK:
            return self.attack_score(obs, option["attackId"])
        if kind == self.O.END:
            return 0
        if kind == self.O.EVOLVE:
            return 1450 if cid == DRAGAPULT else 1400 if cid == BLAZIKEN else 1350
        if kind == self.O.ABILITY:
            if cid in (DRAKLOAK, FEZ):
                return 1500 if me["deckCount"] > (1 if cid == DRAKLOAK else 3) else -10
            if cid == BLAZIKEN:
                return 1470
            if cid == MUNKI:
                return 1460 if any(p["hp"] < p["maxHp"] for p in self.field(me)) else -10
        if kind == self.O.ATTACH:
            priority = self.need_energy(self.target(obs, option), cid)
            return 1200 + priority if priority > 0 else -10
        if kind == self.O.RETREAT:
            active = max((self.attack_score(obs, o["attackId"]) for o in obs["select"]["option"] if o["type"] == self.O.ATTACK), default=-10)
            bench = max((self.ready_score(obs, p) for p in me["bench"]), default=-10)
            return 1650 if bench > active + 50 else -10
        if kind != self.O.PLAY:
            return -10
        if cid in (DREEPY, TORCHIC, BUDEW, MUNKI):
            return 1200 if self.card_value(obs, card, Counter()) >= 90 else -10
        if cid in (FEZ, MEOWTH):
            return 1000 if not field[cid] and len(me["hand"]) < 6 else -10
        if cid == CLEFAIRY:
            return 1100 if not field[cid] and any(self.cards[p["id"]].energyType == 9 for p in self.field(other)) else -10
        if cid == SHAYMIN:
            return 400 if not field[cid] else -10
        if cid == 31:
            return 600 if self.cage(obs) else -10
        if cid == 1079:
            return 1450
        if cid in (1086, 1121, 1152):
            return 1120 if me["deckCount"] > 3 else -10
        if cid == 1097:
            return 1200 if any(self.card_value(obs, c, Counter()) > 100 for c in me["discard"]) else -10
        if cid == 1198:
            return 1250 if not obs["current"]["energyAttached"] and any(self.need_energy(p) > 0 for p in self.field(me)) else -10
        if cid in (1227, 1213):
            return 1100 if len(me["hand"]) < 5 and me["deckCount"] > 8 else -10
        if cid == 1231:
            return 1150 if me["deckCount"] > 4 else -10
        if cid == 1080:
            return 950 if other["handCount"] >= 6 else -10
        if cid == 1250:
            return 1250 if self.cage(obs) or len(me["bench"]) >= 4 else -10
        if cid == 1256:
            return 1000 if self.cage(obs) or any(self.cards[p["id"]].energyType == 0 for p in self.field(other)) else -10
        if cid == 1182 and me["active"]:
            active = me["active"][0]
            aids = [a for a in self.cards[active["id"]].attacks if self.can_pay(active, a)]
            current = max((self.attack_score(obs, a) for a in aids), default=-10)
            best = max((self.attack_score(obs, a, defender=p) for a in aids for p in other["bench"]), default=-10)
            return best + 30 if best >= 1800 and best > current else -10
        return -10

    def select_effect(self, obs):
        select = obs["select"]
        context, options = select["context"], select["option"]
        me, other = self.players(obs)
        chosen, result = Counter(), []
        discard = context in (self.C.DISCARD, self.C.DISCARD_ENERGY_CARD, self.C.DISCARD_ENERGY)

        def score(index):
            o = options[index]
            if o["type"] in (self.O.YES, self.O.NO):
                return 10 if o["type"] == self.O.YES else -1
            if o["type"] == self.O.NUMBER:
                return o["number"]
            c = self.resolve(obs, o)
            if o["type"] == self.O.EVOLVE:
                return (150 if c["id"] == DRAGAPULT else 145 if c["id"] == BLAZIKEN else 100) + 20 * bool(self.target(obs, o)["energies"])
            if context == self.C.SETUP_ACTIVE_POKEMON:
                return 200 if c["id"] == BUDEW else 100 if c["id"] == DREEPY else 50
            if context in (self.C.SWITCH, self.C.TO_ACTIVE):
                if o.get("playerIndex", obs["current"]["yourIndex"]) != obs["current"]["yourIndex"]:
                    active = next(iter(me["active"]), None)
                    return max((self.attack_score(obs, a, defender=c) for a in self.cards[active["id"]].attacks if self.can_pay(active, a)), default=-10) if active else 0
                return self.ready_score(obs, c)
            if context == self.C.ATTACH_FROM:
                source = select.get("contextCard") or {}
                return self.need_energy(c, source.get("id"))
            if context in (self.C.DAMAGE_COUNTER, self.C.DAMAGE_COUNTER_ANY):
                if self.cage(obs) and o.get("area") == self.A.BENCH:
                    return -10
                prizes = 2 if self.cards[c["id"]].ex else 1
                return 2000 * prizes if c["hp"] <= 10 else 300 * prizes / max(1, c["hp"])
            if context in (self.C.REMOVE_DAMAGE_COUNTER, self.C.HEAL):
                return c["maxHp"] - c["hp"]
            value = self.card_value(obs, c, chosen)
            return -value if discard else value

        cap = select["minCount"] if discard else select["maxCount"]
        for _ in range(cap):
            remaining = [i for i in range(len(options)) if i not in result]
            if not remaining:
                break
            best = max(remaining, key=score)
            if score(best) <= 0 and len(result) >= select["minCount"]:
                break
            result.append(best)
            c = self.resolve(obs, options[best])
            if c:
                chosen[c["id"]] += 1
        return result
