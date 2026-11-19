"""Paradoxa der Macht: Stimme abgeben, zwei Mitglieder zusammenlegen, ein Mitglied aufspalten, ein neues Mitglied aufnehmen.

Jede Regel ist eine eigene Funktion (DEMO-PLAYBOOK §1b). Die Anteile sind exakte Brüche, damit „gewinnt Macht“ nie an einer Toleranz hängt. Die Quote bleibt bei
Übertragung, Zusammenlegung und Aufspaltung absolut fest (die Gewichtssumme ändert sich nicht); beim neuen Mitglied wird sie mit demselben Anteil p neu bestimmt."""

import itertools
import math
from fractions import Fraction

import mdx_game as G


def powers(w, q) -> tuple[list[Fraction], list[Fraction]]:
    """(Banzhaf-Anteile, Shapley-Shubik-Anteile) als exakte Brüche, über die dynamische Programmierung."""
    swings, pivots = G.pivot_counts_dp(w, q)
    total = sum(swings)
    n = len(w)
    banzhaf = [Fraction(s, total) if total else Fraction(0) for s in swings]
    shapley_shubik = [Fraction(p, math.factorial(n)) for p in pivots]
    return banzhaf, shapley_shubik


def sign(new, old) -> int:
    """-1, 0 oder +1: ist `new` kleiner, gleich oder größer als `old` (exakter Vergleich)."""
    return (new > old) - (new < old)


def transfer(w, giver: int, receiver: int, amount: int = 1) -> list[int]:
    """Das Mitglied `giver` gibt `amount` Stimmen an `receiver` ab (Gewichtssumme und Quote bleiben gleich)."""
    if giver == receiver or amount < 1 or w[giver] < amount:
        raise ValueError("Übertragung nicht möglich")
    out = list(w)
    out[giver] -= amount
    out[receiver] += amount
    return out


def merge(w, i: int, k: int) -> list[int]:
    """Zwei Mitglieder werden ein Block mit der Summe der Gewichte; der Block steht zuletzt."""
    if i == k:
        raise ValueError("zwei verschiedene Mitglieder nötig")
    return [x for t, x in enumerate(w) if t not in (i, k)] + [w[i] + w[k]]


def split(w, i: int) -> list[int]:
    """Ein Mitglied teilt sich in zwei (Gewicht halbiert, die größere Hälfte zuerst); die beiden stehen zuletzt. Gewicht mindestens 2."""
    if w[i] < 2:
        raise ValueError("Gewicht 1 lässt sich nicht teilen")
    return [x for t, x in enumerate(w) if t != i] + [w[i] - w[i] // 2, w[i] // 2]


def add_member(w, weight: int) -> list[int]:
    return list(w) + [weight]


# ---------------------------------------------------------------- Auswertung je Regel

def donor_outcome(w, q, giver, receiver, base=None):
    """Richtung der Macht des Gebers nach der Übertragung einer Stimme: (Banzhaf, Shapley-Shubik); +1 heißt, der Geber gewinnt Machtanteil. `base` = powers(w, q), falls schon gerechnet."""
    b0, s0 = base or powers(w, q)
    b1, s1 = powers(transfer(w, giver, receiver), q)
    return sign(b1[giver], b0[giver]), sign(s1[giver], s0[giver])


def merge_outcome(w, q, i, k, base=None):
    """Richtung der Macht des Blocks gegenüber der Summe der beiden Einzelanteile: (Banzhaf, Shapley-Shubik); +1 heißt Block hat mehr."""
    b0, s0 = base or powers(w, q)
    b1, s1 = powers(merge(w, i, k), q)
    return sign(b1[-1], b0[i] + b0[k]), sign(s1[-1], s0[i] + s0[k])


def split_outcome(w, q, i, base=None):
    """Richtung der Summe der beiden Hälften gegenüber der Macht vor der Aufspaltung: (Banzhaf, Shapley-Shubik); +1 heißt beide zusammen haben mehr."""
    b0, s0 = base or powers(w, q)
    b1, s1 = powers(split(w, i), q)
    return sign(b1[-1] + b1[-2], b0[i]), sign(s1[-1] + s1[-2], s0[i])


def add_member_outcome(w, weight, p: Fraction):
    """Gewinnt ein altes Mitglied Machtanteil, wenn ein neues kommt (Quote mit demselben Anteil p neu bestimmt)? (Banzhaf, Shapley-Shubik) als True/False."""
    old, new = list(w), add_member(w, weight)
    b0, s0 = powers(old, G.quota_from_share(sum(old), p))
    b1, s1 = powers(new, G.quota_from_share(sum(new), p))
    n = len(old)
    return any(b1[i] > b0[i] for i in range(n)), any(s1[i] > s0[i] for i in range(n))


def exhaustive_donor_count(n: int, wmax: int):
    """Spenderparadox vollständig aufgezählt: alle nichtfallenden Gewichtsvektoren mit n Mitgliedern und Gewichten 1 bis wmax, alle Quoten über W/2, alle Einzelübertragungen
    einer Stimme. Rückgabe (Spiele, Übertragungen, Fälle Banzhaf, Fälle Shapley-Shubik, kleinstes Beispiel Banzhaf als (Gewichte, Quote, Geber, Empfänger))."""
    games = transfers = cases_b = cases_s = 0
    example = None
    for w in itertools.combinations_with_replacement(range(1, wmax + 1), n):
        total = sum(w)
        for q in range(total // 2 + 1, total + 1):
            games += 1
            b0, s0 = powers(w, q)
            for giver in range(n):
                if w[giver] < 2:
                    continue
                for receiver in range(n):
                    if receiver == giver:
                        continue
                    b1, s1 = powers(transfer(w, giver, receiver), q)
                    transfers += 1
                    if b1[giver] > b0[giver]:
                        cases_b += 1
                        if example is None or (total, w, q) < (sum(example[0]), example[0], example[1]):
                            example = (w, q, giver, receiver)
                    if s1[giver] > s0[giver]:
                        cases_s += 1
    return games, transfers, cases_b, cases_s, example
