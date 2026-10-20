"""Alakazam-specific strategy, deployment and native legality regressions."""
from collections import Counter
import copy
import unittest

from pokemon_agent.agents import create_agent, default_deck
from pokemon_agent.alakazam import AlakazamAgent
from pokemon_agent.runner import play_game
from test_agent import card, pokemon, observation, config


def position(options, hand_size=18):
    obs = observation(options)
    me, opponent = obs["current"]["players"]
    me["active"] = [pokemon(743, 10, 140, 1)]
    me["active"][0]["energies"] = [5]
    me["hand"] = [card(1231, 50)] + [card(5, 100+i) for i in range(hand_size-1)]
    me["handCount"] = hand_size
    opponent["active"][0]["hp"] = 350
    opponent["bench"] = [pokemon(723, 30, 350, owner=1)]
    return obs


class AlakazamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AlakazamAgent()

    def test_dedicated_entry_returns_exact_sixty_card_non_ex_deck(self):
        from main_alakazam import agent
        deck = agent({"select": None})
        self.assertEqual(deck, default_deck("alakazam"))
        self.assertEqual(len(deck), 60)
        pokemon_cards = [self.agent.cards[cid] for cid in deck if self.agent.cards[cid].cardType == 0]
        self.assertEqual(sum(c.basic for c in pokemon_cards), 8)
        self.assertTrue(all(not c.ex and not c.megaEx for c in pokemon_cards))
        self.assertTrue(all(count <= 4 for cid, count in Counter(deck).items() if self.agent.cards[cid].cardType != 5))

    def test_counter_knockout_precedes_supporter_that_spends_hand(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 7, "index": 0}, {"type": 14}])
        self.assertEqual(self.agent(obs), [0])  # 18 cards -> 360 counters on a 350-HP Mega.
        obs["current"]["players"][0]["hand"].pop()
        self.assertEqual(self.agent(obs), [1])  # Need more cards before attacking.

    def test_hand_refresh_is_not_used_to_shrink_a_large_hand(self):
        obs = position([{"type": 7, "index": 0}, {"type": 14}], hand_size=10)
        obs["current"]["players"][0]["hand"][0]["id"] = 1227
        self.assertEqual(self.agent(obs), [1])

    def test_psychic_cost_is_not_paid_by_colorless_energy(self):
        p = pokemon(743, 10, 140, 1)
        p["energies"] = [0]
        self.assertFalse(self.agent.can_pay(p, 1072))
        p["energies"] = [5]
        self.assertTrue(self.agent.can_pay(p, 1072))

    def test_free_retreat_pivot_does_not_take_the_attackers_energy(self):
        obs = position([{"type": 14}])
        me = obs["current"]["players"][0]
        me["active"] = [pokemon(65, 10, 60)]
        me["bench"] = [pokemon(741, 20, 50)]
        self.assertLess(self.agent.energy_priority(obs, me["active"][0]), 0)
        self.assertGreater(self.agent.energy_priority(obs, me["bench"][0]), 0)

    def test_boss_accounts_for_the_card_spent_before_counter_attack(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 7, "index": 0}, {"type": 14}])
        me, opponent = obs["current"]["players"]
        me["hand"][0]["id"] = 1182
        self.assertEqual(self.agent(obs), [0])  # Boss would reduce 360 to 340.
        me["hand"] = me["hand"][:16]
        opponent["bench"][0] = pokemon(722, 30, 90, owner=1)
        self.assertEqual(self.agent(obs), [1])  # Reach a one-Prize KO when the Active survives.

    def test_draw_ability_preserves_a_card_for_the_next_turn(self):
        obs = position([{"type": 1}, {"type": 2}])
        obs["select"].update(context=43, contextCard=card(743, 10))
        obs["current"]["players"][0]["deckCount"] = 3
        self.assertEqual(self.agent(obs), [1])
        obs["current"]["players"][0]["deckCount"] = 4
        self.assertEqual(self.agent(obs), [0])

    def test_dudunsparce_does_not_shuffle_away_the_only_pokemon(self):
        obs = position([{"type": 10, "area": 4, "index": 0}, {"type": 14}])
        me = obs["current"]["players"][0]
        me["active"] = [pokemon(66, 10, 140)]
        self.assertEqual(self.agent(obs), [1])
        me["bench"] = [pokemon(741, 20, 50)]
        self.assertEqual(self.agent(obs), [0])

    def test_search_payload_does_not_change_new_policy(self):
        obs = position([{"type": 13, "attackId": 1072}, {"type": 7, "index": 0}, {"type": 14}])
        other = copy.deepcopy(obs)
        other["search_begin_input"] = None
        self.assertEqual(self.agent(obs), self.agent(other))

    def test_factory_preserves_both_distinct_decks(self):
        self.assertNotEqual(default_deck("alakazam"), default_deck("abomasnow"))
        self.assertEqual(create_agent("alakazam").deck, default_deck("alakazam"))
        with self.assertRaises(ValueError):
            create_agent("unknown")

    def test_native_battle_accepts_candidate_and_completes(self):
        settings = dict(config(), agent="alakazam", agent_deck=default_deck("alakazam"))
        result = play_game(settings)
        self.assertEqual(result["status"], "completed", result.get("error"))
        self.assertNotIn("error", result)


if __name__ == "__main__":
    unittest.main()
