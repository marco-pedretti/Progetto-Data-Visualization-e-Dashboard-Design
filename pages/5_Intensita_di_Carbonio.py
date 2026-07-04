"""
Pagina 5 — Intensità di carbonio (Storia)
============================================
Corrisponde al Cap. 4.7 del notebook: l'intensità di carbonio del mix elettrico
(gCO2eq/kWh) come indicatore di esito, alternativo alle quote di mix — nucleare e
rinnovabili sono entrambe fonti a basse emissioni, quindi la sola quota non dice se
un paese ha davvero ridotto le proprie emissioni. Solo il calcolo corretto (media
pesata con NaN mascherati) è mostrato qui; il confronto naive-vs-corretto che ha
portato a questa correzione resta nel notebook, non in dashboard.

Libertà limitata: si può affiancare alla media europea l'andamento di un singolo
paese, ma il grafico e la narrazione principale restano fissi.

Estesa (← Cap. 4.9 del notebook) con uno scatter fisso quota fossile vs intensità di
carbonio sull'ultimo anno del panel, per mostrare esplicitamente perché le due
metriche sono correlate ma non intercambiabili.
"""

import plotly.graph_objects as go
import streamlit as st

from common import PALETTE, SOURCE_NOTE, get_balanced_panel, get_carbon_intensity

bal_all, complete_countries, _ = get_balanced_panel()
carbon = get_carbon_intensity()


def main() -> None:
    st.title("🌍 Intensità di carbonio")
    st.markdown(
        "Le quote di mix rispondono alla domanda \"di cosa è fatta l'elettricità\", ma nucleare e "
        "rinnovabili sono entrambe fonti a basse emissioni: un paese può ridurre la quota nucleare "
        "aumentando le rinnovabili senza migliorare — o persino peggiorando — il proprio bilancio "
        "emissivo reale, se la differenza viene coperta da fossile nel frattempo. "
        "`carbon_intensity_elec` (gCO₂eq/kWh) misura l'esito, non la composizione."
    )

    choice = st.selectbox(
        "Affianca un paese alla media europea (grafico e narrazione principale restano fissi)",
        ["(nessuno)"] + complete_countries,
    )
    country = None if choice == "(nessuno)" else choice

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=carbon.index, y=carbon["panel_bilanciato"], name="Panel bilanciato (33 paesi)",
        line=dict(color=PALETTE["nucleare"], width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=carbon.index, y=carbon["europe_owid"], name='Aggregato "Europe" (OWID, validazione)',
        line=dict(color="#888888", width=1, dash="dash"),
    ))
    if country:
        country_series = bal_all[bal_all["country"] == country].set_index("year")["carbon_intensity_elec"]
        fig.add_trace(go.Scatter(x=country_series.index, y=country_series.values, name=country, line=dict(width=2.5)))

    last_year = int(carbon.index.max())
    fig.add_annotation(
        x=last_year, y=carbon["panel_bilanciato"].loc[last_year],
        text="Flotta nucleare francese ferma per ispezioni<br>+ siccità (idroelettrico in calo)",
        showarrow=True, arrowhead=2, ax=-90, ay=-60, font=dict(size=10),
    )
    fig.update_layout(
        title="L'intensità di carbonio si è quasi dimezzata dal 1990, con una battuta d'arresto nel 2022",
        yaxis_title="gCO₂eq / kWh", template="plotly_white", height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_yaxes(rangemode="tozero")
    st.plotly_chart(fig, width="stretch")
    st.caption(f"{SOURCE_NOTE} — panel bilanciato, righe con carbon_intensity_elec valido")

    first_year = int(carbon.index.min())
    min_year = int(carbon["panel_bilanciato"].idxmin())
    st.markdown(
        f"L'intensità di carbonio del panel scende in modo pressoché continuo da "
        f"**{carbon['panel_bilanciato'].loc[first_year]:.0f} gCO₂/kWh ({first_year}) a "
        f"{carbon['panel_bilanciato'].loc[min_year]:.0f} ({min_year})** — quasi dimezzata — "
        "validata dal confronto con l'aggregato \"Europe\" pubblicato direttamente da OWID "
        "(linea tratteggiata, che coincide entro l'1-2% dal 2000 in poi). L'unica interruzione è "
        f"il **{last_year}** ({carbon['panel_bilanciato'].loc[min_year]:.0f} → "
        f"{carbon['panel_bilanciato'].loc[last_year]:.0f}): non un'inversione di tendenza ma uno "
        "shock di un solo anno — la produzione nucleare francese è scesa di circa un quinto per le "
        "ispezioni sulla corrosione da stress dei reattori, mentre la siccità ha ridotto "
        "l'idroelettrico nel panel; la differenza è stata coperta da fossile."
    )

    if country:
        country_last = bal_all.loc[
            (bal_all["country"] == country) & (bal_all["year"] == last_year), "carbon_intensity_elec"
        ]
        if not country_last.empty and country_last.notna().iloc[0]:
            ratio = country_last.iloc[0] / carbon["panel_bilanciato"].loc[last_year]
            relazione = "più alta" if ratio > 1 else "più bassa"
            st.markdown(
                f"**{country}** nel {last_year} ha un'intensità di carbonio di "
                f"{country_last.iloc[0]:.0f} gCO₂/kWh: {relazione} della media europea di un "
                f"fattore {ratio:.1f}×."
            )

    st.divider()
    st.subheader("Perché l'intensità di carbonio, non solo la quota fossile")

    y_last = bal_all[(bal_all["year"] == last_year) & (bal_all["carbon_intensity_elec"].notna())]
    corr_fc = y_last["fossil_share_elec"].corr(y_last["carbon_intensity_elec"])

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=y_last["fossil_share_elec"], y=y_last["carbon_intensity_elec"], mode="markers",
        marker=dict(color=PALETTE["fossile"], size=9, opacity=0.7, line=dict(color="white", width=1)),
        text=y_last["country"],
        hovertemplate="%{text}<br>Fossile: %{x:.1f}%<br>Intensità: %{y:.0f} gCO₂/kWh<extra></extra>",
        showlegend=False,
    ))
    for c in ["Germany", "Netherlands", "Poland", "Norway", "France", "Italy"]:
        row = y_last[y_last["country"] == c]
        if not row.empty:
            fig2.add_trace(go.Scatter(
                x=row["fossil_share_elec"], y=row["carbon_intensity_elec"], mode="markers+text",
                marker=dict(color=PALETTE["calo"], size=10), text=[c], textposition="top center",
                showlegend=False, hoverinfo="skip",
            ))
    fig2.update_layout(
        title=f"r = {corr_fc:.2f} — ma a parità di quota fossile l'intensità varia ancora",
        xaxis_title="Quota fossile (%)", yaxis_title="Intensità di carbonio (gCO₂/kWh)",
        template="plotly_white", height=480,
    )
    fig2.update_xaxes(range=[0, 100])
    fig2.update_yaxes(rangemode="tozero")
    st.plotly_chart(fig2, width="stretch")
    st.caption(f"{SOURCE_NOTE} — panel bilanciato, 33 paesi, {last_year}")

    st.markdown(
        f"La correlazione è fortissima (**r = {corr_fc:.2f}**): la quota fossile spiega la quasi "
        "totalità della varianza dell'intensità di carbonio. Ma le due metriche non sono "
        "intercambiabili: **Germania** (49.5% fossile, 420 gCO₂/kWh) e **Paesi Bassi** (56.4% "
        "fossile, 326 gCO₂/kWh) hanno quote fossili simili — la Germania perfino più bassa — ma "
        "un'intensità molto diversa, perché il mix fossile non è omogeneo: il carbone (in "
        "particolare la lignite tedesca) emette più del gas naturale (dominante nel mix olandese) "
        "a parità di quota di generazione. La quota fossile dice *quanto* fossile c'è; l'intensità "
        "di carbonio dice *quanto inquina* quel fossile."
    )


if __name__ == "__main__":
    main()
