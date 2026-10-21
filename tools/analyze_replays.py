"""Audit Kaggle gameplay replays without feeding spectator data to the policy.

Run: python -m tools.analyze_replays FILE... --player NAME --output results/audit.json
Execution-log downloads are rejected because they cannot explain gameplay.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from pokemon_agent.agents import create_agent
from pokemon_agent.sdk import load_sdk, validate_selection


def decisions(data, seat):
    """An action at steps[t] answers the ACTIVE observation at steps[t-1]."""
    for index in range(1, len(data["steps"])):
        before = data["steps"][index - 1][seat]
        if before["status"] == "ACTIVE":
            yield index, before["observation"], data["steps"][index][seat]["action"]


def describe(agent, obs, option):
    text = agent.O(option["type"]).name
    if option["type"] == agent.O.ATTACK:
        return text + " " + agent.attacks[option["attackId"]].name
    card = agent.resolve(obs, option)
    if card:
        text += " " + agent.cards[card["id"]].name
    if "inPlayIndex" in option:
        target = agent.target(obs, option)
        if target:
            text += f" -> {agent.cards[target['id']].name}#{target['serial']}"
    return text


def analyze(path, player, agent=None):
    path = Path(path)
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict) or not data.get("steps"):
        raise ValueError(f"{path.name}: need a full replay with steps, not agent execution logs")
    names = data["info"]["TeamNames"]
    if len(names) != 2 or names.count(player) != 1:
        raise ValueError(f"{path.name}: player name must identify exactly one of two seats")
    seat = names.index(player)
    if data["statuses"] != ["DONE", "DONE"]:
        raise ValueError(f"{path.name}: incomplete/error replay; do not treat it as a completed game")
    agent = agent or create_agent("abomasnow")
    api, _ = load_sdk()
    rounds, contexts, changes, main_decisions = {}, Counter(), [], []
    calls = list(decisions(data, seat))
    deck = calls[0][2]
    compare = Counter(deck) == Counter(agent.deck)
    for index, obs, action in calls:
        if obs.get("select") is None:
            continue
        validate_selection(obs, action)
        state, select = obs["current"], obs["select"]
        context = api.SelectContext(select["context"]).name
        contexts[context] += 1
        # Only the actual agent observation is evaluated, never visualize.current.
        visible = {k: v for k, v in obs.items() if k != "search_begin_input"}
        proposed = agent(visible) if compare else None
        entry = {"action_step": index, "observation_pointer": f"/steps/{index-1}/{seat}/observation",
                 "round": state["round"], "turn": state["turn"], "context": context,
                 "recorded": action, "proposed": proposed}
        if proposed is not None and proposed != action:
            entry["recorded_description"] = [describe(agent, obs, select["option"][i]) for i in action]
            entry["proposed_description"] = [describe(agent, obs, select["option"][i]) for i in proposed]
            changes.append(dict(entry))
        if context == "MAIN":
            me, opponent = agent.players(obs)
            def board(p):
                return [{"card": agent.cards[x["id"]].name, "hp": x["hp"],
                         "energy_count": len(x["energies"])} for x in agent.field(p)]
            entry.update(recorded_description=[describe(agent, obs, select["option"][i]) for i in action],
                         own_board=board(me), opponent_board=board(opponent),
                         prizes=[len(me["prize"]), len(opponent["prize"])],
                         own_deck=me["deckCount"], opponent_hand_count=opponent["handCount"])
            main_decisions.append(entry)
    # In these downloads the full event stream lives in the initial visualize list.
    # Its obs contains correct BO3 round numbers; renderer current can retain round=1.
    events = data["steps"][0][0].get("visualize", [])
    for index, event in enumerate(events):
        state = (event.get("obs") or {}).get("current")
        if not state:
            continue
        number = state["round"]
        row = rounds.setdefault(number, {"round": number, "first_player": None,
            "final_turn": 0, "attacks": [Counter(), Counter()], "results": [],
            "counter_hits_on_agent": [], "mulligans": [0, 0], "minimum_own_deck": 60,
            "maximum_opponent_hand": 0})
        if state["firstPlayer"] != -1:
            row["first_player"] = state["firstPlayer"]
        row["final_turn"] = max(row["final_turn"], state["turn"])
        row["minimum_own_deck"] = min(row["minimum_own_deck"], state["players"][seat]["deckCount"])
        row["maximum_opponent_hand"] = max(row["maximum_opponent_hand"], state["players"][1-seat]["handCount"])
        for log in event.get("logs", []):
            kind = log["type"]
            if kind == "Attack":
                row["attacks"][log["playerIndex"]][agent.attacks[log["attackId"]].name] += 1
            elif kind == "HasBasicPokemon" and not log["hasBasicPokemon"]:
                row["mulligans"][log["playerIndex"]] += 1
            elif kind == "HpChange" and log.get("putDamageCounter") and log["playerIndex"] == seat:
                row["counter_hits_on_agent"].append({"visualizer_index": index, "turn": state["turn"],
                    "card": agent.cards[log["cardId"]].name, "counters_hp": -log["value"]})
            elif kind == "Result":
                row["results"].append({"visualizer_index": index, "winner": log["result"], "reason": log["reason"]})
    rewards = data["rewards"]
    outcome = "win" if rewards[seat] > rewards[1-seat] else "loss" if rewards[seat] < rewards[1-seat] else "draw"
    return {"file": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "episode_id": data["info"]["EpisodeId"], "players": names, "agent_seat": seat,
            "outcome": outcome, "rewards": rewards, "configuration": data["configuration"],
            "recorded_calls_including_deck": len(calls), "contexts": dict(contexts),
            "rounds": list(rounds.values()), "main_decisions": main_decisions,
            "compared_with_current_policy": compare, "policy_changes_on_recorded_positions": changes,
            "comparison_policy": type(agent).__name__,
            "opponent_deck": dict(Counter(agent.cards[cid].name for cid in data["steps"][1][1-seat]["action"])),
            "limitations": ["Changed choices are offline position checks, not replayed wins.",
                            "No submitted source fingerprint is included in the replay.",
                            "The policy never receives spectator hands/deck order."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--player", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--policy", choices=("abomasnow", "alakazam"), default="abomasnow")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new report path")
    reports = [analyze(path, args.player, create_agent(args.policy)) for path in args.files]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for report in reports:
        print(f"{report['episode_id']}: {report['outcome']}, {len(report['rounds'])} rounds, "
              f"{len(report['policy_changes_on_recorded_positions'])} changed choices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
