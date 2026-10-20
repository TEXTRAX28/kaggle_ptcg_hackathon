"""Check the indexing and data boundaries that can invalidate replay conclusions."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.analyze_replays import analyze, decisions


class ReplayAnalysisTests(unittest.TestCase):
    def test_action_answers_previous_active_observation(self):
        before = {"select": {"context": 0}}
        stale = {"select": {"context": 99}}
        data = {"steps": [[{"status": "ACTIVE", "observation": before, "action": []}],
                          [{"status": "INACTIVE", "observation": stale, "action": [2]}],
                          [{"status": "DONE", "observation": stale, "action": []}]]}
        self.assertEqual(list(decisions(data, 0)), [(1, before, [2])])

    def test_execution_logs_are_rejected_before_any_gameplay_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "logs.json"
            path.write_text(json.dumps([[{"duration": 0.001, "stdout": "", "stderr": ""}]]))
            with self.assertRaisesRegex(ValueError, "full replay"):
                analyze(path, "Player")

    def test_incomplete_replay_is_not_counted_as_a_finished_match(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "replay.json"
            path.write_text(json.dumps({"steps": [[{}]], "info": {"TeamNames": ["Other", "Player"]},
                                        "statuses": ["DONE", "ERROR"]}))
            with self.assertRaisesRegex(ValueError, "incomplete/error"):
                analyze(path, "Player")


if __name__ == "__main__":
    unittest.main()
