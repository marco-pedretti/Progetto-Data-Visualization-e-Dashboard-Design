# ⚡ Mix elettrico in Europa — Data Visualization & Dashboard Design

**🇮🇹 Italiano** · [🇬🇧 English](README.en.md)

Analisi dell'evoluzione del mix di produzione elettrica nei paesi europei dal 1990 a oggi,
con focus sul confronto tra **nucleare, rinnovabili e fossili**. Progetto per il corso
*Data Visualization e Dashboard Design* (Master UNICATT).

**🔗 App online:** https://pedretti-marco-progetto-data-visualization-e-dashboard-design.streamlit.app

Il progetto è composto da **due deliverable complementari**:

- **`eda_energia_europa.ipynb`** — il notebook di analisi: documenta i dati, l'EDA, la gestione
  dei valori mancanti e soprattutto il *perché* di ogni scelta di visualizzazione (encoding, colore,
  tipo di grafico), inclusi gli errori concettuali individuati e corretti lungo il percorso.
- **Dashboard Streamlit** (`streamlit_app.py` + `pages/`) — il prodotto finale interattivo, che
  traduce i risultati del notebook in pagine esplorabili e narrazioni guidate.

---

## 📊 I dati

Fonte unica: **[OWID Energy Dataset](https://github.com/owid/energy-data)** (Our World in Data,
licenza CC BY), che aggrega dati istituzionali soprattutto da **Ember** (dati elettrici annuali,
copertura sistematica dal 1990 per l'Europa) ed **Energy Institute** (*Statistical Review of World
Energy*, serie storiche più lunghe).

Il dataset grezzo integrale e il codebook sono inclusi nella cartella [`data/`](data/) ed è possibile
scaricarli direttamente dalla Home della dashboard, per riprodurre l'analisi da zero.

Gran parte dell'analisi lavora su un **panel bilanciato** di 33 paesi europei con serie complete
1990–2022, per evitare gli artefatti di composizione dovuti alla copertura disomogenea (la
costruzione e la motivazione sono documentate nel Cap. 4.1 del notebook).

---

## 🗂️ Struttura della dashboard

Il menu (in alto) divide le pagine in due famiglie:

### 🧭 Esplora — filtri liberi su paesi, periodo, ambito e metrica
| Pagina | Cosa fa |
|---|---|
| **Scheda Paese** | Scheda libera su una singola entità qualunque (mondo e aggregati inclusi). |
| **Strategie a confronto** | Confronto testa-a-testa di 2–4 paesi a scelta: KPI, mix, import/export, crescita. |
| **Mappa Europa/Mondo** | Coropleta con ambito, metrica e anno selezionabili, animazione temporale. |

### 📖 Storia — narrazione guidata su un risultato verificato
| Pagina | Domanda |
|---|---|
| **Chi sostituisce chi** | Quando le rinnovabili crescono, a scapito di quale fonte (fossile o nucleare)? |
| **Declino del nucleare** | Ogni crollo del nucleare ha un evento politico preciso dietro. |
| **Firme storiche nei dati** | I dati mancanti come indicatore geopolitico. |

I numeri narrati nelle pagine sono **ricalcolati a schermo dai dati**, non scritti a mano, così
restano corretti al variare dei parametri.

---

## 📁 Struttura del repository

```
├── eda_energia_europa.ipynb      # notebook di analisi (deliverable 1)
├── streamlit_app.py              # entrypoint/router della dashboard (deliverable 2)
├── common.py                     # costanti e funzioni condivise tra le pagine
├── pages/                        # le pagine della dashboard multi-page
│   ├── Home.py
│   ├── Scheda_Paese.py
│   ├── Strategie_a_Confronto.py
│   ├── Mappa_Europa_Mondo.py
│   ├── Chi_Sostituisce_Chi.py
│   ├── Declino_Nucleare.py
│   └── Firme_Storiche.py
├── data/                         # dataset OWID grezzo + codebook
├── requirements.txt
└── README.md
```

---

## ▶️ Eseguire in locale

Serve Python 3.11+.

```bash
# 1. clona il repository
git clone https://github.com/marco-pedretti/Progetto-Data-Visualization-e-Dashboard-Design.git
cd Progetto-Data-Visualization-e-Dashboard-Design

# 2. (consigliato) crea un ambiente virtuale
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 3. installa le dipendenze
pip install -r requirements.txt

# 4. avvia la dashboard
streamlit run streamlit_app.py
```

L'app si aprirà nel browser su `http://localhost:8501`. Il notebook si apre invece con Jupyter o
direttamente in VS Code.

---

## 🎓 Contesto

Elaborato per la prova finale del corso *Data Visualization e Dashboard Design* (Master in
Intelligenza Artificiale e Data Science per le imprese, UNICATT ALTIS e POLIMI). L'impostazione applica i principi
del corso — gerarchia percettiva di **Cleveland & McGill**, palette **colorblind-safe** (Okabe-Ito),
storytelling secondo Nussbaumer Knaflic ed esplicita assenza degli anti-pattern (3D, dual axis, assi
troncati, rainbow) — sia nel notebook sia nella dashboard.
