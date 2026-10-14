# Installazione per lo sviluppo

Per installare MesPy e usarlo nelle tue analisi segui [Inizia qui](getting-started.md): trovi i comandi per uv, Google Colab, Jupyter e pip.

Questa pagina serve a chi vuole modificare MesPy o contribuire al progetto. MesPy richiede Python `3.12` o superiore. I comandi seguenti assumono che tu sia nella directory del repository e che il virtualenv locale sia `.venv`, in coerenza con i target `make` del repository.

## Con make

```bash
git clone https://github.com/giancarmine-sparso/mespy
cd mespy
make setup
```

`make setup` crea `.venv` e installa il pacchetto in modalità modificabile con le dipendenze di sviluppo.

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

## Cosa viene installato

- dipendenze per l'esecuzione: `numpy`, `pandas`, `matplotlib`, `scipy`, `tomli-w`
- strumenti di sviluppo: `pytest`, `sphinx`, `pydata-sphinx-theme`, `myst-nb`, `sphinx-intl`, `build`, `twine`
- il pacchetto locale in modalità modificabile, grazie a `-e`

Dopo l'installazione puoi lanciare i test con `make test` e costruire la documentazione con `make docs`.
