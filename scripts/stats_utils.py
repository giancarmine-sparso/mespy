import numpy as np
import pandas as pd


df = pd.read_csv("dati")
# irrobustimento di np.median
def median(x):
    x = np.asarray(x, dtype=float)
    return np.median(x)


# funzione per valore atteso pesato per 1/$\sigma_i^2$
def weighted_mean(x, w):
    x = np.asarray(
        x, dtype=float
    )  # si convertono gli aromenti a float per evitare problemi con le funzionni di numpy
    w = np.asarray(
        w, dtype=float
    )  # la funzione accetta così sia array che singoli scalari come argomenti.
    return np.sum(x * np.power(w, -2)) / np.sum(np.power(w, -2))


# funzione varianza
def variance(x):
    x = np.asarray(x, dtype=float)

    mu = np.mean(x)
    return np.sum((x - mu) ** 2) / len(x)


# funzione covarianza
def covariance(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if len(x) == 0:
        raise ValueError("x and y must contain at least one value")


    mean_x = np.mean(x)
    mean_y = np.mean(y)
    return np.sum((x - mean_x) * (y - mean_y)) / len(x)


# f. deviazione standard
def standard_deviation(x, ddof=1):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        raise ValueError("x must contain at least one value")
    if ddof < 0:
        raise ValueError("ddof must be non-negative")
    if len(x) <= ddof:
        raise ValueError("ddof must be smaller than len(x)")
    return np.std(x, ddof=ddof)
