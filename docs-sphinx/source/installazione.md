# Installazione

`mespy` richiede Python `3.12` o superiore. I comandi seguenti assumono che tu sia gia nella directory del progetto e che il virtualenv locale sia `.venv`, in coerenza con i target `make` del repository.

## Con uv

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Con pip

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Da jupyter-notebook

Eseguire in una cella di codice 
 
```bash
%pip install mespy 
```

successivamente eliminare la cella.

## Su Colab

Eseguire in una cella di codice:

```bash
!pip install mespy
```

successivamente eliminare la cella.

## Verifica rapida

Dopo l'installazione puoi controllare che l'import funzioni con un test minimo.

```bash
python -c "from mespy import load_csv, weighted_mean; print('mespy ok')"
```

Se vuoi solo il package locale senza tool di sviluppo, sostituisci `".[dev]"` con `.`. In quel caso non sono garantiti i target `make test` e `make docs`, perche richiedono le dipendenze di sviluppo.


## Cosa viene installato

- dipendenze runtime: `numpy`, `pandas`, `matplotlib`
- tool di sviluppo: `pytest`, `sphinx`, `pydata-sphinx-theme`, `myst-parser`, `build`, `twine`
- package locale in editable mode quando usi `-e`

## Passo successivo

Dopo l'installazione puoi continuare con la [Guida rapida](getting-started.md) oppure aprire gli [Esempi](examples/index.md).
