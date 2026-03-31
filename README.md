# mespy

Toolbox Python per l'analisi dei dati di laboratorio di meccanica.

`mespy` raccoglie in un unico package le utility che tornano spesso nei notebook di laboratorio: caricamento CSV, statistiche descrittive e pesate, istogrammi e fit lineare con incertezze.

La release `1.0.0` congela una public API piccola, tipizzata e pensata per un uso didattico: errori espliciti, firme stabili e output facili da leggere in notebook e script.

## API pubblica stabile

Il package espone direttamente:

- `load_csv`
- `median`
- `weighted_mean`
- `variance`
- `covariance`
- `standard_deviation`
- `histogram`
- `lin_fit`

I moduli presenti in `src/mespy` sono:

- `io_utils.py`: lettura CSV con policy esplicita per i valori mancanti
- `stats_utils.py`: funzioni statistiche di base con validazione coerente degli input
- `plot_utils.py`: istogrammi con media e banda `±1σ`
- `fit_utils.py`: fit lineare pesato con risultato tipizzato `LinearFitResult`

Il namespace root resta volutamente piccolo. I tipi pubblici aggiuntivi vivono nei submodule, per esempio `mespy.fit_utils.LinearFitResult`.

## Stabilita` API

- Le firme e il significato delle funzioni esportate da `mespy` seguono semantic versioning.
- Gli input non validi falliscono con `ValueError` invece di propagare `nan` o warning silenziosi.
- Il package distribuisce `py.typed`, quindi IDE e type checker vedono le firme pubbliche reali.

## Esempio minimo

```python
from mespy import lin_fit, load_csv, weighted_mean

df = load_csv(
    "data/reference/test_misure.csv",
    sep=",",
    decimal=".",
    missing="error",
)

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
    show_plot=False,
)

print("media pesata:", y_bar)
print("pendenza:", fit.slope)
print("chi2 ridotto:", fit.reduced_chi2)
```

## Breaking change di `1.0.0`

- `lin_fit(...)` non restituisce piu` un `dict`: ora restituisce `LinearFitResult` con campi descrittivi come `slope`, `intercept`, `chi2`, `reduced_chi2` e `figure`.
- `load_csv(...)` usa `missing="error" | "drop" | "allow"` al posto di `drop_missing`.
- `histogram(...)` usa `ddof=0` di default, in coerenza con `variance` e `standard_deviation`.
- Le funzioni statistiche rifiutano input vuoti, non finiti o con pesi non validi invece di restituire `nan`.

## Struttura del progetto

```text
mespy/
├── src/mespy/            # package Python
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
git clone https://github.com/giancarmine-sparso/mespy
cd mespy
```

Crea il virtualenv e installa il package con le dipendenze di sviluppo:

```bash
make setup
```

Se vuoi attivare l'ambiente manualmente:

```bash
source .venv/bin/activate
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

Le sezioni documentate sono:

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
| `make dist` | Rigenera da zero `sdist` e `wheel` in `dist/` |
| `make twine-check` | Valida solo gli artifact della versione corrente |
| `make upload` | Carica su PyPI solo gli artifact della versione corrente |
| `make release-check` | Esegue il gate completo pre-release per PyPI |
| `make check-tex` | Verifica i prerequisiti LaTeX e, se possibile, i font richiesti |
| `make docs` | Compila la documentazione PDF |
| `make docs-clean` | Rimuove i file temporanei LaTeX |
| `make dist-clean` | Rimuove gli artifact Python di build |
| `make clean` | Esegue la pulizia generale |

## Note

- I notebook in `notebooks/` sono esempi di utilizzo e test esplorativi, non documentazione API normativa.
