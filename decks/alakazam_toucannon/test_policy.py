"""Tactical, hidden-information and native regressions for the separate pilot."""
from collections import Counter
import copy
import json
from pathlib import Path
import unittest

from pokemon_agent.agents import create_agent, default_deck
from pokemon_agent.runner import play_game
from pokemon_agent.sdk import validate_selection
from tests.helpers import card, pokemon, observation, config
from .policy import AlakazamToucannonAgent


def position(options, hand_size=16):
    obs = observation(options)
    me, other = obs["current"]["players"]
    me["active"] = [pokemon(743, 10, 140)]
    me["active"][0]["energies"] = [5]
    me["hand"] = [card(5, 100+i) for i in range(hand_size)]
    me["handCount"] = hand_size
    other["active"] = [pokemon(121, 30, 320, owner=1)]
    other["bench"] = [pokemon(119, 31, 70, owner=1)]
    return obs


class ExperimentalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AlakazamToucannonAgent()

    def test_separate_entry_has_legal_sixty_card_hybrid_and_keeps_yume_reference(self):
        from .main import agent
        deck = agent({"select": None})
        self.assertEqual(deck, default_deck("alakazam_toucannon"))
        self.assertEqual(len(deck), 60)
        counts = Counter(deck)
        self.assertEqual((counts[305], counts[65], counts[1407], counts[1409], counts[13]), (3, 1, 1, 1, 1))
        self.assertEqual((counts[743], counts[66], counts[140]), (4, 4, 0))
        from pokemon_agent.sdk import read_deck
        reference = Counter(read_deck(Path(__file__).with_name("yume_reference.csv")))
        self.assertEqual((reference[1407], reference[1409], reference[140]), (2, 2, 1))
        self.assertEqual(sum(self.agent.cards[i].aceSpec for i in deck), 1)
        self.assertTrue(all(n <= 4 for i, n in counts.items() if self.agent.cards[i].cardType != 5))

    def test_seventy_hp_dunsparce_is_a_draw_line(self):
        obs = position([{"type": 14}])
        obs["current"]["players"][0]["bench"] = [pokemon(305, 20, 70)]
        self.assertEqual(self.agent.lines(obs["current"]["players"][0]), (1, 1))

    def test_enriching_does_not_satisfy_psychic_or_prevent_next_attachment(self):
        obs = position([{"type": 14}])
        p = obs["current"]["players"][0]["active"][0]
        p["energies"] = [0]
        self.assertFalse(self.agent.can_pay(p, 1072))
        self.assertGreater(self.agent.energy_priority(obs, p), 0)

    def test_charge_the_active_seventy_hp_pivot_before_another_bench_attacker(self):
        obs = position([{"type": 14}])
        me = obs["current"]["players"][0]
        me["active"] = [pokemon(305, 10, 70)]
        me["bench"] = [pokemon(743, 20, 140), pokemon(743, 21, 140)]
        me["bench"][0]["energies"] = [5]
        self.assertGreater(self.agent.energy_priority(obs, me["active"][0]),
                           self.agent.energy_priority(obs, me["bench"][1]))

    def test_draw_budget_keeps_turns_to_finish_the_prize_race(self):
        obs = position([{"type": 10, "area": 5, "index": 0}, {"type": 14}])
        me = obs["current"]["players"][0]
        me["deckCount"] = 6
        me["bench"] = [pokemon(1409, 20, 150)]
        self.assertEqual(self.agent(obs), [1])
        me["prize"] = [None, None]
        self.assertEqual(self.agent(obs), [0])  # Fewer Prizes left permits a smaller natural-draw reserve.

    def test_backup_damage_uses_both_benches_and_ignores_mist_counter_protection(self):
        obs = position([{"type": 14}])
        me, other = obs["current"]["players"]
        me["active"] = [pokemon(1409, 10, 150)]
        me["bench"] = [pokemon(305, 20+i, 70) for i in range(4)]
        other["bench"] = [pokemon(119, 40+i, 70, owner=1) for i in range(4)]
        other["active"] = [pokemon(140, 30, 210, owner=1)]
        other["active"][0]["energyCards"] = [card(11, 301, 1)]
        self.assertLess(self.agent.attack_score(obs, 1072), 0)
        self.assertEqual(self.agent.attack_score(obs, 1751), 3600)
        other["active"][0]["hp"] = 230
        self.assertLess(self.agent.attack_score(obs, 1751), 1800)

    def test_hilda_search_keeps_guaranteed_psychic_ahead_of_colorless_draw(self):
        obs = position([{"type": 3, "area": 1, "index": 0}, {"type": 3, "area": 1, "index": 1}])
        me = obs["current"]["players"][0]
        me["active"][0]["energies"] = []
        me["hand"] = [card(743, 100)]
        obs["select"].update(context=7, deck=[card(13, 200), card(19, 201)])
        self.assertEqual(self.agent(obs), [1])

    def test_ready_toucannon_can_gust_an_ex_knockout(self):
        obs = position([{"type": 13, "attackId": 1751}, {"type": 7, "index": 0}, {"type": 14}])
        me, other = obs["current"]["players"]
        me["active"] = [pokemon(1409, 10, 150)]
        me["active"][0]["energies"] = [0]
        me["hand"][0]["id"] = 1182
        me["bench"] = [pokemon(305, 20+i, 70) for i in range(4)]
        other["bench"] = [pokemon(140, 40, 210, owner=1)] + [pokemon(119, 41+i, 70, owner=1) for i in range(3)]
        self.assertEqual(self.agent(obs), [1])

    def test_retreat_then_gust_keeps_supporter_for_a_two_prize_knockout(self):
        obs = position([{"type": 13, "attackId": 1071}, {"type": 12}, {"type": 7, "index": 0}, {"type": 14}])
        me, other = obs["current"]["players"]
        me["active"] = [pokemon(742, 10, 80)]
        me["active"][0]["energies"] = [5]
        me["hand"][0]["id"], me["hand"][1]["id"] = 1231, 1182
        me["bench"] = [pokemon(743, 20, 140)]
        me["bench"][0]["energies"] = [5]
        other["active"] = [pokemon(235, 30, 30, owner=1)]
        other["bench"] = [pokemon(140, 31, 210, owner=1)]
        self.assertEqual(self.agent(obs), [1])
        obs["current"]["supporterPlayed"] = True
        self.assertLess(self.agent.development_score(obs, obs["select"]["option"][1]), 0)

    def test_normal_powered_evolution_precedes_candy_on_an_unpowered_basic(self):
        opts = [{"type": 7, "index": 0},
                {"type": 9, "area": 2, "index": 1, "inPlayArea": 5, "inPlayIndex": 0}, {"type": 14}]
        obs = position(opts, hand_size=10)
        me = obs["current"]["players"][0]
        me["active"] = [pokemon(305, 10, 70)]
        me["hand"][0]["id"], me["hand"][1]["id"] = 1079, 743
        me["bench"] = [pokemon(742, 20, 80), pokemon(741, 21, 50)]
        me["bench"][0]["energies"] = [5]
        self.assertEqual(self.agent(obs), [1])

    def test_winning_attack_precedes_optional_draw(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 10, "area": 5, "index": 0}])
        me, _ = obs["current"]["players"]
        me["prize"] = [None, None]
        me["bench"] = [pokemon(1409, 20, 150)]
        self.assertEqual(self.agent(obs), [0])

    def test_evolution_draw_is_counted_before_spending_a_knockout(self):
        opts = [{"type": 13, "attackId": 1072},
                {"type": 9, "area": 2, "index": 0, "inPlayArea": 5, "inPlayIndex": 0}]
        obs = position(opts)
        me, _ = obs["current"]["players"]
        me["hand"][0]["id"] = 743
        me["bench"] = [pokemon(742, 20, 80)]
        self.assertEqual(self.agent(obs), [1])  # -1 evolution card +3 draw preserves 320.

    def test_cage_does_not_spend_the_exact_current_knockout(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 7, "index": 0}])
        obs["current"]["players"][0]["hand"][0]["id"] = 1264
        self.assertEqual(self.agent(obs), [0])

    def test_candy_can_build_backup_once_alakazam_is_present(self):
        opts = [{"type": 9, "area": 2, "index": 0, "inPlayArea": 5, "inPlayIndex": 0},
                {"type": 9, "area": 2, "index": 1, "inPlayArea": 5, "inPlayIndex": 1}]
        obs = position(opts)
        obs["select"]["context"] = 37
        me = obs["current"]["players"][0]
        me["hand"][0]["id"], me["hand"][1]["id"] = 743, 1409
        me["bench"] = [pokemon(741, 20, 50), pokemon(1407, 21, 70)]
        me["bench"][1]["energies"] = [0]
        self.assertEqual(self.agent(obs), [1])

    def test_low_deck_draw_is_declined_and_enriching_is_not_attached(self):
        obs = position([{"type": 10, "area": 5, "index": 0}, {"type": 14}])
        me = obs["current"]["players"][0]
        me["bench"] = [pokemon(1409, 20, 150)]
        me["deckCount"] = 1
        self.assertEqual(self.agent(obs), [1])
        obs["select"]["option"][0] = {"type": 8, "area": 2, "index": 0, "inPlayArea": 4, "inPlayIndex": 0}
        me["hand"][0]["id"] = 13
        me["deckCount"] = 4
        self.assertEqual(self.agent(obs), [1])

    def test_enriching_lethal_draw_accounts_for_the_card_spent(self):
        obs = position([{"type": 8, "area": 2, "index": 0, "inPlayArea": 4, "inPlayIndex": 0}, {"type": 14}], hand_size=12)
        me = obs["current"]["players"][0]
        me["hand"][0]["id"] = 13
        me["deckCount"], me["prize"] = 4, [None, None]
        self.assertEqual(self.agent(obs), [1])  # 12 - 1 + 4 =15 cards, still short of 320.
        me["hand"].append(card(5, 999))
        self.assertEqual(self.agent(obs), [0])  # 13 - 1 + 4 =16; the winning draw is safe.

    def test_fan_does_not_complete_enemy_blaziken_attack(self):
        opts = [{"type": 3, "area": 5, "index": 0, "playerIndex": 1},
                {"type": 3, "area": 5, "index": 1, "playerIndex": 1}]
        obs = position(opts)
        obs["select"].update(context=21, effect=card(1161, 200), contextCard=card(5, 201, 1))
        other = obs["current"]["players"][1]
        other["bench"] = [pokemon(326, 40, 320, owner=1), pokemon(343, 41, 80, owner=1)]
        other["bench"][0]["energies"] = [2]
        self.assertEqual(self.agent(obs), [1])

    def test_native_game_against_proxy_completes(self):
        settings = dict(config(), agent="alakazam_toucannon", opponent="dragapult_proxy",
                        agent_deck=default_deck("alakazam_toucannon"), opponent_deck=default_deck("dragapult_proxy"))
        result = play_game(settings)
        self.assertEqual(result["status"], "completed", result.get("error"))


class ReplayTests(unittest.TestCase):
    def test_saved_decisions_are_legal_without_the_hidden_search_payload(self):
        rows = json.loads(Path(__file__).with_name("replay_positions.json").read_text(encoding="utf-8"))
        pilot = AlakazamToucannonAgent()
        for name, row in rows.items():
            with self.subTest(position=name):
                obs = copy.deepcopy(row["observation"])
                action = pilot(obs)
                validate_selection(obs, action)
                obs["search_begin_input"] = "unavailable private native state"
                self.assertEqual(pilot(obs), action)
