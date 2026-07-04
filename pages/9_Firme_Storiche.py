"""
Pagina 9 — Firme storiche nei dati (Storia)
==============================================
Corrisponde al Cap. 3.4 del notebook: la censura a sinistra di `electricity_generation`
come indicatore geopolitico. Inizialmente esclusa dalla dashboard (2026-07-03, "EDA non
mix energetico"), re-inclusa su richiesta esplicita dell'utente (2026-07-04) come pagina
di storytelling sui dati stessi.

Racconta la versione VERIFICATA della tesi, non quella del PDF esterno che l'ha ispirata:
il PDF leggeva il 1985 come firma del blocco post-sovietico, ma nei dati 31 dei 40 paesi
europei partono tutti nel 1985 (Francia, Germania e Italia incluse) — è il floor con cui
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
    """Gantt della disponibilità dati: una barra per paese, dal primo all'ultimo anno.

    L'ordinamento è il messaggio: le eccezioni colorate in alto (2005 → 2000 → 1990),
    la massa uniforme del 1985 in grigio sotto — si vede a colpo d'occhio che il 1985
    è la regola del continente, non la firma di un blocco.
    """
    waves = sorted(bounds["first"].unique())  # [1985, 1990, 2000, 2005]

    # Ordine top-down: prima le soglie tardive, alfabetico dentro ogni gruppo; Plotly
    # elenca categoryarray dal basso verso l'alto, quindi si passa la lista rovesciata.
    top_down: list[str] = []
    for wave in sorted(waves, reverse=True):
        top_down += sorted(bounds.loc[bounds["first"] == wave, "country"])

    fig = go.Figure()
    for wave in sorted(waves, reverse=True):
        grp = bounds[bounds["first"] == wave].sort_values("country")
        n = len(grp)
        fig.add_trace(go.Bar(
            y=grp["country"], x=grp["last"] - grp["first"], base=grp["first"],
            orientation="h", marker_color=WAVE_COLORS[wave], name=f"dal {wave} ({n})",
            customdata=grp["last"],
            hovertemplate="%{y}: %{base}–%{customdata}<extra></extra>",
        ))

    # Il 1985 non è un evento: è il momento in cui la fonte inizia a pubblicare.
    fig.add_vline(x=1985, line_dash="dot", line_color="#888888", line_width=1)
    fig.add_annotation(
        x=1985, y=1.0, yref="paper", yanchor="bottom",
        text="1985 — inizio pubblicazione della fonte, non un evento storico",
        showarrow=False, xanchor="left", font=dict(size=10, color="#888888"),
    )
    # L'evento storico vero è il 1991: le serie tardive partono tutte DOPO, mai prima.
    fig.add_vline(x=1991, line_dash="dash", line_color="#888888", line_width=1)
    fig.add_annotation(
        x=1991, y=-0.05, yref="paper", text="1991 — crollo URSS, indipendenze jugoslave",
        showarrow=False, xanchor="left", font=dict(size=10, color="#888888"),
    )
    # L'unica serie interrotta prima del presente per un evento (non per ritardo di
    # pubblicazione): l'Ucraina si ferma al 2022.
    ukr = bounds.loc[bounds["country"] == "Ukraine"].iloc[0]
    fig.add_trace(go.Scatter(
        x=[ukr["last"]], y=["Ukraine"], mode="markers+text",
        marker=dict(color=PALETTE["calo"], size=9, symbol="x"),
        text=[f"  guerra: dati fermi al {ukr['last']}"], textposition="middle right",
        textfont=dict(size=10, color=PALETTE["calo"]), showlegend=False, hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(text="Quasi tutta Europa parte nel 1985: le eccezioni ricalcano la dissoluzione jugoslava", y=0.98, yanchor="top"),
        template="plotly_white", height=820, barmode="overlay", bargap=0.35,
        xaxis=dict(range=[1979, 2034], title=""),
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(top_down)), tickfont=dict(size=10)),
        legend=dict(orientation="h", yanchor="bottom", y=1.055),
        margin=dict(l=10, r=10, t=150, b=40),
    )
    return fig


def main() -> None:
    limit_page_width()
    st.title("🕰️ Firme storiche nei dati")
    st.markdown(
        "Nelle altre pagine i dati mancanti sono un problema da gestire; qui sono il **soggetto**. "
        "La colonna `electricity_generation` non ha nessun buco interno in Europa: una volta "
        "iniziata, ogni serie corre ininterrotta fino all'ultimo anno disponibile. L'informazione "
        "storica non sta quindi nei buchi, ma in **quando una serie comincia** — e in quando "
        "finisce. A patto di saper distinguere il segnale storico dall'artefatto della fonte."
    )

    bounds = get_series_bounds()
    n_total = len(bounds)
    n_1985 = int((bounds["first"] == 1985).sum())
    late = bounds[bounds["first"] > 1985]

    st.plotly_chart(timeline_figure(bounds), width="stretch")
    st.caption(f"{SOURCE_NOTE} — electricity_generation, copertura Europa ({n_total} paesi), zero gap interni")

    st.subheader("⚠️ La trappola del 1985")
    st.markdown(
        f"La tentazione narrativa è leggere il 1985 come la firma del blocco post-sovietico: Russia, "
        f"Ucraina, i tre Baltici partono tutti lì. Ma è una trappola: **{n_1985} dei {n_total} paesi "
        f"europei** partono nel 1985 — comprese Francia, Germania, Italia, Regno Unito e tutta "
        f"l'Europa occidentale. Il 1985 è il *floor* con cui la fonte (Energy Institute) inizia a "
        f"pubblicare questa colonna per l'intero continente, non un evento storico. Il dato \"1985\" "
        f"di Russia, Baltici, Cechia e Slovacchia è anzi una **retropolazione**: i confini attuali "
        f"proiettati all'indietro, *prima* che quegli Stati esistessero (l'URSS si dissolve nel "
        f"dicembre 1991, il divorzio di velluto è del gennaio 1993). Persino la riunificazione "
        f"tedesca (ottobre 1990) è invisibile: la Germania è una serie unica e continua dal 1985 — "
        f"le voci *East Germany* e *West Germany* esistono nel dataset, ma senza un solo valore di "
        f"generazione."
    )

    st.subheader("🧩 La firma vera: lo scaglionamento 1990 → 2000 → 2005")
    g1990 = ", ".join(sorted(late.loc[late["first"] == 1990, "country"]))
    g2000 = ", ".join(sorted(late.loc[late["first"] == 2000, "country"]))
    g2005 = ", ".join(sorted(late.loc[late["first"] == 2005, "country"]))
    st.markdown(
        f"Il segnale storico sta nelle **{len(late)} eccezioni**, e nel loro ordine: **1990** "
        f"({g1990}), **2000** ({g2000}), **2005** ({g2005}). La sequenza ricalca da vicino la "
        f"disgregazione jugoslava — Slovenia, Croazia e Macedonia del Nord (indipendenze 1991) "
        f"partono nel 1990; la Bosnia, devastata dalla guerra 1992-95, solo dal 2000; il Montenegro "
        f"(indipendenza 2006) dal 2005 — sempre **dopo** l'evento politico, mai prima: costruire un "
        f"sistema statistico nazionale richiede anni. Due avvertenze da onestà intellettuale: "
        f"**Malta** è nel gruppo 1990 per pura coincidenza di copertura (nessun legame jugoslavo), "
        f"e la **Moldova** (ex URSS, non ex Jugoslavia) condivide la soglia 2000 con Bosnia e "
        f"Albania — il raggruppamento è per anno, non per causa comune. Anche il **Kosovo** parte "
        f"dal 2000, ma vive nel dataset con un codice non-ISO (sovranità contesa) e resta fuori "
        f"dal conteggio dei {n_total}. Infine, il rovescio metodologico: se i buchi *interni* non "
        f"esistono è perché le fonti li hanno chiusi a monte con stime e retropolazioni — la forma "
        f"dell'assenza è modellata dalle scelte editoriali, non solo dalla storia."
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
        f"ritardo di pubblicazione ma la guerra, che investe anche il sistema statistico di un "
        f"paese. {others_txt} sono invece ordinari ritardi di pubblicazione — in tabella le due "
        f"assenze sono identiche, le cause opposte: il dato mancante va sempre interrogato, mai "
        f"solo contato. Ultima firma, la più silenziosa: *USSR* ({ghost_counts['USSR']} righe), "
        f"*Yugoslavia* ({ghost_counts['Yugoslavia']}) e *Serbia and Montenegro* "
        f"({ghost_counts['Serbia and Montenegro']}) **esistono** ancora nel dataset come entità, "
        f"ma senza un solo valore di generazione elettrica: righe segnaposto di Stati che non ci "
        f"sono più — lapidi statistiche."
    )


if __name__ == "__main__":
    main()
