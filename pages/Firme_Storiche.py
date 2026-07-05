"""
Firme storiche nei dati (Storia)
================================
Corrisponde al Cap. 3.4 del notebook: la censura a sinistra di `electricity_generation`
come indicatore geopolitico. Inizialmente esclusa dalla dashboard (2026-07-03, "EDA non
mix energetico"), re-inclusa su richiesta esplicita dell'utente (2026-07-04) come pagina
di storytelling sui dati stessi.

Racconta la versione VERIFICATA della tesi, non quella del PDF esterno che l'ha ispirata:
il PDF leggeva il 1985 come firma del blocco post-sovietico, ma nei dati 31 dei 40 paesi
europei partono tutti nel 1985 (Francia, Germania e Italia incluse): è il floor con cui
la fonte inizia a pubblicare la colonna, non un segnale storico. La firma vera è lo
scaglionamento successivo (1990/2000/2005), che ricalca la dissoluzione jugoslava.

Nessuna libertà di personalizzazione (come "Declino del nucleare"): la narrazione è
fissa, i numeri sono ricalcolati a schermo dal dataset reale, mai scritti a mano.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import EUROPE_ISO, PALETTE, SOURCE_NOTE, limit_page_width, load_raw_data

# Colori per soglia di inizio: Okabe-Ito coerenti col resto dell'app. Il blocco 1985 è
# volutamente un grigio spento (è lo sfondo della storia, non il protagonista); niente
# nero puro, sparirebbe in dark mode.
WAVE_COLORS = {1985: "#B5B5B5", 1990: "#E69F00", 2000: "#D55E00", 2005: "#0072B2"}

# Entità storiche presenti nel dataset ma senza alcun valore di electricity_generation:
# la loro esistenza "vuota" è parte della storia (righe segnaposto, non serie interrotte).
GHOST_ENTITIES = ["USSR", "Yugoslavia", "Serbia and Montenegro", "East Germany", "West Germany"]


@st.cache_data(show_spinner="Calcolo le soglie di inizio serie...")
def get_series_bounds() -> pd.DataFrame:
    """Primo e ultimo anno con electricity_generation valida per i 40 paesi europei.

    Stesso calcolo del Cap. 3.4 (first_valid_index per paese); i gap interni sono zero
    per costruzione delle fonti (retropolazione a monte), verificato nel notebook.
    """
    df = load_raw_data()
    eu = df[df["iso_code"].isin(EUROPE_ISO)]
    recs = []
    for country, grp in eu.groupby("country"):
        g = grp.sort_values("year").set_index("year")["electricity_generation"]
        fvi = g.first_valid_index()
        if fvi is None:
            continue
        recs.append({"country": country, "first": int(fvi), "last": int(g.last_valid_index())})
    return pd.DataFrame(recs)


def timeline_figure(bounds: pd.DataFrame) -> go.Figure:
    """Gantt della disponibilità dati, compresso sulle righe che raccontano qualcosa.

    Le eccezioni colorate in alto (2005 → 2000 → 1990); del blocco 1985 restano come
    righe singole solo Ucraina e Islanda (le uniche con la serie tronca, per ragioni
    opposte); gli altri paesi, tutti identici 1985–ultimo anno, sono raggruppati in
    un'unica riga: 31 barre grigie uguali erano rumore, una sola dice lo stesso.
    """
    late = bounds[bounds["first"] > 1985]
    notable_ends = ["Ukraine", "Iceland"]
    normal = bounds[(bounds["first"] == 1985) & (~bounds["country"].isin(notable_ends))]
    n_norm = len(normal)
    agg_label = f"Altri {n_norm} paesi"
    agg_last = int(normal["last"].max())

    # Ordine top-down: soglie tardive, poi le due serie tronche, poi la riga aggregata;
    # Plotly elenca categoryarray dal basso verso l'alto, quindi si passa la lista rovesciata.
    top_down: list[str] = []
    for wave in [2005, 2000, 1990]:
        top_down += sorted(late.loc[late["first"] == wave, "country"])
    top_down += notable_ends + [agg_label]

    fig = go.Figure()
    for wave in [2005, 2000, 1990]:
        grp = late[late["first"] == wave].sort_values("country")
        fig.add_trace(go.Bar(
            y=grp["country"], x=grp["last"] - grp["first"], base=grp["first"],
            orientation="h", marker_color=WAVE_COLORS[wave], name=f"dal {wave} ({len(grp)})",
            customdata=grp["last"],
            hovertemplate="%{y}: %{base}–%{customdata}<extra></extra>",
        ))

    # Blocco 1985: Ucraina e Islanda singole + riga aggregata (hover con l'elenco completo).
    b = bounds.set_index("country")
    ukr_last, ice_last = int(b.loc["Ukraine", "last"]), int(b.loc["Iceland", "last"])
    names = sorted(normal["country"])
    names_wrapped = "<br>".join(", ".join(names[i:i + 6]) for i in range(0, len(names), 6))
    grey_last = [ukr_last, ice_last, agg_last]
    fig.add_trace(go.Bar(
        y=notable_ends + [agg_label], x=[v - 1985 for v in grey_last], base=[1985] * 3,
        orientation="h", marker_color=WAVE_COLORS[1985], name=f"dal 1985 ({n_norm + 2})",
        hovertext=[f"Ukraine: 1985–{ukr_last}", f"Iceland: 1985–{ice_last}",
                   f"{n_norm} paesi, 1985–{agg_last}:<br>{names_wrapped}"],
        hoverinfo="text",
    ))

    # Il 1985 non è un evento: è il momento in cui la fonte inizia a pubblicare.
    fig.add_vline(x=1985, line_dash="dot", line_color="#888888", line_width=1)
    fig.add_annotation(
        x=1985, y=1.0, yref="paper", yanchor="bottom",
        text="1985: inizio pubblicazione della fonte",
        showarrow=False, xanchor="left", font=dict(size=10, color="#888888"),
    )

    # Gli eventi storici veri, sotto l'asse su due livelli sfalsati per non sovrapporre
    # le etichette tra loro (1990/1991/1993 distano un anno) né con i tick dell'asse
    # (per questo partono da y=-0.16, sotto la fascia dei tick); la riunificazione
    # tedesca è ancorata a destra così il testo occupa la zona vuota pre-1990.
    # xshift: scostamento orizzontale in PIXEL della sola etichetta (positivo = destra),
    # la linea resta su x: è la manopola per aggiustare a occhio le posizioni.
    events = [
        (1990, -0.16, "right", 35, "1990 · riunificazione tedesca "),
        (1993, -0.16, "left", 0, " 1993 · divorzio di velluto cecoslovacco"),
        (2006, -0.16, "left", 0, " 2006 · indipendenza del Montenegro"),
        (1991, -0.22, "left", -15, " 1991 · dissoluzione dell'URSS · indipendenze jugoslave"),
    ]
    for x, y, anchor, xshift, txt in events:
        fig.add_vline(x=x, line_dash="dash", line_color="#888888", line_width=1)
        fig.add_annotation(x=x, y=y, yref="paper", text=txt, showarrow=False, xshift=xshift,
                           xanchor=anchor, font=dict(size=10, color="#888888"))

    # La guerra di Bosnia come banda ombreggiata: spiega perché la serie bosniaca
    # arriva solo nel 2000, cinque anni dopo Dayton. L'etichetta sta subito a destra
    # della banda, nella zona vuota prima dell'inizio delle barre del 2000 (le righe
    # alte del grafico non hanno barre prima del 2000), non tra le linee tratteggiate.
    fig.add_vrect(x0=1992, x1=1995, fillcolor=PALETTE["calo"], opacity=0.06, line_width=0)
    fig.add_annotation(
        x=1993.5, y=0.84, yref="paper", yanchor="middle", xanchor="left",
        text="guerra di<br>Bosnia 1992–95",
        showarrow=False, font=dict(size=9, color=PALETTE["calo"]), align="left",
    )

    # L'unica serie interrotta prima del presente per un evento (non per ritardo di
    # pubblicazione): l'Ucraina si ferma al 2022.
    fig.add_trace(go.Scatter(
        x=[ukr_last], y=["Ukraine"], mode="markers+text",
        marker=dict(color=PALETTE["calo"], size=9, symbol="x"),
        text=[f"  invasione russa: dati fermi al {ukr_last}"], textposition="middle right",
        textfont=dict(size=10, color=PALETTE["calo"]), showlegend=False, hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(text="Quasi tutta Europa parte nel 1985: le eccezioni ricalcano la dissoluzione jugoslava", y=0.98, yanchor="top"),
        template="plotly_white", height=520, barmode="overlay", bargap=0.35,
        xaxis=dict(range=[1979, 2034], title=""),
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(top_down)), tickfont=dict(size=11)),
        legend=dict(orientation="h", yanchor="bottom", y=1.07),
        margin=dict(l=10, r=10, t=130, b=125),
    )
    return fig


def main() -> None:
    limit_page_width()
    st.title("🕰️ Firme storiche nei dati")
    st.markdown(
        "Nelle altre pagine i dati mancanti sono un problema da gestire; qui sono il **soggetto**. "
        "La colonna `electricity_generation` non ha buchi interni in Europa: ogni serie, una volta "
        "iniziata, corre ininterrotta fino all'ultimo anno disponibile. L'informazione storica sta "
        "quindi in **quando una serie comincia** e in quando finisce, non nei buchi, a patto di "
        "distinguere il segnale storico dall'artefatto della fonte."
    )

    bounds = get_series_bounds()
    n_total = len(bounds)
    n_1985 = int((bounds["first"] == 1985).sum())
    late = bounds[bounds["first"] > 1985]

    st.plotly_chart(timeline_figure(bounds), width="stretch")
    st.caption(
        f"{SOURCE_NOTE} · electricity_generation, copertura Europa ({n_total} paesi). Zero gap "
        "interni: le barre sono continue perché le serie lo sono davvero. Le serie identiche "
        "1985–2025 sono raggruppate in un'unica riga (elenco completo al passaggio del mouse); "
        "Ucraina e Islanda restano singole perché la loro serie si interrompe prima."
    )

    st.subheader("⚠️ La trappola del 1985")
    st.markdown(
        f"La tentazione è leggere il 1985 come la firma del blocco post-sovietico: Russia, Ucraina "
        f"e i tre Baltici partono tutti lì. Ma è una trappola: **{n_1985} dei {n_total} paesi "
        f"europei** partono nel 1985, comprese Francia, Germania, Italia e Regno Unito. Il 1985 è "
        f"il *floor* con cui la fonte (Energy Institute) inizia a pubblicare questa colonna, non un "
        f"evento storico. Per Russia, Baltici, Cechia e Slovacchia è anzi una **retropolazione**: i "
        f"confini attuali proiettati all'indietro, *prima* che quegli Stati esistessero. Persino la "
        f"riunificazione tedesca è invisibile: la Germania è una serie unica dal 1985, mentre le "
        f"voci *East Germany* e *West Germany* esistono nel dataset senza un solo valore di "
        f"generazione."
    )

    st.subheader("🧩 La firma vera: lo scaglionamento 1990 → 2000 → 2005")
    g1990 = ", ".join(sorted(late.loc[late["first"] == 1990, "country"]))
    g2000 = ", ".join(sorted(late.loc[late["first"] == 2000, "country"]))
    g2005 = ", ".join(sorted(late.loc[late["first"] == 2005, "country"]))
    st.markdown(
        f"Il segnale storico sta nelle **{len(late)} eccezioni** e nel loro ordine: **1990** "
        f"({g1990}), **2000** ({g2000}), **2005** ({g2005}). La sequenza ricalca la disgregazione "
        f"jugoslava: Slovenia, Croazia e Macedonia del Nord (indipendenze 1991) partono nel 1990; "
        f"la Bosnia, devastata dalla guerra 1992-95, dal 2000; il Montenegro (indipendenza 2006) "
        f"dal 2005, sempre **dopo** l'evento politico: costruire un sistema statistico richiede "
        f"anni. Due eccezioni non c'entrano con la Jugoslavia: **Malta** è nel gruppo 1990 per pura "
        f"coincidenza, e la **Moldova** (ex URSS) condivide la soglia 2000 con Bosnia e Albania solo "
        f"per anno, non per causa comune. Anche il **Kosovo** parte dal 2000, ma il suo codice "
        f"non-ISO lo esclude dal conteggio dei {n_total}. Un'ultima nota: se i buchi *interni* non "
        f"esistono è perché le fonti li hanno già chiusi a monte con stime e retropolazioni: anche "
        f"l'assenza è una scelta editoriale, non solo storia."
    )

    st.subheader("🪦 Anche la fine di una serie è una firma")
    truncated = bounds[bounds["last"] < bounds["last"].max()].sort_values("last")
    ukr_last = int(bounds.loc[bounds["country"] == "Ukraine", "last"].iloc[0])
    others = truncated[truncated["country"] != "Ukraine"]
    others_txt = "; ".join(f"{r.country} al {r.last}" for r in others.itertuples())
    df_raw = load_raw_data()
    ghost_counts = {e: int((df_raw["country"] == e).sum()) for e in GHOST_ENTITIES}
    st.markdown(
        f"La censura funziona anche a destra. L'**Ucraina** è ferma al **{ukr_last}**: non un "
        f"ritardo di pubblicazione ma la guerra. {others_txt} sono invece ordinari ritardi di "
        f"pubblicazione: in tabella le due assenze sono identiche, ma le cause opposte, e il dato "
        f"mancante va sempre interrogato, mai solo contato. Ultima firma, la più silenziosa: "
        f"*USSR* ({ghost_counts['USSR']} righe), *Yugoslavia* ({ghost_counts['Yugoslavia']}) e "
        f"*Serbia and Montenegro* ({ghost_counts['Serbia and Montenegro']}) **esistono** ancora nel "
        f"dataset come entità, ma senza un solo valore di generazione: righe segnaposto di Stati "
        f"che non ci sono più, lapidi statistiche."
    )


if __name__ == "__main__":
    main()
