# variance

## Firma

```python
variance(
    x: ArrayLike,
    w: ArrayLike | None = None,
    ddof: int | float = 0,
) -> float
```

`variance` calcola la varianza di un campione nel caso non pesato o, in alternativa, nel caso pesato con denominatore corretto da `ddof`.

[Panoramica](variance/panoramica.md) riassume scopo, parametri, errori ed esempio d'uso; [Funzionamento](variance/funzionamento.md) descrive passo per passo il flusso interno e le formule implementate.

```{toctree}
:hidden:
:maxdepth: 1

Panoramica <variance/panoramica>
Funzionamento <variance/funzionamento>
```
