"""Locate the supplied SDK without changing the downloaded competition files."""
from functools import lru_cache
import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "the-pokemon-company-ptcg-ai-battle-challenge-playground"
          / "sample_submission/sample_submission/sample_submission")
DEFAULT_DECK = ROOT / "decks/abomasnow_kyogre/deck.csv"


def read_deck(path=DEFAULT_DECK):
    """Read exactly 60 integer card IDs; native battle_start checks legality."""
    rows = Path(path).read_text(encoding="utf-8-sig").splitlines()
    if len(rows) != 60 or any(not row.strip() for row in rows):
        raise ValueError(f"{path}: expected exactly 60 nonempty card-ID rows")
    try:
        return [int(row) for row in rows]
    except ValueError as error:
        raise ValueError(f"{path}: every row must be an integer card ID") from error


@lru_cache(maxsize=1)
def load_sdk():
    """Prefer a packaged cg/ beside main.py, otherwise use the supplied sample."""
    base = ROOT if (ROOT / "cg/api.py").is_file() else SAMPLE
    if not (base / "cg/api.py").is_file():
        raise FileNotFoundError(f"Supplied SDK not found under {base}")
    # Do not put the vendor directory ahead of this project's main.py.
    # Both the sample and our agent use that filename.
    if str(base) not in sys.path:
        sys.path.append(str(base))
    return importlib.import_module("cg.api"), importlib.import_module("cg.game")


@lru_cache(maxsize=1)
def metadata():
    api, _ = load_sdk()
    return ({c.cardId: c for c in api.all_card_data()},
            {a.attackId: a for a in api.all_attack()})


def validate_selection(observation, action):
    """Reject invalid policies instead of silently repairing their output."""
    select = observation["select"]
    if not isinstance(action, list) or any(type(i) is not int for i in action):
        raise ValueError("Policy must return list[int] (booleans are not indices)")
    if not select["minCount"] <= len(action) <= select["maxCount"]:
        raise ValueError("Selection count is outside minCount/maxCount")
    if len(set(action)) != len(action):
        raise ValueError("Duplicate option indices")
    if any(i < 0 or i >= len(select["option"]) for i in action):
        raise ValueError("Option index out of range")
