"""Brücke zur Sitzverteilung: Mitglieder je Verband -> Sitze (Hamilton, Jefferson, Webster) -> Macht der Sitze bei Mehrheitsbeschluss.

Eigener Code, kein Import der Nachbar-Demo. Alle Rechnungen mit Ganzzahlen und Brüchen; Gleichstand: der kleinere Index zuerst."""

from fractions import Fraction

import mdx_game as G

METHODS = ("Hamilton", "Jefferson", "Webster")


def hamilton(members, seats: int) -> list[int]:
    """Abgerundete Quote, die übrigen Sitze an die größten Reste (Gleichstand: kleinerer Index)."""
    total = sum(members)
    base = [m * seats // total for m in members]
    rest = seats - sum(base)
    order = sorted(range(len(members)), key=lambda i: (-(members[i] * seats % total), i))
    for i in order[:rest]:
        base[i] += 1
    return base


def divisor_method(members, seats: int, rule: str) -> list[int]:
    """Sitz für Sitz an den größten Rang: Jefferson Mitglieder / (Sitze + 1), Webster Mitglieder / (Sitze + 1/2)."""
    if rule not in ("Jefferson", "Webster"):
        raise ValueError(f"unbekannte Divisormethode {rule!r}")
    given = [0] * len(members)
    for _ in range(seats):
        def rank(i):
            return Fraction(members[i]) / (given[i] + (1 if rule == "Jefferson" else Fraction(1, 2)))
        best = max(range(len(members)), key=lambda i: (rank(i), -i))
        given[best] += 1
    return given


def allocate(members, seats: int, method: str) -> list[int]:
    if method == "Hamilton":
        return hamilton(members, seats)
    return divisor_method(members, seats, method)


def seat_power(seats) -> tuple[list[float], list[float], int]:
    """(Banzhaf-Anteile, Shapley-Shubik-Anteile, Quote) bei Beschluss mit mehr als der Hälfte der Sitze; Verbände ohne Sitz haben Macht 0."""
    q = sum(seats) // 2 + 1
    swings, pivots = G.pivot_counts_dp(list(seats), q)
    return G.banzhaf_shares(swings), G.shapley_shubik_shares(pivots, len(seats)), q


def staircase(members, largest: int, seats: int, lo: int, hi: int):
    """Macht des Verbands `largest` gegen seine Sitzzahl s (lo bis hi); die übrigen seats - s Sitze gehen per Hamilton an die anderen Verbände.
    Zeilen (s, Sitzanteil, Banzhaf-Anteil, Shapley-Shubik-Anteil)."""
    others = [m for i, m in enumerate(members) if i != largest]
    rows = []
    for s in range(lo, hi + 1):
        distribution = [s] + hamilton(others, seats - s)
        b, ss, _ = seat_power(distribution)
        rows.append((s, s / seats, b[0], ss[0]))
    return rows
