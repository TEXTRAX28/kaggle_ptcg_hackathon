# Project memory: Pokémon TCG challenge

The user requested a persistent Graphify graph and a node for each user/assistant
message and each successful action. Apply this workflow on every turn in this
project, including after context compaction or in a new chat using this folder.

## Read before work

- Follow any applicable parent/global graph lookup requirements, then read
  `notes/CONTEXT.md` for this project's short handoff.
- Query the local graph for relevant facts, relationships, decisions and outcomes:
  `python -X utf8 tools/graph_memory.py query "submission requirements" --budget 1200`
- Add `--history` for previous conversations, actions and decisions.
- Use graph node `source_file` and `source_location` for citations. Read only
  the necessary source passage when a fact is missing, unclear, stale or being
  changed. The graph does not replace checking current code before edits.
- Read `graphify-out/GRAPH_REPORT.md` for communities, confidence and open issues.
  Do not load the entire graph or all transcripts into model context by default.
- Competition dates, limits and rules are a user-supplied snapshot captured on
  2026-10-16. Check live official sources before decisions that depend on them.
  A reference URL in the graph does not mean its contents were read.

## Record every turn

Before sending the final response, append concise records for all user-visible
user and assistant messages in the turn (including progress updates and the
prepared final reply), plus the actions completed successfully. Summaries must
preserve requests, answers, constraints, decisions, results and unresolved issues.
Do not copy hidden reasoning, system/developer text, secrets or raw tool dumps.
Keep each message as its own record; batch related low-level tool operations into
an action record with enough evidence to say what actually succeeded.

Write a temporary UTF-8 JSON object/array with these fields, then run:

`python -X utf8 tools/graph_memory.py record path/to/records.json`

- `id`: unique stable ID beginning `memory_`; reuse the same ID on retries.
- `date`: current user-facing date, `YYYY-MM-DD`.
- `kind`: `user_message`, `assistant_message`, `action`, `decision`, or `finding`.
- `label`, `summary`: short title and self-contained useful summary.
- `status`: `recorded`, `planned`, `verified`, `failed`, `unresolved`, or `superseded`.
- `topics`: list of relevant existing knowledge node IDs (may be empty).
- `evidence`: successful actions require concrete command outcomes, source
  locations, artifacts or test results. Plans and messages are not proof of success.
- Optional `text`: exact user/assistant text when wording matters.

`record` appends to `notes/history.jsonl` and immediately puts each record into
`graphify-out/graph.json` with topic and chronological edges. Repeating identical
IDs is safe; conflicting replacements fail. Add correction records rather than
rewriting past events. Keep `notes/CONTEXT.md` short and update it when the current
state, a durable decision or an unresolved issue changes. Only the primary agent
writes history; subagents return evidence to the primary agent.

This is an agent-maintained workflow, not a background listener. If recording
fails, report the failure and repair it; do not claim memory was saved. A prepared
final reply record documents the reply text, not independently confirmed delivery.

## Updating facts

- `raw/pokemon-challenge-playground.txt` is the preserved pasted brief.
- `graphify-out/knowledge.json` holds source-derived facts; `index.json` holds
  source hashes and community labels. History is a separate layer in the same graph.
- When source facts change, use the Graphify skill to re-extract only affected
  sources, replace their old nodes/edges, cache the new extraction, regenerate
  communities/labels and source hashes in `index.json`, and save the manifest.
  Preserve `notes/history.jsonl`, then run `python -X utf8 tools/graph_memory.py sync`.
- Do not re-extract generated HTML, JSON, reports, caches or history as source facts.
  History indexing is deterministic and needs no repeated semantic extraction.
- Never label an inference or proposed action as a verified fact. The brief's
  active-submission wording is unresolved; retain both claims until checked.

## Git hygiene and notebooks

- Keep `graphify-out/`, `notes/`, `raw/`, caches, downloaded competition data,
  benchmark outputs and `ipynb/work/` excluded through `.gitignore`. These are
  local working artifacts; do not force-add them without an explicit request.
- Put the Kaggle notebook under `ipynb/`. The current notebook is generated from
  the tested Python modules with `python -X utf8 tools/build_notebook.py`.
  Regenerate it after source changes and keep saved notebook outputs cleared.
- Record local test results honestly; local Windows execution is not proof of
  compatibility with Kaggle's Linux runtime.
