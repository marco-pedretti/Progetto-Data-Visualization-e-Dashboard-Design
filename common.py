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

# Import/export netto: il segno è una direzione (chi compra vs chi vende elettricità), non un
# giudizio di merito — niente verde/rosso ("buono/cattivo" fuori luogo qui). Due toni tenui,
# distinti per tonalità (ambra vs blu, non solo per luminosità) così restano leggibili anche in
# scala di grigi o per un daltonico, e abbastanza chiari da non sparire sullo sfondo scuro.
# L'ambra va sull'import, non sull'export: un tono caldo sui valori negativi (l'export è la barra
# "sotto zero") si legge come un doppio segnale negativo, facendo sembrare l'export un problema.
# Condiviso tra Scheda Paese e Strategie a confronto (stesso significato, stesso colore ovunque).
IMPORT_COLOR = "#D9A566"  # importatore netto (valore positivo)
EXPORT_COLOR = "#7FA6C9"  # esportatore netto (valore negativo)

PANEL_YEAR_START = 1990
PANEL_YEAR_END = 2022

PROFILE_COUNTRIES = ["France", "Germany", "Poland", "Denmark", "Italy"]
# Esclusi dal panel bilanciato per serie incomplete 1990-2022 (Cap. 4.1): selezionabili
# a parte con avviso, mai inclusi di default (Svizzera e Islanda sono casi estremi).
EXTRA_COUNTRIES = ["Switzerland", "Iceland"]
# Paesi da evidenziare nello scatter di correlazione (Cap. 4.6): eccezione (calo nucleare
# concomitante alla crescita rinnovabile) o profilo di riferimento già discusso altrove.
HIGHLIGHT_COUNTRIES = ["Germany", "Lithuania", "Denmark", "France", "Sweden", "Italy"]

# Cap. 4.8: i 5 paesi isolati in 4.6 come eccezione (calo nucleare concomitante alla crescita
# rinnovabile), con l'evento politico che spiega il declino — anno e didascalia verificati contro
# il picco/valore 2022 reale di nuclear_share_elec, non solo affermati.
NUCLEAR_EVENTS = {
    "Lithuania": (2009, "Chiusura Ignalina (UE)"),
    "Germany": (2011, "Fukushima → Energiewende"),
    "Sweden": (2005, "Chiusura Barsebäck"),
    "Belgium": (2003, "Legge di phase-out"),
    "France": (2015, "Legge transizione energetica"),
}

# Copertura mondiale: prima del 2000 pochissimi paesi fuori Europa hanno dati (Cap. 3.2 del
# notebook), il 2025 è pesantemente right-censored (Cap. 3.3, ~90 paesi su 220). Il range
# 2000-2024 è la finestra con copertura ampia e stabile per tutte le metriche della mappa.
WORLD_YEAR_START = 2000
WORLD_YEAR_END = 2024

# Metriche disponibili per la mappa (solo settore elettrico, non emissioni economy-wide):
# scala colore a tinta unica coerente con PALETTE per le tre fonti, YlOrRd per l'intensità
# di carbonio (sequenziale: più scuro = più emissioni — NON RdYlGn_r come il prezzo Airbnb
# in altri_file: rosso-verde è il caso classico di daltonismo e contraddirebbe la scelta
# Okabe-Ito dichiarata in Home), Blues per la generazione totale (grandezza neutra).
MAP_METRICS = {
    "Quota fossile (%)": {"col": "fossil_share_elec", "colorscale": "Greys"},
    "Quota nucleare (%)": {"col": "nuclear_share_elec", "colorscale": "Oranges"},
    "Quota rinnovabili (%)": {"col": "renewables_share_elec", "colorscale": "Greens"},
    "Intensità di carbonio (gCO2/kWh)": {"col": "carbon_intensity_elec", "colorscale": "YlOrRd"},
    "Generazione totale (TWh)": {"col": "electricity_generation", "colorscale": "Blues"},
}


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


@st.cache_data(show_spinner="Carico la storia del nucleare...")
def get_nuclear_history(countries: list[str]) -> pd.DataFrame:
    """Quota nucleare 1985-2022 per un elenco di paesi, dalla serie estesa (non il panel bilanciato).

    Serve perché il picco storico di alcuni paesi (Belgio 1986, Lituania 1993) cade a ridosso o
    prima della soglia 1990 del panel bilanciato (Cap. 4.1): qui non serve la completezza su tutte
    le KEY_COLS, solo nuclear_share_elec (Cap. 4.8 del notebook).
    """
    df = load_raw_data()
    df_eu = df[df["iso_code"].isin(EUROPE_ISO)].copy()
    d = df_eu[df_eu["country"].isin(countries) & (df_eu["year"] <= PANEL_YEAR_END)]
    return d[["country", "year", "nuclear_share_elec"]].dropna(subset=["nuclear_share_elec"])


@st.cache_data(show_spinner="Carico i dati mondiali...")
def get_world_data() -> pd.DataFrame:
    """Tutti i paesi con iso_code valido (Europa inclusa), esclusi gli aggregati OWID (Cap. 2)."""
    df = load_raw_data()
    return df[df["iso_code"].notna()].copy()


def get_scope_kpis(df_year: pd.DataFrame) -> dict:
    """KPI pesati (generazione, quote, intensità di carbonio) su un blocco dati di un solo anno.

    Stessa regola di mascheramento NaN del Cap. 4.7: l'intensità di carbonio esclude,
    numeratore e denominatore insieme, i paesi senza carbon_intensity_elec quell'anno.
    """
    shares = weighted_shares(df_year)
    ci_valid = df_year[df_year["carbon_intensity_elec"].notna()]
    carbon_intensity = (
        (ci_valid["carbon_intensity_elec"] * ci_valid["electricity_generation"]).sum()
        / ci_valid["electricity_generation"].sum()
        if len(ci_valid) else float("nan")
    )
    return dict(
        n_countries=len(df_year),
        total_generation=df_year["electricity_generation"].sum(),
        carbon_intensity=carbon_intensity,
        **shares,
    )


def limit_page_width(max_px: int = 1200) -> None:
    """Limita la larghezza del contenuto della pagina corrente, centrando il blocco principale.

    Il layout "wide" è impostato globalmente in streamlit_app.py, ma su monitor larghi stira
    eccessivamente testo e grafici; questo helper applica un max-width via CSS scoped alla
    pagina che lo chiama (lo stile iniettato da st.markdown sparisce navigando altrove, perché
    ogni pagina multipage è uno script eseguito da zero). Il selettore data-testid dipende
    dai nomi interni di Streamlit — per questo la versione è pinnata in requirements.txt.
    """
    st.markdown(
        f"""
        <style>
        [data-testid="stMainBlockContainer"] {{
            max-width: {max_px}px;
            margin-left: auto;
            margin-right: auto;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
