"""
Pagina 8 — Scheda Paese (Esplora)
=====================================
Vista libera "tutto il possibile" su una singola entità del dataset OWID — un
paese, ma anche un aggregato come "World" o "Europe" (mondo incluso, su
richiesta esplicita dell'utente). A differenza delle altre pagine Esplora
**non** è vincolata al panel bilanciato: qui l'obiettivo è la profondità su
un'unica entità, non il confronto tra paesi, quindi non serve una serie
completa 1990-2022 — ogni grafico mostra semplicemente quanto dato esiste,
gap compresi (la stessa lezione sulla censura dei dati del Cap. 3 del
notebook, qui visibile a scelta su qualunque entità).

A differenza delle altre pagine, qui il taglio non è "fossile/nucleare/
rinnovabili": quel confronto è già il tema di mappa, storia e confronti
altrove nell'app. Questa scheda copre l'intero dataset elettrico/energetico
OWID (energia primaria, emissioni del settore elettrico, import/export,
pro-capite) con un esploratore libero a scelta dell'utente, non un percorso
fisso — coerente con l'idea di lasciare la massima discrezionalità qui
(scelta esplicita dell'utente).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import EUROPE_ISO, PALETTE, SOURCE_NOTE, load_raw_data

SIMPLE_TWH = [("Fossile", "fossil_electricity"), ("Nucleare", "nuclear_electricity"), ("Rinnovabili", "renewables_electricity")]
DETAILED_TWH = [
    ("Fossile", "fossil_electricity"), ("Nucleare", "nuclear_electricity"),
    ("Idroelettrico", "hydro_electricity"), ("Eolico", "wind_electricity"),
    ("Solare", "solar_electricity"), ("Altre rinnovabili", "other_renewable_electricity"),
]
SIMPLE_SHARE = [("Fossile", "fossil_share_elec"), ("Nucleare", "nuclear_share_elec"), ("Rinnovabili", "renewables_share_elec")]
DETAILED_SHARE = [
    ("Fossile", "fossil_share_elec"), ("Nucleare", "nuclear_share_elec"),
    ("Idroelettrico", "hydro_share_elec"), ("Eolico", "wind_share_elec"),
    ("Solare", "solar_share_elec"), ("Altre rinnovabili", "other_renewables_share_elec"),
]

SIMPLE_ENERGY_TWH = [("Fossile", "fossil_fuel_consumption"), ("Nucleare", "nuclear_consumption"), ("Rinnovabili", "renewables_consumption")]
DETAILED_ENERGY_TWH = [
    ("Carbone", "coal_consumption"), ("Gas", "gas_consumption"), ("Petrolio", "oil_consumption"),
    ("Nucleare", "nuclear_consumption"), ("Idroelettrico", "hydro_consumption"), ("Eolico", "wind_consumption"),
    ("Solare", "solar_consumption"), ("Bioenergie", "biofuel_consumption"), ("Altre rinnovabili", "other_renewable_consumption"),
]
SIMPLE_ENERGY_SHARE = [("Fossile", "fossil_share_energy"), ("Nucleare", "nuclear_share_energy"), ("Rinnovabili", "renewables_share_energy")]
DETAILED_ENERGY_SHARE = [
    ("Carbone", "coal_share_energy"), ("Gas", "gas_share_energy"), ("Petrolio", "oil_share_energy"),
    ("Nucleare", "nuclear_share_energy"), ("Idroelettrico", "hydro_share_energy"), ("Eolico", "wind_share_energy"),
    ("Solare", "solar_share_energy"), ("Bioenergie", "biofuel_share_energy"), ("Altre rinnovabili", "other_renewables_share_energy"),
]

# Okabe-Ito, colorblind-safe: 8 tinte usate una sola volta ciascuna sul set fossile
# dettagliato (carbone/gas/petrolio) + quello già esistente per l'elettricità. Il grigio è
# riusato tra "Fossile" aggregato e "Altre rinnovabili" perché non compaiono mai insieme
# nello stesso grafico (sono alternative dello stesso radio "Semplice/Dettagliato"). Niente
# nero puro per il carbone: Streamlit ridisegna Plotly con sfondo scuro in dark mode e il
# nero vi sparisce del tutto — grigio scuro invece, visibile su entrambi i temi.
SOURCE_COLORS = {
    "Fossile": "#999999", "Carbone": "#595959", "Gas": "#F0E442", "Petrolio": "#D55E00",
    "Nucleare": PALETTE["nucleare"], "Rinnovabili": PALETTE["rinnovabili"],
    "Idroelettrico": "#0072B2", "Eolico": "#56B4E9", "Solare": PALETTE["rinnovabili"],
    "Bioenergie": "#CC79A7", "Altre rinnovabili": "#999999",
}

# Esploratore libero: ogni voce è (etichetta, colonna, unità). Raggruppate per tema così
# l'utente sceglie prima l'area (elettricità / energia primaria / emissioni / pro-capite /
# import-export) e poi la metrica specifica, invece di scorrere una lista piatta di ~70 voci.
METRIC_GROUPS: dict[str, list[tuple[str, str, str]]] = {
    "⚡ Elettricità per fonte": [
        ("Generazione totale", "electricity_generation", "TWh"),
        ("Domanda", "electricity_demand", "TWh"),
        ("Fossile", "fossil_electricity", "TWh"),
        ("Carbone", "coal_electricity", "TWh"),
        ("Gas", "gas_electricity", "TWh"),
        ("Petrolio", "oil_electricity", "TWh"),
        ("Nucleare", "nuclear_electricity", "TWh"),
        ("Rinnovabili", "renewables_electricity", "TWh"),
        ("Idroelettrico", "hydro_electricity", "TWh"),
        ("Eolico", "wind_electricity", "TWh"),
        ("Solare", "solar_electricity", "TWh"),
        ("Bioenergie", "biofuel_electricity", "TWh"),
        ("Altre rinnovabili", "other_renewable_electricity", "TWh"),
        ("Low-carbon (nucleare + rinnovabili)", "low_carbon_electricity", "TWh"),
    ],
    "⚡ Quota sulla generazione elettrica": [
        ("Fossile", "fossil_share_elec", "%"),
        ("Carbone", "coal_share_elec", "%"),
        ("Gas", "gas_share_elec", "%"),
        ("Petrolio", "oil_share_elec", "%"),
        ("Nucleare", "nuclear_share_elec", "%"),
        ("Rinnovabili", "renewables_share_elec", "%"),
        ("Idroelettrico", "hydro_share_elec", "%"),
        ("Eolico", "wind_share_elec", "%"),
        ("Solare", "solar_share_elec", "%"),
        ("Bioenergie", "biofuel_share_elec", "%"),
        ("Altre rinnovabili", "other_renewables_share_elec", "%"),
        ("Low-carbon", "low_carbon_share_elec", "%"),
    ],
    "🔥 Energia primaria per fonte": [
        ("Consumo totale", "primary_energy_consumption", "TWh"),
        ("Carbone", "coal_consumption", "TWh"),
        ("Gas", "gas_consumption", "TWh"),
        ("Petrolio", "oil_consumption", "TWh"),
        ("Nucleare", "nuclear_consumption", "TWh"),
        ("Rinnovabili", "renewables_consumption", "TWh"),
        ("Idroelettrico", "hydro_consumption", "TWh"),
        ("Eolico", "wind_consumption", "TWh"),
        ("Solare", "solar_consumption", "TWh"),
        ("Bioenergie", "biofuel_consumption", "TWh"),
        ("Altre rinnovabili", "other_renewable_consumption", "TWh"),
        ("Combustibili fossili (totale)", "fossil_fuel_consumption", "TWh"),
        ("Low-carbon", "low_carbon_consumption", "TWh"),
    ],
    "🔥 Quota sul consumo energetico totale": [
        ("Fossile", "fossil_share_energy", "%"),
        ("Carbone", "coal_share_energy", "%"),
        ("Gas", "gas_share_energy", "%"),
        ("Petrolio", "oil_share_energy", "%"),
        ("Nucleare", "nuclear_share_energy", "%"),
        ("Rinnovabili", "renewables_share_energy", "%"),
        ("Idroelettrico", "hydro_share_energy", "%"),
        ("Eolico", "wind_share_energy", "%"),
        ("Solare", "solar_share_energy", "%"),
        ("Bioenergie", "biofuel_share_energy", "%"),
        ("Altre rinnovabili", "other_renewables_share_energy", "%"),
        ("Low-carbon", "low_carbon_share_energy", "%"),
        ("Elettricità sul totale energia", "electricity_share_energy", "%"),
    ],
    "⛏️ Produzione fonti fossili": [
        ("Carbone", "coal_production", "TWh eq."),
        ("Gas", "gas_production", "TWh eq."),
        ("Petrolio", "oil_production", "TWh eq."),
    ],
    "👤 Pro-capite": [
        ("Popolazione", "population", "persone"),
        ("PIL", "gdp", "international-$"),
        ("Energia (tutte le fonti)", "energy_per_capita", "kWh/persona"),
        ("Elettricità generata", "per_capita_electricity", "kWh/persona"),
        ("Elettricità richiesta", "electricity_demand_per_capita", "kWh/persona"),
        ("Da fossili", "fossil_energy_per_capita", "kWh/persona"),
        ("Da rinnovabili", "renewables_energy_per_capita", "kWh/persona"),
        ("Da nucleare", "nuclear_energy_per_capita", "kWh/persona"),
        ("Da low-carbon", "low_carbon_energy_per_capita", "kWh/persona"),
    ],
    "🌍 Emissioni & efficienza": [
        ("Emissioni del settore elettrico", "greenhouse_gas_emissions", "Mt CO₂eq"),
        ("Emissioni pro-capite (settore elettrico)", "ghg_per_capita_elec", "t CO₂eq/persona"),
        ("Intensità di carbonio elettrica", "carbon_intensity_elec", "gCO₂/kWh"),
        ("Energia per unità di PIL", "energy_per_gdp", "kWh/$"),
    ],
    "🔄 Import/export elettrico": [
        ("Import netto", "net_elec_imports", "TWh"),
        ("Import netto sul fabbisogno", "net_elec_imports_share_demand", "%"),
    ],
}

RAW_COLS_DEFAULT = [
    "year", "population", "gdp",
    "electricity_generation", "fossil_electricity", "nuclear_electricity", "renewables_electricity",
    "hydro_electricity", "wind_electricity", "solar_electricity", "other_renewable_electricity",
    "fossil_share_elec", "nuclear_share_elec", "renewables_share_elec",
    "carbon_intensity_elec", "per_capita_electricity", "electricity_share_energy",
    "primary_energy_consumption", "greenhouse_gas_emissions",
]

df_raw = load_raw_data().copy()
# Derivato: OWID non fornisce le emissioni pro-capite del settore elettrico, solo il totale
# (Mt CO2eq) e la popolazione — si calcola qui una sola volta per riuso sia nei grafici sia
# nel confronto tra paesi. Il .copy() evita di frammentare il DataFrame cachato da
# load_raw_data() (PerformanceWarning di pandas altrimenti innocua ma rumorosa nei log).
df_raw["ghg_per_capita_elec"] = df_raw["greenhouse_gas_emissions"] * 1e6 / df_raw["population"]

ALL_ENTITIES = sorted(df_raw["country"].unique())
DEFAULT_ENTITY = "Italy"
# Universo di confronto per il rank/percentile: solo entità con iso_code a 3 lettere, cioè
# paesi veri — esclude aggregati come "World", "Europe", "European Union (27)", gruppi di
# reddito, ecc. (94 aggregati individuati nel dataset, nessuno ha un iso_code).
IS_REAL_COUNTRY = df_raw["iso_code"].notna() & (df_raw["iso_code"].str.len() == 3)


def last_valid(d_idx: pd.DataFrame, col: str):
    """Ultimo (anno, valore) validi per una colonna, o (None, None) se assente/vuota."""
    if col not in d_idx.columns:
        return None, None
    s = d_idx[col].dropna()
    if s.empty:
        return None, None
    return int(s.index.max()), s.iloc[-1]


def available_metrics(d: pd.DataFrame, group: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    return [(label, col, unit) for label, col, unit in group if col in d.columns and d[col].notna().any()]


def human_count(n: float) -> str:
    """Formato compatto (es. 59.1M) per numeri grandi nelle KPI tile: un valore come
    59.146.263 non ci sta leggibile in una colonna stretta su 5, a differenza di 'TWh'/'%'
    già corti di loro. Il valore esatto resta nel tooltip (help=)."""
    if n >= 1e9:
        return f"{n / 1e9:.2f} Mld"
    if n >= 1e6:
        return f"{n / 1e6:.1f} M"
    if n >= 1e3:
        return f"{n / 1e3:.0f} k"
    return f"{n:.0f}"


def trend_figure(d_idx: pd.DataFrame, entity: str, col: str, label: str, unit: str, show_refs: bool, show_yoy: bool) -> go.Figure:
    series = d_idx[col].dropna()
    title = label
    y_title = unit
    if show_yoy:
        series = series.pct_change() * 100
        series = series.dropna()
        title = f"{label} — variazione % anno su anno"
        y_title = "% anno su anno"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series.values, name=entity, line=dict(color=PALETTE["nucleare"], width=2.5)))
    if show_refs:
        for ref in ["Europe", "World"]:
            if ref == entity:
                continue
            ref_series = df_raw[df_raw["country"] == ref].set_index("year")[col].dropna()
            if show_yoy:
                ref_series = ref_series.pct_change().dropna() * 100
            if not ref_series.empty:
                fig.add_trace(go.Scatter(x=ref_series.index, y=ref_series.values, name=ref, line=dict(width=1, dash="dash")))
    fig.update_layout(
        title=f"{title} — {entity}", yaxis_title=y_title, template="plotly_white",
        height=440, legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def percentile_block(entity: str, iso_code: str | None, col: str, label: str, unit: str, d_idx: pd.DataFrame) -> None:
    if iso_code is None:
        st.info(f'"{entity}" è un aggregato (non un singolo paese): confrontarlo con i paesi non è comparabile su questa base.')
        return

    year, value = last_valid(d_idx, col)
    if year is None:
        st.info(f"Nessun dato di '{label}' per {entity}.")
        return

    pool = df_raw[(df_raw["year"] == year) & IS_REAL_COUNTRY]
    vals = pool[col].dropna()
    if len(vals) < 5:
        st.info(f"Troppo pochi paesi con dato di '{label}' nel {year} per un confronto significativo ({len(vals)}).")
        return

    n = len(vals)
    rank_from_top = int((vals > value).sum()) + 1
    percentile = (vals <= value).mean() * 100

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric(f"Posizione di {entity} ({year})", f"{rank_from_top}° su {n}", help="Dal valore più alto al più basso, tra i paesi con questo dato nello stesso anno.")
        st.metric("Percentile", f"{percentile:.0f}°", help="Percentuale di paesi con un valore uguale o inferiore.")
    with c2:
        fig = px.histogram(vals, nbins=30, labels={"value": unit}, template="plotly_white")
        fig.add_vline(x=value, line_color=PALETTE["calo"], line_width=3, annotation_text=entity, annotation_position="top")
        fig.update_layout(height=280, title=f"Distribuzione tra {n} paesi — {label} ({year})", showlegend=False, yaxis_title="Numero di paesi")
        st.plotly_chart(fig, width="stretch")


def sidebar_controls() -> dict:
    with st.sidebar:
        st.header("🔧 Filtri")
        entity = st.selectbox(
            "Paese o entità (qualunque, mondo incluso)",
            ALL_ENTITIES, index=ALL_ENTITIES.index(DEFAULT_ENTITY),
            help='Non solo i 33 paesi del panel bilanciato: anche Svizzera/Islanda/Ucraina e aggregati come "World" o "Europe".',
        )
    return dict(entity=entity)


def main() -> None:
    # Il layout "wide" dell'app (impostato globalmente in streamlit_app.py) fa occupare al
    # contenuto tutta la larghezza dello schermo: utile per la mappa, ma su monitor larghi
    # allarga eccessivamente anche testo e grafici a due colonne rovinando l'estetica. Si
    # limita la larghezza massima solo su questa pagina, centrando il contenuto (stessa
    # soluzione già applicata alla pagina Mappa).
    st.markdown(
        """
        <style>
        [data-testid="stMainBlockContainer"] {
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🔎 Scheda Paese")
    st.markdown(
        "Scegli un'entità qualunque in sidebar — non è vincolata al panel bilanciato usato nel "
        "resto della dashboard, quindi puoi esplorare anche i casi esclusi (Svizzera, Islanda...), "
        "l'Ucraina, o aggregati come **World**/**Europe**. Ogni grafico mostra solo gli anni per cui "
        "esiste davvero il dato: se una serie inizia tardi o ha un buco, il grafico lo mostra invece "
        "di nasconderlo."
    )

    f = sidebar_controls()
    entity = f["entity"]
    d = df_raw[df_raw["country"] == entity].sort_values("year")
    d_idx = d.set_index("year")

    iso = d["iso_code"].dropna()
    iso_code = iso.iloc[0] if not iso.empty else None
    is_europe = iso_code in EUROPE_ISO if iso_code else False
    tag = "🇪🇺 Europa" if is_europe else ("🌍 Aggregato/resto del mondo" if iso_code is None else "🌐 Extra-Europa")
    st.caption(f"**{entity}** — {tag}" + (f" (ISO: {iso_code})" if iso_code else ""))

    tab_overview, tab_explore, tab_elec, tab_energy, tab_emissioni, tab_dati = st.tabs(
        ["📋 Overview", "🔍 Esplora & confronta", "⚡ Elettricità", "🔥 Energia primaria", "🌍 Emissioni & efficienza", "📄 Dati grezzi"]
    )

    with tab_overview:
        pop_year, pop_val = last_valid(d_idx, "population")
        gdp_year, gdp_val = last_valid(d_idx, "gdp")
        gen_year, gen_val = last_valid(d_idx, "electricity_generation")
        ci_year, ci_val = last_valid(d_idx, "carbon_intensity_elec")
        ghg_year, ghg_val = last_valid(d_idx, "ghg_per_capita_elec")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Popolazione", human_count(pop_val) if pop_val is not None else "n.d.", help=f"{pop_val:,.0f} persone — ultimo dato: {pop_year}" if pop_val is not None else None)
        c2.metric("PIL", f"{gdp_val / 1e9:,.0f} Mld $" if gdp_val is not None else "n.d.", help=f"Ultimo dato: {gdp_year}, international-$" if gdp_year else None)
        c3.metric("Generazione elettrica", f"{gen_val:,.0f} TWh" if gen_val is not None else "n.d.", help=f"Ultimo dato: {gen_year}" if gen_year else None)
        c4.metric("Intensità di carbonio", f"{ci_val:.0f} gCO₂/kWh" if ci_val is not None else "n.d.", help=f"Ultimo dato: {ci_year}" if ci_year else None)
        c5.metric("Emissioni pro-capite", f"{ghg_val:.2f} t CO₂eq" if ghg_val is not None else "n.d.", help=f"Ultimo dato: {ghg_year}, solo settore elettrico" if ghg_year else None)

        col_a, col_b = st.columns(2)
        with col_a:
            pop_series = d_idx["population"].dropna()
            if not pop_series.empty:
                fig = px.line(pop_series.reset_index(), x="year", y="population", labels={"year": "", "population": "Popolazione"}, template="plotly_white")
                fig.update_layout(height=320, title="Popolazione")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di popolazione per questa entità.")
        with col_b:
            pc_series = d_idx["per_capita_electricity"].dropna()
            if not pc_series.empty:
                fig = px.line(pc_series.reset_index(), x="year", y="per_capita_electricity", labels={"year": "", "per_capita_electricity": "kWh/persona"}, template="plotly_white")
                fig.update_layout(height=320, title="Generazione elettrica pro-capite")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di generazione pro-capite per questa entità.")

    with tab_explore:
        st.markdown(
            "Scegli una qualunque delle metriche del dataset OWID raggruppate per area: il grafico "
            "mostra l'andamento nel tempo, e sotto trovi dove si colloca questa entità rispetto a "
            "tutti gli altri paesi nell'ultimo anno disponibile."
        )
        category = st.selectbox("Categoria", list(METRIC_GROUPS.keys()))
        options = available_metrics(d, METRIC_GROUPS[category])
        if not options:
            st.info(f"Nessun dato disponibile per {entity} in questa categoria.")
        else:
            metric_label = st.selectbox("Metrica", [label for label, _, _ in options])
            _, col, unit = next(o for o in options if o[0] == metric_label)

            opt1, opt2 = st.columns(2)
            show_refs = opt1.checkbox("Confronta con Europa e Mondo", value=False)
            show_yoy = opt2.checkbox("Mostra variazione % anno su anno", value=False)

            fig = trend_figure(d_idx, entity, col, metric_label, unit, show_refs, show_yoy)
            st.plotly_chart(fig, width="stretch")

            st.divider()
            st.subheader("Come si colloca rispetto agli altri paesi")
            percentile_block(entity, iso_code, col, metric_label, unit, d_idx)
        st.caption(SOURCE_NOTE)

    with tab_elec:
        col_task, col_detail = st.columns(2)
        task = col_task.radio("Cosa vuoi vedere?", ["Composizione (TWh)", "Quota (%)"], key="elec_task")
        detail = col_detail.radio("Dettaglio fonti", ["Semplice", "Dettagliato"], key="elec_detail")

        cols = (DETAILED_TWH if detail == "Dettagliato" else SIMPLE_TWH) if task.startswith("Composizione") else (DETAILED_SHARE if detail == "Dettagliato" else SIMPLE_SHARE)
        value_name = "TWh" if task.startswith("Composizione") else "quota"
        available = [(label, col) for label, col in cols if col in d.columns and d[col].notna().any()]

        if not available:
            st.info("Nessun dato di mix elettrico per questa entità.")
        else:
            long_d = d[["year"] + [col for _, col in available]].melt(id_vars="year", var_name="col", value_name=value_name)
            label_map = {col: label for label, col in available}
            long_d["fonte"] = long_d["col"].map(label_map)
            long_d = long_d.dropna(subset=[value_name])

            if task.startswith("Composizione"):
                fig = px.area(
                    long_d, x="year", y=value_name, color="fonte",
                    color_discrete_map=SOURCE_COLORS, category_orders={"fonte": [label for label, _ in available]},
                    labels={"year": "", value_name: "TWh", "fonte": ""},
                    title=f"Composizione del mix elettrico — {entity}", template="plotly_white",
                )
            else:
                fig = px.line(
                    long_d, x="year", y=value_name, color="fonte",
                    color_discrete_map=SOURCE_COLORS, category_orders={"fonte": [label for label, _ in available]},
                    labels={"year": "", value_name: "% della generazione", "fonte": ""},
                    title=f"Quota di ciascuna fonte — {entity}", template="plotly_white",
                )
                fig.update_traces(line=dict(width=2.5))
                fig.update_yaxes(range=[0, 100])
            fig.update_layout(height=480)
            st.plotly_chart(fig, width="stretch")
        st.caption(SOURCE_NOTE)

    with tab_energy:
        st.caption("Energia primaria: tutti gli usi energetici (anche trasporti, riscaldamento, industria), non solo l'elettricità.")
        col_task, col_detail = st.columns(2)
        task = col_task.radio("Cosa vuoi vedere?", ["Composizione (TWh)", "Quota (%)"], key="energy_task")
        detail = col_detail.radio("Dettaglio fonti", ["Semplice", "Dettagliato"], key="energy_detail")

        cols = (DETAILED_ENERGY_TWH if detail == "Dettagliato" else SIMPLE_ENERGY_TWH) if task.startswith("Composizione") else (DETAILED_ENERGY_SHARE if detail == "Dettagliato" else SIMPLE_ENERGY_SHARE)
        value_name = "TWh" if task.startswith("Composizione") else "quota"
        available = [(label, col) for label, col in cols if col in d.columns and d[col].notna().any()]

        if not available:
            st.info("Nessun dato di consumo energetico primario per questa entità.")
        else:
            long_d = d[["year"] + [col for _, col in available]].melt(id_vars="year", var_name="col", value_name=value_name)
            label_map = {col: label for label, col in available}
            long_d["fonte"] = long_d["col"].map(label_map)
            long_d = long_d.dropna(subset=[value_name])

            if task.startswith("Composizione"):
                fig = px.area(
                    long_d, x="year", y=value_name, color="fonte",
                    color_discrete_map=SOURCE_COLORS, category_orders={"fonte": [label for label, _ in available]},
                    labels={"year": "", value_name: "TWh", "fonte": ""},
                    title=f"Composizione dell'energia primaria — {entity}", template="plotly_white",
                )
            else:
                fig = px.line(
                    long_d, x="year", y=value_name, color="fonte",
                    color_discrete_map=SOURCE_COLORS, category_orders={"fonte": [label for label, _ in available]},
                    labels={"year": "", value_name: "% del consumo energetico", "fonte": ""},
                    title=f"Quota di ciascuna fonte sull'energia primaria — {entity}", template="plotly_white",
                )
                fig.update_traces(line=dict(width=2.5))
                fig.update_yaxes(range=[0, 100])
            fig.update_layout(height=480)
            st.plotly_chart(fig, width="stretch")

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            prod_cols = [("Carbone", "coal_production"), ("Gas", "gas_production"), ("Petrolio", "oil_production")]
            prod_available = [(label, col) for label, col in prod_cols if col in d.columns and d[col].notna().any()]
            if prod_available:
                long_prod = d[["year"] + [col for _, col in prod_available]].melt(id_vars="year", var_name="col", value_name="TWh eq.")
                label_map = {col: label for label, col in prod_available}
                long_prod["fonte"] = long_prod["col"].map(label_map)
                long_prod = long_prod.dropna(subset=["TWh eq."])
                fig = px.line(
                    long_prod, x="year", y="TWh eq.", color="fonte", color_discrete_map=SOURCE_COLORS,
                    labels={"year": ""}, title="Produzione di fonti fossili (estrazione)", template="plotly_white",
                )
                fig.update_layout(height=340)
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di produzione di fonti fossili per questa entità.")
        with col_b:
            energy_pc = d_idx["energy_per_capita"].dropna() if "energy_per_capita" in d_idx.columns else pd.Series(dtype=float)
            if not energy_pc.empty:
                fig = px.line(energy_pc.reset_index(), x="year", y="energy_per_capita", labels={"year": "", "energy_per_capita": "kWh/persona"}, template="plotly_white")
                fig.update_layout(height=340, title="Consumo energetico pro-capite (tutte le fonti)")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di consumo energetico pro-capite per questa entità.")
        st.caption(SOURCE_NOTE)

    with tab_emissioni:
        ci_series = d_idx["carbon_intensity_elec"].dropna()
        if not ci_series.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ci_series.index, y=ci_series.values, name=entity, line=dict(color=PALETTE["nucleare"], width=2.5)))
            for ref in ["Europe", "World"]:
                if ref == entity:
                    continue
                ref_series = df_raw[df_raw["country"] == ref].set_index("year")["carbon_intensity_elec"].dropna()
                if not ref_series.empty:
                    fig.add_trace(go.Scatter(x=ref_series.index, y=ref_series.values, name=f'"{ref}" (OWID)', line=dict(width=1, dash="dash")))
            fig.update_layout(title="Intensità di carbonio elettrica", yaxis_title="gCO₂eq/kWh", template="plotly_white", height=420, legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Nessun dato di intensità di carbonio per questa entità.")

        col_a, col_b = st.columns(2)
        with col_a:
            ghg_series = d_idx["greenhouse_gas_emissions"].dropna() if "greenhouse_gas_emissions" in d_idx.columns else pd.Series(dtype=float)
            if not ghg_series.empty:
                fig = px.bar(ghg_series.reset_index(), x="year", y="greenhouse_gas_emissions", labels={"year": "", "greenhouse_gas_emissions": "Mt CO₂eq"}, template="plotly_white")
                fig.update_traces(marker_color=PALETTE["calo"])
                fig.update_layout(height=320, title="Emissioni del settore elettrico")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di emissioni per questa entità.")
        with col_b:
            egdp_series = d_idx["energy_per_gdp"].dropna() if "energy_per_gdp" in d_idx.columns else pd.Series(dtype=float)
            if not egdp_series.empty:
                fig = px.line(egdp_series.reset_index(), x="year", y="energy_per_gdp", labels={"year": "", "energy_per_gdp": "kWh per $ di PIL"}, template="plotly_white")
                fig.update_layout(height=320, title="Energia per unità di PIL (efficienza economica)")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di energia per unità di PIL per questa entità.")

        col_c, col_d = st.columns(2)
        with col_c:
            share_energy = d_idx["electricity_share_energy"].dropna() if "electricity_share_energy" in d_idx.columns else pd.Series(dtype=float)
            if not share_energy.empty:
                fig = px.line(share_energy.reset_index(), x="year", y="electricity_share_energy", labels={"year": "", "electricity_share_energy": "% del consumo energetico"}, template="plotly_white")
                fig.update_layout(height=320, title="Quota elettrica sul consumo energetico totale")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di quota elettrica sul consumo energetico per questa entità.")
        with col_d:
            imports = d_idx["net_elec_imports_share_demand"].dropna() if "net_elec_imports_share_demand" in d_idx.columns else pd.Series(dtype=float)
            if not imports.empty:
                fig = px.bar(imports.reset_index(), x="year", y="net_elec_imports_share_demand", labels={"year": "", "net_elec_imports_share_demand": "% del fabbisogno"}, template="plotly_white")
                fig.add_hline(y=0, line_color="#888888", line_width=1)
                fig.update_layout(height=320, title="Import netto sul fabbisogno elettrico (negativo = esportatore)")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di import/export elettrico per questa entità.")
        st.caption(SOURCE_NOTE)

    with tab_dati:
        all_cols_present = [c for c in df_raw.columns if c not in ("country", "iso_code") and d[c].notna().any()]
        default_cols = [c for c in RAW_COLS_DEFAULT if c in all_cols_present]
        chosen_cols = st.multiselect(
            "Colonne da mostrare/scaricare (di default un sottoinsieme rilevante — aggiungine quante vuoi)",
            options=all_cols_present, default=default_cols,
        )
        table = d[chosen_cols].reset_index(drop=True) if chosen_cols else d[default_cols].reset_index(drop=True)
        st.dataframe(table, width="stretch", hide_index=True)
        st.download_button(
            "⬇️ Scarica CSV",
            table.to_csv(index=False).encode("utf-8"),
            file_name=f"{entity.replace(' ', '_')}_dati.csv",
            mime="text/csv",
        )
        st.caption(SOURCE_NOTE)


if __name__ == "__main__":
    main()
