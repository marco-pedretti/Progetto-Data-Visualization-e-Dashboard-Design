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

Focus principale sul settore elettrico (mix, quote, intensità di carbonio,
domanda pro-capite), più una scheda di overview generale (popolazione, PIL) —
non le 130 colonne del dataset, per restare coerenti con il tema del
progetto (scelta esplicita dell'utente, stessa logica già usata per la
pagina Mappa).
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
# Okabe-Ito, colorblind-safe: riusa fossile/nucleare/rinnovabili di PALETTE, aggiunge
# le tre tinte rimanenti della palette per idro/eolico/altre rinnovabili.
SOURCE_COLORS = {
    "Fossile": PALETTE["fossile"], "Nucleare": PALETTE["nucleare"], "Rinnovabili": PALETTE["rinnovabili"],
    "Idroelettrico": "#0072B2", "Eolico": "#56B4E9", "Solare": PALETTE["rinnovabili"], "Altre rinnovabili": "#CC79A7",
}

RAW_COLS = [
    "year", "population", "gdp",
    "electricity_generation", "fossil_electricity", "nuclear_electricity", "renewables_electricity",
    "hydro_electricity", "wind_electricity", "solar_electricity", "other_renewable_electricity",
    "fossil_share_elec", "nuclear_share_elec", "renewables_share_elec",
    "hydro_share_elec", "wind_share_elec", "solar_share_elec", "other_renewables_share_elec",
    "carbon_intensity_elec", "per_capita_electricity", "electricity_share_energy",
]

df_raw = load_raw_data()
ALL_ENTITIES = sorted(df_raw["country"].unique())
DEFAULT_ENTITY = "Italy"


def last_valid(d_idx: pd.DataFrame, col: str):
    """Ultimo (anno, valore) validi per una colonna, o (None, None) se assente/vuota."""
    if col not in d_idx.columns:
        return None, None
    s = d_idx[col].dropna()
    if s.empty:
        return None, None
    return int(s.index.max()), s.iloc[-1]


def sidebar_controls() -> dict:
    with st.sidebar:
        st.header("🔧 Filtri")
        entity = st.selectbox(
            "Paese o entità (qualunque, mondo incluso)",
            ALL_ENTITIES, index=ALL_ENTITIES.index(DEFAULT_ENTITY),
            help='Non solo i 33 paesi del panel bilanciato: anche Svizzera/Islanda/Ucraina e aggregati come "World" o "Europe".',
        )
        task = st.radio("Mix elettrico: cosa vuoi vedere?", ["Composizione (TWh)", "Quota (%)"])
        detail = st.radio("Dettaglio fonti", ["Semplice (fossile/nucleare/rinnovabili)", "Dettagliato (+ idro/eolico/solare)"])
    return dict(entity=entity, task=task, detail=detail)


def main() -> None:
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

    tab_overview, tab_mix, tab_carbonio, tab_dati = st.tabs(
        ["📋 Overview", "⚡ Mix elettrico", "🌍 Intensità & domanda", "📄 Dati grezzi"]
    )

    with tab_overview:
        pop_year, pop_val = last_valid(d_idx, "population")
        gdp_year, gdp_val = last_valid(d_idx, "gdp")
        gen_year, gen_val = last_valid(d_idx, "electricity_generation")
        ci_year, ci_val = last_valid(d_idx, "carbon_intensity_elec")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Popolazione", f"{pop_val:,.0f}" if pop_val is not None else "n.d.", help=f"Ultimo dato: {pop_year}" if pop_year else None)
        c2.metric("PIL", f"{gdp_val / 1e9:,.0f} Mld $" if gdp_val is not None else "n.d.", help=f"Ultimo dato: {gdp_year}, international-$" if gdp_year else None)
        c3.metric("Generazione elettrica", f"{gen_val:,.0f} TWh" if gen_val is not None else "n.d.", help=f"Ultimo dato: {gen_year}" if gen_year else None)
        c4.metric("Intensità di carbonio", f"{ci_val:.0f} gCO₂/kWh" if ci_val is not None else "n.d.", help=f"Ultimo dato: {ci_year}" if ci_year else None)

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

    with tab_mix:
        cols = (DETAILED_TWH if "Dettagliato" in f["detail"] else SIMPLE_TWH) if f["task"].startswith("Composizione") else (DETAILED_SHARE if "Dettagliato" in f["detail"] else SIMPLE_SHARE)
        value_name = "TWh" if f["task"].startswith("Composizione") else "quota"
        available = [(label, col) for label, col in cols if col in d.columns and d[col].notna().any()]

        if not available:
            st.info("Nessun dato di mix elettrico per questa entità.")
        else:
            long_d = d[["year"] + [col for _, col in available]].melt(id_vars="year", var_name="col", value_name=value_name)
            label_map = {col: label for label, col in available}
            long_d["fonte"] = long_d["col"].map(label_map)
            long_d = long_d.dropna(subset=[value_name])

            if f["task"].startswith("Composizione"):
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

    with tab_carbonio:
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
            fig.update_layout(title="Intensità di carbonio", yaxis_title="gCO₂eq/kWh", template="plotly_white", height=420, legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Nessun dato di intensità di carbonio per questa entità.")

        col_a, col_b = st.columns(2)
        with col_a:
            dem_series = d_idx["electricity_demand_per_capita"].dropna() if "electricity_demand_per_capita" in d_idx.columns else pd.Series(dtype=float)
            if not dem_series.empty:
                fig = px.line(dem_series.reset_index(), x="year", y="electricity_demand_per_capita", labels={"year": "", "electricity_demand_per_capita": "kWh/persona"}, template="plotly_white")
                fig.update_layout(height=320, title="Domanda elettrica pro-capite")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di domanda pro-capite per questa entità.")
        with col_b:
            share_energy = d_idx["electricity_share_energy"].dropna() if "electricity_share_energy" in d_idx.columns else pd.Series(dtype=float)
            if not share_energy.empty:
                fig = px.line(share_energy.reset_index(), x="year", y="electricity_share_energy", labels={"year": "", "electricity_share_energy": "% del consumo energetico"}, template="plotly_white")
                fig.update_layout(height=320, title="Quota elettrica sul consumo energetico totale")
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Nessun dato di quota elettrica sul consumo energetico per questa entità.")
        st.caption(SOURCE_NOTE)

    with tab_dati:
        cols_present = [c for c in RAW_COLS if c in d.columns]
        table = d[cols_present].reset_index(drop=True)
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
