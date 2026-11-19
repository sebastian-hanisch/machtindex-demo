"""Harsanyi-Dividenden: die Zerlegung eines einfachen Spiels in Einstimmigkeitsspiele (nur als Erklärung, kein eigener Befund).

Δ(T) = Summe über alle Teilmengen S von T von (-1)^(|T|-|S|) v(S). Der Shapley-Shubik-Wert ist die Summe von Δ(T)/|T| über alle T mit dem Mitglied, der
unnormierte Banzhaf-Wert (Schwingzahl durch 2^(n-1)) die Summe von Δ(T)/2^(|T|-1). Beides wird hier mit exakten Brüchen gerechnet."""

from fractions import Fraction

import numpy as np


def dividends(win, n) -> np.ndarray:
    """Dividenden aller Koalitionen (Bitmasken) durch die schnelle Möbius-Transformation (n * 2^n Schritte); Eintrag 0 (leere Menge) ist 0."""
    d = np.asarray(win, dtype=np.int64).copy()
    idx = np.arange(1 << n)
    for i in range(n):
        bit = 1 << i
        sel = (idx & bit) != 0
        d[sel] -= d[idx[sel] ^ bit]
    d[0] = 0
    return d


def indices_from_dividends(d, n) -> tuple[list[Fraction], list[Fraction]]:
    """(Shapley-Shubik-Werte, unnormierte Banzhaf-Werte = Schwingzahl / 2^(n-1)) als exakte Brüche aus den Dividenden."""
    shapley = [Fraction(0)] * n
    banzhaf = [Fraction(0)] * n
    for mask in range(1, 1 << n):
        value = int(d[mask])
        if value == 0:
            continue
        size = bin(mask).count("1")
        for i in range(n):
            if mask >> i & 1:
                shapley[i] += Fraction(value, size)
                banzhaf[i] += Fraction(value, 2 ** (size - 1))
    return shapley, banzhaf


def nonzero_dividends(d) -> list[tuple[int, int]]:
    """[(Bitmaske, Dividende)] aller Dividenden ungleich null, nach Größe der Koalition und dann Maske sortiert."""
    items = [(m, int(v)) for m, v in enumerate(d) if v != 0]
    return sorted(items, key=lambda t: (bin(t[0]).count("1"), t[0]))
