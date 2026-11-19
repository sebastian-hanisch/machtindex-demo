"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import mdx_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_power(a):
    """Stimmanteil, Banzhaf-Anteil und Shapley–Shubik-Anteil je Mitglied (Beschriftung M1, M2 ... als Text, damit Plotly keine lineare Achse anlegt)."""
    labels = [f"M{i + 1}" for i in range(a.n)]
    fig = go.Figure()
    for title, values, color in (("Stimmanteil", a.vote_share, C.COLOR_WEIGHT), ("Macht nach Banzhaf", a.banzhaf, C.COLOR_BANZHAF),
                                 ("Macht nach Shapley–Shubik", a.shapley_shubik, C.COLOR_SHAPLEY)):
        fig.add_trace(go.Bar(x=labels, y=[100 * v for v in values], name=title, marker_color=color, hovertemplate="%{x}: %{y:.1f} %<extra>" + title + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Anteil (%)")
    return _base(fig)


def build_generator_lines(rows, n):
    """E1: mittlere Abweichung Macht gegen Stimmanteil (Prozentpunkte) über die Quote p, eine Linie je Erzeuger, für die Mitgliederzahl n."""
    fig = go.Figure()
    for gen in dict.fromkeys(r["gen"] for r in rows):
        cells = [r for r in rows if r["gen"] == gen and r["n"] == n]
        fig.add_trace(go.Scatter(x=[r["permille"] / 10 for r in cells], y=[100 * r["dB"] for r in cells], mode="lines+markers", name=C.GENERATOR_LABELS[gen],
                                 hovertemplate="p = %{x} %: %{y:.1f} Prozentpunkte<extra>" + C.GENERATOR_LABELS[gen] + "</extra>"))
    fig.update_xaxes(title_text="Beschlussquote p (%)")
    fig.update_yaxes(title_text="Abweichung Macht gegen Stimmanteil (Prozentpunkte)")
    return _base(fig)


def build_quote_members(percents, shares_by_member, labels):
    """Banzhaf-Anteil je Mitglied über die Quote p; `labels` beschriftet die Linien."""
    fig = go.Figure()
    for i, series in enumerate(shares_by_member):
        fig.add_trace(go.Scatter(x=percents, y=[100 * v for v in series], mode="lines+markers", name=labels[i],
                                 hovertemplate="p = %{x} %: %{y:.1f} %<extra>" + labels[i] + "</extra>"))
    fig.update_xaxes(title_text="Beschlussquote p (%)")
    fig.update_yaxes(title_text="Macht nach Banzhaf (%)")
    return _base(fig)


def build_quote_curve(rows):
    """E2: mittlere Abweichung Macht gegen Stimmanteil über die Quote p für Banzhaf (eine Linie je Erzeuger, `rows` = {gen: Zeilen von quote_curve})."""
    fig = go.Figure()
    for gen, curve in rows.items():
        fig.add_trace(go.Scatter(x=[r["percent"] for r in curve], y=[100 * r["dB"] for r in curve], mode="lines+markers", name=C.GENERATOR_LABELS[gen],
                                 hovertemplate="p = %{x} %: %{y:.1f} Prozentpunkte<extra>" + C.GENERATOR_LABELS[gen] + "</extra>"))
    fig.update_xaxes(title_text="Beschlussquote p (%)")
    fig.update_yaxes(title_text="Abweichung Macht gegen Stimmanteil (Prozentpunkte)")
    return _base(fig)


def build_staircase(rows, members_share):
    """Beirat: Macht des größten Verbands (Banzhaf, Shapley–Shubik) gegen seine Sitzzahl; gestrichelt sein Sitzanteil."""
    xs = [r[0] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[100 * r[1] for r in rows], mode="lines", line=dict(dash="dash", color=C.COLOR_WEIGHT), name="Sitzanteil",
                             hovertemplate="%{x} Sitze: %{y:.1f} %<extra>Sitzanteil</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[100 * r[2] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_BANZHAF), name="Macht nach Banzhaf",
                             hovertemplate="%{x} Sitze: %{y:.1f} %<extra>Banzhaf</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[100 * r[3] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_SHAPLEY), name="Macht nach Shapley–Shubik",
                             hovertemplate="%{x} Sitze: %{y:.1f} %<extra>Shapley–Shubik</extra>"))
    fig.add_hline(y=100 * members_share, line=dict(color=C.COLOR_LINE, dash="dot"), annotation_text="Mitgliederanteil", annotation_position="bottom right")
    fig.update_xaxes(title_text="Sitze des größten Verbands")
    fig.update_yaxes(title_text="Anteil (%)", range=[0, 105])
    return _base(fig)


def build_index_gap(a):
    """Shapley–Shubik-Anteil minus Banzhaf-Anteil je Mitglied in Prozentpunkten."""
    labels = [f"M{i + 1}" for i in range(a.n)]
    gaps = [100 * (s - b) for s, b in zip(a.shapley_shubik, a.banzhaf)]
    fig = go.Figure(go.Bar(x=labels, y=gaps, marker_color=[C.COLOR_SHAPLEY if g >= 0 else C.COLOR_BANZHAF for g in gaps],
                           hovertemplate="%{x}: %{y:+.2f} Prozentpunkte<extra></extra>"))
    fig.update_yaxes(title_text="Shapley–Shubik minus Banzhaf (Prozentpunkte)")
    return _base(fig, 300)
