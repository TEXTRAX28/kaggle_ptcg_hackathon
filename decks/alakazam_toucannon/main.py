"""Experimental Alakazam/Toucannon Kaggle entry point."""
from functools import lru_cache
from decks.alakazam_toucannon.policy import AlakazamToucannonAgent


@lru_cache(maxsize=1)
def _policy():
    return AlakazamToucannonAgent()


def agent(obs_dict):
    return _policy()(obs_dict)
