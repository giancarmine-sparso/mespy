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
- `residuals`: vettore dei residui fisici `y - (m x + c)`, sempre non normalizzati anche quando `lin_fit(..., normalize_residuals=True)` mostra residui normalizzati nel grafico.
- `residual_std`: stima sintetica della dispersione dei residui.
- `chi2`: chi quadrato del fit.
- `reduced_chi2`: chi quadrato ridotto.
- `p_value`: probabilita di ottenere un chi quadrato maggiore o uguale a quello osservato, se il modello e le incertezze sono corretti; vale `nan` con `fit_method="residual"`.
- `dof`: gradi di liberta, pari a `n - 2`.
- `iterations`: numero di aggiornamenti dei pesi effettuati.
- `converged`: indica se l'iterazione con `sigma_x` ha soddisfatto il criterio di arresto.
- `figure`: oggetto matplotlib oppure `None` se `show_plot=False`.
- `fit_method`: modello di incertezza usato, `"absolute"` oppure `"residual"`.
- `scale_factor`: fattore globale applicato alle incertezze con `fit_method="residual"`; vale `1.0` con `fit_method="absolute"`.

## Quando leggerlo

Usa questo oggetto quando vuoi:

- recuperare i parametri del fit senza dover parsare una stringa o una legenda
- controllare la qualita del fit tramite residui, `reduced_chi2` e `p_value`
- decidere se salvare o riusare la figura generata

## Esempio

```python
result = lin_fit(x, y, sigma_y, show_plot=False)

print(result.slope)
print(result.intercept_std)
print(result.reduced_chi2)
print(result.p_value)
print(result.fit_method)
```

## Esportazione in TOML

Il metodo `to_toml(path)` salva il risultato numerico del fit in un file TOML leggibile e versionabile:

```python
fit = mespy.lin_fit(x, y, sigma_y)
fit.to_toml("fit_molla.toml")
```

Il file contiene quattro tabelle:

- `[mespy]`: `schema_version`, `mespy_version` e `result_type = "linear_fit"`, per riconoscere il formato del file.
- `[fit]`: `fit_method`, `slope`, `slope_std`, `intercept`, `intercept_std`, `covariance`, `correlation` e `scale_factor`.
- `[diagnostics]`: `chi2`, `reduced_chi2`, `dof`, `p_value`, `residual_std`, `iterations` e `converged`.
- `[residuals]`: il vettore `values` con i residui fisici.

Il campo `figure` non viene mai salvato: per conservare il grafico usa il parametro `save_path` di [`lin_fit`](lin-fit.md).

Se `path` non ha estensione viene aggiunto `.toml`. Un file esistente viene sovrascritto in modo atomico, quindi non resta mai un file a meta. Il metodo restituisce il `Path` del file scritto. I valori vengono salvati con precisione completa: rileggendo il file con `tomllib` si ottengono esattamente gli stessi numeri.

## Note

La classe non esegue calcoli da sola: e una rappresentazione dell'output prodotto da [`lin_fit`](lin-fit.md). Il parametro `normalize_residuals` di `lin_fit` non aggiunge campi e non cambia i valori numerici contenuti in questa classe; agisce solo sul pannello dei residui della figura. Il campo `scale_factor` e invece parte del calcolo: con `fit_method="residual"` descrive la scala di incertezza stimata dai residui.
