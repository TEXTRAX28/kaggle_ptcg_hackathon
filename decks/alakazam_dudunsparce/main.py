"""Alakazam/Dudunsparce entry point, packaged as root main.py for Kaggle."""
from functools import lru_cache
from decks.alakazam_dudunsparce.policy import AlakazamAgent


@lru_cache(maxsize=1)
def _policy():
    return AlakazamAgent()


def agent(obs_dict):
    return _policy()(obs_dict)
