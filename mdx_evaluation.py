"""Kennzahlen der Instanz und Verdikte der App als reine Funktionen `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`.

Jede Zahl im Text kommt aus den übergebenen Zeilen (f-String), nicht aus dem Gedächtnis; die Tests setzen die Zeilen von Hand."""

from dataclasses import dataclass
from fractions import Fraction

import mdx_constants as C
import mdx_game as G


def de(x: float, digits: int = 1) -> str:
    """Dezimalzahl mit Komma."""
    return f"{x:.{digits}f}".replace(".", ",")


def th(n: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{n:,}".replace(",", ".")


def pct(x: float, digits: int = 1) -> str:
    """Anteil 0 bis 1 als Prozentangabe mit Komma, zum Beispiel '26,9 %'."""
    return f"{de(100 * x, digits)} %"


def pp(x: float, digits: int = 1) -> str:
    """Anteil 0 bis 1 als Prozentpunkte: '2,9 Prozentpunkte'."""
    return f"{de(100 * x, digits)} Prozentpunkte"


def ppd(x: float, digits: int = 1) -> str:
    """Wie `pp`, im Dativ nach „um“, „von“, „bis“: '2,9 Prozentpunkten'."""
    return f"{de(100 * x, digits)} Prozentpunkten"


def name(i: int) -> str:
    return f"M{i + 1}"


def names(indices) -> str:
    return ", ".join(name(i) for i in indices)


@dataclass(frozen=True)
class Settings:
    weights: tuple[int, ...]
    permille: int            # Beschlussquote p in Promille: 500 heißt „mehr als die Hälfte“, 1000 Einstimmigkeit


@dataclass(frozen=True)
class Analysis:
    weights: tuple[int, ...]
    quota: int
    total: int
    swings: tuple[int, ...]
    pivots: tuple[int, ...]
    vote_share: tuple[float, ...]
    banzhaf: tuple[float, ...]
    shapley_shubik: tuple[float, ...]
    veto: tuple[int, ...]
    null: tuple[int, ...]
    dictator: int | None
    d_vote_banzhaf: float     # halbe L1-Abweichung Banzhaf-Anteil gegen Stimmanteil
    d_vote_shapley: float
    d_indices: float          # halbe L1-Abweichung Banzhaf gegen Shapley-Shubik

    @property
    def n(self) -> int:
        return len(self.weights)

    def largest_gap(self) -> tuple[int, float]:
        """(Mitglied, Banzhaf-Anteil minus Stimmanteil) mit dem größten Betrag der Abweichung."""
        gaps = [b - v for b, v in zip(self.banzhaf, self.vote_share)]
        i = max(range(len(gaps)), key=lambda k: (abs(gaps[k]), -k))
        return i, gaps[i]


def permille_of(percent: float) -> int:
    return int(round(percent * 10))


def analyse(settings: Settings) -> Analysis:
    w = list(settings.weights)
    total = sum(w)
    q = G.quota_from_share(total, Fraction(settings.permille, 1000))
    swings, pivots = G.pivot_counts_dp(w, q)
    banzhaf = G.banzhaf_shares(swings)
    shapley = G.shapley_shubik_shares(pivots, len(w))
    votes = G.weight_shares(w)
    return Analysis(
        tuple(w), q, total, tuple(swings), tuple(pivots), tuple(votes), tuple(banzhaf), tuple(shapley), tuple(G.veto_players(w, q)),
        tuple(G.null_players(swings)), G.dictator(swings), G.half_l1(banzhaf, votes), G.half_l1(shapley, votes), G.half_l1(banzhaf, shapley),
    )


# ---------------------------------------------------------------- Kernfrage

def verdict_power(a: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage „Wie weit weicht die Macht vom Stimmanteil ab?“ (Diktator, Nullspieler, Vetospieler, sonst nach der Abweichung)."""
    if a.dictator is not None:
        k = a.dictator
        return "warning", (f"**{name(k)} entscheidet allein** (Gewicht {a.weights[k]} von {a.total}, Quote {a.quota}): jeder Beschluss hängt nur von diesem Mitglied ab, "
                           "alle anderen haben Macht 0.")
    if a.null:
        votes = sum(a.vote_share[i] for i in a.null)
        return "warning", (f"**Nullspieler:** {names(a.null)} {'hat' if len(a.null) == 1 else 'haben'} zusammen {pct(votes)} der Stimmen, wird aber in keiner Koalition gebraucht "
                           f"und hat Macht 0 (Quote {a.quota} von {a.total}). Die Macht weicht im Ganzen um {ppd(a.d_vote_banzhaf)} vom Stimmanteil ab (halbe Abweichungssumme, Banzhaf).")
    if a.veto:
        return "info", (f"**Vetospieler:** ohne {names(a.veto)} erreicht keine Koalition die Quote {a.quota} von {a.total}. Die Macht weicht im Ganzen um "
                        f"{ppd(a.d_vote_banzhaf)} vom Stimmanteil ab (halbe Abweichungssumme, Banzhaf).")
    i, gap = a.largest_gap()
    gap_text = (f"Am weitesten weicht {name(i)} ab: {pct(a.vote_share[i])} der Stimmen, aber {pct(a.banzhaf[i])} der Macht (Banzhaf).")
    if a.d_vote_banzhaf >= 0.05:
        return "info", (f"**Macht und Stimmanteil weichen auseinander:** insgesamt um {ppd(a.d_vote_banzhaf)} (halbe Abweichungssumme, Banzhaf; Shapley–Shubik {pp(a.d_vote_shapley)}). {gap_text}")
    return "success", (f"**Macht und Stimmanteil liegen nahe beieinander:** die halbe Abweichungssumme beträgt {pp(a.d_vote_banzhaf)} (Banzhaf; Shapley–Shubik {pp(a.d_vote_shapley)}). {gap_text}")


# ---------------------------------------------------------------- Tab Zwei Indizes

def verdict_indices(a: Analysis, reversals: int, tie_vs_strict: int) -> tuple[str, str]:
    """Verdikt für die Instanz: weichen die Werte der beiden Indizes ab, und ordnen sie verschieden? Im Gewichtsspiel gilt: nie (Satz, siehe Tab)."""
    gap = max(abs(b - s) for b, s in zip(a.banzhaf, a.shapley_shubik))
    if reversals or tie_vs_strict:
        return "error", f"{reversals} Paare mit umgekehrter und {tie_vs_strict} Paare mit abweichender Rangordnung: das darf in einem Gewichtsspiel nicht vorkommen."
    if a.d_indices == 0:
        return "info", "Beide Indizes geben **dieselben Werte** (jedes Mitglied hat denselben Anteil), und sie ordnen die Mitglieder gleich."
    return "info", (f"Die **Werte** weichen ab: halbe Abweichungssumme {pp(a.d_indices)}, größte Abweichung eines Mitglieds {pp(gap)}. Die **Rangordnung** der Mitglieder ist bei beiden Indizes gleich "
                    "(in jedem Gewichtsspiel, siehe Satz).")


def verdict_rank_theorem(games: int, differ_rank: int, differ_values: int) -> tuple[str, str]:
    if differ_rank:
        return "error", f"In {differ_rank} von {games} Gewichtsspielen ordnen die Indizes verschieden: der Satz ist hier widerlegt."
    return "success", (f"In allen {games} aufgezählten Gewichtsspielen ordnen Banzhaf und Shapley–Shubik die Mitglieder **gleich**, obwohl ihre Werte in {differ_values} dieser Spiele "
                       "verschieden sind.")


# ---------------------------------------------------------------- E1: Erzeuger x Quote

def verdict_generators(rows: list[dict]) -> tuple[str, str]:
    """Verdikt E1: Zählung über alle Zellen (Macht gegen Stimmanteil, Banzhaf gegen Shapley–Shubik)."""
    m = len(rows)
    lo = min(rows, key=lambda r: r["dB"])
    hi = max(rows, key=lambda r: r["dB"])
    five = sum(r["dB"] >= 0.05 for r in rows)
    half = [r["dBS"] for r in rows if r["permille"] == 500]
    top = [r["dBS"] for r in rows if r["permille"] == max(x["permille"] for x in rows)]
    text = (f"In **{five} von {m} Zellen** liegt die mittlere Abweichung zwischen Macht (Banzhaf) und Stimmanteil bei mindestens 5 Prozentpunkten; sie reicht von {ppd(lo['dB'])} "
            f"({C.GENERATOR_LABELS[lo['gen']]}, n = {lo['n']}, p = {de(lo['permille'] / 10)} %) bis {ppd(hi['dB'])} ({C.GENERATOR_LABELS[hi['gen']]}, n = {hi['n']}, "
            f"p = {de(hi['permille'] / 10)} %).")
    if half and top:
        text += (f" Banzhaf und Shapley–Shubik weichen bei p = 50 % höchstens um {ppd(max(half))} voneinander ab, bei p = {de(max(r['permille'] for r in rows) / 10)} % bis zu {ppd(max(top))}.")
    return ("info" if five else "success"), text


# ---------------------------------------------------------------- E2: Quote

def verdict_best_quote(rows: list[dict]) -> tuple[str, str]:
    """Verdikt E2: die beste ganze Quote liegt über der einfachen Mehrheit; Abweichung dort gegen einfache Mehrheit (Banzhaf)."""
    count = rows[0]["count"]
    above = [r["above_majority"] for r in rows]
    worst = min(rows, key=lambda r: r["d_majority_B"] / r["d_best_B"] if r["d_best_B"] else float("inf"))
    best = max(rows, key=lambda r: r["d_majority_B"] / r["d_best_B"] if r["d_best_B"] else 0)
    ratio = lambda r: r["d_majority_B"] / r["d_best_B"]
    lo_q, hi_q = min(r["quote_rel"] for r in rows), max(r["quote_rel"] for r in rows)
    return "info", (f"Die beste Quote (kleinste Abweichung Macht gegen Stimmanteil) liegt im Mittel bei {pct(lo_q, 0)} bis {pct(hi_q, 0)} der Gesamtstimmen und in {min(above)} bis {max(above)} von "
                    f"je {count} Instanzen **über** der einfachen Mehrheit. Die Abweichung sinkt gegenüber der einfachen Mehrheit auf das 1/{de(ratio(worst))} ({C.GENERATOR_LABELS[worst['gen']]}) "
                    f"bis 1/{de(ratio(best))} ({C.GENERATOR_LABELS[best['gen']]}); Banzhaf, Verhältnis der Mittelwerte.")


# ---------------------------------------------------------------- E3: Paradoxa

def verdict_donor(rows: list[dict]) -> tuple[str, str]:
    """Verdikt E3a: Spenderparadox in den Zufallsreihen, getrennt nach Index."""
    cases_b = sum(r["cases_b"] for r in rows)
    cases_s = sum(r["cases_s"] for r in rows)
    transfers = sum(r["transfers"] for r in rows)
    half = [r for r in rows if r["permille"] == 500]
    half_b = sum(r["cases_b"] for r in half)
    if cases_b == 0 and cases_s == 0:
        return "info", f"In keiner der {th(transfers)} Einzelübertragungen gewinnt der Geber Macht, weder bei Banzhaf noch bei Shapley–Shubik."
    return "warning", (f"Der Geber gewinnt Machtanteil in **{th(cases_b)} von {th(transfers)}** Einzelübertragungen bei Banzhaf (bei p = 50 %: {half_b}) und in {cases_s} bei Shapley–Shubik. "
                       "Der Befund gilt für diese Zufallsreihe, nicht für jedes Spiel.")


def verdict_merge(rows: list[dict]) -> tuple[str, str]:
    pairs = sum(r["pairs"] for r in rows)
    less = sum(r["less_b"] for r in rows)
    differ_half = sum(r["differ"] for r in rows if r["permille"] == 500)
    differ_other = sum(r["differ"] for r in rows if r["permille"] != 500)
    return "info", (f"Der Block hat bei Banzhaf **weniger** Macht als die beiden vorher zusammen in {less} von {pairs} Paaren. Die Richtung (weniger, gleich, mehr) ist bei den beiden Indizes "
                    f"verschieden in {differ_half} Paaren bei p = 50 % und in {differ_other} Paaren bei den höheren Quoten.")


def verdict_split(rows: list[dict]) -> tuple[str, str]:
    cases = sum(r["cases"] for r in rows)
    more = sum(r["more_b"] for r in rows)
    less = sum(r["less_b"] for r in rows)
    return "info", f"Nach der Aufspaltung haben die beiden Teile bei Banzhaf zusammen **mehr** Macht in {more} von {cases} Fällen, weniger in {less}."


def verdict_new_member(rows: list[dict]) -> tuple[str, str]:
    count = sum(r["instances"] for r in rows)
    gain = sum(r["gain_b"] for r in rows)
    return "info", (f"Ein altes Mitglied gewinnt Machtanteil, wenn ein neues kommt, in {gain} von {count} Instanzen (Banzhaf). Das ist **keine Wertung**: die Anteile summieren sich zu 1, "
                    "und die neu bestimmte Quote springt (ganze Zahlen).")


# ---------------------------------------------------------------- E4: zwei Gewichtssysteme

def verdict_two_systems_instance(reversals: int, tie_vs_strict: int, pairs: int, values_equal: bool) -> tuple[str, str]:
    """Verdikt für die eingegebene Instanz: ordnen die Indizes verschieden?"""
    if reversals:
        return "warning", f"**Echte Umkehrung:** in {reversals} von {pairs} Mitgliederpaaren steht das eine Mitglied bei Banzhaf vorn und bei Shapley–Shubik hinten."
    if tie_vs_strict:
        return "info", f"Kein Paar ist umgekehrt, aber in {tie_vs_strict} von {pairs} Paaren ist ein Index gleichauf und der andere strikt geordnet."
    if values_equal:
        return "info", "Beide Indizes geben dieselben Werte."
    return "info", "Die Werte weichen ab, die Rangordnung ist bei beiden Indizes gleich."


def verdict_two_systems(rows: list[dict]) -> tuple[str, str]:
    """Verdikt E4: Anteil der Instanzen mit anderer Rangordnung im Schnitt zweier Gewichtssysteme."""
    lo = min(r["rank_differs"] for r in rows)
    hi = max(r["rank_differs"] for r in rows)
    rev_lo, rev_hi = min(r["reversal"] for r in rows), max(r["reversal"] for r in rows)
    zero = sum(r["rank_differs"] == 0 for r in rows)
    return "warning", (f"Im Schnitt zweier Gewichtssysteme ordnen die Indizes in {lo} bis {hi} von je {rows[0]['instances']} Instanzen verschieden (in {zero} von {len(rows)} Zellen nie); "
                       f"eine echte Umkehrung gibt es in {rev_lo} bis {rev_hi} Instanzen je Zelle. Der Rest der Abweichungen ist Gleichstand im einen und strikte Ordnung im anderen Index.")


# ---------------------------------------------------------------- E5/E6/Tab Beirat

def verdict_board(members: list[int], seats: list[int], banzhaf: list[float], shapley: list[float], method: str, total_seats: int) -> tuple[str, str]:
    """Verdikt für die Beirat-Instanz: Mitgliederanteil, Sitzanteil und Macht des größten Verbands."""
    k = max(range(len(members)), key=lambda i: (members[i], -i))
    share = members[k] / sum(members)
    text = (f"Der größte Verband hat {pct(share)} der Mitglieder und nach {method} {seats[k]} von {total_seats} Sitzen ({pct(seats[k] / total_seats)}); bei Beschluss mit mehr als der Hälfte der Sitze "
            f"hat er {pct(banzhaf[k])} der Macht (Banzhaf) und {pct(shapley[k])} (Shapley–Shubik).")
    if banzhaf[k] >= 0.999999:
        return "warning", text + " Er entscheidet allein."
    return ("info" if banzhaf[k] > 1.2 * share else "success"), text


def verdict_seats_series(rows_by_sigma: dict) -> tuple[str, str]:
    """Verdikt E5: Abweichung der Macht vom Mitgliederanteil gegenüber der Abweichung der Sitze; Jefferson am weitesten?"""
    lines = []
    farthest = 0
    cells = 0
    for sigma, rows in rows_by_sigma.items():
        by_seats = {}
        for r in rows:
            by_seats.setdefault(r["seats"], []).append(r)
        for seats, group in by_seats.items():
            cells += 1
            far = max(group, key=lambda r: r["d_seat"])
            farthest += far["method"] == "Jefferson"
        lo = min(r["d_banzhaf"] / r["d_seat"] for r in rows)
        hi = max(r["d_banzhaf"] / r["d_seat"] for r in rows)
        lines.append(f"σ = {de(sigma)}: die Macht weicht {de(lo)}- bis {de(hi)}-mal so weit vom Mitgliederanteil ab wie die Sitze (Banzhaf)")
    return "info", "; ".join(lines) + f". Jefferson liegt in {farthest} von {cells} Zeilen (Größenverteilung, Hausgröße) bei den Sitzen am weitesten vom Mitgliederanteil."


def verdict_runtime(rows: list[dict]) -> tuple[str, str]:
    """Verdikt E6: die DP rechnet 60 Mitglieder bei kleiner Gewichtssumme in Millisekunden; die Zeit hängt an der Gewichtssumme."""
    slowest = max(rows, key=lambda r: r["seconds"])
    return "info", (f"Die längste Messung war n = {slowest['n']} mit Gewichtssumme {th(slowest['total'])} in {de(slowest['seconds'], 3)} s; "
                    "die Zeit hängt an Rechner und Auslastung und wird hier nicht als Befund gewertet.")


def verdict_raster(rows: list[dict]) -> tuple[str, str]:
    """Verdikt E6b: Rundung auf ganze Gewichte; die Abweichung des Banzhaf-Anteils sinkt mit der Gewichtssumme."""
    first, last = rows[0], rows[-1]
    return "info", (f"Bei Gewichtssumme {first['total']} weicht der Banzhaf-Anteil im Mittel um höchstens {de(first['mean_worst_pp'], 2)} Prozentpunkte vom feinen Raster ab "
                    f"(über 1 Prozentpunkt in {first['over_1pp']} von {first['count']} Instanzen), bei {th(last['total'])} sind es {de(last['mean_worst_pp'], 3)} ({last['over_1pp']} von {last['count']}).")


# ---------------------------------------------------------------- Expander Owen

def verdict_owen(vote: dict, airport: dict) -> tuple[str, str]:
    """Verdikt Owen: Zusammenschluss zweier Gruppen; nachteilig in einer Spielklasse, in der anderen in dieser Stichprobe nicht."""
    text = (f"Abstimmungsspiel (n = {vote['n']}, {vote['count']} Zusammenschlüsse): nachteilig {vote['worse']}, unverändert {vote['same']}, vorteilhaft {vote['better']}"
            f"{'; größte Einbuße ' + de(vote['biggest_loss'], 3) + ' (Anteil am Gesamtwert 1)' if vote['worse'] else ''}. "
            f"Flughafenspiel (n = {airport['n']}, {airport['count']} Zusammenschlüsse): nachteilig {airport['worse']}, unverändert {airport['same']}, vorteilhaft {airport['better']}.")
    if vote["worse"] and not airport["worse"]:
        return "warning", text + f" Im Flughafenspiel trat in diesen {airport['count']} Zusammenschlüssen kein nachteiliger Fall auf; die Literatur nennt „immer vorteilhaft“ dort einen Satz."
    return "info", text


# ---------------------------------------------------------------- Tab Paradoxa (eine Instanz)

def verdict_paradox_instance(op: str, subject: str, b0, b1, s0, s1) -> tuple[str, str]:
    """Verdikt für die gewählte Änderung. `b0`/`b1` und `s0`/`s1` sind die exakten Anteile (Brüche) des betrachteten Mitglieds oder Blocks vorher und nachher
    (beim neuen Mitglied: das alte Mitglied mit dem größten Zuwachs). op: 'donor', 'merge', 'split', 'new'."""
    def word(new, old):
        return "mehr" if new > old else ("weniger" if new < old else "gleich viel")
    text = (f"{subject}: Banzhaf-Anteil {pct(float(b0))} → {pct(float(b1))} ({word(b1, b0)}), Shapley–Shubik-Anteil {pct(float(s0))} → {pct(float(s1))} ({word(s1, s0)}).")
    if op == "donor" and b1 > b0:
        return "warning", "**Spenderparadox:** " + text + " Das Mitglied gibt eine Stimme ab und gewinnt Machtanteil."
    if op == "donor" and s1 > s0:
        return "warning", "**Spenderparadox (nur Shapley–Shubik):** " + text
    if op == "merge" and (b1 < b0 or s1 < s0):
        return "warning", "**Der Zusammenschluss kostet Macht:** " + text
    if op == "split" and (b1 > b0 or s1 > s0):
        return "warning", "**Die Aufspaltung gibt zusammen mehr Macht:** " + text
    if op == "new" and (b1 > b0 or s1 > s0):
        return "info", text + " Das ist keine Wertung: die Anteile summieren sich zu 1, und die Quote wird mit demselben Anteil p neu bestimmt."
    return "info", text
