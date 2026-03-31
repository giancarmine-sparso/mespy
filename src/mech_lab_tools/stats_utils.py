import numpy as np

# Nota: tutte le funzioni usano statistiche descrittive della popolazione
# (divisore N), non stimatori campionari (divisore N-1).


# irrobustimento di np.median
def median(x):
    """
    Mediana di x.

    Parametri:
        x : array-like, dati

    Restituisce:
        float, mediana di x
    """
    x = np.asarray(x, dtype=float)
    return np.median(x)


def weighted_mean(x, w=None):
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
    x = np.asarray(x, dtype=float)
    if w is None:
        w = np.ones(len(x))
    else:
        w = np.asarray(w, dtype=float)
    return np.sum(x * w) / np.sum(w)


def variance(x, w=None, ddof=0):
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
        ValueError se w non ha la stessa forma di x
        ValueError se il denominatore è <= 0
    """
    x = np.asarray(x, dtype=float)

    if x.size == 0:
        raise ValueError("x deve contenere almeno un valore")

    if w is None:
        n = x.size
        denom = n - ddof
        if denom <= 0:
            raise ValueError(
                f"denominatore non positivo: len(x) - ddof = {n} - {ddof}"
            )

        mean_x = np.mean(x)
        return np.sum((x - mean_x) ** 2) / denom

    w = np.asarray(w, dtype=float)

    if w.shape != x.shape:
        raise ValueError(
            f"w deve avere la stessa forma di x | x.shape={x.shape}, w.shape={w.shape}"
        )

    w_sum = np.sum(w)
    denom = w_sum - ddof

    if denom <= 0:
        raise ValueError(
            f"denominatore non positivo: sum(w) - ddof = {w_sum} - {ddof}"
        )

    mean_x_w = np.sum(w * x) / w_sum
    return np.sum(w * (x - mean_x_w) ** 2) / denom


def covariance(x, y, w=None):
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
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) != len(y):
        raise ValueError("x e y devono avere la stessa lunghezza")
    return weighted_mean(x * y, w) - weighted_mean(x, w) * weighted_mean(y, w)


def standard_deviation(x, w=None, ddof=0):
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
    x = np.asarray(x, dtype=float)

    if x.size == 0:
        raise ValueError("x deve contenere almeno un valore")

    return np.sqrt(variance(x, w=w, ddof=ddof))
