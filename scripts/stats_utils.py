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


def variance(x, w=None):
    """
    Varianza di x, opzionalmente pesata.

    Usa la formula Var(x) = E[x^2] - E[x]^2.

    Parametri:
        x : array-like, dati
        w : array-like o None, pesi (default: tutti uguali)

    Restituisce:
        float, varianza di x
    """
    x = np.asarray(x, dtype=float)
    return weighted_mean(x**2, w) - weighted_mean(x, w) ** 2


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
        raise ValueError("x and y must have the same length")
    return weighted_mean(x * y, w) - weighted_mean(x, w) * weighted_mean(y, w)


def standard_deviation(x, w=None):
    """
    Deviazione standard di x, opzionalmente pesata.

    Calcola sqrt(Var(x)).

    Parametri:
        x : array-like, dati
        w : array-like o None, pesi (default: tutti uguali)

    Restituisce:
        float, deviazione standard di x

    Errori:
        ValueError se x è vuoto
    """
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        raise ValueError("x must contain at least one value")
    return np.sqrt(variance(x, w))
