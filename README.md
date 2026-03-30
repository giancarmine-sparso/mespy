# mech-lab-tools

Toolbox Python per l'analisi dei dati di laboratorio di meccanica.

L'obiettivo del progetto e' raccogliere in un unico package le utility che tornano spesso nei notebook di laboratorio: caricamento CSV, statistiche descrittive e pesate, istogrammi e fit lineare con incertezze.

Lo stato attuale e' ancora `Alpha`: il package e' gia' utilizzabile per casi semplici, ma l'API non va considerata stabile.

## Cosa c'e' oggi

Il package espone direttamente:

- `load_csv`
- `median`
- `weighted_mean`
- `variance`
- `covariance`
- `standard_deviation`
- `lin_fit`

I moduli attualmente presenti in `src/mech_lab_tools` sono:

- `io_utils.py`: lettura CSV con gestione di separatori, decimali, colonne richieste e missing values
- `stats_utils.py`: funzioni statistiche di base, anche con pesi
- `plot_utils.py`: istogrammi con media e banda `±1σ`
- `fit_utils.py`: fit lineare pesato con residui, incertezze sui parametri e grafico opzionale

## Struttura del progetto

```text
mech-lab-tools/
├── src/mech_lab_tools/   # package Python
├── tests/                # test pytest
├── notebooks/            # notebook di prova e dimostrazione
├── docs/                 # documentazione LaTeX e PDF
├── data/reference/       # dataset di riferimento per test/esempi
├── figures/              # figure esportate
├── tools/                # script di supporto
├── pyproject.toml        # metadata del package
└── Makefile              # comandi di setup e documentazione
```

## Requisiti

- Python `>= 3.12`
- `git`
- `lualatex` e `latexmk` solo se vuoi ricompilare la documentazione

## Installazione rapida

Clona il repository ed entra nella directory:

```bash
git clone https://github.com/giancarmine-sparso/mech-lab-tools
cd mech-lab-tools
```

Crea il virtualenv e installa il package con le dipendenze di sviluppo:

```bash
make setup
```

Se vuoi attivare l'ambiente manualmente:

```bash
source .venv/bin/activate
```

## Esempio minimo

```python
import numpy as np

from mech_lab_tools import lin_fit, load_csv, weighted_mean

df = load_csv("data/reference/test_misure.csv", sep=",", decimal=".")

x = df["Valore1"].to_numpy(dtype=float)
sigma = np.full_like(x, 0.2)

x_bar = weighted_mean(x, 1 / sigma**2)

fit = lin_fit(
    x=np.arange(1, len(x) + 1, dtype=float),
    y=x,
    sigma_y=sigma,
    xlabel="indice",
    ylabel="Valore1",
    plot=False,
)

print("media pesata:", x_bar)
print("pendenza:", fit["m"])
```

## Documentazione

La documentazione del package e' in `docs/main.pdf`.

Per ricompilarla:

```bash
make docs
```

Le sezioni attualmente documentate sono:

- `io_utils`
- `stats_utils`
- `plot_utils`
- `fit_utils`

## Comandi utili

| Target | Descrizione |
| --- | --- |
| `make setup` | Crea il virtualenv e installa il package in editable mode con dipendenze `dev` |
| `make venv` | Crea solo il virtualenv |
| `make install` | Installa il package locale e le dipendenze |
| `make check-tex` | Verifica i prerequisiti LaTeX |
| `make docs` | Compila la documentazione PDF |
| `make docs-clean` | Rimuove i file temporanei LaTeX |
| `make clean` | Esegue la pulizia generale |

## Note

- I notebook in `notebooks/` sono esempi di utilizzo e test esplorativi, non documentazione API stabile.
