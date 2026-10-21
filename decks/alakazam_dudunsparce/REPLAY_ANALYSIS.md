# Alakazam/Dudunsparce: episode 125168227

Analyzed on 2026-10-22. **We lost 0–2 to another Alakazam deck.** The clearest problems were premature attacks that skipped safe board development, poor recovery choices, and vulnerability to hand disruption. The opponent's Togekiss also accelerated the Prize race. This match does not show that replacing Alakazam is necessary.

## Evidence and indexing

The full replay contains **299 raw steps, indexed 0–298**, and a separate **299-event visualizer stream**. Seat 0 is masterlincs; seat 1 is our player, Natanael Rehuel S. Both seats finished DONE, with rewards [1, -1]. Input SHA256: `a114769705d8f1b628d2c6dcc5e8d1fc2efa63adb1e4bbec57f96d394c51c12f`.

- An action at raw step **s[t] answers that seat's ACTIVE observation at s[t−1]**. All 297 non-deck choices validate against the corresponding legal options; there are also two deck submissions.
- All 130 of our non-deck choices matched the frozen pre-fix policy. This is strong behavioral agreement, but the replay contains no submitted-source fingerprint.
- **v[n] means a visualizer event, not a raw step.** For example, our first Powerful Hand attack is raw s54 / visualizer v53. After the round-transition event, indices can coincide again. Never assume they are interchangeable.
- All policy comparisons use the actual player's observation, excluding `search_begin_input`. Spectator hidden hands and deck order are never policy inputs. Historical logs establish what happened after decisions.
- The appendix below covers every raw step once. Detailed legal options, visible boards, hands and original policy scores remain in the local ignored audit ledger under `results/2026-10-22-replay-audit/`.

## Why round 1 was lost

We went second. Our first Alakazam took a Prize on turn 4, but Toucannon knocked it out on turn 5. We spent turn 6 rebuilding through Kadabra and dealt only 30 damage. Later attacks traded KOs, while our replacement attackers and draw lines remained underdeveloped.

The priority error is visible before the collapse. At **s54**, Powerful Hand had 11 cards against an 80-HP Kadabra: four cards were enough. Benching a Dunsparce would leave ten cards and preserve the KO, but the original attack score of 1800 beat its setup score of 1000. At **s110**, we had 16 cards against a damaged 120-HP Toucannon: six were enough. Attaching Basic Psychic to the benched Alakazam was legal and would leave 15 cards, yet the pilot attacked first. At **s124**, our final Alakazam line had a large KO margin while Poffin and recovery actions were again skipped.

On turn 11, **s133 / v132**, the opponent played Special Red Card: our 18-card hand went to the bottom of the deck and was replaced by three cards. Togekiss then entered play, and the opponent's KO took two Prizes after a successful Wonder Kiss coin flip. Our next turn had no Abra line left on the field.

Recovery was poor. At **s150**, Poké Pad fetched Alakazam despite no Abra or Kadabra in play, instead of an available Dunsparce that could be benched. At **s152**, Night Stretcher recovered Basic Psychic instead of an Abra, although our only Pokémon was a 60-HP Dunsparce. Energy did not rebuild the missing attacker line.

The final Dunsparce was knocked out on turn 13. **v154 reports reason 3: no Pokémon in the Active Spot.** The opponent also took its final Prize. Recovering one Abra at s152 would preserve field material, but **would not alone save this round**, because the next KO still takes the opponent's last Prize.

We took three KOs and three Prizes. The opponent took five KOs plus one extra Prize from Togekiss. No initial mulligans occurred; our deck never fell below 17 cards. This was not a timeout, illegal action, or deck-out.

## Why round 2 was lost

We chose to go first after one mulligan. At s162, only Retreat and End were legal; the engine did not allow a first-turn Supporter, and our opening lacked Energy. Calling that End an overlooked draw opportunity would be incorrect.

We then established Alakazam and took KOs on turns 5, 7 and 9. The opponent used Enhanced Hammer to remove a Special Energy, so we had to replace it. At **s197**, the same premature-attack pattern remained: 12 cards could KO a damaged 50-HP Kadabra with only three, while legal backup Energy, Kadabra evolution and Dudunsparce development were left unused.

On turn 10, **s248 / v248**, another Special Red Card reduced our 19-card hand to three. Toucannon knocked out the active Alakazam, and newly evolved Togekiss supplied an extra Prize. On our turn 11, recovery produced only a five-card Powerful Hand: **s271 / v271 dealt 100 to a 150-HP Toucannon**, leaving it alive. Toucannon attacked again on turn 12, and a second successful Wonder Kiss gave the opponent another extra Prize.

We knocked out the damaged Toucannon on turn 13. The opponent already had a powered Alakazam ready and one Prize remaining. Its turn-14 KO ended the game: **v298 reports reason 1: zero Prize cards remaining**.

Both players took four KOs in this round, but Togekiss gave the opponent two additional Prizes: a six-to-four Prize result. Our deck stayed at 22 cards or more. Across both rounds, Wonder Kiss flipped five times and produced three heads; that small result is not evidence of biased randomness or a universal deck advantage.

## Changes implemented on `improvement-2-alakazam-replay`

The [policy](policy.py) now handles these concrete weaknesses while keeping the same 60-card deck:

1. **Develop before an ordinary Powerful Hand KO when its hand margin permits.** Useful play, attachment, evolution and benched draw actions can outrank a regular KO only when the same target still falls after the immediate card cost. Rare Candy reserves two cards. Immediate game-winning attacks remain urgent, and the active attacker is not shuffled away for a draw action. This is a conservative hand-cost check, not a full search of every possible consequence.
2. **Recover a functioning board.** Abra receives urgent value when no attacker line exists. Alakazam search/recovery value depends on an evolution route; a usable Kadabra route receives higher priority. An available Basic can outrank redundant Energy or an unusable evolution. Basic selection also favors establishing at least one attacker line and one draw line before redundant copies.
3. **Distinguish equal-Prize KO targets.** Gust and opposing-switch target choices now value visible Togekiss, Toucannon and powered Alakazam threats. Bonuses stay below an additional Prize's value. This is a general improvement: the replay had no legal missed Boss's Orders against an already visible Togekiss. Our Boss cards were available earlier, then removed by Red Card before Togekiss evolved.

**Observed limitation still open:** draw-Supporter sequencing. At s146–147, evolving Dudunsparce and drawing first raised our hand to six, making the current policy decline Lillie's Determination. Using Lillie earlier would change the draw and later choices; it is not a guaranteed winning counterfactual. This sequencing issue has **not** been fixed in this change.

Other remaining limits include shallow lookahead, incomplete valuation of future draw routes and disruption risk, and a narrow local opponent pool. At s269, Poffin spent a card on a Dunsparce that could not evolve that turn. However, omitting that Poffin alone would leave six cards for 120 damage, still short of Toucannon's 150 HP; it was not a single-card explanation for the missed KO.

Battle Cage was correctly left unused in this matchup: it prevents opposing effects from placing damage counters on benched Pokémon. It does not disable Togekiss, and it does not prevent Powerful Hand's counters on the Active Pokémon. Adding Togekiss to its trigger list would be a rules mistake. The supplied SDK documents result reasons in `cg/api.py:320`.

## Local benchmark evidence

The baseline is the pre-fix policy frozen at commit `0549661`. The four reports below use balanced seats and starting orders, with zero reported execution errors. Improved-policy results are from the final policy, including its immediate-win guard; earlier candidate batches are superseded for this comparison.

| Pilot / opponent | Wins / games | Observed rate | 95% Wilson interval |
|---|---:|---:|---:|
| Improved / frozen Alakazam | 161 / 200 | 80.5% | 74.5–85.4% |
| Frozen / our Abomasnow | 88 / 100 | 88.0% | 80.2–93.0% |
| Improved / our Abomasnow | 93 / 100 | 93.0% | 86.3–96.6% |
| Improved / random on Alakazam deck | 39 / 40 | 97.5% | 87.1–99.6% |

These are **independent single games, not BO3 matches**, run locally on Windows. Native deals and coin flips were not seeded, and the old/new batches did not share identical deals. The observed 88% to 93% result against our Abomasnow is encouraging, but is not a paired experiment or proof of a five-point true improvement. The 80.5% result against the frozen same-deck pilot is stronger direct evidence that the changed policy helps against that particular opponent. Neither result proves a Kaggle ladder improvement or compatibility with Kaggle's Linux runtime. Beating random is a sanity check, not a competitive-strength target.

Source reports: `final-candidate-vs-frozen-200.json`, `frozen-vs-abomasnow-100.json`, `final-candidate-vs-abomasnow-100.json`, and `final-candidate-vs-random-40.json` under the ignored audit results folder. Changed choices on saved observations are regression evidence, not replayed wins; this exact historical match has not been rerun under alternate decisions.

All 49 shared and deck-specific tests passed. Both regenerated notebooks executed all four code cells locally, completing four games each without errors. Archive checks verified 15 project source files and the Linux native library in each bundle. Saved notebook outputs remain cleared. The current artifact has **not yet been verified in a Kaggle runtime**; local execution and the presence of a Linux library do not establish that result. Notebook evidence is in `results/2026-10-22-replay-audit/notebook-verification.json`.

## BF16 and opponent training

The current agent is a hand-written scoring policy. It has no neural network, learned weights or neural tensor workload. Changing a numeric format would not teach it to develop a backup attacker or recover Abra.

Opponent training is a plausible next research stage. First build a legal-observation encoder, legal-action mask and small trainable policy/value model; establish a reproducible evaluation harness and measure simulation and inference throughput. Train against a mixture of competent deck pilots and frozen earlier versions, then evaluate against separate frozen opponents that were never used for training. AlphaStar's primary paper describes learning through a diverse league of strategies and counter-strategies; that supports exploring opponent diversity, but its StarCraft result does not establish the best recipe for this Pokémon competition. The held-out evaluation proposal here is our experimental design, not a claimed Pokémon result. [Vinyals et al., Nature (2019)](https://www.nature.com/articles/s41586-019-1724-z).

After a neural baseline is learning, profile where time is spent. If supported hardware and neural operations make precision a bottleneck, compare FP32 with BF16 automatic mixed precision, checking speed, memory, numerical stability and held-out playing strength. PyTorch's AMP supports operation-specific precision and documents BF16 autocasting; gains depend on the actual workload and device. BF16 is an implementation choice for a learner or model, rather than the learning method itself. [PyTorch AMP documentation](https://docs.pytorch.org/docs/2.14/amp.html).

The immediate next competitive test should be more full BO3 replays against varied competent opponents, followed by separate deck ablations. Do not mix a deck change, model change and precision change in one experiment and then attribute all improvement to BF16.

## Appendix: every raw replay step

There is exactly one row for each index 0–298. **P0 is the opponent; P1 is us.** Round/turn belongs to the observation answered by that action. Selection indices are zero-based indices into that observation's legal options; a plain `CARD` can represent a facedown Prize whose identity the decision-maker cannot see. Setup and effect selections are part of the audit, not additional turns. Key decision notes distinguish confirmed mistakes from hypotheses.

| Raw step | Player; round/turn | Context | Recorded action | Note |
|---:|---|---|---|---|
| 0 | P0 and P1; setup | INITIALIZATION | No action yet | Initialization; both players receive deck requests. |
| 1 | P0; setup<br>P1; setup | DECK_SUBMISSION<br>DECK_SUBMISSION | 60-card deck<br>60-card deck | Both legal deck submissions. All later entries are selections. |
| 2 | P0; R1/T0 | IS_FIRST | YES [0] |  |
| 3 | P0; R1/T0 | SETUP_ACTIVE_POKEMON | CARD Dunsparce [1] |  |
| 4 | P1; R1/T0 | SETUP_ACTIVE_POKEMON | CARD Abra [0] |  |
| 5 | P0; R1/T0 | SETUP_BENCH_POKEMON | CARD Togepi, CARD Pikipek [0, 1] |  |
| 6 | P0; R1/T1 | MAIN | PLAY Poké Pad [1] |  |
| 7 | P0; R1/T1 | TO_HAND | CARD Dudunsparce [0] |  |
| 8 | P0; R1/T1 | MAIN | PLAY Poké Pad [1] |  |
| 9 | P0; R1/T1 | TO_HAND | CARD Toucannon [5] |  |
| 10 | P0; R1/T1 | MAIN | PLAY Buddy-Buddy Poffin [0] |  |
| 11 | P0; R1/T1 | TO_BENCH | CARD Abra, CARD Dunsparce [0, 1] |  |
| 12 | P0; R1/T1 | MAIN | PLAY Fezandipiti ex [0] |  |
| 13 | P0; R1/T1 | MAIN | END [0] |  |
| 14 | P1; R1/T2 | MAIN | ATTACH Telepath Psychic Energy -> Abra#63 [2] |  |
| 15 | P1; R1/T2 | TO_BENCH | CARD Abra, CARD Abra [0, 1] |  |
| 16 | P1; R1/T2 | MAIN | PLAY Buddy-Buddy Poffin [2] |  |
| 17 | P1; R1/T2 | TO_BENCH | CARD Dunsparce, CARD Dunsparce [0, 1] |  |
| 18 | P1; R1/T2 | MAIN | PLAY Poké Pad [1] |  |
| 19 | P1; R1/T2 | TO_HAND | CARD Alakazam [0] |  |
| 20 | P1; R1/T2 | MAIN | PLAY Hilda [0] |  |
| 21 | P1; R1/T2 | TO_HAND | CARD Alakazam [1] |  |
| 22 | P1; R1/T2 | TO_HAND | CARD Telepath Psychic Energy [0] |  |
| 23 | P1; R1/T2 | MAIN | ATTACK Teleportation Attack [0] | Abra deals 10; subsequent switch protects the evolving line. |
| 24 | P1; R1/T2 | SWITCH | CARD Dunsparce [2] |  |
| 25 | P0; R1/T3 | MAIN | EVOLVE Dudunsparce -> Dunsparce#14 [1] |  |
| 26 | P0; R1/T3 | MAIN | PLAY Dawn [0] |  |
| 27 | P0; R1/T3 | TO_HAND | CARD Abra [0] |  |
| 28 | P0; R1/T3 | TO_HAND | CARD Kadabra [1] |  |
| 29 | P0; R1/T3 | TO_HAND | CARD Alakazam [0] |  |
| 30 | P0; R1/T3 | MAIN | EVOLVE Kadabra -> Abra#4 [6] |  |
| 31 | P0; R1/T3 | ACTIVATE | YES [0] |  |
| 32 | P0; R1/T3 | MAIN | ABILITY Dudunsparce [12] |  |
| 33 | P0; R1/T3 | TO_ACTIVE | CARD Kadabra [2] |  |
| 34 | P0; R1/T3 | MAIN | ATTACH Basic {P} Energy -> Kadabra#10 [0] |  |
| 35 | P0; R1/T3 | MAIN | ATTACH Handheld Fan -> Pikipek#22 [3] |  |
| 36 | P0; R1/T3 | MAIN | PLAY Abra [0] |  |
| 37 | P0; R1/T3 | MAIN | PLAY Rare Candy [0] |  |
| 38 | P0; R1/T3 | EVOLVE | EVOLVE Toucannon -> Pikipek#22 [0] |  |
| 39 | P0; R1/T3 | MAIN | ABILITY Toucannon [0] |  |
| 40 | P0; R1/T3 | MAIN | EVOLVE Dudunsparce -> Dunsparce#15 [0] |  |
| 41 | P0; R1/T3 | MAIN | ABILITY Dudunsparce [0] |  |
| 42 | P0; R1/T3 | MAIN | PLAY Abra [0] |  |
| 43 | P0; R1/T3 | MAIN | ATTACK Super Psy Bolt [0] |  |
| 44 | P1; R1/T4 | MAIN | RETREAT [10] | Free retreat to the energized Abra. |
| 45 | P1; R1/T4 | SWITCH | CARD Abra [2] |  |
| 46 | P1; R1/T4 | MAIN | EVOLVE Dudunsparce -> Dunsparce#77 [0] |  |
| 47 | P1; R1/T4 | MAIN | EVOLVE Dudunsparce -> Dunsparce#75 [6] |  |
| 48 | P1; R1/T4 | MAIN | ATTACH Telepath Psychic Energy -> Abra#65 [2] |  |
| 49 | P1; R1/T4 | MAIN | ABILITY Dudunsparce [1] |  |
| 50 | P1; R1/T4 | MAIN | ABILITY Dudunsparce [2] |  |
| 51 | P1; R1/T4 | MAIN | PLAY Rare Candy [3] |  |
| 52 | P1; R1/T4 | EVOLVE | EVOLVE Alakazam -> Abra#63 [0] |  |
| 53 | P1; R1/T4 | ACTIVATE | YES [0] |  |
| 54 | P1; R1/T4 | MAIN | ATTACK Powerful Hand [4] | Safe bench development skipped: 11 cards versus 80 HP; KO needs four. |
| 55 | P1; R1/T4 | TO_HAND | CARD [0] |  |
| 56 | P0; R1/T4 | TO_ACTIVE | CARD Toucannon [1] |  |
| 57 | P0; R1/T5 | MAIN | EVOLVE Kadabra -> Abra#3 [5] |  |
| 58 | P0; R1/T5 | ACTIVATE | YES [0] |  |
| 59 | P0; R1/T5 | MAIN | ABILITY Toucannon [13] |  |
| 60 | P0; R1/T5 | MAIN | ABILITY Fezandipiti ex [14] |  |
| 61 | P0; R1/T5 | MAIN | ATTACH Telepath Psychic Energy -> Toucannon#24 [0] |  |
| 62 | P0; R1/T5 | MAIN | PLAY Buddy-Buddy Poffin [4] |  |
| 63 | P0; R1/T5 | TO_BENCH | CARD Dunsparce [0] |  |
| 64 | P0; R1/T5 | MAIN | PLAY Battle Cage [3] |  |
| 65 | P0; R1/T5 | MAIN | PLAY Rare Candy [1] |  |
| 66 | P0; R1/T5 | EVOLVE | EVOLVE Alakazam -> Abra#6 [0] |  |
| 67 | P0; R1/T5 | ACTIVATE | YES [0] |  |
| 68 | P0; R1/T5 | MAIN | PLAY Dawn [2] |  |
| 69 | P0; R1/T5 | TO_HAND | CARD Shaymin [0] |  |
| 70 | P0; R1/T5 | TO_HAND | CARD Dudunsparce [1] |  |
| 71 | P0; R1/T5 | MAIN | ATTACK Feather Rondo [2] | Toucannon knocks out first Alakazam (v70). |
| 72 | P0; R1/T5 | TO_HAND | CARD [0] |  |
| 73 | P1; R1/T5 | TO_ACTIVE | CARD Abra [0] |  |
| 74 | P1; R1/T6 | MAIN | PLAY Abra [11] |  |
| 75 | P1; R1/T6 | MAIN | ATTACH Basic {P} Energy -> Abra#64 [2] |  |
| 76 | P1; R1/T6 | MAIN | PLAY Dunsparce [4] |  |
| 77 | P1; R1/T6 | MAIN | PLAY Poké Pad [3] |  |
| 78 | P1; R1/T6 | TO_HAND | CARD Alakazam [7] |  |
| 79 | P1; R1/T6 | MAIN | PLAY Dawn [3] |  |
| 80 | P1; R1/T6 | TO_HAND | CARD Dunsparce [0] |  |
| 81 | P1; R1/T6 | TO_HAND | CARD Kadabra [0] |  |
| 82 | P1; R1/T6 | MAIN | EVOLVE Kadabra -> Abra#65 [2] |  |
| 83 | P1; R1/T6 | ACTIVATE | YES [0] |  |
| 84 | P1; R1/T6 | MAIN | EVOLVE Kadabra -> Abra#64 [3] |  |
| 85 | P1; R1/T6 | ACTIVATE | YES [0] |  |
| 86 | P1; R1/T6 | MAIN | PLAY Dunsparce [1] |  |
| 87 | P1; R1/T6 | MAIN | ATTACK Super Psy Bolt [2] | Only 30 damage; no legal Alakazam attack is being overlooked here. |
| 88 | P0; R1/T6 | SWITCH_ENERGY | ENERGY Telepath Psychic Energy [0] |  |
| 89 | P0; R1/T6 | ATTACH_FROM | CARD Kadabra [0] | Handheld Fan moves Energy after damage (v88). |
| 90 | P0; R1/T7 | MAIN | EVOLVE Alakazam -> Kadabra#8 [0] |  |
| 91 | P0; R1/T7 | ACTIVATE | YES [0] |  |
| 92 | P0; R1/T7 | MAIN | EVOLVE Dudunsparce -> Dunsparce#14 [8] |  |
| 93 | P0; R1/T7 | MAIN | ABILITY Toucannon [10] |  |
| 94 | P0; R1/T7 | MAIN | PLAY Dawn [10] |  |
| 95 | P0; R1/T7 | TO_HAND | CARD Dudunsparce [0] |  |
| 96 | P0; R1/T7 | MAIN | PLAY Poké Pad [8] |  |
| 97 | P0; R1/T7 | TO_HAND | CARD Kadabra [0] |  |
| 98 | P0; R1/T7 | MAIN | ABILITY Dudunsparce [8] |  |
| 99 | P0; R1/T7 | MAIN | ATTACH Telepath Psychic Energy -> Alakazam#11 [15] |  |
| 100 | P0; R1/T7 | MAIN | PLAY Buddy-Buddy Poffin [6] |  |
| 101 | P0; R1/T7 | TO_BENCH | CARD Dunsparce [0] |  |
| 102 | P0; R1/T7 | MAIN | ATTACK Feather Rondo [2] | Toucannon knocks out Kadabra (v101). |
| 103 | P0; R1/T7 | TO_HAND | CARD [0] |  |
| 104 | P1; R1/T7 | TO_ACTIVE | CARD Kadabra [0] |  |
| 105 | P1; R1/T8 | MAIN | PLAY Rare Candy [18] |  |
| 106 | P1; R1/T8 | EVOLVE | EVOLVE Alakazam -> Abra#66 [0] |  |
| 107 | P1; R1/T8 | ACTIVATE | YES [0] |  |
| 108 | P1; R1/T8 | MAIN | EVOLVE Alakazam -> Kadabra#70 [1] |  |
| 109 | P1; R1/T8 | ACTIVATE | YES [0] |  |
| 110 | P1; R1/T8 | MAIN | ATTACK Powerful Hand [22] | KO preempts safe backup Energy/evolutions; 16 cards versus 120 HP. |
| 111 | P1; R1/T8 | TO_HAND | CARD [0] |  |
| 112 | P0; R1/T8 | TO_ACTIVE | CARD Alakazam [2] |  |
| 113 | P0; R1/T9 | MAIN | ABILITY Fezandipiti ex [21] |  |
| 114 | P0; R1/T9 | MAIN | PLAY Hilda [11] |  |
| 115 | P0; R1/T9 | TO_HAND | CARD Dudunsparce [0] |  |
| 116 | P0; R1/T9 | MAIN | ATTACH Enriching Energy -> Dunsparce#14 [5] |  |
| 117 | P0; R1/T9 | MAIN | PLAY Poké Pad [10] |  |
| 118 | P0; R1/T9 | MAIN | ATTACK Powerful Hand [10] | Opponent knocks out Alakazam (v117). |
| 119 | P0; R1/T9 | TO_HAND | CARD [0] |  |
| 120 | P1; R1/T9 | TO_ACTIVE | CARD Dunsparce [1] |  |
| 121 | P1; R1/T10 | MAIN | ATTACH Telepath Psychic Energy -> Alakazam#73 [21] |  |
| 122 | P1; R1/T10 | MAIN | RETREAT [12] |  |
| 123 | P1; R1/T10 | SWITCH | CARD Alakazam [0] |  |
| 124 | P1; R1/T10 | MAIN | ATTACK Powerful Hand [12] | Last Abra line active; useful Poffin/recovery/Red Card are skipped. |
| 125 | P1; R1/T10 | TO_HAND | CARD [0] |  |
| 126 | P0; R1/T10 | TO_ACTIVE | CARD Dunsparce [3] |  |
| 127 | P0; R1/T11 | MAIN | EVOLVE Dudunsparce -> Dunsparce#14 [8] |  |
| 128 | P0; R1/T11 | MAIN | PLAY Hilda [20] |  |
| 129 | P0; R1/T11 | MAIN | ATTACH Telepath Psychic Energy -> Alakazam#13 [11] |  |
| 130 | P0; R1/T11 | MAIN | PLAY Buddy-Buddy Poffin [8] |  |
| 131 | P0; R1/T11 | MAIN | PLAY Pikipek [1] |  |
| 132 | P0; R1/T11 | MAIN | PLAY Dunsparce [2] |  |
| 133 | P0; R1/T11 | MAIN | PLAY Special Red Card [2] | Red Card bottoms 18-card hand and draws three (v132). |
| 134 | P0; R1/T11 | MAIN | PLAY Rare Candy [2] |  |
| 135 | P0; R1/T11 | EVOLVE | EVOLVE Togekiss -> Togepi#20 [0] | Togekiss enters play (v134). |
| 136 | P0; R1/T11 | MAIN | PLAY Night Stretcher [0] |  |
| 137 | P0; R1/T11 | TO_HAND | CARD Abra [1] |  |
| 138 | P0; R1/T11 | MAIN | PLAY Sacred Ash [0] |  |
| 139 | P0; R1/T11 | TO_DECK | CARD Kadabra, CARD Toucannon, CARD Pikipek, CARD Alakazam, CARD Kadabra [0, 1, 2, 3, 4] |  |
| 140 | P0; R1/T11 | MAIN | ABILITY Fezandipiti ex [1] |  |
| 141 | P0; R1/T11 | MAIN | ABILITY Dudunsparce [1] |  |
| 142 | P0; R1/T11 | TO_ACTIVE | CARD Alakazam [2] |  |
| 143 | P0; R1/T11 | MAIN | ATTACK Powerful Hand [5] | Alakazam KO plus Wonder Kiss heads: opponent takes two Prizes (v142). |
| 144 | P0; R1/T11 | TO_HAND | CARD, CARD [0, 1] |  |
| 145 | P1; R1/T11 | TO_ACTIVE | CARD Dunsparce [0] |  |
| 146 | P1; R1/T12 | MAIN | EVOLVE Dudunsparce -> Dunsparce#77 [0] | Lillie sequencing remains unresolved: evolution outranks legal refresh. |
| 147 | P1; R1/T12 | MAIN | ABILITY Dudunsparce [1] | Draw first raises hand to six and disables the Lillie heuristic. |
| 148 | P1; R1/T12 | TO_ACTIVE | CARD Dunsparce [0] |  |
| 149 | P1; R1/T12 | MAIN | PLAY Poké Pad [2] |  |
| 150 | P1; R1/T12 | TO_HAND | CARD Alakazam [1] | Pad chooses unusable Alakazam over a benchable Dunsparce. |
| 151 | P1; R1/T12 | MAIN | PLAY Night Stretcher [1] |  |
| 152 | P1; R1/T12 | TO_HAND | CARD Basic {P} Energy [7] | Stretcher chooses Energy while no attacker line remains; Abra is legal. |
| 153 | P1; R1/T12 | MAIN | END [2] | No attack or recovered Basic; only Dunsparce remains. |
| 154 | P0; R1/T13 | MAIN | ATTACK Powerful Hand [24] | Final Dunsparce KO (v153). |
| 155 | P0; R1/T13 | TO_HAND | CARD [0] | Round 1 ends: no Active Pokémon, reason 3 (v154). Enemy also takes final Prize. |
| 156 | P1; R2/T0 | IS_FIRST | YES [0] | After losing, choose to go first in round 2. |
| 157 | P0; R2/T0 | SETUP_ACTIVE_POKEMON | CARD Abra [0] |  |
| 158 | P1; R2/T0 | SETUP_ACTIVE_POKEMON | CARD Dunsparce [0] |  |
| 159 | P0; R2/T0 | DRAW_COUNT | NUMBER [0] | Opponent receives bonus draw after our one mulligan. |
| 160 | P1; R2/T0 | SETUP_BENCH_POKEMON | CARD Abra [0] |  |
| 161 | P0; R2/T0 | SETUP_BENCH_POKEMON | CARD Abra [0] |  |
| 162 | P1; R2/T1 | MAIN | END [1] | Only Retreat/End legal; first-turn Supporter is unavailable. |
| 163 | P0; R2/T2 | MAIN | PLAY Poké Pad [2] |  |
| 164 | P0; R2/T2 | TO_HAND | CARD Kadabra [11] |  |
| 165 | P0; R2/T2 | MAIN | PLAY Buddy-Buddy Poffin [1] |  |
| 166 | P0; R2/T2 | TO_BENCH | CARD Dunsparce, CARD Abra [0, 2] |  |
| 167 | P0; R2/T2 | MAIN | ATTACH Handheld Fan -> Dunsparce#14 [3] |  |
| 168 | P0; R2/T2 | MAIN | END [1] |  |
| 169 | P1; R2/T3 | MAIN | EVOLVE Dudunsparce -> Dunsparce#78 [2] |  |
| 170 | P1; R2/T3 | MAIN | ATTACH Basic {P} Energy -> Abra#65 [4] |  |
| 171 | P1; R2/T3 | MAIN | ABILITY Dudunsparce [3] |  |
| 172 | P1; R2/T3 | TO_ACTIVE | CARD Abra [0] |  |
| 173 | P1; R2/T3 | MAIN | PLAY Buddy-Buddy Poffin [4] |  |
| 174 | P1; R2/T3 | TO_BENCH | CARD Abra, CARD Abra [0, 3] |  |
| 175 | P1; R2/T3 | MAIN | PLAY Dawn [2] |  |
| 176 | P1; R2/T3 | TO_HAND | CARD Dunsparce [0] |  |
| 177 | P1; R2/T3 | TO_HAND | CARD Kadabra [2] |  |
| 178 | P1; R2/T3 | TO_HAND | CARD Alakazam [0] |  |
| 179 | P1; R2/T3 | MAIN | EVOLVE Kadabra -> Abra#65 [1] |  |
| 180 | P1; R2/T3 | ACTIVATE | YES [0] |  |
| 181 | P1; R2/T3 | MAIN | PLAY Dunsparce [0] |  |
| 182 | P1; R2/T3 | MAIN | ATTACK Super Psy Bolt [0] |  |
| 183 | P0; R2/T4 | MAIN | EVOLVE Dudunsparce -> Dunsparce#14 [1] |  |
| 184 | P0; R2/T4 | MAIN | EVOLVE Kadabra -> Abra#4 [1] |  |
| 185 | P0; R2/T4 | ACTIVATE | YES [0] |  |
| 186 | P0; R2/T4 | MAIN | EVOLVE Kadabra -> Abra#3 [1] |  |
| 187 | P0; R2/T4 | ACTIVATE | YES [0] |  |
| 188 | P0; R2/T4 | MAIN | EVOLVE Kadabra -> Abra#6 [3] |  |
| 189 | P0; R2/T4 | ACTIVATE | YES [0] |  |
| 190 | P0; R2/T4 | MAIN | ABILITY Dudunsparce [3] |  |
| 191 | P0; R2/T4 | MAIN | PLAY Buddy-Buddy Poffin [3] |  |
| 192 | P0; R2/T4 | TO_BENCH | CARD Togepi, CARD Pikipek [1, 2] |  |
| 193 | P0; R2/T4 | MAIN | PLAY Shaymin [1] |  |
| 194 | P0; R2/T4 | MAIN | END [1] |  |
| 195 | P1; R2/T5 | MAIN | EVOLVE Alakazam -> Kadabra#70 [0] |  |
| 196 | P1; R2/T5 | ACTIVATE | YES [0] |  |
| 197 | P1; R2/T5 | MAIN | ATTACK Powerful Hand [16] | Ordinary KO skips legal backup setup: 12 cards versus 50 HP. |
| 198 | P1; R2/T5 | TO_HAND | CARD [0] |  |
| 199 | P0; R2/T5 | TO_ACTIVE | CARD Kadabra [0] |  |
| 200 | P0; R2/T6 | MAIN | EVOLVE Alakazam -> Kadabra#7 [1] |  |
| 201 | P0; R2/T6 | ACTIVATE | YES [0] |  |
| 202 | P0; R2/T6 | MAIN | EVOLVE Alakazam -> Kadabra#9 [1] |  |
| 203 | P0; R2/T6 | ACTIVATE | YES [0] |  |
| 204 | P0; R2/T6 | MAIN | PLAY Poké Pad [6] |  |
| 205 | P0; R2/T6 | TO_HAND | CARD Dunsparce [1] |  |
| 206 | P0; R2/T6 | MAIN | ATTACH Basic {P} Energy -> Alakazam#12 [7] |  |
| 207 | P0; R2/T6 | MAIN | ATTACK Powerful Hand [8] | Opponent KO on Alakazam; no Wonder Kiss yet. |
| 208 | P0; R2/T6 | TO_HAND | CARD [0] |  |
| 209 | P1; R2/T6 | TO_ACTIVE | CARD Dunsparce [2] |  |
| 210 | P1; R2/T7 | MAIN | PLAY Rare Candy [12] |  |
| 211 | P1; R2/T7 | EVOLVE | EVOLVE Alakazam -> Abra#66 [0] |  |
| 212 | P1; R2/T7 | ACTIVATE | YES [0] |  |
| 213 | P1; R2/T7 | MAIN | EVOLVE Kadabra -> Abra#64 [12] |  |
| 214 | P1; R2/T7 | ACTIVATE | YES [0] |  |
| 215 | P1; R2/T7 | MAIN | ATTACH Telepath Psychic Energy -> Alakazam#73 [4] |  |
| 216 | P1; R2/T7 | TO_BENCH | CARD Abra [0] |  |
| 217 | P1; R2/T7 | MAIN | RETREAT [12] |  |
| 218 | P1; R2/T7 | SWITCH | CARD Alakazam [0] |  |
| 219 | P1; R2/T7 | MAIN | ATTACK Powerful Hand [12] | Another ordinary KO while safe development remains available. |
| 220 | P1; R2/T7 | TO_HAND | CARD [0] |  |
| 221 | P0; R2/T7 | TO_ACTIVE | CARD Alakazam [0] |  |
| 222 | P0; R2/T8 | MAIN | PLAY Dunsparce [1] |  |
| 223 | P0; R2/T8 | MAIN | PLAY Abra [2] |  |
| 224 | P0; R2/T8 | MAIN | PLAY Battle Cage [2] |  |
| 225 | P0; R2/T8 | MAIN | PLAY Rare Candy [1] |  |
| 226 | P0; R2/T8 | EVOLVE | EVOLVE Toucannon -> Pikipek#22 [0] |  |
| 227 | P0; R2/T8 | MAIN | ABILITY Toucannon [2] |  |
| 228 | P0; R2/T8 | MAIN | PLAY Enhanced Hammer [2] | Enhanced Hammer removes our Special Energy. |
| 229 | P0; R2/T8 | DISCARD_ENERGY | ENERGY Telepath Psychic Energy [0] |  |
| 230 | P0; R2/T8 | MAIN | END [2] |  |
| 231 | P1; R2/T9 | MAIN | EVOLVE Alakazam -> Kadabra#69 [3] |  |
| 232 | P1; R2/T9 | ACTIVATE | YES [0] |  |
| 233 | P1; R2/T9 | MAIN | ATTACH Telepath Psychic Energy -> Alakazam#73 [5] |  |
| 234 | P1; R2/T9 | MAIN | ATTACK Powerful Hand [14] | KO obtained, but opponent disruption is about to expose thin development. |
| 235 | P1; R2/T9 | TO_HAND | CARD [0] |  |
| 236 | P0; R2/T9 | TO_ACTIVE | CARD Toucannon [1] |  |
| 237 | P0; R2/T10 | MAIN | EVOLVE Dudunsparce -> Dunsparce#15 [1] |  |
| 238 | P0; R2/T10 | MAIN | ABILITY Toucannon [10] |  |
| 239 | P0; R2/T10 | MAIN | ABILITY Dudunsparce [11] |  |
| 240 | P0; R2/T10 | MAIN | PLAY Lana’s Aid [9] |  |
| 241 | P0; R2/T10 | TO_HAND | CARD Kadabra, CARD Kadabra, CARD Kadabra [0, 3, 7] |  |
| 242 | P0; R2/T10 | MAIN | EVOLVE Kadabra -> Abra#5 [13] |  |
| 243 | P0; R2/T10 | ACTIVATE | YES [0] |  |
| 244 | P0; R2/T10 | MAIN | ATTACH Enriching Energy -> Toucannon#25 [3] |  |
| 245 | P0; R2/T10 | MAIN | PLAY Dunsparce [0] |  |
| 246 | P0; R2/T10 | MAIN | PLAY Fezandipiti ex [0] |  |
| 247 | P0; R2/T10 | MAIN | ABILITY Fezandipiti ex [5] |  |
| 248 | P0; R2/T10 | MAIN | PLAY Special Red Card [2] | Red Card bottoms 19-card hand and draws three. |
| 249 | P0; R2/T10 | MAIN | PLAY Rare Candy [0] |  |
| 250 | P0; R2/T10 | EVOLVE | EVOLVE Togekiss -> Togepi#20 [0] | Togekiss enters play. |
| 251 | P0; R2/T10 | MAIN | ATTACK Feather Rondo [2] | Toucannon KO plus Wonder Kiss heads: opponent takes two Prizes. |
| 252 | P0; R2/T10 | TO_HAND | CARD, CARD [0, 1] |  |
| 253 | P1; R2/T10 | TO_ACTIVE | CARD Dunsparce [0] |  |
| 254 | P1; R2/T11 | MAIN | EVOLVE Kadabra -> Abra#63 [0] |  |
| 255 | P1; R2/T11 | ACTIVATE | YES [0] |  |
| 256 | P1; R2/T11 | MAIN | ATTACH Basic {P} Energy -> Alakazam#72 [2] |  |
| 257 | P1; R2/T11 | MAIN | RETREAT [3] |  |
| 258 | P1; R2/T11 | SWITCH | CARD Alakazam [0] |  |
| 259 | P1; R2/T11 | MAIN | PLAY Poké Pad [1] |  |
| 260 | P1; R2/T11 | TO_HAND | CARD Alakazam [6] |  |
| 261 | P1; R2/T11 | MAIN | PLAY Dawn [1] |  |
| 262 | P1; R2/T11 | TO_HAND | CARD Dunsparce [0] |  |
| 263 | P1; R2/T11 | TO_HAND | CARD Dudunsparce [0] |  |
| 264 | P1; R2/T11 | MAIN | EVOLVE Dudunsparce -> Dunsparce#77 [1] |  |
| 265 | P1; R2/T11 | MAIN | PLAY Dunsparce [0] |  |
| 266 | P1; R2/T11 | MAIN | ABILITY Dudunsparce [0] |  |
| 267 | P1; R2/T11 | MAIN | PLAY Poké Pad [1] |  |
| 268 | P1; R2/T11 | TO_HAND | CARD Dudunsparce [0] | Dudunsparce fetched without a remaining same-turn evolution route. |
| 269 | P1; R2/T11 | MAIN | PLAY Buddy-Buddy Poffin [0] | Poffin costs one hand card; skipping it alone still would not reach 150 damage. |
| 270 | P1; R2/T11 | TO_BENCH | CARD Dunsparce [0] |  |
| 271 | P1; R2/T11 | MAIN | ATTACK Powerful Hand [0] | Powerful Hand deals 100 to 150-HP Toucannon; no KO. |
| 272 | P0; R2/T12 | MAIN | EVOLVE Alakazam -> Kadabra#10 [1] |  |
| 273 | P0; R2/T12 | ACTIVATE | YES [0] |  |
| 274 | P0; R2/T12 | MAIN | EVOLVE Dudunsparce -> Dunsparce#16 [8] |  |
| 275 | P0; R2/T12 | MAIN | ABILITY Toucannon [26] |  |
| 276 | P0; R2/T12 | MAIN | PLAY Dawn [9] |  |
| 277 | P0; R2/T12 | MAIN | ABILITY Dudunsparce [20] |  |
| 278 | P0; R2/T12 | MAIN | PLAY Poké Pad [22] |  |
| 279 | P0; R2/T12 | TO_HAND | CARD Dunsparce [1] |  |
| 280 | P0; R2/T12 | MAIN | ATTACH Telepath Psychic Energy -> Alakazam#13 [4] |  |
| 281 | P0; R2/T12 | MAIN | PLAY Buddy-Buddy Poffin [3] |  |
| 282 | P0; R2/T12 | MAIN | PLAY Buddy-Buddy Poffin [5] |  |
| 283 | P0; R2/T12 | MAIN | PLAY Dunsparce [0] |  |
| 284 | P0; R2/T12 | MAIN | ATTACK Feather Rondo [2] | Toucannon KO plus second Wonder Kiss heads; opponent has one Prize left. |
| 285 | P0; R2/T12 | TO_HAND | CARD, CARD [0, 1] |  |
| 286 | P1; R2/T12 | TO_ACTIVE | CARD Dunsparce [1] |  |
| 287 | P1; R2/T13 | MAIN | EVOLVE Alakazam -> Kadabra#67 [1] |  |
| 288 | P1; R2/T13 | ACTIVATE | YES [0] |  |
| 289 | P1; R2/T13 | MAIN | EVOLVE Dudunsparce -> Dunsparce#75 [2] |  |
| 290 | P1; R2/T13 | MAIN | EVOLVE Dudunsparce -> Dunsparce#77 [2] |  |
| 291 | P1; R2/T13 | MAIN | ABILITY Dudunsparce [3] |  |
| 292 | P1; R2/T13 | TO_ACTIVE | CARD Alakazam [0] |  |
| 293 | P1; R2/T13 | MAIN | ATTACH Basic {P} Energy -> Alakazam#74 [4] |  |
| 294 | P1; R2/T13 | MAIN | ATTACK Powerful Hand [5] | 160 damage knocks out the previously damaged Toucannon. |
| 295 | P1; R2/T13 | TO_HAND | CARD [0] |  |
| 296 | P0; R2/T13 | TO_ACTIVE | CARD Alakazam [2] |  |
| 297 | P0; R2/T14 | MAIN | ATTACK Powerful Hand [30] | Ready opposing Alakazam knocks out our active; Wonder Kiss tails. |
| 298 | P0; R2/T14 | TO_HAND | CARD [0] | Opponent takes final Prize. Round 2/match ends, reason 1 (v298). |

Coverage verified: **299 contiguous raw-step rows (0–298)**, including initialization and the terminal Prize selection. The separate visualizer stream has 299 events; all events were inspected in the local audit.
