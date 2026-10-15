# fit_utils.py

`fit_utils.py` implementa la funzione di fit lineare di MesPy e il suo oggetto risultato immutabile.

## Interfaccia pubblica

- [`lin_fit`](lin-fit.md): minimi quadrati ordinari (OLS), minimi quadrati pesati (WLS) con incertezze assolute e propagazione facoltativa delle incertezze orizzontali selezionata esplicitamente tramite `x_error_method`.
- [`LinearFitResult`](linear-fit-result.md): parametri stimati, incertezze, residui in unità fisiche, informazioni diagnostiche, previsioni ed esportazione TOML.
- `XErrorMethod`: l'alias di tipo `Literal["none", "iterate"]` per il trattamento delle incertezze orizzontali.

## Implementazione

Il modulo valida vettori reali finiti in ingresso, incertezze verticali positive e incertezze orizzontali facoltative non negative. Le coordinate centrate e riscalate preservano l'accuratezza numerica del fit e delle previsioni. L'iterazione facoltativa della varianza efficace ha impostazioni di convergenza fisse; `fit_method`, `tol` e `max_iter` non sono più argomenti pubblici in ingresso.

La creazione dei grafici usa il [contesto di stile](../../checks/plot_utils/style-context.md) condiviso, con `"mespy"` come stile predefinito. L'esportazione scrive file TOML e, quando la creazione dei grafici è attiva, PDF a partire da un percorso base senza estensione. Il [riferimento della funzione](lin-fit.md) descrive in dettaglio validazione, iterazione, grafici ed esportazione.

```{toctree}
:hidden:
:maxdepth: 2

lin-fit
linear-fit-result
```
