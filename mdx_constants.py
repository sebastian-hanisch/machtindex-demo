"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX = 2, 60                      # Zahl der Mitglieder
WEIGHT_MIN = 1                            # kleinstes Gewicht (Lkw im Fuhrpark)
WEIGHT_SUM_MAX = 100_000                  # größte Gewichtssumme: so groß ist das Zählfeld der DP (60 x 100.001 int64 = 48 MB)
TEXT_MAX_CHARS = 2_000
P_MIN, P_MAX, P_STEP, DEFAULT_P = 50.0, 100.0, 0.1, 50.0      # Beschlussquote p in Prozent; 100 heißt Einstimmigkeit
DEFAULT_WEIGHTS = "40, 25, 10, 8, 5, 3, 2"
DEFAULT_GENERATOR, DEFAULT_N, DEFAULT_SEED, SEED_MAX = "uniform", 12, 35, 999_999

GENERATOR_LABELS = {
    "equal": "fast gleich (8 bis 12)",
    "uniform": "gleichverteilt (1 bis 20)",
    "stepped": "gestuft (3, 10 oder 30)",
    "pareto12": "Pareto mit Tail (α = 1,2)",
    "pareto25": "Pareto (α = 2,5)",
    "lognormal": "lognormal (μ = 2, σ = 1)",
}

# Messreihen: vier feste Zufalls-Seeds mit je 50 Instanzen je Zelle
EXPERIMENT_GENERATORS = ("equal", "uniform", "stepped", "pareto12", "pareto25", "lognormal")
PARADOX_GENERATORS = ("uniform", "stepped", "pareto25", "lognormal")
PERMILLES = (500, 600, 667, 750)          # p = 1/2, 3/5, 2/3, 3/4 (Quote = mehr als dieser Anteil)

# Spenderparadox vollständig aufgezählt (vorgerechnet; tests/test_claims.py rechnet jede Zeile neu):
# (n, größtes Gewicht, Spiele, Einzelübertragungen, Fälle Banzhaf, Fälle Shapley-Shubik)
DONOR_ENUMERATION = ((3, 8, 840, 4600, 0, 0), (4, 8, 3050, 33180, 0, 0), (5, 8, 9108, 164380, 100, 0), (6, 5, 1940, 48880, 39, 0))

# Zweites Gewichtssystem (Tab „Zwei Gewichtssysteme“): kleinstes gefundenes Beispiel mit echter Rang-Umkehr, n = 7
SYSTEM_FLEET, SYSTEM_FLEET_QUOTA = "4, 5, 1, 1, 2, 4, 1", 10
SYSTEM_TURNOVER, SYSTEM_TURNOVER_QUOTA = "3, 1, 4, 4, 4, 3, 5", 13

# Beirat (Brücke zur Sitzverteilung): Standardinstanz der sitzverteilung-demo (acht Verbände, 40 Sitze)
BOARD_MEMBERS = "521, 840, 5279, 1933, 194, 995, 536, 1160"
BOARD_SEATS_DEFAULT = 40
BOARD_SEATS_MIN, BOARD_SEATS_MAX = 8, 100
BOARD_HAMILTON_SEATS = "2, 3, 18, 7, 1, 3, 2, 4"    # Hamilton-Verteilung der Standardinstanz (Test: gleich hamilton(BOARD_MEMBERS, 40))

COLOR_WEIGHT = "#9aa5b1"
COLOR_BANZHAF = "#2F6B65"
COLOR_SHAPLEY = "#c0782b"
COLOR_LINE = "#4c78a8"

PRESETS = {
    "Fuhrpark 7, einfache Mehrheit (Voreinstellung)": {"weights": DEFAULT_WEIGHTS, "p": 50.0},
    "Fuhrpark 7, mehr als zwei Drittel": {"weights": DEFAULT_WEIGHTS, "p": 67.0},
    "Ein Großer, fünf Kleine": {"weights": "3, 1, 1, 1, 1, 1", "p": 50.0},
    "Banzhaf ≠ Shapley–Shubik": {"weights": "2, 1, 1", "p": 50.0},
    "Nullspieler": {"weights": "3, 3, 1", "p": 60.0},
    "Diktator": {"weights": "5, 1, 1, 1", "p": 50.0},
    "Spenderparadox": {"weights": "1, 1, 1, 2, 4", "p": 67.0},
    "Einstimmigkeit": {"weights": "3, 3, 3, 1", "p": 100.0},
    "EU-Rat Nizza (nur Stimmbedingung)": {
        "weights": "29, 29, 29, 29, 27, 27, 14, 13, 12, 12, 12, 12, 12, 10, 10, 10, 7, 7, 7, 7, 7, 4, 4, 4, 4, 4, 3", "p": 73.7},
    "Beirat: 40 Sitze nach Hamilton": {"weights": BOARD_HAMILTON_SEATS, "p": 50.0},
}
PRESET_HELP = {
    "Fuhrpark 7, einfache Mehrheit (Voreinstellung)": "Sieben Mitglieder mit 40, 25, 10, 8, 5, 3 und 2 Lkw; beschlossen ist, was mehr als die Hälfte der 93 Stimmen hat (Quote 47). Das Mitglied mit 25 Lkw hat nicht mehr Macht als das mit 10.",
    "Fuhrpark 7, mehr als zwei Drittel": "Dieselben sieben Mitglieder, aber es braucht mehr als 2/3 der Stimmen (Quote 63). Mit der höheren Quote ändert sich die Machtverteilung.",
    "Ein Großer, fünf Kleine": "Ein Mitglied mit 3 Stimmen, fünf mit je 1; Quote 5 von 8. Der Große hat 37,5 % der Stimmen und 50 % der Macht.",
    "Banzhaf ≠ Shapley–Shubik": "Gewichte 2, 1, 1 und Quote 3: der kleinste Fall, in dem die beiden Indizes verschiedene Werte geben (60 % gegen 66,7 % für das große Mitglied).",
    "Nullspieler": "Gewichte 3, 3, 1 und Quote 5: das Mitglied mit 1 Stimme wird nie gebraucht und hat Macht 0, obwohl es Stimmen hat.",
    "Diktator": "Gewichte 5, 1, 1, 1 und Quote 5: das große Mitglied entscheidet allein, die anderen haben Macht 0.",
    "Spenderparadox": "Gewichte 1, 1, 1, 2, 4 und Quote 7. Gibt das Mitglied mit 4 Stimmen eine Stimme an das mit 2 ab, wächst sein Banzhaf-Anteil (Tab Paradoxa).",
    "Einstimmigkeit": "Gewichte 3, 3, 3, 1 und Quote 10 von 10: alle haben ein Veto und damit gleich viel Macht, auch das Mitglied mit nur 1 Stimme.",
    "EU-Rat Nizza (nur Stimmbedingung)": "27 Gewichte des Vertrags von Nizza ab 2007 (Summe 345) mit der Schwelle 255. Modelliert ist nur diese Stimmbedingung, nicht die weiteren Bedingungen der Beschlussregel; die Gewichte stimmen mit einer Sekundärquelle (Wikipedia) überein.",
    "Beirat: 40 Sitze nach Hamilton": "Acht Verbände, 40 Sitze nach Hamilton verteilt (Standardinstanz der Sitzverteilungs-Demo); beschlossen wird mit mehr als der Hälfte der Sitze. Der Tab Beirat vergleicht drei Verfahren.",
}
