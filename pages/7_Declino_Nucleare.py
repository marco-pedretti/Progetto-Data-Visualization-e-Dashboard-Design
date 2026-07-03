"""
Pagina 7 — Declino del nucleare (Storia)
============================================
Corrisponde al Cap. 4.8 del notebook: i cinque paesi già isolati in "Chi sostituisce
chi" (Cap. 4.6) come eccezione — dove il calo del nucleare coincide con la crescita
rinnovabile, non con il fossile — mostrano ciascuno un picco storico seguito da un
evento politico preciso, non un trend generico. Serie estesa dal 1985 (non il solo
panel bilanciato 1990-2022): per Belgio e Lituania il picco storico cade a ridosso o
prima di quella soglia.

Nessuna libertà di personalizzazione: narrazione e cinque paesi sono fissi. A
differenza di "Cinque strategie nazionali", qui gli eventi politici sono cablati per
paese — sostituire uno slot con un altro paese romperebbe la narrazione, non la
arricchirebbe.
"""

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from common import NUCLEAR_EVENTS, PALETTE, SOURCE_NOTE, get_nuclear_history

NUCLEAR_COUNTRIES = list(NUCLEAR_EVENTS.keys())
POSITIONS = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]


def main() -> None:
    st.title("☢️ Declino del nucleare: picco, evento, crollo")
    st.markdown(
        "La pagina **Chi sostituisce chi** isola un piccolo gruppo di paesi dove il calo del "
        "nucleare *coincide* con la crescita rinnovabile: Germania, Lituania, Svezia, Francia e "
        "Belgio. Per ciascuno la domanda naturale è **quando** è iniziato il declino e **perché** "
        "— non solo quanto è cambiata la quota."
    )

    history = get_nuclear_history(NUCLEAR_COUNTRIES)

    fig = make_subplots(rows=2, cols=3, subplot_titles=NUCLEAR_COUNTRIES + [""])
    for (row, col), country in zip(POSITIONS, NUCLEAR_COUNTRIES):
        s = history[history["country"] == country].sort_values("year")
        peak_row = s.loc[s["nuclear_share_elec"].idxmax()]
        ev_year, ev_label = NUCLEAR_EVENTS[country]

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
                x=[peak_row["year"]], y=[peak_row["nuclear_share_elec"]], mode="markers",
                marker=dict(color="black", size=8), showlegend=False,
                hovertemplate=f"Picco {int(peak_row['year'])}: {peak_row['nuclear_share_elec']:.0f}%<extra></extra>",
            ),
            row=row, col=col,
        )
        fig.add_vline(x=ev_year, line=dict(color=PALETTE["calo"], dash="dot", width=1.5), row=row, col=col)
        fig.add_annotation(
            x=ev_year, y=8, text=ev_label, showarrow=False, font=dict(size=9, color=PALETTE["calo"]),
            xanchor="left", row=row, col=col,
        )
        fig.update_yaxes(range=[0, 100], row=row, col=col)

    fig.update_xaxes(visible=False, row=2, col=3)
    fig.update_yaxes(visible=False, row=2, col=3)
    fig.update_layout(
        height=560, template="plotly_white", showlegend=False,
        title="Ogni declino nucleare ha un evento preciso, non è un trend generico",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(f"{SOURCE_NOTE} — quota % della generazione, serie estesa dal 1985 (non solo il panel bilanciato)")

    st.markdown(
        "Il picco e l'evento non coincidono mai: la **Lituania** tocca l'88% nel 1993 (Ignalina, "
        "eredità sovietica, unica centrale del paese) ma il declino a zero avviene solo dopo la "
        "chiusura definitiva del secondo reattore nel 2009, imposta come condizione di adesione "
        "all'UE — sedici anni dopo il picco. La **Germania** picca al 31.2% nel 1997, ben prima di "
        "Fukushima (2011): l'uscita dal nucleare non è la causa del declino ma la sua accelerazione "
        "— l'ultimo reattore si è fermato nell'aprile 2023, pochi mesi dopo il 2022 con cui chiude "
        "questo pannello. **Svezia** e **Belgio** mostrano il pattern più lento: entrambi i declini "
        "seguono leggi di phase-out (Svezia dopo il referendum del 1980, chiusure Barsebäck 1999 e "
        "2005; Belgio con la legge del 2003) ma restano rispettivamente al 30% e al 46.5% ancora nel "
        "2022 — un phase-out annunciato non è un crollo immediato. La **Francia**, infine, è il caso "
        "più lento di tutti: picca nel 2006 (79.4%) e nel 2022 è ancora al 62.9%, nonostante la "
        "legge del 2015 avesse fissato un obiettivo del 50% mai raggiunto — il calo puntuale del "
        "2022 (vedi la pagina **Intensità di carbonio**) è dovuto a un evento congiunturale "
        "(corrosione, siccità), non alla legge."
    )


if __name__ == "__main__":
    main()
