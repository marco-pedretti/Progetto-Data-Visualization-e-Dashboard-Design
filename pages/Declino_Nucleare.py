"""
Declino del nucleare (Storia)
=============================
Corrisponde al Cap. 4.7 del notebook: i cinque paesi già isolati in "Chi sostituisce
chi" (Cap. 4.5) come eccezione (dove il calo del nucleare coincide con la crescita
rinnovabile, non con il fossile) mostrano ciascuno un picco storico seguito da un
evento politico preciso, non un trend generico. Serie estesa dal 1985 (non il solo
panel bilanciato 1990-2022): per Belgio e Lituania il picco storico cade a ridosso o
prima di quella soglia.

Il messaggio della pagina è il *divario* tra picco ed evento (9-17 anni): il picco è
tecnico/anagrafico, l'evento è politico, e il crollo arriva solo dopo l'evento. La
banda ombreggiata in ogni riquadro è proprio quella distanza; la tabella la rende
scansionabile a colpo d'occhio.

Nessuna libertà di personalizzazione: narrazione e cinque paesi sono fissi. A
differenza di "Strategie a confronto", qui gli eventi politici sono cablati per
paese: sostituire uno slot con un altro paese romperebbe la narrazione, non la
arricchirebbe.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from common import NUCLEAR_EVENTS, PALETTE, SOURCE_NOTE, get_nuclear_history, limit_page_width

NUCLEAR_COUNTRIES = list(NUCLEAR_EVENTS.keys())
POSITIONS = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]
KEY_CELL = (2, 3)  # 6ª cella del grid 2×3: legenda "come leggere", non spazio morto

# Nomi in italiano per titoli dei riquadri e tabella (i dati OWID usano l'inglese).
IT_NAME = {
    "Lithuania": "Lituania", "Germany": "Germania", "Sweden": "Svezia",
    "Belgium": "Belgio", "France": "Francia",
}
# Grigio medio semitrasparente: legge come "tempo trascorso" (non come una fonte) e resta
# visibile sia su sfondo scuro sia chiaro: a bassa opacità sparirebbe nel nero della dark mode.
LAG_BAND = "rgba(150, 152, 165, 0.34)"


def _reading_key(fig: go.Figure) -> None:
    """Disegna una piccola legenda nella 6ª cella (coordinate locali 0-1), al posto del vuoto."""
    row, col = KEY_CELL
    fig.update_xaxes(range=[0, 1], visible=False, row=row, col=col)
    fig.update_yaxes(range=[0, 1], visible=False, row=row, col=col)

    def label(y: float, text: str) -> None:
        fig.add_annotation(x=0.24, y=y, text=text, showarrow=False, xanchor="left",
                           font=dict(size=10, color="#888888"), row=row, col=col)

    fig.add_annotation(x=0.0, y=0.95, text="<b>Come leggere</b>", showarrow=False, xanchor="left",
                       font=dict(size=11, color="#aaaaaa"), row=row, col=col)
    # Campione linea nucleare
    fig.add_trace(go.Scatter(x=[0.03, 0.19], y=[0.72, 0.72], mode="lines",
                             line=dict(color=PALETTE["nucleare"], width=2.5),
                             showlegend=False, hoverinfo="skip"), row=row, col=col)
    label(0.72, "quota nucleare (%)")
    # Campione marker picco
    fig.add_trace(go.Scatter(x=[0.11], y=[0.50], mode="markers",
                             marker=dict(color="#888888", size=8),
                             showlegend=False, hoverinfo="skip"), row=row, col=col)
    label(0.50, "picco storico")
    # Campione linea evento
    fig.add_trace(go.Scatter(x=[0.11, 0.11], y=[0.26, 0.40], mode="lines",
                             line=dict(color=PALETTE["calo"], dash="dot", width=1.5),
                             showlegend=False, hoverinfo="skip"), row=row, col=col)
    label(0.33, "evento politico")
    # Campione banda del divario (traccia riempita, come nei riquadri)
    fig.add_trace(go.Scatter(x=[0.03, 0.19, 0.19, 0.03, 0.03], y=[0.06, 0.06, 0.18, 0.18, 0.06],
                             fill="toself", fillcolor=LAG_BAND, mode="lines", line=dict(width=0),
                             showlegend=False, hoverinfo="skip"), row=row, col=col)
    label(0.12, "anni dal picco all'evento")


def main() -> None:
    limit_page_width()
    st.title("☢️ Declino del nucleare: picco, evento, crollo")
    st.markdown(
        "La pagina **Chi sostituisce chi** isola un piccolo gruppo di paesi dove il calo del "
        "nucleare *coincide* con la crescita rinnovabile: Germania, Lituania, Svezia, Francia e "
        "Belgio. Per ciascuno la domanda naturale è **quando** è iniziato il declino e **perché**, "
        "non solo quanto è cambiata la quota. La risposta ricorrente è che il **picco** (tecnico) "
        "e l'**evento politico** che avvia il crollo non coincidono mai: tra i due passano dai 9 ai "
        "17 anni (la banda grigia in ogni riquadro)."
    )

    history = get_nuclear_history(NUCLEAR_COUNTRIES)

    subplot_titles = [IT_NAME[c] for c in NUCLEAR_COUNTRIES] + [""]
    fig = make_subplots(rows=2, cols=3, subplot_titles=subplot_titles,
                        horizontal_spacing=0.07, vertical_spacing=0.13)

    summary = []
    for (row, col), country in zip(POSITIONS, NUCLEAR_COUNTRIES):
        s = history[history["country"] == country].sort_values("year")
        peak_row = s.loc[s["nuclear_share_elec"].idxmax()]
        peak_year, peak_val = int(peak_row["year"]), float(peak_row["nuclear_share_elec"])
        ev_year, ev_label = NUCLEAR_EVENTS[country]
        v22 = s.loc[s["year"] == 2022, "nuclear_share_elec"]
        val_2022 = float(v22.iloc[0]) if not v22.empty else float(s["nuclear_share_elec"].iloc[-1])

        # Banda del divario picco→evento. Disegnata come traccia riempita (non add_vrect):
        # uno shape con layer="below" nei subplot finisce sotto lo sfondo del riquadro e resta
        # invisibile; una traccia rispetta l'ordine di disegno, così la banda sta sotto la linea.
        fig.add_trace(
            go.Scatter(
                x=[peak_year, ev_year, ev_year, peak_year, peak_year],
                y=[0, 0, 100, 100, 0], fill="toself", fillcolor=LAG_BAND,
                mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False,
            ),
            row=row, col=col,
        )
        fig.add_trace(
            go.Scatter(
                x=s["year"], y=s["nuclear_share_elec"], mode="lines",
                line=dict(color=PALETTE["nucleare"], width=2.5), showlegend=False,
                hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
            ),
            row=row, col=col,
        )
        fig.add_trace(
            go.Scatter(
                x=[peak_year], y=[peak_val], mode="markers",
                marker=dict(color="#888888", size=8), showlegend=False,
                hovertemplate=f"Picco {peak_year}: {peak_val:.0f}%<extra></extra>",
            ),
            row=row, col=col,
        )
        fig.add_annotation(
            x=peak_year, y=peak_val, text=f"Picco {peak_year}", showarrow=False, yshift=13,
            font=dict(size=9, color="#888888"), xanchor="center", row=row, col=col,
        )
        fig.add_vline(x=ev_year, line=dict(color=PALETTE["calo"], dash="dot", width=1.5), row=row, col=col)
        # Eventi tardivi (vicini al bordo destro) vanno ancorati a destra per non uscire dal riquadro.
        ev_anchor = "right" if ev_year >= 2010 else "left"
        fig.add_annotation(
            x=ev_year, y=8, text=ev_label, showarrow=False, font=dict(size=9, color=PALETTE["calo"]),
            xanchor=ev_anchor, row=row, col=col,
        )
        fig.update_yaxes(range=[0, 100], row=row, col=col)

        summary.append({
            "Paese": IT_NAME[country],
            "Picco": f"{peak_year} · {peak_val:.0f}%",
            "Evento politico": f"{ev_year} · {ev_label}",
            "Divario": f"{ev_year - peak_year} anni",
            "Nucleare 2022": f"{val_2022:.0f}%",
        })

    _reading_key(fig)
    fig.update_layout(
        height=580, template="plotly_white", showlegend=False,
        title="Ogni declino nucleare ha un evento preciso, non è un trend generico",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(f"{SOURCE_NOTE} · quota % della generazione, serie dal 1985 (oltre l'intervallo 1990-2022 usato altrove)")

    st.subheader("Il divario tra picco ed evento")
    st.markdown(
        "Ordinati dal crollo più completo (Lituania, a zero) a quello appena iniziato (Francia, "
        "ancora al 63%). La colonna **Divario** è la distanza tra il picco tecnico e l'evento "
        "politico: mai sotto i 9 anni."
    )
    st.dataframe(pd.DataFrame(summary), hide_index=True, width="stretch")

    st.markdown(
        "Il picco e l'evento non coincidono mai: la **Lituania** tocca l'88% nel 1993 (Ignalina, "
        "eredità sovietica, unica centrale del paese) ma il declino a zero avviene solo dopo la "
        "chiusura definitiva del secondo reattore nel 2009, imposta come condizione di adesione "
        "all'UE, sedici anni dopo il picco. La **Germania** picca al 31.2% nel 1997, ben prima di "
        "Fukushima (2011): l'uscita dal nucleare non è la causa del declino ma la sua accelerazione: "
        "l'ultimo reattore si è fermato nell'aprile 2023, pochi mesi dopo il 2022 con cui chiude "
        "questo pannello. **Svezia** e **Belgio** mostrano il pattern più lento: entrambi i declini "
        "seguono leggi di phase-out (Svezia dopo il referendum del 1980, chiusure Barsebäck 1999 e "
        "2005; Belgio con la legge del 2003) ma restano rispettivamente al 30% e al 46.5% ancora nel "
        "2022: un phase-out annunciato non è un crollo immediato. La **Francia**, infine, è il caso "
        "più lento di tutti: picca nel 2006 (79.4%) e nel 2022 è ancora al 62.9%, nonostante la "
        "legge del 2015 avesse fissato un obiettivo del 50% mai raggiunto: il calo puntuale del "
        "2022 (vedi la pagina **Intensità di carbonio**) è dovuto a un evento congiunturale "
        "(corrosione, siccità), non alla legge."
    )


if __name__ == "__main__":
    main()
