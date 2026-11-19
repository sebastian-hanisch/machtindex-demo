"""Macht in der Genossenschaft: wer entscheidet wirklich? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stimmgewichte und Quote einer Spediteursgenossenschaft -> Banzhaf- und Shapley-Shubik-Index (Zählen per dynamischer Programmierung statt 2^n Koalitionen).
Aufbau und Regeln: DEMO-PLAYBOOK §2. Alle Zahlen im Text kommen aus der Rechnung oder stehen in tests/test_claims.py.

Lauffähig mit: streamlit run app.py
"""

import math
import time
from fractions import Fraction

import pandas as pd
import streamlit as st

import mdx_constants as C
import mdx_experiments as E
import mdx_game as G
import mdx_harsanyi as H
import mdx_paradoxes as P
import mdx_scenario as S
import mdx_seats as ST
import mdx_texts as T
from mdx_evaluation import (
    Settings, analyse, de, name, pct, permille_of, pp, th, verdict_best_quote, verdict_board, verdict_donor, verdict_generators, verdict_indices,
    verdict_merge, verdict_new_member, verdict_owen, verdict_paradox_instance, verdict_power, verdict_rank_theorem, verdict_raster, verdict_runtime,
    verdict_seats_series, verdict_split, verdict_two_systems, verdict_two_systems_instance,
)
from mdx_layout import dunkles_design, kopf_css
from mdx_presets import (
    bounds, generate_weights, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params,
)
from mdx_visualization import (
    build_generator_lines, build_index_gap, build_power, build_quote_curve, build_quote_members, build_staircase,
)

st.set_page_config(page_title="Macht in der Genossenschaft – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _quote_scan(weights, percents):
    return E.quote_scan(weights, percents)


@st.cache_data(show_spinner=False)
def _best_quote_of(weights):
    return E.best_quote_of(weights)


@st.cache_data(show_spinner=False)
def _timing(weights, quota):
    """Zeit der Zählung (DP) und, bei n <= 20, der Aufzählung über die Gewinntabelle für diese Instanz (Sekunden; hängt an Rechner und Auslastung)."""
    t0 = time.perf_counter()
    G.pivot_counts_dp(list(weights), quota)
    dp = time.perf_counter() - t0
    enum = None
    if len(weights) <= 20:
        t0 = time.perf_counter()
        G.pivot_counts_subsets(list(weights), quota)
        enum = time.perf_counter() - t0
    return dp, enum


@st.cache_data(show_spinner=False)
def _power_of(weights, quota):
    swings, pivots = G.pivot_counts_dp(list(weights), quota)
    return swings, pivots


def run_experiment(key, label, fn, spinner="Rechnet …"):
    """Knopf `🔬 …`: rechnet beim Klick, merkt sich das Ergebnis samt Zeit im Session State und gibt es bei jedem Lauf zurück (oder None)."""
    if st.button(label, key=f"run_{key}"):
        t0 = time.perf_counter()
        with st.spinner(spinner):
            result = fn()
        st.session_state[f"result_{key}"] = (result, time.perf_counter() - t0)
    stored = st.session_state.get(f"result_{key}")
    if stored is not None:
        st.caption(f"Gerechnet in {de(stored[1], 1)} s (Zeit hängt an Rechner und Auslastung).")
    return None if stored is None else stored[0]


def show(verdict):
    kind, text = verdict
    getattr(st, kind)(text)


def percent_column(label):
    return st.column_config.NumberColumn(label, format="%.1f %%")


def points_column(label):
    return st.column_config.NumberColumn(label, format="%.1f")


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mdx_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🗳️ Macht in der Genossenschaft: wer entscheidet wirklich?")
st.markdown(T.INTRO_MARKDOWN)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/machtindex-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Eine Spediteursgenossenschaft beschließt per Abstimmung: Jedes Mitglied hat so viele Stimmen, wie es Lkw im Fuhrpark hat, und ein Beschluss fällt, wenn die Zustimmenden zusammen mindestens die **Quote** erreichen. Die Demo fragt, wie oft ein Mitglied den Ausschlag gibt, und vergleicht diese **Macht** mit dem Stimmanteil. Sie zählt auf zwei Arten: über alle Gruppen von Zustimmenden (**Banzhaf-Index**) und über alle Reihenfolgen des Beitritts (**Shapley–Shubik-Index**). Danach prüft sie an erzeugten Genossenschaften, wann Macht und Stimmanteil auseinanderlaufen. **Gewichte und Quote sind Modellannahmen, und Macht heißt nur: den Ausschlag geben.** Die Zählungen gelten für die gezogenen Zufallsinstanzen und sind kein Beweis.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/machtindex-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert die Macht-Messung", expanded=True):
    st.markdown(T.HOW_IT_WORKS_MARKDOWN)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Genossenschaft**")
    weights_text = st.text_input("Gewichte der Mitglieder (Lkw im Fuhrpark)", key="weights_text",
                                 help=f"{C.N_MIN} bis {C.N_MAX} ganze Zahlen von {C.WEIGHT_MIN} an, getrennt durch Komma. Die Gewichtssumme darf höchstens {th(C.WEIGHT_SUM_MAX)} sein.")
    p_percent = st.slider("Beschlussquote p (in %)", *bounds("p_slider"), key="p_slider", step=C.P_STEP, format="%.1f",
                          help="Ein Beschluss braucht mehr als diesen Anteil der Gesamtgewichte (bei 100 % alle Stimmen). 50 % ist die einfache Mehrheit, 100 % Einstimmigkeit.")
    st.markdown("**Gewichte erzeugen**")
    st.caption("Der Knopf überschreibt das Textfeld oben mit zufälligen Gewichten aus diesem Erzeuger.")
    st.selectbox("Erzeuger", list(S.generator_keys()), key="gen_select", format_func=C.GENERATOR_LABELS.get)
    st.slider("Mitglieder n", *bounds("n_slider"), key="n_slider", help="Wie viele Gewichte der Erzeuger zieht.")
    st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Gewichte erzeugen", width="stretch", on_click=generate_weights, key="generate")
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed, key="random_seed")

sync_query_params({k: st.session_state.get(k) for k in ("weights_text", "p_slider", "gen_select", "n_slider", "seed_input")})

weights, error = S.parse_weights(weights_text)
if error:
    st.error(error)
    st.stop()

settings = Settings(weights, permille_of(p_percent))
a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Mitglieder", f"{a.n}")
m2.metric("Gesamtstimmen", th(a.total))
m3.metric("Quote", f"{th(a.quota)} von {th(a.total)}", delta=f"{pct(a.quota / a.total)} der Stimmen", delta_color="off")
m4.metric("Vetospieler", f"{len(a.veto)}", delta="ohne sie fällt kein Beschluss", delta_color="off")
m5.metric("Nullspieler", f"{len(a.null)}", delta="Macht 0 trotz Stimmen", delta_color="off")

table = pd.DataFrame({
    "Mitglied": [name(i) for i in range(a.n)],
    "Gewicht": list(a.weights),
    "Stimmanteil": [100 * x for x in a.vote_share],
    "Schwingzahl": list(a.swings),
    "Banzhaf-Anteil": [100 * x for x in a.banzhaf],
    "Shapley–Shubik-Anteil": [100 * x for x in a.shapley_shubik],
    "Macht je Stimmanteil (Banzhaf)": [b / v for b, v in zip(a.banzhaf, a.vote_share)],
})
st.dataframe(
    table, hide_index=True, width="stretch",
    column_config={
        "Stimmanteil": percent_column("Stimmanteil"), "Banzhaf-Anteil": percent_column("Banzhaf-Anteil"), "Shapley–Shubik-Anteil": percent_column("Shapley–Shubik-Anteil"),
        "Macht je Stimmanteil (Banzhaf)": st.column_config.NumberColumn("Macht je Stimmanteil (Banzhaf)", format="%.2f"),
    },
)
st.plotly_chart(build_power(a), width="stretch", key="power_chart")
st.caption("Anteile an der gesamten Macht (Summe 100 %). „Macht je Stimmanteil“ ist der Banzhaf-Anteil geteilt durch den Stimmanteil: 1 heißt, die Macht folgt den Stimmen.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie weit weicht die Macht vom Stimmanteil ab?")
show(verdict_power(a))

st.markdown("---")

# --- Tabs ------------------------------------------------------------------------------------------------------------------------------------

tab_power, tab_quote, tab_indices, tab_two, tab_paradox, tab_count, tab_board = st.tabs([
    "Macht gegen Stimmanteil", "Quote als Regler", "Zwei Indizes", "Zwei Gewichtssysteme", "Paradoxa", "Zählen statt Aufzählen", "Beirat",
])

# ---- Tab 1 ----------------------------------------------------------------------------------------------------------------------------------
with tab_power:
    st.markdown("Oben steht die Macht der eingestellten Genossenschaft. Hier die Frage über **viele zufällige Genossenschaften**: weicht die Macht vom Stimmanteil ab, auch wenn die Gewichte keinen schweren Tail haben?")
    st.subheader("🔬 Experiment: Macht gegen Stimmanteil nach Erzeuger, Mitgliederzahl und Quote")
    st.caption("Je Zelle (Erzeuger, n, Quote) vier feste Zufalls-Seeds mit je 50 Instanzen; die Quote ist „mehr als p“ der Gesamtgewichte.")
    rows = run_experiment("e1", "🔬 Erzeuger × Quote rechnen", lambda: E.generator_table(C.EXPERIMENT_GENERATORS, (5, 7, 9), C.PERMILLES), "Zählt 72 Zellen mit je 200 Instanzen …")
    if rows:
        n_show = st.radio("Mitgliederzahl für das Diagramm", (5, 7, 9), index=1, horizontal=True, key="e1_n")
        st.plotly_chart(build_generator_lines(rows, n_show), width="stretch", key="e1_chart")
        st.dataframe(
            pd.DataFrame([{
                "Erzeuger": C.GENERATOR_LABELS[r["gen"]], "n": r["n"], "p (%)": r["permille"] / 10, "Macht gegen Stimmanteil (Banzhaf)": 100 * r["dB"],
                "Macht gegen Stimmanteil (Shapley–Shubik)": 100 * r["dS"], "Banzhaf gegen Shapley–Shubik": 100 * r["dBS"], "größte Abweichung eines Mitglieds": r["max_pp"],
                "Nullspieler": 100 * r["null"], "Diktator": 100 * r["dictator"], "Vetospieler": 100 * r["veto"],
            } for r in rows]),
            hide_index=True, width="stretch",
            column_config={k: points_column(k) for k in ("Macht gegen Stimmanteil (Banzhaf)", "Macht gegen Stimmanteil (Shapley–Shubik)", "Banzhaf gegen Shapley–Shubik", "größte Abweichung eines Mitglieds")}
            | {k: percent_column(k) for k in ("Nullspieler", "Diktator", "Vetospieler")},
        )
        st.caption("Abweichungen in Prozentpunkten (halbe Summe der Beträge); Nullspieler, Diktator und Vetospieler als Anteil der 200 Instanzen je Zelle (Vetospieler ohne Diktator).")
        show(verdict_generators(rows))

# ---- Tab 2 ----------------------------------------------------------------------------------------------------------------------------------
with tab_quote:
    st.markdown("Die Quote steuert, wie ungleich die Macht verteilt ist: bei **Einstimmigkeit** hat jedes Mitglied ein Veto und damit gleich viel Macht, bei knapper Mehrheit entscheiden wenige.")
    st.subheader("Diese Genossenschaft: Macht über die Quote")
    percents = tuple(range(50, 101, 5))
    scan = _quote_scan(a.weights, percents)
    shown = sorted(range(a.n), key=lambda i: (-a.weights[i], i))[:10]
    st.plotly_chart(build_quote_members(list(percents), [[row[i] for row in scan] for i in shown], [f"{name(i)} (Gewicht {a.weights[i]})" for i in shown]), width="stretch", key="quote_members_chart")
    st.caption("Banzhaf-Anteil der (höchstens zehn) gewichtsstärksten Mitglieder bei Quoten von 50 % bis 100 % in Schritten von 5 Prozentpunkten; die Mitglieder sind nach Gewicht sortiert.")
    best = _best_quote_of(a.weights)
    if best is None:
        st.info(f"Die beste ganze Quote wird nur für höchstens {G.MAX_MULTI_PLAYERS} Mitglieder und Gewichtssumme bis 2.000 gesucht (hier n = {a.n}, Summe {th(a.total)}).")
    else:
        st.info(f"Beste ganze Quote für diese Genossenschaft: **{best['quote']} von {best['total']}** ({pct(best['quote'] / best['total'])}); die Abweichung zwischen Macht (Banzhaf) und Stimmanteil beträgt dort "
                f"{pp(best['distance'])} gegenüber {pp(best['distance_majority'])} bei der einfachen Mehrheit (Quote {best['majority']}).")
    st.subheader("🔬 Experiment: Welche Quote macht die Macht dem Stimmanteil am ähnlichsten?")
    st.caption("n = 7 Mitglieder, je Erzeuger vier feste Zufalls-Seeds mit je 50 Instanzen; die beste Quote wird je Instanz über alle ganzen Quoten über der Hälfte gesucht.")

    def _e2():
        gens = C.EXPERIMENT_GENERATORS
        return ({g: E.quote_curve(g, 7, (50, 55, 60, 67, 75, 85, 100)) for g in gens}, [E.best_quote(g, 7) for g in gens])

    result = run_experiment("e2", "🔬 Quote-Verlauf und beste Quote rechnen", _e2, "Sucht die beste Quote in 1.200 Instanzen …")
    if result:
        curves, bests = result
        st.plotly_chart(build_quote_curve(curves), width="stretch", key="e2_chart")
        st.dataframe(
            pd.DataFrame([{
                "Erzeuger": C.GENERATOR_LABELS[b["gen"]], "Abweichung bei einfacher Mehrheit": 100 * b["d_majority_B"], "Abweichung bei bester Quote": 100 * b["d_best_B"],
                "mittlere beste Quote (% von W)": 100 * b["quote_rel"], "beste Quote über einfacher Mehrheit (Instanzen)": b["above_majority"], "Instanzen": b["count"],
            } for b in bests]),
            hide_index=True, width="stretch",
            column_config={"Abweichung bei einfacher Mehrheit": points_column("Abweichung bei einfacher Mehrheit"), "Abweichung bei bester Quote": points_column("Abweichung bei bester Quote"),
                           "mittlere beste Quote (% von W)": points_column("mittlere beste Quote (% von W)")},
        )
        st.caption("Abweichung Macht (Banzhaf) gegen Stimmanteil in Prozentpunkten, Mittel über die Instanzen.")
        show(verdict_best_quote(bests))

# ---- Tab 3 ----------------------------------------------------------------------------------------------------------------------------------
with tab_indices:
    st.markdown("Banzhaf zählt **Koalitionen**, Shapley–Shubik **Reihenfolgen**. Die **Werte** weichen ab, die **Rangordnung** der Mitglieder nie: das ist ein Satz für Gewichtsspiele.")
    reversals, tie_vs_strict = E.rank_pairs(a.swings, a.pivots)
    show(verdict_indices(a, reversals, tie_vs_strict))
    st.plotly_chart(build_index_gap(a), width="stretch", key="gap_chart")
    st.caption("Positive Balken: Shapley–Shubik gibt dem Mitglied mehr Macht als Banzhaf.")
    with st.expander("Satz und Beweisskizze: warum beide Indizes in Gewichtsspielen gleich ordnen"):
        st.markdown(T.RANK_THEOREM_MARKDOWN)
    st.subheader("🔬 Experiment: Satz an allen kleinen Gewichtsspielen prüfen")
    st.caption("Aufgezählt werden alle nichtfallenden Gewichtsvektoren mit n = 3 bis 7 Mitgliedern und kleinen Gewichten (n = 3: bis 12, n = 4: bis 10, n = 5: bis 8, n = 6: bis 6, n = 7: bis 4), jeweils mit allen Quoten über der Hälfte.")
    result = run_experiment("e_rank", "🔬 Satz prüfen", E.rank_theorem_enumeration, "Zählt alle kleinen Gewichtsspiele …")
    if result:
        show(verdict_rank_theorem(result["games"], result["rank_differs"], result["values_differ"]))
    if a.weights == S.parse_weights(C.PRESETS["EU-Rat Nizza (nur Stimmbedingung)"]["weights"])[0]:
        top, small = 0, a.n - 1
        st.info(f"EU-Rat Nizza (nur die Stimmbedingung, nicht die Beschlussregel): ein Mitglied mit {a.weights[top]} Stimmen hat {pct(a.vote_share[top], 2)} der Stimmen, "
                f"{pct(a.banzhaf[top], 2)} nach Banzhaf und {pct(a.shapley_shubik[top], 2)} nach Shapley–Shubik; das kleinste Mitglied ({a.weights[small]} Stimmen) hat {pct(a.vote_share[small], 2)}, "
                f"{pct(a.banzhaf[small], 2)} und {pct(a.shapley_shubik[small], 2)}. Banzhaf liegt bei allen Mitgliedern bis 14 Stimmen über dem Stimmanteil, Shapley–Shubik nur bei den sechs Mitgliedern mit 27 oder 29 Stimmen.")

# ---- Tab 4 ----------------------------------------------------------------------------------------------------------------------------------
with tab_two:
    st.markdown("Gelten **zwei Quoten zugleich** (zum Beispiel nach Fuhrpark **und** nach Umsatz müssen beide erreicht sein), ist das Spiel kein Gewichtsspiel mehr. Hier können Banzhaf und Shapley–Shubik die Mitglieder verschieden ordnen, im Gewichtsspiel mit einer Quote nicht.")

    def _reset_two():
        st.session_state["ts_w1"], st.session_state["ts_q1"] = C.SYSTEM_FLEET, C.SYSTEM_FLEET_QUOTA
        st.session_state["ts_w2"], st.session_state["ts_q2"] = C.SYSTEM_TURNOVER, C.SYSTEM_TURNOVER_QUOTA

    for key, default in (("ts_w1", C.SYSTEM_FLEET), ("ts_q1", C.SYSTEM_FLEET_QUOTA), ("ts_w2", C.SYSTEM_TURNOVER), ("ts_q2", C.SYSTEM_TURNOVER_QUOTA)):
        st.session_state.setdefault(key, default)
    c1, c2 = st.columns(2)
    w1_text = c1.text_input("Gewichte nach Fuhrpark", key="ts_w1")
    q1 = c1.number_input("Quote Fuhrpark", min_value=1, max_value=100_000, step=1, key="ts_q1")
    w2_text = c2.text_input("Gewichte nach Umsatz", key="ts_w2")
    q2 = c2.number_input("Quote Umsatz", min_value=1, max_value=100_000, step=1, key="ts_q2")
    st.button("Beispiel zurücksetzen (n = 7, echte Umkehrung)", on_click=_reset_two, key="reset_two")
    w1, e1 = S.parse_weights(w1_text)
    w2, e2 = S.parse_weights(w2_text)
    if e1 or e2:
        st.error(e1 or e2)
    elif len(w1) != len(w2) or len(w1) > 12:
        st.error("Beide Systeme brauchen gleich viele Mitglieder (höchstens 12).")
    elif not (1 <= q1 <= sum(w1) and 1 <= q2 <= sum(w2)):
        st.error(f"Die Quoten müssen zwischen 1 und der Gewichtssumme liegen (Fuhrpark {sum(w1)}, Umsatz {sum(w2)}).")
    else:
        n2 = len(w1)
        win = G.intersection_game([w1, w2], [int(q1), int(q2)])
        if not win.any():
            st.warning("Keine Koalition erreicht beide Quoten: es gibt keinen Beschluss.")
        else:
            sw2, pv2 = G.pivot_counts_from_win(win, n2)
            b2, s2 = G.banzhaf_shares(sw2), G.shapley_shubik_shares(pv2, n2)
            st.dataframe(
                pd.DataFrame({"Mitglied": [name(i) for i in range(n2)], "Fuhrpark": list(w1), "Umsatz": list(w2), "Schwingzahl": sw2, "Banzhaf-Anteil": [100 * x for x in b2],
                              "Reihenfolgen (Shapley–Shubik, von " + th(math.factorial(n2)) + ")": pv2, "Shapley–Shubik-Anteil": [100 * x for x in s2]}),
                hide_index=True, width="stretch",
                column_config={"Banzhaf-Anteil": percent_column("Banzhaf-Anteil"), "Shapley–Shubik-Anteil": percent_column("Shapley–Shubik-Anteil")},
            )
            rev, tie = E.rank_pairs(sw2, pv2)
            show(verdict_two_systems_instance(rev, tie, n2 * (n2 - 1) // 2, E.same_values(sw2, pv2, n2)))
    st.subheader("🔬 Experiment: Wie oft ordnen die Indizes im Schnitt zweier Gewichtssysteme verschieden?")
    st.caption("Beide Gewichtsvektoren unabhängig aus demselben Erzeuger, Quote „mehr als p“ in beiden; je Zelle vier feste Zufalls-Seeds mit je 50 Instanzen.")

    def _e4():
        return [E.two_system_series(g, n, pm) for g in ("uniform", "lognormal") for n in (6, 8, 9) for pm in (500, 667)]

    rows = run_experiment("e4", "🔬 Rangordnungen vergleichen", _e4, "Zählt zwölf Zellen …")
    if rows:
        st.dataframe(
            pd.DataFrame([{"Erzeuger": C.GENERATOR_LABELS[r["gen"]], "n": r["n"], "p (%)": r["permille"] / 10, "Instanzen": r["instances"], "Rangordnung verschieden": r["rank_differs"],
                           "davon echte Umkehrung": r["reversal"], "nur Gleichstand gegen strikt": r["tie_only"], "Werte verschieden": r["values_differ"]} for r in rows]),
            hide_index=True, width="stretch")
        st.caption("Zahl der Instanzen je Zelle. Echte Umkehrung: ein Mitglied steht bei Banzhaf vor einem anderen und bei Shapley–Shubik dahinter.")
        show(verdict_two_systems(rows))

# ---- Tab 5 ----------------------------------------------------------------------------------------------------------------------------------
with tab_paradox:
    st.markdown("Weniger Stimmen heißen nicht immer weniger Macht. Hier verändern Sie die **Genossenschaft aus der Seitenleiste** (Quote bleibt als Zahl gleich, außer beim neuen Mitglied) und sehen, wie sich der Machtanteil bewegt.")
    op = st.selectbox("Änderung", ["Eine Stimme abgeben", "Zwei Mitglieder zusammenlegen", "Ein Mitglied aufspalten", "Ein neues Mitglied aufnehmen"], key="paradox_op")
    members = [name(i) for i in range(a.n)]
    q_now = a.quota
    if op == "Eine Stimme abgeben":
        pc1, pc2 = st.columns(2)
        giver = pc1.selectbox("Geber", range(a.n), format_func=name, key="p_giver")
        receiver = pc2.selectbox("Empfänger", range(a.n), index=min(1, a.n - 1), format_func=name, key="p_receiver")
        if giver == receiver or a.weights[giver] < 2:
            st.warning("Geber und Empfänger müssen verschieden sein, und der Geber braucht mindestens 2 Stimmen.")
        else:
            new_w = tuple(P.transfer(a.weights, giver, receiver))
            sw, pv = _power_of(new_w, q_now)
            b1, s1 = G.banzhaf_shares(sw), G.shapley_shubik_shares(pv, a.n)
            st.dataframe(pd.DataFrame({"Mitglied": members, "Gewicht vorher": a.weights, "Gewicht nachher": new_w, "Banzhaf vorher": [100 * x for x in a.banzhaf], "Banzhaf nachher": [100 * x for x in b1],
                                       "Shapley–Shubik vorher": [100 * x for x in a.shapley_shubik], "Shapley–Shubik nachher": [100 * x for x in s1]}),
                         hide_index=True, width="stretch",
                         column_config={k: percent_column(k) for k in ("Banzhaf vorher", "Banzhaf nachher", "Shapley–Shubik vorher", "Shapley–Shubik nachher")})
            b0f, s0f = P.powers(a.weights, q_now)
            b1f, s1f = P.powers(new_w, q_now)
            show(verdict_paradox_instance("donor", f"Geber {name(giver)}", b0f[giver], b1f[giver], s0f[giver], s1f[giver]))
    elif op == "Zwei Mitglieder zusammenlegen":
        pc1, pc2 = st.columns(2)
        first = pc1.selectbox("Erstes Mitglied", range(a.n), format_func=name, key="p_first")
        second = pc2.selectbox("Zweites Mitglied", range(a.n), index=min(1, a.n - 1), format_func=name, key="p_second")
        if first == second:
            st.warning("Bitte zwei verschiedene Mitglieder wählen.")
        else:
            new_w = tuple(P.merge(a.weights, first, second))
            b0f, s0f = P.powers(a.weights, q_now)
            b1f, s1f = P.powers(new_w, q_now)
            st.info(f"Der Block hat das Gewicht {new_w[-1]} und steht in der neuen Liste zuletzt (Quote bleibt {q_now}).")
            show(verdict_paradox_instance("merge", f"Block aus {name(first)} und {name(second)}", b0f[first] + b0f[second], b1f[-1], s0f[first] + s0f[second], s1f[-1]))
    elif op == "Ein Mitglied aufspalten":
        who = st.selectbox("Mitglied", range(a.n), format_func=name, key="p_split")
        if a.weights[who] < 2:
            st.warning("Ein Mitglied mit Gewicht 1 lässt sich nicht teilen.")
        else:
            new_w = tuple(P.split(a.weights, who))
            b0f, s0f = P.powers(a.weights, q_now)
            b1f, s1f = P.powers(new_w, q_now)
            st.info(f"Die beiden Teile haben die Gewichte {new_w[-2]} und {new_w[-1]} und stehen in der neuen Liste zuletzt (Quote bleibt {q_now}).")
            show(verdict_paradox_instance("split", f"Beide Teile von {name(who)}", b0f[who], b1f[-1] + b1f[-2], s0f[who], s1f[-1] + s1f[-2]))
    else:
        newcomer = st.number_input("Gewicht des neuen Mitglieds", min_value=1, max_value=max(1, a.total), value=min(3, max(1, a.total)), step=1, key="p_new")
        if a.n >= C.N_MAX:
            st.warning(f"Die Genossenschaft hat schon {C.N_MAX} Mitglieder.")
        else:
            old_w, new_w = a.weights, a.weights + (int(newcomer),)
            q_new = G.quota_from_share(sum(new_w), Fraction(settings.permille, 1000))
            b0f, s0f = P.powers(old_w, q_now)
            b1f, s1f = P.powers(new_w, q_new)
            gains = [(b1f[i] - b0f[i], i) for i in range(a.n)]
            best_gain, who = max(gains, key=lambda t: (t[0], -t[1]))
            st.info(f"Die Quote wird mit demselben Anteil p neu bestimmt: {q_now} → {q_new}.")
            show(verdict_paradox_instance("new", f"Das alte Mitglied mit dem größten Zuwachs ({name(who)})", b0f[who], b1f[who], s0f[who], s1f[who]))
    st.markdown(f"**Vollständig aufgezählt** (alle nichtfallenden Gewichtsvektoren mit n = 3 bis 6 und kleinen Gewichten, alle Quoten über der Hälfte, alle Einzelübertragungen einer Stimme): "
                f"unter {T.DONOR_TRANSFERS_TEXT} Übertragungen gewinnt der Geber bei Banzhaf Machtanteil in {T.DONOR_CASES_B_TEXT} Fällen, bei Shapley–Shubik in {T.DONOR_CASES_S}. "
                "Das kleinste Beispiel ist das Preset „Spenderparadox“ (Gewichte 1, 1, 1, 2, 4; Quote 7; das Mitglied mit 4 Stimmen gibt eine an das mit 2 ab). Die Zählung ist kein Beweis.")
    st.subheader("🔬 Experiment: Wie oft kommen die Paradoxa in Zufallsinstanzen vor?")
    st.caption("n = 6 Mitglieder (neues Mitglied: 6 alte), vier Erzeuger, Quote mehr als 1/2 und mehr als 2/3; je Zelle vier feste Zufalls-Seeds mit je 50 Instanzen.")

    def _e3():
        cells = [(g, pm) for g in C.PARADOX_GENERATORS for pm in (500, 667)]
        return ([E.donor_series(g, 6, pm) for g, pm in cells], [E.merge_series(g, 6, pm) for g, pm in cells], [E.split_series(g, 6, pm) for g, pm in cells],
                [E.new_member_series(g, 6, pm) for g, pm in cells])

    result = run_experiment("e3", "🔬 Paradoxa zählen", _e3, "Zählt Übertragungen, Zusammenschlüsse, Aufspaltungen …")
    if result:
        donors, merges, splits, newcomers = result
        label = lambda r: f"{C.GENERATOR_LABELS[r['gen']]}, p = {de(r['permille'] / 10)} %"
        st.markdown("**Stimme abgeben** (Geber gewinnt Machtanteil)")
        st.dataframe(pd.DataFrame([{"Zelle": label(r), "Einzelübertragungen": r["transfers"], "Banzhaf: Fälle": r["cases_b"], "Shapley–Shubik: Fälle": r["cases_s"],
                                    "Instanzen mit Fall (Banzhaf)": r["instances_b"]} for r in donors]), hide_index=True, width="stretch")
        show(verdict_donor(donors))
        st.markdown("**Zwei Mitglieder zusammenlegen** (alle 15 Paare)")
        st.dataframe(pd.DataFrame([{"Zelle": label(r), "Paare": r["pairs"], "Banzhaf: Block hat weniger": r["less_b"], "Banzhaf: mehr": r["more_b"], "Shapley–Shubik: weniger": r["less_s"],
                                    "Shapley–Shubik: mehr": r["more_s"], "Richtung verschieden": r["differ"]} for r in merges]), hide_index=True, width="stretch")
        show(verdict_merge(merges))
        st.markdown("**Ein Mitglied aufspalten** (Gewicht mindestens 2)")
        st.dataframe(pd.DataFrame([{"Zelle": label(r), "Fälle": r["cases"], "Banzhaf: beide zusammen mehr": r["more_b"], "Banzhaf: weniger": r["less_b"], "Shapley–Shubik: mehr": r["more_s"],
                                    "Shapley–Shubik: weniger": r["less_s"]} for r in splits]), hide_index=True, width="stretch")
        show(verdict_split(splits))
        st.markdown("**Neues Mitglied** (Quote mit demselben Anteil p neu bestimmt; kein Befund, nur Zählung)")
        st.dataframe(pd.DataFrame([{"Zelle": label(r), "Instanzen": r["instances"], "Banzhaf: ein altes gewinnt Anteil": r["gain_b"], "Shapley–Shubik: ein altes gewinnt Anteil": r["gain_s"]} for r in newcomers]),
                     hide_index=True, width="stretch")
        show(verdict_new_member(newcomers))

# ---- Tab 6 ----------------------------------------------------------------------------------------------------------------------------------
with tab_count:
    st.markdown("Die Aufzählung aller Koalitionen wächst mit **2ⁿ**; die Zählung per dynamischer Programmierung wächst mit der **Gewichtssumme** und rechnet 60 Mitglieder bei kleiner Gewichtssumme in Millisekunden, bei Gewichtssumme 100.000 in rund einer Sekunde (je nach Rechner). Hier die Zahlen für die eingestellte Genossenschaft.")
    dp_s, enum_s = _timing(a.weights, a.quota)
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Koalitionen (2ⁿ)", th(2 ** a.n) if a.n <= 60 else "sehr viele")
    t2.metric("Zählfeld", f"{de((a.n + 1) * (a.total + 1) * 8 / 1e6, 2)} MB", delta="(n + 1) × (Summe + 1) × 8 Byte", delta_color="off")
    t3.metric("Zählung (DP)", f"{de(dp_s * 1000, 1)} ms")
    t4.metric("Aufzählung", "nicht gerechnet" if enum_s is None else f"{de(enum_s * 1000, 1)} ms", delta=None if enum_s is not None else "n > 20", delta_color="off")
    st.caption("Zeiten: ein Lauf, hängt an Rechner und Auslastung. Die Aufzählung (Gewinntabelle mit numpy) wird nur bis n = 20 gerechnet.")
    st.subheader("🔬 Experiment: Laufzeit über n und Gewichtssumme, und Rundung auf ganze Gewichte")
    st.caption("Gewichte gleichverteilt von 1 bis zum größten Gewicht, Quote mehr als die Hälfte; je Zeile ein Lauf. Dazu 200 reelle lognormale Gewichtsvektoren (n = 8), auf ganze Zahlen gerundet.")

    def _e6():
        dp_rows = [E.runtime_row(n, mw) for n, mw in ((14, 20), (30, 20), (60, 20), (30, 100), (30, 1000), (30, 10000))]
        enum_rows = [E.enumeration_row(n, 20) for n in (14, 18, 20)]
        return dp_rows, enum_rows, E.raster_series()

    result = run_experiment("e6", "🔬 Laufzeit und Raster messen", _e6, "Misst die Zählung und rundet 200 Gewichtsvektoren …")
    if result:
        dp_rows, enum_rows, raster = result
        st.dataframe(pd.DataFrame([{"n": r["n"], "größtes Gewicht": r["max_weight"], "Gewichtssumme": r["total"], "Zählung (ms)": 1000 * r["seconds"]} for r in dp_rows]), hide_index=True, width="stretch",
                     column_config={"Zählung (ms)": st.column_config.NumberColumn("Zählung (ms)", format="%.1f")})
        st.dataframe(pd.DataFrame([{"n": r["n"], "Gewichtssumme": r["total"], "Aufzählung (ms)": 1000 * r["seconds"]} for r in enum_rows]), hide_index=True, width="stretch",
                     column_config={"Aufzählung (ms)": st.column_config.NumberColumn("Aufzählung (ms)", format="%.1f")})
        show(verdict_runtime(dp_rows))
        st.dataframe(pd.DataFrame([{"Raster (Gewichtssumme)": r["total"], "mittlere größte Abweichung (Prozentpunkte)": r["mean_worst_pp"], "Instanzen über 1 Prozentpunkt": r["over_1pp"], "Instanzen": r["count"]} for r in raster]),
                     hide_index=True, width="stretch",
                     column_config={"mittlere größte Abweichung (Prozentpunkte)": st.column_config.NumberColumn("mittlere größte Abweichung (Prozentpunkte)", format="%.3f")})
        st.caption("Bezug ist das feine Raster 100.000; es ist selbst nur eine Näherung der reellen Gewichte und misst die Rasterstufe, nicht den „wahren“ Wert.")
        show(verdict_raster(raster))

# ---- Tab 7 ----------------------------------------------------------------------------------------------------------------------------------
with tab_board:
    st.markdown("Ein Beirat verteilt Sitze auf Verbände nach deren Mitgliederzahl; beschlossen wird mit mehr als der Hälfte der Sitze. Die **Sitze** sind das Gewicht, und die **Macht** der Sitze weicht in den Zufallsreihen unten stärker vom Mitgliederanteil ab als die Sitze selbst.")
    st.session_state.setdefault("board_members", C.BOARD_MEMBERS)
    st.session_state.setdefault("board_seats", C.BOARD_SEATS_DEFAULT)
    bc1, bc2, bc3 = st.columns([3, 1, 1])
    board_text = bc1.text_input("Mitglieder je Verband", key="board_members")
    board_seats = bc2.slider("Sitze", C.BOARD_SEATS_MIN, C.BOARD_SEATS_MAX, key="board_seats")
    board_method = bc3.selectbox("Verfahren", ST.METHODS, key="board_method")
    bm, berr = S.parse_weights(board_text)
    if berr or len(bm) > 12:
        st.error(berr or "Höchstens 12 Verbände.")
    else:
        members_b = list(bm)
        alloc = {m: ST.allocate(members_b, board_seats, m) for m in ST.METHODS}
        power = {m: ST.seat_power(alloc[m]) for m in ST.METHODS}
        share = G.weight_shares(members_b)
        st.dataframe(
            pd.DataFrame({"Verband": [f"V{i + 1}" for i in range(len(members_b))], "Mitglieder": members_b, "Mitgliederanteil": [100 * x for x in share],
                          **{f"Sitze {m}": alloc[m] for m in ST.METHODS},
                          f"Macht Banzhaf ({board_method})": [100 * x for x in power[board_method][0]], f"Macht Shapley–Shubik ({board_method})": [100 * x for x in power[board_method][1]]}),
            hide_index=True, width="stretch",
            column_config={"Mitgliederanteil": percent_column("Mitgliederanteil"), f"Macht Banzhaf ({board_method})": percent_column(f"Macht Banzhaf ({board_method})"),
                           f"Macht Shapley–Shubik ({board_method})": percent_column(f"Macht Shapley–Shubik ({board_method})")},
        )
        show(verdict_board(members_b, alloc[board_method], power[board_method][0], power[board_method][1], board_method, board_seats))
        biggest = max(range(len(members_b)), key=lambda i: (members_b[i], -i))
        exact = members_b[biggest] * board_seats / sum(members_b)
        lo, hi = max(1, math.floor(exact) - 4), min(board_seats, math.ceil(exact) + 3)
        if len(members_b) >= 2 and lo <= hi:
            st.plotly_chart(build_staircase(ST.staircase(members_b, biggest, board_seats, lo, hi), share[biggest]), width="stretch", key="staircase_chart")
            st.caption(f"Macht des größten Verbands (V{biggest + 1}), wenn er {lo} bis {hi} Sitze bekommt und die übrigen Sitze per Hamilton an die anderen gehen; seine Quote ist {de(exact, 2)} Sitze.")
    st.subheader("🔬 Experiment: Wie weit weicht die Macht der Sitze vom Mitgliederanteil ab?")
    st.caption("Acht Verbände mit lognormalen Mitgliederzahlen (σ = 1,2 und σ = 0,5), 16, 24, 48 und 64 Sitze; je Zeile vier feste Zufalls-Seeds mit je 75 Instanzen.")

    def _e5():
        return {sigma: [r for h in (16, 24, 48, 64) for r in E.seats_series(sigma, h)] for sigma in (1.2, 0.5)}

    result = run_experiment("e5", "🔬 Sitze und Macht vergleichen", _e5, "Verteilt Sitze in 2.400 Instanzen (je drei Verfahren) …")
    if result:
        for sigma, rows in result.items():
            st.markdown(f"**σ = {de(sigma)}**")
            st.dataframe(pd.DataFrame([{"Sitze": r["seats"], "Verfahren": r["method"], "Abweichung der Sitze": 100 * r["d_seat"], "Abweichung der Macht (Banzhaf)": 100 * r["d_banzhaf"],
                                        "Abweichung der Macht (Shapley–Shubik)": 100 * r["d_shapley_shubik"], "Instanzen mit Diktator": r["dictators"], "Instanzen": r["count"]} for r in rows]),
                         hide_index=True, width="stretch",
                         column_config={k: points_column(k) for k in ("Abweichung der Sitze", "Abweichung der Macht (Banzhaf)", "Abweichung der Macht (Shapley–Shubik)")})
        st.caption("Abweichungen vom Mitgliederanteil in Prozentpunkten (halbe Summe der Beträge), Mittel über die Instanzen; „Diktator“: ein Verband hat die ganze Macht (Shapley–Shubik gleich 1).")
        show(verdict_seats_series(result))

st.markdown("---")

# --- Expander ---------------------------------------------------------------------------------------------------------------------------------

with st.expander("Harsanyi-Dividenden: die Zerlegung in Einstimmigkeitsspiele"):
    st.markdown(T.HARSANYI_MARKDOWN)
    example_win = G.win_vector([4, 3, 2, 1], 6)
    example_d = H.dividends(example_win, 4)
    letters = "ABCD"
    st.dataframe(pd.DataFrame([{"Gruppe T": "{" + ",".join(letters[i] for i in range(4) if m >> i & 1) + "}", "Dividende Δ(T)": v} for m, v in H.nonzero_dividends(example_d)]),
                 hide_index=True, width="stretch")
    shap, banz = H.indices_from_dividends(example_d, 4)
    st.caption("Aus den Dividenden: Shapley–Shubik-Werte " + ", ".join(f"{letters[i]} = {shap[i]}" for i in range(4)) + "; Schwingzahl durch 2³ (unnormierter Banzhaf-Wert) " + ", ".join(f"{letters[i]} = {banz[i]}" for i in range(4)) + ".")

with st.expander("Owen-Wert: Zusammenschluss nicht immer vorteilhaft"):
    st.markdown("""
Der **Owen-Wert** erweitert den Shapley-Wert um **Gruppen**: Mitglieder verhandeln erst in ihrer Gruppe, dann treten die Gruppen als Ganzes ein. Schließen sich zwei Gruppen zusammen, fragt man: bekommen sie danach zusammen mehr?
Die Aussage „ein Zusammenschluss ist beim Owen-Wert immer vorteilhaft“ steht in Abschnitt 3.1 von arXiv 2304.10002 (Gómez-Rodríguez, Davila-Pena und Casas-Méndez, über die HTML-Fassung gelesen), das sich dort auf Vázquez-Brage u. a. (1997) beruft, für **Flughafenprobleme** mit Gruppen, ein Kostenspiel; die Arbeit von 1997 selbst wurde nicht gelesen. Hier gemessen, ob sie auch für ein **Abstimmungsspiel** gilt: Gewichte 1 bis 9, Quote über der Hälfte, zufällige Gruppen (aus Mustern wie 2 + 2 + 1 Mitglieder), zwei zufällige Gruppen werden zusammengelegt.
Handbeispiel: bei einfacher Mehrheit mit drei Spielern und den Gruppen {1,2} und {3} ist der Owen-Wert (1/2, 1/2, 0), der Shapley-Wert 1/3 je Spieler.
""")
    result = run_experiment("owen", "🔬 Zusammenschlüsse zählen", lambda: (E.owen_merge_series("vote", 6, 300), E.owen_merge_series("airport", 6, 300)), "Rechnet 600 Zusammenschlüsse mit exakten Brüchen …")
    if result:
        show(verdict_owen(*result))
        st.caption("Zufalls-Seed 7; die Formel des Owen-Werts steht in `mdx_owen.py` und ist gegen die Definition über alle Reihenfolgen geprüft.")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(T.ASSUMPTIONS_MARKDOWN)

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(T.LIMITS_MARKDOWN)

with st.expander("🚧 Bewusst nicht umgesetzt"):
    st.markdown(T.NOT_IMPLEMENTED_MARKDOWN)

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/machtindex-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind $n$ Mitglieder mit ganzzahligen Gewichten und eine Quote. Gesucht ist für jedes Mitglied, wie oft es für den Beschluss entscheidend ist.

| Symbol | Bedeutung |
|---|---|
| $N = \{1, \dots, n\}$ | die Mitglieder |
| $w_i$ | Gewicht (Stimmen) von Mitglied $i$, ganzzahlig und mindestens 1 |
| $W = \sum_i w_i$ | Gesamtgewicht |
| $p$ | Beschlussquote als Anteil, $0{,}5 \le p \le 1$ |
| $q$ | Quote als ganze Zahl: kleinste ganze Zahl mit $q > pW$, bei $p = 1$ gilt $q = W$ |
| $v(S)$ | Wert einer Koalition $S$: 1, wenn $\sum_{i \in S} w_i \ge q$, sonst 0 |
| $\eta_i$ | Schwingzahl von $i$ (Zahl der Koalitionen, in denen $i$ entscheidend ist) |
| $\beta_i,\ \varphi_i$ | Banzhaf-Anteil und Shapley–Shubik-Anteil von $i$ |
| $C(s,k)$ | Zahl der Teilmengen der Größe $s$ mit Gewichtssumme $k$ |
| $D_i(s,k)$ | dasselbe ohne das Mitglied $i$ |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/machtindex-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(T.MATH_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Koalitionen und Teilen: Macht und Aufteilung](https://sebastianhanisch.net/konzepte-koalitionen-teilen.html)."
)
