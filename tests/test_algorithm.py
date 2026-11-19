"""Kern gegen Handrechnung, je Einheit (DEMO-PLAYBOOK §1b): Quote, vier Rechenwege, Anteile, Vetospieler, Schnitt zweier Systeme, Übertragung, Harsanyi, Sitze.

Die Handwerte stehen in `conftest.py` mit ihrer Rechnung; unabhängige Gegenproben im Großen stehen in `test_oracle_machtindex.py`."""

from fractions import Fraction

import pytest

from conftest import HAND

import mdx_game as G
import mdx_harsanyi as H
import mdx_paradoxes as P
import mdx_seats as ST


def test_quota_from_share_is_more_than_p_of_the_total():
    assert G.quota_from_percent(93, 50) == 47          # mehr als 46,5
    assert G.quota_from_percent(93, 67) == 63          # mehr als 62,31
    assert G.quota_from_share(93, Fraction(2, 3)) == 63    # mehr als 62 (exakt 2/3)
    assert G.quota_from_percent(8, 50) == 5            # genau die Hälfte reicht nicht: mehr als 4
    assert G.quota_from_percent(7, 60) == 5            # mehr als 4,2
    assert G.quota_from_percent(10, 100) == 10         # Einstimmigkeit
    assert G.quota_from_share(345, Fraction(737, 1000)) == 255      # EU-Rat Nizza: mehr als 254,265


def test_quota_is_always_reachable_and_a_strict_majority():
    for total in range(1, 60):
        for pct in range(50, 101):
            q = G.quota_from_percent(total, pct)
            assert 1 <= q <= total
            if pct < 100:
                assert q * 100 > pct * total      # strikt mehr als der Anteil p
            else:
                assert q == total


def test_quota_rejects_p_outside_the_range():
    for bad in (Fraction(0), Fraction(-1, 2), Fraction(3, 2)):
        with pytest.raises(ValueError):
            G.quota_from_share(10, bad)


@pytest.mark.parametrize("key", [k for k in HAND if HAND[k][1] is not None])
def test_all_four_ways_give_the_hand_calculation(hand, key):
    w, q = key
    swings, pivots = hand[key]
    assert G.swing_counts_enum(w, q) == swings
    assert G.pivot_counts_perm(w, q) == pivots
    assert G.pivot_counts_subsets(w, q) == (swings, pivots)
    assert G.pivot_counts_dp(list(w), q) == (swings, pivots)
    assert G.pivot_counts_dp_multi(list(w), [q])[q] == (swings, pivots)


def test_hand_calculation_of_the_largest_member_in_the_fleet_example():
    """Fuhrpark [40, 25, 10, 8, 5, 3, 2], Quote 47: das Mitglied mit 40 ist in 2^6 = 64 Teilmengen der übrigen Schwingspieler, außer wenn die übrigen allein
    gewinnen (Summe der übrigen 53 >= 47: Teilmengen mit Summe >= 47) oder mit ihm nicht gewinnen (Summe < 7). Von Hand: 64 - 5 - 5 = 54 für das Mitglied mit 40."""
    swings, _ = G.pivot_counts_dp([40, 25, 10, 8, 5, 3, 2], 47)
    assert swings == [54, 10, 10, 10, 6, 2, 2]


def test_shares_are_fractions_of_the_totals():
    assert G.banzhaf_shares([3, 1, 1]) == pytest.approx([0.6, 0.2, 0.2])
    assert G.shapley_shubik_shares([4, 1, 1], 3) == pytest.approx([4 / 6, 1 / 6, 1 / 6])
    assert G.banzhaf_shares([0, 0]) == [0.0, 0.0]
    assert G.weight_shares([2, 1, 1]) == pytest.approx([0.5, 0.25, 0.25])


def test_ties_between_members_of_equal_weight_get_equal_power():
    swings, pivots = G.pivot_counts_dp([2, 2, 2, 5], 7)
    assert swings[0] == swings[1] == swings[2] and pivots[0] == pivots[1] == pivots[2]


def test_veto_null_and_dictator_on_the_hand_examples():
    assert G.veto_players([3, 3, 3, 1], 10) == [0, 1, 2, 3]      # Einstimmigkeit: jedes Mitglied hat ein Veto
    assert G.veto_players([3, 3, 1], 5) == [0, 1]
    assert G.veto_players([2, 1, 1], 3) == [0]
    assert G.veto_players([1, 1, 1], 2) == []
    assert G.null_players([2, 2, 0]) == [2]
    assert G.dictator([8, 0, 0, 0]) == 0 and G.dictator([2, 2, 0]) is None and G.dictator([0, 0]) is None


def test_intersection_of_two_systems_needs_both_quotas():
    """Zwei Mitglieder, System A [1, 1] Quote 1 (jeder gewinnt), System B [1, 0] ... ersetzt durch [2, 1] Quote 2: nur Koalitionen mit Mitglied 0 gewinnen beide."""
    win = G.intersection_game([[1, 1], [2, 1]], [1, 2])
    assert list(win) == [False, True, False, True]            # Masken 0 (leer), 1 (nur M1), 2 (nur M2), 3 (beide)
    assert G.pivot_counts_from_win(win, 2) == ([2, 0], [2, 0])      # M1 ist Diktator


def test_transfer_merge_split_and_add_member_on_the_hand_example():
    assert P.transfer([1, 1, 1, 2, 4], 4, 3) == [1, 1, 1, 3, 3]
    assert P.merge([5, 3, 2, 1], 1, 2) == [5, 1, 5]
    assert P.split([5, 3, 2, 1], 0) == [3, 2, 1, 3, 2]
    assert P.add_member([5, 3], 2) == [5, 3, 2]
    with pytest.raises(ValueError):
        P.transfer([1, 1], 0, 1, amount=2)    # mehr Stimmen abgeben, als man hat
    with pytest.raises(ValueError):
        P.split([1, 3], 0)


def test_donor_paradox_by_hand_banzhaf_up_shapley_shubik_down():
    """[1, 1, 1, 2, 4], Quote 7: der Spieler mit 4 gibt eine Stimme an den mit 2 ab ([1, 1, 1, 3, 3]). Schwingzahlen 2/2/2/6/8 (Summe 20) -> 1/1/1/7/7 (Summe 17):
    Banzhaf-Anteil des Gebers 8/20 = 0,400 -> 7/17 = 0,4118. Shapley-Shubik 60/120 = 0,5 -> 54/120 = 0,45."""
    b0, s0 = P.powers([1, 1, 1, 2, 4], 7)
    b1, s1 = P.powers([1, 1, 1, 3, 3], 7)
    assert b0[4] == Fraction(2, 5) and b1[4] == Fraction(7, 17)
    assert s0[4] == Fraction(1, 2) and s1[4] == Fraction(54, 120)
    assert P.donor_outcome([1, 1, 1, 2, 4], 7, 4, 3) == (1, -1)


def test_merge_split_outcome_directions_on_a_small_case():
    """[2, 1, 1], Quote 3: M2 und M3 zusammen (Block 2, Gewichte [2, 2], Quote 3) haben je die halbe Macht = 1/2; vorher zusammen 2/5 (Banzhaf), 1/3 (Shapley-Shubik): mehr."""
    assert P.merge_outcome([2, 1, 1], 3, 1, 2) == (1, 1)
    # Aufspaltung des Mitglieds mit 2 in 1 + 1: Gewichte [1, 1, 1, 1], Quote 3: jedes 1/4; vorher 3/5 (Banzhaf), 4/6 (Shapley-Shubik): weniger
    assert P.split_outcome([2, 1, 1], 3, 0) == (-1, -1)


def test_harsanyi_dividends_of_the_four_member_example():
    """[4, 3, 2, 1], Quote 6: Δ({A,B}) = Δ({A,C}) = Δ({B,C,D}) = 1 und Δ({A,B,C}) = Δ({A,B,C,D}) = -1, alle anderen 0."""
    win = G.win_vector([4, 3, 2, 1], 6)
    d = H.dividends(win, 4)
    items = dict(H.nonzero_dividends(d))
    A, B, C_, D = 1, 2, 4, 8
    assert items == {A | B: 1, A | C_: 1, B | C_ | D: 1, A | B | C_: -1, A | B | C_ | D: -1}
    shapley, banzhaf = H.indices_from_dividends(d, 4)
    assert shapley == [Fraction(10, 24), Fraction(6, 24), Fraction(6, 24), Fraction(2, 24)]
    assert banzhaf == [Fraction(5, 8), Fraction(3, 8), Fraction(3, 8), Fraction(1, 8)]


def test_hamilton_jefferson_webster_on_a_small_case():
    """Mitglieder [900, 600, 300, 100], 7 Sitze: Quoten 3,29 / 2,2 / 1,1 / 0,37; Hamilton gibt 3/2/1/1 (der größte Rest 0,37 an den kleinsten), Jefferson 4/2/1/0."""
    members = [900, 600, 300, 100]
    assert ST.hamilton(members, 7) == [3, 2, 1, 1]
    assert ST.divisor_method(members, 7, "Jefferson") == [4, 2, 1, 0]
    assert sum(ST.divisor_method(members, 7, "Webster")) == 7


def test_seat_power_of_a_zero_seat_member_is_zero():
    b, s, q = ST.seat_power([3, 2, 0])
    assert q == 3 and b[2] == 0 and s[2] == 0 and sum(b) == pytest.approx(1) and sum(s) == pytest.approx(1)
