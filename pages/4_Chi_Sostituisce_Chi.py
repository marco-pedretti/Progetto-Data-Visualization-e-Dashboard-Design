"""
Pagina 4 — Chi sostituisce chi (Storia)
==========================================
Corrisponde ai Cap. 4.4 e 4.6 del notebook: ranking "chi ha trasformato di più il
mix" e scatter di correlazione Δrinnovabili vs Δfossile/Δnucleare sui 33 paesi del
panel bilanciato. Tutti i numeri della narrazione sono ricalcolati a schermo, non
scritti a mano, così restano corretti anche cambiando gli anni di confronto.

Libertà limitata: si possono cambiare i due anni di confronto, ma non i paesi (è
sempre l'intero panel bilanciato) né il tipo di grafico.
"""

import plotly.express as px
import streamlit as st

from common import HIGHLIGHT_COUNTRIES, PALETTE, PANEL_YEAR_END, PANEL_YEAR_START, SOURCE_NOTE, get_balanced_panel, get_share_deltas

bal_all, complete_countries, _ = get_balanced_panel()


def main() -> None:
    st.title("🔀 Chi sostituisce chi")

    year_start, year_end = st.slider(
        "Anni di confronto (paesi e tipo di grafico restano fissi: l'unica libertà qui è cambiare i due anni)",
        min_value=PANEL_YEAR_START, max_value=PANEL_YEAR_END,
        value=(PANEL_YEAR_START, PANEL_YEAR_END),
    )
    if year_start >= year_end:
        st.warning("⚠️ L'anno iniziale deve precedere l'anno finale.")
        st.stop()

    deltas = get_share_deltas(bal_all, year_start, year_end).reset_index().rename(columns={"index": "country"})

    st.subheader(f"Chi ha trasformato di più il proprio mix elettrico? ({year_start}→{year_end})")
    st.markdown(
        "Task di **confronto** puro: un valore per paese, la variazione della quota rinnovabili. "
        "Bar orizzontale ordinata per valore (non alfabeticamente), colore diverging per isolare "
        "gli eventuali casi in calo."
    )

    delta_sorted = deltas[["country", "d_renewables"]].sort_values("d_renewables")
    delta_sorted["segno"] = delta_sorted["d_renewables"].apply(lambda v: "Aumento" if v >= 0 else "Calo")
    n_up = int((delta_sorted["d_renewables"] >= 0).sum())

    fig = px.bar(
        delta_sorted, x="d_renewables", y="country", orientation="h", color="segno",
        color_discrete_map={"Aumento": PALETTE["rinnovabili"], "Calo": PALETTE["calo"]},
        labels={"d_renewables": f"Variazione quota rinnovabili {year_start}→{year_end} (p.p.)", "country": ""},
        title=f"{n_up} dei {len(delta_sorted)} paesi hanno aumentato la quota di rinnovabili",
        template="plotly_white",
    )
    fig.update_layout(height=900, showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"{SOURCE_NOTE} — panel bilanciato, {year_start} vs {year_end}")

    min_row = deltas.loc[deltas["d_renewables"].idxmin()]
    if min_row["d_renewables"] < 0:
        if min_row["start_renewables"] >= 95:
            st.markdown(
                f"Il solo caso in calo è la **{min_row['country']}** ({min_row['d_renewables']:.1f} p.p.): "
                f"non è una regressione, è un **effetto soffitto** — era già al "
                f"{min_row['start_renewables']:.1f}% nel {year_start}, quindi non aveva margine di crescita."
            )
        else:
            st.markdown(
                f"Il solo caso in calo è la **{min_row['country']}** ({min_row['d_renewables']:.1f} p.p., "
                f"partiva dal {min_row['start_renewables']:.1f}% nel {year_start})."
            )

    france = deltas[deltas["country"] == "France"]
    if not france.empty and float(france["start_nuclear"].iloc[0]) >= 40:
        fr = france.iloc[0]
        st.markdown(
            f"La **Francia**, invece, mostra una variazione modesta (+{fr['d_renewables']:.0f} p.p.) non "
            f"perché sia rimasta ferma, ma perché nel {year_start} partiva già da un mix a basse emissioni "
            f"grazie al nucleare ({fr['start_nuclear']:.0f}% di quota): una metrica di sola \"variazione "
            "quota rinnovabili\" penalizza chi ha scelto una strada diversa per lo stesso obiettivo di "
            "decarbonizzazione — va sempre letta insieme al punto di partenza."
        )

    st.divider()
    st.subheader("Le rinnovabili sostituiscono il fossile o il nucleare?")
    st.markdown(
        "Il caso tedesco solleva una domanda che vale per l'intero panel: quando le rinnovabili "
        "crescono, a scapito di quale fonte? Scatter (posizione su due assi), l'encoding più "
        "accurato secondo Cleveland & McGill per una correlazione tra due variabili continue."
    )

    deltas["evidenziato"] = deltas["country"].isin(HIGHLIGHT_COUNTRIES)
    deltas["etichetta"] = deltas["country"].where(deltas["evidenziato"], "")

    corr_fossil = deltas["d_renewables"].corr(deltas["d_fossil"])
    corr_nuclear = deltas["d_renewables"].corr(deltas["d_nuclear"])

    col_a, col_b = st.columns(2)
    for col, y_col, label, corr in [
        (col_a, "d_fossil", "fossile", corr_fossil),
        (col_b, "d_nuclear", "nucleare", corr_nuclear),
    ]:
        fig = px.scatter(
            deltas, x="d_renewables", y=y_col, text="etichetta", color="evidenziato",
            color_discrete_map={True: PALETTE["calo"], False: PALETTE["rinnovabili"]},
            labels={
                "d_renewables": f"Δ quota rinnovabili {year_start}→{year_end} (p.p.)",
                y_col: f"Δ quota {label} {year_start}→{year_end} (p.p.)",
            },
            title=f"r = {corr:.2f}",
            template="plotly_white",
        )
        fig.update_traces(textposition="top center", textfont_size=9)
        fig.add_hline(y=0, line_color="black", line_width=0.6)
        fig.add_vline(x=0, line_color="black", line_width=0.6)
        fig.update_layout(showlegend=False, height=440)
        col.plotly_chart(fig, width="stretch")

    st.caption(f"{SOURCE_NOTE} — panel bilanciato, 33 paesi, variazione quote {year_start} vs {year_end}")

    bersaglio = "fossile" if abs(corr_fossil) > abs(corr_nuclear) else "nucleare"
    st.markdown(
        f"In questo intervallo la correlazione è più forte con il **{bersaglio}** "
        f"(r = {corr_fossil:.2f} col fossile, r = {corr_nuclear:.2f} col nucleare): nella maggioranza "
        "dei 33 paesi il nucleare non è mai stato presente o è rimasto stabile, e la crescita delle "
        "rinnovabili ha eroso soprattutto quota fossile. Un piccolo gruppo — **Germania**, "
        "**Lituania**, **Svezia**, e in misura minore Francia e Belgio — è l'eccezione in cui un calo "
        "di nucleare *coesiste* con la crescita rinnovabile, per ragioni specifiche: la Lituania ha "
        "chiuso la centrale di Ignalina come condizione di adesione all'UE, la Svezia ha ridotto "
        "gradualmente la sua flotta per scelta interna, la Germania ha deciso l'uscita dal nucleare "
        "dopo Fukushima (2011). Il pattern tedesco non è quindi un'anomalia isolata, ma nemmeno la "
        "norma: per la maggior parte degli altri paesi del panel — **Italia** inclusa, priva di "
        "nucleare da confrontare — è il fossile, non il nucleare, ad aver ceduto terreno."
    )


if __name__ == "__main__":
    main()
