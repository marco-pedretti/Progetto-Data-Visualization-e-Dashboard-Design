"""
Pagina 3 — Cinque strategie nazionali (Storia)
=================================================
Corrisponde al Cap. 4.3 del notebook: cinque profili nazionali a confronto, small
multiples con assi condivisi 0-100% (mai un dual axis). Narrazione fissa sul mito
dell'Energiewende e sul percorso più lineare dell'Italia (nessun nucleare dal 1987).

Libertà limitata (non un filtro libero): ogni uno dei cinque slot può essere
sostituito con un altro paese del panel bilanciato, ma restano sempre cinque
profili confrontati sugli stessi assi — non un multiselect aperto come nelle
pagine Esplora.
"""

import plotly.express as px
import streamlit as st

from common import PALETTE, PROFILE_COUNTRIES, SOURCE_NOTE, get_balanced_panel

SOURCES = [("Fossile", "fossil_share_elec", "fossile"), ("Nucleare", "nuclear_share_elec", "nucleare"), ("Rinnovabili", "renewables_share_elec", "rinnovabili")]
COLOR_MAP = {label: PALETTE[key] for label, _, key in SOURCES}

bal_all, complete_countries, _ = get_balanced_panel()


def profile_controls() -> list[str]:
    """Un piccolo controllo inline, non un filtro in sidebar: qui la libertà è minima
    (sostituire un profilo), non i filtri liberi delle pagine Esplora."""
    with st.expander("🔧 Sostituisci uno o più profili", expanded=False):
        st.caption("Puoi sostituire uno o più dei cinque profili di default con un altro paese del panel.")
        cols = st.columns(5)
        slots = [
            col.selectbox(f"Profilo {i + 1}", complete_countries, index=complete_countries.index(default))
            for i, (col, default) in enumerate(zip(cols, PROFILE_COUNTRIES))
        ]
    return slots


def main() -> None:
    st.title("🗺️ Cinque strategie nazionali")
    st.markdown(
        "La media europea nasconde traiettorie molto diverse. I cinque profili di default "
        "rappresentano strategie distinte, verificate sui dati 2022: **Francia** (nucleare "
        "stabile), **Germania** (transizione: fossile ancora dominante ma in calo, nucleare "
        "quasi azzerato, rinnovabili in forte crescita), **Polonia** (fossile dominante, "
        "transizione appena iniziata), **Danimarca** (rinnovabili leader, trainate dall'eolico), "
        "**Italia** (fossile in calo costante, nessun nucleare, rinnovabili quasi raddoppiate)."
    )

    countries = profile_controls()
    if len(set(countries)) < len(countries):
        st.warning("⚠️ Hai selezionato lo stesso paese più volte in slot diversi: alcuni pannelli saranno identici.")

    d = bal_all[bal_all["country"].isin(countries)]
    long_share = d.melt(
        id_vars=["year", "country"], value_vars=[c for _, c, _ in SOURCES], var_name="fonte", value_name="quota"
    )
    long_share["fonte"] = long_share["fonte"].map({c: label for label, c, _ in SOURCES})

    fig = px.area(
        long_share, x="year", y="quota", color="fonte", facet_col="country", facet_col_wrap=3,
        color_discrete_map=COLOR_MAP,
        category_orders={"fonte": [label for label, _, _ in SOURCES], "country": countries},
        labels={"year": "", "quota": "% della generazione", "fonte": "", "country": ""},
        title="Ogni paese ha la sua transizione: nucleare stabile, fossile dominante o svolta rinnovabile",
        template="plotly_white",
    )
    fig.update_yaxes(range=[0, 100])
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_layout(height=560)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"{SOURCE_NOTE} — quota % della generazione, 1990–2022")

    st.divider()
    st.subheader("Il mito dell'Energiewende")
    st.markdown(
        """
        Il caso tedesco è quello più spesso frainteso: nel 1990 il mix era **68% fossile / 28%
        nucleare / 3.5% rinnovabili**, nel 2022 è **49.5% / 6.1% / 44.4%** — il nucleare non è
        stato sostituito dalle rinnovabili, ma da un mix di rinnovabili in crescita **e** fossile
        ancora dominante. Il calo del nucleare tedesco viene spesso letto — erroneamente — come
        prova che "le rinnovabili hanno sostituito il nucleare in Europa", mentre è un pattern
        specifico di un singolo paese (approfondito, su tutto il panel, nella pagina
        **Chi sostituisce chi**).

        L'**Italia** mostra invece il percorso più lineare tra i cinque: nessun nucleare da
        confrontare (uscita completa dopo il referendum del 1987, quota già a 0 nel 1990), quindi
        tutta la transizione passa dalla sostituzione diretta fossile→rinnovabili — dall'84% al
        64% di fossile, dal 16% al 36% di rinnovabili, senza la complessità aggiuntiva del caso
        tedesco.
        """
    )


if __name__ == "__main__":
    main()
