"""
Pagina 2 — Velocità di crescita (Esplora)
============================================
Confronta la crescita assoluta (TWh) e l'indice di crescita (base 100 = primo anno
selezionato) di una fonte tra i paesi scelti — stessa tecnica del *price index*
usata nell'esempio del corso (altri_file/elaborato_airbnb/pages/2_Trend.py).

L'indice da solo è fuorviante quando i paesi scelti partono da livelli molto
diversi (Cap. 4.5 del notebook: Danimarca e Polonia esplodono nell'indice pur
crescendo meno in TWh della Germania). Per questo qui i due grafici sono sempre
affiancati, e un avviso compare automaticamente quando le basi di partenza
differiscono di più di un ordine di grandezza.
"""

import plotly.express as px
import streamlit as st

from common import PALETTE, PANEL_YEAR_END, PANEL_YEAR_START, PROFILE_COUNTRIES, SOURCE_NOTE, get_balanced_panel

SOURCE_OPTIONS = {
    "Rinnovabili": ("renewables_electricity", "rinnovabili"),
    "Fossile": ("fossil_electricity", "fossile"),
    "Nucleare": ("nuclear_electricity", "nucleare"),
    "Generazione totale": ("electricity_generation", "calo"),
}

bal_all, complete_countries, _ = get_balanced_panel()


def sidebar_controls() -> dict:
    with st.sidebar:
        st.header("🔧 Filtri")

        countries = st.multiselect(
            "Paesi da confrontare (panel bilanciato)",
            complete_countries,
            default=PROFILE_COUNTRIES,
            help="Limitato al panel bilanciato: l'indice richiede una serie completa dall'anno base.",
        )
        source_label = st.radio("Fonte", list(SOURCE_OPTIONS.keys()))
        year_range = st.slider(
            "Periodo (l'anno iniziale è la base = 100)",
            min_value=PANEL_YEAR_START, max_value=PANEL_YEAR_END,
            value=(PANEL_YEAR_START, PANEL_YEAR_END),
        )

        st.divider()
        st.caption(
            "L'indice va sempre letto insieme al valore assoluto: da solo esagera i paesi "
            "con base di partenza quasi nulla (Cap. 4.5 del notebook)."
        )

    return dict(countries=countries, source_label=source_label, year_range=year_range)


def main() -> None:
    st.title("📈 Velocità di crescita")
    st.markdown(
        "Scegli paesi, fonte e periodo in sidebar. Il pannello sinistro mostra il **valore "
        "assoluto** (TWh), il destro l'**indice di crescita** rispetto al primo anno "
        "selezionato (base = 100) — la stessa lettura che, applicata da sola, può ingannare "
        "quando le basi di partenza sono molto diverse tra loro."
    )

    f = sidebar_controls()
    if len(f["countries"]) == 0:
        st.warning("⚠️ Seleziona almeno un paese in sidebar.")
        st.stop()

    col_name, palette_key = SOURCE_OPTIONS[f["source_label"]]
    year_start, year_end = f["year_range"]

    d = bal_all[bal_all["country"].isin(f["countries"]) & bal_all["year"].between(year_start, year_end)]
    wide = d.pivot(index="year", columns="country", values=col_name)

    base_values = wide.loc[year_start]
    if (base_values <= 0).any():
        st.warning(
            "⚠️ Uno o più paesi hanno valore zero nell'anno base per questa fonte: l'indice "
            "non è calcolabile per quei paesi (divisione per zero) e viene omesso dal grafico."
        )
    valid_countries = base_values[base_values > 0].index
    idx = wide[valid_countries].div(base_values[valid_countries]) * 100

    ratio = base_values[valid_countries].max() / base_values[valid_countries].min()
    if ratio > 10:
        st.warning(
            f"⚠️ Le basi di partenza ({year_start}) differiscono di un fattore {ratio:,.0f}× tra i "
            "paesi selezionati: l'indice a destra esagera chi parte da un valore quasi nullo. "
            "Leggilo sempre insieme al grafico assoluto a sinistra, non da solo."
        )

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.line(
            wide.reset_index().melt(id_vars="year", var_name="country", value_name="value"),
            x="year", y="value", color="country",
            labels={"year": "", "value": "TWh", "country": ""},
            title=f"{f['source_label']} — valore assoluto (TWh)",
            template="plotly_white",
        )
        fig.update_yaxes(rangemode="tozero")
        fig.update_layout(height=460)
        st.plotly_chart(fig, width="stretch")

    with col_b:
        fig = px.line(
            idx.reset_index().melt(id_vars="year", var_name="country", value_name="index"),
            x="year", y="index", color="country",
            labels={"year": "", "index": f"Indice ({year_start}=100)", "country": ""},
            title=f"{f['source_label']} — indice di crescita ({year_start}=100)",
            template="plotly_white",
        )
        fig.add_hline(y=100, line_dash="dot", line_color="gray")
        fig.update_layout(height=460)
        st.plotly_chart(fig, width="stretch")

    st.caption(SOURCE_NOTE)


if __name__ == "__main__":
    main()
