"""Abomasnow/Kyogre strategy and recorded-position regressions."""
import copy
import json
from pathlib import Path
import unittest

from .policy import AbomasnowAgent
from pokemon_agent.sdk import SAMPLE, read_deck
from tests.helpers import card, pokemon, observation


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AbomasnowAgent()

    def test_entry_point_returns_original_sixty_card_deck(self):
        from .main import agent
        self.assertEqual(agent({"select": None}), read_deck(SAMPLE / "deck.csv"))
        self.assertEqual(len(agent({"select": None})), 60)

    def test_lone_kyogre_keeps_charging_when_riptide_has_no_damage(self):
        obs = observation([{"type": 8, "area": 2, "index": 0, "inPlayArea": 4, "inPlayIndex": 0},
                           {"type": 13, "attackId": 1042}, {"type": 14}])
        obs["current"]["players"][0]["active"] = [pokemon(721, 10, 150, 1)]
        self.assertEqual(self.agent(obs), [0])

    def test_avoid_milling_last_cards_when_frost_barrier_is_available(self):
        obs = observation([{"type": 13, "attackId": 1046}, {"type": 13, "attackId": 1047}, {"type": 14}])
        me, opponent = obs["current"]["players"]
        me["deckCount"] = 5
        opponent["active"][0]["hp"] = 350
        opponent["bench"] = [pokemon(721, 22, 150, owner=1)]
        self.assertEqual(self.agent(obs), [1])

    def test_kyogre_recycles_large_discard(self):
        obs = observation([{"type": 13, "attackId": 1042}, {"type": 13, "attackId": 1043}, {"type": 14}])
        me = obs["current"]["players"][0]
        me["active"] = [pokemon(721, 10, 150, 3)]
        me["discard"] = [card(3, 1000 + i) for i in range(12)]
        me["deckCount"] = 3
        self.assertEqual(self.agent(obs), [0])

    def test_retreat_to_kyogre_against_ex_damage_immunity(self):
        a = self.agent
        for defender_id in (330, 345):
            with self.subTest(defender=defender_id):
                obs = observation([{"type": int(a.O.ATTACK), "attackId": 1046},
                                   {"type": int(a.O.ATTACK), "attackId": 1047},
                                   {"type": int(a.O.RETREAT)}, {"type": int(a.O.END)}])
                me, opponent = obs["current"]["players"]
                me["active"] = [pokemon(723, 10, 350, 4)]
                me["bench"] = [pokemon(721, 20, 150, 1)]
                me["discard"] = [card(3, 1000 + i) for i in range(10)]
                opponent["active"] = [pokemon(defender_id, 11, 150 if defender_id == 345 else 120, owner=1)]
                opponent["bench"] = [pokemon(721, 22, 150, owner=1)]
                self.assertEqual(a(obs), [2])
                self.assertGreater(a.attack_score(obs, 1042, me["bench"][0]), 0)

    def test_blocked_abomasnow_preserves_deck_and_uses_frost_barrier(self):
        a = self.agent
        obs = observation([{"type": int(a.O.ATTACK), "attackId": 1046},
                           {"type": int(a.O.ATTACK), "attackId": 1047},
                           {"type": int(a.O.END)}])
        me, opponent = obs["current"]["players"]
        opponent["active"] = [pokemon(345, 11, 150, owner=1)]
        self.assertLess(a.attack_score(obs, 1046), 0)
        self.assertEqual(a(obs), [1])

    def test_optional_bench_does_not_fill_with_redundant_kyogre(self):
        obs = observation([{"type": 3, "area": 2, "index": i, "playerIndex": 0} for i in range(2)],
                          context=2, minimum=0, maximum=2)
        me = obs["current"]["players"][0]
        me["bench"] = [pokemon(721, 20, 150)]
        me["hand"] = [card(721, 40), card(722, 41)]
        self.assertEqual(self.agent(obs), [1])

    def test_unknown_native_search_input_does_not_affect_policy(self):
        obs = observation([{"type": 13, "attackId": 1046}, {"type": 13, "attackId": 1047}, {"type": 14}])
        other = copy.deepcopy(obs)
        other["search_begin_input"] = None
        self.assertEqual(self.agent(obs), self.agent(other))


class ReplayRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AbomasnowAgent()
        cls.positions = json.loads((Path(__file__).with_name("replay_positions.json")).read_text())

    def position(self, name):
        return copy.deepcopy(self.positions[name]["observation"])

    def test_prepare_kyogre_before_damaged_mega_is_knocked_out(self):
        obs = self.position("prepare_kyogre")
        option = obs["select"]["option"][self.agent(obs)[0]]
        self.assertEqual(option["type"], self.agent.O.ATTACH)
        self.assertEqual(self.agent.target(obs, option)["id"], 721)

    def test_keep_energy_for_the_current_attack_under_counter_pressure(self):
        obs = self.position("enable_current_attack")
        option = obs["select"]["option"][self.agent(obs)[0]]
        self.assertEqual(option["type"], self.agent.O.ATTACH)
        self.assertEqual(self.agent.target(obs, option)["serial"], 71)

    def test_defer_unpowered_bench_mega_when_opponent_needs_two_prizes(self):
        obs = self.position("defer_bench_mega")
        option = obs["select"]["option"][self.agent(obs)[0]]
        self.assertEqual(option["type"], self.agent.O.ATTACH)
        self.assertEqual(self.agent.target(obs, option)["id"], 721)
        evolve = next(o for o in obs["select"]["option"] if o["type"] == self.agent.O.EVOLVE)
        self.assertLess(self.agent.main_score(obs, evolve), 0)

    def test_evolution_still_protects_active_snover_and_readies_powered_bench(self):
        obs = self.position("defer_bench_mega")
        me, _ = self.agent.players(obs)
        evolve = next(o for o in obs["select"]["option"] if o["type"] == self.agent.O.EVOLVE)
        me["bench"][0]["energies"] = [3, 3]
        self.assertGreater(self.agent.main_score(obs, evolve), 1000)
        me["active"], me["bench"] = me["bench"], me["active"]
        me["active"][0]["energies"] = []
        evolve["inPlayArea"] = self.agent.A.ACTIVE
        self.assertGreater(self.agent.main_score(obs, evolve), 1000)

    def test_backup_priority_uses_public_threat_not_hidden_payload(self):
        obs = self.position("prepare_kyogre")
        _, opponent = self.agent.players(obs)
        opponent["handCount"] = 0
        option = obs["select"]["option"][self.agent(obs)[0]]
        self.assertEqual(self.agent.target(obs, option)["id"], 722)
        obs["search_begin_input"] = "unreadable hidden data"
        opponent["hand"] = [card(3, 9000 + i, owner=0) for i in range(30)]
        self.assertEqual(self.agent(obs), [obs["select"]["option"].index(option)])

    def test_winning_attack_precedes_preparing_a_backup(self):
        obs = self.position("prepare_kyogre")
        me, opponent = self.agent.players(obs)
        me["prize"] = [None]
        opponent["active"][0]["hp"] = 10
        selected = obs["select"]["option"][self.agent(obs)[0]]
        self.assertEqual(selected["type"], self.agent.O.ATTACK)
