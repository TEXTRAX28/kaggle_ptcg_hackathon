# Pokémon TCG project handoff

Updated: 2026-10-20. This repository contains two Python heuristic pilots:
Mega Abomasnow ex/Kyogre and Alakazam/Dudunsparce. The combined working branch
is `main`. There is no neural network, BF16 implementation or training pipeline.

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

| File | Purpose |
|---|---|
| `main.py`, `deck.csv` | Abomasnow/Kyogre competition entry and 60-card deck |
| `main_alakazam.py`, `decks/alakazam.csv` | Alakazam/Dudunsparce entry and 60-card deck |
| `pokemon_agent/policy.py` | Abomasnow decisions, legal-choice handling and shared helpers |
| `pokemon_agent/alakazam.py` | Alakazam hand growth, damage-counter attack and resource priorities |
| `pokemon_agent/agents.py` | Select a named pilot and its corresponding deck |
| `pokemon_agent/sdk.py` | Find the supplied simulator SDK, read decks and validate choices |
| `pokemon_agent/runner.py` | Run balanced local games and save results, errors and timings |
| `tools/analyze_replays.py` | Analyze full Kaggle gameplay replays; reject timing-only logs |
| `tools/build_notebook.py` | Generate either Kaggle notebook from the Python sources |
| `tests/` | Policy, replay, native runner and notebook recovery checks |
| `tools/graph_memory.py` | Query and update private local Graphify memory |

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
python -X utf8 -m unittest discover -s tests -v
python -X utf8 -m pokemon_agent.runner --agent alakazam --opponent abomasnow --games 100
python -X utf8 -m pokemon_agent.runner --agent alakazam --opponent random --games 40
python -X utf8 tools/build_notebook.py --agent alakazam
python -X utf8 tools/build_notebook.py --agent abomasnow
```

In Kaggle, import the desired notebook from `ipynb/`, attach
**The Pokémon Company - PTCG AI Battle Challenge Playground** using
**Add Input > Competition Datasets**, wait until it is ready, then **Run All**.
If explicitly setting `SDK_ROOT`, use the directory that contains `cg/api.py`.
A path setting cannot replace missing competition files.

| Notebook | Generated Kaggle submission archive |
|---|---|
| `ipynb/alakazam.ipynb` | `/kaggle/working/alakazam/submission.tar.gz` |
| `ipynb/abomasnow_kyogre.ipynb` | `/kaggle/working/abomasnow-kyogre/submission.tar.gz` |

Local generation uses `ipynb/work/`. Creating an archive does not submit it.
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
