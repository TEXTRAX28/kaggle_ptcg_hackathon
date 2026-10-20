"""Run isolated local games and save results; no Kaggle service is contacted.

Example: python -m pokemon_agent.runner --games 100 --output results/baseline.json
The seed controls policy randomness only: the supplied native API seeds its own
shuffles/coins and does not expose a seed argument.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

from .sdk import ROOT, load_sdk, read_deck, validate_selection


def play_game(config, policies=None):
    """Play to an engine result, rejecting illegal output and bounding decisions."""
    from .agents import create_agent

    api, game = load_sdk()
    seat = config["agent_seat"]
    decks = [None, None]
    decks[seat], decks[1 - seat] = config["agent_deck"], config["opponent_deck"]
    if policies is None:
        policies = [None, None]
        for player, name in ((seat, config["agent"]), (1 - seat, config["opponent"])):
            policies[player] = create_agent(name, decks[player], config["policy_seed"] + player)
    result = {"game": config["game"], "agent_seat": seat, "policy_seed": config["policy_seed"],
              "scheduled_first_player": config["first_player"], "status": "error",
              "decisions": [0, 0], "policy_seconds": [0.0, 0.0],
              "max_policy_seconds": [0.0, 0.0]}
    counts = [Counter(), Counter()]
    observation, action, started, trace = None, None, False, None
    began = time.perf_counter()
    try:
        if config.get("trace_file"):
            path = Path(config["trace_file"])
            path.parent.mkdir(parents=True, exist_ok=True)
            trace = path.open("x", encoding="utf-8")
        observation, start = game.battle_start(*decks)
        started = bool(start.battlePtr)
        if observation is None:
            raise ValueError(f"Native deck rejection: player={start.errorPlayer}, type={start.errorType}")
        for step in range(config["max_decisions"]):
            state = observation["current"]
            result.update(turns=state["turn"], first_player=state["firstPlayer"],
                          native_round=state.get("round", 1))
            if state["result"] != -1:
                winner = state["result"]
                if winner not in (0, 1, 2):
                    raise ValueError(f"Unexpected native result {winner}")
                logs = [log for log in observation["logs"] if log["type"] == api.LogType.RESULT]
                result.update(status="completed", winner=winner,
                              outcome="draw" if winner == 2 else "win" if winner == seat else "loss",
                              finish_reason=logs[-1].get("reason") if logs else None)
                if trace:
                    trace.write(json.dumps({"event": "result", "winner": winner,
                                            "observation": {k: v for k, v in observation.items() if k != "search_begin_input"}},
                                           ensure_ascii=False) + "\n")
                break
            select = observation["select"]
            player = state["yourIndex"]
            before = time.perf_counter()
            if select["context"] == api.SelectContext.IS_FIRST:
                # Control first/second independently of seat for fair comparison.
                desired = api.OptionType.YES if player == config["first_player"] else api.OptionType.NO
                action = [next(i for i, option in enumerate(select["option"]) if option["type"] == desired)]
            else:
                action = policies[player](observation)
            elapsed = time.perf_counter() - before
            result["policy_seconds"][player] += elapsed
            result["max_policy_seconds"][player] = max(result["max_policy_seconds"][player], elapsed)
            result["decisions"][player] += 1
            if elapsed > config["decision_timeout"]:
                result["status"] = "timeout"
                raise TimeoutError(f"Player {player} decision exceeded {config['decision_timeout']} seconds")
            try:
                validate_selection(observation, action)
            except ValueError:
                result["status"] = "illegal_action"
                raise
            counts[player][api.SelectContext(select["context"]).name] += 1
            if trace:
                visible = {k: v for k, v in observation.items() if k != "search_begin_input"}
                trace.write(json.dumps({"step": step, "observation": visible, "action": action}, ensure_ascii=False) + "\n")
                trace.flush()
            try:
                observation = game.battle_select(action)
            except IndexError:
                result["status"] = "illegal_action"
                raise
        else:
            # A terminal result produced by the last allowed action still counts.
            state = observation["current"]
            if state["result"] in (0, 1, 2):
                winner = state["result"]
                result.update(status="completed", winner=winner, turns=state["turn"],
                              outcome="draw" if winner == 2 else "win" if winner == seat else "loss")
            else:
                result.update(status="decision_limit", error=f"Exceeded {config['max_decisions']} decisions")
    except Exception as error:
        result.update(error=f"{type(error).__name__}: {error}", traceback=traceback.format_exc())
        if observation:
            result["last_observation"] = {k: v for k, v in observation.items() if k != "search_begin_input"}
            result["last_action"] = action
    finally:
        if started:
            game.battle_finish()
        if trace:
            trace.close()
    result["wall_seconds"] = time.perf_counter() - began
    result["selection_contexts"] = [dict(c) for c in counts]
    return result


def run_isolated(config, timeout):
    """Terminate a hung/crashed native game without losing previous results."""
    try:
        worker = subprocess.run([sys.executable, "-X", "utf8", "-m", "pokemon_agent.runner", "--worker"],
                                input=json.dumps(config), capture_output=True, text=True,
                                encoding="utf-8", cwd=ROOT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"game": config["game"], "agent_seat": config["agent_seat"],
                "status": "timeout", "error": f"Game worker exceeded {timeout} seconds"}
    if worker.returncode:
        return {"game": config["game"], "agent_seat": config["agent_seat"],
                "status": "worker_error", "error": worker.stderr[-8000:], "returncode": worker.returncode}
    try:
        return json.loads(worker.stdout)
    except json.JSONDecodeError:
        return {"game": config["game"], "agent_seat": config["agent_seat"],
                "status": "worker_error", "error": "Worker did not return JSON", "stdout": worker.stdout[-2000:]}


def wilson_interval(wins, total):
    if not total:
        return None
    z = 1.959963984540054
    p = wins / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - margin), min(1, center + margin)]


def summarize(games):
    completed = [g for g in games if g["status"] == "completed"]
    outcomes = Counter(g["outcome"] for g in completed)
    total = len(completed)
    errors = Counter(g["status"] for g in games if g["status"] != "completed")

    def split(key):
        bins = {}
        for g in completed:
            value = str(g["agent_seat"]) if key == "seat" else "first" if g["first_player"] == g["agent_seat"] else "second"
            bucket = bins.setdefault(value, {"games": 0, "wins": 0, "losses": 0, "draws": 0})
            bucket["games"] += 1
            bucket[{"win": "wins", "loss": "losses", "draw": "draws"}[g["outcome"]]] += 1
        return bins

    decisions = sum(g["decisions"][g["agent_seat"]] for g in completed)
    seconds = sum(g["policy_seconds"][g["agent_seat"]] for g in completed)
    return {"attempted": len(games), "completed": total,
            "wins": outcomes["win"], "losses": outcomes["loss"], "draws": outcomes["draw"],
            "errors": dict(errors), "win_rate": outcomes["win"] / total if total else None,
            "win_rate_95pct_wilson": wilson_interval(outcomes["win"], total),
            "by_seat": split("seat"), "by_start_order": split("order"),
            "agent_decisions": decisions,
            "agent_mean_decision_ms": 1000 * seconds / decisions if decisions else None,
            "agent_max_decision_ms": 1000 * max((g["max_policy_seconds"][g["agent_seat"]] for g in completed), default=0),
            "mean_game_seconds": sum(g["wall_seconds"] for g in completed) / total if total else None}


def fingerprint():
    """Identify the exact code and native library used for this run."""
    import importlib
    load_sdk()
    sim = importlib.import_module("cg.sim")
    files = [ROOT / "main.py", ROOT / "deck.csv", *sorted((ROOT / "pokemon_agent").glob("*.py")),
             *sorted((ROOT / "decks").glob("*.csv")), Path(sim.lib_path)]
    if (ROOT / "main_alakazam.py").is_file():
        files.append(ROOT / "main_alakazam.py")
    return {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def save_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main():
    from .agents import AGENT_NAMES, default_deck
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--agent", choices=AGENT_NAMES, default="abomasnow")
    parser.add_argument("--opponent", choices=AGENT_NAMES, default="random")
    parser.add_argument("--agent-deck", type=Path, default=None)
    parser.add_argument("--opponent-deck", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42, help="Policy RNG seed; native deals remain unseeded")
    parser.add_argument("--game-timeout", type=float, default=30)
    parser.add_argument("--decision-timeout", type=float, default=1)
    parser.add_argument("--max-decisions", type=int, default=5000)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--trace-dir", type=Path, help="Optional per-decision visible observations as JSONL")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(play_game(json.load(sys.stdin)), ensure_ascii=False))
        return 0
    if args.games < 1 or args.max_decisions < 1 or args.game_timeout <= 0 or args.decision_timeout <= 0:
        parser.error("Game counts, decision counts and time limits must be positive")
    now = datetime.now(timezone.utc)
    output = args.output or ROOT / "results" / f"{now:%Y%m%dT%H%M%S%fZ}-{args.agent}-vs-{args.opponent}.json"
    if output.exists():
        parser.error(f"Refusing to overwrite existing results: {output}")
    deck = read_deck(args.agent_deck) if args.agent_deck else default_deck(args.agent)
    opponent_deck = (read_deck(args.opponent_deck) if args.opponent_deck else
                     list(deck) if args.opponent == "random" else default_deck(args.opponent))
    report = {"schema_version": 1, "started_utc": now.isoformat(), "run_status": "running",
              "agent": args.agent, "opponent": args.opponent, "requested_games": args.games,
              "agent_deck": deck, "opponent_deck": opponent_deck, "policy_seed": args.seed,
              "native_rng_seeded": False, "format": "independent single games, not BO3",
              "start_order": "Four-game cycle balances both seats and first/second; IS_FIRST is controlled by runner",
              "limits": {"game_timeout_seconds": args.game_timeout, "decision_timeout_seconds": args.decision_timeout,
                         "max_decisions": args.max_decisions},
              "python": sys.version, "platform": platform.platform(), "source_sha256": fingerprint(), "games": []}
    save_report(output, report)
    for number in range(args.games):
        seat = number % 2
        first = seat if (number // 2) % 2 == 0 else 1 - seat
        config = {"game": number + 1, "agent": args.agent, "opponent": args.opponent,
                  "agent_seat": seat, "first_player": first, "policy_seed": args.seed + 2 * number,
                  "agent_deck": deck, "opponent_deck": opponent_deck,
                  "max_decisions": args.max_decisions, "decision_timeout": args.decision_timeout,
                  "trace_file": str((args.trace_dir / f"game-{number + 1:04d}.jsonl").resolve()) if args.trace_dir else None}
        result = run_isolated(config, args.game_timeout)
        report["games"].append(result)
        report["summary"] = summarize(report["games"])
        save_report(output, report)
        print(f"{number + 1}/{args.games}: {result.get('outcome', result['status'])}, seat {seat}, "
              f"first {'agent' if seat == first else 'opponent'}", flush=True)
    report["run_status"] = "complete" if not report["summary"]["errors"] else "completed_with_errors"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save_report(output, report)
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved {output.resolve()}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
