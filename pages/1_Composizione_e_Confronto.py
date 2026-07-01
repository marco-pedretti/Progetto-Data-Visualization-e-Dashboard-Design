"""
Pagina 1 — Composizione & Confronto (Esplora)
================================================
Filtri liberi su paesi e periodo, ma vincolati al panel bilanciato: il multiselect
parte dai 33 paesi con serie complete 1990-2022 (Cap. 4.1 del notebook); Svizzera e
Islanda — esclusi di default perché profili estremi che spostano le medie — sono
aggiungibili solo esplicitamente, con l'avviso già presente nel notebook.

Composizione (stacked area, TWh) e Confronto (linee di quota %, 0-100) sono sempre
due grafici separati, mai un dual axis: rispondono a due task comunicativi diversi
(Cap. 4.2).
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from common import (
    EXTRA_COUNTRIES,
    PALETTE,
    PANEL_YEAR_END,
    PANEL_YEAR_START,
    SOURCE_NOTE,
    get_balanced_panel,
    get_extended_panel,
)

SOURCES = [("Fossile", "fossil_electricity", "fossile"), ("Nucleare", "nuclear_electricity", "nucleare"), ("Rinnovabili", "renewables_electricity", "rinnovabili")]
COLOR_MAP = {label: PALETTE[key] for label, _, key in SOURCES}

_, complete_countries, _ = get_balanced_panel()


def sidebar_controls() -> dict:
    with st.sidebar:
        st.header("🔧 Filtri")

        countries = st.multiselect(
            "Paesi (panel bilanciato)",
            complete_countries,
            default=complete_countries,
        )
        extra = st.multiselect(
            "Aggiungi casi esclusi dal panel",
            EXTRA_COUNTRIES,
            default=[],
            help=(
                "Svizzera e Islanda hanno serie incomplete 1990-2022 e sono esclusi di "
                "default (Cap. 4.1 del notebook): Svizzera è nucleare+idro con fossile "
                "quasi assente, Islanda è 100% rinnovabile/geotermico — profili estremi "
                "che spostano le medie se inclusi senza dichiararlo."
            ),
        )
        year_range = st.slider(
            "Periodo",
            min_value=PANEL_YEAR_START, max_value=PANEL_YEAR_END,
            value=(PANEL_YEAR_START, PANEL_YEAR_END),
        )
        task = st.radio(
            "Cosa vuoi vedere?",
            ["Composizione (di cosa è fatto il totale)", "Confronto (quota di ciascuna fonte)"],
        )

        st.divider()
        st.caption(
            "Composizione e confronto restano sempre due grafici separati, mai un unico "
            "grafico a doppio asse: rispondono a domande diverse (Cap. 4.2 del notebook)."
        )

    return dict(countries=countries + extra, year_range=year_range, task=task)


def main() -> None:
    st.title("📊 Composizione & Confronto")
    st.markdown(
        "Scegli paesi e periodo in sidebar. Lo **stacked area** risponde alla domanda "
        '"di cosa è fatto il totale" (composizione, in TWh); le **linee su base 0–100%** '
        'rispondono a "quale fonte pesa di più" (confronto). Non sono lo stesso grafico letto '
        "in due modi diversi: sono due encoding scelti per due task diversi (Cleveland & McGill)."
    )

    f = sidebar_controls()
    if not f["countries"]:
        st.warning("⚠️ Seleziona almeno un paese in sidebar.")
        st.stop()

    extra_selected = [c for c in f["countries"] if c not in complete_countries]
    d = get_extended_panel(extra_selected)
    d = d[d["country"].isin(f["countries"]) & d["year"].between(*f["year_range"])]

    agg = d.groupby("year")[
        ["electricity_generation", "fossil_electricity", "nuclear_electricity", "renewables_electricity"]
    ].sum()
    share = agg.div(agg["electricity_generation"], axis=0) * 100

    st.caption(f"{len(f['countries'])} paesi selezionati · {f['year_range'][0]}–{f['year_range'][1]}")

    if f["task"].startswith("Composizione"):
        long_twh = agg.reset_index().melt(
            id_vars="year", value_vars=[c for _, c, _ in SOURCES], var_name="fonte", value_name="TWh"
        )
        long_twh["fonte"] = long_twh["fonte"].map({c: label for label, c, _ in SOURCES})
        fig = px.area(
            long_twh, x="year", y="TWh", color="fonte",
            color_discrete_map=COLOR_MAP,
            category_orders={"fonte": [label for label, _, _ in SOURCES]},
            labels={"year": "", "TWh": "TWh", "fonte": ""},
            title="Composizione assoluta del mix elettrico (TWh)",
            template="plotly_white",
        )
        fig.update_layout(height=520)
        st.plotly_chart(fig, width="stretch")
    else:
        long_share = share.reset_index().melt(
            id_vars="year", value_vars=[c for _, c, _ in SOURCES], var_name="fonte", value_name="quota"
        )
        long_share["fonte"] = long_share["fonte"].map({c: label for label, c, _ in SOURCES})
        fig = px.line(
            long_share, x="year", y="quota", color="fonte",
            color_discrete_map=COLOR_MAP,
            category_orders={"fonte": [label for label, _, _ in SOURCES]},
            labels={"year": "", "quota": "% della generazione", "fonte": ""},
            title="Quota di ciascuna fonte sul totale generato (%)",
            template="plotly_white",
        )
        fig.update_traces(line=dict(width=3))
        fig.update_yaxes(range=[0, 100])
        fig.update_layout(height=520)

        crossover = share[share["renewables_electricity"] > share["nuclear_electricity"]].index.min()
        if pd.notna(crossover):
            fig.add_vline(x=crossover, line_dash="dot", line_color="gray")
            fig.add_annotation(x=crossover, y=95, text=f"Rinnovabili > nucleare dal {crossover}", showarrow=False)

        st.plotly_chart(fig, width="stretch")

    st.caption(SOURCE_NOTE)


if __name__ == "__main__":
    main()
