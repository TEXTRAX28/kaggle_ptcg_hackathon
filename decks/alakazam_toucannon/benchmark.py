"""Balanced deck/pilot ablations; the Dragapult opponent is a disclosed proxy.

Run from the root: python -m decks.alakazam_toucannon.benchmark --games 8
No training or Kaggle submission occurs. Native deals cannot be paired/seeded.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from decks.alakazam_dudunsparce.policy import AlakazamAgent
from .policy import AlakazamToucannonAgent
from pokemon_agent.agents import create_agent, default_deck
from pokemon_agent.runner import fingerprint, play_game, save_report, summarize


def evaluate(output, games, opponents):
    if output.exists():
        raise FileExistsError(output)
    before = fingerprint()
    original, candidate = default_deck("alakazam"), default_deck("alakazam_toucannon")
    variants = [("baseline", AlakazamAgent, original),
                ("deck_only", AlakazamAgent, candidate),
                ("pilot_only", AlakazamToucannonAgent, original),
                ("candidate", AlakazamToucannonAgent, candidate)]
    report = {"created_utc": datetime.now(timezone.utc).isoformat(),
              "source_sha256": before, "native_rng_seeded": False,
              "format": "independent single games, not BO3; unpaired native deals",
              "proxy_warning": "dragapult_proxy uses Dipam's list but is not his actual policy",
              "results": []}
    for opponent in opponents:
        other_deck = original if opponent == "random" else default_deck(opponent)
        for label, policy, deck in variants:
            began, rows = time.perf_counter(), []
            for number in range(games):
                seat = number % 2
                first = seat if (number // 2) % 2 == 0 else 1-seat
                settings = dict(game=number+1, agent_seat=seat, agent=label, opponent=opponent,
                                agent_deck=deck, opponent_deck=other_deck, first_player=first,
                                policy_seed=20261026+number, max_decisions=5000, decision_timeout=1)
                pilots = [None, None]
                pilots[seat], pilots[1-seat] = policy(deck), create_agent(opponent, other_deck, number)
                rows.append(play_game(settings, policies=pilots))
            result = {"variant": label, "opponent": opponent, "agent_deck": deck,
                      "opponent_deck": other_deck, "games": rows, "summary": summarize(rows),
                      "wall_seconds": time.perf_counter()-began}
            report["results"].append(result)
            save_report(output, report)
            print(label, opponent, json.dumps(result["summary"]), flush=True)
            if result["summary"]["errors"]:
                raise RuntimeError("Benchmark failed; inspect the saved error instead of counting it as a loss")
    assert fingerprint() == before, "Playing source files changed during the benchmark"
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=8)
    parser.add_argument("--opponents", nargs="+", default=["dragapult_proxy", "alakazam", "abomasnow"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.games < 4 or args.games % 4:
        parser.error("Use a positive multiple of four to balance seats and first/second")
    evaluate(args.output, args.games, args.opponents)
