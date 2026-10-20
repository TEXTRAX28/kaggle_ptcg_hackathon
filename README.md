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
  ex attacks for this fixed deck. On `improvement-1`, delays an unpowered benched
  Mega when the opponent needs three or fewer Prizes, and prepares Kyogre when
  a powered Mega faces lethal Alakazam counters. It never reads the opaque
  search payload or spectator hands/deck order.
- `pokemon_agent/runner.py`: process isolation, balanced starts, result capture,
  error handling, code/native-library hashes and a 95% Wilson win-rate interval.
- `tests/test_agent.py`: policy regressions, baseline equivalence, selection
  guards, native lifecycle, starting-order and result-accounting tests.
- `pokemon_agent/sdk.py`: finds the supplied native SDK, loads card metadata,
  reads the deck and validates returned option indices.
- `tools/build_notebook.py`: generates the portable notebook from current source.
- `tools/graph_memory.py`: records and queries local project memory; it is not
  called by the game-playing agent.
- `tools/analyze_replays.py`: checks full Kaggle replays, resolves our seat from
  the player name, summarizes each BO3 round and compares recorded choices with
  the current policy. An action in `steps[t]` answers `steps[t-1]`'s ACTIVE
  observation. Agent execution logs are rejected because they lack gameplay.
- `tests/fixtures/replay_positions.json`: three small agent-visible positions
  from the Alakazam match. Spectator state, output logs and opaque search data
  are excluded. These support regression tests without downloading raw replays.
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

## Improvement 1: analysis of both matches

Analysis date: **2026-10-20**. The full replays were downloaded through Kaggle's
signed-in browser session after the separate agent-log files proved to contain
only durations and empty stdout/stderr. Our player is **seat 1 in both matches**.
Both are completed **BO3** episodes, not individual games. The replay configuration
records engine version 2; the initial observations show a 600-second agent time bank;
these are observations about these episodes, not promises about future limits.

| Episode | Opponent | Match result | Our calls, including deck selection |
|---|---|---|---:|
| 124987293 | kutty1119, Dragapult ex | Won 2–0 | 39 |
| 124987236 | awewrasdffetfe, Alakazam | Lost 1–2 | 87 |

| Episode / round | Our starting order | Final numbered turn | Winner / reason |
|---|---|---:|---|
| 124987293 / 1 | Second | 10 | Us: all required Prizes taken |
| 124987293 / 2 | First | 11 | Us: opponent has no Active Pokémon left |
| 124987236 / 1 | Second | 14 | Us: all required Prizes taken |
| 124987236 / 2 | First | 8 | Opponent: all required Prizes taken |
| 124987236 / 3 | Second | 9 | Opponent: all required Prizes taken |

These five rounds show valid battle endings, rather than a recorded timeout,
illegal selection or deck-out. Our lowest observed deck counts by round were
20/30 cards in the win and 27/16/29 in the loss. The frozen `main` policy matches
all **126 recorded calls** across both episodes. That is behavioral agreement on
these positions; the replay does not provide the submitted source fingerprint.

### Winning match: what worked and what remains weak

Abomasnow developed in time and converted Water density into knockouts. Round 1
used four Hammer-lanche attacks; round 2 used two Hammer-lanches and three Frost
Barriers. Frost Barrier correctly finished Dragapult after a 200-damage Hammer
left it at 120 HP, then knocked out the last Budew. Kyogre received an Energy
as a backup, without distracting from the Active attacker.

The opponent **never used Phantom Dive** in either round: its Dragapult attacks
were four 70-damage Jet Headbutts. That allowed our 350-HP Mega to survive while
taking multiple Prizes. This win establishes that the pilot can exploit that
board; it does not establish an advantage against every Dragapult pilot.

The backup board was thin: typically one Mega and one Kyogre. This is a potential
consistency weakness even in a win, rather than evidence that a particular draw
or supporter choice was wrong. The opponent also used Unfair Stamp in both
rounds, including round 2 turn 4, reducing our hand to two cards. That explains
some lost setup options. A future deck experiment should test better access to
backup Basics and recovery through hand disruption. For now, all **39 recorded
winning-match calls remain unchanged** by this patch.

### Losing match: the actual problem was the prize race

Alakazam's Powerful Hand places **two damage counters per card in its owner's
hand**. This is not attack damage reduced by Frost Barrier. Its draw engine
included Kadabra/Alakazam evolution draws, Dudunsparce and Toucannon. The opponent
reached 24 cards in hand in round 1 and 20 in each later round.

Round 1 was a successful recovery: after losing a Snover, a Mega and Kyogre,
Riptide dealt 160, then Lillie plus Mega Signal found the final evolution and
Frost Barrier took our last Prize on turn 14. This shows why the one-Prize
Kyogre and evolution access matter; abandoning the whole deck is not required
to identify useful policy changes.

Round 2 exposed the three-Prize cost of Mega knockouts. The first Mega took
260 counters on turn 4, leaving 80 HP. On our turn 5, the manual attachment and
Waitress both favored Snover while Kyogre stayed unpowered. The Mega was knocked
out on turn 6; a replacement Mega was then knocked out for 360 counters on turn
8. Two Mega knockouts supplied all six opposing Prizes. Preparing a one-Energy
Kyogre before the first knockout offers a lower-Prize replacement; its later
damage and the opponent's responses still require a new game to evaluate.

Round 3 contains the clearest avoidable liability. On turn 8 the opponent had
two Prizes remaining. We had an unpowered Active Kyogre and an unpowered benched
Snover. The policy evolved Snover into a Mega **before** attaching to Kyogre.
Kyogre then dealt 140 and knocked out an Alakazam, but the opponent played Boss's
Orders, brought up the unpowered Mega and placed 380 counters for the final
Prizes. Leaving Snover unevolved would remove that three-Prize target at this
point. It does **not** prove we could win the remaining game from five Prizes.

Source pointers for the decisive positions are
`/steps/162/1/observation` (round 2 turn 5),
`/steps/242/1/observation` (round 3 turn 6, attack-enabling control), and
`/steps/251/1/observation` (round 3 turn 8). Event/result evidence is in
`/steps/0/0/visualize`, including indices 189–190 and 253–261 in the loss.
Visualizer indices and outer `steps` indices are distinct.

### Changes and validation

1. Delay evolving a benched Snover with fewer than two Energy when the opponent
   needs three or fewer Prizes. Attaching to Snover can make evolution useful
   later that same turn. Active evolution and powered backup evolution remain
   available.
2. Prioritize the first Energy on a benched Kyogre when a Mega that can already
   use Hammer-lanche faces lethal counters estimated from public Alakazam and
   hand-count information. Keep the attachment needed to enable the Active
   Mega's attack now. Immediate winning attacks still take priority.

The second rule models this observed matchup, not every opposing effect. It is
an estimate from the current public board, not knowledge of the opponent's next
draw or action. The deck's 60 cards and its 35 Water Energy remain unchanged.

| Check | Result | What it establishes |
|---|---|---|
| Unit/integration suite | 25 passed | New replay regressions and existing guards pass |
| Original winning positions | 39/39 calls unchanged | Preserves decisions observed in this win |
| Original losing positions | Three changed choices | Two views of round 2 setup plus round 3 evolution |
| Against frozen `main`, 100 games | 47 wins / 53 losses, no errors | No measured overall superiority; Wilson 95% interval 37.5–56.7% |
| Against random, 20 games | 17 wins / 3 losses, no errors | A small execution/reference sample; interval 64.0–94.8% |
| Generated notebook, four local games | Two wins / two losses, no errors | All nine code cells execute locally |
| Submission archive | Six project files verified; Linux library present | Sources match after normalizing the deck CSV's newlines |

Local games are independently dealt single games with balanced seats and starts;
they are not seeded, paired counterfactuals or BO3 ladder matches. Offline changed
choices do not propagate through a replay or change its historical outcome. The
branch is an experiment with two justified fixes, **not a proven rating increase**.
The new notebook/archive have not been run in Kaggle or submitted.

The next substantial deck experiment should target hand disruption against
Alakazam and backup consistency. With six Basics in the current deck, an ordinary
seven-card opening hand has a 45.86% chance of containing no Basic before redraws
(`C(54,7)/C(60,7)`); our lost episode actually included two opening redraws in
round 1. More Basics compete with Hammer-lanche's Water density, so compare full
BO3 matches before changing the list. A neural network is not yet supported by
enough labeled games or reliable matchup evaluation.

To inspect future full replays, place them under ignored `match-data/` and run:

```powershell
python -X utf8 -m tools.analyze_replays match-data/episode-124987293-replay.json match-data/episode-124987236-replay.json --player "Natanael Rehuel S" --output results/new-replay-analysis.json
```

Reports and hashes for this work are in
`results/2026-10-20-improvement-1-replay-analysis.json`,
`results/2026-10-20-improvement-1-baseline-replay-analysis.json`,
`results/2026-10-20-improvement-1-vs-main-100.json`,
`results/2026-10-20-improvement-1-vs-random-20.json`, and
`results/2026-10-20-improvement-1-notebook-verification.json`.

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
