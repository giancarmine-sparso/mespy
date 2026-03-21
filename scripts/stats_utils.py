import numpy as np



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
