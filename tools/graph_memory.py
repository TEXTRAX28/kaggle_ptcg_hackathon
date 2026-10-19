"""Small local adapter: Graphify facts + append-only conversation/work records.

Run with Python -X utf8. No model call is needed to query or index new records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"
HISTORY = ROOT / "notes/history.jsonl"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def records():
    return [json.loads(line) for line in HISTORY.read_text(encoding="utf-8").splitlines() if line.strip()] if HISTORY.exists() else []


def check_records(items, knowledge_ids):
    seen = set()
    for item in items:
        for field in ("id", "date", "kind", "label", "summary", "status"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Record requires a nonempty {field}: {item.get('id')}")
        if not item["id"].startswith("memory_") or item["id"] in seen:
            raise ValueError(f"Invalid or duplicate memory ID: {item['id']}")
        seen.add(item["id"])
        if item["kind"] not in {"user_message", "assistant_message", "action", "decision", "finding"}:
            raise ValueError(f"Invalid record kind: {item['kind']}")
        if item["status"] not in {"recorded", "planned", "verified", "failed", "unresolved", "superseded"}:
            raise ValueError(f"Invalid status: {item['status']}")
        if item["status"] == "verified" and not item.get("evidence"):
            raise ValueError(f"Verified record needs evidence: {item['id']}")
        if item["kind"].endswith("_message") and item["status"] == "verified":
            raise ValueError("A message is not proof that an action succeeded; use an action record.")
        unknown = set(item.get("topics", [])) - knowledge_ids
        if unknown:
            raise ValueError(f"Unknown topic IDs: {sorted(unknown)}")


def stale_sources(index):
    stale = []
    for name, expected in index["source_hashes"].items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            stale.append(name)
    return stale


def sync():
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
    from graphify.build import build_from_json
    from graphify.cluster import score_all
    from graphify.export import to_html, to_json
    from graphify.report import generate
    from graphify.validate import assert_valid

    extraction = read_json(OUT / "knowledge.json")
    index = read_json(OUT / "index.json")
    assert_valid(extraction)
    stale = stale_sources(index)
    if stale:
        raise ValueError(f"Source changed; refresh its extraction before syncing: {stale}")
    items = records()
    ids = {n["id"] for n in extraction["nodes"]}
    check_records(items, ids)
    communities = {int(k): v for k, v in index["communities"].items()}
    labels = {int(k): v for k, v in index["labels"].items()}
    clustered_ids = [n for group in communities.values() for n in group]
    if set(clustered_ids) != ids or len(clustered_ids) != len(ids):
        raise ValueError("Knowledge nodes changed; regenerate index communities and labels.")
    core = build_from_json(extraction)
    if core.number_of_edges() != len(extraction["edges"]):
        raise ValueError("Duplicate/reverse edges would be lost in Graphify's simple graph.")
    cohesion = score_all(core, communities)
    questions = index.get("questions") or suggest_questions(core, communities, labels)
    report = generate(core, communities, cohesion, labels, god_nodes(core, top_n=3),
                      surprising_connections(core, communities, top_n=2),
                      index["corpus"], {"input": 0, "output": 0}, str(ROOT),
                      suggested_questions=questions[:2])
    report = re.sub(r"\(\d{4}-\d{2}-\d{2}\)$", f"({index['captured_on']})", report, count=1, flags=re.M)
    report = report.replace("- Token cost: 0 input · 0 output",
                            "- Token cost: unavailable; actual model usage was not exposed. No zero-cost claim.")
    # No Obsidian vault was requested; remove links to nonexistent vault files.
    report = re.sub(r"\[\[_COMMUNITY_[^|]+\|([^\]]+)\]\]", r"\1", report)

    graph = core.copy()
    previous = None
    history_ids = []
    for number, item in enumerate(items, 1):
        attrs = {k: v for k, v in item.items() if k not in {"id", "topics", "text"}}
        attrs.update(file_type="document", layer="history", source_file="notes/history.jsonl",
                     source_location=f"line {number}", captured_at=item["date"])
        graph.add_node(item["id"], **attrs)
        history_ids.append(item["id"])
        targets = [(topic, "records_topic") for topic in item.get("topics", [])]
        if previous:
            targets.append((previous, "follows_record"))
        for target, relation in targets:
            graph.add_edge(item["id"], target, relation=relation, confidence="EXTRACTED",
                           confidence_score=1.0, weight=1.0, source_file="notes/history.jsonl",
                           source_location=f"line {number}", _src=item["id"], _tgt=target)
        previous = item["id"]
    if history_ids:
        cid = max(communities, default=-1) + 1
        communities[cid] = history_ids
        labels[cid] = "Conversation and verified work"
    graph.graph.update(captured_on=index["captured_on"], community_labels=labels,
                       source_hashes=index["source_hashes"],
                       history_records=len(items),
                       verification="See each node's source and status: brief claims, inspected local code/data, research findings and proposals have different evidence.")
    # Export to a temporary path, then replace the previous complete graph.
    temp = OUT / "graph.json.tmp"
    to_json(graph, communities, str(temp))
    temp.replace(OUT / "graph.json")
    if graph.number_of_nodes() <= 5000:
        temp_html = OUT / "graph.html.tmp"
        to_html(graph, communities, str(temp_html), community_labels=labels)
        temp_html.replace(OUT / "graph.html")
    else:
        print("Over 5,000 nodes: HTML refresh skipped; JSON and report remain current.")
    report += (f"\n\n## History and provenance\n"
               f"- Full graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.\n"
               f"- {len(items)} message/work records are indexed from `notes/history.jsonl`.\n"
               "- Communities, hubs and cohesion above describe the knowledge layer. History is grouped separately to avoid distorting it.\n"
               "- EXTRACTED means the relationship appears in a saved source; it does not mean the competition claim was checked online.\n"
               "- Every successful action needs recorded evidence; messages and plans are not successful actions.\n"
               "- See `notes/CONTEXT.md` for the short project handoff and unresolved questions.\n")
    write_atomic(OUT / "GRAPH_REPORT.md", report)
    print(f"Synced: {core.number_of_nodes()} knowledge + {len(items)} history nodes; {graph.number_of_edges()} edges.")


def record(path):
    new = read_json(Path(path))
    new = new if isinstance(new, list) else [new]
    current = records()
    existing = {item["id"]: item for item in current}
    for item in new:
        if item.get("id") in existing:
            if existing[item["id"]] != item:
                raise ValueError(f"Refusing to overwrite history: {item['id']}")
        else:
            current.append(item)
            existing[item["id"]] = item
    ids = {n["id"] for n in read_json(OUT / "knowledge.json")["nodes"]}
    check_records(current, ids)
    if stale_sources(read_json(OUT / "index.json")):
        raise ValueError("Source changed; refresh knowledge before recording into the graph.")
    write_atomic(HISTORY, "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in current))
    sync()


def normalize(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))


def query(text, budget, history):
    data = read_json(OUT / "graph.json")
    stale = stale_sources(read_json(OUT / "index.json"))
    if stale:
        print(f"WARNING: stale/missing sources {stale}; verify these before relying on their nodes.")
    eligible = {n["id"]: n for n in data["nodes"] if history or n.get("layer") != "history"}
    stop = {"what", "which", "when", "where", "does", "have", "with", "about", "this", "that", "the", "and", "for", "are", "how", "can"}
    terms = set(re.findall(r"[\w.]+", normalize(text))) - stop
    scores, coverage = {}, {}
    position = {n["id"]: i for i, n in enumerate(data["nodes"])}
    for node_id, n in eligible.items():
        label = normalize(n["label"])
        body = normalize(n.get("summary", "") + " " + n.get("status", ""))
        coverage[node_id] = sum(term in label or term in body for term in terms)
        scores[node_id] = sum(3 * (term in label) + (term in body) for term in terms)
    best_coverage = max(coverage.values(), default=0)
    rank = lambda n: (-coverage[n], -scores[n], -position[n])
    seeds = sorted((n for n in eligible if scores[n] and coverage[n] == best_coverage), key=rank)[:3]
    if not seeds:
        print("No matching nodes. Consult a narrow source section and add the missing verified knowledge.")
        return
    selected = set(seeds)
    for edge in data["links"]:
        if edge["source"] in seeds and edge["target"] in eligible:
            selected.add(edge["target"])
        if edge["target"] in seeds and edge["source"] in eligible:
            selected.add(edge["source"])
    order = seeds + sorted(selected - set(seeds), key=rank)
    limit = max(200, budget * 4)  # Approximate character budget, not measured tokens.
    parts, shown = [], set()
    for node_id in order:
        n = eligible[node_id]
        part = (f"{node_id} | {n['label']} | community={n.get('community')}\n"
                f"  {n.get('summary', '')}\n"
                f"  Source: {n['source_file']}:{n.get('source_location', '?')}\n"
                f"  Status: {n.get('status', n.get('verification_status', 'see source'))}\n")
        if sum(map(len, parts)) + len(part) > limit * 0.8:
            break
        parts.append(part)
        shown.add(node_id)
    for edge in data["links"]:
        if {edge["source"], edge["target"]} <= shown:
            src, tgt = edge.get("_src", edge["source"]), edge.get("_tgt", edge["target"])
            part = f"{src} --{edge['relation']} [{edge['confidence']} {edge['confidence_score']}]--> {tgt}\n"
            if sum(map(len, parts)) + len(part) <= limit:
                parts.append(part)
    print("".join(parts), end="")
    if len(shown) < len(order):
        print("[Additional nodes omitted by approximate budget; narrow query or raise --budget.]")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sync", help="Rebuild graph/report/HTML from saved facts and history")
    add = commands.add_parser("record", help="Append JSON record(s) and update the graph immediately")
    add.add_argument("json_file")
    search = commands.add_parser("query", help="Retrieve source-linked summaries and neighboring edges")
    search.add_argument("text")
    search.add_argument("--budget", type=int, default=1200)
    search.add_argument("--history", action="store_true", help="Also search conversation/work records")
    args = parser.parse_args()
    if args.command == "sync":
        sync()
    elif args.command == "record":
        record(args.json_file)
    else:
        query(args.text, args.budget, args.history)


if __name__ == "__main__":
    main()
