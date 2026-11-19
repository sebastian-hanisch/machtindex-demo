"""Jede Zahl der README und der App-Texte steht hier mit ihrer Voraussetzung (Erzeuger, n, Quote, Zahl der Zufalls-Seeds und Instanzen).

Zufall kommt aus SplitMix64 (`mdx_rng.py`); alle Reihen sind feste Funktionen von vier Zufalls-Seeds (101, 202, 303, 404) mit je 50 Instanzen je Zelle (200 je Zelle), die Beirat-Reihen
mit je 75 (300 je Zelle). Zählungen sind exakt, Mittel Bänder (Plattform: Summationsreihenfolge). Die Gewichte der Pareto- und Lognormal-Erzeuger laufen über Potenz, Logarithmus, Kosinus und
Exponentialfunktion der Rechenbibliothek; eine Rundungsabweichung zwischen Plattformen könnte dort einen Fall verschieben (siehe README, Ehrliche Grenzen).

Zahl -> Test: Voreinstellungen und Presets -> test_preset_*; Fuhrpark -> test_fleet_*; Erzeuger x Quote -> test_generator_table_*; Quote -> test_best_quote_*, test_unanimity_*;
Zählen -> test_nizza_*, test_raster_*; Rang-Satz -> test_rank_theorem_*; Spenderparadox -> test_donor_*; Zusammenschluss, Aufspaltung, neues Mitglied -> test_merge_*, test_split_*,
test_new_member_*; zwei Gewichtssysteme -> test_two_systems_*; Beirat -> test_board_*; Owen -> test_owen_*; Harsanyi -> test_harsanyi_*; Kern -> test_oracle_machtindex.py."""

import itertools
import math
from functools import lru_cache

import pytest

import mdx_constants as C
import mdx_evaluation as ev
import mdx_experiments as E
import mdx_game as G
import mdx_paradoxes as P
import mdx_scenario as S
import mdx_seats as ST


@lru_cache(maxsize=None)
def _generator_table():
    return E.generator_table(C.EXPERIMENT_GENERATORS, (5, 7, 9), C.PERMILLES)


def _cell(gen, n, permille):
    return next(r for r in _generator_table() if r["gen"] == gen and r["n"] == n and r["permille"] == permille)


def _analysis(weights, percent):
    w, err = S.parse_weights(weights)
    assert err is None
    return ev.analyse(ev.Settings(w, ev.permille_of(percent)))


# ---- Voreinstellung und Presets ---------------------------------------------------------------------------------------------------------

def test_fleet_preset_numbers():
    """Fuhrpark [40, 25, 10, 8, 5, 3, 2]: Summe 93, Quote 47 (einfache Mehrheit), 63 (mehr als 2/3). Das Mitglied mit 25 Lkw hat 26,9 % der Stimmen, aber Banzhaf-Schwingzahl 10 wie das mit 10 Lkw."""
    a = _analysis(C.DEFAULT_WEIGHTS, 50.0)
    assert a.total == 93 and a.quota == 47 and a.swings == (54, 10, 10, 10, 6, 2, 2)
    assert round(100 * a.vote_share[1], 1) == 26.9 and round(100 * a.banzhaf[1], 1) == 10.6 and round(100 * a.banzhaf[2], 1) == 10.6 and round(100 * a.vote_share[2], 1) == 10.8
    assert a.pivots[1] == a.pivots[2] and not a.veto and not a.null
    assert a.swings[3] == 10 and round(100 * a.banzhaf[3], 1) == 10.6 and round(100 * a.vote_share[3], 1) == 8.6      # auch das Mitglied mit 8 Lkw
    b = _analysis(C.DEFAULT_WEIGHTS, 67.0)
    assert b.quota == 63 and b.veto == (0,) and b.swings == (37, 27, 5, 5, 3, 1, 1)
    assert round(100 * b.banzhaf[0], 1) == 46.8 and round(100 * b.shapley_shubik[0], 1) == 56.0


def test_preset_one_large_five_small_has_half_the_power_with_37_5_percent_of_the_votes():
    a = _analysis("3, 1, 1, 1, 1, 1", 50.0)
    assert a.quota == 5 and a.vote_share[0] == 0.375 and a.banzhaf[0] == 0.5 and a.shapley_shubik[0] == 0.5
    assert a.banzhaf[1:] == (0.1,) * 5 and a.vote_share[1] == 0.125


def test_preset_banzhaf_differs_from_shapley_shubik_by_hand():
    a = _analysis("2, 1, 1", 50.0)
    assert a.quota == 3 and a.swings == (3, 1, 1) and a.pivots == (4, 1, 1)
    assert round(100 * a.banzhaf[0], 1) == 60.0 and round(100 * a.shapley_shubik[0], 1) == 66.7


def test_preset_null_player_dictator_and_unanimity():
    nul = _analysis("3, 3, 1", 60.0)
    assert nul.quota == 5 and nul.null == (2,) and nul.banzhaf == (0.5, 0.5, 0.0) and nul.shapley_shubik == (0.5, 0.5, 0.0)
    dic = _analysis("5, 1, 1, 1", 50.0)
    assert dic.quota == 5 and dic.dictator == 0 and dic.banzhaf == (1.0, 0.0, 0.0, 0.0)
    uni = _analysis("3, 3, 3, 1", 100.0)
    assert uni.quota == 10 and uni.banzhaf == (0.25,) * 4 and uni.shapley_shubik == (0.25,) * 4 and uni.veto == (0, 1, 2, 3)


def test_preset_donor_paradox_by_hand():
    a = _analysis("1, 1, 1, 2, 4", 67.0)
    assert a.quota == 7 and a.swings == (2, 2, 2, 6, 8)
    assert P.donor_outcome(list(a.weights), a.quota, 4, 3) == (1, -1)       # Banzhaf des Gebers steigt (8/20 -> 7/17), Shapley-Shubik sinkt (1/2 -> 9/20)


def test_preset_nizza_numbers():
    """27 Gewichte, Summe 345, Schwelle 255; Stimmanteil / Banzhaf / Shapley-Shubik in Prozent für das Mitglied mit 29 Stimmen, das mit 14 und das mit 3."""
    a = _analysis(C.PRESETS["EU-Rat Nizza (nur Stimmbedingung)"]["weights"], C.PRESETS["EU-Rat Nizza (nur Stimmbedingung)"]["p"])
    assert a.n == 27 and a.total == 345 and a.quota == 255
    for i, (votes, banz, ss) in {0: (8.41, 7.78, 8.67), 6: (4.06, 4.26, 3.99), 26: (0.87, 0.94, 0.82)}.items():
        assert (round(100 * a.vote_share[i], 2), round(100 * a.banzhaf[i], 2), round(100 * a.shapley_shubik[i], 2)) == (votes, banz, ss), i
    assert round(a.d_vote_banzhaf, 4) == 0.0330 and round(a.d_vote_shapley, 4) == 0.0141 and round(a.d_indices, 4) == 0.0472
    assert round(100 * max(abs(b - s) for b, s in zip(a.banzhaf, a.shapley_shubik)), 2) == 0.89


def test_preset_board_is_the_hamilton_distribution_of_the_standard_instance():
    members = [int(x) for x in C.BOARD_MEMBERS.split(",")]
    assert ST.hamilton(members, C.BOARD_SEATS_DEFAULT) == [int(x) for x in C.BOARD_HAMILTON_SEATS.split(",")]
    a = _analysis(C.PRESETS["Beirat: 40 Sitze nach Hamilton"]["weights"], 50.0)
    assert a.quota == 21 and round(100 * a.banzhaf[2], 1) == 78.2 and round(100 * a.shapley_shubik[2], 1) == 67.9


# ---- Erzeuger x Quote ------------------------------------------------------------------------------------------------------------------

def test_generator_table_shape_and_count_of_cells_with_at_least_five_points():
    rows = _generator_table()
    assert len(rows) == 72 and all(r["count"] == 200 for r in rows)
    assert sum(r["dB"] >= 0.05 for r in rows) == 59


def test_generator_table_range_of_the_deviation_between_power_and_vote_share():
    rows = _generator_table()
    low, high = min(rows, key=lambda r: r["dB"]), max(rows, key=lambda r: r["dB"])
    assert (low["gen"], low["n"], low["permille"]) == ("uniform", 9, 600) and low["dB"] == pytest.approx(0.0262, abs=5e-4)
    assert (high["gen"], high["n"], high["permille"]) == ("lognormal", 5, 500) and high["dB"] == pytest.approx(0.2174, abs=5e-4)


def test_generator_table_the_deviation_does_not_need_a_heavy_tail():
    """Fast gleiche Gewichte (8 bis 12) und Pareto mit α = 2,5 (leichter Tail): Abweichung von 3,2 bis 13,1 bzw. 3,7 bis 11,0 Prozentpunkten über alle 12 Zellen je Erzeuger."""
    for gen, lo, hi in (("equal", 0.0324, 0.1310), ("pareto25", 0.0365, 0.1103)):
        cells = [r["dB"] for r in _generator_table() if r["gen"] == gen]
        assert len(cells) == 12 and min(cells) == pytest.approx(lo, abs=5e-4) and max(cells) == pytest.approx(hi, abs=5e-4)


def test_generator_table_index_deviation_grows_with_the_quote():
    rows = _generator_table()
    half = [r for r in rows if r["permille"] == 500]
    top = [r for r in rows if r["permille"] == 750]
    assert max(r["dBS"] for r in half) == pytest.approx(0.0330, abs=5e-4) and max(r["max_pp"] for r in half) == pytest.approx(2.49, abs=0.05)
    assert max(r["dBS"] for r in top) == pytest.approx(0.1074, abs=5e-4)
    assert len(half) == len(top) == 18


@pytest.mark.parametrize("gen,null,dictator", [("equal", 0.0, 0.0), ("uniform", 0.37, 0.05), ("stepped", 0.5, 0.225), ("pareto12", 0.37, 0.27), ("pareto25", 0.075, 0.065), ("lognormal", 0.54, 0.32)])
def test_generator_table_null_players_and_dictators_depend_on_the_generator(gen, null, dictator):
    """n = 5, einfache Mehrheit, 200 Instanzen: Anteil der Instanzen mit Nullspieler bzw. Diktator."""
    r = _cell(gen, 5, 500)
    assert r["null"] == pytest.approx(null, abs=1e-9) and r["dictator"] == pytest.approx(dictator, abs=1e-9)


def test_generator_table_null_players_fall_with_n_for_the_stepped_generator():
    assert [_cell("stepped", n, 500)["null"] for n in (5, 7, 9)] == pytest.approx([0.5, 0.405, 0.35])


def test_every_generator_gives_other_weights_than_every_other_one():
    sets = {g: tuple(S.make_weights(g, 7, 101, j) for j in range(5)) for g in S.generator_keys()}
    assert len(set(sets.values())) == len(sets)


# ---- Quote als Regler ----------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _best(gen):
    return E.best_quote(gen, 7)


@pytest.mark.parametrize("gen,maj,best,rel,above,low", [
    ("equal", 0.0531, 0.0160, 0.6072, 200, 154), ("uniform", 0.0616, 0.0220, 0.6235, 197, 100), ("stepped", 0.1606, 0.0333, 0.7080, 196, 58),
    ("pareto12", 0.1932, 0.0352, 0.6735, 193, 42), ("pareto25", 0.0795, 0.0247, 0.6630, 190, 62), ("lognormal", 0.1861, 0.0376, 0.6676, 199, 33),
])
def test_best_quote_per_generator(gen, maj, best, rel, above, low):
    """n = 7, 200 Instanzen je Erzeuger: mittlere Abweichung bei einfacher Mehrheit und bei der besten ganzen Quote, mittlere beste Quote relativ zur Gewichtssumme,
    Instanzen mit bester Quote über der einfachen Mehrheit, Instanzen mit bester Abweichung unter 2 Prozentpunkten."""
    r = _best(gen)
    assert r["count"] == 200
    assert r["d_majority_B"] == pytest.approx(maj, abs=5e-4) and r["d_best_B"] == pytest.approx(best, abs=5e-4) and r["quote_rel"] == pytest.approx(rel, abs=5e-4)
    assert r["above_majority"] == above and r["below_low"] == low


def test_best_quote_verdict_counts_and_ratios():
    kind, text = ev.verdict_best_quote([_best(g) for g in C.EXPERIMENT_GENERATORS])
    assert kind == "info"
    assert "61 % bis 71 %" in text and "190 bis 200 von je 200" in text and "1/2,8" in text and "bis 1/5,5" in text


def test_unanimity_gives_every_member_the_same_power_and_raises_the_deviation():
    for w in ([3, 3, 3, 1], [10, 5, 1], [4, 4, 4, 2, 1]):
        sw, pv = G.pivot_counts_dp(w, sum(w))
        assert len(set(sw)) == 1 and len(set(pv)) == 1
    for gen, at_100 in (("equal", 0.0584), ("uniform", 0.2180), ("stepped", 0.3277), ("pareto12", 0.3451), ("pareto25", 0.1667), ("lognormal", 0.3561)):
        curve = E.quote_curve(gen, 7, (50, 100))
        assert curve[1]["dB"] == pytest.approx(at_100, abs=5e-4) and curve[1]["dB"] > curve[0]["dB"]
        assert curve[1]["dBS"] == 0.0 and curve[0]["count"] == 200       # bei Einstimmigkeit haben beide Indizes jedes Mitglied bei 1/7: Abstand 0


# ---- Zählen statt Aufzählen ----------------------------------------------------------------------------------------------------------------

def test_raster_numbers():
    """200 lognormale reelle Gewichtsvektoren (n = 8), auf ganze Gewichte mit Summe 30 bis 10.000 gerundet, Bezug Summe 100.000: größte Abweichung des Banzhaf-Anteils (Prozentpunkte)."""
    rows = E.raster_series()
    assert [r["total"] for r in rows] == [30, 100, 300, 1000, 10000]
    assert [r["over_1pp"] for r in rows] == [150, 82, 23, 8, 1]
    assert [r["mean_worst_pp"] for r in rows] == pytest.approx([2.4996, 0.9713, 0.3159, 0.1340, 0.0110], abs=5e-3)


def test_the_dp_table_for_the_slider_maximum_fits_and_runs():
    """n = 60, Gewichtssumme 100.000 (Reglermaximum): Ergebnis mit n! als Summe der Reihenfolgen; Zählfeld 60 x 100.001 x 8 Byte unter 50 MB."""
    w = [1666] * 59 + [100_000 - 1666 * 59]
    assert sum(w) == 100_000 and len(w) == 60
    sw, pv = G.pivot_counts_dp(w, 50_001)
    assert sum(pv) == math.factorial(60) and (len(w) + 1) * (sum(w) + 1) * 8 < 50e6


# ---- Rang-Satz ---------------------------------------------------------------------------------------------------------------------

def test_rank_theorem_enumeration_counts():
    r = E.rank_theorem_enumeration()
    assert r["ranges"] == E.RANK_THEOREM_RANGES
    assert (r["games"], r["rank_differs"], r["values_differ"]) == (26_832, 0, 10_565)


# ---- Paradoxa ----------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("row", C.DONOR_ENUMERATION)
def test_donor_enumeration_row(row):
    """Spenderparadox vollständig aufgezählt: alle nichtfallenden Gewichtsvektoren mit n Mitgliedern und Gewichten 1 bis wmax, alle Quoten über W/2, alle Einzelübertragungen einer Stimme."""
    n, wmax, games, transfers, cases_b, cases_s, *_ = (*row,)
    result = P.exhaustive_donor_count(n, wmax)
    assert result[:4] == (games, transfers, cases_b, cases_s)
    if n == 5:
        assert result[4] == ((1, 1, 1, 2, 4), 7, 4, 3)


def test_donor_enumeration_totals():
    assert sum(r[3] for r in C.DONOR_ENUMERATION) == 251_040 and sum(r[4] for r in C.DONOR_ENUMERATION) == 139 and sum(r[5] for r in C.DONOR_ENUMERATION) == 0
    assert (C.DONOR_ENUMERATION[2][4], C.DONOR_ENUMERATION[3][4]) == (100, 39)


@lru_cache(maxsize=None)
def _donor():
    return [E.donor_series(g, 6, pm) for g in C.PARADOX_GENERATORS for pm in (500, 667)]


def test_donor_random_series_banzhaf_only_above_the_simple_majority():
    rows = _donor()
    assert [r["transfers"] for r in rows] == [5725, 5725, 6000, 6000, 6000, 6000, 5330, 5330]
    assert [r["cases_b"] for r in rows] == [0, 4, 0, 30, 0, 3, 0, 15]
    assert [r["instances_b"] for r in rows] == [0, 4, 0, 15, 0, 3, 0, 13]
    assert [r["cases_s"] for r in rows] == [0] * 8 and all(r["instances"] == 200 for r in rows)
    assert ev.verdict_donor(rows)[0] == "warning"


def test_donor_verdict_text_names_the_zero_in_half_and_the_total():
    rows = _donor()
    kind, text = ev.verdict_donor(rows)
    assert sum(r["transfers"] for r in rows) == 46_110 and sum(r["cases_b"] for r in rows) == 52
    assert "**52 von 46.110**" in text and "bei p = 50 %: 0" in text and "und in 0 bei Shapley–Shubik" in text


@lru_cache(maxsize=None)
def _merge():
    return [E.merge_series(g, 6, pm) for g in C.PARADOX_GENERATORS for pm in (500, 667)]


def test_merge_counts_and_direction_agreement():
    rows = _merge()
    assert all(r["pairs"] == 3000 for r in rows)
    assert [r["less_b"] for r in rows] == [20, 337, 258, 262, 127, 233, 259, 331]
    assert [r["more_b"] for r in rows] == [2165, 1734, 1312, 1192, 2516, 2157, 1117, 1404]
    assert [r["less_s"] for r in rows] == [20, 325, 258, 205, 127, 122, 259, 330]
    assert [r["differ"] for r in rows] == [0, 137, 0, 318, 0, 201, 0, 21]          # bei p = 50 % in allen vier Erzeugern 0, bei 2/3 überall > 0 (Zweig-Test)
    assert sum(r["differ"] for r in rows[::2]) == 0 and all(r["differ"] > 0 for r in rows[1::2])


@lru_cache(maxsize=None)
def _split():
    return [E.split_series(g, 6, pm) for g in C.PARADOX_GENERATORS for pm in (500, 667)]


def test_split_counts():
    rows = _split()
    assert [r["cases"] for r in rows] == [1145, 1145, 1200, 1200, 1200, 1200, 1066, 1066]
    assert [r["more_b"] for r in rows] == [162, 343, 143, 224, 219, 421, 212, 290]
    assert [r["less_b"] for r in rows] == [808, 663, 570, 558, 849, 622, 490, 558]
    assert sum(r["more_b"] for r in rows) == 2014 and sum(r["cases"] for r in rows) == 9222 and sum(r["less_b"] for r in rows) == 5118


@lru_cache(maxsize=None)
def _new():
    return [E.new_member_series(g, 6, pm) for g in C.PARADOX_GENERATORS for pm in (500, 667)]


def test_new_member_counts():
    rows = _new()
    assert [r["gain_b"] for r in rows] == [171, 148, 96, 94, 155, 134, 121, 145]
    assert [r["gain_s"] for r in rows] == [170, 153, 105, 87, 151, 131, 128, 149] and all(r["instances"] == 200 for r in rows)
    assert sum(r["gain_b"] for r in rows) == 1064


# ---- zwei Gewichtssysteme ---------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _two():
    return [E.two_system_series(g, n, pm) for g in ("uniform", "lognormal") for n in (6, 8, 9) for pm in (500, 667)]


def test_two_systems_counts():
    rows = _two()
    assert all(r["instances"] == 200 for r in rows)
    assert [r["rank_differs"] for r in rows] == [57, 0, 94, 111, 94, 135, 16, 1, 77, 49, 80, 94]
    assert [r["reversal"] for r in rows] == [0, 0, 13, 42, 34, 86, 0, 0, 33, 11, 48, 48]
    assert [r["tie_only"] for r in rows] == [57, 0, 81, 69, 60, 49, 16, 1, 44, 38, 32, 46]
    assert [r["values_differ"] for r in rows] == [163, 184, 199, 200, 199, 200, 175, 184, 195, 198, 196, 200]
    assert all(r["reversal"] + r["tie_only"] == r["rank_differs"] for r in rows)


def test_two_systems_preset_has_a_true_reversal_found_by_enumeration_of_all_orders():
    """Fuhrpark [4, 5, 1, 1, 2, 4, 1] mit Quote 10 UND Umsatz [3, 1, 4, 4, 4, 3, 5] mit Quote 13: Schwingzahlen 21/17/11/11/11/21/19, Reihenfolgen 972/888/468/468/468/972/804 von 5040;
    Mitglied 7 liegt bei Banzhaf vor Mitglied 2 und bei Shapley-Shubik dahinter. Gegenprobe: alle 5040 Reihenfolgen."""
    w1, _ = S.parse_weights(C.SYSTEM_FLEET)
    w2, _ = S.parse_weights(C.SYSTEM_TURNOVER)
    win = G.intersection_game([w1, w2], [C.SYSTEM_FLEET_QUOTA, C.SYSTEM_TURNOVER_QUOTA])
    swings, pivots = G.pivot_counts_from_win(win, 7)
    assert swings == [21, 17, 11, 11, 11, 21, 19] and pivots == [972, 888, 468, 468, 468, 972, 804]
    counts = [0] * 7
    for order in itertools.permutations(range(7)):
        mask = 0
        for i in order:
            mask |= 1 << i
            if win[mask]:
                counts[i] += 1
                break
    assert counts == pivots
    assert swings[6] > swings[1] and pivots[6] < pivots[1]
    assert E.rank_pairs(swings, pivots)[0] >= 1


# ---- Beirat -------------------------------------------------------------------------------------------------------------------------

def test_board_standard_instance():
    members = [int(x) for x in C.BOARD_MEMBERS.split(",")]
    share = G.weight_shares(members)[2]
    assert round(100 * share, 1) == 46.1
    expect = {"Hamilton": (18, 78.2, 67.9), "Webster": (18, 78.2, 67.9), "Jefferson": (20, 91.3, 85.7)}
    for method, (seats, banz, ss) in expect.items():
        alloc = ST.allocate(members, 40, method)
        b, s, q = ST.seat_power(alloc)
        assert q == 21 and alloc[2] == seats and (round(100 * b[2], 1), round(100 * s[2], 1)) == (banz, ss), method
    ham = ST.staircase(members, 2, 40, 14, 22)
    assert [round(100 * r[2], 1) for r in ham] == [44.5, 50.0, 57.3, 68.0, 78.2, 86.8, 91.3, 100.0, 100.0]
    assert [round(100 * r[3], 1) for r in ham][4] == 67.9


@lru_cache(maxsize=None)
def _board_rows():
    return {sigma: [r for h in (16, 24, 48, 64) for r in E.seats_series(sigma, h)] for sigma in (1.2, 0.5)}


def test_board_series_jefferson_is_farthest_in_every_row_and_power_deviates_more_than_seats():
    rows = _board_rows()
    for sigma, group in rows.items():
        assert all(r["count"] == 300 for r in group)
        for h in (16, 24, 48, 64):
            cell = [r for r in group if r["seats"] == h]
            assert max(cell, key=lambda r: r["d_seat"])["method"] == "Jefferson"
            assert max(cell, key=lambda r: r["d_banzhaf"])["method"] == "Jefferson" and max(cell, key=lambda r: r["d_shapley_shubik"])["method"] == "Jefferson"
        assert all(r["d_banzhaf"] > r["d_seat"] and r["d_shapley_shubik"] > r["d_seat"] for r in group)


def test_board_series_dictators_and_ratios():
    rows = _board_rows()
    assert [r["dictators"] for r in rows[1.2]] == [52, 84, 52, 53, 74, 53, 53, 66, 53, 53, 65, 55]
    assert sum(r["dictators"] for r in rows[0.5]) == 0
    ratios = {sigma: [r["d_banzhaf"] / r["d_seat"] for r in group] for sigma, group in rows.items()}
    assert (min(ratios[1.2]), max(ratios[1.2])) == pytest.approx((2.5, 10.9), abs=0.1)
    assert (min(ratios[0.5]), max(ratios[0.5])) == pytest.approx((1.2, 2.7), abs=0.1)


# ---- Owen -----------------------------------------------------------------------------------------------------------------------------

def test_owen_merge_counts():
    """Zufalls-Seed 7, 300 Zusammenschlüsse je Zeile; Abstimmung: Gewichte 1 bis 9, Quote über W/2; Flughafen: Bedarfe 1 bis 20, Kostenspiel."""
    expected = {("vote", 6): (5, 132, 163), ("vote", 5): (0, 200, 100), ("airport", 6): (0, 69, 231), ("airport", 5): (0, 73, 227)}
    for (kind, n), (worse, same, better) in expected.items():
        r = E.owen_merge_series(kind, n, 300)
        assert (r["worse"], r["same"], r["better"]) == (worse, same, better), (kind, n)
        assert r["count"] == 300
    assert E.owen_merge_series("vote", 6, 300)["biggest_loss"] == pytest.approx(1 / 30)


def test_owen_verdict_names_the_class_dependence():
    kind, text = ev.verdict_owen(E.owen_merge_series("vote", 6, 300), E.owen_merge_series("airport", 6, 300))
    assert kind == "warning" and "nachteilig 5, unverändert 132, vorteilhaft 163" in text and "nachteilig 0, unverändert 69, vorteilhaft 231" in text


# ---- Harsanyi -------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("gen,permille,pearson", [("uniform", 500, -0.249), ("uniform", 750, 0.052), ("stepped", 500, 0.132), ("stepped", 750, 0.660), ("lognormal", 500, 0.209), ("lognormal", 750, 0.552)])
def test_harsanyi_mass_does_not_explain_the_index_deviation_throughout(gen, permille, pearson):
    """n = 8, 50 Instanzen (Zufalls-Seed 101): Pearson-Korrelation zwischen der Dividendenmasse ab Größe 3 und der Abweichung Banzhaf gegen Shapley-Shubik; das Vorzeichen wechselt, und der Betrag ist in vier von sechs Zellen unter 0,3."""
    r = E.harsanyi_correlation(gen, 8, permille)
    assert r["count"] == 50 and r["pearson"] == pytest.approx(pearson, abs=0.01)


def test_harsanyi_correlation_signs_and_sizes():
    values = [E.harsanyi_correlation(g, 8, pm)["pearson"] for g in ("uniform", "stepped", "lognormal") for pm in (500, 750)]
    assert min(values) < 0 < max(values) and sum(abs(v) < 0.3 for v in values) == 4
