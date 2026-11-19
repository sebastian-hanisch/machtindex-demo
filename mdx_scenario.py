"""Szenario: Gewichtsvektoren der Genossenschaft (Handeingabe oder Erzeuger mit SplitMix64) und ihre Prüfung.

Der Zufall kommt nur aus `mdx_rng.SplitMix64` (wörtliche Kopie aus ab-test-demo). Eine Instanz ist durch (Erzeuger, n, Zufalls-Seed, Nummer j, Strom `which`) festgelegt;
gleiche Eingabe, gleiche Gewichte, auf jeder Plattform (bis auf die Rundung von exp, log, cos und Potenzen bei Pareto und Lognormal, siehe README)."""

import math
import re

import mdx_constants as C
from mdx_rng import SplitMix64


def _gen_equal(rng, n):
    return [8 + int(rng.uniform() * 5) for _ in range(n)]


def _gen_uniform(rng, n):
    return [1 + int(rng.uniform() * 20) for _ in range(n)]


def _gen_stepped(rng, n):
    return [(3, 10, 30)[int(rng.uniform() * 3)] for _ in range(n)]


def _pareto(rng, n, alpha):
    return [max(1, int(3 * (1.0 - rng.uniform()) ** (-1.0 / alpha))) for _ in range(n)]


def _gen_pareto12(rng, n):
    return _pareto(rng, n, 1.2)


def _gen_pareto25(rng, n):
    return _pareto(rng, n, 2.5)


def _gen_lognormal(rng, n):
    out = []
    for _ in range(n):
        u1, u2 = 1.0 - rng.uniform(), rng.uniform()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        out.append(max(1, int(math.exp(2.0 + z))))
    return out


_FUNCTIONS = {
    "equal": _gen_equal, "uniform": _gen_uniform, "stepped": _gen_stepped,
    "pareto12": _gen_pareto12, "pareto25": _gen_pareto25, "lognormal": _gen_lognormal,
}


def generator_keys() -> tuple[str, ...]:
    return tuple(_FUNCTIONS)


def stream(gen: str, n: int, seed: int, j: int = 0, which: int = 0) -> SplitMix64:
    """Eigener Zufallsstrom je (Erzeuger, n, Zufalls-Seed, Instanznummer, Strom): gleiche Eingabe, gleicher Strom."""
    key = ((((seed * 1_000_003 + j) * 1_009 + n) * 7 + which) * 16 + generator_keys().index(gen)) * 7_919 + 12_345
    return SplitMix64(key)


def make_weights(gen: str, n: int, seed: int, j: int = 0, which: int = 0) -> tuple[int, ...]:
    """n ganzzahlige Gewichte (mindestens 1) aus dem Erzeuger `gen`."""
    if gen not in _FUNCTIONS:
        raise ValueError(f"unbekannter Erzeuger {gen!r}")
    return tuple(_FUNCTIONS[gen](stream(gen, n, seed, j, which), n))


def weights_text(weights) -> str:
    return ", ".join(str(int(x)) for x in weights)


def parse_weights(text: str) -> tuple[tuple[int, ...] | None, str | None]:
    """Gewichte aus der Handeingabe: ganze Zahlen von 1 an, getrennt durch Komma, Semikolon oder Leerzeichen. Rückgabe (Gewichte, None) oder (None, Fehlertext)."""
    if text is None or len(text) > C.TEXT_MAX_CHARS:
        return None, f"Die Eingabe ist zu lang (höchstens {C.TEXT_MAX_CHARS} Zeichen)."
    parts = [p for p in re.split(r"[,;\s]+", text.strip()) if p]
    if not parts:
        return None, "Bitte mindestens zwei Gewichte eingeben, zum Beispiel „40, 25, 10, 8“."
    weights = []
    for p in parts:
        if not re.fullmatch(r"\d+", p):
            return None, f"„{p}“ ist keine ganze Zahl. Erlaubt sind ganze Zahlen von {C.WEIGHT_MIN} an, getrennt durch Komma."
        weights.append(int(p))
    if len(weights) < C.N_MIN or len(weights) > C.N_MAX:
        k = len(weights)
        return None, f"Es {'ist' if k == 1 else 'sind'} {k} {'Gewicht' if k == 1 else 'Gewichte'} angegeben; erlaubt sind {C.N_MIN} bis {C.N_MAX} Mitglieder."
    if min(weights) < C.WEIGHT_MIN:
        return None, f"Jedes Gewicht muss mindestens {C.WEIGHT_MIN} sein."
    if sum(weights) > C.WEIGHT_SUM_MAX:
        return None, f"Die Gewichtssumme darf höchstens {C.WEIGHT_SUM_MAX:,} sein (sie ist {sum(weights):,}).".replace(",", ".")
    return tuple(weights), None
