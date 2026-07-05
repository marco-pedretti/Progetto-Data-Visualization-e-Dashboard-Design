# ⚡ Europe's Electricity Mix — Data Visualization & Dashboard Design

[🇮🇹 Italiano](README.md) · **🇬🇧 English**

Analysis of how the electricity generation mix has evolved across European countries from 1990 to
today, focusing on the comparison between **nuclear, renewables and fossil fuels**. Final project
for the *Data Visualization e Dashboard Design* course (UNICATT Master's).

**🔗 Live app:** https://pedretti-marco-progetto-data-visualization-e-dashboard-design.streamlit.app

The project consists of **two complementary deliverables**:

- **`eda_energia_europa.ipynb`** — the analysis notebook: documents the data, the EDA, missing-value
  handling and, above all, the *reasoning* behind every visualization choice (encoding, colour, chart
  type), including the conceptual mistakes spotted and corrected along the way.
- **Streamlit dashboard** (`streamlit_app.py` + `pages/`) — the final interactive product, which turns
  the notebook's findings into explorable pages and guided narratives.

> The notebook and the in-app text are written in **Italian** (the project is a university deliverable
> assessed in Italian); this README is the English entry point to the repository.

---

## 📊 The data

Single source: **[OWID Energy Dataset](https://github.com/owid/energy-data)** (Our World in Data,
CC BY licence), which aggregates institutional data mainly from **Ember** (annual electricity data,
systematic coverage from 1990 for Europe) and the **Energy Institute** (*Statistical Review of World
Energy*, longer historical series).

The full raw dataset and the codebook are included in the [`data/`](data/) folder and can also be
downloaded directly from the dashboard's Home page, so the analysis can be reproduced from scratch.

Most of the analysis works on a **balanced panel** of 33 European countries with complete series over
1990–2022, to avoid the composition artefacts caused by uneven coverage (its construction and
rationale are documented in Chapter 4.1 of the notebook).

---

## 🗂️ Dashboard structure

The top menu splits the pages into two families:

### 🧭 Explore — free filters on countries, period, scope and metric
| Page | What it does |
|---|---|
| **Scheda Paese** (Country Card) | Free deep-dive on any single entity (world and aggregates included). |
| **Strategie a confronto** (Strategies compared) | Head-to-head comparison of 2–4 chosen countries: KPIs, mix, imports/exports, growth. |
| **Mappa Europa/Mondo** (Europe/World Map) | Choropleth with selectable scope, metric and year, plus time animation. |

### 📖 Story — guided narrative around a verified result
| Page | Question |
|---|---|
| **Chi sostituisce chi** (Who replaces whom) | When renewables grow, at the expense of which source (fossil or nuclear)? |
| **Intensità di carbonio** (Carbon intensity) | The mix got cleaner, but what about emissions per kWh? |
| **Declino del nucleare** (Nuclear decline) | Every nuclear collapse has a precise political event behind it. |
| **Firme storiche nei dati** (Historical signatures in the data) | Missing data as a geopolitical indicator. |

The figures narrated in the pages are **recomputed on screen from the data**, not hard-coded, so they
stay correct as the parameters change.

---

## 📁 Repository structure

```
├── eda_energia_europa.ipynb      # analysis notebook (deliverable 1)
├── streamlit_app.py              # dashboard entrypoint/router (deliverable 2)
├── common.py                     # constants and functions shared across pages
├── pages/                        # the multi-page dashboard pages
│   ├── Home.py
│   ├── Scheda_Paese.py
│   ├── Strategie_a_Confronto.py
│   ├── Mappa_Europa_Mondo.py
│   ├── Chi_Sostituisce_Chi.py
│   ├── Intensita_di_Carbonio.py
│   ├── Declino_Nucleare.py
│   └── Firme_Storiche.py
├── data/                         # raw OWID dataset + codebook
├── requirements.txt
└── README.md
```

---

## ▶️ Running locally

Requires Python 3.11+.

```bash
# 1. clone the repository
git clone https://github.com/marco-pedretti/Progetto-Data-Visualization-e-Dashboard-Design.git
cd Progetto-Data-Visualization-e-Dashboard-Design

# 2. (recommended) create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 3. install the dependencies
pip install -r requirements.txt

# 4. launch the dashboard
streamlit run streamlit_app.py
```

The app opens in the browser at `http://localhost:8501`. The notebook opens with Jupyter or directly
in VS Code.

---

## 🎓 Context

Final-exam project for the *Data Visualization e Dashboard Design* course (Master's in Artificial
Intelligence and Data Science for Business, UNICATT ALTIS and POLIMI). The approach applies the
course's principles — **Cleveland & McGill**'s perceptual hierarchy, a **colourblind-safe** palette
(Okabe-Ito), storytelling à la Nussbaumer Knaflic, and the deliberate absence of anti-patterns (3D,
dual axis, truncated axes, rainbow) — in both the notebook and the dashboard.
