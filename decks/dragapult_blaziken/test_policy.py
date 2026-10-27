"""Tactical sanity checks for the disclosed benchmark approximation."""
import unittest
from tests.helpers import card, pokemon, observation
from .policy import DragapultBenchmarkAgent


class ProxyTests(unittest.TestCase):
    def test_cage_removes_the_phantom_dive_bench_bonus(self):
        p = DragapultBenchmarkAgent()
        obs = observation([{"type": 13, "attackId": 154}])
        me, other = obs["current"]["players"]
        me["active"] = [pokemon(121, 10, 320)]
        other["bench"] = [pokemon(65, 30, 60, owner=1)]
        unprotected = p.attack_score(obs, 154)
        obs["current"]["stadium"] = [card(1264, 100)]
        self.assertGreater(unprotected, p.attack_score(obs, 154) + 1700)

    def test_typed_dragapult_energy_is_not_replaced_by_darkness(self):
        p = DragapultBenchmarkAgent()
        dragon = pokemon(121, 10, 320)
        dragon["energies"] = [2]
        self.assertGreater(p.need_energy(dragon, 5), 0)
        self.assertLess(p.need_energy(dragon, 7), 0)

    def test_counter_choice_finishes_the_small_bench_target(self):
        p = DragapultBenchmarkAgent()
        obs = observation([{"type": 3, "area": 5, "index": 0, "playerIndex": 1},
                           {"type": 3, "area": 5, "index": 1, "playerIndex": 1}], context=14)
        obs["current"]["players"][1]["bench"] = [pokemon(140, 20, 100, owner=1), pokemon(741, 21, 10, owner=1)]
        self.assertEqual(p(obs), [1])
