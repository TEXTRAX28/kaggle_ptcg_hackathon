# Pokémon TCG project handoff

Updated: 2026-10-22. This repository contains two Python heuristic pilots:
Mega Abomasnow ex/Kyogre and Alakazam/Dudunsparce. The combined working branch
is `main`. There is no neural network, BF16 implementation or training pipeline.

## Active replay audit and next implementation

The current request is to audit every one of the 299 steps in episode
`125168227`, explain the loss, and implement evidence-backed improvements on a
new branch. The repeated request after context compaction is the same task;
record it once in project memory. Update this existing handoff as work advances.

The full replay is already downloaded at `match-data/125168227.json` (ignored):
8,225,947 bytes; SHA256
`a114769705d8f1b628d2c6dcc5e8d1fc2efa63adb1e4bbec57f96d394c51c12f`.
Our player is `Natanael Rehuel S`, seat 1, against `masterlincs`; final rewards
are `[1, -1]`, both statuses DONE. Access verification is saved in
`results/2026-10-21-episode-125168227-access.json`. Strategic causes and round
scores still need auditing. Actions at step t answer the ACTIVE observation at
step t-1. Spectator-only hidden information must never enter policy decisions.

Before implementation, preserve the pending deck-folder reorganization and
create a separate improvement branch. At this handoff update, HEAD is
`main` / `bfe80f7`; the layout revision below remains uncommitted, including
new untracked deck folders and shared helpers. Do not discard these files.
The next work is a complete step ledger, causal analysis, targeted policy
regressions, native-game checks, notebook regeneration and incremental Graphify
refresh. Current Graphify has 301 source nodes, 455 edges and 32 indexed sources;
all source hashes matched at the start of this task.

The user permits accessing/editing their Kaggle notebook where possible:
`https://www.kaggle.com/code/natanaelrehuels/ptcg-alakazam/edit/run/360438660`.
Preserve any cloud draft before replacing it; validate local sources first.
No competition submission is requested. Local files plus a regenerated notebook
are the fallback. Assess BF16 separately from opponent/self-play training:
the current pilot has no neural workload, and lower precision alone is not a
playing strategy. No training changes have yet been made.

## Current deck layout revision

After consolidation, the user requested grouping all deck-specific files.
Each folder under `decks/abomasnow_kyogre/` and `decks/alakazam_dudunsparce/`
now contains its own `main.py`, `policy.py`, `deck.csv`, generated notebook
and strategy tests. Sanitized Abomasnow replay positions live with that deck.
Shared runtime code stays in `pokemon_agent/`; shared developer tools and
infrastructure tests stay in `tools/` and `tests/`. See README's layout table.

`BaseAgent` now owns the common dispatch, visible lookup, Energy and readiness
helpers. Both deck pilots inherit it. All scoring methods and 179 prior
decisions are unchanged; both deck lists are byte-identical. The SDK loader,
registry, report fingerprint paths, replay tool and notebook generator use
the new locations. The archive still supplies root `main.py` and `deck.csv`.

Local generated files now go to `build/notebooks/<deck-folder>/`. The old
`ipynb/work/` tree was moved intact to `build/legacy-notebook-work-20261020/`.
The two notebooks have moved into the deck folders, so `ipynb/` is gone.
Existing `/build/` ignore rules cover the new workspaces and preserved files.

Validation: 38 tests pass with `python -X utf8 -m unittest discover -v`.
All four code cells in both notebooks ran locally from their deck folders;
four games per notebook completed without errors, deleted `sdk.py` was restored,
and both archives passed member/source/Linux-library checks. Each embeds 15
project files. This layout has not been rerun in Kaggle. The earlier live run
below tested the previous layout and does not certify this package revision.
Evidence and pre-change source/graph snapshots: `results/2026-10-20-deck-layout/`.

The following consolidation account describes the earlier checkpoint; its
old filenames are historical. Current locations are given in the file table.

## What was consolidated

The user requested combining the project branches, stopping to report any
conflicts, then writing this handoff. Inspection found that `main` already
contained both histories:

| Ref before consolidation | Commit | Relationship to `main` |
|---|---|---|
| `main` | `f5ac167ae8390e4f15a0ba3a511b8ddf2445b75c` | Starting checkout |
| `deck-experiment-1` | `f5ac167ae8390e4f15a0ba3a511b8ddf2445b75c` | Same commit |
| `improvement-1` | `e226a03782555b107de0793fef2c054b84d748fe` | Ancestor |

Running `git merge --no-edit improvement-1 deck-experiment-1` returned
`Already up to date.` with exit code 0 and no unmerged paths. No conflict
resolution or new merge commit was necessary. Historical branch refs were
retained. The original tested baseline is still available at `842c9bb`.

Five pending files were reviewed and included with the handoff in the
consolidation commit:

- `.gitignore`: exclude nested `graphify-out/` directories and caches as well
  as the existing private memory, raw data, results and notebook workspaces.
- `tools/build_notebook.py`: explain how to attach the competition input when
  SDK discovery fails, and list the visible input directories.
- `ipynb/alakazam.ipynb` and `ipynb/abomasnow_kyogre.ipynb`: generated notebooks
  containing that diagnostic, with saved outputs cleared.
- `README.md`: document the successful Kaggle run and current combined branch.

The playing policies and deck lists were not changed during consolidation.
No remote push or competition submission was performed. To identify the
consolidation commit, use `git log --oneline -- HANDOFF.md`.

Before the merge check, a complete Git bundle and a binary patch of the pending
changes were saved locally:

- `results/2026-10-20-before-branch-consolidation.bundle`
- `results/2026-10-20-before-branch-consolidation.patch`
- `results/2026-10-20-branch-consolidation.json`: merge and verification evidence.

These files are ignored and are not part of a fresh clone.

## What is already built

| File or folder | Purpose |
|---|---|
| `decks/abomasnow_kyogre/` | Abomasnow entry, strategy, card list, notebook and strategy tests |
| `decks/alakazam_dudunsparce/` | Alakazam/Dudunsparce entry, strategy, list, notebook and strategy tests |
| `pokemon_agent/base.py` | Shared legal-choice dispatch and visible-state/attack helpers |
| `pokemon_agent/random_agent.py` | Shared random baseline |
| `pokemon_agent/agents.py` | Shared pilot/deck registry |
| `pokemon_agent/sdk.py` | SDK loading, metadata, deck reading and validation |
| `pokemon_agent/runner.py` | Match isolation, timing, failures and reports |
| `tools/` | Notebook generator, replay analyzer and private graph-memory adapter |
| `tests/` | Shared runtime, notebook and replay infrastructure checks |

Earlier replay improvements avoid exposing an idle benched Mega for an easy
Prize finish, prepare a backup Kyogre against visible counter threats, and
preserve the current attack's Energy attachment. Alakazam uses one-Prize
attackers and builds its hand with the evolution and Dudunsparce draw engines.
The README contains the two-match analysis and policy limitations.

The notebooks restore all required project modules together through
`prepare_workspace()` before evaluation and packaging. This fixes the missing
`pokemon_agent.sdk` failure caused by an incomplete generated workspace.

## Verification and its limits

Consolidation checks on 2026-10-20:

- `python -X utf8 -m unittest discover -s tests -v`: **38 tests passed** on
  Windows. This includes actual native games and notebook module recovery.
- Both saved notebooks contain seven cells, four of them code, with empty
  outputs and no execution counts.
- All 24 indexed Graphify source hashes match the current files.
- Private memory, nested graph caches, local backups and generated archives
  are excluded by `.gitignore`.

Earlier performance evidence:

| Test | Result | Scope |
|---|---|---|
| Local Alakazam vs our Abomasnow | 85 wins / 15 losses | 100 independent games; no errors |
| Local Alakazam vs random on the same deck | 40 wins / 0 losses | Functionality and weak-opponent benchmark |
| Live Kaggle Alakazam notebook | 18 wins / 2 losses | 20 games against our Abomasnow; no errors; Linux SDK worked |

The live Kaggle failure was **No input attached**. Attaching the official
competition data and running all cells succeeded and generated a 0.52 MiB
`/kaggle/working/alakazam/submission.tar.gz`. Evidence is saved in
`results/2026-10-20-kaggle-alakazam-live-verification.json` and
`results/2026-10-20-kaggle-input-fixed.jpg`. The JSON preserves observed output,
not a downloaded full benchmark report. The clearer diagnostic was tested
locally after that run; there was no separate cloud rerun of that text change.

These results compare decks plus their pilots against our own limited
opponents. They do not establish ladder strength, meta superiority or BO3
performance. The local runner uses independent single games. Its policy seed
does not seed native deals or coin flips. A Windows test pass alone is not
proof of Kaggle compatibility; only the observed live run supplies that evidence.

## Run and package

Run commands from the repository root with the downloaded official competition
folder available for the native SDK:

```powershell
python -X utf8 -m unittest discover -v
python -X utf8 -m pokemon_agent.runner --agent alakazam --opponent abomasnow --games 100
python -X utf8 -m pokemon_agent.runner --agent alakazam --opponent random --games 40
python -X utf8 tools/build_notebook.py --agent alakazam
python -X utf8 tools/build_notebook.py --agent abomasnow
```

In Kaggle, import the desired notebook from the appropriate `decks/<deck>/` folder, attach
**The Pokémon Company - PTCG AI Battle Challenge Playground** using
**Add Input > Competition Datasets**, wait until it is ready, then **Run All**.
If explicitly setting `SDK_ROOT`, use the directory that contains `cg/api.py`.
A path setting cannot replace missing competition files.

| Notebook | Generated Kaggle submission archive |
|---|---|
| `decks/alakazam_dudunsparce/alakazam_dudunsparce.ipynb` | `/kaggle/working/alakazam/submission.tar.gz` |
| `decks/abomasnow_kyogre/abomasnow_kyogre.ipynb` | `/kaggle/working/abomasnow-kyogre/submission.tar.gz` |

Local generation uses `build/notebooks/<deck-folder>/`. Creating an archive does not submit it.
Local source changes do not automatically update an existing Kaggle notebook.

## Continue from here

1. Read `AGENTS.md` and this handoff. If local memory is present, read
   `notes/CONTEXT.md`, query the graph and consult its report before inspecting
   only the necessary source passages. Do not assume ignored memory exists
   in a fresh clone.
2. Use `main` as the combined working branch. Keep both pilots available so
   changes can be measured against a fixed baseline.
3. Obtain full BO3 gameplay replays and test against competent, varied
   opponents, especially hand disruption and bench pressure. Timing-only
   stdout/stderr downloads are insufficient for gameplay analysis.
4. Improve the decisions revealed by those games and compare balanced results.
   Do not infer that a popular deck or a dtype change will improve the rating.
5. Record each user/assistant message and successful action with
   `tools/graph_memory.py`; refresh source extraction only for changed indexed
   facts. Keep generated memory and caches ignored.

The user's BF16 question was interrupted by this merge request. No BF16 change
was authorized or implemented. A future neural model would need profiling and
evaluation before deciding its precision. No new training work was started.
