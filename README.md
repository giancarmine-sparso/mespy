# mech-lab-tools

Toolbox Python modulare per l'analisi dei dati di laboratorio di meccanica (primo anno).

Raccoglie le funzioni che mi ritrovo a riscrivere ogni volta che apro un nuovo notebook: caricare un CSV, calcolare medie pesate, propagare gli errori, fare un fit lineare. L'idea è avere un posto solo dove tenere queste cose, documentarle bene una volta, e importarle nei notebook delle singole esperienze senza copia-incolla.

## Struttura

```
mech-lab-tools/
├── script/                      ← moduli Python del toolbox
│   ├── io_utils.py              ← caricamento CSV con gestione separatori e decimali
│   ├── stats_utils.py           ← media pesata, varianza, covarianza, mediana
│   ├── plot_utils.py            ← istogrammi colorblind-safe
│   ├── fit_utils.py             ← fit lineare con incertezze          [WIP]
│   ├── format_utils.py          ← formattazione x ± σ                 [WIP]
│   └── uncertainty_utils.py     ← propagazione degli errori           [WIP]
├── dati/
│   ├── grezzi/                  ← dati originali (non tracciati da git)
│   └── elaborati/               ← risultati processati (non tracciati da git)
├── dati_riferimento/            ← dataset di test e campioni di riferimento
├── figure/                      ← grafici esportati (non tracciati da git)
├── notebooks/                   ← notebook Jupyter di prova
├── documentazione/              ← 📖 sorgente LaTeX + main.pdf  ← leggi qui per capire come funzionano gli script
└── references/                  ← dispense del corso (non tracciate da git)
```
