"""Owen-Wert: Shapley-Wert mit Gruppen (Vorverhandlung innerhalb von Gruppen), nur als Expander-Messung (Zusammenschluss zweier Gruppen).

Zwei Rechenwege, die gegeneinander laufen: die geschlossene Formel (Owen 1977, aus dem Gedächtnis aufgeschrieben und hier gegen die Definition geprüft)
und die Definition als Mittel über alle Reihenfolgen, in denen jede Gruppe am Stück steht. Exakte Brüche."""

import itertools
import math
from fractions import Fraction


def owen_formula(v, n, unions) -> list[Fraction]:
    """Owen-Wert aus der geschlossenen Formel. `v[m]` ist der Wert der Koalition mit Bitmaske m, `unions` eine Liste von Gruppen (Listen von Mitgliedern)."""
    m = len(unions)
    masks = [sum(1 << i for i in u) for u in unions]
    f = math.factorial
    phi = [Fraction(0)] * n
    for k, group in enumerate(unions):
        size = len(group)
        others = [h for h in range(m) if h != k]
        for r in range(m):
            for chosen in itertools.combinations(others, r):
                rest_mask = 0
                for h in chosen:
                    rest_mask |= masks[h]
                weight_groups = Fraction(f(r) * f(m - r - 1), f(m))
                for i in group:
                    mates = [j for j in group if j != i]
                    for t in range(size):
                        for sub in itertools.combinations(mates, t):
                            sub_mask = sum(1 << j for j in sub)
                            weight_inner = Fraction(f(t) * f(size - t - 1), f(size))
                            base = rest_mask | sub_mask
                            phi[i] += weight_groups * weight_inner * (v[base | (1 << i)] - v[base])
    return phi


def owen_by_orders(v, n, unions) -> list[Fraction]:
    """Owen-Wert nach der Definition: Mittel der Beiträge über alle Reihenfolgen, in denen jede Gruppe am Stück steht."""
    phi = [Fraction(0)] * n
    count = 0
    for group_order in itertools.permutations(range(len(unions))):
        for inner in itertools.product(*[list(itertools.permutations(u)) for u in unions]):
            current = 0
            for g in group_order:
                for i in inner[g]:
                    phi[i] += v[current | (1 << i)] - v[current]
                    current |= 1 << i
            count += 1
    return [p / count for p in phi]


def shapley_value(v, n) -> list[Fraction]:
    """Shapley-Wert = Owen-Wert mit lauter Einzelgruppen."""
    return owen_formula(v, n, [[i] for i in range(n)])
