# LinearFitResult

L'oggetto risultato immutabile restituito da [`lin_fit`](lin-fit.md). I suoi campi numerici descrivono un singolo fit; la figura Matplotlib facoltativa può comunque essere modificata e salvata.

## Attributi pubblici

| Attributo | Significato |
| --- | --- |
| `slope`, `intercept` | Pendenza e intercetta stimate dal fit. |
| `slope_std`, `intercept_std` | Le loro incertezze tipo. |
| `covariance` | Covarianza tra pendenza e intercetta. |
| `correlation` | Correlazione dei parametri, oppure `None` quando non definita. |
| `residuals` | Residui in unità fisiche di sola lettura, `y - (slope*x + intercept)`. |
| `residual_std` | Radice quadrata della somma dei quadrati dei residui divisa per `dof`, oppure `None` se `dof=0`. |
| `estimated_sigma` | Dispersione verticale comune stimata nei minimi quadrati ordinari (OLS); uguale a `residual_std` in OLS e a `None` nei minimi quadrati pesati (WLS). |
| `chi2` | Criterio pesato dei residui, oppure `None` in OLS. WLS iterativo usa le varianze efficaci. |
| `reduced_chi2` | `chi2 / dof`, oppure `None` quando non definito. |
| `p_value` | Probabilità nella coda superiore del chi quadro, oppure `None` in OLS o con zero gradi di libertà. Approssimata in WLS iterativo. |
| `dof` | Numero di osservazioni meno due. |
| `fit_method` | `"ols"` o `"wls"`. |
| `x_error_method` | `"none"` o `"iterate"`: il trattamento delle incertezze orizzontali scelto in `lin_fit`. |
| `figure` | Figura Matplotlib, oppure `None` quando `plot=False`. |

Per `x_error_method="iterate"`, la covarianza dei parametri, la banda e l'interpretazione del chi quadro e del valore p appartengono all'approssimazione storica della varianza efficace. Non sono risultati York/ODR validati. `fit_method` rimane `"wls"` e `estimated_sigma` rimane `None`.

`normalize_residuals` modifica soltanto il grafico; `residuals` conserva sempre le unità di `y`. Le modifiche ai campi stimati tramite `dataclasses.replace()` vengono rifiutate quando sarebbero incoerenti con il fit conservato. Puoi modificare `result.figure` e salvarla separatamente; questo non aggiorna una precedente esportazione PDF automatica.

## Previsione

```python
result = lin_fit(x, y, sigma_y, plot=False)
predicted = result.predict([1.0, 2.0, 3.0])
```

`predict()` accetta uno scalare reale finito o un vettore monodimensionale. Usa la rappresentazione locale conservata per preservare l'accuratezza in prossimità di grandi traslazioni delle coordinate.

## Esportazione TOML

```python
result.to_toml("fit_results.toml")
```

La directory di destinazione deve già esistere. Un'estensione mancante diventa `.toml`; una destinazione esistente viene sostituita atomicamente. Il metodo restituisce il `Path` del file scritto.

Il documento contiene le tabelle `[mespy]`, `[data]`, `[fit]`, `[diagnostics]`, `[residuals]` e `[plot]`. Le incertezze in ingresso vengono conservate nella loro forma originale dopo l'espansione degli scalari e i risultati in virgola mobile mantengono la piena precisione. Le informazioni diagnostiche non definite vengono omesse. Le modifiche alla figura e la configurazione Matplotlib completa non vengono serializzate.

Senza `sigma_x`, le esportazioni mantengono lo schema 2. Con `sigma_x`, lo schema 3 memorizza anche `[data].sigma_x` e `[fit].x_error_method`, compreso `"none"` quando sono state soltanto visualizzate barre orizzontali.
