# io_utils.py

`io_utils.py` si occupa del caricamento dei file CSV e concentra in un solo punto le scelte di validazione legate a colonne mancanti, rinomina dei campi e gestione dei valori `NaN`.

## Import principali

- Standard library:
  `collections.abc.Collection`, `collections.abc.Mapping`, `pathlib.Path`, `typing.Literal`
- Librerie esterne:
  `pandas as pd`
- Tipi definiti nel modulo:
  `MissingPolicy = Literal["error", "drop", "allow"]`

## Cosa espone

- [`load_csv`](load-csv.md): wrapper di `pandas.read_csv` con un contratto piu piccolo e prevedibile.

## Responsabilita del modulo

- leggere un file CSV da percorso stringa o `Path`
- supportare separatori e separatori decimali configurabili
- rinominare le colonne subito dopo il caricamento
- verificare eventuali colonne obbligatorie
- scegliere in modo esplicito la policy sui valori mancanti

## Relazioni con il resto del package

`io_utils.py` e il punto di ingresso per trasformare dati su disco in un `DataFrame` da passare poi alle funzioni di [`stats_utils`](../stats_utils/index.md), [`plot_utils`](../plot_utils/index.md) e [`fit_utils`](../fit_utils/index.md).

## Pagina di dettaglio

- [`load_csv`](load-csv.md)

```{toctree}
:hidden:
:maxdepth: 2

load-csv
```
