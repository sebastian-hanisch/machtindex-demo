"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink; jedes Preset ergibt die dokumentierte Machtverteilung."""

from pathlib import Path

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import mdx_constants as C
import mdx_evaluation as ev
import mdx_presets as P
import mdx_scenario as S

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_every_preset_has_help_and_only_known_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_parse():
    for name, preset in C.PRESETS.items():
        weights, error = S.parse_weights(preset["weights"])
        assert error is None, name
        assert C.P_MIN <= preset["p"] <= C.P_MAX


def test_default_preset_equals_the_default_settings():
    first = C.PRESETS[next(iter(C.PRESETS))]
    assert first["weights"] == C.DEFAULT_WEIGHTS and first["p"] == C.DEFAULT_P


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) <= set(P.SETTING_SPECS)


# Erwartete Verdikt-Art je Preset (§11a Punkt 7: jedes Preset durchläuft die Verdikte, ein Preset ohne Effekt meldet keinen Effekt)
EXPECTED_KIND = {
    "Fuhrpark 7, einfache Mehrheit (Voreinstellung)": "info",        # Abweichung 17,5 Prozentpunkte, kein Veto, kein Nullspieler
    "Fuhrpark 7, mehr als zwei Drittel": "info",                     # Vetospieler M1
    "Ein Großer, fünf Kleine": "info",                               # Abweichung 12,5 Prozentpunkte
    "Banzhaf ≠ Shapley–Shubik": "info",                              # Vetospieler M1
    "Nullspieler": "warning",
    "Diktator": "warning",
    "Spenderparadox": "info",                                        # Vetospieler M5
    "Einstimmigkeit": "info",                                        # alle Vetospieler
    "EU-Rat Nizza (nur Stimmbedingung)": "success",                  # Abweichung 3,3 Prozentpunkte
    "Beirat: 40 Sitze nach Hamilton": "info",                        # Abweichung 33,2 Prozentpunkte
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_through_the_verdict_with_the_expected_kind(name):
    preset = C.PRESETS[name]
    weights, _ = S.parse_weights(preset["weights"])
    a = ev.analyse(ev.Settings(weights, ev.permille_of(preset["p"])))
    kind, text = ev.verdict_power(a)
    assert kind == EXPECTED_KIND[name] and text


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_clicking_a_preset_loads_its_weights_and_quote(name):
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception
    assert at.sidebar.text_input(key="weights_text").value == C.PRESETS[name]["weights"]
    assert at.sidebar.slider(key="p_slider").value == C.PRESETS[name]["p"]


def test_permalink_loads_and_clamps_the_values():
    at = AppTest.from_file(APP, default_timeout=180)
    at.query_params["w"] = "5, 1, 1, 1"
    at.query_params["p"] = "20"          # unter der Grenze: wird auf 50 begrenzt
    at.query_params["gen"] = "gibt-es-nicht"
    at.query_params["n"] = "7"
    at.run()
    assert not at.exception
    assert at.sidebar.text_input(key="weights_text").value == "5, 1, 1, 1"
    assert at.sidebar.slider(key="p_slider").value == 50.0
    assert at.sidebar.selectbox(key="gen_select").value == C.DEFAULT_GENERATOR       # unbekannte Auswahl wird ignoriert
    assert at.sidebar.slider(key="n_slider").value == 7


def test_the_generate_button_writes_generated_weights_into_the_text_field():
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    at.sidebar.selectbox(key="gen_select").select("stepped")
    at.sidebar.slider(key="n_slider").set_value(9)
    at.sidebar.number_input(key="seed_input").set_value(1234)
    at.sidebar.button(key="generate").click().run()
    assert at.sidebar.text_input(key="weights_text").value == S.weights_text(S.make_weights("stepped", 9, 1234))
    assert not at.exception
