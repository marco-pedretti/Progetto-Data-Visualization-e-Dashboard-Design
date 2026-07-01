"""Costanti e funzioni condivise tra le pagine della dashboard Streamlit.

Riproduce la stessa logica del Cap. 4 di eda_energia_europa.ipynb (panel bilanciato,
palette, fonte) in un unico punto, per evitare che le pagine divergano tra loro.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"

EUROPE_ISO = {
    "ALB", "AND", "AUT", "BLR", "BEL", "BIH", "BGR", "HRV", "CYP", "CZE",
    "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ITA",
    "XKX", "LVA", "LIE", "LTU", "LUX", "MLT", "MDA", "MCO", "MNE", "NLD",
    "MKD", "NOR", "POL", "PRT", "ROU", "RUS", "SMR", "SRB", "SVK", "SVN",
    "ESP", "SWE", "CHE", "UKR", "GBR", "VAT",
}

KEY_COLS = [
    "electricity_generation",
    "fossil_electricity",
    "nuclear_electricity",
    "renewables_electricity",
]

SOURCE_COLS = {"fossile": "fossil", "nucleare": "nuclear", "rinnovabili": "renewables"}

PALETTE = {"fossile": "#999999", "nucleare": "#E69F00", "rinnovabili": "#009E73", "calo": "#D55E00"}
SOURCE_NOTE = "Fonte: OWID Energy Dataset (Ember; Energy Institute)"

PANEL_YEAR_START = 1990
PANEL_YEAR_END = 2022

PROFILE_COUNTRIES = ["France", "Germany", "Poland", "Denmark", "Italy"]
# Esclusi dal panel bilanciato per serie incomplete 1990-2022 (Cap. 4.1): selezionabili
# a parte con avviso, mai inclusi di default (Svizzera e Islanda sono casi estremi).
EXTRA_COUNTRIES = ["Switzerland", "Iceland"]
# Paesi da evidenziare nello scatter di correlazione (Cap. 4.6): eccezione (calo nucleare
# concomitante alla crescita rinnovabile) o profilo di riferimento già discusso altrove.
HIGHLIGHT_COUNTRIES = ["Germany", "Lithuania", "Denmark", "France", "Sweden", "Italy"]


@st.cache_data(show_spinner="Carico il dataset OWID...")
def load_raw_data() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "owid-energy-data.csv")


@st.cache_data(show_spinner="Costruisco il panel bilanciato...")
def get_balanced_panel() -> tuple[pd.DataFrame, list[str], list[str]]:
    """Ritorna (bal_all, complete_countries, excluded): panel 1990-2022 con serie complete su KEY_COLS.

    Un paese entra nel panel solo se ha dati validi su tutte le KEY_COLS per ogni anno
    1990-2022 (stessa regola del Cap. 4.1 del notebook).
    """
    df = load_raw_data()
    df_eu = df[df["iso_code"].isin(EUROPE_ISO)].copy()
    window = df_eu[(df_eu["year"] >= PANEL_YEAR_START) & (df_eu["year"] <= PANEL_YEAR_END)]

    complete_countries = sorted(
        country
        for country, grp in window.groupby("country")
        if grp.set_index("year").reindex(range(PANEL_YEAR_START, PANEL_YEAR_END + 1))[KEY_COLS]
        .notna().all().all()
    )
    excluded = sorted(set(df_eu["country"].unique()) - set(complete_countries))
    bal_all = window[window["country"].isin(complete_countries)].copy()
    return bal_all, complete_countries, excluded


def get_extended_panel(extra_countries: list[str]) -> pd.DataFrame:
    """Panel bilanciato + eventuali paesi extra (Svizzera/Islanda) richiesti esplicitamente in sidebar."""
    bal_all, _, _ = get_balanced_panel()
    if not extra_countries:
        return bal_all
    df = load_raw_data()
    df_eu = df[df["iso_code"].isin(EUROPE_ISO)].copy()
    window = df_eu[(df_eu["year"] >= PANEL_YEAR_START) & (df_eu["year"] <= PANEL_YEAR_END)]
    extra = window[window["country"].isin(extra_countries)]
    return pd.concat([bal_all, extra], ignore_index=True)


def weighted_shares(d: pd.DataFrame) -> dict:
    """Quote fossile/nucleare/rinnovabili pesate per generazione, su un blocco dati già filtrato."""
    tot = d["electricity_generation"].sum()
    return {label: d[f"{col}_electricity"].sum() / tot * 100 for label, col in SOURCE_COLS.items()}


def get_share_deltas(bal_all: pd.DataFrame, year_start: int, year_end: int) -> pd.DataFrame:
    """Variazione delle quote fossile/nucleare/rinnovabili tra due anni, un valore per paese.

    Stessa logica del Cap. 4.4/4.6 del notebook (pivot su due anni, differenza). Richiesta da
    entrambe le pagine "Chi sostituisce chi" (ranking e correlazione) sugli stessi due anni.
    """
    two_years = bal_all[bal_all["year"].isin([year_start, year_end])].pivot_table(
        index="country", columns="year",
        values=["fossil_share_elec", "nuclear_share_elec", "renewables_share_elec"],
    )
    return pd.DataFrame({
        "d_fossil": two_years["fossil_share_elec"][year_end] - two_years["fossil_share_elec"][year_start],
        "d_nuclear": two_years["nuclear_share_elec"][year_end] - two_years["nuclear_share_elec"][year_start],
        "d_renewables": two_years["renewables_share_elec"][year_end] - two_years["renewables_share_elec"][year_start],
        "start_renewables": two_years["renewables_share_elec"][year_start],
        "start_nuclear": two_years["nuclear_share_elec"][year_start],
    })


@st.cache_data(show_spinner="Calcolo l'intensità di carbonio...")
def get_carbon_intensity() -> pd.DataFrame:
    """Intensità di carbonio (gCO2eq/kWh): media pesata sul panel bilanciato + validazione OWID.

    Esclude dal calcolo, numeratore e denominatore insieme, le righe senza carbon_intensity_elec:
    la Russia non ha questa colonna per il 1990-1999 e, se non esclusa da entrambi i lati del
    rapporto, abbassa artificialmente la media proprio nei primi anni (bug trovato e corretto nel
    Cap. 4.7 del notebook). "europe_owid" è l'aggregato pubblicato direttamente da OWID, usato lì
    come validazione indipendente del calcolo sul panel.
    """
    bal_all, _, _ = get_balanced_panel()
    valid = bal_all[bal_all["carbon_intensity_elec"].notna()]
    panel_avg = valid.groupby("year").apply(
        lambda g: (g["carbon_intensity_elec"] * g["electricity_generation"]).sum() / g["electricity_generation"].sum()
    )
    df = load_raw_data()
    europe_owid = df[df["country"] == "Europe"].set_index("year")["carbon_intensity_elec"].reindex(panel_avg.index)
    return pd.DataFrame({"panel_bilanciato": panel_avg, "europe_owid": europe_owid})
