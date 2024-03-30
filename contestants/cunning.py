import random
from game import base_agent
from game import helpers
from game.card import Card


def one_set(plus_starts: bool, plus, rest):
    from itertools import permutations, product
    if plus_starts:
        # We require that the first entry is a plus, otherwise there's nothing to do
        if len(plus) == 0:
            return []
        if len(rest) == 0:
            # don't return [+, +, ...]
            return [[p] for p in plus]
        return [[p[0], *r, *(p[1:])] for p, r in product(permutations(plus), permutations(rest))]
    else:
        # plus should only be 0 or 1 element
        if len(plus) == 0:
            return [list(r) for r in permutations(rest)]
        return [[*r, plus[0]] for r in permutations(rest)]


def possible(checker, operator: str, budget: int, cards: list[Card]) -> list[list[Card]]:
    from itertools import combinations, product
    plus = [c for c in cards if c.operator == '+']
    rest = [c for c in cards if c.operator == ('*' if operator == '+' else operator)]

    plus_count = 2 if operator == '+' else 1

    plus_options = set(p for i in range(plus_count) for p in combinations(plus, i+1))
    rest_options = set(r for i in range(len(rest)) for r in combinations(rest, i+1))
    options = []
    if len(plus_options) and len(rest_options):
        options.extend([(p, r) for p, r in product(plus_options, rest_options) if sum(c.cost for c in p+r) <= budget])
    if len(plus_options):
        options.extend([(p, []) for p in plus_options if sum(c.cost for c in p) <= budget])
    if len(rest_options):
        options.extend([([], r) for r in rest_options if sum(c.cost for c in r) <= budget])

    opts = [one for p, r in options for one in one_set(operator == '+', p, r)]
    return sorted(opts, key=checker, reverse=True)  # highest total value first


class Agent(base_agent.BaseAgent):
    def __init__(self, *args, deck=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Greg"
        self._user_deck = deck

        # Can add variables here, will be stored between games in a single match

    def select_cards(self):
        if self._user_deck is not None:
            self.deck = dict(self._user_deck)
        else:
            options = [
                #  {'plus5': 3, 'plus10': 3, 'div10': 3, 'plus1': 7, 'div5': 2, 'mult10': 3, 'mult3': 5},
                {'plus5': 5, 'plus10': 4, 'div10': 0, 'plus1': 2, 'div5': 0, 'mult10': 4, 'mult3': 0},
                {'plus5': 5, 'plus10': 1, 'div10': 1, 'plus1': 2, 'div5': 1, 'mult10': 4, 'mult3': 1}
            ]
            self.deck = options[random.randint(0, len(options) - 1)]

    def play_turn(self, hand, energy, game_info, locked_term, current_term):
        from math import log, ceil, floor

        def checker(cards):
            l, c = locked_term, current_term
            for this_card in cards:
                l, c = helpers.apply_card(this_card, l, c)
            return l + c

        # Figure out which cards could be played now (sufficient energy)
        can_play = helpers.can_be_played(hand, energy)

        hands = possible(checker, '*' if current_term > 0 else '+', energy, can_play)
        if current_term < -15:
            hands.extend(possible(checker, '/', energy, can_play))
            hands = sorted(hands, key=checker, reverse=True)  # re-sort

        # don't worry too much about smaller negative totals
        if (locked_term + current_term) < 0:
            n = log(1-(locked_term + current_term), 10) + 1
            hands = [h for h in hands if len(h) <= n]

        for hand in hands:
            if helpers.can_be_played(hand, energy):
                return hand
        return []


def fake_checker(fixed, current):
    from game.helpers import apply_card

    def checker(cards):
        l, c = fixed, current
        for card in cards:
            l, c = apply_card(card, l, c)
        return l+c

    return checker

def test_possible():
    c1 = Card('+', 1, 1)
    c3 = Card('*', 3, 2)
    c5 = Card('+', 5, 3)
    c10 = Card('*', 10, 3)

    # starting from (0, 0)
    o001 = possible(fake_checker(0, 0), '+', 1, [c1, c3, c5, c10])
    assert o001 == [[c1]]

    o003 = possible(fake_checker(0, 0), '+', 3, [c1, c3, c5, c10])
    assert o003 == [[c5], [c1, c3], [c1]]

    o005 = possible(fake_checker(0, 0), '+', 5, [c1, c3, c5, c10])
    assert o005 == [[c5, c3], [c1, c10], [c5], [c5], [c1, c3], [c1], [c1]]


def test_one_set():
    c1 = Card('+', 1, 1)
    c3 = Card('*', 3, 2)
    c5 = Card('+', 5, 3)
    c10 = Card('*', 10, 3)

    p1 = [c1]
    s = one_set(False, p1, [])
    assert s == [p1]

    r1 = [Card('*', 3, 2)]
    assert one_set(False, p1, r1) == [[r1[0], p1[0]]]
    assert one_set(True, p1, r1) == [[p1[0], r1[0]]]

    r2 = [c3, c3]
    assert one_set(False, p1, r2) == [r2 + p1, r2 + p1]
    assert one_set(True, p1, r2) == [p1 + r2, p1 + r2]

    assert one_set(False, [], r2) == [r2, r2]
    assert one_set(True, [], r2) == []

    r3 = [c3, c10]
    assert one_set(False, p1, r3) == [[c3, c10, c1], [c10, c3, c1]]
    assert one_set(True, p1, r3) == [[c1, c3, c10], [c1, c10, c3]]

    p2 = [c1, c5]
    assert one_set(False, p2, r3) == one_set(False, p1, r3)
    assert one_set(True, p2, r3) == [[c1, c3, c10, c5], [c1, c10, c3, c5], [c5, c3, c10, c1], [c5, c10, c3, c1]]


if __name__ == '__main__':
    test_one_set()
    test_possible()
