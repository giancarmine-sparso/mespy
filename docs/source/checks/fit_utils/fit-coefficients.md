# _fit_coefficients

## Firma

```python
_fit_coefficients(
    x: FloatVector,
    y: FloatVector,
    weights: FloatVector,
) -> tuple[float, float, float]
```

## Che problema risolve

Calcola un singolo aggiornamento dei coefficienti del fit lineare pesato: pendenza, intercetta e varianza pesata di `x`.

## Contratto sugli input

- `x`, `y` e `weights` devono essere gia validati dal chiamante.
- `weights` deve contenere pesi strettamente positivi.
- `x` deve avere varianza pesata finita e non nulla.

## Dove viene usata

- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) per il calcolo iniziale dei coefficienti
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) a ogni iterazione quando `sigma_x` e presente

## Come fallisce

- `ValueError` se la varianza pesata di `x` non e finita
- `ValueError` se la varianza pesata di `x` e troppo vicina a zero, cioe se non ci sono abbastanza valori distinti per stimare la pendenza

## Perche resta privata

E un mattone interno dell'algoritmo di `lin_fit`. Documentarlo chiarisce il flusso del calcolo, ma non avrebbe molto senso come endpoint pubblico separato.
