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

# Colore per i punti "evidenziati" negli scatter (paesi di riferimento/eccezione): blu Okabe-Ito,
# NON PALETTE["calo"] (vermillion), che in tutta la dashboard significa "calo/anomalia": i punti
# evidenziati non sono anomalie, sono solo riferimenti. Usato negli scatter della pagina
# "Chi sostituisce chi" così l'evidenza ha sempre lo stesso significato.
HIGHLIGHT_COUNTRY = "#0072B2"

# Import/export netto: il segno è una direzione (chi compra vs chi vende elettricità), non un
# giudizio di merito: niente verde/rosso ("buono/cattivo" fuori luogo qui). Due toni tenui,
# distinti per tonalità (ambra vs blu, non solo per luminosità) così restano leggibili anche in
# scala di grigi o per un daltonico, e abbastanza chiari da non sparire sullo sfondo scuro.
# L'ambra va sull'import, non sull'export: un tono caldo sui valori negativi (l'export è la barra
# "sotto zero") si legge come un doppio segnale negativo, facendo sembrare l'export un problema.
# Condiviso tra Scheda Paese e Strategie a confronto (stesso significato, stesso colore ovunque).
IMPORT_COLOR = "#D9A566"  # importatore netto (valore positivo)
EXPORT_COLOR = "#7FA6C9"  # esportatore netto (valore negativo)

PANEL_YEAR_START = 1990
PANEL_YEAR_END = 2022

# Nomi italiani dei paesi del panel (i dati OWID usano l'inglese): la UI è in italiano, così le
# etichette dei grafici e la prosa restano coerenti. `.get(name, name)` come fallback per entità
# non mappate. Condiviso; alcune pagine hanno ancora un dizionario locale ridotto (storico).
IT_NAME = {
    "Austria": "Austria", "Belgium": "Belgio", "Bulgaria": "Bulgaria", "Croatia": "Croazia",
    "Cyprus": "Cipro", "Czechia": "Cechia", "Denmark": "Danimarca", "Estonia": "Estonia",
    "Finland": "Finlandia", "France": "Francia", "Germany": "Germania", "Greece": "Grecia",
    "Hungary": "Ungheria", "Ireland": "Irlanda", "Italy": "Italia", "Latvia": "Lettonia",
    "Lithuania": "Lituania", "Luxembourg": "Lussemburgo", "Malta": "Malta",
    "Netherlands": "Paesi Bassi", "North Macedonia": "Macedonia del Nord", "Norway": "Norvegia",
    "Poland": "Polonia", "Portugal": "Portogallo", "Romania": "Romania", "Russia": "Russia",
    "Serbia": "Serbia", "Slovakia": "Slovacchia", "Slovenia": "Slovenia", "Spain": "Spagna",
    "Sweden": "Svezia", "Ukraine": "Ucraina", "United Kingdom": "Regno Unito",
}

# Cap. 4.6: i 5 paesi isolati in 4.5 come eccezione (calo nucleare concomitante alla crescita
# rinnovabile), con l'evento politico che spiega il declino: anno e didascalia verificati contro
# il picco/valore 2022 reale di nuclear_share_elec, non solo affermati.
NUCLEAR_EVENTS = {
    "Lithuania": (2009, "Chiusura Ignalina (UE)"),
    "Germany": (2011, "Fukushima → Energiewende"),
    "Sweden": (2005, "Chiusura Barsebäck"),
    "Belgium": (2003, "Legge di phase-out"),
    "France": (2015, "Legge transizione energetica"),
}

# Range esteso al massimo disponibile nel dataset (Cap. 3.2/3.3 del notebook): 1985 è il floor
# storico di electricity_generation (Cap. 3.4, "Firme storiche"), 2025 è l'ultimo anno pubblicato
# ma pesantemente right-censored fuori Europa (~90 paesi su 220). In precedenza il range era
# ristretto a 2000-2024 proprio per evitare troppi paesi "grigi silenziosi"; ora che il dato
# mancante ha un indicatore esplicito e consistente (vedi MAP_NO_DATA_COLOR), l'intero range è
# mostrabile onestamente: la sparsità diventa informazione (es. carbon_intensity_elec non esiste
# per NESSUN paese nel 1985: la mappa sarà tutta "nessun dato", correttamente).
WORLD_YEAR_START = 1985
WORLD_YEAR_END = 2025

# Colore fisso per "nessun dato disponibile" nella mappa, indipendente dalla metrica scelta.
# Deliberatamente estraneo alle 5 colorscale sequenziali usate sotto (Greys/Oranges/Greens/
# YlOrRd/Blues): un grigio si confonderebbe con l'estremo chiaro di "Greys" o del grigio di
# default di Plotly per i paesi senza traccia, rendendo "nessun dato" indistinguibile da "valore
# basso". Un tono lavanda non compare in nessuna delle scale, quindi il significato è univoco a
# prescindere dalla metrica visualizzata.
MAP_NO_DATA_COLOR = "#8A7CA8"

# Metriche disponibili per la mappa (solo settore elettrico, non emissioni economy-wide):
# scala colore a tinta unica coerente con PALETTE per le tre fonti, YlOrRd per l'intensità
# di carbonio (sequenziale: più scuro = più emissioni; NON RdYlGn_r come il prezzo Airbnb
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


@st.cache_data(show_spinner="Carico i dati europei...")
def get_europe_window() -> pd.DataFrame:
    """Tutte le righe europee 1990-2022, serie complete o no: universo di selezione per le
    pagine Esplora (nessun paese europeo escluso, a differenza del panel bilanciato)."""
    df = load_raw_data()
    df_eu = df[df["iso_code"].isin(EUROPE_ISO)].copy()
    return df_eu[(df_eu["year"] >= PANEL_YEAR_START) & (df_eu["year"] <= PANEL_YEAR_END)]


@st.cache_data(show_spinner="Costruisco il panel bilanciato...")
def get_balanced_panel() -> tuple[pd.DataFrame, list[str], list[str]]:
    """Ritorna (bal_all, complete_countries, excluded): panel 1990-2022 con serie complete su KEY_COLS.

    Un paese entra nel panel solo se ha dati validi su tutte le KEY_COLS per ogni anno
    1990-2022 (stessa regola del Cap. 4.1 del notebook). Usato solo dalle pagine Storia, dove
    la media aggregata richiede serie complete; le pagine Esplora usano invece
    `get_europe_window()`, senza esclusioni.
    """
    window = get_europe_window()
    complete_countries = sorted(
        country
        for country, grp in window.groupby("country")
        if grp.set_index("year").reindex(range(PANEL_YEAR_START, PANEL_YEAR_END + 1))[KEY_COLS]
        .notna().all().all()
    )
    excluded = sorted(set(window["country"].unique()) - set(complete_countries))
    bal_all = window[window["country"].isin(complete_countries)].copy()
    return bal_all, complete_countries, excluded


def weighted_shares(d: pd.DataFrame) -> dict:
    """Quote fossile/nucleare/rinnovabili pesate per generazione, su un blocco dati già filtrato."""
    tot = d["electricity_generation"].sum()
    return {label: d[f"{col}_electricity"].sum() / tot * 100 for label, col in SOURCE_COLS.items()}


def get_share_deltas(bal_all: pd.DataFrame, year_start: int, year_end: int) -> pd.DataFrame:
    """Variazione delle quote fossile/nucleare/rinnovabili tra due anni, un valore per paese.

    Stessa logica del Cap. 4.3/4.5 del notebook (pivot su due anni, differenza). Richiesta da
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


@st.cache_data(show_spinner="Carico la storia del nucleare...")
def get_nuclear_history(countries: list[str]) -> pd.DataFrame:
    """Quota nucleare 1985-2022 per un elenco di paesi, dalla serie estesa (non il panel bilanciato).

    Serve perché il picco storico di alcuni paesi (Belgio 1986, Lituania 1993) cade a ridosso o
    prima della soglia 1990 del panel bilanciato (Cap. 4.1): qui non serve la completezza su tutte
    le KEY_COLS, solo nuclear_share_elec (Cap. 4.6 del notebook).
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

    Mascheramento NaN per l'intensità di carbonio: esclude, numeratore e denominatore insieme,
    i paesi senza carbon_intensity_elec quell'anno (es. la Russia non ha la colonna per il
    1990-1999), che altrimenti abbasserebbero artificialmente la media pesata.
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
    dai nomi interni di Streamlit: per questo la versione è pinnata in requirements.txt.
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
