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

[Panoramica](load-csv/panoramica.md) riassume scopo, parametri, errori ed esempio d'uso; [Funzionamento](load-csv/funzionamento.md) descrive passo per passo il flusso interno e le formule implementate.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <load-csv/panoramica>
Funzionamento <load-csv/funzionamento>
```
