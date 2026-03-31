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
- `histogram`
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
- `lualatex`, `latexmk` e `pygmentize` solo se vuoi ricompilare la documentazione
- font richiesti dalla build docs: `Libertinus Serif`, `Libertinus Math`, `Libertinus Sans`, `JetBrains Mono`, `Inter Display`

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

Questo installa anche gli strumenti usati per il check pre-release (`build` e `twine`).

Se vuoi attivare l'ambiente manualmente:

```bash
source .venv/bin/activate
```

## Esempio minimo

```python
from mech_lab_tools import lin_fit, load_csv, weighted_mean

df = load_csv("data/reference/test_misure.csv", sep=",", decimal=".")

x = df["misura_n"].to_numpy(dtype=float)
y = df["lunghezza_mm"].to_numpy(dtype=float)
sigma_y = df["sigma_mm"].to_numpy(dtype=float)

y_bar = weighted_mean(y, 1 / sigma_y**2)

fit = lin_fit(
    x=x,
    y=y,
    sigma_y=sigma_y,
    xlabel="numero misura",
    ylabel="lunghezza [mm]",
    plot=False,
)

print("media pesata:", y_bar)
print("pendenza:", fit["m"])
```

## Documentazione

La documentazione del package e' in `docs/main.pdf`.

Per ricompilarla:

```bash
make docs
```

Il target usa `minted`, quindi richiede anche `pygmentize` disponibile nel `PATH`.
Inoltre il sorgente LaTeX usa i font `Libertinus Serif`, `Libertinus Math`, `Libertinus Sans`, `JetBrains Mono` e `Inter Display`.
`make check-tex` verifica i comandi necessari e, se `fc-match` e' disponibile nel sistema, controlla anche la presenza di questi font.

Le sezioni attualmente documentate sono:

- `io_utils`
- `stats_utils`
- `plot_utils`
- `fit_utils`

## Check pre-release

Per eseguire il gate completo di release PyPI in locale:

```bash
make release-check
```

Il comando esegue test, `compileall`, `pip check`, build di `sdist` e `wheel`, validazione con `twine check` e smoke test degli import a partire dalla wheel generata.

## Comandi utili

| Target | Descrizione |
| --- | --- |
| `make setup` | Crea il virtualenv e installa il package in editable mode con dipendenze `dev` |
| `make venv` | Crea solo il virtualenv |
| `make install` | Installa il package locale e le dipendenze |
| `make test` | Esegue l'intera suite `pytest` |
| `make dist` | Genera `sdist` e `wheel` in `dist/` |
| `make twine-check` | Valida gli artifact generati con `twine check` |
| `make release-check` | Esegue il gate completo pre-release per PyPI |
| `make check-tex` | Verifica i prerequisiti LaTeX e, se possibile, i font richiesti |
| `make docs` | Compila la documentazione PDF |
| `make docs-clean` | Rimuove i file temporanei LaTeX |
| `make dist-clean` | Rimuove gli artifact Python di build |
| `make clean` | Esegue la pulizia generale |

## Note

- I notebook in `notebooks/` sono esempi di utilizzo e test esplorativi, non documentazione API stabile.
