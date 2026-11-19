"""Eigenschaften der Indizes (Axiome und Invarianzen) an Zufallsinstanzen und der Rang-Satz an allen kleinen Gewichtsspielen."""

import itertools
import math
from fractions import Fraction

import pytest

import mdx_experiments as E
import mdx_game as G
import mdx_scenario as S


def _games(n_values=(3, 5, 7), per=8):
    for gen in S.generator_keys():
        for n in n_values:
            for j in range(per):
                w = list(S.make_weights(gen, n, 21, j))
                for pct in (50, 67, 100):
                    yield w, G.quota_from_percent(sum(w), pct)


def test_efficiency_the_counts_sum_to_what_the_shares_need():
    for w, q in _games():
        swings, pivots = G.pivot_counts_dp(w, q)
        assert sum(swings) > 0 and sum(pivots) == math.factorial(len(w))        # in jeder Reihenfolge schwingt genau ein Mitglied (Quote <= W)
        assert sum(G.banzhaf_shares(swings)) == pytest.approx(1)
        assert sum(G.shapley_shubik_shares(pivots, len(w))) == pytest.approx(1)


def test_symmetry_members_with_equal_weight_have_equal_counts():
    for w, q in _games():
        swings, pivots = G.pivot_counts_dp(w, q)
        for i, j in itertools.combinations(range(len(w)), 2):
            if w[i] == w[j]:
                assert swings[i] == swings[j] and pivots[i] == pivots[j]


def test_monotonicity_a_bigger_weight_never_has_less_power():
    for w, q in _games():
        swings, pivots = G.pivot_counts_dp(w, q)
        for i, j in itertools.permutations(range(len(w)), 2):
            if w[i] >= w[j]:
                assert swings[i] >= swings[j] and pivots[i] >= pivots[j], (w, q)


def test_a_null_player_has_zero_power_in_both_indices_at_once():
    seen_null = 0
    for w, q in _games():
        swings, pivots = G.pivot_counts_dp(w, q)
        assert [s == 0 for s in swings] == [p == 0 for p in pivots], (w, q)
        seen_null += any(s == 0 for s in swings)
    assert seen_null > 20                  # der Zweig kommt vor (Nullspalten-Regel)


def test_renaming_the_members_permutes_the_counts():
    for w, q in _games((6,), 4):
        order = [3, 0, 5, 1, 4, 2]
        swings, pivots = G.pivot_counts_dp(w, q)
        w2 = [w[i] for i in order]
        swings2, pivots2 = G.pivot_counts_dp(w2, q)
        assert swings2 == [swings[i] for i in order] and pivots2 == [pivots[i] for i in order]


def test_scaling_weights_and_quote_with_the_same_factor_changes_nothing():
    for w, q in _games((4, 6), 4):
        for k in (2, 3):
            assert G.pivot_counts_dp([k * x for x in w], k * q) == G.pivot_counts_dp(w, q)


def test_rank_theorem_both_indices_order_all_small_weighted_games_the_same():
    """Satz: in einem Gewichtsspiel ordnen Banzhaf und Shapley-Shubik die Mitglieder gleich (alle Paare, einschließlich der Gleichstände).
    Aufgezählt: alle nichtfallenden Gewichtsvektoren mit n = 3 bis 6 Mitgliedern und Gewichten bis `wmax`, alle Quoten über W/2."""
    result = E.rank_theorem_enumeration()
    assert result["rank_differs"] == 0
    assert result["games"] > 10_000 and result["values_differ"] > 3_000          # die Aufzählung ist groß genug, und die Werte weichen oft ab, die Ordnung nie
    # und die Zählung selbst ist nicht leer: rank_pairs erkennt eine künstlich vertauschte Ordnung
    assert E.rank_pairs([3, 1, 1], [1, 4, 1]) == (1, 2) and E.rank_pairs([3, 1, 1], [3, 1, 1]) == (0, 0) and E.rank_pairs([2, 2, 1], [3, 2, 1]) == (0, 1)


def test_rank_theorem_also_holds_for_random_larger_games():
    for w, q in _games((9, 12), 3):
        swings, pivots = G.pivot_counts_dp(w, q)
        for i, j in itertools.combinations(range(len(w)), 2):
            assert (swings[i] > swings[j]) - (swings[i] < swings[j]) == (pivots[i] > pivots[j]) - (pivots[i] < pivots[j])


def test_the_scaled_quota_in_the_unit_of_fractions_is_exact():
    """Banzhaf-Anteile als Brüche sind unabhängig von der Skala: [2,1,1] mit Quote 3 und [4,2,2] mit Quote 6 geben dieselben Anteile."""
    a = G.pivot_counts_dp([2, 1, 1], 3)[0]
    b = G.pivot_counts_dp([4, 2, 2], 6)[0]
    assert [Fraction(x, sum(a)) for x in a] == [Fraction(x, sum(b)) for x in b]
