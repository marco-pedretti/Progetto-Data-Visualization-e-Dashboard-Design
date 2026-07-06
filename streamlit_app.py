"""
Mix energetico in Europa: Dashboard
======================================
Entrypoint/router: definisce la navigazione (barra in alto, sezioni Esplora/Storia)
e delega l'esecuzione alla pagina scelta. `st.set_page_config` va chiamato una sola
volta per l'intera app: vive qui, non nelle singole pagine.

Struttura dell'app (vedi pages/):
    Home                    → panoramica, KPI, guida alla navigazione
    Strategie_a_Confronto   → Esplora: confronto libero da due a quattro paesi a scelta
    Mappa_Europa_Mondo      → Esplora: coropleta con ambito/metrica/anno liberi
    Scheda_Paese            → Esplora: scheda libera su un'entità qualunque, mondo incluso
    Chi_Sostituisce_Chi     → Storia: ranking e correlazione, narrazione guidata
    Declino_Nucleare        → Storia: picco/evento/crollo del nucleare, narrazione guidata
    Firme_Storiche          → Storia: i dati mancanti come indicatore geopolitico (Cap. 3.4)

Le pagine "Esplora" permettono di scegliere liberamente paesi e periodo, ma restano
vincolate al panel bilanciato (33 paesi con serie complete 1990-2022, Svizzera e
Islanda selezionabili a parte con avviso) per evitare di ricreare gli artefatti di
copertura descritti nel notebook (eda_energia_europa.ipynb, Cap. 3-4), eccetto
"Scheda Paese", pensata apposta per esplorare una singola entità qualunque senza
questo vincolo (non serve confrontare serie tra paesi). Le pagine "Storia" hanno una
narrazione fissa, con al più una piccola libertà di sostituzione.
"""

import streamlit as st

st.set_page_config(
    page_title="Mix energetico in Europa",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# I KPI in colonne strette (es. mappa a 5 colonne) tagliano l'unità di misura con
# l'ellissi di default di st.metric: qui si consente al valore di andare a capo.
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        white-space: normal;
        overflow-wrap: break-word;
        font-size: 1.6rem;
        line-height: 1.2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pages = st.navigation(
    {
        "": [st.Page("pages/Home.py", title="Home", icon="⚡", default=True)],
        "Esplora": [
            st.Page("pages/Scheda_Paese.py", title="Scheda Paese", icon="🔎"),
            st.Page("pages/Strategie_a_Confronto.py", title="Strategie a confronto", icon="🆚"),
            st.Page("pages/Mappa_Europa_Mondo.py", title="Mappa Europa/Mondo", icon="🗺️"),
        ],
        "Storia": [
            st.Page("pages/Chi_Sostituisce_Chi.py", title="Chi sostituisce chi", icon="🔀"),
            st.Page("pages/Declino_Nucleare.py", title="Declino del nucleare", icon="☢️"),
            st.Page("pages/Firme_Storiche.py", title="Firme storiche nei dati", icon="🕰️"),
        ],
    },
    position="top",
)
pages.run()
