# LinearFitResult

## Definizione

`LinearFitResult` e una `dataclass` immutabile con `slots=True`, usata come oggetto di ritorno di [`lin_fit`](lin-fit.md).

## Scopo

Raccogliere in un unico contenitore tipizzato i parametri del fit, le incertezze associate, i residui, le diagnostiche e la figura opzionale.

## Campi

- `slope`: pendenza della retta stimata.
- `intercept`: intercetta della retta stimata.
- `slope_std`: incertezza standard sulla pendenza.
- `intercept_std`: incertezza standard sull'intercetta.
- `covariance`: covarianza tra i due parametri del fit.
- `correlation`: coefficiente di correlazione tra pendenza e intercetta.
- `residuals`: vettore dei residui `y - (m x + c)`.
- `residual_std`: stima sintetica della dispersione dei residui.
- `chi2`: chi quadrato del fit.
- `reduced_chi2`: chi quadrato ridotto.
- `dof`: gradi di liberta, pari a `n - 2`.
- `iterations`: numero di aggiornamenti dei pesi effettuati.
- `converged`: indica se l'iterazione con `sigma_x` ha soddisfatto il criterio di arresto.
- `figure`: oggetto matplotlib oppure `None` se `show_plot=False`.

## Quando leggerlo

Usa questo oggetto quando vuoi:

- recuperare i parametri del fit senza dover parsare una stringa o una legenda
- controllare la qualita del fit tramite residui e `reduced_chi2`
- decidere se salvare o riusare la figura generata

## Esempio

```python
result = lin_fit(x, y, sigma_y, show_plot=False)

print(result.slope)
print(result.intercept_std)
print(result.reduced_chi2)
```

## Note

La classe non esegue calcoli da sola: e una rappresentazione dell'output prodotto da [`lin_fit`](lin-fit.md).
