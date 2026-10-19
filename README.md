# Pokémon TCG local baseline

Python heuristic pilot for the supplied Mega Abomasnow ex/Kyogre deck, with an
isolated local game runner. Uses the competition's bundled native simulator.
The policy uses hand-written rules and probabilities. The notebook packages it
for Kaggle; generating an archive does not upload it.

## Development branches and match data

The current tested version is preserved on `main` at commit `842c9bb`.
Work on match analysis and improvements on `improvement-1` so the baseline stays
available for comparison. Before changing branches, commit or otherwise preserve
any unfinished changes; switching branches is not a substitute for saving work.

```powershell
git branch --show-current
git log --oneline --all --decorate -5
```

## Kaggle notebook

Open `ipynb/abomasnow_kyogre.ipynb`, attach the competition dataset in Kaggle,
and Run All. The notebook embeds the Python sources, locates the supplied SDK,
runs a configurable benchmark and builds a Linux `submission.tar.gz` under
`/kaggle/working/abomasnow-kyogre/`. It requires no separate repository upload.

The latest notebook was checked by executing all nine Python code cells locally
with a four-game smoke run. The user previously reported a successful Kaggle run
of an older snapshot; the latest immunity patch has not been directly tested in
Kaggle. Regenerate the notebook after changing its source modules, then import
the regenerated file into Kaggle to update the embedded source snapshot:

```powershell
python -X utf8 tools/build_notebook.py
```

`.gitignore` excludes the graph, notes/history, raw snapshots, downloaded data,
caches, local environments, benchmark results and the notebook's generated
workspace. The notebook itself and reusable Python sources are versioned.

## Run

From `C:\Users\natan\kaggle-pokemon` in PowerShell:

```powershell
python -X utf8 -m pokemon_agent.runner --games 100 --output results/my-run.json
python -X utf8 -m unittest discover -s tests -v
```

Use Python 3.10 or newer and keep the downloaded competition folder in place.
The agent/runner use the standard library and the supplied `cg` package; Graphify
is only needed to maintain project memory. The Windows native library has been
tested locally. Linux/macOS loading is supported by the vendor SDK but has not
been validated in this task.

The default opponent uses the sample policy's algorithm: uniformly sample exactly
`maxCount` distinct legal option indices. Both sides use the same 60-card deck.
The unit suite checks the baseline against the supplied implementation.

Every group of four games covers both agent seats and both starting orders. The
runner controls the initial first/second choice for that balance; other choices
come from the selected policies. An incomplete group is reported as played.
These are **independent single games**, not the deployed Kaggle BO3 match format.

Useful variants:

```powershell
# Random-versus-random sanity check.
python -X utf8 -m pokemon_agent.runner --agent random --opponent random --games 40

# Save visible observations and choices for debugging.
python -X utf8 -m pokemon_agent.runner --games 4 --trace-dir results/traces-new

# Choose policy RNG seeds and local safety limits.
python -X utf8 -m pokemon_agent.runner --games 20 --seed 73 --game-timeout 30 --decision-timeout 1 --max-decisions 5000
```

Each game runs in a separate process. The parent kills workers exceeding the
game deadline; selection count, index and uniqueness checks run before each
native step. Policy exceptions, native failures, timeouts and decision limits
remain failures in the output and produce a nonzero batch exit status.
The one-second decision deadline is a local evaluation guard, not a claim about
the competition's per-decision limit. A stuck decision is ultimately bounded by
the outer game deadline.

The seed controls **policy randomness only**. The supplied native battle API
does not expose a shuffle/coin seed, so repeated commands do not reproduce exact
deals. Optional traces preserve observations and actions for inspection, not a
deterministic engine replay. Trace folders and result files must be new; existing
results are not overwritten.

## Files and behavior

- `main.py`: competition-style `agent(obs_dict)` entry point; returns the deck
  on initialization and legal option indices afterward.
- `deck.csv`: exact supplied 60-card list, including 35 Basic Water Energy.
- `pokemon_agent/policy.py`: setups, evolution, attachments, supporters, card
  choices, attack selection and retreat. Estimates Hammer-lanche over unknown
  own deck/prizes using visible counts, avoids avoidable deck-out and uses
  Kyogre to recycle discarded Energy. Recognizes Sylveon/Crustle protection from
  ex attacks for this fixed deck. It never reads the opaque search payload.
- `pokemon_agent/runner.py`: process isolation, balanced starts, result capture,
  error handling, code/native-library hashes and a 95% Wilson win-rate interval.
- `tests/test_agent.py`: policy regressions, baseline equivalence, selection
  guards, native lifecycle, starting-order and result-accounting tests.
- `pokemon_agent/sdk.py`: finds the supplied native SDK, loads card metadata,
  reads the deck and validates returned option indices.
- `tools/build_notebook.py`: generates the portable notebook from current source.
- `tools/graph_memory.py`: records and queries local project memory; it is not
  called by the game-playing agent.
- `ipynb/abomasnow_kyogre.ipynb`: Kaggle entry notebook with embedded source,
  local evaluation and archive creation.

The baseline passed 16 automated tests on 2026-10-20 before the improvement branch
was created. A local pass verifies those checks; it does not establish stronger
play on the competition ladder.

The policy is specific to this deck. Damage estimates are heuristics and do not
model every opposing ability, temporary effect or special Energy. It is not a
general optimal policy, an MCTS implementation or a trained model. A strong
result against random play establishes a baseline; stronger opponents and BO3
evaluation are still required.

## Results and memory

Reports under `results/` include every game, win/loss/draw counts, failures,
seat/start splits, decision timings and exact source fingerprints. Reports are
checkpointed after each game. Win rate and its interval use completed games;
failed games are reported separately and never counted as wins.

The initial development report is `results/2026-10-17-development-01.json`.
It belongs to the first policy version; later code hashes may differ.
The larger evaluation is `results/2026-10-17-abomasnow-vs-random-100.json`.

Use `notes/CONTEXT.md` and `tools/graph_memory.py query` for the current project
handoff. Successful steps and test results are recorded into graph history by
the agent. Running a benchmark yourself does not automatically write graph
history; its JSON remains the evidence to record afterward.
