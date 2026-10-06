# _validate_fit_method

## Firma

```python
_validate_fit_method(fit_method: str) -> FitMethod
```

## Che problema risolve

Valida il modello di incertezza richiesto da `lin_fit` e restringe il tipo di ritorno al literal interno `FitMethod`.

## Contratto sugli input

- `fit_method="absolute"` usa le incertezze assolute fornite dall'utente.
- `fit_method="residual"` stima dai residui un fattore globale di scala.
- Qualunque altro valore viene rifiutato.

## Dove viene usata

- in [`lin_fit`](../../moduli/fit_utils/lin-fit.md), prima di scegliere il ramo di calcolo

## Come fallisce

- `ValueError` se il valore non e `"absolute"` oppure `"residual"`

## Perche resta privata

Formalizza una scelta interna gia esposta dal parametro pubblico `fit_method`, senza introdurre un secondo punto di ingresso nell'API.
