"""
Mix energetico in Europa — Dashboard
======================================
Home: panoramica, KPI e guida alla navigazione.

Struttura dell'app (vedi pages/):
    1_Composizione_e_Confronto  → Esplora: filtri liberi (paesi, anni), composizione vs confronto
    2_Velocita_di_Crescita      → Esplora: filtri liberi (paesi, fonte), valore assoluto vs indice
    3_Cinque_Strategie_Nazionali → Storia: profili fissi, narrazione guidata
    4_Chi_Sostituisce_Chi        → Storia: ranking e correlazione, narrazione guidata
    5_Intensita_di_Carbonio      → Storia: decarbonizzazione, narrazione guidata

Le pagine "Esplora" permettono di scegliere liberamente paesi e periodo, ma restano
vincolate al panel bilanciato (33 paesi con serie complete 1990-2022, Svizzera e
Islanda selezionabili a parte con avviso) per evitare di ricreare gli artefatti di
copertura descritti nel notebook (eda_energia_europa.ipynb, Cap. 3-4). Le pagine
"Storia" hanno una narrazione fissa, con al più una piccola libertà di sostituzione.
"""

import streamlit as st

from common import PALETTE, SOURCE_NOTE, get_balanced_panel, weighted_shares

st.set_page_config(
    page_title="Mix energetico in Europa",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚡ Mix energetico in Europa")
st.markdown(
    """
    Come si è evoluto il modo in cui l'Europa produce elettricità, tra **fossili**,
    **nucleare** e **rinnovabili**, dal 1990 al 2022? Questa dashboard accompagna il
    notebook di analisi (`eda_energia_europa.ipynb`) ed è organizzata in due tipi di
    pagine, elencate nel menu a sinistra:

    - **Esplora** (pagine 1-2): filtri liberi su paesi e periodo, per fare le proprie
      domande ai dati.
    - **Storia** (pagine 3-5): narrazione guidata sui risultati principali dell'analisi,
      con libertà di personalizzazione limitata — qui l'obiettivo è comunicare una
      conclusione verificata, non esplorare.
    """
)

bal_all, complete_countries, excluded = get_balanced_panel()
last_year = int(bal_all["year"].max())
latest = bal_all[bal_all["year"] == last_year]
shares = weighted_shares(latest)

st.divider()
st.subheader(f"Il mix elettrico europeo nel {last_year}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Paesi nel panel", f"{len(complete_countries)}", help="Serie complete 1990–2022 sulle variabili chiave")
c2.metric("Fossile", f"{shares['fossile']:.1f}%", help="Quota pesata per generazione")
c3.metric("Nucleare", f"{shares['nucleare']:.1f}%", help="Quota pesata per generazione")
c4.metric("Rinnovabili", f"{shares['rinnovabili']:.1f}%", help="Quota pesata per generazione")

st.divider()

st.markdown("**Legenda colori** (fissa in tutta la dashboard, palette colorblind-safe Okabe-Ito):")
leg1, leg2, leg3, leg4 = st.columns(4)
for col, (label, color) in zip((leg1, leg2, leg3, leg4), [
    ("Fossile", PALETTE["fossile"]),
    ("Nucleare", PALETTE["nucleare"]),
    ("Rinnovabili", PALETTE["rinnovabili"]),
    ("Calo/anomalia", PALETTE["calo"]),
]):
    col.markdown(
        f'<span style="display:inline-block;width:14px;height:14px;background:{color};'
        f'border-radius:2px;margin-right:6px;"></span>{label}',
        unsafe_allow_html=True,
    )

st.caption(
    f"{SOURCE_NOTE}. Panel bilanciato: {len(complete_countries)} paesi europei con serie "
    f"complete 1990–{last_year}. Esclusi (serie incomplete): {', '.join(excluded)} — "
    "Svizzera e Islanda restano selezionabili a parte nelle pagine Esplora."
)
