"""
Mix energetico in Europa — Dashboard
======================================
Entrypoint/router: definisce la navigazione (barra in alto, sezioni Esplora/Storia)
e delega l'esecuzione alla pagina scelta. `st.set_page_config` va chiamato una sola
volta per l'intera app: vive qui, non nelle singole pagine.

Struttura dell'app (vedi pages/):
    0_Home                       → panoramica, KPI, guida alla navigazione
    1_Composizione_e_Confronto   → Esplora: filtri liberi (paesi, anni), composizione vs confronto
    2_Velocita_di_Crescita       → Esplora: filtri liberi (paesi, fonte), valore assoluto vs indice
    6_Mappa_Europa_Mondo         → Esplora: coropleta con ambito/metrica/anno liberi
    8_Scheda_Paese               → Esplora: scheda libera su un'entità qualunque, mondo incluso
    3_Cinque_Strategie_Nazionali → Storia: profili fissi, narrazione guidata
    4_Chi_Sostituisce_Chi        → Storia: ranking e correlazione, narrazione guidata
    5_Intensita_di_Carbonio      → Storia: decarbonizzazione, narrazione guidata
    7_Declino_Nucleare           → Storia: picco/evento/crollo del nucleare, narrazione guidata

Le pagine "Esplora" permettono di scegliere liberamente paesi e periodo, ma restano
vincolate al panel bilanciato (33 paesi con serie complete 1990-2022, Svizzera e
Islanda selezionabili a parte con avviso) per evitare di ricreare gli artefatti di
copertura descritti nel notebook (eda_energia_europa.ipynb, Cap. 3-4) — eccetto
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
        "": [st.Page("pages/0_Home.py", title="Home", icon="⚡", default=True)],
        "Esplora": [
            st.Page("pages/1_Composizione_e_Confronto.py", title="Composizione & Confronto", icon="📊"),
            st.Page("pages/2_Velocita_di_Crescita.py", title="Velocità di crescita", icon="📈"),
            st.Page("pages/6_Mappa_Europa_Mondo.py", title="Mappa Europa/Mondo", icon="🗺️"),
            st.Page("pages/8_Scheda_Paese.py", title="Scheda Paese", icon="🔎"),
        ],
        "Storia": [
            st.Page("pages/3_Cinque_Strategie_Nazionali.py", title="Cinque strategie nazionali", icon="🧭"),
            st.Page("pages/4_Chi_Sostituisce_Chi.py", title="Chi sostituisce chi", icon="🔀"),
            st.Page("pages/5_Intensita_di_Carbonio.py", title="Intensità di carbonio", icon="🌍"),
            st.Page("pages/7_Declino_Nucleare.py", title="Declino del nucleare", icon="☢️"),
        ],
    },
    position="top",
)
pages.run()
