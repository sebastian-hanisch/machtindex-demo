"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Handrechnungen (Gewichte, Quote -> Schwingzahlen Banzhaf; Reihenfolgenzähler Shapley-Shubik von n!):
  [4, 3, 2, 1], 6   Schwingzahlen 5 / 3 / 3 / 1 (Summe 12); Reihenfolgen 10 / 6 / 6 / 2 von 24
  [2, 1, 1], 3      Schwingzahlen 3 / 1 / 1 (Summe 5); Reihenfolgen 4 / 1 / 1 von 6
  [1, 1, 1], 2      Schwingzahlen 2 / 2 / 2; Reihenfolgen 2 / 2 / 2 von 6
  [3, 3, 1], 5      Schwingzahlen 2 / 2 / 0 (Nullspieler); Reihenfolgen 3 / 3 / 0
  [5, 1, 1, 1], 5   Schwingzahlen 8 / 0 / 0 / 0 (Diktator); Reihenfolgen 24 / 0 / 0 / 0
  [1, 1, 1, 2, 4], 7  Schwingzahlen 2 / 2 / 2 / 6 / 8 (Summe 20); nach der Übertragung einer Stimme von 4 an 2 ([1, 1, 1, 3, 3]): 1 / 1 / 1 / 7 / 7 (Summe 17)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HAND = {
    ((4, 3, 2, 1), 6): ([5, 3, 3, 1], [10, 6, 6, 2]),
    ((2, 1, 1), 3): ([3, 1, 1], [4, 1, 1]),
    ((1, 1, 1), 2): ([2, 2, 2], [2, 2, 2]),
    ((3, 3, 1), 5): ([2, 2, 0], [3, 3, 0]),
    ((5, 1, 1, 1), 5): ([8, 0, 0, 0], [24, 0, 0, 0]),
    ((1, 1, 1, 2, 4), 7): ([2, 2, 2, 6, 8], [10, 10, 10, 30, 60]),
    ((1, 1, 1, 3, 3), 7): ([1, 1, 1, 7, 7], None),
}


@pytest.fixture
def hand():
    return HAND
