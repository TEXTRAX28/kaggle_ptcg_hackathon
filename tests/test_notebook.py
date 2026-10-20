"""Regressions for incomplete Kaggle notebook file setup."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import build_notebook


class NotebookSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Inspect newly generated cells without replacing either user notebook.
        with patch.object(Path, "write_text", return_value=0), redirect_stdout(io.StringIO()):
            cls.notebooks = {pilot: build_notebook.build(pilot)
                             for pilot in ("abomasnow", "alakazam")}

    def test_evaluation_repairs_missing_sdk_before_fresh_python_import(self):
        for pilot, notebook in self.notebooks.items():
            with self.subTest(pilot=pilot), tempfile.TemporaryDirectory(prefix="ptcg-setup-test-") as temp:
                work = Path(temp)
                code = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
                namespace = {"WORK_DIR": work}
                with redirect_stdout(io.StringIO()):
                    exec(next(c for c in code if "PROJECT_SOURCES = {" in c), namespace)
                helper = work / "pokemon_agent/sdk.py"
                expected = helper.read_bytes()
                helper.unlink()
                calls = []

                def probe(command, cwd, check):
                    # Exercise real imports in the same fresh-process context as
                    # the benchmark. No native engine or game is needed for help.
                    result = subprocess.run(
                        [sys.executable, "-X", "utf8", "-m", "pokemon_agent.runner", "--help"],
                        cwd=cwd, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(helper.read_bytes(), expected)
                    calls.append(command)
                    report = namespace["REPORT_PATH"]
                    report.parent.mkdir(parents=True, exist_ok=True)
                    report.write_text(json.dumps({"summary": {"import_check": "passed"}}),
                                      encoding="utf-8")

                namespace.update(datetime=datetime, timezone=timezone, json=json, sys=sys,
                                 subprocess=SimpleNamespace(run=probe), GAMES=4, AGENT=pilot,
                                 OPPONENT="random", POLICY_SEED=42)
                with redirect_stdout(io.StringIO()):
                    exec(next(c for c in code if "subprocess.run(command" in c), namespace)
                self.assertEqual(len(calls), 1)
                self.assertIn(pilot, calls[0])

    def test_evaluation_and_packaging_require_setup_with_clear_instruction(self):
        for pilot, notebook in self.notebooks.items():
            for cell in notebook["cells"]:
                text = "".join(cell["source"])
                if cell["cell_type"] == "code" and (
                        "subprocess.run(command" in text or 'linux_library = WORK_DIR' in text):
                    with self.subTest(pilot=pilot, cell=cell["id"]):
                        with self.assertRaisesRegex(RuntimeError, "setup cell.*Run All"):
                            exec(text, {})


if __name__ == "__main__":
    unittest.main()
