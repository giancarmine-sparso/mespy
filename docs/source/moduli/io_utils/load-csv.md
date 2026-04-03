# load_csv

## Firma

```python
load_csv(
    path: str | Path,
    *,
    sep: str = ",",
    decimal: str = ".",
    rename_columns: Mapping[str, str] | None = None,
    required_columns: Collection[str] | None = None,
    missing: Literal["error", "drop", "allow"] = "error",
    comment: str | None = None,
    skip_initial_space: bool = True,
) -> pd.DataFrame
```

`load_csv` carica un file CSV in un `DataFrame` pandas con controlli espliciti su rinomina colonne, colonne richieste e valori mancanti.

Questa pagina fa da hub rapido della funzione. I dettagli di utilizzo stanno in [Panoramica](load-csv/panoramica.md), mentre [Funzionamento](load-csv/funzionamento.md) resta disponibile come sottopagina dedicata.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <load-csv/panoramica>
Funzionamento <load-csv/funzionamento>
```
