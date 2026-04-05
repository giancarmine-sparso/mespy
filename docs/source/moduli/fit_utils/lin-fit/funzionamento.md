# Funzionamento

Questa pagina descrive il flusso interno di `lin_fit` e l'ordine con cui vengono applicate validazioni, stima dei coefficienti, eventuale aggiornamento iterativo dei pesi, diagnostiche e plotting. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere la lista dei parametri, ma mostrare come la funzione costruisce davvero il fit lineare pesato.

I frammenti seguenti sono estratti dal codice attuale di `src/mespy/fit_utils.py`. Le formule di base riprendono e adattano la formulazione teorica gia presente nella documentazione legacy `fit_utils.tex`; il criterio di arresto, le diagnostiche restituite e la banda del grafico sono invece spiegati a partire dall'implementazione attuale. Gli helper privati vengono citati solo per chiarire il flusso; i dettagli completi sono documentati in [`_as_float_vector`](../../../checks/stats_utils/as-float-vector.md), [`_fit_coefficients`](../../../checks/fit_utils/fit-coefficients.md), [`_validate_axis_limits`](../../../checks/plot_utils/validate-axis-limits.md), [`_validate_decimals`](../../../checks/plot_utils/validate-decimals.md), [`_validate_figsize`](../../../checks/plot_utils/validate-figsize.md) e [`_style_context`](../../../checks/plot_utils/style-context.md). Quando servono i simboli $\bar{x}_w$, $\mathrm{Var}_w$ e $\mathrm{Cov}_w$, il riferimento pratico sono le funzioni pubbliche [`weighted_mean`](../../stats_utils/weighted-mean.md), [`variance`](../../stats_utils/variance.md) e [`covariance`](../../stats_utils/covariance.md).

## Sequenza di esecuzione

L'implementazione segue questa sequenza:

1. Converte `x`, `y` e `sigma_y` in vettori `float64` monodimensionali e finiti.
2. Verifica che `x`, `y` e `sigma_y` abbiano la stessa lunghezza e che i punti siano almeno 3.
3. Valida `decimals` come intero non negativo e leggibile.
4. Valida `tol` come scalare positivo e `max_iter` come intero positivo.
5. Se `sigma_x` e presente, lo valida come vettore strettamente positivo con la stessa forma di `x`.
6. Costruisce i pesi iniziali $w_i = 1 / \sigma_{y_i}^2$.
7. Stima una prima retta con `_fit_coefficients(...)`.
8. Se `sigma_x` e presente, aggiorna iterativamente i pesi usando la varianza efficace $\sigma_{\mathrm{eff},i}^2 = \sigma_{y_i}^2 + m^2 \sigma_{x_i}^2$ finche la variazione relativa della pendenza scende sotto `tol`.
9. Calcola varianze dei parametri, covarianza, correlazione, residui, `chi2`, `reduced_chi2` e altre diagnostiche.
10. Se `show_plot=True`, entra in `_style_context(style)` e costruisce una figura a due pannelli con dati, retta e residui.
11. Restituisce un [`LinearFitResult`](../linear-fit-result.md) con tutti i risultati numerici e la figura opzionale.

## Validazione input e setup numerico

```python
x_values = _as_float_vector("x", x)
y_values = _as_float_vector("y", y)
sigma_y_values = _validate_positive_vector("sigma_y", sigma_y)

if x_values.shape != y_values.shape or x_values.shape != sigma_y_values.shape:
    raise ValueError("x, y e sigma_y devono avere la stessa lunghezza")

n = x_values.size
if n < 3:
    raise ValueError("Servono almeno 3 punti per effettuare un fit lineare")

decimals = _validate_decimals(decimals)

tol_value = _validate_positive_scalar("tol", tol)
max_iter_value = _validate_max_iter(max_iter)

use_sigma_x = sigma_x is not None
sigma_x_values: FloatVector | None = None
if use_sigma_x:
    sigma_x_values = _validate_positive_vector(
        "sigma_x",
        sigma_x,
        expected_shape=x_values.shape,
    )

sigma_y2 = sigma_y_values**2
sigma_x2 = sigma_x_values**2 if sigma_x_values is not None else None
weights = 1.0 / sigma_y2
```

Questo primo blocco definisce il contratto numerico del fit.

- `x`, `y` e `sigma_y` non vengono usati direttamente: prima passano attraverso validatori che impongono array numerici, monodimensionali e finiti.
- `sigma_y` e, se presente, `sigma_x` devono essere strettamente positivi. Questo e essenziale per poter costruire pesi fisicamente e numericamente sensati.
- La funzione rifiuta dataset con meno di 3 punti, perche il fit lineare restituisce due parametri e poi usa `dof = n - 2` nelle diagnostiche.
- `decimals` viene validato anche quando `show_plot=False`, perche fa parte del contratto generale della funzione e della formattazione della legenda quando il grafico e attivo.
- I pesi iniziali del caso base sono

$$
w_i = \frac{1}{\sigma_{y_i}^2}.
$$

Questa e la formulazione standard del fit lineare pesato quando le incertezze sono solo sulle ordinate.

- Le quantita pesate che compaiono piu avanti si appoggiano alle funzioni statistiche del package:

$$
\bar{x}_w = \frac{\sum_i w_i x_i}{\sum_i w_i},
\qquad
\bar{y}_w = \frac{\sum_i w_i y_i}{\sum_i w_i}.
$$

- Nel codice queste medie non vengono riscritte a mano: vengono delegate a [`weighted_mean`](../../stats_utils/weighted-mean.md). Lo stesso vale per varianza e covarianza pesata, che vengono delegate a [`variance`](../../stats_utils/variance.md) e [`covariance`](../../stats_utils/covariance.md).

## Stima dei coefficienti e ramo iterativo

```python
slope, intercept, var_x = _fit_coefficients(x_values, y_values, weights)
iterations = 0
converged = not use_sigma_x

if use_sigma_x:
    previous_slope = slope

    for _ in range(max_iter_value):
        sigma_eff2 = sigma_y2 + slope**2 * sigma_x2
        weights = 1.0 / sigma_eff2
        iterations += 1

        next_slope, next_intercept, next_var_x = _fit_coefficients(
            x_values,
            y_values,
            weights,
        )

        rel_change = abs(next_slope - previous_slope) / max(
            abs(next_slope),
            1e-300,
        )
        if rel_change < tol_value:
            slope = next_slope
            intercept = next_intercept
            var_x = next_var_x
            converged = True
            break

        previous_slope = next_slope
        slope = next_slope
        intercept = next_intercept
        var_x = next_var_x
    else:
        raise RuntimeError(
            f"Il fit lineare non converge entro max_iter={max_iter_value}"
        )
```

Qui avviene la stima vera e propria della retta.

Nel caso base, `_fit_coefficients(...)` usa varianza e covarianza pesata di `x` e `y` per stimare

$$
\hat{m} = \frac{\mathrm{Cov}_w(x,y)}{\mathrm{Var}_w(x)},
\qquad
\hat{c} = \bar{y}_w - \hat{m}\,\bar{x}_w.
$$

La quantita `var_x` restituita dall'helper coincide con $\mathrm{Var}_w(x)$ e viene riusata anche nel calcolo delle incertezze sui parametri.

- Se `x` non ha abbastanza variabilita, `_fit_coefficients(...)` fallisce. In pratica il codice richiede che la varianza pesata di `x` sia finita e non troppo vicina a zero.
- Se `sigma_x is None`, il fit si ferma qui: `iterations = 0` e `converged = True`.

Quando invece sono presenti incertezze anche su `x`, la funzione passa a un algoritmo iterativo.

- La varianza efficace di ogni punto diventa

$$
\sigma_{\mathrm{eff},i}^2 = \sigma_{y_i}^2 + m^2 \sigma_{x_i}^2.
$$

- Questa formula ha una motivazione teorica precisa: nel modello lineare $y = mx + c$, un'incertezza orizzontale $\sigma_{x_i}$ puo essere propagata lungo l'asse verticale con la regola lineare

$$
\sigma_{y,\mathrm{da}\,x,i}^2 \approx
\left(\frac{\partial y}{\partial x}\right)^2 \sigma_{x_i}^2
= m^2 \sigma_{x_i}^2.
$$

- In altre parole, `lin_fit` usa l'idea della varianza efficace: tratta l'errore su `x` come un contributo aggiuntivo all'errore su `y`, ottenendo una singola varianza verticale per punto.
- Questo porta naturalmente alla quantita che il fit cerca di rendere il piu piccola possibile:

$$
\chi^2_{\mathrm{eff}}(m,c) =
\sum_i
\frac{\left[y_i - (m x_i + c)\right]^2}
{\sigma_{y_i}^2 + m^2 \sigma_{x_i}^2}.
$$

- Qui si vede perche serve iterare: nel denominatore compare la pendenza `m`. Quindi i pesi dipendono proprio dalla quantita che stiamo cercando di stimare.
- Per questo il metodo non puo chiudersi in un solo passaggio come nel caso con sole incertezze su `y`. La funzione procede invece per passi successivi:

$$
m^{(k)}
\;\longrightarrow\;
w_i^{(k)} = \frac{1}{\sigma_{y_i}^2 + \left(m^{(k)}\right)^2 \sigma_{x_i}^2}
\;\longrightarrow\;
\left(m^{(k+1)}, c^{(k+1)}\right).
$$

- In pratica il procedimento e questo: si parte da una prima stima di `m`, si calcolano i pesi con quella stima, si ricalcola la retta con i nuovi pesi e si ripete finche il risultato cambia pochissimo.
- La funzione non usa un metodo geometrico completo che minimizza direttamente tutte le distanze nel piano. Fa una scelta piu semplice: trasforma l'effetto di `sigma_x` in un contributo aggiuntivo all'incertezza verticale su `y`. E proprio questa idea che porta alla formula della varianza efficace usata nel codice.

- I nuovi pesi sono quindi

$$
w_i = \frac{1}{\sigma_{\mathrm{eff},i}^2}.
$$

- A ogni iterazione il codice ricalcola la retta con questi nuovi pesi e misura la variazione relativa della pendenza tramite

```python
rel_change = abs(next_slope - previous_slope) / max(abs(next_slope), 1e-300)
```

- Il criterio di arresto guarda la pendenza, non l'intercetta, perche nella formula dei pesi compare solo `m`. Se `m` smette quasi di cambiare, allora smettono quasi di cambiare anche $\sigma_{\mathrm{eff},i}^2$ e quindi i pesi.
- L'intercetta non entra nella varianza efficace. Quando i pesi sono ormai quasi stabili, anche `c` e `var_x` si assestano di conseguenza.
- La scelta di usare una variazione relativa, invece di una assoluta, serve a non legare il test alle unita di misura. Per esempio, una stessa differenza numerica su `m` puo sembrare grande o piccola a seconda di come sono misurati `x` e `y`.
- Il denominatore usa `max(abs(next_slope), 1e-300)` per evitare una divisione per zero quando la pendenza stimata e molto piccola o nulla.
- Il valore `1e-300` non ha un significato fisico o statistico: e solo una protezione numerica molto piccola per evitare problemi quando `next_slope` e vicino a zero.
- La convergenza e dichiarata quando `rel_change < tol_value`.
- Anche `tol` va letto come parametro numerico, non come una costante teorica universale. Nel repository non compare una derivazione speciale del valore di default: la scelta pratica e usare una soglia relativa molto piccola (`1e-10`) per fermarsi quando la pendenza, e quindi anche i pesi, stanno ormai cambiando in modo trascurabile.
- In modo molto concreto, `tol` risponde a questa domanda: "quanto deve essere piccolo l'ultimo cambiamento della pendenza per poter dire che il procedimento si e assestato?" Non misura quanto il fit sia "buono" dal punto di vista fisico e non va letta come una soglia su `chi2`.
- Ridurre `tol` significa chiedere un assestamento ancora piu stretto e quindi, spesso, piu iterazioni. Aumentare `tol` significa fermarsi prima, accettando una stabilita finale un po meno rigorosa.
- `iterations` conta quanti aggiornamenti dei pesi sono stati effettuati davvero.
- `converged` indica se il criterio di arresto e stato soddisfatto prima di esaurire `max_iter`.
- `max_iter` completa il criterio di stop come limite di sicurezza: non decide da solo la convergenza, ma impedisce che un caso difficile o molto lento lasci il ciclo aperto troppo a lungo.
- Se il ciclo termina senza convergere, la funzione alza `RuntimeError` invece di restituire un risultato parziale.

## Diagnostiche del fit

```python
sum_w = float(np.sum(weights))
var_m = 1.0 / (var_x * sum_w)
var_c = weighted_mean(x_values**2, weights) / (var_x * sum_w)
cov_mc = -weighted_mean(x_values, weights) / (var_x * sum_w)

sigma_m = float(np.sqrt(var_m))
sigma_c = float(np.sqrt(var_c))
rho_mc = float(cov_mc / (sigma_m * sigma_c))

residuals = y_values - slope * x_values - intercept
dof = n - 2
residual_std = float(np.sqrt(np.sum(residuals**2) / dof))

sigma_fit2 = sigma_y2 if sigma_x2 is None else sigma_y2 + slope**2 * sigma_x2
chi2 = float(np.sum((residuals**2) / sigma_fit2))
reduced_chi2 = float(chi2 / dof)
```

Dopo aver fissato i pesi finali, `lin_fit` costruisce le principali grandezze diagnostiche del modello.

Se chiamiamo

$$
S_w = \sum_i w_i,
$$

allora il codice usa le formule

$$
\mathrm{Var}(m) = \frac{1}{\mathrm{Var}_w(x)\,S_w},
$$

$$
\mathrm{Var}(c) = \frac{\overline{x^2}_w}{\mathrm{Var}_w(x)\,S_w},
$$

$$
\mathrm{Cov}(m,c) = -\frac{\bar{x}_w}{\mathrm{Var}_w(x)\,S_w}.
$$

Da qui seguono direttamente

$$
\sigma_m = \sqrt{\mathrm{Var}(m)},
\qquad
\sigma_c = \sqrt{\mathrm{Var}(c)},
$$

e il coefficiente di correlazione tra pendenza e intercetta

$$
\rho_{mc} = \frac{\mathrm{Cov}(m,c)}{\sigma_m \sigma_c}.
$$

I residui sono definiti come

$$
r_i = y_i - (m x_i + c),
$$

e i gradi di liberta sono

$$
\mathrm{dof} = n - 2.
$$

La dispersione sintetica dei residui e calcolata come

$$
\mathrm{residual\_std} =
\sqrt{\frac{\sum_i r_i^2}{\mathrm{dof}}}.
$$

Per il chi quadrato, invece, il codice usa una varianza di fit che dipende dal ramo seguito:

$$
\sigma_{\mathrm{fit},i}^2 =
\begin{cases}
\sigma_{y_i}^2 & \text{se } \sigma_x \text{ non e presente} \\
\sigma_{y_i}^2 + m^2 \sigma_{x_i}^2 & \text{se } \sigma_x \text{ e presente}
\end{cases}
$$

e quindi

$$
\chi^2 = \sum_i \frac{r_i^2}{\sigma_{\mathrm{fit},i}^2},
\qquad
\chi^2_\nu = \frac{\chi^2}{\mathrm{dof}}.
$$

Alcune osservazioni pratiche aiutano a leggere questi numeri nel modo corretto.

- `residual_std` non pesa i residui con le incertezze sperimentali: misura solo la dispersione quadratica dei residui attorno alla retta.
- `chi2` e `reduced_chi2` invece confrontano i residui con le incertezze del modello, quindi hanno una lettura statistica diversa.
- Nel caso con `sigma_x`, sia i pesi finali sia `chi2` usano la stessa forma di varianza efficace.

## Grafico opzionale e oggetto di ritorno

```python
if save_path is not None and not show_plot:
    raise ValueError("save_path può essere usato solo se show_plot=True")

fig = None

if show_plot:
    with _style_context(style):
        if xlim is not None:
            xlim = _validate_axis_limits(...)
        if ylim is not None:
            ylim = _validate_axis_limits(...)

        subplots_kwargs = {
            "gridspec_kw": {"height_ratios": [3, 1]},
            "sharex": True,
            "constrained_layout": True,
        }
        if figsize is not None:
            subplots_kwargs["figsize"] = _validate_figsize(figsize)
        if dpi is not None:
            subplots_kwargs["dpi"] = dpi

        fig, (ax_fit, ax_res) = plt.subplots(2, 1, **subplots_kwargs)

        errorbar_kwargs = {
            "yerr": sigma_y_values,
            "xerr": sigma_x_values if use_sigma_x else None,
            "fmt": "o",
            "markersize": 4,
            "elinewidth": 1,
            "capsize": 3,
            "alpha": data_alpha,
        }
        if point_color is not None:
            errorbar_kwargs["color"] = point_color
            errorbar_kwargs["ecolor"] = point_color

        ax_fit.errorbar(x_values, y_values, **errorbar_kwargs)

        fmt = f".{decimals}f"
        x_fit = np.linspace(x_values.min(), x_values.max(), 200)
        y_fit = slope * x_fit + intercept
        fit_label = (
            f"Fit: m={slope:{fmt}}, c={intercept:{fmt}}"
            if show_fit_params
            else "Fit"
        )
        ax_fit.plot(x_fit, y_fit, color=fit_color, linewidth=1.5, label=fit_label)

        if show_band:
            x_bar = weighted_mean(x_values, weights)
            sigma_y_fit = np.sqrt(
                1.0 / sum_w + (x_fit - x_bar) ** 2 / (var_x * sum_w)
            )
            ax_fit.fill_between(
                x_fit,
                y_fit - sigma_y_fit,
                y_fit + sigma_y_fit,
                color=band_color,
                alpha=band_alpha,
                label=r"$\pm 1 \sigma$ retta",
            )

        ax_res.errorbar(x_values, residuals, **errorbar_kwargs)
        ax_res.axhline(0, color=fit_color, linewidth=1, linestyle="--")

        if not show_grid:
            ax_fit.grid(False)
            ax_res.grid(False)
        elif grid_alpha is not None:
            ax_fit.grid(True, axis="y", alpha=grid_alpha)
            ax_res.grid(True, axis="y", alpha=grid_alpha)

        if save_path is not None:
            savefig_kwargs = {"bbox_inches": "tight"}
            if dpi is not None:
                savefig_kwargs["dpi"] = dpi
            fig.savefig(save_path, **savefig_kwargs)

return LinearFitResult(
    slope=float(slope),
    intercept=float(intercept),
    slope_std=sigma_m,
    intercept_std=sigma_c,
    covariance=float(cov_mc),
    correlation=rho_mc,
    residuals=residuals,
    residual_std=residual_std,
    chi2=chi2,
    reduced_chi2=reduced_chi2,
    dof=dof,
    iterations=iterations,
    converged=converged,
    figure=fig,
)
```

L'ultima parte gestisce plotting e packaging finale del risultato.

- `save_path` puo essere usato solo se `show_plot=True`. La funzione controlla questa incompatibilita prima di entrare nel ramo Matplotlib.
- Se `show_plot=False`, tutta la parte grafica viene saltata e `figure` nel risultato finale vale `None`.
- Quando il grafico e attivo, `lin_fit` usa lo stesso [`_style_context`](../../../checks/plot_utils/style-context.md) di [`histogram`](../../plot_utils/histogram.md): `style=None` mantiene gli `rcParams` correnti, `style="mespy"` carica lo stile del package, qualunque altra stringa viene passata a Matplotlib.
- Quando il grafico e attivo, `lin_fit` crea sempre due pannelli verticali: in alto il fit, in basso i residui.
- `figsize` e `dpi` vengono passati a `plt.subplots(...)` solo quando sono stati specificati. In assenza di override, decide lo stile attivo.
- `point_color`, quando presente, viene applicato sia ai marker sia alle barre d'errore; `fit_color` viene usato per la retta e per la linea orizzontale dei residui; `band_color` controlla la fascia attorno alla retta.
- `xlim` viene applicato sia a `ax_fit` sia a `ax_res`, mentre `ylim` viene applicato solo al pannello superiore.
- `show_grid=False` spegne esplicitamente la griglia su entrambi i pannelli; `show_grid=True` con `grid_alpha is None` lascia la griglia allo stile attivo; `grid_alpha` esplicito applica una griglia sull'asse `y` di entrambi i pannelli.
- `decimals` e `show_fit_params` influiscono solo sulla stringa della legenda della retta, non sul calcolo numerico del fit.
- Il salvataggio usa sempre `bbox_inches="tight"`; il `dpi` viene passato a `savefig(...)` solo quando e esplicitato.

La retta visualizzata e

$$
y_{\mathrm{fit}}(x) = m x + c.
$$

Se `show_band=True`, il codice costruisce anche una banda attorno alla retta usando

$$
\bar{x}_w = \mathrm{weighted\_mean}(x, w),
$$

$$
\sigma_{\mathrm{line}}(x) =
\sqrt{
\frac{1}{S_w}
+
\frac{(x - \bar{x}_w)^2}{\mathrm{Var}_w(x)\,S_w}
}.
$$

Il grafico mostra quindi

$$
y_{\mathrm{fit}}(x) \pm \sigma_{\mathrm{line}}(x).
$$

Questa e la formula implementata oggi nel codice: non viene moltiplicata per `reduced_chi2` ne per altri fattori di scala aggiuntivi.

Il valore restituito non e una coppia `(fig, ax)` ma un [`LinearFitResult`](../linear-fit-result.md), cioe un contenitore immutabile che raccoglie parametri del fit, incertezze, diagnostiche, residui e figura opzionale.

## Interazioni importanti tra parametri

Alcune combinazioni di parametri definiscono il comportamento pratico piu importante della funzione.

- `sigma_x` attiva il ramo iterativo e rende rilevanti `tol` e `max_iter`.
- `tol` e una soglia di convergenza numerica sulla pendenza relativa, non una soglia statistica sulla qualita del fit.
- Se `sigma_x` non e presente, il fit usa solo i pesi `1 / sigma_y**2`, non itera e marca subito `converged=True`.
- `style=None` usa gli `rcParams` correnti, `style="mespy"` usa lo stile del package, qualunque altra stringa passa direttamente da Matplotlib.
- `point_color`, `title_fontsize`, `title_pad`, `legend_fontsize`, `legend_loc` e `grid_alpha` sovrascrivono lo stile solo quando non sono `None`.
- `show_plot=False` disattiva tutta la parte Matplotlib: in questo caso `figure=None` e `xlim` e `ylim` non vengono nemmeno validati, ma `decimals`, `tol` e `max_iter` continuano a essere controllati.
- `save_path` non e un salvataggio indipendente dal plotting: e ammesso solo insieme a `show_plot=True`.
- `show_fit_params=True` cambia la label della retta da `"Fit"` a una stringa con `m` e `c` formattati con `decimals`.
- `show_band` controlla solo la banda attorno alla retta, non il calcolo del fit.
- `show_legend=False` lascia comunque disegnati punti, retta e banda, ma senza legenda.
- `xlim` agisce su entrambi i pannelli condivisi, mentre `ylim` limita solo il pannello superiore.

## Esempio commentato

```python
import numpy as np

from mespy import lin_fit

x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
y = np.array([2.2, 4.1, 5.8, 8.2, 9.9])
sigma_y = np.array([0.20, 0.20, 0.25, 0.25, 0.30])
sigma_x = np.array([0.05, 0.05, 0.05, 0.08, 0.08])

result = lin_fit(
    x,
    y,
    sigma_y,
    sigma_x=sigma_x,
    xlabel="tempo [s]",
    ylabel="spazio [m]",
    title="Fit lineare pesato",
    show_fit_params=True,
)

print(result.slope)
print(result.intercept)
print(result.reduced_chi2)
print(result.iterations, result.converged)
```

In questo esempio la presenza di `sigma_x` forza il ramo iterativo con varianza efficace. Il risultato finale resta un [`LinearFitResult`](../linear-fit-result.md): i campi `slope`, `intercept`, `reduced_chi2`, `iterations` e `converged` permettono di leggere subito sia l'esito numerico del fit sia il comportamento dell'algoritmo.
