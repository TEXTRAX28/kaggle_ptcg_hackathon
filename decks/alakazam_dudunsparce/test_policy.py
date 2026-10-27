"""Alakazam-specific strategy, deployment and native legality regressions."""
from collections import Counter
import copy
import json
from pathlib import Path
import unittest

from pokemon_agent.agents import default_deck
from .policy import AlakazamAgent
from pokemon_agent.runner import play_game
from pokemon_agent.sdk import validate_selection
from tests.helpers import card, pokemon, observation, config


def position(options, hand_size=18):
    obs = observation(options)
    me, opponent = obs["current"]["players"]
    me["active"] = [pokemon(743, 10, 140, 1)]
    me["active"][0]["energies"] = [5]
    me["hand"] = [card(1231, 50)] + [card(5, 100+i) for i in range(hand_size-1)]
    me["handCount"] = hand_size
    opponent["active"][0]["hp"] = 350
    opponent["bench"] = [pokemon(723, 30, 350, owner=1)]
    return obs


class AlakazamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AlakazamAgent()

    def test_dedicated_entry_returns_exact_sixty_card_non_ex_deck(self):
        from .main import agent
        deck = agent({"select": None})
        self.assertEqual(deck, default_deck("alakazam"))
        self.assertEqual(len(deck), 60)
        pokemon_cards = [self.agent.cards[cid] for cid in deck if self.agent.cards[cid].cardType == 0]
        self.assertEqual(sum(c.basic for c in pokemon_cards), 8)
        self.assertTrue(all(not c.ex and not c.megaEx for c in pokemon_cards))
        self.assertTrue(all(count <= 4 for cid, count in Counter(deck).items() if self.agent.cards[cid].cardType != 5))

    def test_counter_knockout_precedes_supporter_that_spends_hand(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 7, "index": 0}, {"type": 14}])
        self.assertEqual(self.agent(obs), [0])  # 18 cards -> 360 counters on a 350-HP Mega.
        obs["current"]["players"][0]["hand"].pop()
        self.assertEqual(self.agent(obs), [1])  # Need more cards before attacking.

    def test_hand_refresh_is_not_used_to_shrink_a_large_hand(self):
        obs = position([{"type": 7, "index": 0}, {"type": 14}], hand_size=10)
        obs["current"]["players"][0]["hand"][0]["id"] = 1227
        self.assertEqual(self.agent(obs), [1])

    def test_psychic_cost_is_not_paid_by_colorless_energy(self):
        p = pokemon(743, 10, 140, 1)
        p["energies"] = [0]
        self.assertFalse(self.agent.can_pay(p, 1072))
        p["energies"] = [5]
        self.assertTrue(self.agent.can_pay(p, 1072))

    def test_free_retreat_pivot_does_not_take_the_attackers_energy(self):
        obs = position([{"type": 14}])
        me = obs["current"]["players"][0]
        me["active"] = [pokemon(65, 10, 60)]
        me["bench"] = [pokemon(741, 20, 50)]
        self.assertLess(self.agent.energy_priority(obs, me["active"][0]), 0)
        self.assertGreater(self.agent.energy_priority(obs, me["bench"][0]), 0)

    def test_boss_accounts_for_the_card_spent_before_counter_attack(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 7, "index": 0}, {"type": 14}])
        me, opponent = obs["current"]["players"]
        me["hand"][0]["id"] = 1182
        self.assertEqual(self.agent(obs), [0])  # Boss would reduce 360 to 340.
        me["hand"] = me["hand"][:16]
        opponent["bench"][0] = pokemon(722, 30, 90, owner=1)
        self.assertEqual(self.agent(obs), [1])  # Reach a one-Prize KO when the Active survives.

    def test_draw_ability_preserves_a_card_for_the_next_turn(self):
        obs = position([{"type": 1}, {"type": 2}])
        obs["select"].update(context=43, contextCard=card(743, 10))
        obs["current"]["players"][0]["deckCount"] = 3
        self.assertEqual(self.agent(obs), [1])
        obs["current"]["players"][0]["deckCount"] = 4
        self.assertEqual(self.agent(obs), [0])

    def test_dudunsparce_does_not_shuffle_away_the_only_pokemon(self):
        obs = position([{"type": 10, "area": 4, "index": 0}, {"type": 14}])
        me = obs["current"]["players"][0]
        me["active"] = [pokemon(66, 10, 140)]
        self.assertEqual(self.agent(obs), [1])
        me["bench"] = [pokemon(741, 20, 50)]
        self.assertEqual(self.agent(obs), [0])

    def test_search_payload_does_not_change_new_policy(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 7, "index": 0}, {"type": 14}])
        other = copy.deepcopy(obs)
        other["search_begin_input"] = None
        self.assertEqual(self.agent(obs), self.agent(other))



    def test_native_battle_accepts_candidate_and_completes(self):
        settings = dict(config(), agent="alakazam", agent_deck=default_deck("alakazam"))
        result = play_game(settings)
        self.assertEqual(result["status"], "completed", result.get("error"))
        self.assertNotIn("error", result)


class ReplayRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AlakazamAgent()
        cls.positions = json.loads(Path(__file__).with_name("replay_positions.json").read_text(encoding="utf-8"))

    def obs(self, name):
        return copy.deepcopy(self.positions[name]["observation"])

    def chosen(self, obs):
        return [obs["select"]["option"][i] for i in self.agent(obs)]

    def test_search_completes_missing_stage_one_before_duplicate_stage_two(self):
        for name in ("pad_first_stage1", "hilda_reachable_evolution", "pad_second_stage1"):
            with self.subTest(name=name):
                obs = self.obs(name)
                self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 742)

    def test_search_prioritizes_immediately_usable_alakazam(self):
        obs = self.obs("pad_first_stage1")
        me, _ = self.agent.players(obs)
        me["active"][0]["id"] = 742
        me["hand"] = [c for c in me["hand"] if c["id"] != 743]
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 743)

    def test_safe_backup_attachment_before_ordinary_knockout(self):
        obs = self.obs("prepare_backup_energy")
        option = self.chosen(obs)[0]
        self.assertEqual(option["type"], self.agent.O.ATTACH)
        self.assertEqual(self.agent.target(obs, option)["serial"], 73)
        me, enemy = self.agent.players(obs)
        self.assertGreaterEqual(20*(len(me["hand"])-1), enemy["active"][0]["hp"])

    def test_safe_preparation_does_not_spend_the_knockout(self):
        obs = self.obs("prepare_backup_energy")
        options = obs["select"]["option"]
        obs["select"]["option"] = [options[4], options[22], options[24]]
        me, enemy = self.agent.players(obs)
        me["hand"] = me["hand"][:6]  # 120 is exactly the remaining HP.
        self.assertEqual(self.chosen(obs)[0]["type"], self.agent.O.ATTACK)
        me["prize"] = [None]
        me["hand"] += [card(5, 300+i) for i in range(10)]
        self.assertEqual(self.chosen(obs)[0]["type"], self.agent.O.ATTACK)

    def test_red_card_before_ko_when_it_preserves_damage(self):
        obs = self.obs("disrupt_large_hand_before_ko")
        options = obs["select"]["option"]
        obs["select"]["option"] = [options[6], options[12], options[13]]
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1413)

    def test_recovery_rebuilds_basic_instead_of_unusable_energy(self):
        obs = self.obs("recover_missing_basic")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 741)

    def test_search_avoids_stage_two_without_an_evolution_route(self):
        obs = self.obs("search_supported_evolution")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 65)

    def test_poffin_restores_both_attack_and_draw_lines(self):
        obs = self.obs("balance_poffin_targets")
        self.assertCountEqual([self.agent.resolve(obs, o)["id"] for o in self.chosen(obs)], [741, 65])

    def test_gust_breaks_equal_prize_tie_for_toucannon(self):
        obs = self.obs("gust_toucannon_threat")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1182)
        _, enemy = self.agent.players(obs)
        targets = [self.agent.knockout_target_score(obs, p, len(self.agent.players(obs)[0]["hand"])-1)
                   for p in enemy["bench"]]
        self.assertEqual(enemy["bench"][targets.index(max(targets))]["id"], 1409)
        # A visible Togekiss is a higher-value equal-Prize target. This is a
        # synthetic extension: no Boss-vs-visible-Togekiss miss is claimed.
        target = copy.deepcopy(enemy["bench"][0])
        target.update(id=214, hp=140, energies=[])
        self.assertGreater(self.agent.knockout_target_score(obs, target), max(targets))

    def test_winning_attack_precedes_optional_gust(self):
        obs = self.obs("gust_toucannon_threat")
        me, _ = self.agent.players(obs)
        me["prize"] = [None]
        self.assertEqual(self.chosen(obs)[0]["type"], self.agent.O.ATTACK)

    def test_mist_energy_is_not_a_false_game_winning_counter_knockout(self):
        obs = self.obs("history_mist_false_win")
        self.assertLess(self.agent.attack_score(obs, 1072), 0)
        self.assertNotEqual(self.chosen(obs)[0]["type"], self.agent.O.ATTACK)
        # Mist stops effects; it does not stop Kadabra's ordinary damage.
        attack = self.agent.cards[742].attacks[0]
        self.assertGreater(self.agent.attack_score(obs, attack), 0)

    def test_rock_fighting_only_protects_fighting_pokemon(self):
        obs = self.obs("history_mist_false_win")
        _, enemy = self.agent.players(obs)
        target = enemy["active"][0]
        target["energyCards"][0]["id"] = 20
        self.assertGreater(self.agent.attack_score(obs, 1072), 0)  # Grass Crustle.
        target["id"] = 117  # Fighting Cornerstone Mask Ogerpon ex.
        self.assertLess(self.agent.attack_score(obs, 1072), 0)
        target["energyCards"] = []
        self.assertGreater(self.agent.attack_score(obs, 1072), 0)  # Its Ability stops damage only.

    def test_gust_takes_an_unprotected_knockout_instead_of_attacking_mist(self):
        obs = self.obs("history_mist_gust_escape")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1182)

    def test_ability_protection_stops_counters_but_bench_only_protection_does_not(self):
        obs = self.obs("history_ability_immunity")
        _, enemy = self.agent.players(obs)
        target = enemy["active"][0]
        for cid in (203, 835, 1348, 1349, 1374, 1375):
            with self.subTest(card=cid):
                target["id"] = cid
                self.assertLess(self.agent.attack_score(obs, 1072), 0)
        target["id"] = 28  # This other Poltchageist is protected only on the Bench.
        self.assertGreater(self.agent.attack_score(obs, 1072), 0)

    def test_rocket_articuno_protection_applies_only_to_basic_rocket_pokemon(self):
        obs = self.obs("history_ability_immunity")
        _, enemy = self.agent.players(obs)
        enemy["active"][0]["id"] = 463  # Team Rocket's Murkrow.
        enemy["bench"] = [pokemon(414, 800, 120, owner=enemy["active"][0]["playerIndex"])]
        self.assertLess(self.agent.attack_score(obs, 1072), 0)
        enemy["active"][0]["id"] = 741  # Abra is outside Repelling Veil's scope.
        self.assertGreater(self.agent.attack_score(obs, 1072), 0)

    def test_confused_attacker_retreats_to_a_ready_replacement_for_the_same_knockout(self):
        obs = self.obs("history_confusion_pivot")
        self.assertEqual(self.chosen(obs)[0]["type"], self.agent.O.RETREAT)
        me, _ = self.agent.players(obs)
        me["prize"] = [None]
        self.assertEqual(self.chosen(obs)[0]["type"], self.agent.O.RETREAT)
        me["confused"] = False
        self.assertEqual(self.chosen(obs)[0]["type"], self.agent.O.ATTACK)

    def test_hilda_finds_missing_attack_energy_before_a_random_refresh(self):
        obs = self.obs("history_energy_supporter")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1225)
        me, _ = self.agent.players(obs)
        me["discard"] += [card(19, 500+i) for i in range(4)]
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1227)

    def test_search_remains_available_with_four_cards_and_reserves_a_draw(self):
        obs = self.obs("history_low_deck_search")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1225)
        me, _ = self.agent.players(obs)
        me["deckCount"] = 2
        self.assertEqual(self.chosen(obs)[0]["type"], self.agent.O.END)

    def test_gust_denies_an_unpowered_alakazam_in_the_mirror(self):
        obs = self.obs("history_mirror_unpowered_threat")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1182)

    def test_refresh_precedes_spending_the_draw_engine(self):
        obs = self.obs("history_refresh_before_draw")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1227)

    def test_cage_is_played_before_the_opposing_counter_line_evolves(self):
        obs = self.obs("history_preemptive_cage")
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1264)

    def test_hammer_removes_mist_before_claiming_a_knockout(self):
        obs = self.obs("history_mist_false_win")
        me, _ = self.agent.players(obs)
        me["hand"].append(card(1081, 900))
        obs["select"]["option"].append({"type": 7, "index": len(me["hand"])-1})
        self.assertEqual(self.agent.resolve(obs, self.chosen(obs)[0])["id"], 1081)

    def test_hammer_discards_protection_instead_of_other_special_energy(self):
        obs = self.obs("history_mist_false_win")
        _, enemy = self.agent.players(obs)
        target = enemy["active"][0]
        target["energyCards"].append(card(19, 901, owner=target["playerIndex"]))
        obs["select"].update(context=int(self.agent.C.DISCARD_ENERGY),
                             effect=card(1081, 900), minCount=1, maxCount=1,
                             option=[{"type": int(self.agent.O.ENERGY), "playerIndex": target["playerIndex"],
                                      "area": int(self.agent.A.ACTIVE), "index": 0, "energyIndex": i, "count": 1}
                                     for i in (1, 0)])
        self.assertEqual(self.agent(obs), [1])

    def test_recorded_positions_are_legal_and_hidden_payload_invariant(self):
        for name, row in self.positions.items():
            with self.subTest(name=name):
                obs = copy.deepcopy(row["observation"])
                action = self.agent(obs)
                validate_selection(obs, action)
                self.assertIsNone(self.agent.players(obs)[1]["hand"])
                obs["search_begin_input"] = "unavailable spectator payload"
                self.assertEqual(self.agent(obs), action)


if __name__ == "__main__":
    unittest.main()
