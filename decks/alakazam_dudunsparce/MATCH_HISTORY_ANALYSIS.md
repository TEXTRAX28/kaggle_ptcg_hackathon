# Submission 57640356: complete match-history review

Reviewed on 2026-10-26. **The submitted agent is a functioning heuristic with clear strengths, but it makes serious strategic mistakes against protection and disruption.** Its 54.3% match win rate in this snapshot is substantially less reassuring than its earlier results against our own Abomasnow pilot. Fixing a rules error is useful; it does not establish that the resulting agent will climb the ladder.

## What was actually reviewed

- All **130 rows** in the loaded history snapshot: **129 matches against other players**, plus one match between two of the user's submissions. The snapshot runs from 2026-10-25 into 2026-10-26; its latest opponent match is episode 125433619, displayed as 16:00:08 UTC. Later matches are outside this snapshot.
- All 129 opponent replays were downloaded in full: **38,300 raw steps**, **299 individual rounds**, **95 distinct opponent names**, and **1,032,371,863 bytes** of raw replay data. The self-match 125382210 is archived separately and excluded from statistics because both seats have the same display name.
- Every one of the **38,042 non-deck selections across both seats** validated against its preceding ACTIVE observation. Both players finished DONE in these replays. The losses are not explained by illegal selections or execution failures in this sample.
- All **20,329 own selections** exactly matched the frozen local pre-review policy, and all 129 own deck lists matched. This is strong behavioral agreement; the replays do not contain a submitted-source fingerprint.
- Every recorded choice and the full event streams were screened programmatically. Critical turns were then inspected tactically. This is not a claim that every alternative line in 38,300 steps was manually solved.
- An action at raw step **s[t] answers the ACTIVE observation at s[t-1]**. Visualizer indices **v[n]** are separate. Spectator states describe historical outcomes only; policy checks use the actual player's observation without `search_begin_input`.

Evidence is saved under `results/2026-10-26-submission-57640356/`: the download manifest has hashes and sizes; `decision-ledger.jsonl` covers every own selection; `episodes/` contains every match audit; `history-audit.json` contains aggregate counts and matchup groups.

## Results and what they mean

**70 match wins, 59 losses, no draws: 54.3%.** Individual rounds were 161 wins and 138 losses. These are observed results against the sampled submissions, not universal archetype win rates. Archetype labels below are assigned from the actual submitted card lists; hybrid and small-sample categories deserve caution.

| Opposing deck group | Match wins | Match losses | Observed win rate |
|---|---:|---:|---:|
| Dragapult ex | 6 | 15 | 28.6% |
| Alakazam | 10 | 11 | 47.6% |
| Mega Lucario ex | 12 | 3 | 80.0% |
| Crustle | 3 | 12 | 20.0% |
| Mega Abomasnow ex | 13 | 0 | 100.0% |
| Dipplin | 5 | 2 | 71.4% |
| Mega Froslass ex | 5 | 2 | 71.4% |
| Teal Mask Ogerpon ex | 3 | 3 | 50.0% |
| Archaludon ex | 4 | 2 | 66.7% |
| Marnie's Grimmsnarl ex | 2 | 1 | 66.7% |
| Mega Kangaskhan ex/Latias ex | 0 | 2 | 0.0% |
| Latias ex/Lillie’s Clefairy ex | 2 | 0 | 100.0% |
| Fezandipiti ex/Latias ex | 0 | 2 | 0.0% |
| Mega Starmie ex | 1 | 0 | 100.0% |
| Lillie’s Clefairy ex | 0 | 1 | 0.0% |
| Lillie’s Clefairy ex/Bloodmoon Ursaluna ex | 0 | 1 | 0.0% |
| Mega Excadrill ex/Genesect ex | 1 | 0 | 100.0% |
| Other | 1 | 0 | 100.0% |
| Bloodmoon Ursaluna ex/Lillie’s Clefairy ex | 0 | 1 | 0.0% |
| Iono’s Bellibolt ex | 1 | 0 | 100.0% |
| Mega Absol ex | 1 | 0 | 100.0% |
| Steven's Metagross ex | 0 | 1 | 0.0% |

Crustle and Dragapult account for **27 of the 59 losses**. Those are the first matchups to address. The Alakazam mirror is close to even, so improving threat selection and recovery also has value. Going first was associated with 101/180 round wins; going second with 60/119. Starting order was not randomized here and is affected by match choices, so this comparison is not proof of a causal advantage.

## Good play and a sound core

The one-Prize plan works against the sampled large attackers: the agent went **13-0 against Mega Abomasnow ex groups** and **12-3 against Mega Lucario ex groups**. A sufficiently large hand lets Alakazam exchange a one-Prize attacker for a multi-Prize knockout. The evolution/draw engine can develop several attackers and produce real knockout pressure without a high Energy requirement.

The agent also makes useful resource preparations before ordinary knockouts while preserving enough cards for the same KO. It takes immediate wins in the reviewed ordinary positions, uses the free-retreat pivot, and can exploit exposed multi-Prize support Pokémon. In the linked Mandavi match, **s63** gusting Fezandipiti ex for two Prizes was a reasonable concrete conversion of hand size into a Prize lead. A subsequent loss does not make every earlier action wrong.

The code reliably follows legal choices in the full sample. That is a useful foundation, but beating a random player or our own Abomasnow is an insufficient measure of competitive strength. The broader history exposes problems those benchmarks do not exercise.

## Bad play: protection is the largest confirmed error

Of **1,111 Powerful Hand attacks**, **196 were nullified by visible protection**: **163 by Mist Energy or applicable Rock Fighting Energy**, and **33 by protective Abilities**. These attacks occurred in 20 matches, with 4 wins and 16 losses. The association does not prove that every one of those losses would become a win after a fix.

Powerful Hand places damage counters through an attack effect. **Mist Energy stops that effect.** Rock Fighting Energy does so on a Fighting Pokémon. In episode **125418713**, **s32** was scored as an immediate win against a lone protected Crustle. Later, **s177** was scored as another winning attack against a protected Cornerstone Mask Ogerpon ex. Neither attack could deliver the predicted KO. Repeating the attack while refusing development because the evaluator thinks the game is already won is a rules-model failure.

Damage-only protection is different: Cornerstone Stance by itself does not stop Powerful Hand, and Crustle's anti-ex damage Ability is not what stops this non-ex Alakazam. Treating these Abilities as the cause would prescribe the wrong counter.

There are also walls that Enhanced Hammer cannot solve. Poltchageist, Shuppet and Banette variants with **Hide 'n' Sneak** prevent attack effects through their own Abilities. The first such recorded failure in episode **125383877** is **s21**. Team Rocket's Articuno also protected a Basic Team Rocket's Murkrow in episode **125386807**, **v117**. Removing Energy does not remove those Abilities. A competitive deck needs an explicit route around each form of protection: Energy removal, an unprotected gust target, suitable ordinary attack damage, or a tested Ability-denial plan.

One other zero-effect attack had a different cause. In episode **125409292**, **s310**, our confused Alakazam had 20 HP and two powered Alakazam on the Bench. Retreat was legal and preserved the same KO. The original policy attacked, lost the Confusion flip, and knocked itself out. This was an avoidable coin flip, not another protection effect.

## Bad play: large hands are fragile resources

The linked match **125433324** was a **1-2 loss to Mandavi Singh**. We won round 2 by removing the opponent's only Pokémon; the longer rounds exposed weaknesses in recovery and target selection.

In round 3, **s310** still had legal Boss's Orders and unpowered opposing Alakazam on the Bench. The old evaluator gave those threats the same one-Prize value as the active Dunsparce, used development and then Dawn, and eventually took the Dunsparce at **s321**. Removing a built Stage 2 attacker can matter more than taking an interchangeable Basic. This was a credible stronger line, not a proven alternate match win.

The opponent then played Xerosic's Machinations and our hand fell from **26 to 3** around **v325-v327**; Enhanced Hammer also attacked our Energy supply. A hand of 20-plus cards is not durable board strength. The policy needs powered replacement attackers and a recovery Supporter plan that still functions after a reset.

At **s353**, our deck contained four cards and our hand held two Hilda plus Lillie's Determination. Hilda was legal, but the policy rejected it solely because its blanket search cutoff required more than four cards in the deck. It ended the turn. **s360**, with three cards left, repeated the pattern. Search and draw effects have different deck-out implications. Searching up to two cards from four or three can leave a natural draw; refusing even to search forfeits a chance to recover. This observation does not prove that the remaining hidden cards would produce a match win.

There are also earlier Supporter sequencing mistakes. In episode **125415699**, **s90**, we had two unpowered Alakazam, no Energy in hand, an unused attachment and legal Hilda. The agent chose Lillie's random redraw and ended that turn without an attack. A targeted search for attack Energy better addresses the visible bottleneck. Across the sample, four decisions had this same missing-Energy/available-Hilda pattern; availability of a legal search is not proof that a particular card remains outside the Prizes.

The older replay **125168227**, **s147**, supplies a separate regression: Run Away Draw was used before a useful Lillie refresh, inflating the hand enough to discourage the Supporter. Refreshing while the draw Pokémon remains on the field preserves a subsequent draw route. Ordinary KO and immediate-win constraints still matter; this is not a universal instruction to redraw before every action.

## Bad play: Dragapult punishes the bench and the hand together

The **6-15 Dragapult result** is a real warning. Multiple 50-60 HP Basics can become additional Prizes while the Active is knocked out. Bench development needs to account for that pressure, not just count how many evolution lines exist.

Episode **125431219** illustrates it. In round 1, Dragapult's turn-8 sequence at **v114-v120** knocked out the active Dunsparce and placed six counters on the remaining Dunsparce, ending the round with no Pokémon left. In round 2, Hand Trimmer and Unfair Stamp combined with Phantom Dive to leave very small hands and damaged evolution lines. Battle Cage finally appeared at **v235** and later counter-placement logs show zero, but the earlier material and tempo losses had already accumulated.

The old Cage trigger recognized only fully evolved Dragapult, Dusclops and Dusknoir. It could decline Cage while their Basic or Stage 1 precursors were visible, then lose the opportunity before the next evolution and attack. Earlier deployment is a concrete improvement. It does not ensure Cage will be drawn, remain in play or prevent damage to the Active, and it does not make every Basic worth benching into this matchup.

## Changes made and what remains open

The default 60-card deck is unchanged. The local Alakazam pilot now:

1. Recognizes the observed protective Energies, the attack-effect-blocking Ability families, and relevant conditional protection. Gust scoring uses the target's protection as the prospective Active Pokémon; bench-only protection is not treated as an Active wall.
2. Gives an opposing unpowered Alakazam a threat bonus when comparing equal-Prize gust targets.
3. Prioritizes Hilda for missing attack Energy when an attachment and a plausible Telepath search route remain. Already revealed exhausted copies do not receive that urgency.
4. Allows Dawn/Hilda searches at safe smaller deck sizes rather than using one blanket cutoff for both.
5. Defers the draw Ability when a useful Lillie refresh should happen first, within the existing KO safeguards.
6. Recognizes Dreepy, Drakloak and Duskull as reasons to deploy Battle Cage early.
7. Retreats a confused attacker to a ready replacement when that preserves a certain KO.
8. Supports Enhanced Hammer and chooses protective Energy ahead of unrelated Special Energy in the experimental variant.

Nine sanitized historical observations and thirteen new tests cover these changes, alongside the existing tests. These remain hand-written scores. The pilot does not solve a full turn or a multi-turn Prize race, and the protection model is not a complete implementation of every possible effect. Recognizing an impenetrable wall does not give the unchanged deck a way to beat it. Draw sequencing, future disruption, retreat costs, finite recovery resources and matchup-specific bench sizing still require deeper planning and evaluation.

## Experimental deck: two Enhanced Hammer

`results/2026-10-26-submission-57640356/tech-deck.csv` is a valid 60-card experimental list using the same Pokémon engine. It adds **two Enhanced Hammer**, removes **one Basic Psychic Energy** and **one Lana's Aid**, and has seven Energy total. It has not replaced the default list.

This is a test of a counter package, not a proven better deck. It addresses removable Special Energy; it does not solve Hide 'n' Sneak, and two Hammers may be insufficient against multiple stacked protection Energies. Cutting a Basic Energy also has a real consistency and disruption-resilience cost. The next deck experiment should explicitly measure that tradeoff against competent protection and Dragapult pilots, with other matchups held out. An ordinary-damage attacker or a tested Ability-denial route is a separate hypothesis for permanent Ability walls.

## Final local verification

**62 shared and deck tests pass.** Both maintained notebooks were regenerated with four code cells, no Markdown and cleared saved outputs. All four cells ran locally for each notebook, completing four games each. Both archives matched their 15 embedded project sources, included `cg/libcg.so`, and their packaged Python compiled.

The following final cohorts used the final policy, balanced both seats and starting orders, and reported no execution errors:

| Deck / opponent | Wins / games |
|---|---:|
| Default / frozen submitted pilot | 51 / 100 |
| Hammer experiment / frozen submitted pilot | 44 / 100 |
| Default / our Abomasnow | 56 / 60 |
| Hammer experiment / our Abomasnow | 57 / 60 |
| Default / random | 40 / 40 |
| Hammer experiment / random | 40 / 40 |

All **20,329** saved own decision positions also passed a legality check under the final policy: **1,276** choices changed across **106** matches. Changed choices are offline position checks, not rerun historical wins.

There were 400 games in these final local cohorts. They were independent single games on Windows, with unseeded native deals and no paired identical deals. **51/100 against the old pilot does not establish an overall strength increase.** The Hammer experiment also has not earned promotion to the default deck. The earlier preliminary cohorts are retained separately; they are not substituted for the final results. No new Kaggle run, competition submission, Git commit, merge or push was performed for these changes.

The next useful competitive evidence is a fresh held-out BO3 sample against competent Crustle/protection, Dragapult and mirror opponents. Improvements should be judged by successful Prize routes and recovery under disruption, not just by hand size, damage scores or wins against our own favorable matchup.

## Every opponent match in the snapshot

The table below accounts for all 129 opponent replays exactly once. The score is our individual-round wins and losses; the result is the whole BO3 match. Episode links return to Kaggle's corresponding replay.

| Episode | Opponent | Deck group | Match result | Round score | Raw steps |
|---|---|---|---|---:|---:|
| [125433619](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125433619) | Omar Kamal | Alakazam | win | 2-0 | 376 |
| [125433324](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125433324) | Mandavi Singh | Alakazam | loss | 1-2 | 367 |
| [125432319](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125432319) | Ted Mothwake | Mega Froslass ex | win | 2-1 | 208 |
| [125432299](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125432299) | Amedeo Biolatti | Archaludon ex | loss | 1-2 | 429 |
| [125431219](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125431219) | hiro yoko | Dragapult ex | loss | 0-2 | 293 |
| [125430220](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125430220) | Tianyu Hou | Alakazam | win | 2-1 | 458 |
| [125429707](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125429707) | Ted Mothwake | Mega Froslass ex | win | 2-0 | 196 |
| [125429371](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125429371) | Kydyrbek Kozykorpesh | Archaludon ex | win | 2-1 | 349 |
| [125428817](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125428817) | Chriszcodes | Dragapult ex | loss | 0-2 | 278 |
| [125427729](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125427729) | NK49540 | Mega Lucario ex | win | 2-0 | 268 |
| [125426700](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125426700) | Shixiang Yan | Mega Abomasnow ex | win | 2-0 | 53 |
| [125425660](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125425660) | Tushar Anand | Crustle | loss | 1-2 | 376 |
| [125425651](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125425651) | Paal | Alakazam | win | 2-0 | 269 |
| [125424541](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125424541) | john inan | Mega Abomasnow ex | win | 2-0 | 227 |
| [125424236](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125424236) | PP.TAKEHIRO_KAWADA | Steven's Metagross ex | loss | 1-2 | 468 |
| [125423853](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125423853) | mo | Mega Lucario ex | win | 2-0 | 256 |
| [125423408](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125423408) | Hokuto Tokutake | Dragapult ex | loss | 0-2 | 155 |
| [125423197](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125423197) | Raosaheb | Mega Lucario ex | win | 2-0 | 217 |
| [125423003](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125423003) | Matsui Data | Mega Lucario ex | win | 2-0 | 312 |
| [125421958](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125421958) | tanzaku | Teal Mask Ogerpon ex | loss | 1-2 | 464 |
| [125421873](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125421873) | NK49540 | Mega Lucario ex | loss | 0-2 | 186 |
| [125421870](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125421870) | pika28samson | Alakazam | win | 2-0 | 266 |
| [125400865](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125400865) | mm bbAlez | Mega Abomasnow ex | win | 2-0 | 99 |
| [125419841](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125419841) | yayaswya | Alakazam | win | 2-0 | 147 |
| [125418835](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125418835) | diujin217 | Crustle | win | 2-0 | 164 |
| [125418713](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125418713) | ISAKA Tsuyoshi | Crustle | loss | 0-2 | 252 |
| [125417705](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125417705) | shengjia lei | Dipplin | win | 2-1 | 468 |
| [125416709](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125416709) | Tolga Kiremit | Alakazam | loss | 0-2 | 371 |
| [125415699](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125415699) | Dihpplin It In | Dipplin | win | 2-1 | 492 |
| [125415572](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125415572) | GengarX17 | Dragapult ex | loss | 0-2 | 251 |
| [125414896](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125414896) | nonpapa | Marnie's Grimmsnarl ex | win | 2-0 | 269 |
| [125413918](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125413918) | suk1yak1 | Dragapult ex | win | 2-1 | 431 |
| [125412953](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125412953) | nonpapa | Marnie's Grimmsnarl ex | win | 2-0 | 270 |
| [125412015](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125412015) | Chen Kuan-Chin | Dragapult ex | loss | 0-2 | 319 |
| [125411301](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125411301) | Raymime | Mega Lucario ex | win | 2-0 | 254 |
| [125410823](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125410823) | Mibbles | Alakazam | loss | 0-2 | 291 |
| [125410306](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125410306) | jazivxt | Archaludon ex | win | 2-1 | 317 |
| [125409532](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125409532) | destbreso | Latias ex/Lillie’s Clefairy ex | win | 2-0 | 229 |
| [125409361](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125409361) | diujin217 | Crustle | loss | 1-2 | 406 |
| [125409292](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125409292) | marnie's number 1 fan | Dragapult ex | loss | 1-2 | 477 |
| [125408373](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125408373) | Christian Shin | Dipplin | win | 2-1 | 488 |
| [125407409](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125407409) | Raymime | Alakazam | win | 2-0 | 344 |
| [125406442](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125406442) | boonies | Dragapult ex | loss | 0-2 | 320 |
| [125405471](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125405471) | Tom Curry11 | Crustle | loss | 0-2 | 348 |
| [125404444](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125404444) | yaying1 | Alakazam | loss | 0-2 | 210 |
| [125404154](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125404154) | marnie's number 1 fan | Dragapult ex | loss | 1-2 | 426 |
| [125403168](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125403168) | Wei Hsiang Lin111 | Fezandipiti ex/Latias ex | loss | 1-2 | 372 |
| [125402179](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125402179) | Raosaheb | Mega Lucario ex | loss | 1-2 | 349 |
| [125401479](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125401479) | Juhil Modi-24BCS10310 | Alakazam | win | 2-1 | 323 |
| [125401148](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125401148) | Chen Kuan-Chin | Dragapult ex | win | 2-1 | 360 |
| [125400354](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125400354) | GengarX17 | Dragapult ex | loss | 1-2 | 505 |
| [125399404](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125399404) | Haoyang Wu | Mega Abomasnow ex | win | 2-0 | 164 |
| [125398438](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125398438) | nnnnio_pppira | Alakazam | win | 2-0 | 184 |
| [125397474](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125397474) | Uttam Limbani | Crustle | loss | 0-2 | 268 |
| [125396964](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125396964) | MMN0222 | Crustle | loss | 0-2 | 274 |
| [125396088](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125396088) | Kevin Rio Harristyando | Mega Lucario ex | win | 2-0 | 200 |
| [125395602](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125395602) | pika28samson | Alakazam | loss | 0-2 | 320 |
| [125395281](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125395281) | ZHIRUI ZHAO | Mega Lucario ex | win | 2-0 | 257 |
| [125394339](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125394339) | (ノ◡ <) | Dragapult ex | win | 2-0 | 267 |
| [125393404](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125393404) | ScDomi | Mega Lucario ex | win | 2-1 | 265 |
| [125393332](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125393332) | Tolga Kiremit | Crustle | win | 2-1 | 167 |
| [125392528](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125392528) | Sliver-Ze | Mega Abomasnow ex | win | 2-0 | 158 |
| [125391592](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125391592) | john inan | Mega Abomasnow ex | win | 2-0 | 197 |
| [125391404](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125391404) | Shiv sib | Mega Froslass ex | loss | 1-2 | 343 |
| [125391361](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125391361) | Toxtricity | Mega Absol ex | win | 2-1 | 512 |
| [125391199](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125391199) | Anto Antony Selvaraj | Mega Abomasnow ex | win | 2-0 | 121 |
| [125391030](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125391030) | GengarX17 | Dragapult ex | loss | 0-2 | 368 |
| [125390871](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125390871) | Juhil Modi-24BCS10310 | Dragapult ex | loss | 0-2 | 358 |
| [125390707](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125390707) | jjdddd | Mega Abomasnow ex | win | 2-0 | 170 |
| [125390544](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125390544) | ISAKA Tsuyoshi | Crustle | loss | 0-2 | 262 |
| [125390382](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125390382) | Namir Chaudry | Alakazam | loss | 1-2 | 433 |
| [125390215](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125390215) | hzn | Mega Abomasnow ex | win | 2-0 | 91 |
| [125390051](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125390051) | Shreyashsri_ | Archaludon ex | loss | 0-2 | 261 |
| [125389891](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125389891) | NIP | Mega Abomasnow ex | win | 2-0 | 155 |
| [125389728](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125389728) | Brian Bonti | Mega Lucario ex | loss | 1-2 | 448 |
| [125389566](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125389566) | Ted Mothwake | Mega Froslass ex | win | 2-0 | 166 |
| [125389404](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125389404) | Wei Hsiang Lin111 | Fezandipiti ex/Latias ex | loss | 0-2 | 228 |
| [125389244](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125389244) | tanzaku | Alakazam | win | 2-1 | 461 |
| [125389079](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125389079) | teppei | Mega Kangaskhan ex/Latias ex | loss | 1-2 | 224 |
| [125388916](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125388916) | Dark_trio | Archaludon ex | win | 2-1 | 286 |
| [125388753](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125388753) | awewrasdffetfe | Alakazam | loss | 0-2 | 324 |
| [125388592](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125388592) | Noel Bobby | Teal Mask Ogerpon ex | win | 2-0 | 157 |
| [125388430](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125388430) | tai | Iono’s Bellibolt ex | win | 2-1 | 590 |
| [125388266](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125388266) | Menelik Zafir | Mega Froslass ex | win | 2-0 | 207 |
| [125388103](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125388103) | Attention Is All You Mew | Dragapult ex | loss | 0-2 | 242 |
| [125387942](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125387942) | Tomeiser | Alakazam | loss | 1-2 | 464 |
| [125387776](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125387776) | kloaken | Dipplin | loss | 1-2 | 468 |
| [125387618](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125387618) | HOLY0305 | Crustle | loss | 0-2 | 200 |
| [125387456](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125387456) | Wei Hsiang Lin111 | Bloodmoon Ursaluna ex/Lillie’s Clefairy ex | loss | 0-2 | 313 |
| [125387294](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125387294) | shubham qwqw | Mega Lucario ex | win | 2-0 | 274 |
| [125387130](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125387130) | Aditya ingale | Mega Abomasnow ex | win | 2-0 | 121 |
| [125386969](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386969) | NK49540 | Mega Lucario ex | win | 2-1 | 274 |
| [125386807](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386807) | Phi Long Nguyen | Other | win | 2-1 | 567 |
| [125386645](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386645) | Es Kecap | Marnie's Grimmsnarl ex | loss | 0-2 | 230 |
| [125386527](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386527) | Philipp k-s | Teal Mask Ogerpon ex | loss | 0-2 | 379 |
| [125386483](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386483) | Kydyrbek Kozykorpesh | Dipplin | win | 2-0 | 373 |
| [125386318](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386318) | Pratyush Sahoo | Latias ex/Lillie’s Clefairy ex | win | 2-0 | 184 |
| [125386193](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386193) | Tolga Kiremit | Alakazam | loss | 0-2 | 385 |
| [125386158](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125386158) | sergeicu | Dragapult ex | win | 2-1 | 409 |
| [125385996](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385996) | nguyenbaotri-VIETNAM | Mega Lucario ex | win | 2-0 | 247 |
| [125385829](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385829) | Jeffrey Tucker | Alakazam | win | 2-0 | 378 |
| [125385684](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385684) | wadigongren | Alakazam | loss | 1-2 | 463 |
| [125385668](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385668) | boonies | Dragapult ex | loss | 0-2 | 323 |
| [125385619](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385619) | WolfeyVGC | Dragapult ex | loss | 1-2 | 336 |
| [125385506](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385506) | tanzaku | Teal Mask Ogerpon ex | win | 2-0 | 243 |
| [125385343](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385343) | jdx | Dipplin | win | 2-0 | 339 |
| [125385178](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385178) | Don't foget me | Mega Excadrill ex/Genesect ex | win | 2-0 | 226 |
| [125385018](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125385018) | Menelik Zafir | Mega Froslass ex | loss | 0-2 | 241 |
| [125384881](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125384881) | sue124 | Lillie’s Clefairy ex/Bloodmoon Ursaluna ex | loss | 0-2 | 217 |
| [125384854](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125384854) | jazivxt | Archaludon ex | win | 2-1 | 400 |
| [125384691](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125384691) | Shaun2024 | Crustle | loss | 0-2 | 252 |
| [125384527](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125384527) | Rayan | Mega Froslass ex | win | 2-0 | 200 |
| [125384365](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125384365) | Rajveer Vora | Crustle | win | 2-0 | 241 |
| [125384003](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125384003) | LiYang578 | Mega Abomasnow ex | win | 2-0 | 100 |
| [125384041](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125384041) | Noel Bobby | Teal Mask Ogerpon ex | win | 2-0 | 242 |
| [125383959](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383959) | MMN0222 | Crustle | loss | 1-2 | 345 |
| [125383877](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383877) | Ramanath Rakshit | Lillie’s Clefairy ex | loss | 0-2 | 384 |
| [125383711](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383711) | PeterSharps | Mega Abomasnow ex | win | 2-0 | 151 |
| [125383592](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383592) | MMN0222 | Crustle | loss | 0-2 | 316 |
| [125383552](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383552) | Tom Curry11 | Crustle | loss | 0-2 | 270 |
| [125383482](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383482) | pika28samson | Alakazam | loss | 1-2 | 500 |
| [125383384](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383384) | Trynewthing | Mega Starmie ex | win | 2-0 | 236 |
| [125383226](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383226) | WolfeyVGC | Dragapult ex | loss | 0-2 | 311 |
| [125383062](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125383062) | bai fang | Dipplin | loss | 0-2 | 290 |
| [125382900](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125382900) | sergeicu | Dragapult ex | win | 2-0 | 308 |
| [125382733](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125382733) | teppei | Mega Kangaskhan ex/Latias ex | loss | 0-2 | 123 |
| [125382575](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125382575) | Hi Im Ryo | Teal Mask Ogerpon ex | loss | 0-2 | 333 |
| [125382436](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125382436) | LowTiste | Dragapult ex | win | 2-0 | 252 |
| [125382404](https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground/submissions?submissionId=57640356&episodeId=125382404) | F.A.Nina | Mega Lucario ex | win | 2-0 | 241 |

Self-match 125382210: 482 raw steps; both display names are Natanael Rehuel S. It is archived in `match-data/125382210.json` and excluded from the opponent totals above.
