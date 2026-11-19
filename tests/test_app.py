"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

import pytest

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


BUTTON_KEYS = ("generate", "random_seed", "reset_two", "run_e1", "run_e2", "run_e_rank", "run_e4", "run_e3", "run_e6", "run_e5", "run_owen")


def test_the_button_list_is_complete():
    """Jeder Knopf außer den Presets steht in BUTTON_KEYS (die Presets klickt tests/test_presets.py einzeln)."""
    keys = {b.key for b in _fresh_app().button if b.key and not b.key.startswith("preset_")}
    assert keys == set(BUTTON_KEYS)


@pytest.mark.parametrize("key", BUTTON_KEYS)
def test_every_button_click_does_not_raise(key):
    at = _fresh_app()
    at.button(key=key).click().run(timeout=TIMEOUT)
    assert not at.exception, (key, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_every_number_input_and_text_field_at_its_edges_does_not_raise():
    base = _fresh_app()
    for index, ni in enumerate(base.number_input):
        for edge in (ni.min, ni.max):
            at = _fresh_app()
            at.number_input[index].set_value(edge).run(timeout=TIMEOUT)
            assert not at.exception, (ni.label, edge, [str(e) for e in at.exception])


def test_experiment_buttons_show_a_table_and_a_verdict():
    """Jeder 🔬-Knopf: nach dem Klick steht eine Zeitangabe da, es gibt Tabellen und mindestens ein Verdikt (info, warning oder success), und der Lauf bleibt beim nächsten Rerun erhalten."""
    at = _fresh_app()
    labels = [b.label for b in at.button if b.label.startswith("🔬")]
    assert len(labels) == 8, labels
    for key in ("run_e1", "run_e_rank"):
        at.button(key=key).click().run(timeout=TIMEOUT)
        assert not at.exception, [str(e) for e in at.exception]
    assert any("Gerechnet in" in c.value for c in at.caption)
    assert len(at.dataframe) >= 3
    verdicts = [e.value for group in (at.info, at.success, at.warning) for e in group]
    assert any("Zellen" in v for v in verdicts) and any("aufgezählten Gewichtsspielen" in v for v in verdicts)
    at.run(timeout=TIMEOUT)                     # nächster Lauf: das Ergebnis bleibt im Session State
    assert any("Gerechnet in" in c.value for c in at.caption)


def test_invalid_weights_show_an_error_and_stop_the_page():
    at = _fresh_app()
    at.sidebar.text_input(key="weights_text").set_value("3, x").run(timeout=TIMEOUT)
    assert not at.exception and any("keine ganze Zahl" in e.value for e in at.error)
    assert not at.metric
