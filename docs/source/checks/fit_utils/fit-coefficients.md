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
- `x` deve contenere almeno due valori distinti.

## Dove viene usata

- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) per il calcolo iniziale dei coefficienti
- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md) a ogni iterazione quando `sigma_x` e presente

## Come fallisce

- `ValueError` se tutti i valori di `x` sono uguali: la pendenza non e identificabile. Il controllo e esatto e non dipende dall'unita di misura di `x`
- `ValueError` se la varianza pesata di `x` non e rappresentabile in `float64`, cioe se il calcolo va in underflow o overflow perche i valori di `x` sono estremamente piccoli o grandi in modulo

## Perche resta privata

E un mattone interno dell'algoritmo di `lin_fit`. Documentarlo chiarisce il flusso del calcolo, ma non avrebbe molto senso come endpoint pubblico separato.
