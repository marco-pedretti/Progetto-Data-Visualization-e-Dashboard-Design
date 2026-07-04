"""
Pagina 6 — Mappa Europa/Mondo (Esplora)
==========================================
Coropleta interattiva del mix elettrico: ambito (Europa/Mondo), metrica e anno
scelti liberamente, con KPI ricalcolati sullo scope selezionato. Solo variabili
del settore elettrico (quote fossile/nucleare/rinnovabili, intensità di carbonio,
generazione totale) — non emissioni economy-wide, per restare coerenti col tema
del progetto (scelta esplicita dell'utente).

I paesi senza dato per la metrica/anno scelti restano grigi nella mappa: non è un
errore da correggere, è la stessa distinzione strutturale del Cap. 3 del notebook
(la copertura fuori Europa è molto più eterogenea — always-null, right-censoring),
qui delegata al comportamento di default di Plotly invece che gestita a mano.

Periodo limitato al 2000-2024 (Cap. 3.2/3.3): prima del 2000 pochissimi paesi
fuori Europa hanno dati, il 2025 è pesantemente right-censored.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from common import EUROPE_ISO, MAP_METRICS, SOURCE_NOTE, WORLD_YEAR_END, WORLD_YEAR_START, get_scope_kpis, get_world_data

world = get_world_data()


def sidebar_controls() -> dict:
    with st.sidebar:
        st.header("🔧 Filtri")
        scope = st.radio("Ambito", ["Europa", "Mondo"])
        metric_label = st.selectbox("Metrica", list(MAP_METRICS.keys()))
        st.caption(
            "Copertura più scarsa prima del 2000 e nel 2025 (dati non ancora pubblicati per molti "
            "paesi, Cap. 3.2-3.3 del notebook): il periodo qui è limitato al 2000-2024."
        )
    return dict(scope=scope, metric_label=metric_label)


def main() -> None:
    st.title("🗺️ Mappa Europa/Mondo")
    st.markdown(
        "Scegli ambito, metrica e anno (slider in fondo). I paesi in **grigio** non hanno un dato "
        "disponibile per quella combinazione — non è un errore, è la stessa distinzione strutturale "
        "vista nel Cap. 3 del notebook (la copertura fuori Europa è molto più eterogenea)."
    )

    f = sidebar_controls()
    metric = MAP_METRICS[f["metric_label"]]
    scope_df = world[world["iso_code"].isin(EUROPE_ISO)] if f["scope"] == "Europa" else world

    year = st.slider("Anno", min_value=WORLD_YEAR_START, max_value=WORLD_YEAR_END, value=2022)
    df_year = scope_df[scope_df["year"] == year]

    kpis = get_scope_kpis(df_year)
    n_with_metric = int(df_year[metric["col"]].notna().sum())

    # Scala colore fissata sul range della metrica nell'intero ambito (tutti gli anni), non sul
    # solo anno selezionato: altrimenti muovendo lo slider la legenda si ricalibra ogni volta e i
    # colori non sono più confrontabili anno per anno.
    color_min = scope_df[metric["col"]].min()
    color_max = scope_df[metric["col"]].max()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"Paesi in {f['scope']}", f"{kpis['n_countries']}")
    c2.metric("Con dato per la metrica", f"{n_with_metric}")
    c3.metric("Generazione totale", f"{kpis['total_generation']:,.0f} TWh")
    c4.metric(
        "Intensità di carbonio",
        f"{kpis['carbon_intensity']:.0f} gCO₂/kWh" if pd.notna(kpis["carbon_intensity"]) else "n.d.",
    )
    c5.metric("Quota rinnovabili", f"{kpis['rinnovabili']:.1f}%")

    fig = px.choropleth(
        df_year, locations="iso_code", color=metric["col"], hover_name="country",
        color_continuous_scale=metric["colorscale"],
        range_color=(color_min, color_max),
        scope="europe" if f["scope"] == "Europa" else "world",
        labels={metric["col"]: f["metric_label"]},
        title=f"{f['metric_label']} — {year}",
        template="plotly_white",
    )
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, width="stretch")
    st.caption(SOURCE_NOTE)


if __name__ == "__main__":
    main()
