"""Shared registry selecting each deck's pilot and matching card list."""
from decks.abomasnow_kyogre.policy import AbomasnowAgent
from decks.alakazam_dudunsparce.policy import AlakazamAgent
from decks.alakazam_toucannon.policy import AlakazamToucannonAgent
from decks.dragapult_blaziken.policy import DragapultBenchmarkAgent
from .random_agent import RandomAgent
from .sdk import ROOT, read_deck

AGENT_NAMES = ("abomasnow", "alakazam", "alakazam_toucannon", "dragapult_proxy", "random")


def default_deck(name):
    if name not in AGENT_NAMES:
        raise ValueError(f"Unknown pilot: {name}")
    folder = {"alakazam": "alakazam_dudunsparce", "alakazam_toucannon": "alakazam_toucannon",
              "dragapult_proxy": "dragapult_blaziken"}.get(name, "abomasnow_kyogre")
    return read_deck(ROOT / "decks" / folder / "deck.csv")


def create_agent(name, deck=None, seed=0):
    deck = default_deck(name) if deck is None else deck
    if name == "abomasnow":
        return AbomasnowAgent(deck)
    if name == "alakazam":
        return AlakazamAgent(deck)
    if name == "alakazam_toucannon":
        return AlakazamToucannonAgent(deck)
    if name == "dragapult_proxy":
        return DragapultBenchmarkAgent(deck)
    if name == "random":
        return RandomAgent(deck, seed)
    raise ValueError(f"Unknown pilot: {name}")
