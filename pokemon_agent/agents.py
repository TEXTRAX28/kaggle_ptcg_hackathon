"""Shared registry selecting each deck's pilot and matching card list."""
from decks.abomasnow_kyogre.policy import AbomasnowAgent
from decks.alakazam_dudunsparce.policy import AlakazamAgent
from .random_agent import RandomAgent
from .sdk import ROOT, read_deck

AGENT_NAMES = ("abomasnow", "alakazam", "random")


def default_deck(name):
    if name not in AGENT_NAMES:
        raise ValueError(f"Unknown pilot: {name}")
    folder = "alakazam_dudunsparce" if name == "alakazam" else "abomasnow_kyogre"
    return read_deck(ROOT / "decks" / folder / "deck.csv")


def create_agent(name, deck=None, seed=0):
    deck = default_deck(name) if deck is None else deck
    if name == "abomasnow":
        return AbomasnowAgent(deck)
    if name == "alakazam":
        return AlakazamAgent(deck)
    if name == "random":
        return RandomAgent(deck, seed)
    raise ValueError(f"Unknown pilot: {name}")
