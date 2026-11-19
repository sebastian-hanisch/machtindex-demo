"""Randfälle (DEMO-PLAYBOOK §12): n = 1, n = 2, Gleichstände, Quote an beiden Rändern, Gewicht 0, ein Mitglied mit allen Stimmen, Grenzen inklusive, Eingaben der App."""

from fractions import Fraction
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import mdx_constants as C
import mdx_evaluation as ev
import mdx_experiments as E
import mdx_game as G
import mdx_paradoxes as P
import mdx_seats as ST

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_exactly_two_members():
    """n = 2, Gewichte [3, 2], Quote 3: nur das Mitglied mit 3 entscheidet (Diktator); bei Quote 4 haben beide Veto und gleich viel Macht."""
    assert G.pivot_counts_dp([3, 2], 3) == ([2, 0], [2, 0]) == G.pivot_counts_subsets([3, 2], 3) == (G.swing_counts_enum([3, 2], 3), G.pivot_counts_perm([3, 2], 3))
    assert G.pivot_counts_dp([3, 2], 4) == ([1, 1], [1, 1])


def test_single_member_decides_everything():
    """n = 1: die Quote ist erreichbar nur mit dem Mitglied, es ist Diktator (eine Schwingzahl, eine Reihenfolge)."""
    for q in (1, 5):
        assert G.pivot_counts_dp([5], q) == ([1], [1]) == G.pivot_counts_subsets([5], q)
    assert G.dictator([1]) == 0 and G.veto_players([5], 5) == [0]


def test_quote_at_both_edges():
    """Quote 1 (jede nichtleere Koalition gewinnt) und Quote W (nur die ganze Koalition): im zweiten Fall haben alle ein Veto und gleich viel Macht."""
    w = [4, 3, 2, 1]
    sw1, pv1 = G.pivot_counts_dp(w, 1)
    assert sum(pv1) == 24 and pv1 == [6, 6, 6, 6]                  # das erste Mitglied jeder Reihenfolge entscheidet
    sw_w, pv_w = G.pivot_counts_dp(w, sum(w))
    assert sw_w == [1, 1, 1, 1] and pv_w == [6, 6, 6, 6] and G.veto_players(w, sum(w)) == [0, 1, 2, 3]


def test_quote_above_the_total_gives_no_power_and_zero_shares():
    sw, pv = G.pivot_counts_dp([2, 1], 4)
    assert sw == [0, 0] and pv == [0, 0] and G.banzhaf_shares(sw) == [0.0, 0.0] and G.dictator(sw) is None


def test_zero_weight_member_is_a_null_player():
    sw, pv = G.pivot_counts_dp([3, 0, 2], 3)
    assert sw[1] == 0 and pv[1] == 0 and sw == G.swing_counts_enum([3, 0, 2], 3)
    assert G.banzhaf_shares(sw) == [1.0, 0.0, 0.0] and G.banzhaf_shares(G.pivot_counts_dp([3, 2], 3)[0]) == [1.0, 0.0]     # das Gewicht-0-Mitglied ändert die Anteile nicht


def test_all_weights_equal_gives_equal_power_and_ties_are_resolved_by_equality():
    sw, pv = G.pivot_counts_dp([2] * 6, 7)
    assert len(set(sw)) == 1 and len(set(pv)) == 1 and E.rank_pairs(sw, pv) == (0, 0)


def test_one_member_with_all_the_votes():
    sw, pv = G.pivot_counts_dp([1000, 1, 1], 1002)
    assert G.dictator(sw) is None and sw == [1, 1, 1]            # Quote 1002 = W: alle haben ein Veto, nur die ganze Koalition gewinnt
    sw2, _ = G.pivot_counts_dp([1000, 1, 1], 501)
    assert G.dictator(sw2) == 0


def test_boundaries_are_inclusive_in_the_win_condition():
    """Die Gewichtssumme gleich der Quote gewinnt (>=): [2, 1], Quote 2: {2} gewinnt."""
    assert list(G.win_vector([2, 1], 2)) == [False, True, False, True]
    with pytest.raises(ValueError):
        G.pivot_counts_perm([1] * 9, 5)
    with pytest.raises(ValueError):
        G.win_vector([1] * 21, 5)
    with pytest.raises(ValueError):
        G.subset_count_table([1] * 63)


def test_dp_multi_matches_single_and_handles_quotas_outside_the_range():
    w = [3, 3, 1, 4]
    multi = G.pivot_counts_dp_multi(w, [1, 6, 11, 12])
    for q in (1, 6, 11):
        assert multi[q] == G.pivot_counts_dp(w, q)
    assert multi[12] == ([0] * 4, [0] * 4)
    with pytest.raises(ValueError):
        G.pivot_counts_dp_multi([1] * 21, [5])


def test_paradox_operations_on_the_smallest_cases():
    assert P.merge([1, 1], 0, 1) == [2] and P.split([2], 0) == [1, 1]
    b, s = P.powers([2], 2)
    assert b == [Fraction(1)] and s == [Fraction(1)]
    with pytest.raises(ValueError):
        P.merge([1, 2], 1, 1)


def test_experiment_functions_on_the_smallest_sizes():
    row = E.cell_stats("uniform", 2, 500, seeds=(1,), per_seed=3)
    assert row["count"] == 3 and 0 <= row["dB"] <= 1
    assert E.quote_curve("equal", 2, (50, 100), seeds=(1,), per_seed=2)[1]["dB"] >= 0
    assert E.two_system_series("uniform", 2, 500, seeds=(1,), per_seed=3)["instances"] <= 3
    assert E.best_quote_of([1]) == {"quote": 1, "total": 1, "distance": 0.0, "distance_majority": 0.0, "majority": 1}
    assert E.best_quote_of([1] * 21) is None and E.best_quote_of([5000] * 3) is None


def test_seat_rules_at_the_edges():
    assert ST.hamilton([1, 1], 1) == [1, 0]                        # Gleichstand: der kleinere Index zuerst
    assert ST.divisor_method([5, 5], 3, "Jefferson") == [2, 1] and ST.hamilton([7], 5) == [5]
    with pytest.raises(ValueError):
        ST.divisor_method([1, 2], 3, "gibt-es-nicht")
    assert ST.staircase([5, 3, 2], 0, 10, 1, 3)[0][0] == 1


def test_permille_and_quota_at_the_slider_edges():
    assert ev.permille_of(50.0) == 500 and ev.permille_of(100.0) == 1000 and ev.permille_of(73.7) == 737
    assert G.quota_from_share(1, Fraction(1, 2)) == 1 and G.quota_from_share(2, Fraction(1, 1)) == 2


APP_INPUTS = [
    ("weights_text", "1, 1"), ("weights_text", "1, 1, 1"), ("weights_text", "5, 1, 1, 1"), ("weights_text", ", ".join(["1"] * 60)), ("weights_text", ", ".join(["1666"] * 59 + ["1706"])),
    ("weights_text", "3, 3, 3, 1"), ("weights_text", "2, 2"), ("weights_text", "x"), ("weights_text", ""), ("weights_text", "99999, 1"), ("weights_text", "100000, 1"),
]


@pytest.mark.parametrize("key,value", APP_INPUTS)
def test_app_with_extreme_weight_inputs_never_raises(key, value):
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    at.sidebar.text_input(key=key).set_value(value).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("percent", [C.P_MIN, C.P_MAX])
@pytest.mark.parametrize("weights", ["1, 1", "5, 1, 1, 1", ", ".join(["1666"] * 59 + ["1706"])])
def test_app_with_the_quote_at_both_edges(percent, weights):
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    at.sidebar.text_input(key="weights_text").set_value(weights)
    at.sidebar.slider(key="p_slider").set_value(percent).run()
    assert not at.exception, [str(e) for e in at.exception]
