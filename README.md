# Pokémon TCG agents for Kaggle

Two Python heuristic pilots use the competition's bundled native simulator:
Mega Abomasnow ex/Kyogre and the new Alakazam/Dudunsparce experiment. Each has a
Kaggle notebook that embeds its tested sources, runs local games and builds a
submission archive. Archive creation does not upload a submission.

## Branches

| Branch | Purpose |
|---|---|
| `main` | Combined working branch: replay improvements, both pilots/decks, both notebooks and SDK setup fixes |
| `improvement-1` at `e226a03` | Retained checkpoint for the replay-based Abomasnow policy fixes |
| `deck-experiment-1` at `f5ac167` | Retained checkpoint for Alakazam and the notebook module recovery fix |

On 2026-10-20, `git merge --no-edit improvement-1 deck-experiment-1` on `main`
reported **Already up to date**: both branch histories were already included,
with no conflicts. The original Abomasnow baseline remains at commit `842c9bb`.
The root `main.py`, `deck.csv` and `pokemon_agent/policy.py` match
`improvement-1`; Alakazam has its separate entry and notebook. Continue shared
work on `main`; the historical branch refs are retained for recovery.

See [HANDOFF.md](HANDOFF.md) for the consolidation, verified results, commands
and remaining work.

## Deck experiment 1: Alakazam / Dudunsparce

Alakazam beat our Abomasnow agent in the supplied losing replay. This is a
practical candidate to test, rather than evidence that a popular deck must win.
Its attackers give up one Prize, and Powerful Hand needs one Psychic Energy.
A separate pilot is necessary because its hand-building strategy differs from
Abomasnow's Water-density strategy.

The pilot evolves Abra through Kadabra or Rare Candy, uses evolution draws and
Dudunsparce to grow its hand, and searches with Dawn/Hilda. Powerful Hand places
20 HP of damage counters per card in hand: 18 cards can knock out a full-health
350-HP Mega. The pilot accounts for the hand card spent on Boss's Orders, avoids
Lillie when it would shrink a large hand, saves a draw reserve and does not
shuffle away its sole Pokémon with Dudunsparce. It attaches Psychic to the
Alakazam line; the 60-HP Dunsparce variant is a free-retreat pivot.

The native simulator accepts this 60-card list in `decks/alakazam.csv`:

| Cards | Copies each | Subtotal |
|---|---:|---:|
| Abra / Kadabra / Alakazam | 4 | 12 |
| Dunsparce / Dudunsparce | 4 | 8 |
| Basic Psychic / Telepath Psychic Energy | 4 | 8 |
| Dawn / Hilda / Poké Pad / Buddy-Buddy Poffin / Rare Candy | 4 | 20 |
| Lillie | 2 | 2 |
| Boss's Orders | 3 | 3 |
| Lana's Aid / Night Stretcher / Battle Cage | 2 | 6 |
| Special Red Card | 1 | 1 |
| **Total: 20 Pokémon, 8 Energy, 32 Trainers** | | **60** |

All Pokémon in this list give up one Prize. Eight Basics reduce the ordinary
seven-card probability of no Basic to 34.64%, compared with 45.86% for the
six-Basic Abomasnow list, before redraws. These are combinatorial opening-hand
probabilities, not game win rates. The draw engine and 60-HP bench Pokémon can
still be punished; Battle Cage addresses some opposing bench counter effects.
Hand disruption and a slow Stage 2 setup remain weaknesses.

Results on 2026-10-20, using the frozen candidate source:

| Opponent / check | Result | Interpretation |
|---|---|---|
| `improvement-1` Abomasnow deck and unchanged pilot | **85 wins / 15 losses** | 100 completed games; 95% Wilson interval 76.7–90.7%; no errors |
| Random policy using the same Alakazam deck | **40 wins / 0 losses** | 40 completed games; interval 91.2–100%; no errors |
| Unit/integration suite | **36 passed** | Existing guards plus Alakazam legality, counter math, Psychic costs, hand preservation and entry/deck checks |
| Initial notebooks, before the setup fix | All 13 code cells each executed locally | Four-game smoke runs: Alakazam 2W/2L vs Abomasnow; Abomasnow 4W/0L vs random; no errors |
| Both submission archives | Entry, deck and ten source members checked | Correct distinct decks, Linux library included, saved notebook outputs empty |

The 100-game result has 50 games in each seat and starting order: 46/50 wins in
seat 0, 39/50 in seat 1; 44/50 going first, 41/50 second. Alakazam averaged
0.211 ms per decision, with a 2.103 ms maximum on this Windows machine. The first
eight development games were also wins, but used an earlier pilot version and
are excluded from the 100-game result.

This compares a **new deck plus its dedicated pilot** against our local
Abomasnow implementation. It does not isolate the deck's causal contribution,
establish strength against competent Dragapult/other opponents, or predict a
Kaggle rating. Local games are independent single games, not BO3 matches. The
small notebook smoke runs are packaging checks, not additional strength claims.
At that initial experiment checkpoint, the notebook/archive had not yet been
run in Kaggle or submitted. The later verified Kaggle run is documented below.

Reports, including source/native-library fingerprints and every game, are kept
locally under the ignored `results/` directory:

- `2026-10-20-alakazam-vs-abomasnow-100.json`
- `2026-10-20-alakazam-vs-random-40.json`
- `2026-10-20-deck-experiment-notebook-verification.json`

## Kaggle notebooks and submission files

Use **`ipynb/alakazam.ipynb`** for the new deck. Attach the competition dataset
in Kaggle's Add Input panel and Run All. The default benchmark tests Alakazam
against Abomasnow. Its output archive is:

`/kaggle/working/alakazam/submission.tar.gz`

`ipynb/abomasnow_kyogre.ipynb` still builds Abomasnow at
`/kaggle/working/abomasnow-kyogre/submission.tar.gz`. Both notebooks materialize
their own `main.py` and `deck.csv` and keep named deck copies so the opponent
gets its correct list. Locally their generated workspaces are respectively
`ipynb/work/alakazam/` and `ipynb/work/abomasnow-kyogre/`.

Regenerate embedded snapshots after source changes, then import the regenerated
notebook into Kaggle. An existing Kaggle copy does not update automatically:

```powershell
python -X utf8 tools/build_notebook.py --agent alakazam
python -X utf8 tools/build_notebook.py --agent abomasnow
```

Both current notebooks have **seven cells, including four code cells**. All code
cells were executed on Windows, including benchmark subprocesses, archive
content checks and a fresh-process entry/deck check. Linux library inclusion
does not prove Kaggle/Linux runtime compatibility. The user reported
a successful Kaggle run of an older Abomasnow snapshot.

The 2026-10-20 setup fix addresses `No module named 'pokemon_agent.sdk'` before
a benchmark starts. The earlier notebook wrote each file in its own cell;
omitting the SDK cell reproduces that exact traceback. This does not establish
which cells ran in the user's Kaggle session.

The new agent-file setup cell embeds and writes all ten project files together.
Evaluation and archive creation call `prepare_workspace()` again to restore
missing files. Running either step before setup gives a clear Run All instruction.
After importing an updated notebook into Kaggle, restart the session and **Run All**.
Look for `Prepared 10 agent files, including pokemon_agent/sdk.py` before games.

The suite now passes **38 tests**, including fresh-process import recovery after
deleting the helper and clear failure for out-of-order evaluation/packaging.
Both full notebooks also passed four local games each after SDK deletion
(Alakazam 2W/2L, Abomasnow 4W/0L), with no execution errors. Sources, selected
entry/deck and Linux library were checked in each archive. See
`results/2026-10-20-notebook-sdk-setup-fix-verification.json`; these checks
were initially Windows-only checks. The Alakazam notebook was subsequently
verified directly in Kaggle, as described below.

If setup reports no supplied cg SDK under `/kaggle/input`, check the notebook's
**Input** panel. Use **Add Input → Competition Datasets**, find **The Pokémon
Company - PTCG AI Battle Challenge Playground**, and add it. Wait for the ready
notification, then **Run All**. The engine files come from the attached competition
data; setting `SDK_ROOT` cannot replace missing files. Automatic discovery is
preferred; an explicit root must be the directory containing `cg/api.py`.
The notebook's diagnostic now lists visible input entries to make this clearer.

On 2026-10-20, the live PTCG-alakazam notebook showed **No input attached**.
After attaching the official competition data and running all existing cells,
the Kaggle/Linux benchmark completed **20 games: 18 wins, 2 losses, no errors**
against our Abomasnow pilot. All starting-order/seat groups had ten games;
seat wins were9/10 each, first10/10 and second8/10. This is a notebook benchmark,
not a ladder result. It generated `/kaggle/working/alakazam/submission.tar.gz`
(0.52 MiB) and did not submit it to the competition.

Live SDK root was
`/kaggle/input/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/sample_submission/sample_submission/sample_submission`.
Saved evidence: `results/2026-10-20-kaggle-alakazam-live-verification.json`
contains the visible output summary, and `results/2026-10-20-kaggle-input-fixed.jpg`
shows the attached input and generated bundle. This is observed browser output,
not a downloaded full benchmark report. The additional clearer error text was
tested locally with empty and unrelated input folders;38 tests still pass.

## Run locally

From `C:\Users\natan\kaggle-pokemon` with Python 3.10 or newer:

```powershell
# New deck and pilot against our existing Abomasnow deck and pilot.
python -X utf8 -m pokemon_agent.runner --agent alakazam --opponent abomasnow --games 100

# Same Alakazam deck on both sides, with a random opponent policy.
python -X utf8 -m pokemon_agent.runner --agent alakazam --opponent random --games 40

# Original default: Abomasnow versus random, using the Abomasnow deck.
python -X utf8 -m pokemon_agent.runner --games 100

python -X utf8 -m unittest discover -s tests -v
```

Keep the downloaded competition folder in place. The playing agent and runner
use the standard library and supplied `cg` SDK; Graphify is only for project
memory. Named pilots use their matching decks; a random opponent uses the
candidate's deck unless `--opponent-deck path.csv` is supplied. Explicit
`--agent-deck` overrides are also supported, but a pilot is specialized for its
own deck and is not automatically competent with arbitrary cards.

Every group of four games covers both agent seats and starting orders. The
runner controls the initial first/second choice for that balance; other choices
come from the selected policies. An incomplete group is reported as played.
Each game runs in an isolated process. Illegal selections, policy exceptions,
native failures, decision limits and timeouts remain errors and produce a
nonzero batch exit status. The one-second decision limit and 30-second game
limit are local guards, not verified competition limits.

The `--seed` controls policy randomness only. The native battle API does not
expose a shuffle/coin seed, so identical commands need not reproduce deals.
Use `--trace-dir results/new-traces` to save visible positions and choices, or
`--output results/new-run.json` for a chosen report path. Existing results and
trace folders are not overwritten. Traces are not deterministic engine replays.

## Files and behavior

- `main.py`, `deck.csv`: unchanged Abomasnow competition entry and supplied list.
- `main_alakazam.py`: Alakazam entry; its notebook packages this file as `main.py`.
- `decks/alakazam.csv`: new list of 60 native card IDs, including eight Basics.
- `pokemon_agent/alakazam.py`: Alakazam hand-building strategy. Reuses visible
  card resolution, legal-choice dispatch and typed Energy checks from the base
  class while overriding attack, search, attachment and action priorities.
- `pokemon_agent/agents.py`: factory mapping policy names to pilots and decks.
- `pokemon_agent/policy.py`: Abomasnow setup, Water attachment, Hammer-lanche
  estimates, Frost Barrier, Kyogre recovery and the replay fixes described below.
  Neither pilot reads opaque search input or spectator hands/deck order.
- `pokemon_agent/runner.py`: balanced starts, process/deadline guards, game
  accounting, source hashes and 95% Wilson win-rate intervals.
- `pokemon_agent/sdk.py`: supplied SDK discovery, card metadata, deck loading
  and selection validation.
- `tests/test_agent.py`, `tests/test_alakazam.py`: baseline and new-pilot
  regressions, legality, native lifecycle, starting-order and accounting checks.
- `tools/build_notebook.py`: generates either self-contained Kaggle notebook.
- `tools/analyze_replays.py`: checks full Kaggle replays, identifies our seat,
  summarizes each BO3 round and compares recorded choices with a selected pilot
  (`--policy abomasnow` by default; `--policy alakazam` also available). An action
  in `steps[t]` answers `steps[t-1]`'s ACTIVE observation. Timing-only agent logs
  are rejected because they contain no gameplay.
- `tests/fixtures/replay_positions.json`, `tests/test_replay_analysis.py`:
  sanitized visible replay positions and replay-parser regression checks.
- `tools/graph_memory.py`: records and queries local memory; absent from the
  playing agent and submission archives.

These are deck-specific heuristics. They do not model every opposing ability,
temporary effect or special Energy. Neither uses neural training or tree search.
The next useful evidence is BO3 play and full ladder replays against competent,
varied opponents, especially hand disruption and bench-pressure decks.

`.gitignore` already covers `graphify-out/`, `notes/`, `raw/`, `match-data/`,
downloaded data, caches, results, submission archives and `ipynb/work/`. New code,
the deck list, README and cleared notebooks remain versioned. No extra ignore
pattern is needed for this experiment.

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
