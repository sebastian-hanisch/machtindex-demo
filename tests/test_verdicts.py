"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

from dataclasses import replace
from fractions import Fraction

import mdx_evaluation as ev


def _a(weights, percent=50.0):
    return ev.analyse(ev.Settings(tuple(weights), ev.permille_of(percent)))


def test_format_helpers():
    assert ev.de(2.345, 2) == "2,35" and ev.pct(0.269) == "26,9 %" and ev.pp(0.0333) == "3,3 Prozentpunkte" and ev.th(46110) == "46.110" and ev.name(0) == "M1"
    assert ev.names([0, 2]) == "M1, M3"


def test_power_verdict_dictator():
    kind, text = ev.verdict_power(_a([5, 1, 1, 1]))
    assert kind == "warning" and "**M1 entscheidet allein** (Gewicht 5 von 8, Quote 5)" in text and "alle anderen haben Macht 0" in text


def test_power_verdict_null_player_singular_and_plural():
    kind, text = ev.verdict_power(_a([3, 3, 1], 60.0))
    assert kind == "warning" and "**Nullspieler:** M3 hat zusammen 14,3 % der Stimmen" in text and "Quote 5 von 7" in text and "14,3 Prozentpunkten" in text
    kind2, text2 = ev.verdict_power(_a([6, 6, 1, 1], 70.0))                # Quote 10 von 14: nur {M1, M2} gewinnt; M3 und M4 sind Nullspieler
    assert kind2 == "warning" and "M3, M4 haben zusammen 14,3 % der Stimmen" in text2


def test_power_verdict_veto_player():
    kind, text = ev.verdict_power(_a([2, 1, 1], 50.0))
    assert kind == "info" and "**Vetospieler:** ohne M1 erreicht keine Koalition die Quote 3 von 4" in text and "10,0 Prozentpunkte" in text


def test_power_verdict_threshold_between_info_and_success_is_five_points():
    a = _a([4, 3, 2], 50.0)                                                     # kein Veto, kein Nullspieler (Quote 5)
    assert not a.veto and not a.null and a.dictator is None
    assert ev.verdict_power(replace(a, d_vote_banzhaf=0.05))[0] == "info"
    kind, text = ev.verdict_power(replace(a, d_vote_banzhaf=0.0499))
    assert kind == "success" and "nahe beieinander" in text
    assert ev.verdict_power(_a([1, 1, 1], 50.0))[0] == "success"                # Symmetrie: Macht gleich Stimmanteil


def test_power_verdict_names_the_largest_gap_member():
    kind, text = ev.verdict_power(_a([40, 25, 10, 8, 5, 3, 2], 50.0))
    assert kind == "info" and "Am weitesten weicht M2 ab: 26,9 % der Stimmen, aber 10,6 % der Macht (Banzhaf)." in text and "17,5 Prozentpunkten" in text


def test_indices_verdict_branches():
    a = _a([2, 1, 1])
    kind, text = ev.verdict_indices(a, 0, 0)
    assert kind == "info" and "6,7 Prozentpunkte" in text and "größte Abweichung eines Mitglieds 6,7 Prozentpunkte" in text and "gleich" in text
    assert "dieselben Werte" in ev.verdict_indices(_a([3, 3, 3, 1], 100.0), 0, 0)[1]
    kind, text = ev.verdict_indices(a, 2, 1)
    assert kind == "error" and "2 Paare mit umgekehrter und 1 Paare" in text


def test_rank_theorem_verdict():
    kind, text = ev.verdict_rank_theorem(26832, 0, 10565)
    assert kind == "success" and "allen 26832 aufgezählten" in text and "in 10565 dieser Spiele" in text
    kind, text = ev.verdict_rank_theorem(100, 3, 50)
    assert kind == "error" and "3 von 100" in text


def _row(gen, n, pm, dB, dBS):
    return {"gen": gen, "n": n, "permille": pm, "dB": dB, "dBS": dBS}


def test_generators_verdict_counts_cells_and_names_the_extremes():
    rows = [_row("uniform", 9, 500, 0.03, 0.01), _row("lognormal", 5, 500, 0.21, 0.03), _row("uniform", 7, 750, 0.06, 0.10), _row("lognormal", 7, 750, 0.20, 0.09)]
    kind, text = ev.verdict_generators(rows)
    assert kind == "info" and "In **3 von 4 Zellen**" in text and "sie reicht von 3,0 Prozentpunkten" in text and "bis 21,0 Prozentpunkten (lognormal (μ = 2, σ = 1), n = 5, p = 50,0 %)" in text
    assert "bei p = 50 % höchstens um 3,0 Prozentpunkten" in text and "bei p = 75,0 % bis zu 10,0 Prozentpunkten" in text
    assert ev.verdict_generators([_row("equal", 5, 500, 0.01, 0.0)])[0] == "success"


def _best(gen, maj, best, rel, above):
    return {"gen": gen, "d_majority_B": maj, "d_best_B": best, "quote_rel": rel, "above_majority": above, "count": 200}


def test_best_quote_verdict_by_hand():
    kind, text = ev.verdict_best_quote([_best("equal", 0.06, 0.02, 0.60, 190), _best("stepped", 0.20, 0.04, 0.70, 200)])
    assert kind == "info" and "60 % bis 70 %" in text and "190 bis 200 von je 200" in text and "1/3,0 (fast gleich (8 bis 12)) bis 1/5,0 (gestuft (3, 10 oder 30))" in text


def test_donor_verdict_zero_and_nonzero():
    zero = [{"permille": 500, "transfers": 1000, "cases_b": 0, "cases_s": 0}]
    assert ev.verdict_donor(zero)[0] == "info" and "In keiner der 1.000 Einzelübertragungen" in ev.verdict_donor(zero)[1]
    rows = [{"permille": 500, "transfers": 1000, "cases_b": 0, "cases_s": 0}, {"permille": 667, "transfers": 1000, "cases_b": 7, "cases_s": 1}]
    kind, text = ev.verdict_donor(rows)
    assert kind == "warning" and "**7 von 2.000**" in text and "bei p = 50 %: 0" in text and "in 1 bei Shapley–Shubik" in text


def test_merge_split_new_verdicts():
    merge = [{"permille": 500, "pairs": 100, "less_b": 4, "differ": 0}, {"permille": 667, "pairs": 100, "less_b": 6, "differ": 9}]
    assert "weniger** Macht als die beiden vorher zusammen in 10 von 200 Paaren" in ev.verdict_merge(merge)[1] and "in 0 Paaren bei p = 50 %" in ev.verdict_merge(merge)[1] and "in 9 Paaren bei den höheren" in ev.verdict_merge(merge)[1]
    assert "**mehr** Macht in 30 von 100 Fällen, weniger in 60" in ev.verdict_split([{"cases": 100, "more_b": 30, "less_b": 60}])[1]
    assert "in 120 von 200 Instanzen (Banzhaf)" in ev.verdict_new_member([{"instances": 200, "gain_b": 120}])[1]


def test_paradox_instance_verdicts():
    one, two, three, four = Fraction(2, 5), Fraction(7, 17), Fraction(1, 2), Fraction(9, 20)
    kind, text = ev.verdict_paradox_instance("donor", "Geber M5", one, two, three, four)
    assert kind == "warning" and text.startswith("**Spenderparadox:**") and "Banzhaf-Anteil 40,0 % → 41,2 % (mehr)" in text and "Shapley–Shubik-Anteil 50,0 % → 45,0 % (weniger)" in text
    assert ev.verdict_paradox_instance("donor", "x", two, one, three, four)[0] == "info"
    assert ev.verdict_paradox_instance("donor", "x", one, one, one, Fraction(3, 5))[1].startswith("**Spenderparadox (nur Shapley–Shubik):**")
    assert ev.verdict_paradox_instance("merge", "B", Fraction(1, 2), Fraction(1, 3), Fraction(1, 2), Fraction(1, 2))[0] == "warning"
    assert ev.verdict_paradox_instance("merge", "B", Fraction(1, 3), Fraction(1, 2), Fraction(1, 3), Fraction(1, 2))[0] == "info"
    assert ev.verdict_paradox_instance("split", "S", Fraction(1, 3), Fraction(1, 2), Fraction(1, 3), Fraction(1, 3))[0] == "warning"
    assert ev.verdict_paradox_instance("split", "S", Fraction(1, 2), Fraction(1, 3), Fraction(1, 2), Fraction(1, 3))[0] == "info"
    assert "keine Wertung" in ev.verdict_paradox_instance("new", "N", Fraction(1, 5), Fraction(1, 4), Fraction(1, 5), Fraction(1, 5))[1]
    assert "gleich viel" in ev.verdict_paradox_instance("new", "N", Fraction(1, 5), Fraction(1, 5), Fraction(1, 5), Fraction(1, 5))[1]


def test_two_system_verdicts():
    assert ev.verdict_two_systems_instance(2, 1, 21, False)[0] == "warning" and "in 2 von 21 Mitgliederpaaren" in ev.verdict_two_systems_instance(2, 1, 21, False)[1]
    assert "in 3 von 21 Paaren ist ein Index gleichauf" in ev.verdict_two_systems_instance(0, 3, 21, False)[1]
    assert ev.verdict_two_systems_instance(0, 0, 21, True)[1] == "Beide Indizes geben dieselben Werte."
    assert "Rangordnung ist bei beiden Indizes gleich" in ev.verdict_two_systems_instance(0, 0, 21, False)[1]
    rows = [{"instances": 200, "rank_differs": 0, "reversal": 0}, {"instances": 200, "rank_differs": 135, "reversal": 86}]
    kind, text = ev.verdict_two_systems(rows)
    assert kind == "warning" and "in 0 bis 135 von je 200 Instanzen" in text and "in 1 von 2 Zellen nie" in text and "in 0 bis 86 Instanzen je Zelle" in text


def test_board_verdict_branches():
    members, seats = [10, 5, 5], [2, 1, 1]
    kind, text = ev.verdict_board(members, seats, [0.65, 0.175, 0.175], [0.7, 0.15, 0.15], "Hamilton", 4)
    assert kind == "info" and "50,0 % der Mitglieder" in text and "2 von 4 Sitzen (50,0 %)" in text and "65,0 % der Macht (Banzhaf) und 70,0 % (Shapley–Shubik)" in text
    assert ev.verdict_board(members, seats, [0.6, 0.2, 0.2], [0.5, 0.25, 0.25], "Webster", 4)[0] == "success"       # 0,6 = 1,2 mal Mitgliederanteil: nicht darüber
    kind, text = ev.verdict_board(members, [3, 0, 0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], "Jefferson", 3)
    assert kind == "warning" and text.endswith("Er entscheidet allein.")


def test_seats_series_verdict_by_hand():
    def rows(h, a, b, c):
        return [{"method": m, "seats": h, "d_seat": d, "d_banzhaf": 3 * d, "d_shapley_shubik": 2 * d} for m, d in zip(("Hamilton", "Jefferson", "Webster"), (a, b, c))]
    kind, text = ev.verdict_seats_series({1.2: rows(16, 0.1, 0.2, 0.1) + rows(24, 0.1, 0.3, 0.1), 0.5: rows(16, 0.2, 0.1, 0.1)})
    assert kind == "info" and "σ = 1,2: die Macht weicht 3,0- bis 3,0-mal so weit" in text and "Jefferson liegt in 2 von 3 Zeilen" in text


def test_runtime_and_raster_verdicts():
    rows = [{"n": 14, "total": 143, "seconds": 0.0003}, {"n": 60, "total": 12345, "seconds": 0.0123}]
    assert "n = 60 mit Gewichtssumme 12.345 in 0,012 s" in ev.verdict_runtime(rows)[1]
    kind, text = ev.verdict_raster([{"total": 30, "mean_worst_pp": 2.5, "over_1pp": 150, "count": 200}, {"total": 10000, "mean_worst_pp": 0.011, "over_1pp": 1, "count": 200}])
    assert "Gewichtssumme 30" in text and "um höchstens 2,50 Prozentpunkte" in text and "über 1 Prozentpunkt in 150 von 200" in text and "bei 10.000 sind es 0,011 (1 von 200)" in text


def test_owen_verdict_branches():
    vote = {"n": 6, "count": 300, "worse": 5, "same": 132, "better": 163, "biggest_loss": 1 / 30}
    airport = {"n": 6, "count": 300, "worse": 0, "same": 69, "better": 231}
    kind, text = ev.verdict_owen(vote, airport)
    assert kind == "warning" and "größte Einbuße 0,033" in text and "kein nachteiliger Fall auf" in text
    kind2, text2 = ev.verdict_owen({**vote, "worse": 0, "biggest_loss": 0.0}, airport)
    assert kind2 == "info" and "größte Einbuße" not in text2
    assert ev.verdict_owen(vote, {**airport, "worse": 2})[0] == "info"
