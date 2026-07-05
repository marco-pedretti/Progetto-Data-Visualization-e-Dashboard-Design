"""
Pagina 3: Strategie nazionali a confronto (Esplora)
=======================================================
Confronto libero tra due e quattro paesi (default testa-a-testa). Eredita dai "cinque
profili nazionali" del notebook (una sezione poi rimossa in revisione) l'idea che la media
europea nasconda traiettorie molto diverse, ma la apre a scelta dell'utente: paesi qualunque
invece di cinque profili fissi. Da qui la ricollocazione tra le pagine Esplora.

La pagina alterna due registri, e adatta il numero di colonne ai paesi scelti (2–4):
- sezioni **a colonne** (una per paese) per ciò che si legge meglio in parallelo ma non si
  può sovrapporre: lo scoreboard KPI, la composizione impilata del mix (stack di paesi
  diversi non stanno sullo stesso grafico) e l'import/export elettrico (qui il colore è il
  segno, importatore/esportatore, non il paese, coerente con Scheda Paese);
- una sezione **unificata** (una linea per paese sullo stesso asse) per le metriche scalari-per-anno,
  dove la sovrapposizione diretta è proprio il confronto, con un selettore di metrica che
  è la parte di esplorazione libera vera e propria, più la crescita di una fonte nel tempo
  (valore assoluto o indice 1990 = 100, ex pagina "Velocità di crescita" confluita qui: la
  crescita è un dato come gli altri, non una lezione a sé).

Tutti i paesi europei del dataset sono selezionabili, 1990-2022 (a differenza del panel
bilanciato a serie complete usato nelle pagine Storia): un paese con una serie più corta
mostra semplicemente meno anni nei grafici, invece di sparire dalla scelta.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import (
    EXPORT_COLOR,
    IMPORT_COLOR,
    PALETTE,
    SOURCE_NOTE,
    get_europe_window,
    limit_page_width,
    load_raw_data,
)

# Identità dei paesi nei grafici unificati (Confronto diretto, Crescita): 4 tinte Okabe-Ito ad
# alto contrasto reciproco. Rosa e azzurro cielo (prima versione) sono stati sostituiti perché
# troppo simili/deboli accanto a blu e vermiglio (feedback utente 2026-07-04); questo quartetto
# (blu/vermiglio/verde/giallo) è il sottoinsieme Okabe-Ito con la massima separazione percettiva
# reciproca. Il verde riprende la tinta di PALETTE["rinnovabili"], ma senza ambiguità: questa
# tupla non compare mai nello stesso grafico delle aree per fonte (mix e import/export usano
# altri colori), quindi qui il verde non è mai visto accanto al suo significato "rinnovabili".
COUNTRY_COLORS = ("#0072B2", "#D55E00", "#009E73", "#F0E442")

# Layout adattivo: le sezioni "a colonne" (scoreboard, mix) crescono col numero di paesi tenendo
# ogni colonna larga almeno COL_PX invece di comprimerla; le sezioni di confronto comune (linee
# sovrapposte) restano fisse a UNIFIED_PX a prescindere da quanti paesi si confrontano.
# UNIFIED_PX va tenuto ≤ area utile della pagina al minimo (PAGE_MIN meno il padding di Streamlit,
# ~160px): altrimenti a 2 paesi il wrapper non raggiunge il suo max-width e le sezioni comuni
# risulterebbero più strette che a 4 (verificato via browser headless).
COL_PX = 500
PAGE_MIN = 1100
UNIFIED_PX = 930

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
    "Quota low-carbon: nucleare + rinnovabili (%)": ("low_carbon_share_elec", "%", True, False),
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


def import_export_figure(d_c, country: str) -> "go.Figure | None":
    """Barre di import netto sul fabbisogno (%) per un paese, colorate per segno (non per paese:
    qui il colore = direzione import/export, stesso significato di Scheda Paese)."""
    s = d_c.set_index("year")["net_elec_imports_share_demand"].dropna() if "net_elec_imports_share_demand" in d_c.columns else None
    if s is None or s.empty:
        return None
    bar_colors = [IMPORT_COLOR if v >= 0 else EXPORT_COLOR for v in s.values]
    fig = go.Figure(go.Bar(x=s.index, y=s.values, marker_color=bar_colors))
    fig.add_hline(y=0, line_color="#888888", line_width=1)
    fig.update_layout(
        title=country, yaxis_title="% del fabbisogno", template="plotly_white",
        height=340, margin=dict(t=40),
    )
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
    limit_page_width(PAGE_MIN)  # cap iniziale; sotto viene riadattato al numero di paesi scelti
    # Le sezioni di confronto comune (wrapper con chiave "fw_…") restano larghe UNIFIED_PX e centrate
    # anche quando la pagina si allarga per fare spazio a più colonne-paese.
    st.markdown(
        f'<style>div[class*="st-key-fw_"]{{max-width:{UNIFIED_PX}px;margin-left:auto;margin-right:auto;}}</style>',
        unsafe_allow_html=True,
    )
    st.title("🆚 Strategie nazionali a confronto")
    st.markdown(
        "La media europea nasconde traiettorie opposte: chi ha puntato sul nucleare, chi sulle "
        "rinnovabili, chi è ancora legato al fossile. Selezione libera di due-quattro paesi: numeri "
        "chiave, mix affiancati, confronto diretto su una metrica a scelta e crescita di una fonte "
        "nel tempo."
    )

    # Tutti i paesi europei sono inclusi qui (a differenza del panel bilanciato usato nelle
    # pagine Storia): il confronto è tra paesi scelti esplicitamente dall'utente, non un
    # aggregato europeo, quindi una serie incompleta non altera nessuna media, mostra solo
    # meno anni nei grafici.
    data = _with_derived(get_europe_window())
    options = sorted(data["country"].unique())

    selected = st.multiselect(
        "Paesi da confrontare (da 2 a 4)", options, default=["France", "Germany"],
        max_selections=4,
        help=(
            "Il caso base è il testa-a-testa; fino a 4 paesi, la pagina adatta le colonne di "
            "conseguenza. Tutti i paesi europei sono selezionabili, anche con serie più corte."
        ),
    )
    if len(selected) < 2:
        st.info("Seleziona almeno due paesi per confrontarli.")
        st.stop()

    # (paese, dati, colore) in ordine di selezione: il colore identifica il paese in tutta la pagina.
    series = [
        (c, data[data["country"] == c].sort_values("year"), COUNTRY_COLORS[i])
        for i, c in enumerate(selected)
    ]

    # La pagina si allarga con il numero di paesi, così le colonne non scendono sotto COL_PX; le
    # sezioni di confronto comune restano comunque a UNIFIED_PX grazie al wrapper "fw_…".
    limit_page_width(max(PAGE_MIN, len(series) * COL_PX))

    # Scoreboard: una colonna per paese
    st.subheader("Scheda sintetica")
    st.caption("Valore al 2022 e variazione dal primo anno disponibile (di norma il 1990). Freccia verde = miglioramento.")
    for (country, d_c, _), col in zip(series, st.columns(len(series), border=True)):
        with col:
            render_scoreboard(country, d_c.set_index("year"))

    st.divider()

    # Composizione del mix: una colonna per paese, stessa scala
    st.subheader("Composizione del mix elettrico")
    mode = st.radio(
        "Come rappresentare il mix", ["Quota (%)", "Composizione (TWh)"], horizontal=True,
        help="La quota (%) rende i paesi direttamente confrontabili; i TWh mostrano anche il divario di dimensione.",
    )
    for (country, d_c, _), col in zip(series, st.columns(len(series), border=True)):
        with col:
            st.plotly_chart(mix_figure(d_c, country, mode), width="stretch")
    st.caption(f"{SOURCE_NOTE} · quote fossile/nucleare/rinnovabili, 1990–2022")

    st.divider()

    # Import/export elettrico: una colonna per paese, colore = segno (non paese)
    st.subheader("Import ed export elettrico")
    st.markdown(
        "Import netto sul fabbisogno elettrico: **ambra** = anno da importatore netto, **blu** = "
        "anno da esportatore netto. Qui il colore segnala una direzione, non una prestazione: un "
        "paese può alternare le due condizioni negli anni."
    )
    any_imports = False
    for (country, d_c, _), col in zip(series, st.columns(len(series), border=True)):
        with col:
            fig = import_export_figure(d_c, country)
            if fig is not None:
                any_imports = True
                st.plotly_chart(fig, width="stretch")
            else:
                st.info(f"Nessun dato di import/export per {country}.")
    if any_imports:
        st.caption(f"{SOURCE_NOTE} · import netto in % del fabbisogno elettrico, 1990–2022")

    st.divider()

    # Confronto diretto su una metrica: sezione unificata (larghezza fissa UNIFIED_PX)
    with st.container(key="fw_confronto"):
        st.subheader("Confronto diretto")
        st.markdown(
            "Qui i paesi selezionati stanno **sullo stesso grafico**: scegli una metrica e confronta le "
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
        for country, d_c, color in series:
            s = d_c.set_index("year")[col].dropna() if col in d_c.columns else None
            if s is None or s.empty:
                continue
            finals[country] = int(s.index.max())
            fig.add_trace(go.Scatter(x=s.index, y=s.values, name=country, line=dict(color=color, width=2.8)))

        if show_europe:
            ref = europe_reference(col, series[0][1]["year"].unique())
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

        note = f"{SOURCE_NOTE} · 1990–2022"
        if is_abs:
            note += " · ⚠️ valore assoluto: riflette anche la dimensione del paese, non solo la strategia"
        st.caption(note)

        # Lettura dinamica sull'ultimo anno in comune a tutti i paesi con questa metrica: più alto vs
        # più basso (il "divario A-B" del testa-a-testa non si generalizza a 3-4 paesi).
        if len(finals) >= 2:
            year = min(finals.values())
            vals = {}
            for country, d_c, _ in series:
                s = d_c.set_index("year")[col].dropna() if col in d_c.columns else None
                if s is not None and year in s.index:
                    vals[country] = float(s[year])
            if len(vals) >= 2:
                hi = max(vals, key=vals.get)
                lo = min(vals, key=vals.get)
                parts = " · ".join(f"**{c}** {v:.1f}" for c, v in vals.items())
                st.markdown(
                    f"Nel **{year}**, {metric_label.split(' (')[0].lower()} ({unit}): {parts}. "
                    f"Più alto **{hi}**, più basso **{lo}**, divario {vals[hi] - vals[lo]:.1f} {unit}."
                )

    st.divider()

    # Crescita di una fonte nel tempo: sezione unificata (larghezza fissa UNIFIED_PX)
    with st.container(key="fw_crescita"):
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
        for country, d_c, color in series:
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
            title=f"{growth_source} – {'indice di crescita' if as_index else 'valore assoluto (TWh)'}",
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
