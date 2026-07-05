"""
Pagina 4: Chi sostituisce chi (Storia)
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

from common import HIGHLIGHT_COUNTRY, IT_NAME, PALETTE, PANEL_YEAR_END, PANEL_YEAR_START, SOURCE_NOTE, get_balanced_panel, get_share_deltas, limit_page_width

bal_all, complete_countries, _ = get_balanced_panel()


def main() -> None:
    limit_page_width()
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
    st.caption(f"{SOURCE_NOTE} · {year_start} vs {year_end}")

    min_row = deltas.loc[deltas["d_renewables"].idxmin()]
    if min_row["d_renewables"] < 0:
        if min_row["start_renewables"] >= 95:
            st.markdown(
                f"Il solo caso in calo è la **{min_row['country']}** ({min_row['d_renewables']:.1f} p.p.): "
                f"non è una regressione, è un **effetto soffitto**: era già al "
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
            "decarbonizzazione: va sempre letta insieme al punto di partenza."
        )

    st.divider()
    st.subheader("Le rinnovabili sostituiscono il fossile o il nucleare?")
    st.markdown(
        "Il caso tedesco solleva una domanda che vale per l'intero panel: quando le rinnovabili "
        "crescono, a scapito di quale fonte? Scatter (posizione su due assi), l'encoding più "
        "accurato secondo Cleveland & McGill per una correlazione tra due variabili continue."
    )

    # Eccezione al pattern dominante ("le rinnovabili sostituiscono il fossile"): i paesi in cui,
    # nell'intervallo scelto, è il NUCLEARE, più del fossile, ad aver ceduto quota mentre le
    # rinnovabili crescevano. Calcolata dai dati, non una lista fissa: così resta vera al variare
    # degli anni e coincide con i punti evidenziati. Δnuc < -5 p.p. esclude i cali trascurabili;
    # |Δnuc| > |Δfos| isola i casi dove il nucleare è il bersaglio, non un comprimario (altrimenti
    # entrerebbero Regno Unito/Paesi Bassi, dove il calo di quota è quasi tutto fossile).
    is_exc = (
        (deltas["d_renewables"] > 0)
        & (deltas["d_nuclear"] < -5)
        & (deltas["d_nuclear"].abs() > deltas["d_fossil"].abs())
    )
    deltas["evidenziato"] = is_exc
    deltas["etichetta"] = [IT_NAME.get(c, c) if e else "" for c, e in zip(deltas["country"], is_exc)]

    corr_fossil = deltas["d_renewables"].corr(deltas["d_fossil"])
    corr_nuclear = deltas["d_renewables"].corr(deltas["d_nuclear"])

    # Declutter etichette: alterno alto/basso secondo il rango sull'asse x (Δrinnovabili), così due
    # paesi-eccezione con Δ simili (es. Spagna e Belgio, quasi coincidenti) finiscono uno sopra e uno
    # sotto invece di accavallarsi. Deterministico e indipendente dagli anni (il set cambia con lo slider),
    # quindi non serve, e non sarebbe possibile, assegnare le posizioni a mano come nella pagina 5.
    exc_rows = deltas[is_exc]
    xrank = exc_rows["d_renewables"].rank(method="first").astype(int)
    pos_map = dict(zip(exc_rows["country"], ["top center" if r % 2 else "bottom center" for r in xrank]))
    exc_positions = [pos_map[c] for c in exc_rows["country"]]

    col_a, col_b = st.columns(2)
    for col, y_col, label, corr in [
        (col_a, "d_fossil", "fossile", corr_fossil),
        (col_b, "d_nuclear", "nucleare", corr_nuclear),
    ]:
        fig = px.scatter(
            deltas, x="d_renewables", y=y_col, text="etichetta", color="evidenziato",
            color_discrete_map={True: HIGHLIGHT_COUNTRY, False: PALETTE["fossile"]},
            labels={
                "d_renewables": f"Δ quota rinnovabili {year_start}→{year_end} (p.p.)",
                y_col: f"Δ quota {label} {year_start}→{year_end} (p.p.)",
            },
            title=f"r = {corr:.2f}",
            template="plotly_white",
        )
        fig.update_traces(textfont_size=9)
        # Etichette: posizione a array (alto/basso alternati) sul solo trace evidenziato; l'altro non
        # ha testo, la sua posizione è irrilevante.
        for tr in fig.data:
            tr.textposition = exc_positions if tr.marker.color == HIGHLIGHT_COUNTRY else "top center"
        fig.add_hline(y=0, line_color="#888888", line_width=0.6)
        fig.add_vline(x=0, line_color="#888888", line_width=0.6)
        fig.update_layout(showlegend=False, height=440)
        col.plotly_chart(fig, width="stretch")

    st.caption(
        f"{SOURCE_NOTE} · 33 paesi, variazione quote {year_start} vs {year_end}. "
        "In blu i paesi-eccezione (calo di nucleare maggiore del calo di fossile)."
    )

    bersaglio = "fossile" if abs(corr_fossil) > abs(corr_nuclear) else "nucleare"
    exc_df = deltas[is_exc].sort_values("d_nuclear")
    exc_it = [IT_NAME.get(c, c) for c in exc_df["country"]]

    def _join_it(names: list[str]) -> str:
        if len(names) <= 1:
            return names[0] if names else ""
        return ", ".join(names[:-1]) + " e " + names[-1]

    # Ragioni storiche note (non calcolabili): mostrate solo per i paesi-eccezione che compaiono
    # davvero nell'intervallo scelto. Tutte e tre femminili → l'articolo "la" è sempre corretto.
    REASONS = {
        "Lithuania": "la Lituania ha chiuso Ignalina come condizione di adesione all'UE",
        "Germany": "la Germania è uscita dal nucleare dopo Fukushima (2011)",
        "Sweden": "la Svezia ha ridotto gradualmente la propria flotta per scelta interna",
    }
    noted = [REASONS[c] for c in exc_df["country"] if c in REASONS]

    if exc_it:
        testo_ecc = (
            f"L'eccezione (i paesi in cui è il nucleare, **più del fossile**, ad aver ceduto quota "
            f"mentre le rinnovabili crescevano) è **{_join_it(exc_it)}** ({len(exc_it)} su 33). "
        )
        if noted:
            testo_ecc += "Ragioni specifiche a ciascuno: " + "; ".join(noted) + ". "
    else:
        testo_ecc = (
            "In questo intervallo nessun paese mostra un calo di nucleare maggiore di quello del fossile. "
        )

    st.markdown(
        f"In questo intervallo la correlazione è più forte con il **{bersaglio}** "
        f"(r = {corr_fossil:.2f} col fossile, r = {corr_nuclear:.2f} col nucleare): nella maggior parte "
        "dei 33 paesi il nucleare non era presente o è rimasto stabile, e la crescita delle rinnovabili "
        "ha eroso soprattutto quota fossile. "
        + testo_ecc
        + "Nel resto del gruppo (**Italia** inclusa, che di nucleare non ne ha) a cedere terreno è il "
        "fossile, non il nucleare."
    )


if __name__ == "__main__":
    main()
