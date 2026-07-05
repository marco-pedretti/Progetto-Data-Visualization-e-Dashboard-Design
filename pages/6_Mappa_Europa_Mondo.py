"""
Pagina 6 — Mappa Europa/Mondo (Esplora)
==========================================
Coropleta interattiva del mix elettrico: ambito (Europa/Mondo), metrica e anno
scelti liberamente, con KPI ricalcolati sullo scope selezionato. Solo variabili
del settore elettrico (quote fossile/nucleare/rinnovabili, intensità di carbonio,
generazione totale) — non emissioni economy-wide, per restare coerenti col tema
del progetto (scelta esplicita dell'utente).

I paesi senza dato per la metrica/anno scelti sono colorati in modo esplicito e fisso
(lavanda, `MAP_NO_DATA_COLOR`), indipendente dalla metrica/scala scelta — non è un errore
da correggere, è la stessa distinzione strutturale del Cap. 3 del notebook (la copertura
fuori Europa è molto più eterogenea — always-null, right-censoring), qui resa esplicita
invece di affidata al grigio di default di Plotly (che si confonderebbe con l'estremo
chiaro di scale come "Greys").

Periodo esteso al massimo disponibile nel dataset, 1985-2025 (Cap. 3.2/3.3/3.4): prima
del 2000 pochissimi paesi fuori Europa hanno dati e il 2025 è pesantemente right-censored,
ma ora che l'assenza di dato è marcata esplicitamente l'intero range è mostrabile onestamente.
"""

import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (
    EUROPE_ISO,
    MAP_METRICS,
    MAP_NO_DATA_COLOR,
    SOURCE_NOTE,
    WORLD_YEAR_END,
    WORLD_YEAR_START,
    get_scope_kpis,
    get_world_data,
    limit_page_width,
)

world = get_world_data()


def main() -> None:
    st.title("🗺️ Mappa Europa/Mondo")
    st.markdown(
        "Scegli ambito, metrica e anno (slider in fondo). I paesi in **lavanda** non hanno un dato "
        "disponibile per quella combinazione — non è un errore, è la stessa distinzione strutturale "
        "vista nel Cap. 3 del notebook (la copertura fuori Europa è molto più eterogenea)."
    )

    limit_page_width()
    col_scope, col_metric = st.columns(2)
    scope = col_scope.radio("Ambito", ["Europa", "Mondo"], horizontal=True)
    metric_label = col_metric.selectbox("Metrica", list(MAP_METRICS.keys()))
    st.caption(
        "Copertura più scarsa prima del 2000 e nel 2025 (dati non ancora pubblicati per molti "
        "paesi, Cap. 3.2-3.3 del notebook): quegli anni mostreranno più paesi in lavanda."
    )

    metric = MAP_METRICS[metric_label]
    scope_df = world[world["iso_code"].isin(EUROPE_ISO)] if scope == "Europa" else world
    # Lo slider seleziona un anno singolo, non un intervallo: Streamlit colora di default il
    # tratto a sinistra del cursore come se fosse un range selezionato, il che genera l'illusione
    # segnalata di una selezione multipla. Si uniforma l'intera barra allo stesso grigio neutro
    # (lo stesso già usato da Streamlit per la parte "non selezionata"), lasciando il pallino con
    # l'etichetta dell'anno come unico indicatore del valore puntuale. Stile applicato solo in
    # questa pagina: le altre pagine usano slider a due estremi dove il tratto colorato è corretto.
    st.markdown(
        """
        <style>
        div[data-baseweb="slider"] > div > div > div:nth-child(2) {
            background: rgba(151, 166, 195, 0.25) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.setdefault("map_anim_year", 2025)
    st.session_state.setdefault("map_playing", False)
    st.session_state.setdefault("map_advance_pending", False)

    # Il valore di un widget con "key" non è modificabile dopo che il widget è stato istanziato
    # in quello stesso run (StreamlitAPIException). Per avanzare l'anno lo si fa qui, prima di
    # creare lo slider, sulla base del flag impostato dal run precedente.
    if st.session_state.map_playing and st.session_state.map_advance_pending:
        st.session_state.map_advance_pending = False
        current = st.session_state.map_anim_year
        st.session_state.map_anim_year = current + 1 if current < WORLD_YEAR_END else WORLD_YEAR_START

    # Lo slider va istanziato PRIMA dei pulsanti nell'ordine di esecuzione (il layout a colonne
    # resta invariato: la posizione visiva dipende dall'ordine delle colonne, non da quello del
    # codice). Se un bottone chiama st.rerun() prima che lo slider sia stato creato in quel run,
    # Streamlit considera il suo stato "non visto" in quel passaggio e lo elimina, facendolo
    # ripartire dal default al giro successivo (bug osservato: Stop riportava l'anno a 2022).
    col_play, col_stop, col_slider = st.columns([1, 1, 6])
    with col_slider:
        year = st.slider("Anno", min_value=WORLD_YEAR_START, max_value=WORLD_YEAR_END, key="map_anim_year")
    with col_play:
        if st.button("▶️ Play", disabled=st.session_state.map_playing, width="stretch"):
            st.session_state.map_playing = True
            st.rerun()
    with col_stop:
        if st.button("⏹️ Stop", disabled=not st.session_state.map_playing, width="stretch"):
            st.session_state.map_playing = False
            st.rerun()
    df_year = scope_df[scope_df["year"] == year]

    kpis = get_scope_kpis(df_year)
    n_with_metric = int(df_year[metric["col"]].notna().sum())

    # Scala colore fissata sul range della metrica nell'intero ambito (tutti gli anni), non sul
    # solo anno selezionato: altrimenti muovendo lo slider la legenda si ricalibra ogni volta e i
    # colori non sono più confrontabili anno per anno.
    color_min = scope_df[metric["col"]].min()
    color_max = scope_df[metric["col"]].max()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"Paesi in {scope}", f"{kpis['n_countries']}")
    c2.metric("Con dato per la metrica", f"{n_with_metric}")
    c3.metric("Generazione totale", f"{kpis['total_generation']:,.0f} TWh")
    c4.metric(
        "Intensità di carbonio",
        f"{kpis['carbon_intensity']:.0f} gCO₂/kWh" if pd.notna(kpis["carbon_intensity"]) else "n.d.",
    )
    c5.metric("Quota rinnovabili", f"{kpis['rinnovabili']:.1f}%")

    # Due tracce sovrapposte invece di una sola: la prima copre l'intero ambito con il colore
    # fisso "nessun dato" (universo = tutti i paesi mai comparsi in questo ambito, non solo
    # quelli del solo anno selezionato); la seconda disegna sopra, con la scala della metrica,
    # solo i paesi che hanno davvero un valore quest'anno — dove manca, resta visibile lo strato
    # sottostante. Un colore fisso indipendente dalla metrica (MAP_NO_DATA_COLOR) rende "nessun
    # dato" sempre riconoscibile allo stesso modo, invece del grigio di default di Plotly che si
    # confonde con l'estremo chiaro di scale come "Greys".
    all_locations = scope_df["iso_code"].unique()
    names_by_iso = scope_df.drop_duplicates("iso_code").set_index("iso_code")["country"]
    value_df = df_year[df_year[metric["col"]].notna()]

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=all_locations,
        z=[0] * len(all_locations),
        customdata=names_by_iso.reindex(all_locations).values,
        colorscale=[[0, MAP_NO_DATA_COLOR], [1, MAP_NO_DATA_COLOR]],
        showscale=False,
        hovertemplate="%{customdata}<br>Nessun dato disponibile<extra></extra>",
    ))
    if not value_df.empty:
        fig.add_trace(go.Choropleth(
            locations=value_df["iso_code"], z=value_df[metric["col"]], customdata=value_df["country"],
            colorscale=metric["colorscale"], zmin=color_min, zmax=color_max,
            colorbar_title=metric_label,
            hovertemplate=f"%{{customdata}}<br>{metric_label}: " + "%{z:.1f}<extra></extra>",
        ))
    fig.update_geos(scope="europe" if scope == "Europa" else "world")
    fig.update_layout(
        title=f"{metric_label} — {year}", template="plotly_white",
        height=600, margin=dict(l=0, r=0, t=40, b=0),
    )
    # I trace Choropleth non hanno una voce di legenda "a swatch" come scatter/bar (il colore è
    # comunicato dalla colorbar, non dalla legenda): un trace fittizio per ottenerla dentro la
    # figura si scontrava con il titolo interno (margine superiore troppo stretto per ospitare
    # entrambi, testo sovrapposto). Stesso pattern swatch-HTML già usato per la legenda colori
    # della Home, fuori dal grafico: robusto in dark mode, nessun conflitto di layout Plotly.
    st.markdown(
        f'<span style="display:inline-block;width:12px;height:12px;background:{MAP_NO_DATA_COLOR};'
        f'border-radius:2px;margin-right:6px;"></span>Nessun dato disponibile',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(SOURCE_NOTE)

    # Animazione: ogni rerun mostra un anno, aspetta, poi segnala al run successivo di avanzare
    # (torna a inizio dopo l'ultimo). Un click su "Stop" interrompe lo script a metà sleep e
    # riparte con playing=False, quindi il pulsante resta reattivo anche durante la riproduzione.
    if st.session_state.map_playing:
        time.sleep(0.7)
        st.session_state.map_advance_pending = True
        st.rerun()


if __name__ == "__main__":
    main()
