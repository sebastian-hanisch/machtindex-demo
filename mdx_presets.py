"""Permalink (Begrenzen), Presets und der Zufalls-Button.

Die Gewichte der Genossenschaft stehen als Text im Regler `weights_text`; Erzeuger, n und Zufalls-Seed gehören zum Knopf „Gewichte erzeugen“, der den Text überschreibt
(so gibt es genau eine Quelle der Wahrheit und keinen Regler, der je nach Modus ohne Wirkung ist)."""

import time
from dataclasses import dataclass

import streamlit as st

import mdx_constants as C
import mdx_scenario as S
from mdx_rng import SplitMix64


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    choices: tuple | None = None


SETTING_SPECS = {
    "weights_text": SettingSpec("w", str, C.DEFAULT_WEIGHTS),
    "p_slider": SettingSpec("p", float, C.DEFAULT_P, C.P_MIN, C.P_MAX),
    "gen_select": SettingSpec("gen", str, C.DEFAULT_GENERATOR, choices=S.generator_keys()),
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"weights": "weights_text", "p": "p_slider"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param not in qp:
            continue
        try:
            value = spec.caster(qp[spec.url_param])
        except (ValueError, TypeError):
            continue
        if spec.lo is not None:
            value = max(spec.lo, value)
        if spec.hi is not None:
            value = min(spec.hi, value)
        if spec.choices is not None and value not in spec.choices:
            continue
        if isinstance(value, float):
            value = round(value, 1)
        if isinstance(value, str):
            value = value[: C.TEXT_MAX_CHARS]
        st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    """Setzt Gewichte und Quote des Presets; Erzeuger, n und Zufalls-Seed gehen auf ihre Voreinstellung zurück (sonst bliebe die Markierung des Presets aus)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for state_key, spec in SETTING_SPECS.items():
        st.session_state[state_key] = C.PRESETS[name].get(preset_key_of.get(state_key), spec.default)


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen Standardwert) mit dem Session State."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def generate_weights():
    """Knopf „Gewichte erzeugen“: schreibt Gewichte aus Erzeuger, n und Zufalls-Seed in das Textfeld."""
    st.session_state["weights_text"] = S.weights_text(
        S.make_weights(st.session_state["gen_select"], int(st.session_state["n_slider"]), int(st.session_state["seed_input"]))
    )


def randomize_seed():
    st.session_state["seed_input"] = SplitMix64(time.time_ns()).next() % (C.SEED_MAX + 1)       # nur für den Knopf; alle Befunde laufen über feste Zufalls-Seeds
    generate_weights()
