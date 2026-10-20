"""Select a pilot and its matching deck for local comparisons."""
from .alakazam import AlakazamAgent
from .policy import AbomasnowAgent, RandomAgent
from .sdk import ROOT, DEFAULT_DECK, read_deck

AGENT_NAMES = ("abomasnow", "alakazam", "random")


def default_deck(name):
    if name == "alakazam":
        return read_deck(ROOT / "decks/alakazam.csv")
    if name not in AGENT_NAMES:
        raise ValueError(f"Unknown pilot: {name}")
    packaged = ROOT / "decks/abomasnow.csv"
    return read_deck(packaged if packaged.is_file() else DEFAULT_DECK)


def create_agent(name, deck=None, seed=0):
    deck = default_deck(name) if deck is None else deck
    if name == "abomasnow":
        return AbomasnowAgent(deck)
    if name == "alakazam":
        return AlakazamAgent(deck)
    if name == "random":
        return RandomAgent(deck, seed)
    raise ValueError(f"Unknown pilot: {name}")
