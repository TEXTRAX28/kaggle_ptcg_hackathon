"""Abomasnow/Kyogre heuristic using only visible observations and legal choices.

Scores are preferences, not a complete damage/rules simulator. No training or
opponent-hand access is involved.
"""
from collections import Counter
from math import comb

from pokemon_agent.base import BaseAgent
from pokemon_agent.sdk import read_deck

WATER, KYOGRE, SNOVER, ABOMASNOW = 3, 721, 722, 723
SIGNAL, BELT, CYRANO, LILLIE, WAITRESS = 1145, 1158, 1205, 1227, 1235


class AbomasnowAgent(BaseAgent):
    """Set up Abomasnow, preserve useful resources and recycle with Kyogre."""

    def __init__(self, deck=None):
        super().__init__(read_deck() if deck is None else deck)

    def water_distribution(self, obs):
        """Marginal draw distribution over unknown deck/prizes, not true order."""
        me, _ = self.players(obs)
        visible = list(me["hand"] or []) + me["discard"] + [c for c in me["prize"] if c]
        for p in self.field(me):
            visible += [p] + p["energyCards"] + p["tools"] + p["preEvolution"]
        unique = {c["serial"]: c for c in visible}
        unknown = me["deckCount"] + sum(c is None for c in me["prize"])
        water = max(0, min(unknown, self.deck.count(WATER) - sum(c["id"] == WATER for c in unique.values())))
        draws = min(6, me["deckCount"])
        if unknown == 0 or draws == 0:
            return [(0, 1.0)]
        denominator = comb(unknown, draws)
        return [(k, comb(water, k) * comb(unknown - water, draws - k) / denominator)
                for k in range(draws + 1) if k <= water and draws - k <= unknown - water]

    def attack_score(self, obs, attack_id, attacker=None):
        me, opponent = self.players(obs)
        attacker = attacker or next(iter(me["active"]), None)
        defender = next(iter(opponent["active"]), None)
        if not attacker or not defender:
            return -10.0
        attack = self.attacks[attack_id]
        if attack.name == "Hammer-lanche":
            distribution = [(100 * k, p) for k, p in self.water_distribution(obs)]
        elif attack.name == "Riptide":
            distribution = [(20 * sum(c["id"] == WATER for c in me["discard"]), 1.0)]
        else:
            distribution = [(max(0, attack.damage), 1.0)]
        target_info, attacker_info = self.cards[defender["id"]], self.cards[attacker["id"]]
        # This deck cannot disable Sylveon's Safeguard or Crustle's Mysterious
        # Rock Inn. Both prevent attack damage from ex (including Mega ex).
        # Frost Barrier can still apply its defensive effect; Hammer-lanche
        # would only spend deck cards. A non-ex Kyogre remains a valid attacker.
        if defender["id"] in (330, 345) and (attacker_info.ex or attacker_info.megaEx):
            return 20.0 if attack.name == "Frost Barrier" else -1.0
        prizes = 3 if target_info.megaEx else 2 if target_info.ex else 1
        belt = any(t["id"] == BELT for t in attacker["tools"]) and (target_info.ex or target_info.megaEx)
        expected, knockout = 0.0, 0.0
        for damage, probability in distribution:
            if damage > 0:
                damage += 50 if belt else 0
                if target_info.weakness == attacker_info.energyType:
                    damage *= 2
                if target_info.resistance == attacker_info.energyType:
                    damage = max(0, damage - 30)
            expected += min(damage, defender["hp"]) * probability
            knockout += probability * (damage >= defender["hp"])
        winning_ko = prizes >= len(me["prize"]) or len(self.field(opponent)) == 1
        score = 200 + expected * 0.4 + knockout * (350 * prizes + (5000 if winning_ko else 0))
        if attack.name == "Hammer-lanche":
            score -= 25  # Prefer a sufficient Frost Barrier over needless milling.
            if me["deckCount"] <= 6:
                score -= 1800 * (1 - (knockout if winning_ko else 0))
        elif attack.name == "Frost Barrier":
            score += 20
        elif attack.name == "Riptide":
            discarded = sum(c["id"] == WATER for c in me["discard"])
            score += min(discarded, 12) * (15 if me["deckCount"] <= 8 else 2)
        elif attack.name == "Swirling Waves":
            score -= 45
        return score if expected > 0 else -1

    def energy_priority(self, obs, pokemon):
        if not pokemon:
            return -100
        me, opponent = self.players(obs)
        active = bool(me["active"] and pokemon["serial"] == me["active"][0]["serial"])
        count = len(pokemon["energies"])
        if pokemon["id"] == KYOGRE and not active and count == 0 and me["active"]:
            front = me["active"][0]
            # Powerful Hand places counters: Frost Barrier cannot reduce it.
            # Public handCount estimates the threat; no hidden cards are read.
            counter_threat = 20 * opponent["handCount"] if any(
                p["id"] == 743 and p["energies"] for p in self.field(opponent)) else 0
            if (front["id"] == ABOMASNOW and len(front["energies"]) >= 2
                    and counter_threat >= front["hp"]):
                # Do not divert the attachment that enables Hammer-lanche now.
                return 130  # Prepare a one-Prize Riptide attacker before the KO.
        if pokemon["id"] in (SNOVER, ABOMASNOW):
            needed = 2 if count < 2 else 3
            score = 90 if count < 2 else 35 if count == 2 else -20
            if (active and pokemon["id"] == ABOMASNOW and count == 3 and me["deckCount"] <= 8
                    and any(p["id"] == KYOGRE and len(p["energies"]) >= 1 for p in me["bench"])):
                needed, score = 4, 110  # Pay retreat and recycle before decking out.
        else:
            # A lone Kyogre with an empty discard cannot deal damage with
            # Riptide. Charge Swirling Waves (or its three-Energy retreat).
            discarded = sum(c["id"] == WATER for c in me["discard"])
            needed = 3 if active and (discarded < 7 or any(p["id"] in (SNOVER, ABOMASNOW) for p in me["bench"])) else 1
            score = 60 if count == 0 else 45 if count < needed else -25
        return score + (35 if active and count < needed else 0) + min(pokemon["hp"], 100) / 100

    def main_score(self, obs, option):
        me, opponent = self.players(obs)
        kind = option["type"]
        hand = Counter(c["id"] for c in me["hand"])
        field = Counter(p["id"] for p in self.field(me))
        if kind == self.O.ATTACK:
            return self.attack_score(obs, option["attackId"])
        if kind == self.O.END:
            return 0
        if kind == self.O.EVOLVE:
            target = self.target(obs, option)
            if (option.get("inPlayArea") == self.A.BENCH and len(opponent["prize"]) <= 3
                    and len(target["energies"]) < 2):
                # A gust can turn an idle Mega into the opponent's final Prizes.
                # Attach to Snover first; reconsider evolution once it can attack.
                return -10
            return 1100 + self.energy_priority(obs, target)
        if kind == self.O.ATTACH:
            card, target = self.resolve(obs, option), self.target(obs, option)
            if card["id"] == BELT:
                return 850 if target["id"] in (SNOVER, ABOMASNOW) else 5
            priority = self.energy_priority(obs, target)
            return 900 + priority if priority > 0 else -5
        if kind == self.O.RETREAT:
            if not me["bench"]:
                return -100
            available = [self.attack_score(obs, o["attackId"]) for o in obs["select"]["option"] if o["type"] == self.O.ATTACK]
            active_value = max(available, default=-10)
            best_bench = max(self.ready_score(obs, p) for p in me["bench"])
            return 1050 if best_bench > active_value + 150 else -100
        if kind == self.O.PLAY:
            cid = self.resolve(obs, option)["id"]
            if cid == SNOVER:
                return 1200 if field[SNOVER] + field[ABOMASNOW] < 2 else -10
            if cid == KYOGRE:
                return 1000 if field[KYOGRE] < 1 else -10
            need_evolution = field[SNOVER] > hand[ABOMASNOW]
            if cid == SIGNAL:
                return 950 if need_evolution else -10
            if cid == CYRANO:
                return 800 if need_evolution and not hand[SIGNAL] else -10
            if cid == WAITRESS:
                priority = max((self.energy_priority(obs, p) for p in self.field(me)), default=-100)
                return 800 + priority if priority > 0 else -10
            if cid == LILLIE:
                draws = 8 if len(me["prize"]) == 6 else 6
                if me["deckCount"] + len(me["hand"]) - 1 <= draws:
                    return -100
                missing_setup = field[SNOVER] + field[ABOMASNOW] < 2 or (need_evolution and not hand[SIGNAL])
                return 750 if missing_setup or len(me["hand"]) <= draws else 30
            return -10
        if kind == self.O.ABILITY:
            return 50
        return -20

    def card_value(self, obs, card, chosen):
        if card is None:  # A face-down prize has no known identity.
            return 1
        me, _ = self.players(obs)
        cid = card["id"]
        field = Counter(p["id"] for p in self.field(me))
        hand = Counter(c["id"] for c in me["hand"])
        if cid == ABOMASNOW:
            return 90 if hand[cid] + chosen[cid] < max(1, field[SNOVER]) else -2
        if cid == SNOVER:
            return 85 if field[cid] + field[ABOMASNOW] + chosen[cid] < 2 else -2
        if cid == KYOGRE:
            return 75 if field[cid] + chosen[cid] < 1 else -2
        if cid == WATER:
            return 30 if hand[cid] < 3 else 5
        return {LILLIE: 70, WAITRESS: 65, SIGNAL: 50, CYRANO: 40, BELT: 55}.get(cid, 1)

    def select_effect(self, obs):
        select = obs["select"]
        context, options = select["context"], select["option"]
        C, O = self.C, self.O
        me, _ = self.players(obs)
        chosen, indices = Counter(), []
        discard = context in (C.DISCARD, C.DISCARD_CARD_OR_ATTACHED_CARD, C.DISCARD_ENERGY_CARD,
                              C.DISCARD_ENERGY, C.DISCARD_TOOL_CARD)

        def score(i):
            option = options[i]
            kind = option["type"]
            if kind in (O.YES, O.NO):
                # Evolving early is valuable; the evaluation runner can control
                # first/second order independently of this policy preference.
                yes = context != C.MULLIGAN
                return 10 if (kind == O.YES) == yes else -1
            if kind == O.NUMBER:
                return option["number"] if context != C.DRAW_COUNT else min(option["number"], max(0, me["deckCount"] - 1)) - (0.01 * option["number"])
            if kind == O.ATTACK:
                return self.attack_score(obs, option["attackId"])
            card = self.resolve(obs, option)
            if context == C.SETUP_ACTIVE_POKEMON:
                return 100 if card and card["id"] == SNOVER else 60
            if context in (C.SWITCH, C.TO_ACTIVE) and card and "energies" in card:
                return self.ready_score(obs, card) + (30 if card["id"] == ABOMASNOW else 0)
            if context == C.ATTACH_FROM and card and "energies" in card:
                return self.energy_priority(obs, card)
            if context == C.ATTACH_TO:
                return 100 if card and card["id"] == WATER else 5
            value = self.card_value(obs, card, chosen)
            return -value if discard else value

        cap = select["maxCount"]
        # Discard only what is required. Energy prompts can ask again until the
        # cost is paid; obey their supplied bounds on every selection.
        if discard:
            cap = select["minCount"]
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
