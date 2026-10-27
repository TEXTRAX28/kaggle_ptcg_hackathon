# YumeNeko comparison and a separate Alakazam experiment

Initial analysis prepared 2026-10-26 before changing agent code; implementation
results were appended afterward. Evidence: official episode
[125429278](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/leaderboard?submissionId=57666077&episodeId=125429278),
the archived seven-match Dipam scouting sample, the current local sources, and
the earlier local match-history audit. This is a proposed improvement with a
verification plan; a 2-0 replay is not a controlled matchup win-rate estimate.

## What we actually have

Our current agent is a hand-written action scorer. It has no neural network,
PPO learner, BF16 computation, learned weights, or opponent-training pipeline.
Those were future proposals. The previous decision is preserved at
`notes/history.jsonl:351`; the implemented policy is
`decks/alakazam_dudunsparce/policy.py:L20`.

BF16 describes arithmetic precision, not how an agent learns a strategy.
PyTorch's AMP documentation describes selecting different operation dtypes;
its value must be measured on an actual model and hardware workload.
[PyTorch AMP](https://docs.pytorch.org/docs/2.14/amp.html).

## Deck differences

| Component | Current local list | YumeNeko's list | Practical effect |
| --- | --- | --- | --- |
| Overall | 20 Pokemon / 32 Trainers / 8 Energy | 25 Pokemon / 28 Trainers / 7 Energy | More board engines and backup attackers, fewer search/recovery slots |
| Basics | 8 | 12 | More setup options, but some are fragile support Pokemon |
| Alakazam line | 4 Abra / 4 Kadabra / 4 Alakazam | 4 / 4 / 3 | One fewer main attacker; depends more on recovery and alternatives |
| Dunsparce | Four ID65: 60 HP, free retreat | Three ID305: 70 HP, retreat 1 | An undamaged 70-HP Dunsparce survives one six-counter Phantom Dive allocation; retreat becomes less convenient |
| Dudunsparce | 4 | 3 | One fewer repeated draw engine |
| Backup attacker | Mainly Kadabra | 2 Pikipek / 2 Toucannon | Feather Rondo provides direct damage and costs one Colorless Energy |
| Extra draw | Evolution, Dudunsparce, 2 Lillie | Evolution, Dudunsparce, Toucannon, Fezandipiti ex, Enriching Energy | Rebuilds after Judge/Unfair Stamp and can reach larger hands |
| Prize acceleration | None | 1 Togepi / 1 Togekiss | Chance of an extra Prize after knocking out the Active; never assume the coin flip succeeds |
| Bench defense | 2 Battle Cage | 2 Battle Cage plus Shaymin | Cage blocks opposing bench counters; Shaymin blocks attack damage to non-Rule-Box bench Pokemon. They solve different effects |
| Energy | 4 Psychic / 4 Telepath | 2 Psychic / 4 Telepath / 1 Enriching | Enriching draws four on attachment but supplies Colorless, so it cannot power Powerful Hand by itself |
| Recovery | 2 Night Stretcher / 2 Lana | 1 Night Stretcher / 1 Lana / 1 Sacred Ash | Recovers more Pokemon to the deck at the cost of immediate hand recovery |
| Supporters | 4 Hilda / 4 Dawn / 3 Boss / 2 Lana / 2 Lillie | 3 Hilda / 3 Dawn / 2 Boss / 1 Lana | Fewer Supporters; the board has to provide more of the draw |
| Other additions | None | Enhanced Hammer and Handheld Fan | Special-Energy removal and reactive Energy displacement; Hammer has no target against Dipam's eight basic Energy |

Both lists have four Rare Candy, four Poffin, four Poke Pad, two Battle Cage and
one Special Red Card. YumeNeko has no Trumbeak or Togetic: both additional Stage
2 lines depend on Rare Candy, which competes with Alakazam and is stopped by
Budew's Item lock. Copying the list therefore requires a pilot that handles it.

## What the winning replay demonstrates

1. In round 1, YumeNeko used Fezandipiti to draw after a knockout, evolved
   Alakazam, and attacked with 16 cards for 320 counter damage. The next
   Alakazam attacked with 17 cards for 340, taking two Dragapult ex knockouts.
2. Toucannon ended round 1 with Feather Rondo for 220 against Meowth ex. It
   remained useful when there was no adequate Alakazam attack available.
3. In round 2, Battle Cage made all six Phantom Dive bench placements at turn
   12 record zero HP change. Maintaining the Stadium matters because Dipam has
   Area Zero and a Chi-Yu attack that can remove Stadiums.
4. Togekiss was in the list, but was not needed to explain the two winning
   rounds. It is an optional extension, not a proven cause of that victory.

The essential competitive plan is to exchange one-Prize attackers for two-Prize
ex knockouts, recover enough hand size after disruption, protect developing
Pokemon, and use a direct-damage attacker when counters are ineffective or the
hand is too small. Sixteen cards gives Powerful Hand 320 counter damage; after
spending Boss's Orders, that requires seventeen cards before the Supporter.

## Gaps in our present pilot

The existing policy recognizes Dunsparce ID65, not YumeNeko's ID305. Its
`energy_priority` only powers the Abra line; its Ability branch only uses
Dudunsparce; its Rare Candy branch only plans for Alakazam. It does not calculate
Feather Rondo's bench-based damage, attach Enriching Energy for its draw, use
Fezandipiti/Toucannon draw, or allocate Rare Candy among the three Stage 2 lines.
Source: `decks/alakazam_dudunsparce/policy.py:L29,L77,L110,L155,L197,L214`.

An offline check of the current scorer on YumeNeko's recorded observations found
76 different main-action choices. That is a coverage diagnostic, not a count of
mistakes: different sequences can both be reasonable, and the replay positions
would diverge if another action were actually taken.

## Implementation decision

Create `decks/alakazam_toucannon/` with its own policy, deck, entry point, strategy
tests and **alakazam_toucannon.ipynb**. Start with the exact verified YumeNeko list
so the first experiment has an identifiable reference. Keep the existing deck,
policy and saved notebook intact. The experimental policy will reuse shared
mechanics and extend the current Alakazam pilot in its own module.

Implement these changes in order:

1. Recognize both Dunsparce prints and all added Pokemon, including attack,
   draw, Energy and Rare Candy choices. Avoid handing the opponent unnecessary
   Fezandipiti ex prizes merely because it is in hand.
2. Calculate direct damage and counter damage separately. Use Toucannon's
   actual bench count, respect visible immunity, and allow Boss's Orders with
   a ready backup attacker.
3. Sequence draw, search, attachment and evolution around the knockout
   threshold. Take a guaranteed match-ending attack; preserve a current
   knockout when spending cards; develop a replacement when it is safe.
4. Give Cage priority against visible Dragapult/Munkidori threats. Account for
   vulnerable bench Pokemon when selecting basics, pivots and recovery.
5. Check deck-out safety, optional draws, Enriching's Colorless limitation,
   recovery and Handheld Fan choices in legal-observation tests.

## A stronger development method

For the current project, use replay-informed tactical tests and balanced games
against several competent strategies. Separate deck changes from pilot changes
with ablations: current pilot/current deck, current pilot/Yume list, and new
pilot/Yume list. Include an exact-Dipam-list benchmark pilot with transparent
heuristics; it must be labeled a proxy, because Dipam's actual source is unknown.
Measure the candidate against the current Alakazam pilot and other opponents,
not just random play. Keep fresh evaluation games separate from replay fixtures
used to develop the policy.

If we later build a neural learner, a sensible research progression is visible
observation encoding and legal-action handling, imitation from curated replays,
then reinforcement learning against a mixture of competent pilots and frozen
earlier policies. Retain unseen opponents for evaluation and include opponents
that exploit the current policy's weaknesses. AlphaStar supplies evidence for
imitation plus diverse league training in StarCraft; applying that recipe here
is our proposed experiment, not an established Pokemon result.
[DeepMind's AlphaStar research](https://deepmind.google/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/).

Choose FP32/BF16 only after profiling such a model. Changing arithmetic precision
cannot repair the current scorer's missing card mechanics or bad action order.

## Validation and promotion boundary

Run root `python -X utf8 -m unittest discover -v`, replay legality checks on both
available Alakazam decks, and balanced native games with source hashes and
Wilson intervals. Native deals are not seedable, so comparisons are unpaired.
Execute the new notebook locally with a small game count, inspect the packaged
archive, and verify its saved cells contain code only with no outputs. Confirm
the two existing notebook hashes remain unchanged by this task.

The final results will be appended below after implementation. Local Windows
results do not certify Kaggle Linux, reproduce Dipam's agent, or establish that
the candidate beats him on the leaderboard. Packaging is authorized; no new
Kaggle submission is made as part of this local experiment.

## Implementation results

The separate notebook and pilot are implemented. The final default is a smaller
adaptation of our original list; the exact YumeNeko list is retained in
`yume_reference.csv`. The earlier proposal to use the full Yume list as the
default was superseded after local ablations exposed consistency costs.

### Final deck changes from our original list

- Replace three 60-HP Dunsparce with three 70-HP Dunsparce; retain one free-retreat
  Dunsparce. The pilot now recognizes both prints and funds the active pivot's
  retreat before attaching to another benched attacker.
- Replace one Lana's Aid and one Lillie's Determination with one Pikipek and one
  Toucannon. Keep four Alakazam, four Dudunsparce, four Hilda and four Dawn. The
  single backup line is less demanding than two additional Stage 2 engines,
  although it can be unavailable when a key card is prized.
- Replace one basic Psychic with Enriching Energy. The list still has eight
  Energy, including seven Psychic-providing cards. The policy distinguishes
  Colorless from Psychic and searches for guaranteed Psychic when it is needed.
- Keep both Battle Cage. No Fezandipiti ex, Togekiss, Shaymin, Hammer or Fan is
  required by the default hybrid; the pilot supports the full reference list
  for controlled comparison. The default has 22 Pokemon, 30 Trainers and 8 Energy.

### Implemented decision changes

The new pilot supports the added draw/attack mechanics, scores Feather Rondo
using both benches, handles Boss with a ready backup, and considers a visible
retreat-then-gust sequence before spending the Supporter elsewhere. Normal
evolution of a powered Kadabra takes priority over spending Candy on an
unpowered Abra. Hand-cost accounting preserves a current knockout and allows
known evolution draw. Optional draws reserve natural draws for the remaining
Prize race, while allowing a draw that enables an immediate guaranteed win.

A native development trace exposed two concrete issues: an unfunded active
pivot and excessive late draw. They were repaired and covered by tests. A
temporary misplaced retreat rule caused a NameError in one development run;
that failed run is preserved in the local evidence and excluded from the
completed-game comparison below.

### Final local comparison

Each cell is wins out of 64 independent single games. The four-game scheduling
cycle balances seats and first/second. Deals and coins are native and unseeded;
the variants do not receive identical hands. All 1,024 final games completed
without errors. Source: `results/2026-10-26-alakazam-toucannon/final-hybrid-verified.json`.

| Variant | Dragapult proxy | Original Alakazam pilot | Abomasnow pilot | Random on the fixed original Alakazam deck |
| --- | ---: | ---: | ---: | ---: |
| Original pilot + original deck | 58/64 | 30/64 | 60/64 | 63/64 |
| Original pilot + hybrid deck | 55/64 | 16/64 | 62/64 | 55/64 |
| New pilot + original deck | 59/64 | 28/64 | 60/64 | 58/64 |
| New pilot + hybrid deck | 62/64 | 35/64 | 57/64 | 59/64 |

The hybrid's proxy result is 96.9%, with a 95% Wilson interval of 89.3-99.1%; the baseline's 90.6% has an interval of 81.0-95.6%. These intervals overlap and do not establish superiority. Results against Abomasnow/random were lower than the original baseline. The evidence supports keeping this as a separate experiment, not replacing our default or claiming an overall improvement.

The full Yume list with the corrected new pilot previously scored 58/64 against
the proxy, 25/64 against our Alakazam, 54/64 against Abomasnow and 61/64 against
random (`final-ablations-v3.json`). These were development comparisons used to
choose the hybrid, not independent proof that the hybrid is stronger. Earlier
`final-ablations-v2.json` results belong to the version before pivot/draw repair.

The proxy is much easier for our original pilot than the sampled competent
Kaggle Dragapult opponents in the earlier history audit. Its scores should be
used for local regressions and card interactions. They cannot stand in for
Dipam's source or estimate our win rate against him. Fresh real BO3 matches
against strong Item-lock/hand-disruption pilots are the next meaningful check.

### Verification and files

- Root discovery: **84 tests passed**. New tests cover direct-damage versus
  counter protection, typed Energy, Energy search, Candy allocation, retreat
  then gust, low-deck draw reserves, a native game, and hidden-payload invariance.
- Offline checks: all **20,329** older own replay positions, **1,936** Dipam
  positions for the proxy, and **181** YumeNeko positions for the new pilot
  produced legal selections. Modified choices are not reconstructed wins.
- The notebook has **four code cells**, **21 embedded source files**, no saved
  outputs or execution counts. All four cells ran locally with four native
  games (4 wins, 0 losses); its archive contains matching source text and the
  supplied `cg/libcg.so`. This is not a Kaggle Linux run.
- The original policy, original deck, and both pre-existing notebook SHA-256
  hashes match their before-task backups. No Kaggle submission was created.
- Notebook: `decks/alakazam_toucannon/alakazam_toucannon.ipynb`.
- Local archive: `build/notebooks/alakazam_toucannon/submission.tar.gz`.
- Evidence and source hashes: `results/2026-10-26-alakazam-toucannon/`.

Run from the root:

```powershell
python -X utf8 tools/build_notebook.py --agent alakazam_toucannon
python -X utf8 -m pokemon_agent.runner --agent alakazam_toucannon --opponent dragapult_proxy --games 100
python -X utf8 -m pokemon_agent.runner --agent alakazam_toucannon --agent-deck decks/alakazam_toucannon/yume_reference.csv --opponent dragapult_proxy --games 100
python -X utf8 -m decks.alakazam_toucannon.benchmark --games 64 --output results/a-new-comparison.json
```

In Kaggle, import the new notebook, attach the official competition dataset,
and Run All. Packaging does not submit it. It writes to the separate
`/kaggle/working/alakazam-toucannon/` directory.

### What is better than the previous development approach

The concrete improvement is coverage of missing mechanics and explicit
two-action sequences, plus tests that distinguish deck strength from pilot
strength. We measured and rejected the assumption that copying a successful
list automatically improves our agent. The current data does not establish a
stronger overall competitor. For a future learned agent, curated imitation,
diverse frozen opponents and held-out evaluation remain the proposed learning
method; BF16 remains a later hardware/throughput decision. None of those neural
training components is represented as implemented here.
