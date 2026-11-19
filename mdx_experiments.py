"""Messreihen der Experimente (🔬): jede Reihe ist eine reine Funktion von festen Zufalls-Seeds, die App und die Tests rechnen mit derselben Funktion.

Eine Zelle ist (Erzeuger, n, Quote). Je Zelle werden `seeds` x `per_seed` Instanzen gezogen (Standard: 4 Zufalls-Seeds x 50 = 200). Alle Zählungen sind exakt; Anteile als
Brüche, wo ein Vergleich an einer Toleranz hängen könnte."""

import itertools
import math
import time
from fractions import Fraction

import mdx_game as G
import mdx_owen as O
import mdx_paradoxes as P
import mdx_scenario as S
import mdx_seats as ST
from mdx_rng import SplitMix64

SEEDS = (101, 202, 303, 404)
PER_SEED = 50


def _p(permille: int) -> Fraction:
    return Fraction(permille, 1000)


def distance_to_weights(counts, w) -> Fraction:
    """Halbe L1-Distanz zwischen dem Machtanteil (Zähler `counts`, normiert auf ihre Summe) und dem Stimmanteil: exakt."""
    total, wsum = sum(counts), sum(w)
    if total == 0:
        return Fraction(1)
    return Fraction(sum(abs(c * wsum - wi * total) for c, wi in zip(counts, w)), 2 * wsum * total)


def distance_between(counts_a, counts_b) -> Fraction:
    """Halbe L1-Distanz zwischen zwei Machtanteilen aus je eigenen Zählern (zum Beispiel Banzhaf gegen Shapley-Shubik): exakt."""
    ta, tb = sum(counts_a), sum(counts_b)
    if ta == 0 or tb == 0:
        return Fraction(1)
    return Fraction(sum(abs(a * tb - b * ta) for a, b in zip(counts_a, counts_b)), 2 * ta * tb)


def instances(gen, n, seeds=SEEDS, per_seed=PER_SEED, which=0):
    for seed in seeds:
        for j in range(per_seed):
            yield S.make_weights(gen, n, seed, j, which)


# ---------------------------------------------------------------- E1: Erzeuger x Quote (Macht gegen Stimmanteil)

def cell_stats(gen, n, permille, seeds=SEEDS, per_seed=PER_SEED) -> dict:
    """Mittel und Anteile über die Instanzen einer Zelle. dB: Macht (Banzhaf) gegen Stimmanteil, dS: dasselbe für Shapley-Shubik, dBS: die beiden Indizes gegeneinander
    (halbe L1-Abstände), max_pp: größte Abweichung eines Mitglieds zwischen den beiden Indizes in Prozentpunkten (Mittel); null/dictator/veto: Anteil der Instanzen mit
    Nullspieler, Diktator, Vetospieler (ohne Diktator)."""
    sums = {"dB": 0.0, "dS": 0.0, "dBS": 0.0, "max_pp": 0.0, "null": 0, "dictator": 0, "veto": 0}
    count = 0
    fact = math.factorial(n)
    for w in instances(gen, n, seeds, per_seed):
        q = G.quota_from_share(sum(w), _p(permille))
        swings, pivots = G.pivot_counts_dp(w, q)
        sums["dB"] += float(distance_to_weights(swings, w))
        sums["dS"] += float(distance_to_weights(pivots, w))
        sums["dBS"] += float(distance_between(swings, pivots))
        sw_total = sum(swings)
        sums["max_pp"] += 100.0 * float(max(abs(Fraction(s, sw_total) - Fraction(p, fact)) for s, p in zip(swings, pivots)))
        sums["null"] += bool(G.null_players(swings))
        dik = G.dictator(swings) is not None
        sums["dictator"] += dik
        sums["veto"] += (not dik) and bool(G.veto_players(w, q))
        count += 1
    out = {k: v / count for k, v in sums.items()}
    out.update(count=count, gen=gen, n=n, permille=permille)
    return out


def generator_table(gens, ns, permilles, seeds=SEEDS, per_seed=PER_SEED) -> list[dict]:
    return [cell_stats(g, n, pm, seeds, per_seed) for g in gens for n in ns for pm in permilles]


# ---------------------------------------------------------------- E2: Quote als Regler

def quote_curve(gen, n, percents, seeds=SEEDS, per_seed=PER_SEED) -> list[dict]:
    """Verlauf über die Quote p (in Prozent; 100 heißt Einstimmigkeit q = W): Mittel von dB, dS, dBS und Anteil mit Nullspieler und Vetospieler."""
    rows = []
    for pct in percents:
        acc = {"dB": 0.0, "dS": 0.0, "dBS": 0.0, "null": 0, "veto": 0}
        count = 0
        for w in instances(gen, n, seeds, per_seed):
            q = G.quota_from_percent(sum(w), pct)
            swings, pivots = G.pivot_counts_dp(w, q)
            acc["dB"] += float(distance_to_weights(swings, w))
            acc["dS"] += float(distance_to_weights(pivots, w))
            acc["dBS"] += float(distance_between(swings, pivots))
            acc["null"] += bool(G.null_players(swings))
            acc["veto"] += (G.dictator(swings) is None) and bool(G.veto_players(w, q))
            count += 1
        rows.append({"percent": pct, "count": count, **{k: v / count for k, v in acc.items()}})
    return rows


def best_quote(gen, n, seeds=SEEDS, per_seed=PER_SEED, low=0.02) -> dict:
    """Beste ganze Quote je Instanz: die Quote q in (W/2, W] mit der kleinsten Abweichung zwischen Banzhaf-Anteil und Stimmanteil (bei Gleichstand die kleinere Quote).
    Rückgabe: Mittel der Abweichung bei einfacher Mehrheit und bei bester Quote (Banzhaf und Shapley-Shubik), mittlere beste Quote relativ zu W, Zahl der Instanzen, in
    denen die beste Quote über der einfachen Mehrheit liegt, und in denen die beste Abweichung unter `low` liegt."""
    acc = {"d_majority_B": 0.0, "d_best_B": 0.0, "d_majority_S": 0.0, "d_best_S": 0.0, "quote_rel": 0.0}
    above = below_low = count = 0
    for w in instances(gen, n, seeds, per_seed):
        total = sum(w)
        quotas = list(range(total // 2 + 1, total + 1))
        table = G.pivot_counts_dp_multi(w, quotas)
        best_b = best_s = None
        best_q = None
        for q in quotas:
            sw, pv = table[q]
            db, ds = distance_to_weights(sw, w), distance_to_weights(pv, w)
            if q == quotas[0]:
                acc["d_majority_B"] += float(db)
                acc["d_majority_S"] += float(ds)
            if best_b is None or db < best_b:
                best_b, best_q = db, q
            if best_s is None or ds < best_s:
                best_s = ds
        acc["d_best_B"] += float(best_b)
        acc["d_best_S"] += float(best_s)
        acc["quote_rel"] += best_q / total
        above += best_q > quotas[0]
        below_low += best_b < Fraction(low).limit_denominator(1000)
        count += 1
    out = {k: v / count for k, v in acc.items()}
    out.update(count=count, above_majority=above, below_low=below_low, gen=gen, n=n)
    return out


# ---------------------------------------------------------------- E3: Paradoxa

def donor_series(gen, n, permille, seeds=SEEDS, per_seed=PER_SEED) -> dict:
    """Spenderparadox: Anteil aller Einzelübertragungen einer Stimme, nach denen der Geber Machtanteil GEWINNT (Banzhaf, Shapley-Shubik), und Zahl der Instanzen mit mindestens einem Fall."""
    transfers = cases_b = cases_s = games = games_b = games_s = 0
    for w in instances(gen, n, seeds, per_seed):
        q = G.quota_from_share(sum(w), _p(permille))
        any_b = any_s = False
        base = P.powers(w, q)
        for giver in range(n):
            if w[giver] < 2:
                continue
            for receiver in range(n):
                if receiver == giver:
                    continue
                rb, rs = P.donor_outcome(w, q, giver, receiver, base)
                transfers += 1
                cases_b += rb > 0
                cases_s += rs > 0
                any_b |= rb > 0
                any_s |= rs > 0
        games += 1
        games_b += any_b
        games_s += any_s
    return {"gen": gen, "n": n, "permille": permille, "instances": games, "transfers": transfers, "cases_b": cases_b, "cases_s": cases_s,
            "instances_b": games_b, "instances_s": games_s}


def merge_series(gen, n, permille, seeds=SEEDS, per_seed=PER_SEED) -> dict:
    """Zusammenschluss zweier Mitglieder (alle Paare): der Block hat weniger / gleich / mehr Macht als die beiden vorher zusammen (Banzhaf, Shapley-Shubik); dazu die Zahl der Paare,
    bei denen die beiden Indizes in der Richtung verschieden sind."""
    less_b = more_b = less_s = more_s = differ = pairs = 0
    for w in instances(gen, n, seeds, per_seed):
        q = G.quota_from_share(sum(w), _p(permille))
        base = P.powers(w, q)
        for i in range(n):
            for k in range(i + 1, n):
                rb, rs = P.merge_outcome(w, q, i, k, base)
                pairs += 1
                less_b += rb < 0
                more_b += rb > 0
                less_s += rs < 0
                more_s += rs > 0
                differ += rb != rs
    return {"gen": gen, "n": n, "permille": permille, "pairs": pairs, "less_b": less_b, "more_b": more_b, "less_s": less_s, "more_s": more_s, "differ": differ}


def split_series(gen, n, permille, seeds=SEEDS, per_seed=PER_SEED) -> dict:
    """Aufspaltung eines Mitglieds (Gewicht mindestens 2) in zwei: beide zusammen haben mehr / weniger Macht als vorher (Banzhaf, Shapley-Shubik)."""
    more_b = less_b = more_s = less_s = cases = 0
    for w in instances(gen, n, seeds, per_seed):
        q = G.quota_from_share(sum(w), _p(permille))
        base = P.powers(w, q)
        for i in range(n):
            if w[i] < 2:
                continue
            rb, rs = P.split_outcome(w, q, i, base)
            cases += 1
            more_b += rb > 0
            less_b += rb < 0
            more_s += rs > 0
            less_s += rs < 0
    return {"gen": gen, "n": n, "permille": permille, "cases": cases, "more_b": more_b, "less_b": less_b, "more_s": more_s, "less_s": less_s}


def new_member_series(gen, n, permille, seeds=SEEDS, per_seed=PER_SEED) -> dict:
    """Neues Mitglied (n alte; das (n+1)-te Gewicht aus demselben Erzeuger), Quote mit demselben Anteil p neu bestimmt: in wie vielen Instanzen gewinnt ein altes Mitglied Machtanteil?"""
    gain_b = gain_s = count = 0
    for w in instances(gen, n + 1, seeds, per_seed):
        gb, gs = P.add_member_outcome(w[:n], w[n], _p(permille))
        gain_b += gb
        gain_s += gs
        count += 1
    return {"gen": gen, "n": n, "permille": permille, "instances": count, "gain_b": gain_b, "gain_s": gain_s}


# ---------------------------------------------------------------- E4: zwei Gewichtssysteme

def rank_pairs(swings, pivots) -> tuple[int, int]:
    """Vergleich der Rangordnung beider Indizes über alle Paare: (Paare mit echter Umkehrung, Paare mit Gleichstand im einen und strikter Ordnung im anderen Index)."""
    n = len(swings)
    reversals = tie_vs_strict = 0
    for i in range(n):
        for j in range(i + 1, n):
            a = (swings[i] > swings[j]) - (swings[i] < swings[j])
            b = (pivots[i] > pivots[j]) - (pivots[i] < pivots[j])
            if a * b < 0:
                reversals += 1
            elif a != b:
                tie_vs_strict += 1
    return reversals, tie_vs_strict


RANK_THEOREM_RANGES = ((3, 12), (4, 10), (5, 8), (6, 6), (7, 4))      # (n, größtes Gewicht)


def rank_theorem_enumeration(ranges=RANK_THEOREM_RANGES) -> dict:
    """Aufzählung aller nichtfallenden Gewichtsvektoren (n Mitglieder, Gewichte 1 bis wmax) mit allen Quoten über W/2: Zahl der Spiele, in denen die Rangordnung der beiden Indizes
    verschieden ist (der Satz sagt: nie), und in denen ihre Werte verschieden sind."""
    games = rank_differs = values_differ = 0
    for n, wmax in ranges:
        for w in itertools.combinations_with_replacement(range(1, wmax + 1), n):
            total = sum(w)
            for q in range(total // 2 + 1, total + 1):
                swings, pivots = G.pivot_counts_dp(list(w), q)
                games += 1
                reversal, tie = rank_pairs(swings, pivots)
                rank_differs += (reversal + tie) > 0
                values_differ += not same_values(swings, pivots, n)
    return {"games": games, "rank_differs": rank_differs, "values_differ": values_differ, "ranges": ranges}


def same_values(swings, pivots, n) -> bool:
    """Sind Banzhaf-Anteil und Shapley-Shubik-Anteil in allen Mitgliedern gleich (exakt)?"""
    total = sum(swings)
    return total > 0 and all(s * math.factorial(n) == p * total for s, p in zip(swings, pivots))


def two_system_series(gen, n, permille, seeds=SEEDS, per_seed=PER_SEED) -> dict:
    """Schnitt zweier Gewichtssysteme (beide Quoten müssen erreicht sein; die Gewichte kommen unabhängig aus demselben Erzeuger): in wie vielen Instanzen ordnen die beiden Indizes verschieden?"""
    games = rank_differs = reversal = tie_only = values_differ = 0
    for seed in seeds:
        for j in range(per_seed):
            w1, w2 = S.make_weights(gen, n, seed, j, 0), S.make_weights(gen, n, seed, j, 1)
            q1, q2 = G.quota_from_share(sum(w1), _p(permille)), G.quota_from_share(sum(w2), _p(permille))
            win = G.intersection_game([w1, w2], [q1, q2])
            if not win.any():
                continue
            swings, pivots = G.pivot_counts_from_win(win, n)
            games += 1
            rev, tie = rank_pairs(swings, pivots)
            rank_differs += (rev + tie) > 0
            reversal += rev > 0
            tie_only += (rev == 0 and tie > 0)
            values_differ += not same_values(swings, pivots, n)
    return {"gen": gen, "n": n, "permille": permille, "instances": games, "rank_differs": rank_differs, "reversal": reversal, "tie_only": tie_only, "values_differ": values_differ}


# ---------------------------------------------------------------- E5: Beirat (Sitzverteilung und Macht)

def lognormal_members(sigma: float, count: int, seed: int, j: int) -> list[int]:
    """`count` Mitgliederzahlen exp(6 + sigma * Z) (Z standardnormal, Box-Muller aus SplitMix64), mindestens 1."""
    rng = SplitMix64(((seed * 1_000_003 + j) * 1_009 + count) * 31 + int(round(sigma * 100)))
    out = []
    for _ in range(count):
        u1, u2 = 1.0 - rng.uniform(), rng.uniform()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        out.append(max(1, int(math.exp(6.0 + sigma * z))))
    return out


def seats_series(sigma, seats, associations=8, seeds=SEEDS, per_seed=75) -> list[dict]:
    """Je Verfahren: mittlere Abweichung (halbe L1) von Sitzanteil, Banzhaf- und Shapley-Shubik-Macht vom Mitgliederanteil, Zahl der Instanzen, in denen ein Verband die ganze Macht hat."""
    rows = []
    for method in ST.METHODS:
        d_seat = d_b = d_s = 0.0
        dictators = count = 0
        for seed in seeds:
            for j in range(per_seed):
                members = lognormal_members(sigma, associations, seed, j)
                allocation = ST.allocate(members, seats, method)
                b, s, _ = ST.seat_power(allocation)
                share = G.weight_shares(members)
                d_seat += G.half_l1([x / seats for x in allocation], share)
                d_b += G.half_l1(b, share)
                d_s += G.half_l1(s, share)
                dictators += any(abs(x - 1.0) < 1e-12 for x in s)
                count += 1
        rows.append({"method": method, "sigma": sigma, "seats": seats, "count": count, "d_seat": d_seat / count, "d_banzhaf": d_b / count,
                     "d_shapley_shubik": d_s / count, "dictators": dictators})
    return rows


# ---------------------------------------------------------------- E6: Laufzeit und Raster

def runtime_row(n: int, max_weight: int, seed: int = 5) -> dict:
    """Ein Lauf der Zählung (DP) bei n Mitgliedern mit Gewichten 1 bis max_weight; Zeit in Sekunden und Gewichtssumme (die Zeit hängt an Rechner und Auslastung)."""
    rng = SplitMix64(seed * 1_000_003 + n * 101 + max_weight)
    w = [1 + int(rng.uniform() * max_weight) for _ in range(n)]
    q = sum(w) // 2 + 1
    t0 = time.perf_counter()
    G.pivot_counts_dp(w, q)
    return {"n": n, "max_weight": max_weight, "total": sum(w), "seconds": time.perf_counter() - t0}


def raster_series(sums=(30, 100, 300, 1000, 10000), reference=100_000, n=8, count=200, seed=11) -> list[dict]:
    """Rundung reeller (lognormaler) Gewichte auf ganze Zahlen: wie weit weicht der Banzhaf-Anteil vom Anteil beim feinen Raster `reference` ab (Prozentpunkte)?"""
    rng = SplitMix64(seed)
    reals = []
    for _ in range(count):
        row = []
        for _ in range(n):
            u1, u2 = 1.0 - rng.uniform(), rng.uniform()
            row.append(math.exp(math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)))
        reals.append(row)

    def shares_at(real, total):
        scale = total / sum(real)
        w = [max(1, round(x * scale)) for x in real]
        sw, _ = G.pivot_counts_dp(w, sum(w) // 2 + 1)
        return G.banzhaf_shares(sw)

    ref = [shares_at(r, reference) for r in reals]
    rows = []
    for total in sums:
        worst = [max(abs(a - b) for a, b in zip(shares_at(r, total), rf)) * 100 for r, rf in zip(reals, ref)]
        rows.append({"total": total, "mean_worst_pp": sum(worst) / count, "over_1pp": sum(x > 1 for x in worst), "count": count})
    return rows


# ---------------------------------------------------------------- Expander: Owen-Wert, Zusammenschluss zweier Gruppen

_PATTERNS = {4: [[2, 2], [2, 1, 1], [3, 1]], 5: [[2, 2, 1], [3, 2], [2, 1, 1, 1], [3, 1, 1]], 6: [[2, 2, 2], [3, 2, 1], [2, 2, 1, 1], [3, 3], [2, 1, 1, 1, 1]]}


def _randint(rng, lo, hi):
    return lo + int(rng.uniform() * (hi - lo + 1))


def _shuffled(rng, items):
    items = list(items)
    for i in range(len(items) - 1, 0, -1):
        j = _randint(rng, 0, i)
        items[i], items[j] = items[j], items[i]
    return items


def _group_structure(rng, n):
    order = _shuffled(rng, range(n))
    sizes = _PATTERNS[n][_randint(rng, 0, len(_PATTERNS[n]) - 1)]
    unions, pos = [], 0
    for s in sizes:
        unions.append(order[pos : pos + s])
        pos += s
    return unions


def value_table(f, n) -> list[int]:
    return [f([i for i in range(n) if m >> i & 1]) for m in range(1 << n)]


def owen_merge_series(kind: str, n: int, count: int, seed: int = 7) -> dict:
    """Zusammenschluss zweier Gruppen beim Owen-Wert: Zahl der Fälle, in denen er nachteilig / unverändert / vorteilhaft ist (für die Summe der Anteile der beiden Gruppen).
    kind 'vote': gewichtete Abstimmung (Gewichte 1 bis 9, Quote > W/2, Gewinnspiel: vorteilhaft = Summe steigt); 'airport': Flughafenspiel (c(S) = größter Bedarf 1 bis 20,
    Kostenspiel: vorteilhaft = Summe der Kostenanteile sinkt)."""
    worse = same = better = 0
    biggest_loss = Fraction(0)
    for j in range(count):
        rng = SplitMix64(seed * 1_000_003 + j * 1_009 + n * 7 + (0 if kind == "vote" else 1))
        if kind == "vote":
            w = [_randint(rng, 1, 9) for _ in range(n)]
            q = sum(w) // 2 + 1
            v, gain_game = value_table(lambda S: int(sum(w[i] for i in S) >= q), n), True
        elif kind == "airport":
            c = [_randint(rng, 1, 20) for _ in range(n)]
            v, gain_game = value_table(lambda S: max((c[i] for i in S), default=0), n), False
        else:
            raise ValueError(kind)
        unions = _group_structure(rng, n)
        a = _randint(rng, 0, len(unions) - 1)
        b = _randint(rng, 0, len(unions) - 2)
        b = b + 1 if b >= a else b
        merged = [u for h, u in enumerate(unions) if h not in (a, b)] + [unions[a] + unions[b]]
        before = O.owen_formula(v, n, unions)
        after = O.owen_formula(v, n, merged)
        members = unions[a] + unions[b]
        delta = sum(after[i] for i in members) - sum(before[i] for i in members)
        if not gain_game:
            delta = -delta
        if delta < 0:
            worse += 1
            biggest_loss = max(biggest_loss, -delta)
        elif delta > 0:
            better += 1
        else:
            same += 1
    return {"kind": kind, "n": n, "count": count, "worse": worse, "same": same, "better": better, "biggest_loss": float(biggest_loss)}


# ---------------------------------------------------------------- Hilfen für die Tabs (eine Instanz)

def quote_scan(weights, percents) -> list[list[float]]:
    """Banzhaf-Anteile je Mitglied für jede Quote p (Prozent) der Liste: Ergebnis[k][i] ist der Anteil von Mitglied i bei percents[k]."""
    w = list(weights)
    out = []
    for pct in percents:
        swings, _ = G.pivot_counts_dp(w, G.quota_from_percent(sum(w), pct))
        out.append(G.banzhaf_shares(swings))
    return out


def best_quote_of(weights) -> dict | None:
    """Beste ganze Quote q in (W/2, W] für diese Instanz (kleinste Abweichung Banzhaf-Anteil gegen Stimmanteil; bei Gleichstand die kleinere): Rückgabe mit der Abweichung bei
    einfacher Mehrheit. Nur für n <= 20 und Gewichtssumme <= 2000 (sonst None)."""
    w = list(weights)
    total = sum(w)
    if len(w) > G.MAX_MULTI_PLAYERS or total > 2000:
        return None
    quotas = list(range(total // 2 + 1, total + 1))
    table = G.pivot_counts_dp_multi(w, quotas)
    best_q, best_d = None, None
    for q in quotas:
        d = distance_to_weights(table[q][0], w)
        if best_d is None or d < best_d:
            best_q, best_d = q, d
    return {"quote": best_q, "total": total, "distance": float(best_d), "distance_majority": float(distance_to_weights(table[quotas[0]][0], w)), "majority": quotas[0]}


def enumeration_row(n: int, max_weight: int, seed: int = 5) -> dict:
    """Ein Lauf der Aufzählung über die Gewinntabelle (numpy) bei n Mitgliedern mit Gewichten 1 bis max_weight; Zeit in Sekunden (n <= 20)."""
    rng = SplitMix64(seed * 1_000_003 + n * 101 + max_weight)
    w = [1 + int(rng.uniform() * max_weight) for _ in range(n)]
    q = sum(w) // 2 + 1
    t0 = time.perf_counter()
    G.pivot_counts_subsets(w, q)
    return {"n": n, "max_weight": max_weight, "total": sum(w), "seconds": time.perf_counter() - t0}


# ---------------------------------------------------------------- Harsanyi: erklärt die Dividendenmasse die Abweichung der Indizes?

def harsanyi_correlation(gen, n, permille, count=50, seed=101) -> dict:
    """Pearson-Korrelation (über `count` Instanzen eines Zufalls-Seeds) zwischen der Dividendenmasse in Koalitionen ab Größe 3 (Summe der Beträge) und der Abweichung
    Banzhaf gegen Shapley-Shubik (halbe L1-Distanz). Außerdem der Anteil der Dividenden ungleich null und der negativen unter ihnen."""
    import numpy as np

    import mdx_harsanyi as H

    sizes = np.array([bin(m).count("1") for m in range(1 << n)])
    mass, spread = [], []
    nonzero = negative = 0
    for j in range(count):
        w = S.make_weights(gen, n, seed, j)
        q = G.quota_from_share(sum(w), _p(permille))
        d = H.dividends(G.win_vector(w, q), n)
        mass.append(float(np.abs(d[sizes >= 3]).sum()))
        swings, pivots = G.pivot_counts_dp(list(w), q)
        spread.append(float(distance_between(swings, pivots)))
        nonzero += int((d != 0).sum())
        negative += int((d < 0).sum())
    return {"gen": gen, "n": n, "permille": permille, "count": count, "pearson": float(np.corrcoef(mass, spread)[0, 1]), "nonzero_share": nonzero / (count * (1 << n)),
            "negative_share": negative / nonzero}
