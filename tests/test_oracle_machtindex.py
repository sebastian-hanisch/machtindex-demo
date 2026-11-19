"""Orakel-Tests (DEMO-PLAYBOOK §12): jede Kernroutine gegen einen anderen Rechenweg. Das Gerüst-Marker-Wort der Vorlage ist entfernt.

1. Die vier Rechenwege des Kerns (Aufzählung in Python, alle Reihenfolgen, Gewinntabelle in numpy, DP) auf Zufallsinstanzen aller Erzeuger, n = 3 bis 8.
2. Eine eigene Bruchrechnung nach der Definition (Shapley-Shubik über Teilmengen mit `fractions`) und die Zerlegung in Einstimmigkeitsspiele (Harsanyi).
3. Vetospieler gegen den Kern per LP (scipy, nur im Test).
4. Zählen in reinen Python-Ganzzahlen (eigene, andere Rekursion) gegen die numpy-DP bei n = 20 und n = 60.
5. EU-Rat Nizza (n = 27): DP gegen Aufzählung aller 2^26 Teilmengen je verschiedenem Gewicht (rund 2 s, rund 200 MB).
6. Owen-Formel gegen die Definition (alle Reihenfolgen mit Gruppen am Stück); Sitzverteilung gegen die Divisor-Bedingung und die Zahlen der Sitzverteilungs-Demo."""

import itertools
import math
from fractions import Fraction

import numpy as np
import pytest

import mdx_constants as C
import mdx_game as G
import mdx_harsanyi as H
import mdx_owen as O
import mdx_scenario as S
import mdx_seats as ST


def _instances(gens, ns, per_n, quotas=(500, 600, 750)):
    for gen in gens:
        for n in ns:
            for j in range(per_n):
                w = list(S.make_weights(gen, n, 11, j))
                for pm in quotas:
                    yield w, G.quota_from_share(sum(w), Fraction(pm, 1000))


def test_four_ways_agree_on_random_instances_of_every_generator():
    count = 0
    for w, q in _instances(S.generator_keys(), (3, 4, 5, 6), 6):
        swings, pivots = G.pivot_counts_dp(w, q)
        assert swings == G.swing_counts_enum(w, q), (w, q)
        assert pivots == G.pivot_counts_perm(w, q), (w, q)
        assert (swings, pivots) == G.pivot_counts_subsets(w, q), (w, q)
        assert G.pivot_counts_dp_multi(w, [q])[q] == (swings, pivots), (w, q)
        count += 1
    assert count == 6 * 4 * 6 * 3


def test_dp_agrees_with_the_enumeration_up_to_n_12_and_with_seven_orderings_at_n_7():
    for w, q in _instances(("uniform", "stepped", "lognormal"), (7, 8, 10, 12), 2):
        swings, pivots = G.pivot_counts_dp(w, q)
        assert swings == G.swing_counts_enum(w, q), (w, q)
        assert (swings, pivots) == G.pivot_counts_subsets(w, q), (w, q)
        if len(w) == 7:
            assert pivots == G.pivot_counts_perm(w, q), (w, q)


def test_shapley_shubik_from_the_definition_with_fractions():
    """Eigener Rechenweg ohne Hilfsfunktionen des Kerns: phi_i = Summe über S ohne i von |S|! (n-|S|-1)! / n! mal (v(S+i) - v(S))."""
    for w, q in _instances(("uniform", "pareto12"), (4, 5, 6), 3):
        n = len(w)
        phi = [Fraction(0)] * n
        for i in range(n):
            others = [j for j in range(n) if j != i]
            for r in range(n):
                coef = Fraction(math.factorial(r) * math.factorial(n - r - 1), math.factorial(n))
                for sub in itertools.combinations(others, r):
                    s = sum(w[j] for j in sub)
                    phi[i] += coef * ((s + w[i] >= q) - (s >= q))
        _, pivots = G.pivot_counts_dp(w, q)
        assert phi == [Fraction(p, math.factorial(n)) for p in pivots], (w, q)


def test_indices_from_harsanyi_dividends_equal_the_counts_exactly():
    for w, q in _instances(("equal", "uniform", "stepped"), (4, 6, 8), 2):
        n = len(w)
        win = G.win_vector(w, q)
        d = H.dividends(win, n)
        shapley, banzhaf = H.indices_from_dividends(d, n)
        swings, pivots = G.pivot_counts_dp(w, q)
        assert shapley == [Fraction(p, math.factorial(n)) for p in pivots], (w, q)
        assert banzhaf == [Fraction(s, 2 ** (n - 1)) for s in swings], (w, q)
        # die Dividenden zerlegen das Spiel: v(S) = Summe der Dividenden aller Teilmengen von S
        for mask in (1, (1 << n) - 1, 5 % (1 << n)):
            assert int(win[mask]) == sum(int(d[t]) for t in range(1 << n) if t & mask == t)


def test_veto_players_decide_whether_the_core_of_the_winning_game_is_empty():
    linprog = pytest.importorskip("scipy.optimize").linprog
    checked = nonempty = 0
    for n in (3, 4, 5):
        for w in itertools.combinations_with_replacement(range(1, 6), n):
            total = sum(w)
            for q in range(total // 2 + 1, total + 1):
                winners = [m for m in range(1, 1 << n) if sum(w[i] for i in range(n) if m >> i & 1) >= q]
                a = [[-(1.0 if m >> i & 1 else 0.0) for i in range(n)] for m in winners]
                res = linprog(np.zeros(n), A_ub=np.array(a), b_ub=-np.ones(len(winners)), A_eq=np.ones((1, n)), b_eq=[1.0], bounds=[(0, None)] * n, method="highs")
                core_nonempty = res.status == 0
                assert core_nonempty == bool(G.veto_players(list(w), q)), (w, q)
                checked += 1
                nonempty += core_nonempty
    assert checked > 1000 and 0 < nonempty < checked      # beide Fälle kommen vor


def _banzhaf_python_ints(w, q):
    """Banzhaf-Schwingzahlen in reinen Python-Ganzzahlen: je Mitglied eine Zählung der Teilmengensummen der übrigen (andere Rekursion als die Rücknahme der DP)."""
    out = []
    memo = {}
    for i, wi in enumerate(w):
        if wi in memo:
            out.append(memo[wi])
            continue
        rest = w[:i] + w[i + 1:]
        counts = {0: 1}
        for x in rest:
            nxt = dict(counts)
            for s, c in counts.items():
                nxt[s + x] = nxt.get(s + x, 0) + c
            counts = nxt
        memo[wi] = sum(c for s, c in counts.items() if q - wi <= s < q)
        out.append(memo[wi])
    return out


def _pivots_python_ints(w, q):
    """Shapley-Shubik-Zähler in reinen Python-Ganzzahlen: je Mitglied die Zählung nach (Größe, Summe) der übrigen."""
    n = len(w)
    out = []
    memo = {}
    for i, wi in enumerate(w):
        if wi in memo:
            out.append(memo[wi])
            continue
        counts = {(0, 0): 1}
        for j, x in enumerate(w):
            if j == i:
                continue
            nxt = dict(counts)
            for (k, s), c in counts.items():
                nxt[(k + 1, s + x)] = nxt.get((k + 1, s + x), 0) + c
            counts = nxt
        memo[wi] = sum(c * math.factorial(k) * math.factorial(n - 1 - k) for (k, s), c in counts.items() if q - wi <= s < q)
        out.append(memo[wi])
    return out


def test_numpy_dp_equals_python_integer_counting_at_n_20_and_n_60():
    w20 = [1 + (7 * i + 3) % 6 for i in range(20)]                 # Gewichte 1 bis 6, Summe 70 (von Hand festgelegt, nicht zufällig)
    q20 = sum(w20) // 2 + 1
    swings, pivots = G.pivot_counts_dp(w20, q20)
    assert swings == _banzhaf_python_ints(w20, q20) and pivots == _pivots_python_ints(w20, q20)
    assert sum(pivots) == math.factorial(20)
    w60 = [1 + (11 * i + 5) % 20 for i in range(60)]
    q60 = sum(w60) // 2 + 1
    assert G.pivot_counts_dp(w60, q60)[0] == _banzhaf_python_ints(w60, q60)
    swings60, pivots60 = G.pivot_counts_dp(w60, q60)
    assert sum(pivots60) == math.factorial(60)                      # die Zähler der Reihenfolgen summieren sich zu n! (große Python-Zahl, kein Überlauf)


def _nizza():
    preset = C.PRESETS["EU-Rat Nizza (nur Stimmbedingung)"]
    w, err = S.parse_weights(preset["weights"])
    assert err is None
    return list(w), G.quota_from_share(sum(w), Fraction(round(preset["p"] * 10), 1000))


def test_nizza_preset_has_27_members_345_votes_and_threshold_255():
    w, q = _nizza()
    assert len(w) == 27 and sum(w) == 345 and q == 255


def _enumerate_numpy(w, q):
    """Unabhängig vom DP: je verschiedenem Gewicht alle 2^(n-1) Teilmengen der übrigen (Summe und Größe) durch Verdopplung."""
    n = len(w)
    fak = [math.factorial(k) for k in range(n + 1)]
    result = {}
    for wi in sorted(set(w)):
        rest = list(w)
        rest.remove(wi)
        sums = np.zeros(1, dtype=np.int16)
        sizes = np.zeros(1, dtype=np.int8)
        for x in rest:
            sums = np.concatenate((sums, sums + np.int16(x)))
            sizes = np.concatenate((sizes, sizes + np.int8(1)))
        mask = (sums >= q - wi) & (sums < q)
        per_size = np.bincount(sizes[mask], minlength=n)
        result[wi] = (int(mask.sum()), sum(int(per_size[s]) * fak[s] * fak[n - 1 - s] for s in range(n)))
        del sums, sizes, mask
    return [result[x][0] for x in w], [result[x][1] for x in w]


def test_dp_equals_the_enumeration_of_all_2_to_the_26_subsets_for_the_nizza_weights():
    w, q = _nizza()
    assert G.pivot_counts_dp(w, q) == _enumerate_numpy(w, q)


def _core_two_ways(v, n, unions):
    return O.owen_formula(v, n, unions), O.owen_by_orders(v, n, unions)


def test_owen_formula_equals_the_definition_over_all_admissible_orders():
    rng_games = []
    for j in range(12):
        w = S.make_weights("uniform", 5, 3, j)
        q = sum(w) // 2 + 1
        rng_games.append(([int(sum(w[i] for i in range(5) if m >> i & 1) >= q) for m in range(32)], 5))
        rng_games.append(([max([w[i] for i in range(5) if m >> i & 1], default=0) for m in range(32)], 5))      # Flughafenspiel
    for v, n in rng_games:
        for unions in ([[0, 1], [2], [3, 4]], [[0], [1], [2], [3], [4]], [[0, 1, 2, 3, 4]], [[0, 3], [1, 2, 4]]):
            formula, by_orders = _core_two_ways(v, n, unions)
            assert formula == by_orders
            assert sum(formula) == v[(1 << n) - 1]


def test_owen_of_the_three_player_majority_by_hand():
    """Mehrheit mit drei Spielern, Gruppen {1,2} und {3}: Owen (1/2, 1/2, 0); mit lauter Einzelgruppen der Shapley-Wert 1/3 je Spieler."""
    v = [int(bin(m).count("1") >= 2) for m in range(8)]
    assert O.owen_formula(v, 3, [[0, 1], [2]]) == [Fraction(1, 2), Fraction(1, 2), Fraction(0)]
    assert O.shapley_value(v, 3) == [Fraction(1, 3)] * 3


def test_hamilton_is_the_largest_remainder_rule_with_fractions_and_jefferson_satisfies_the_divisor_condition():
    for j in range(40):
        members = S.make_weights("lognormal", 8, 5, j)
        total, seats = sum(members), 16 + j % 40
        ham = ST.hamilton(list(members), seats)
        quotas = [Fraction(m * seats, total) for m in members]
        assert sum(ham) == seats
        assert all(math.floor(qt) <= h <= math.ceil(qt) for qt, h in zip(quotas, ham))             # Quotenregel (Hamilton hält sie immer)
        jef = ST.divisor_method(list(members), seats, "Jefferson")
        assert sum(jef) == seats
        # Divisorbedingung: der kleinste Rang unter den vergebenen Sitzen ist mindestens so groß wie der größte Rang eines nächsten Sitzes
        assert min(Fraction(m, s) for m, s in zip(members, jef) if s > 0) >= max(Fraction(m, s + 1) for m, s in zip(members, jef))
        web = ST.divisor_method(list(members), seats, "Webster")
        assert min(Fraction(m, 2 * s - 1) for m, s in zip(members, web) if s > 0) >= max(Fraction(m, 2 * s + 1) for m, s in zip(members, web))


def test_the_standard_instance_of_the_seat_demo_gives_its_readme_numbers():
    """README der Sitzverteilungs-Demo: Quote des größten Verbands 18,43; Jefferson gibt ihm 20 Sitze und dem kleinsten (194 Mitglieder, Quote 0,68) keinen; Hamilton und Webster 18."""
    members = [int(x) for x in C.BOARD_MEMBERS.split(",")]
    assert sum(members) == 11458 and round(members[2] * 40 / sum(members), 2) == 18.43 and round(members[4] * 40 / sum(members), 2) == 0.68
    assert ST.hamilton(members, 40)[2] == 18 and ST.divisor_method(members, 40, "Webster")[2] == 18
    jefferson = ST.divisor_method(members, 40, "Jefferson")
    assert jefferson[2] == 20 and jefferson[4] == 0
    assert ST.hamilton(members, 40) == [int(x) for x in C.BOARD_HAMILTON_SEATS.split(",")]
