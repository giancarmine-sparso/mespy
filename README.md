# mech-lab-tools

Toolbox Python modulare per l'analisi dei dati di laboratorio di meccanica (primo anno).

Raccoglie le funzioni che mi ritrovo a riscrivere ogni volta che apro un nuovo notebook: caricare un CSV, calcolare medie pesate, propagare gli errori, fare un fit lineare. L'idea è avere un posto solo dove tenere queste cose, documentarle bene una volta, e importarle nei notebook delle singole esperienze senza copia-incolla.

## Struttura

```
mech-lab-tools/
├── src/
│   └── mech_lab_tools/          ← moduli Python del toolbox
│       ├── io_utils.py          ← caricamento CSV con gestione separatori e decimali
│       ├── stats_utils.py       ← media pesata, varianza, covarianza, mediana
│       ├── plot_utils.py        ← istogrammi colorblind-safe
│       ├── fit_utils.py         ← fit lineare con incertezze          [WIP]
│       ├── format_utils.py      ← formattazione x ± σ                 [WIP]
│       └── uncertainty_utils.py ← propagazione degli errori           [WIP]
├── data/
│   ├── raw/                     ← dati originali (non tracciati da git)
│   ├── processed/               ← risultati processati (non tracciati da git)
│   └── reference/               ← dataset di test e campioni di riferimento
├── figures/                     ← grafici esportati (non tracciati da git)
├── notebooks/                   ← notebook Jupyter di prova
├── docs/                        ← sorgente LaTeX e documentazione compilata (main.pdf)
│   └── sections/                ← sorgenti LaTeX divisi per modulo
├── tests/                       ← test dei moduli
├── tools/                       ← script di supporto al Makefile
└── references/                  ← dispense del corso (non tracciate da git)
```

## Stack

Il toolbox è costruito sopra le librerie scientifiche standard di Python: NumPy, pandas e matplotlib.
L'obiettivo non è sostituirle, ma fornire un piccolo livello riutilizzabile pensato per i flussi di lavoro del laboratorio di meccanica del primo anno.

## Prerequisiti

- Python 3 (≥ 3.12)
- `git`

- `lualatex` e `latexmk` — solo per compilare la documentazione **(opzionale)**

## Come iniziare

Clona la repo e spostati nella directory:

```bash
git clone https://github.com/giancarmine-sparso/mech-lab-tools
cd mech-lab-tools
```

Crea il virtualenv e installa le dipendenze:

```bash
make setup
```

Attiva il virtualenv per usare i moduli nei notebook:

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (cmd):**

```cmd
.venv\Scripts\activate.bat
```

> **Nota:** con [direnv](https://direnv.net/) installato, il virtualenv si attiva automaticamente entrando nella directory — non serve il passo manuale.

## Utilizzo

```python
from mech_lab_tools import load_csv, weighted_mean, standard_deviation

df = load_csv("data/raw/misure.csv", sep=";", decimal=",")
x_bar = weighted_mean(df["lunghezza_mm"], 1 / df["sigma_mm"]**2)
sigma = standard_deviation(df["lunghezza_mm"])
```

## Documentazione

La documentazione dettagliata di ciascun modulo è in `docs/main.pdf`.
Per ricompilarla (richiede `lualatex` e `latexmk`):

```bash
make docs
```

## Target del Makefile

| Target | Descrizione |
| --- | --- |
| `make setup` | Crea il virtualenv e installa le dipendenze |
| `make venv` | Crea solo il virtualenv |
| `make install` | Installa solo le dipendenze Python |
| `make check-tex` | Verifica i prerequisiti LaTeX |
| `make docs` | Compila la documentazione PDF |
| `make docs-clean` | Rimuove i file temporanei LaTeX |
| `make clean` | Rimuove tutti i file temporanei |
