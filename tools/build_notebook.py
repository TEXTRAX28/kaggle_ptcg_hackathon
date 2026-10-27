"""Generate a code-only Kaggle notebook from the tested Python source files.

Run from the project root: python -X utf8 tools/build_notebook.py
The notebook embeds a snapshot so importing it into Kaggle needs only the
competition data attachment, not another upload of this repository.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK_FOLDERS = ("abomasnow_kyogre", "alakazam_dudunsparce", "alakazam_toucannon", "dragapult_blaziken")


def cell(kind, source):
    result = {"cell_type": kind, "id": hashlib.sha256(source.encode()).hexdigest()[:12],
              "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def build(agent="abomasnow"):
    if agent not in ("abomasnow", "alakazam", "alakazam_toucannon"):
        raise ValueError(f"Unknown notebook pilot: {agent}")
    folder = {"alakazam": "alakazam", "alakazam_toucannon": "alakazam-toucannon"}.get(agent, "abomasnow-kyogre")
    deck_folder = {"alakazam": "alakazam_dudunsparce", "alakazam_toucannon": "alakazam_toucannon"}.get(agent, "abomasnow_kyogre")
    output = ROOT / "decks" / deck_folder / f"{deck_folder}.ipynb"
    cells = [cell("code", """from pathlib import Path
import json
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

GAMES = 20              # Use 100 or more for a larger evaluation.
AGENT = "__PILOT__"
OPPONENT = "__OPPONENT__"  # random uses the candidate deck; named pilots use their own.
POLICY_SEED = 20261017
SDK_ROOT = None         # Optional explicit path to the folder containing cg/.

local_root = Path.cwd().resolve()
local_root = next((p for p in (local_root, *local_root.parents)
                   if (p / "tools/build_notebook.py").is_file()), local_root)
on_kaggle = Path("/kaggle/working").is_dir()
WORK_DIR = Path("/kaggle/working/abomasnow-kyogre") if on_kaggle else local_root / "build/notebooks/__DECK_FOLDER__"
WORK_DIR.mkdir(parents=True, exist_ok=True)

if SDK_ROOT is None:
    input_root = Path("/kaggle/input") if on_kaggle else local_root / "the-pokemon-company-ptcg-ai-battle-challenge-playground"
    candidates = sorted({p.parent.parent for p in input_root.rglob("cg/api.py")})
    if len(candidates) != 1:
        attached = sorted(p.name for p in input_root.iterdir()) if input_root.is_dir() else []
        raise RuntimeError(
            f"Expected one supplied cg SDK under {input_root}; found {candidates}. "
            f"Visible input entries: {attached or '<none>'}. "
            "In Kaggle, use Add Input > Competition Datasets to attach "
            "The Pokemon Company - PTCG AI Battle Challenge Playground. "
            "If setting SDK_ROOT explicitly, use the folder containing cg/api.py.")
    SDK_ROOT = candidates[0]
SDK_ROOT = Path(SDK_ROOT)
if not (SDK_ROOT / "cg/api.py").is_file():
    raise FileNotFoundError(f"No cg/api.py under {SDK_ROOT}")
shutil.copytree(SDK_ROOT / "cg", WORK_DIR / "cg", dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
print(f"Workspace: {WORK_DIR}\\nSDK: {SDK_ROOT}")
""".replace("abomasnow-kyogre", folder).replace("__DECK_FOLDER__", deck_folder).replace("__PILOT__", agent)
       .replace("__OPPONENT__", "dragapult_proxy" if agent == "alakazam_toucannon" else "abomasnow" if agent == "alakazam" else "random"))]
    common = ["pokemon_agent/__init__.py", "pokemon_agent/sdk.py", "pokemon_agent/base.py",
              "pokemon_agent/random_agent.py", "pokemon_agent/agents.py", "pokemon_agent/runner.py",
              "decks/__init__.py"]
    common += [f"decks/{name}/{filename}" for name in DECK_FOLDERS
               for filename in ("__init__.py", "policy.py", "deck.csv")]
    sources = [(name, name) for name in common] + [
        (f"decks/{deck_folder}/main.py", "main.py"),
        (f"decks/{deck_folder}/deck.csv", "deck.csv")]
    embedded = []
    for source_path, relative in sources:
        source = (ROOT / source_path).read_text(encoding="utf-8")
        # A JSON-encoded string is also a valid Python string literal. This
        # avoids magic commands and handles quotes/backslashes in source safely.
        # The visible implementation is a multiline literal when safe to use.
        literal = "r'''" + source + "'''" if "'''" not in source else json.dumps(source, ensure_ascii=False)
        embedded.append(f"    {relative!r}: {literal},")
    setup = ("# Set up all agent files together; run this cell before evaluation.\n"
             "PROJECT_SOURCES = {\n" + "\n".join(embedded) + "\n}\n\n"
             "def prepare_workspace():\n"
             "    for relative, source in PROJECT_SOURCES.items():\n"
             "        destination = WORK_DIR / relative\n"
             "        destination.parent.mkdir(parents=True, exist_ok=True)\n"
             "        destination.write_text(source, encoding='utf-8', newline='\\n')\n\n"
             "prepare_workspace()\n"
             "print(f'Prepared {len(PROJECT_SOURCES)} agent files, including pokemon_agent/sdk.py')\n")
    cells.append(cell("code", setup))
    cells += [cell("code", """if "prepare_workspace" not in globals():
    raise RuntimeError("Run the agent-file setup cell above first, or choose Run All.")
prepare_workspace()
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
REPORT_PATH = WORK_DIR / "results" / f"notebook-{stamp}.json"
command = [sys.executable, "-X", "utf8", "-m", "pokemon_agent.runner",
           "--agent", AGENT, "--opponent", OPPONENT,
           "--games", str(GAMES), "--seed", str(POLICY_SEED),
           "--game-timeout", "30", "--decision-timeout", "1",
           "--output", str(REPORT_PATH)]
subprocess.run(command, cwd=WORK_DIR, check=True)
report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
print(json.dumps(report["summary"], indent=2))
"""), cell("code", """if "prepare_workspace" not in globals():
    raise RuntimeError("Run the agent-file setup cell above first, or choose Run All.")
prepare_workspace()
linux_library = WORK_DIR / "cg/libcg.so"
if not linux_library.is_file():
    raise FileNotFoundError("The supplied x86-64 Linux library cg/libcg.so is missing")
members = [WORK_DIR / relative for relative in sorted(PROJECT_SOURCES)] + [linux_library]
members += sorted((WORK_DIR / "cg").glob("*.py"))
ARCHIVE_PATH = WORK_DIR / "submission.tar.gz"
with tarfile.open(ARCHIVE_PATH, "w:gz") as archive:
    for path in members:
        archive.add(path, arcname=path.relative_to(WORK_DIR).as_posix())
print(f"Submission bundle: {ARCHIVE_PATH} ({ARCHIVE_PATH.stat().st_size / 1024**2:.2f} MiB)")
print(f"Benchmark report: {REPORT_PATH}")
""")]
    notebook = {"cells": cells,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                             "language_info": {"name": "python", "version": "3.10"}},
                "nbformat": 4, "nbformat_minor": 5}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {output}: {len(cells)} cells, no saved outputs")
    return notebook


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("abomasnow", "alakazam", "alakazam_toucannon"), default="abomasnow")
    build(parser.parse_args().agent)
