"""Behavioral checks for the pilot and failures that could corrupt evaluation."""
import copy
import importlib.util
import random
from pathlib import Path
import tempfile
import unittest

from pokemon_agent.policy import AbomasnowAgent, RandomAgent
from pokemon_agent.runner import play_game, run_isolated, summarize, wilson_interval
from pokemon_agent.sdk import SAMPLE, read_deck, validate_selection


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


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AbomasnowAgent()

    def test_entry_point_returns_original_sixty_card_deck(self):
        from main import agent
        self.assertEqual(agent({"select": None}), read_deck(SAMPLE / "deck.csv"))
        self.assertEqual(len(agent({"select": None})), 60)

    def test_random_matches_supplied_random_policy(self):
        spec = importlib.util.spec_from_file_location("supplied_random", SAMPLE / "main.py")
        supplied = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(supplied)
        obs = observation([{"type": 3, "area": 6, "index": i, "playerIndex": 0} for i in range(6)],
                          context=7, minimum=0, maximum=3)
        state = random.getstate()
        try:
            random.seed(73)
            expected = supplied.agent(obs)
        finally:
            random.setstate(state)
        self.assertEqual(RandomAgent(seed=73)(obs), expected)

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

    def test_reject_bad_counts_duplicate_indices_bool_and_bounds(self):
        obs = observation([{"type": 14}, {"type": 14}], maximum=2)
        for action in ([], [0, 0], [True], [-1], [2], [0, 1, 0], "0"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                validate_selection(obs, action)

    def test_deck_reader_rejects_silent_truncation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deck.csv"
            path.write_text("3\n" * 61, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_deck(path)


class RunnerTests(unittest.TestCase):
    def test_illegal_policy_is_failure_then_engine_is_reusable(self):
        broken = lambda obs: [999999]
        result = play_game(config(), policies=[broken, broken])
        self.assertEqual(result["status"], "illegal_action")
        self.assertNotIn("outcome", result)
        self.assertEqual(play_game(config())["status"], "completed")

    def test_decision_limit_is_not_a_win(self):
        limited = dict(config(), max_decisions=1)
        result = play_game(limited)
        self.assertEqual(result["status"], "decision_limit")
        self.assertNotIn("outcome", result)

    def test_hung_worker_deadline_is_recorded(self):
        self.assertEqual(run_isolated(config(), 0.00001)["status"], "timeout")

    def test_all_seats_and_start_orders_complete(self):
        for seat in (0, 1):
            for first in (0, 1):
                with self.subTest(seat=seat, first=first):
                    result = play_game(dict(config(), agent_seat=seat, first_player=first))
                    self.assertEqual(result["status"], "completed", result.get("error"))
                    self.assertEqual(result["first_player"], first)
                    self.assertIn(result["winner"], (0, 1, 2))

    def test_summary_does_not_turn_errors_into_wins(self):
        base = {"status": "completed", "agent_seat": 0, "first_player": 0, "decisions": [10, 10],
                "policy_seconds": [0.1, 0.1], "max_policy_seconds": [0.01, 0.01], "wall_seconds": 1}
        games = [dict(base, outcome=o) for o in ("win", "loss", "draw")]
        games.append({"status": "timeout"})
        summary = summarize(games)
        self.assertEqual(summary["completed"], 3)
        self.assertEqual(summary["attempted"], 4)
        self.assertEqual(summary["win_rate"], 1 / 3)
        self.assertEqual(summary["errors"], {"timeout": 1})
        self.assertIsNone(wilson_interval(0, 0))


if __name__ == "__main__":
    unittest.main()
