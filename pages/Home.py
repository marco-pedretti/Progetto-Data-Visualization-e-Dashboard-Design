"""
Home: landing page. Cos'è la dashboard, com'è organizzata, quali dati la alimentano.

Nota: `st.set_page_config` è chiamato una sola volta nel router (`streamlit_app.py`),
non qui: questa pagina viene eseguita da `st.navigation(...).run()`.

Riscritta il 2026-07-05 (richiesta esplicita dell'utente: la Home precedente "non
convinceva", faceva troppo il lavoro delle pagine). Scelta "landing pulita": la Home
orienta e aggancia, non duplica i contenuti analitici. Rimossi il mini-grafico
d'insieme (quasi identico a quelli delle pagine) e i "tre risultati verificati" con
numeri narrati (spoileravano le Storie); al loro posto card di navigazione con un solo
gancio-domanda per pagina. In fondo, sezione nuova "I dati dietro l'analisi" con download
del dataset OWID grezzo (quello che il notebook analizza davvero) e del codebook,
su richiesta esplicita dell'utente.

Rifiniture successive (richieste esplicite utente, 2026-07-05):
- Larghezza limitata come le altre pagine (`limit_page_width()`); prima era l'unica "wide".
- Legenda colori fissa rimossa: era un residuo del mini-grafico ormai eliminato, senza più
  nulla in pagina a cui riferirsi.
- Rimossa anche l'ultima riga KPI: era l'ultimo residuo del "fare il lavoro delle pagine"
  (una quota decontestualizzata di un solo anno, che vive con contesto nelle pagine). La Home
  ora è pura landing: orienta e aggancia, nessun dato analitico.
- Titolo "Il mix elettrico europeo" (era "Mix energetico in Europa"): preciso rispetto al cuore
  della dashboard (generazione elettrica), non l'energia totale.
- Rimossa la nota metodologica sul panel bilanciato in fondo pagina (richiesta esplicita
  dell'utente): è un dettaglio interno senza un grafico a cui riferirsi qui, e ora che tutti i
  paesi sono selezionabili in ogni pagina Esplora non serve più rassicurare su chi è escluso.
"""

import streamlit as st

from common import DATA_DIR, limit_page_width


@st.cache_data
def _dataset_files() -> tuple[bytes, int, bytes]:
    """Byte grezzi del dataset OWID e del codebook, letti dal disco una sola volta.

    Si serve il CSV integrale (tutto il mondo, tutte le metriche): la fonte reale che il
    notebook analizza, non un sottoinsieme pre-filtrato. Chi scarica deve poter riprodurre
    l'analisi da zero. Cache: il file grezzo (~16MB) va letto una volta, non a ogni rerun.
    """
    data = (DATA_DIR / "owid-energy-data.csv").read_bytes()
    codebook = (DATA_DIR / "owid-energy-codebook.csv").read_bytes()
    n_rows = data.count(b"\n") - 1  # righe dati (esclusa l'intestazione)
    return data, n_rows, codebook


limit_page_width()

st.title("⚡ Il mix elettrico europeo")
st.markdown(
    """
    **Analisi del mix elettrico europeo dal 1990 a oggi: fossili, nucleare e rinnovabili
    a confronto.** Dashboard basata sull'**OWID Energy Dataset**, a supporto del notebook
    di analisi `eda_energia_europa.ipynb`.

    Le pagine, nel menu in alto, si dividono in due categorie: **Esplora**, filtri liberi
    su paesi, periodo e metrica; **Storia**, narrazione guidata su un risultato verificato.
    """
)

st.divider()

# Come è organizzata: le due famiglie di pagine come punti d'ingresso, con un solo
# gancio-domanda per pagina (aggancio, non spoiler: nessun numero narrato qui, quelli
# vivono nelle pagine). Sostituisce sia i "tre risultati verificati" che il mini-grafico.
st.subheader("Cosa trovi")
col_esplora, col_storia = st.columns(2)

with col_esplora:
    st.markdown("#### 🧭 Esplora")
    st.caption("Filtri liberi su paesi, periodo, ambito e metrica: esplora i dati a modo tuo.")
    st.page_link("pages/Scheda_Paese.py", label="Scheda Paese", icon="🔎")
    st.caption("Una scheda libera su qualunque entità, mondo incluso.")
    st.page_link("pages/Strategie_a_Confronto.py", label="Strategie a confronto", icon="🆚")
    st.caption("Confronta da 2 a 4 paesi testa a testa.")
    st.page_link("pages/Mappa_Europa_Mondo.py", label="Mappa Europa/Mondo", icon="🗺️")
    st.caption("Coropleta con ambito, metrica e anno liberi.")

with col_storia:
    st.markdown("#### 📖 Storia")
    st.caption("Narrazione guidata su un risultato specifico e verificato, pensata per comunicare, non per esplorare.")
    st.page_link("pages/Chi_Sostituisce_Chi.py", label="Chi sostituisce chi", icon="🔀")
    st.caption("Quando il mix cambia, cosa rimpiazza cosa davvero?")
    st.page_link("pages/Declino_Nucleare.py", label="Declino del nucleare", icon="☢️")
    st.caption("Ogni crollo del nucleare ha un evento preciso dietro.")
    st.page_link("pages/Firme_Storiche.py", label="Firme storiche nei dati", icon="🕰️")
    st.caption("I dati mancanti come indicatore geopolitico.")

# I dati dietro l'analisi: si offre il CSV OWID grezzo integrale (la fonte reale del
# notebook) più il codebook che documenta ogni colonna, per provenienza e documentazione
# complete, non solo il file nudo. Byte letti/serviti da funzione cache, non a ogni rerun.
st.subheader("I dati dietro l'analisi")
data_bytes, n_rows, codebook_bytes = _dataset_files()
st.markdown(
    f"L'intera dashboard si basa su un unico dataset pubblico, l'**OWID Energy Dataset** "
    f"(tutto il mondo, tutte le metriche, {n_rows:,} righe). È scaricabile integralmente per "
    f"riprodurre l'analisi dal notebook; il **codebook** documenta ogni colonna."
)
dl1, dl2 = st.columns(2)
dl1.download_button(
    "⬇️ Scarica il dataset (CSV)",
    data=data_bytes,
    file_name="owid-energy-data.csv",
    mime="text/csv",
    width="stretch",
)
dl2.download_button(
    "⬇️ Scarica il codebook (CSV)",
    data=codebook_bytes,
    file_name="owid-energy-codebook.csv",
    mime="text/csv",
    width="stretch",
)
