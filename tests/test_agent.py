"""Shared selection validation, random baseline and runner checks."""
import importlib.util
import random
from pathlib import Path
import tempfile
import unittest

from pokemon_agent.agents import create_agent, default_deck
from pokemon_agent.random_agent import RandomAgent
from pokemon_agent.runner import play_game, run_isolated, summarize, wilson_interval
from pokemon_agent.sdk import SAMPLE, read_deck, validate_selection
from tests.helpers import observation, config


class CommonTests(unittest.TestCase):
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

    def test_factory_preserves_both_distinct_decks(self):
        self.assertNotEqual(default_deck("alakazam"), default_deck("abomasnow"))
        self.assertEqual(create_agent("alakazam").deck, default_deck("alakazam"))
        with self.assertRaises(ValueError):
            create_agent("unknown")


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
