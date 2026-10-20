"""Alternative entry point; the Alakazam notebook packages this as main.py."""
from functools import lru_cache
from pokemon_agent.alakazam import AlakazamAgent


@lru_cache(maxsize=1)
def _policy():
    return AlakazamAgent()


def agent(obs_dict):
    return _policy()(obs_dict)
