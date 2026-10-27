"""Visible-observation Alakazam pilot with draw engines and a physical backup.

The original pilot and its saved notebook remain a separate baseline. This
supports the YumeNeko reference and a smaller adaptation; no learned weights.
"""
from collections import Counter

from decks.alakazam_dudunsparce.policy import (
    AlakazamAgent, ABRA, KADABRA, ALAKAZAM, DUDUNSPARCE, PSYCHIC, TELEPATH,
    POFFIN, CANDY, PAD, DAWN, HILDA, LILLIE, BOSS, LANA, STRETCHER, CAGE,
)
from pokemon_agent.sdk import ROOT, read_deck

DUNSPARCES = (65, 305)
FEZ, SHAYMIN, TOGEPI, TOGEKISS, PIKIPEK, TOUCANNON = 140, 343, 959, 214, 1407, 1409
ENRICHING, FAN, ASH = 13, 1161, 1129
BACKUP_ATTACK = 1751
DECK_PATH = ROOT / "decks/alakazam_toucannon/deck.csv"


class AlakazamToucannonAgent(AlakazamAgent):
    """Build a large hand, preserve knockouts, and keep a direct-damage route."""

    def __init__(self, deck=None):
        super().__init__(read_deck(DECK_PATH) if deck is None else deck)

    def lines(self, player):
        counts = Counter(p["id"] for p in self.field(player))
        return (sum(counts[c] for c in (ABRA, KADABRA, ALAKAZAM)),
                sum(counts[c] for c in (*DUNSPARCES, DUDUNSPARCE)))

    def counter_threat(self, obs):
        _, other = self.players(obs)
        return any(p["id"] in (112, 119, 120, 121, 131, 132, 133)
                   for p in self.field(other))

    def attack_score(self, obs, attack_id, attacker=None, defender=None, hand_count=None):
        if attack_id != BACKUP_ATTACK:
            return super().attack_score(obs, attack_id, attacker, defender, hand_count)
        me, other = self.players(obs)
        attacker = attacker or next(iter(me["active"]), None)
        defender = defender or next(iter(other["active"]), None)
        if not attacker or not defender:
            return -10
        damage = 60 + 20 * (len(me["bench"]) + len(other["bench"]))
        target, source = self.cards[defender["id"]], self.cards[attacker["id"]]
        if target.weakness == source.energyType:
            damage *= 2
        if target.resistance == source.energyType:
            damage = max(0, damage - 30)
        prizes = 3 if target.megaEx else 2 if target.ex else 1
        winning = prizes >= len(me["prize"]) or len(self.field(other)) == 1
        return (1800 * prizes + (6000 if winning else 0) if damage >= defender["hp"]
                else 200 + min(damage, defender["hp"]) * .4)

    def best_target(self, obs, defender, hand_count=None):
        me, _ = self.players(obs)
        if not me["active"]:
            return -10
        active = me["active"][0]
        return max((self.attack_score(obs, aid, active, defender, hand_count)
                    for aid in self.cards[active["id"]].attacks if self.can_pay(active, aid)),
                   default=-10)

    def energy_priority(self, obs, pokemon):
        if not pokemon:
            return -10
        me, _ = self.players(obs)
        if me["active"] and pokemon["serial"] == me["active"][0]["serial"]:
            missing_retreat = self.cards[pokemon["id"]].retreatCost - len(pokemon["energies"])
            best = max((self.pivot_score(obs, p) for p in me["bench"]), default=-10)
            if missing_retreat > 0 and best > max(200, self.pivot_score(obs, pokemon) + 50):
                return 350  # A 70-HP Dunsparce cannot use the old free-retreat plan.
        if pokemon["id"] in (ABRA, KADABRA, ALAKAZAM):
            if 5 in pokemon["energies"]:
                return -10
            me, _ = self.players(obs)
            active = bool(me["active"] and pokemon["serial"] == me["active"][0]["serial"])
            return {ABRA: 90, KADABRA: 100, ALAKAZAM: 140}[pokemon["id"]] + 20 * active
        if pokemon["id"] in (PIKIPEK, TOUCANNON):
            return (145 if pokemon["id"] == TOUCANNON else 95) if not pokemon["energies"] else -10
        return super().energy_priority(obs, pokemon)

    def pivot_score(self, obs, pokemon):
        """Value a ready replacement and the public retreat -> gust sequence."""
        me, other = self.players(obs)
        value = self.ready_score(obs, pokemon)
        if not obs["current"]["supporterPlayed"] and any(c["id"] == BOSS for c in me["hand"]):
            value = max(value, max((self.attack_score(obs, aid, pokemon, target, len(me["hand"])-1)
                for aid in self.cards[pokemon["id"]].attacks if self.can_pay(pokemon, aid)
                for target in other["bench"]), default=-10))
        return value

    def draw_allowed(self, obs, count, hand_cost=0):
        """Keep natural draws for the remaining Prize race, with a lethal out."""
        me, other = self.players(obs)
        reserve = max(2, min(6, len(me["prize"])))
        if me["deckCount"] - count >= reserve:
            return True
        if me["deckCount"] < count or not me["active"] or not other["active"]:
            return False
        active = me["active"][0]
        return (active["id"] == ALAKAZAM and self.can_pay(active, 1072)
                and self.attack_score(obs, 1072, hand_count=len(me["hand"])+count-hand_cost) >= 7800)

    def evolution_priority(self, obs, cid, target=None):
        me, _ = self.players(obs)
        counts = Counter(p["id"] for p in self.field(me))
        powered = bool(target and target["energies"])
        if cid == ALAKAZAM:
            normal = bool(target and target["id"] == KADABRA)
            return (1500 if not counts[ALAKAZAM] else 1250) + 120 * powered + 80 * normal
        if cid == TOUCANNON:
            return (1450 if not counts[TOUCANNON] else 700) + 80 * powered
        if cid == TOGEKISS:
            return 650 if counts[ALAKAZAM] or counts[TOUCANNON] else 100
        return 1100 if cid == KADABRA else 1000 if cid == DUDUNSPARCE else -10

    def card_value(self, obs, card, chosen):
        if card is None:
            return 1
        me, _ = self.players(obs)
        cid = card["id"]
        field = Counter(p["id"] for p in self.field(me))
        hand = Counter(c["id"] for c in me["hand"])
        if cid in DUNSPARCES:
            _, draws = self.lines(me)
            copies = sum(hand[c] + chosen[c] for c in DUNSPARCES)
            return 90 if draws + copies < 2 else 15
        if cid in (PIKIPEK, TOUCANNON, TOGEPI, TOGEKISS):
            root, final = (PIKIPEK, TOUCANNON) if cid in (PIKIPEK, TOUCANNON) else (TOGEPI, TOGEKISS)
            copies = field[root] + field[final] + hand[cid] + chosen[cid]
            if cid == final:
                return (145 if final == TOUCANNON else 65) if field[root] and not hand[cid] + chosen[cid] else 15
            return (100 if root == PIKIPEK else 45) if copies == 0 else 10
        if cid == ENRICHING:
            need_psychic = not hand[PSYCHIC] + hand[TELEPATH] and any(
                p["id"] in (ABRA, KADABRA, ALAKAZAM) and 5 not in p["energies"] for p in self.field(me))
            return (80 if need_psychic else 150) if me["deckCount"] > 4 and not hand[cid] + chosen[cid] else 30
        if cid == FEZ:
            return 105 if not field[cid] and len(me["hand"]) < 8 else 15
        if cid == SHAYMIN:
            return 30 if not field[cid] else 5
        if cid == ASH:
            return 75 if sum(self.cards[c["id"]].cardType == 0 for c in me["discard"]) >= 2 else 15
        return super().card_value(obs, card, chosen)

    def hand_delta(self, obs, option):
        """Conservative immediate hand change, including known evolution draw."""
        me, _ = self.players(obs)
        card = self.resolve(obs, option)
        if not card:
            return 0
        cid, kind = card["id"], option["type"]
        if kind == self.O.ABILITY:
            return min(me["deckCount"], {DUDUNSPARCE: 3, FEZ: 3, TOUCANNON: 1}.get(cid, 0))
        if kind == self.O.EVOLVE:
            draw = {KADABRA: 2, ALAKAZAM: 3}.get(cid, 0)
            return -1 + (draw if draw and self.draw_allowed(obs, draw) else 0)
        if kind == self.O.ATTACH and cid == ENRICHING:
            return 3
        return -2 if cid == CANDY else -1

    def main_score(self, obs, option):
        score = self.development_score(obs, option)
        if score <= 0 or option["type"] in (self.O.ATTACK, self.O.RETREAT, self.O.END):
            return score
        me, other = self.players(obs)
        attacks = [o for o in obs["select"]["option"] if o["type"] == self.O.ATTACK]
        if not attacks:
            return score
        best = max(self.attack_score(obs, o["attackId"]) for o in attacks)
        if best >= 7800:
            return min(score, best - 1)
        if best < 1800:
            return score
        card = self.resolve(obs, option)
        if card and card["id"] in (BOSS, LILLIE):
            return score
        delta = self.hand_delta(obs, option)
        powerful = any(o["attackId"] == 1072 and self.attack_score(obs, 1072) == best for o in attacks)
        if powerful and 20 * (len(me["hand"]) + delta) < other["active"][0]["hp"]:
            return min(score, best - 1)
        # Development is useful only if the attacker's current knockout survives.
        if option["type"] == self.O.ABILITY and option.get("area") == self.A.ACTIVE:
            return score
        return max(score, best + 5 + score / 10000)

    def development_score(self, obs, option):
        me, other = self.players(obs)
        kind = option["type"]
        card = self.resolve(obs, option)
        cid = card["id"] if card else None
        field = Counter(p["id"] for p in self.field(me))
        hand = Counter(c["id"] for c in me["hand"])
        if kind == self.O.RETREAT:
            current = max((self.attack_score(obs, o["attackId"]) for o in obs["select"]["option"]
                           if o["type"] == self.O.ATTACK), default=-10)
            best = max((self.pivot_score(obs, p) for p in me["bench"]), default=-10)
            if best >= 1800 and best > current + 50:
                return best + 40
        if kind == self.O.ABILITY:
            if cid in (FEZ, TOUCANNON):
                count = 3 if cid == FEZ else 1
                return 1420 if self.draw_allowed(obs, count) else -10
            if cid == DUDUNSPARCE:
                if len(self.field(me)) == 1 or not self.draw_allowed(obs, 3):
                    return -10
                return 1380
        if kind == self.O.ATTACH:
            target = self.target(obs, option)
            if cid == FAN:
                return 650 if target and me["active"] and target["serial"] == me["active"][0]["serial"] else -10
            if cid == ENRICHING:
                if not self.draw_allowed(obs, 4, hand_cost=1):
                    return -10
                # Colorless does not satisfy Alakazam's Psychic requirement.
                return 1400 + (40 if target and target["id"] in (PIKIPEK, TOUCANNON) and not target["energies"] else 0)
        if kind == self.O.EVOLVE:
            if cid == DUDUNSPARCE and len(self.field(me)) == 1:
                return -10
            return self.evolution_priority(obs, cid, self.target(obs, option))
        if kind == self.O.PLAY:
            if cid in DUNSPARCES:
                return 1050 if self.lines(me)[1] < 2 else -10
            if cid in (PIKIPEK, TOGEPI):
                final = TOUCANNON if cid == PIKIPEK else TOGEKISS
                if field[cid] + field[final]:
                    return -10
                if self.counter_threat(obs) and not any(c["id"] == CAGE for c in obs["current"]["stadium"]):
                    # A ready Candy route merits the fragile bench slot sooner.
                    return 750 if hand[final] and hand[CANDY] else 350
                return 1050 if cid == PIKIPEK else 450
            if cid == FEZ:
                knocked = any(log.get("type") == 6 and log.get("toArea") == self.A.DISCARD
                              and log.get("fromArea") in (self.A.ACTIVE, self.A.BENCH)
                              and log.get("playerIndex") == obs["current"]["yourIndex"]
                              for log in obs.get("logs", []))
                return 1100 if not field[FEZ] and (knocked or len(me["hand"]) <= 5) else -10
            if cid == SHAYMIN:
                # Shaymin blocks damage, not the opponent's damage counters.
                return 300 if not field[SHAYMIN] and any(p["id"] in (140, 144, 1064, 1409) for p in self.field(other)) else -10
            if cid == CANDY:
                routes = [(final, p) for final, root in ((ALAKAZAM, ABRA), (TOUCANNON, PIKIPEK), (TOGEKISS, TOGEPI))
                          if hand[final] for p in self.field(me) if p["id"] == root and not p["appearThisTurn"]]
                return max((self.evolution_priority(obs, final, p) for final, p in routes), default=-10)
            if cid == POFFIN:
                wants = self.lines(me)[0] < 3 or self.lines(me)[1] < 2 or not (field[PIKIPEK] + field[TOUCANNON])
                return 1080 if wants else -10
            if cid == PAD:
                return 980 if any(p["id"] in (ABRA, KADABRA, PIKIPEK, TOGEPI, *DUNSPARCES) for p in self.field(me)) else -10
            if cid == ASH:
                count = sum(self.cards[c["id"]].cardType == 0 for c in me["discard"])
                return 1150 if count and me["deckCount"] <= 6 else 820 if count >= 3 else -10
            if cid == CAGE:
                return 1450 if self.counter_threat(obs) else -10
            if cid == BOSS:
                current = self.best_target(obs, other["active"][0]) if other["active"] else -10
                best = max((self.best_target(obs, p, len(me["hand"])-1) for p in other["bench"]), default=-10)
                return best + 20 if best >= 1800 and best > current else -10
            if cid == HILDA and me["deckCount"] > 2 and not obs["current"]["energyAttached"]:
                enrich_known = sum(c["id"] == ENRICHING for c in me["discard"] + me["hand"])
                enrich_known += sum(c["id"] == ENRICHING for p in self.field(me) for c in p["energyCards"])
                if ENRICHING in self.deck and not enrich_known and me["deckCount"] > 6:
                    return 1170
        return super().development_score(obs, option)

    def select_effect(self, obs):
        select = obs["select"]
        context, options = select["context"], select["option"]
        me, other = self.players(obs)
        effect = (select.get("effect") or {}).get("id")
        if context == self.C.ACTIVATE:
            cid = (select.get("contextCard") or {}).get("id")
            count = {KADABRA: 2, ALAKAZAM: 3, DUDUNSPARCE: 3, FEZ: 3, TOUCANNON: 1}.get(cid)
            if count is not None:
                yes = self.draw_allowed(obs, count)
                return [next(i for i, o in enumerate(options) if o["type"] == (self.O.YES if yes else self.O.NO))]
        custom = context in (self.C.EVOLVE, self.C.SETUP_ACTIVE_POKEMON, self.C.SWITCH, self.C.TO_ACTIVE)
        custom |= effect == FAN and context in (self.C.ATTACH_FROM, self.C.SWITCH_ENERGY)
        if not custom:
            # The base dispatch uses this class's card_value, energy_priority and lines.
            return super().select_effect(obs)

        def score(index):
            o = options[index]
            card = self.resolve(obs, o)
            if context == self.C.EVOLVE:
                return self.evolution_priority(obs, card["id"], self.target(obs, o))
            if effect == FAN:
                if context == self.C.SWITCH_ENERGY:
                    return 100 if card and card["id"] in (2, 5) else 10
                # Avoid completing an opponent's attack with the displaced Energy.
                if not card:
                    return 0
                source = select.get("contextCard") or {}
                energy_type = self.cards[source["id"]].energyType if source.get("id") in self.cards else 0
                aids = self.cards[card["id"]].attacks
                before = any(self.can_pay(card, a) for a in aids)
                after = dict(card, energies=card["energies"] + [energy_type])
                if (not before and any(self.can_pay(after, a) for a in aids)) or (card["id"] == 112 and energy_type == 7):
                    return -500
                return 300 if card["id"] in (235, SHAYMIN) or before else 40
            if context == self.C.SETUP_ACTIVE_POKEMON:
                return {305: 100, 65: 100, FEZ: 90, PIKIPEK: 70, SHAYMIN: 65, ABRA: 50, TOGEPI: 30}.get(card["id"], 40)
            if o.get("playerIndex", obs["current"]["yourIndex"]) != obs["current"]["yourIndex"]:
                return self.best_target(obs, card)
            ready = self.pivot_score(obs, card)
            if ready > 0:
                return ready
            retreat = self.cards[card["id"]].retreatCost
            return 100 - 30 * retreat + min(card["hp"], 100) / 10

        return [max(range(len(options)), key=score)]
