from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatVector = NDArray[np.float64]


def _as_float_vector(name: str, values: ArrayLike, *, allow_empty: bool = False) -> FloatVector:
    """Converte *values* in un array float64 monodimensionale e finito."""
    vector = np.asarray(values, dtype=float)

    if vector.ndim != 1:
        raise ValueError(f"{name} deve essere un array monodimensionale")

    if not allow_empty and vector.size == 0:
        raise ValueError(f"{name} deve contenere almeno un valore")

    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} deve contenere solo valori finiti")

    return vector


def _validate_weights(x: FloatVector, w: ArrayLike | None) -> FloatVector | None:
    """Valida un vettore di pesi positivo e compatibile con *x*."""
    if w is None:
        return None

    weights = _as_float_vector("w", w)
    if weights.shape != x.shape:
        raise ValueError(
            f"w deve avere la stessa forma di x | x.shape={x.shape}, w.shape={weights.shape}"
        )

    if np.any(weights <= 0):
        raise ValueError("w deve contenere solo valori strettamente positivi")

    w_sum = float(np.sum(weights))
    if not np.isfinite(w_sum) or w_sum <= 0:
        raise ValueError("la somma dei pesi deve essere strettamente positiva")

    return weights


def median(x: ArrayLike) -> float:
    """
    Mediana di x.

    Parametri:
        x : array-like, dati

    Restituisce:
        float, mediana di x
    """
    values = _as_float_vector("x", x)
    return float(np.median(values))


def weighted_mean(x: ArrayLike, w: ArrayLike | None = None) -> float:
    """
    Media di x, opzionalmente pesata.

    Se w=None, calcola la media aritmetica semplice.
    I pesi w devono essere già calcolati come w_i = 1/sigma_i^2.

    Parametri:
        x : array-like, dati
        w : array-like o None, pesi (default: tutti uguali)

    Restituisce:
        float, media (pesata) di x
    """
    values = _as_float_vector("x", x)
    weights = _validate_weights(values, w)

    if weights is None:
        return float(np.mean(values))

    return float(np.sum(values * weights) / np.sum(weights))


def variance(x: ArrayLike, w: ArrayLike | None = None, ddof: int | float = 0) -> float:
    """
    Varianza di x, opzionalmente pesata.

    Parametri:
        x : array-like
            Dati.
        w : array-like o None, default None
            Pesi associati ai dati. Se None, usa la formula non pesata.
        ddof : int o float, default 0
            Correzione sui gradi di libertà.

    Restituisce:
        float
            Varianza di x.

    Errori:
        ValueError se x è vuoto
        ValueError se x o w contengono valori non finiti
        ValueError se w non ha la stessa forma di x
        ValueError se w contiene valori non positivi
        ValueError se il denominatore è <= 0
    """
    values = _as_float_vector("x", x)
    weights = _validate_weights(values, w)

    if weights is None:
        n = values.size
        denom = n - ddof
        if denom <= 0:
            raise ValueError(
                f"denominatore non positivo: len(x) - ddof = {n} - {ddof}"
            )

        mean_x = float(np.mean(values))
        return float(np.sum((values - mean_x) ** 2) / denom)

    w_sum = float(np.sum(weights))
    denom = w_sum - ddof
    if denom <= 0:
        raise ValueError(
            f"denominatore non positivo: sum(w) - ddof = {w_sum} - {ddof}"
        )

    mean_x_w = float(np.sum(weights * values) / w_sum)
    return float(np.sum(weights * (values - mean_x_w) ** 2) / denom)


def covariance(x: ArrayLike, y: ArrayLike, w: ArrayLike | None = None) -> float:
    """
    Covarianza tra x e y, opzionalmente pesata.

    Usa la formula Cov(x,y) = E[xy] - E[x]E[y].

    Parametri:
        x : array-like, prima variabile
        y : array-like, seconda variabile
        w : array-like o None, pesi (default: tutti uguali)

    Restituisce:
        float, covarianza tra x e y

    Errori:
        ValueError se x e y hanno lunghezze diverse
        ValueError se x, y o w contengono valori non finiti
        ValueError se w ha forma incompatibile o contiene valori non positivi
    """
    x_values = _as_float_vector("x", x)
    y_values = _as_float_vector("y", y)

    if x_values.shape != y_values.shape:
        raise ValueError("x e y devono avere la stessa lunghezza")

    weights = _validate_weights(x_values, w)
    if weights is None:
        mean_xy = float(np.mean(x_values * y_values))
        mean_x = float(np.mean(x_values))
        mean_y = float(np.mean(y_values))
    else:
        w_sum = float(np.sum(weights))
        mean_xy = float(np.sum(weights * x_values * y_values) / w_sum)
        mean_x = float(np.sum(weights * x_values) / w_sum)
        mean_y = float(np.sum(weights * y_values) / w_sum)

    return float(mean_xy - mean_x * mean_y)


def standard_deviation(
    x: ArrayLike,
    w: ArrayLike | None = None,
    ddof: int | float = 0,
) -> float:
    """
    Deviazione standard di x, opzionalmente pesata.

    Parametri:
        x : array-like
            Dati.
        w : array-like o None, default None
            Pesi associati ai dati. Se None, usa la formula non pesata.
        ddof : int o float, default 0
            Delta degrees of freedom. Nel caso non pesato:
                var = sum((x - mean)^2) / (N - ddof)
            Nel caso pesato viene passato a variance(...).

    Restituisce:
        float
            Deviazione standard di x.

    Errori:
        ValueError se x è vuoto
    """
    return float(np.sqrt(variance(x, w=w, ddof=ddof)))
