"""Random baseline usable with any supplied deck."""
import random

from .sdk import read_deck


class RandomAgent:
    """The supplied baseline's algorithm: sample exactly maxCount options."""

    def __init__(self, deck=None, seed=0):
        self.deck = list(deck) if deck is not None else read_deck()
        self.rng = random.Random(seed)

    def __call__(self, obs):
        if obs.get("select") is None:
            return list(self.deck)
        select = obs["select"]
        return self.rng.sample(range(len(select["option"])), select["maxCount"])
