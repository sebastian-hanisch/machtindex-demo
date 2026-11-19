"""Kern: Machtindizes (Banzhaf, Shapley-Shubik) gewichteter Abstimmungsspiele, nur numpy und Standardbibliothek.

Ein Beschluss fällt, wenn die Gewichtssumme der Zustimmenden mindestens die Quote q erreicht. Ein Mitglied ist in einer Koalition S ohne es
**Schwingspieler**, wenn S verliert und S plus das Mitglied gewinnt. Alle Zählungen sind ganzzahlig und exakt; geteilt wird erst bei der Anzeige.

Vier Rechenwege (DEMO-PLAYBOOK §1b, je Weg eine Funktion), die in den Tests gegeneinander laufen:
  `swing_counts_enum`      Aufzählung aller Koalitionen in reinem Python (Banzhaf-Schwingzahlen)
  `pivot_counts_perm`      Aufzählung aller Reihenfolgen (Shapley-Shubik), nur für n <= 8
  `pivot_counts_subsets`   Aufzählung aller Koalitionen mit numpy über die Gewinntabelle (beide Indizes; für beliebige einfache Spiele)
  `pivot_counts_dp`        Zählen statt Aufzählen: dynamische Programmierung über (Größe, Gewichtssumme), der Weg der App für große n
"""

import itertools
import math
from fractions import Fraction

import numpy as np

MAX_DP_PLAYERS = 62          # größere Zählfelder passen nicht mehr in int64 (2^62 Teilmengen)
MAX_MULTI_PLAYERS = 20       # n! passt dann noch in int64: Voraussetzung von `pivot_counts_dp_multi`
MAX_TABLE_PLAYERS = 20       # Gewinntabellen mit 2^n Einträgen


def quota_from_share(total: int, p: Fraction) -> int:
    """Ganze Quote q für „mehr als der Anteil p der Gesamtgewichte“: q = floor(p * W) + 1; bei p = 1 (Einstimmigkeit) q = W."""
    if not 0 < p <= 1:
        raise ValueError(f"p = {p} liegt nicht in (0, 1]")
    if p >= 1:
        return total
    return (p.numerator * total) // p.denominator + 1


def quota_from_percent(total: int, percent: int) -> int:
    """Wie `quota_from_share` mit p = percent / 100: 50 heißt einfache Mehrheit, 100 Einstimmigkeit."""
    return quota_from_share(total, Fraction(percent, 100))


# ---------------------------------------------------------------- Rechenweg 1: Aufzählung, reines Python

def swing_counts_enum(w, q) -> list[int]:
    """Banzhaf-Schwingzahlen: für jedes Mitglied die Zahl der Koalitionen S (mit ihm), die gewinnen und ohne es verlieren."""
    n = len(w)
    swings = [0] * n
    for mask in range(1 << n):
        s = sum(w[i] for i in range(n) if mask >> i & 1)
        if s >= q:
            for i in range(n):
                if mask >> i & 1 and s - w[i] < q:
                    swings[i] += 1
    return swings


# ---------------------------------------------------------------- Rechenweg 2: Aufzählung aller Reihenfolgen

def pivot_counts_perm(w, q) -> list[int]:
    """Shapley-Shubik: für jedes Mitglied die Zahl der Reihenfolgen, in denen es die Quote als erstes erreicht (n <= 8: n! Reihenfolgen)."""
    n = len(w)
    if n > 8:
        raise ValueError("Aufzählung aller Reihenfolgen nur bis n = 8")
    counts = [0] * n
    for order in itertools.permutations(range(n)):
        total = 0
        for i in order:
            total += w[i]
            if total >= q:
                counts[i] += 1
                break
    return counts


# ---------------------------------------------------------------- Rechenweg 3: Aufzählung über die Gewinntabelle (numpy)

def win_vector(w, q) -> np.ndarray:
    """Gewinntabelle des Gewichtsspiels: Eintrag m (Bitmaske der Koalition) ist True, wenn die Gewichtssumme mindestens q ist."""
    n = len(w)
    if n > MAX_TABLE_PLAYERS:
        raise ValueError(f"Gewinntabelle nur bis n = {MAX_TABLE_PLAYERS}")
    masks = np.arange(1 << n)
    sums = np.zeros(1 << n, dtype=np.int64)
    for i, wi in enumerate(w):
        sums += ((masks >> i) & 1) * int(wi)
    return sums >= q


def intersection_game(weight_systems, quotas) -> np.ndarray:
    """Gewinntabelle des Schnitts mehrerer Gewichtssysteme: eine Koalition gewinnt, wenn sie in JEDEM System ihre Quote erreicht."""
    win = None
    for w, q in zip(weight_systems, quotas):
        v = win_vector(w, q)
        win = v if win is None else (win & v)
    return win


def pivot_counts_from_win(win, n) -> tuple[list[int], list[int]]:
    """Schwingzahlen (Banzhaf) und Reihenfolgenzähler (Shapley-Shubik) eines monotonen einfachen Spiels aus seiner Gewinntabelle (2^n Einträge)."""
    masks = np.arange(1 << n)
    size = np.zeros(1 << n, dtype=np.int64)
    for i in range(n):
        size += (masks >> i) & 1
    fak = [math.factorial(k) for k in range(n + 1)]
    swings, pivots = [], []
    for i in range(n):
        bit = 1 << i
        with_i = masks[(masks & bit) != 0]
        pivotal = win[with_i] & ~win[with_i ^ bit]
        swings.append(int(pivotal.sum()))
        per_size = np.bincount(size[with_i[pivotal]] - 1, minlength=n)
        pivots.append(sum(int(per_size[s]) * fak[s] * fak[n - 1 - s] for s in range(n)))
    return swings, pivots


def pivot_counts_subsets(w, q) -> tuple[list[int], list[int]]:
    """Beide Indizes eines Gewichtsspiels über die Gewinntabelle (n <= 20)."""
    return pivot_counts_from_win(win_vector(w, q), len(w))


# ---------------------------------------------------------------- Rechenweg 4: Zählen per dynamischer Programmierung

def subset_count_table(w) -> np.ndarray:
    """C[s][k] = Zahl der Teilmengen der Größe s mit Gewichtssumme k (alle Mitglieder; int64, n <= 62)."""
    n, total = len(w), int(sum(w))
    if n > MAX_DP_PLAYERS:
        raise ValueError(f"Zählfeld nur bis n = {MAX_DP_PLAYERS}")
    table = np.zeros((n + 1, total + 1), dtype=np.int64)
    table[0, 0] = 1
    for j, wj in enumerate(w):
        wj = int(wj)
        for s in range(j + 1, 0, -1):
            table[s, wj:] += table[s - 1, : total + 1 - wj]
    return table


def _without_member(table, s, previous, wi, total):
    """Rücknahme eines Mitglieds mit Gewicht wi: D[s][k] = C[s][k] - D[s-1][k - wi] (Teilmengen der Größe s ohne dieses Mitglied)."""
    nxt = table[s].copy()
    nxt[wi:] -= previous[: total + 1 - wi]
    return nxt


def pivot_counts_dp(w, q) -> tuple[list[int], list[int]]:
    """Schwingzahlen und Reihenfolgenzähler ohne Aufzählung: Aufwand etwa n^2 * W mit W = Gewichtssumme (n <= 62, ganzzahlig, exakt).

    Mitglied i ist Schwingspieler in einer Teilmenge der übrigen mit Summe k genau dann, wenn q - w_i <= k <= q - 1; die Zahl solcher Teilmengen
    je Größe s kommt aus der Rücknahme von i aus dem Zählfeld. Der Zähler der Reihenfolgen gewichtet Größe s mit s! (n-1-s)!."""
    n, total = len(w), int(sum(w))
    table = subset_count_table(w)
    fak = [math.factorial(k) for k in range(n + 1)]
    cache: dict[int, tuple[int, int]] = {}
    swings, pivots = [], []
    for wi in w:
        wi = int(wi)
        if wi not in cache:
            lo, hi = max(0, q - wi), min(total, q - 1)
            d = np.zeros(total + 1, dtype=np.int64)
            d[0] = 1
            b = p = 0
            for s in range(n):
                if s > 0:
                    d = _without_member(table, s, d, wi, total)
                piv = int(d[lo : hi + 1].sum()) if lo <= hi else 0
                b += piv
                p += piv * fak[s] * fak[n - 1 - s]
            cache[wi] = (b, p)
        swings.append(cache[wi][0])
        pivots.append(cache[wi][1])
    return swings, pivots


def pivot_counts_dp_multi(w, quotas) -> dict[int, tuple[list[int], list[int]]]:
    """Wie `pivot_counts_dp` für viele Quoten auf einmal (die Rücknahme hängt nicht von der Quote ab); nur für n <= 20 (n! passt in int64)."""
    n, total = len(w), int(sum(w))
    if n > MAX_MULTI_PLAYERS:
        raise ValueError(f"mehrere Quoten auf einmal nur bis n = {MAX_MULTI_PLAYERS}")
    table = subset_count_table(w)
    fak = [math.factorial(k) for k in range(n + 1)]
    cache: dict[int, np.ndarray] = {}
    result = {q: ([], []) for q in quotas}
    for wi in w:
        wi = int(wi)
        if wi not in cache:
            by_sum = np.zeros(total + 1, dtype=np.int64)
            weighted = np.zeros(total + 1, dtype=np.int64)
            d = np.zeros(total + 1, dtype=np.int64)
            d[0] = 1
            for s in range(n):
                if s > 0:
                    d = _without_member(table, s, d, wi, total)
                by_sum += d
                weighted += d * (fak[s] * fak[n - 1 - s])
            cache[wi] = np.stack([np.concatenate(([0], np.cumsum(by_sum))), np.concatenate(([0], np.cumsum(weighted)))])
        prefix = cache[wi]
        for q in quotas:
            lo, hi = max(0, q - wi), min(total, q - 1)
            b, p = (0, 0) if lo > hi else (int(prefix[0][hi + 1] - prefix[0][lo]), int(prefix[1][hi + 1] - prefix[1][lo]))
            result[q][0].append(b)
            result[q][1].append(p)
    return result


# ---------------------------------------------------------------- Anteile und Eigenschaften

def banzhaf_shares(swings) -> list[float]:
    """Normierter Banzhaf-Index: Anteil an der Summe aller Schwingzahlen (Summe 1; ohne Schwingzahlen lauter Nullen)."""
    total = sum(swings)
    return [s / total for s in swings] if total else [0.0] * len(swings)


def shapley_shubik_shares(pivots, n) -> list[float]:
    """Shapley-Shubik-Index: Anteil der Reihenfolgen, in denen das Mitglied die Quote als erstes erreicht (Summe 1)."""
    f = math.factorial(n)
    return [p / f for p in pivots]


def weight_shares(w) -> list[float]:
    total = sum(w)
    return [x / total for x in w]


def veto_players(w, q) -> list[int]:
    """Mitglieder, ohne die keine Koalition die Quote erreicht (die Gewichtssumme der übrigen liegt unter q)."""
    total = sum(w)
    return [i for i, wi in enumerate(w) if total - wi < q]


def dictator(swings) -> int | None:
    """Das Mitglied, das allein alle Schwingzahlen hat (es entscheidet jeden Beschluss), sonst None."""
    total = sum(swings)
    if total == 0:
        return None
    holders = [i for i, s in enumerate(swings) if s == total]
    return holders[0] if len(holders) == 1 else None


def null_players(swings) -> list[int]:
    return [i for i, s in enumerate(swings) if s == 0]


def half_l1(a, b) -> float:
    """Abstand zweier Anteilsvektoren: die halbe Summe der Beträge (der Anteil, der umverteilt werden müsste; 0 bis 1)."""
    return sum(abs(x - y) for x, y in zip(a, b)) / 2
