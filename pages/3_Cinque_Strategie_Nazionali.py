"""
Pagina 3 — Strategie nazionali a confronto (Esplora)
=======================================================
Confronto libero testa-a-testa tra due paesi. Eredita dal vecchio "Cinque strategie
nazionali" (Cap. 4.3) l'idea che la media europea nasconda traiettorie molto diverse,
ma la apre a scelta dell'utente: due paesi qualunque del panel bilanciato invece di
cinque profili fissi. Da qui la ricollocazione tra le pagine Esplora.

La pagina alterna due registri:
- sezioni **in due colonne** (una per paese) per ciò che si legge meglio in parallelo
  ma non si può sovrapporre: lo scoreboard KPI e la composizione impilata del mix (due
  stack di paesi diversi non stanno sullo stesso grafico);
- una sezione **unificata** (due linee sullo stesso asse) per le metriche scalari-per-anno,
  dove la sovrapposizione diretta è proprio il confronto — con un selettore di metrica che
  è la parte di esplorazione libera vera e propria — più la crescita di una fonte nel tempo
  (valore assoluto o indice 1990 = 100, ex pagina "Velocità di crescita" confluita qui: la
  crescita è un dato come gli altri, non una lezione a sé).

Vincolata al panel bilanciato (33 paesi, 1990-2022) come le altre pagine di confronto:
serie complete = confronto onesto. Svizzera e Islanda restano aggiungibili a parte, con
avviso, come altrove (Cap. 4.1 del notebook).
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import (
    EXTRA_COUNTRIES,
    PALETTE,
    SOURCE_NOTE,
    get_balanced_panel,
    get_extended_panel,
    limit_page_width,
    load_raw_data,
)

# Identità dei due paesi nei grafici unificati: due tinte Okabe-Ito distinte e visibili in
# dark mode (blu / vermiglio). Non sono i colori delle fonti — qui il colore = il paese.
COUNTRY_COLORS = ("#0072B2", "#D55E00")

# Scoreboard: (etichetta, colonna, unità, verso "buono"). delta_color="inverse" dove un calo
# è un miglioramento (fossile, intensità di carbonio), "normal" dove lo è una crescita.
KPI = [
    ("Quota fossile", "fossil_share_elec", "%", "inverse"),
    ("Quota nucleare", "nuclear_share_elec", "%", "normal"),
    ("Quota rinnovabili", "renewables_share_elec", "%", "normal"),
    ("Intensità di carbonio", "carbon_intensity_elec", "gCO₂/kWh", "inverse"),
]

MIX_SOURCES = [("Fossile", "fossile"), ("Nucleare", "nucleare"), ("Rinnovabili", "rinnovabili")]
MIX_COLOR_MAP = {label: PALETTE[key] for label, key in MIX_SOURCES}

# Metriche confrontabili come due linee sullo stesso asse. (colonna, unità, is_pct, is_assoluta).
# is_pct → asse 0-100; le assolute (TWh) riflettono anche la dimensione del paese: avviso e
# niente riferimento Europa (schiaccerebbe la scala).
COMPARE_METRICS = {
    "Intensità di carbonio (gCO₂/kWh)": ("carbon_intensity_elec", "gCO₂/kWh", False, False),
    "Quota fossile (%)": ("fossil_share_elec", "%", True, False),
    "Quota nucleare (%)": ("nuclear_share_elec", "%", True, False),
    "Quota rinnovabili (%)": ("renewables_share_elec", "%", True, False),
    "Quota low-carbon — nucleare + rinnovabili (%)": ("low_carbon_share_elec", "%", True, False),
    "Elettricità pro-capite (kWh)": ("per_capita_electricity", "kWh/persona", False, False),
    "Emissioni pro-capite, settore elettrico (t CO₂eq)": ("ghg_per_capita_elec", "t CO₂eq/persona", False, False),
    "Generazione totale (TWh)": ("electricity_generation", "TWh", False, True),
}

# Crescita di una fonte nel tempo (assoluta o indicizzata al primo anno = 100).
GROWTH_SOURCES = {
    "Rinnovabili": "renewables_electricity",
    "Fossile": "fossil_electricity",
    "Nucleare": "nuclear_electricity",
    "Generazione totale": "electricity_generation",
}

_, COMPLETE_COUNTRIES, _ = get_balanced_panel()


def _with_derived(df):
    """Aggiunge le emissioni pro-capite del settore elettrico (OWID dà solo il totale Mt CO₂eq)."""
    df = df.copy()
    df["ghg_per_capita_elec"] = df["greenhouse_gas_emissions"] * 1e6 / df["population"]
    return df


def render_scoreboard(country: str, d_idx) -> None:
    """Quattro KPI tile (valore ultimo anno + variazione dal primo) per un paese, in griglia 2×2."""
    st.markdown(f"#### {country}")
    cells = st.columns(2) + st.columns(2)
    for cell, (label, col, unit, mode) in zip(cells, KPI):
        s = d_idx[col].dropna() if col in d_idx.columns else d_idx.get(col)
        if s is None or s.empty:
            cell.metric(label, "n.d.")
            continue
        first, last = float(s.iloc[0]), float(s.iloc[-1])
        delta = last - first
        value = f"{last:.0f}%" if unit == "%" else f"{last:.0f} {unit}"
        delta_str = f"{delta:+.1f} pp" if unit == "%" else f"{delta:+.0f}"
        cell.metric(
            label, value, delta=delta_str, delta_color=mode,
            help=f"{int(s.index.min())} → {int(s.index.max())}: da {first:.0f} a {last:.0f} {unit}",
        )


def mix_figure(d_c, country: str, mode: str) -> go.Figure:
    """Area impilata del mix (quota % o TWh) per un singolo paese."""
    if mode == "Quota (%)":
        cols = [("Fossile", "fossil_share_elec"), ("Nucleare", "nuclear_share_elec"), ("Rinnovabili", "renewables_share_elec")]
        y_title, y_range = "% della generazione", [0, 100]
    else:
        cols = [("Fossile", "fossil_electricity"), ("Nucleare", "nuclear_electricity"), ("Rinnovabili", "renewables_electricity")]
        y_title, y_range = "TWh", None

    long = d_c[["year"] + [c for _, c in cols]].melt(id_vars="year", var_name="col", value_name="v")
    long["fonte"] = long["col"].map({c: label for label, c in cols})
    long = long.dropna(subset=["v"])

    fig = px.area(
        long, x="year", y="v", color="fonte", color_discrete_map=MIX_COLOR_MAP,
        category_orders={"fonte": [label for label, _ in cols]},
        labels={"year": "", "v": y_title, "fonte": ""}, title=country, template="plotly_white",
    )
    if y_range:
        fig.update_yaxes(range=y_range)
    else:
        fig.update_yaxes(rangemode="tozero")
    fig.update_layout(height=380, legend=dict(orientation="h", yanchor="bottom", y=1.02), margin=dict(t=60))
    return fig


def europe_reference(col: str, years) -> "tuple | None":
    """Serie dell'aggregato OWID 'Europe' per la stessa metrica, come riferimento (o None)."""
    raw = load_raw_data()
    e = raw[raw["country"] == "Europe"].copy()
    if col == "ghg_per_capita_elec":
        e[col] = e["greenhouse_gas_emissions"] * 1e6 / e["population"]
    if col not in e.columns:
        return None
    s = e.set_index("year")[col].dropna()
    s = s[s.index.isin(years)]
    return (s.index, s.values) if not s.empty else None


def main() -> None:
    limit_page_width()
    st.title("🆚 Strategie nazionali a confronto")
    st.markdown(
        "La media europea nasconde traiettorie opposte: chi ha puntato sul nucleare, chi sulle "
        "rinnovabili, chi è ancora legato al fossile. Scegli **due paesi** e mettili testa a testa "
        "— prima i numeri chiave, poi i mix affiancati, infine il confronto diretto su una metrica "
        "a tua scelta."
    )

    with st.expander("⚙️ Opzioni"):
        include_extra = st.checkbox(
            "Includi Svizzera e Islanda (serie incomplete 1990-2022, profili estremi)",
            value=False,
            help="Esclusi dal panel bilanciato nel resto dell'app: Svizzera nucleare+idro, Islanda 100% rinnovabile.",
        )

    data = _with_derived(get_extended_panel(EXTRA_COUNTRIES if include_extra else []))
    options = sorted(data["country"].unique())

    c1, c2 = st.columns(2)
    country_a = c1.selectbox("Paese A", options, index=options.index("France"))
    country_b = c2.selectbox("Paese B", options, index=options.index("Germany"))
    if country_a == country_b:
        st.warning("⚠️ Hai scelto lo stesso paese in entrambi gli slot: il confronto sarà con sé stesso.")

    da = data[data["country"] == country_a].sort_values("year")
    db = data[data["country"] == country_b].sort_values("year")

    # --- Scoreboard: due colonne, una per paese ---
    st.subheader("Scheda sintetica")
    st.caption("Valore al 2022 e variazione dal primo anno disponibile (di norma il 1990). Freccia verde = miglioramento.")
    col_a, col_b = st.columns(2)
    with col_a:
        render_scoreboard(country_a, da.set_index("year"))
    with col_b:
        render_scoreboard(country_b, db.set_index("year"))

    st.divider()

    # --- Composizione del mix: due colonne, una per paese, stessa scala ---
    st.subheader("Composizione del mix elettrico")
    mode = st.radio(
        "Come rappresentare il mix", ["Quota (%)", "Composizione (TWh)"], horizontal=True,
        help="La quota (%) rende i due paesi direttamente confrontabili; i TWh mostrano anche il divario di dimensione.",
    )
    mcol_a, mcol_b = st.columns(2)
    with mcol_a:
        st.plotly_chart(mix_figure(da, country_a, mode), width="stretch")
    with mcol_b:
        st.plotly_chart(mix_figure(db, country_b, mode), width="stretch")
    st.caption(f"{SOURCE_NOTE} — quote fossile/nucleare/rinnovabili, 1990–2022")

    st.divider()

    # --- Confronto diretto su una metrica: sezione unificata, due linee ---
    st.subheader("Confronto diretto")
    st.markdown(
        "Qui i due paesi stanno **sullo stesso grafico**: scegli una metrica e confronta le due "
        "traiettorie direttamente. Utile soprattutto per gli esiti (intensità di carbonio) e le "
        "quote, dove la distanza tra le linee *è* il confronto."
    )
    metric_label = st.selectbox("Metrica da confrontare", list(COMPARE_METRICS.keys()))
    col, unit, is_pct, is_abs = COMPARE_METRICS[metric_label]

    show_europe = False
    if not is_abs:
        show_europe = st.checkbox("Aggiungi la media europea come riferimento", value=False)

    fig = go.Figure()
    finals = {}
    for country, d_c, color in [(country_a, da, COUNTRY_COLORS[0]), (country_b, db, COUNTRY_COLORS[1])]:
        s = d_c.set_index("year")[col].dropna() if col in d_c.columns else None
        if s is None or s.empty:
            continue
        finals[country] = (int(s.index.max()), float(s.iloc[-1]))
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=country, line=dict(color=color, width=2.8)))

    if show_europe:
        ref = europe_reference(col, da["year"].unique())
        if ref is not None:
            fig.add_trace(go.Scatter(x=ref[0], y=ref[1], name="Europa (OWID)", line=dict(color="#888888", width=1.5, dash="dash")))

    fig.update_layout(
        title=metric_label, yaxis_title=unit, template="plotly_white", height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    if is_pct:
        fig.update_yaxes(range=[0, 100])
    else:
        fig.update_yaxes(rangemode="tozero")
    st.plotly_chart(fig, width="stretch")

    note = f"{SOURCE_NOTE} — panel bilanciato, 1990–2022"
    if is_abs:
        note += " · ⚠️ valore assoluto: riflette anche la dimensione del paese, non solo la strategia"
    st.caption(note)

    # Piccola lettura dinamica del confronto sull'ultimo anno in comune.
    if country_a in finals and country_b in finals:
        ya, va = finals[country_a]
        yb, vb = finals[country_b]
        year = min(ya, yb)
        sa = da.set_index("year")[col].dropna()
        sb = db.set_index("year")[col].dropna()
        if year in sa.index and year in sb.index:
            va, vb = float(sa[year]), float(sb[year])
            higher, lower = (country_a, country_b) if va >= vb else (country_b, country_a)
            hv, lv = (va, vb) if va >= vb else (vb, va)
            gap = hv - lv
            ratio = f" ({hv / lv:.1f}× )" if lv > 0 else ""
            st.markdown(
                f"Nel **{year}**, {metric_label.split(' (')[0].lower()}: **{country_a}** {va:.1f} {unit} · "
                f"**{country_b}** {vb:.1f} {unit}. Divario: **{higher}** più alto di {gap:.1f} {unit}{ratio}."
            )

    st.divider()

    # --- Crescita di una fonte nel tempo: assoluto o indicizzato ---
    st.subheader("Crescita di una fonte nel tempo")
    g1, g2 = st.columns([2, 3])
    growth_source = g1.selectbox("Fonte", list(GROWTH_SOURCES.keys()))
    representation = g2.radio(
        "Come rappresentarla", ["Indice di crescita (1990 = 100)", "Valore assoluto (TWh)"],
        horizontal=True,
        help="L'indice mostra quanto è cresciuta ciascuna fonte rispetto al 1990; il valore assoluto i TWh effettivi.",
    )
    gcol = GROWTH_SOURCES[growth_source]
    as_index = representation.startswith("Indice")

    gfig = go.Figure()
    skipped = []
    for country, d_c, color in [(country_a, da, COUNTRY_COLORS[0]), (country_b, db, COUNTRY_COLORS[1])]:
        s = d_c.set_index("year")[gcol].dropna() if gcol in d_c.columns else None
        if s is None or s.empty:
            continue
        if as_index:
            base = float(s.iloc[0])
            if base <= 0:  # fonte assente nel primo anno (es. nucleare in un paese senza): indice non definito
                skipped.append(country)
                continue
            s = s / base * 100
        gfig.add_trace(go.Scatter(x=s.index, y=s.values, name=country, line=dict(color=color, width=2.8)))

    if as_index:
        gfig.add_hline(y=100, line_dash="dot", line_color="#888888")
        y_title = "Indice (1990 = 100)"
    else:
        y_title = "TWh"
        gfig.update_yaxes(rangemode="tozero")  # l'indice no: la sua ancora di lettura è 100, non 0
    gfig.update_layout(
        title=f"{growth_source} — {'indice di crescita' if as_index else 'valore assoluto (TWh)'}",
        yaxis_title=y_title, template="plotly_white", height=440,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(gfig, width="stretch")
    note = SOURCE_NOTE
    if skipped:
        note = f"Indice non calcolabile per {', '.join(skipped)} (fonte nulla nel 1990). " + note
    st.caption(note)


if __name__ == "__main__":
    main()
