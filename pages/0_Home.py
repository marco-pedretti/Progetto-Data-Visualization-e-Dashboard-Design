"""
Home — panoramica, risultati chiave e guida alla navigazione.

Nota: `st.set_page_config` è chiamato una sola volta nel router (`streamlit_app.py`),
non qui — questa pagina viene eseguita da `st.navigation(...).run()`.

Aggiornata il 2026-07-03 (richiesta esplicita dell'utente: la Home era troppo debole
come "aggancio" iniziale) con tre elementi in più rispetto al solo KPI row:
un mini-grafico d'insieme, 2-3 risultati chiave con link diretto alla pagina Storia
che li approfondisce, e un percorso di lettura suggerito **solo** tra le pagine
Storia (le pagine Esplora restano libere per design, non hanno un ordine da
suggerire).
"""

import plotly.express as px
import streamlit as st

from common import (
    PALETTE,
    PANEL_YEAR_END,
    PANEL_YEAR_START,
    SOURCE_NOTE,
    get_balanced_panel,
    get_carbon_intensity,
    get_nuclear_history,
    weighted_shares,
)

st.title("⚡ Mix energetico in Europa")
st.markdown(
    """
    Come si è evoluto il modo in cui l'Europa produce elettricità, tra **fossili**,
    **nucleare** e **rinnovabili**, dal 1990 al 2022? Questa dashboard accompagna il
    notebook di analisi (`eda_energia_europa.ipynb`) ed è organizzata in due tipi di
    pagine, elencate nel menu in alto:

    - **Esplora**: filtri liberi su paesi, periodo, ambito e metrica, per fare le
      proprie domande ai dati.
    - **Storia**: narrazione guidata su un risultato specifico, con libertà di
      personalizzazione limitata — qui l'obiettivo è comunicare una conclusione
      verificata, non esplorare.
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

# --- Mini-grafico d'insieme sul panel aggregato: compatto e senza controlli, qui serve ---
# --- solo a dare il contesto generale prima che l'utente navighi, non a sostituire le ---
# --- pagine di dettaglio (il confronto per paese vive in "Strategie a confronto"). ---
agg = bal_all.groupby("year")[
    ["electricity_generation", "fossil_electricity", "nuclear_electricity", "renewables_electricity"]
].sum()
share_series = agg.div(agg["electricity_generation"], axis=0) * 100
crossover = share_series[share_series["renewables_electricity"] > share_series["nuclear_electricity"]].index.min()

long_share = share_series.reset_index().melt(
    id_vars="year",
    value_vars=["fossil_electricity", "nuclear_electricity", "renewables_electricity"],
    var_name="fonte", value_name="quota",
)
long_share["fonte"] = long_share["fonte"].map({
    "fossil_electricity": "Fossile", "nuclear_electricity": "Nucleare", "renewables_electricity": "Rinnovabili",
})
fig = px.line(
    long_share, x="year", y="quota", color="fonte",
    color_discrete_map={"Fossile": PALETTE["fossile"], "Nucleare": PALETTE["nucleare"], "Rinnovabili": PALETTE["rinnovabili"]},
    category_orders={"fonte": ["Fossile", "Nucleare", "Rinnovabili"]},
    labels={"year": "", "quota": "% della generazione", "fonte": ""},
    template="plotly_white",
)
fig.update_traces(line=dict(width=2.5))
fig.update_yaxes(range=[0, 100])
if crossover:
    fig.add_vline(x=crossover, line_dash="dot", line_color="gray")
fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=1.0))
st.plotly_chart(fig, width="stretch")
st.caption(f"{SOURCE_NOTE} — panel bilanciato, quota % della generazione, {PANEL_YEAR_START}–{PANEL_YEAR_END}")

# --- Risultati chiave: numeri ricalcolati qui, non scritti a mano, con link alla ---
# --- pagina Storia che li approfondisce (mai una pagina di sintesi a parte). ---
st.divider()
st.subheader("Tre risultati verificati")

carbon = get_carbon_intensity()
ci_1990 = carbon["panel_bilanciato"].loc[1990]
ci_min_year = int(carbon["panel_bilanciato"].idxmin())
ci_min = carbon["panel_bilanciato"].loc[ci_min_year]

lit = get_nuclear_history(["Lithuania"])
lit_peak = lit.loc[lit["nuclear_share_elec"].idxmax()]
lit_last_row = lit[lit["year"] == PANEL_YEAR_END]["nuclear_share_elec"]
lit_last = lit_last_row.iloc[0] if not lit_last_row.empty else None

h1, h2, h3 = st.columns(3)
with h1:
    st.markdown(f"**Le rinnovabili superano il nucleare dal {crossover}**")
    st.caption(
        f"Nel 1990 il nucleare pesava {share_series['nuclear_electricity'].loc[1990]:.0f}% contro il "
        f"{share_series['renewables_electricity'].loc[1990]:.0f}% delle rinnovabili; nel {last_year} il "
        f"rapporto è invertito ({share_series['renewables_electricity'].loc[last_year]:.0f}% contro "
        f"{share_series['nuclear_electricity'].loc[last_year]:.0f}%)."
    )
    st.page_link("pages/3_Cinque_Strategie_Nazionali.py", label="Confronta due paesi →", icon="🆚")
with h2:
    st.markdown(f"**L'intensità di carbonio si è quasi dimezzata dal 1990 al {ci_min_year}**")
    st.caption(
        f"Da {ci_1990:.0f} a {ci_min:.0f} gCO₂/kWh nel panel bilanciato — ma quota di mix e intensità "
        "non sono la stessa cosa."
    )
    st.page_link("pages/5_Intensita_di_Carbonio.py", label="Approfondisci →", icon="🌍")
with h3:
    st.markdown("**Ogni declino nucleare ha un evento preciso**")
    if lit_last is not None:
        st.caption(
            f"Es. Lituania: da {lit_peak['nuclear_share_elec']:.0f}% ({int(lit_peak['year'])}) a "
            f"{lit_last:.0f}% ({PANEL_YEAR_END}) dopo la chiusura di Ignalina, condizione di adesione UE."
        )
    st.page_link("pages/7_Declino_Nucleare.py", label="Approfondisci →", icon="☢️")

# --- Percorso di lettura: solo tra le pagine Storia. Le pagine Esplora restano ---
# --- libere per design (nessun ordine da suggerire, sono fatte per farsi le ---
# --- proprie domande, non per seguire una narrazione — vedi le pagine Esplora). ---
st.divider()
st.subheader("Un filo conduttore tra le pagine Storia")
st.markdown(
    "Le pagine Storia si leggono in qualunque ordine, ma se cerchi un filo conduttore: il pattern "
    "di sostituzione verificato su tutto il panel → il gruppo eccezione approfondito nel tempo → "
    "l'indicatore di esito che chiude il quadro."
)
r1, r2, r3 = st.columns(3)
r1.page_link("pages/4_Chi_Sostituisce_Chi.py", label="1. Chi sostituisce chi", icon="🔀")
r2.page_link("pages/7_Declino_Nucleare.py", label="2. Declino del nucleare", icon="☢️")
r3.page_link("pages/5_Intensita_di_Carbonio.py", label="3. Intensità di carbonio", icon="🌍")

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
