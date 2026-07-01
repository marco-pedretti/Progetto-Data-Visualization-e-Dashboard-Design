"""
Home — panoramica, KPI e guida alla navigazione.

Nota: `st.set_page_config` è chiamato una sola volta nel router (`streamlit_app.py`),
non qui — questa pagina viene eseguita da `st.navigation(...).run()`.
"""

import streamlit as st

from common import PALETTE, SOURCE_NOTE, get_balanced_panel, weighted_shares

st.title("⚡ Mix energetico in Europa")
st.markdown(
    """
    Come si è evoluto il modo in cui l'Europa produce elettricità, tra **fossili**,
    **nucleare** e **rinnovabili**, dal 1990 al 2022? Questa dashboard accompagna il
    notebook di analisi (`eda_energia_europa.ipynb`) ed è organizzata in due tipi di
    pagine, elencate nel menu in alto:

    - **Esplora**: filtri liberi su paesi, periodo, ambito e metrica, per fare le
      proprie domande ai dati.
    - **Storia**: narrazione guidata sui risultati principali dell'analisi, con
      libertà di personalizzazione limitata — qui l'obiettivo è comunicare una
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
