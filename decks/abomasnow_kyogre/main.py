"""Competition-style Python entry point for the local heuristic agent."""
from functools import lru_cache
from decks.abomasnow_kyogre.policy import AbomasnowAgent


@lru_cache(maxsize=1)
def _policy():
    return AbomasnowAgent()


def agent(obs_dict):
    return _policy()(obs_dict)
