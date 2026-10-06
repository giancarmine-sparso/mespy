from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatVector = NDArray[np.float64]


def _as_float_vector(name: str, values: ArrayLike, *, allow_empty: bool = False) -> FloatVector:
    """Convert *values* into a finite, one-dimensional float64 array."""
    vector = np.asarray(values, dtype=float)

    if vector.ndim != 1:
        raise ValueError(f"{name} deve essere un array monodimensionale")

    if not allow_empty and vector.size == 0:
        raise ValueError(f"{name} deve contenere almeno un valore")

    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} deve contenere solo valori finiti")

    return vector


def _validate_weights(x: FloatVector, w: ArrayLike | None) -> FloatVector | None:
    """Validate a positive weight vector with the same shape as *x*."""
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
    Median of ``x``.

    Parameters
    ----------
    x : array-like
        Data.

    Returns
    -------
    float
        Median of ``x``.

    Raises
    ------
    ValueError
        If ``x`` is empty, not one-dimensional, or contains non-finite
        values.
    """
    values = _as_float_vector("x", x)
    return float(np.median(values))


def weighted_mean(x: ArrayLike, w: ArrayLike | None = None) -> float:
    """
    Mean of ``x``, optionally weighted.

    If ``w`` is ``None``, computes the plain arithmetic mean. Weights
    must already be computed, e.g. as ``w_i = 1 / sigma_i**2``.

    Parameters
    ----------
    x : array-like
        Data.
    w : array-like or None, optional
        Weights; ``None`` means all equal (default ``None``).

    Returns
    -------
    float
        (Weighted) mean of ``x``.

    Raises
    ------
    ValueError
        If ``x`` is empty, not one-dimensional, or contains non-finite
        values.
    ValueError
        If ``w`` does not have the same shape as ``x``, contains
        non-finite or non-positive values.
    """
    values = _as_float_vector("x", x)
    weights = _validate_weights(values, w)

    if weights is None:
        return float(np.mean(values))

    return float(np.sum(values * weights) / np.sum(weights))


def variance(x: ArrayLike, w: ArrayLike | None = None, ddof: int | float = 0) -> float:
    """
    Variance of ``x``, optionally weighted.

    Parameters
    ----------
    x : array-like
        Data.
    w : array-like or None, optional
        Weights associated with the data. If ``None``, the unweighted
        formula is used (default ``None``).
    ddof : int or float, optional
        Delta degrees of freedom. The denominator is ``N - ddof``
        (unweighted) or ``sum(w) - ddof`` (weighted) (default ``0``).

    Returns
    -------
    float
        Variance of ``x``.

    Raises
    ------
    ValueError
        If ``x`` is empty, not one-dimensional, or contains non-finite
        values.
    ValueError
        If ``w`` does not have the same shape as ``x``, contains
        non-finite or non-positive values.
    ValueError
        If the denominator is not positive.
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

        dx = values - float(np.mean(values))
        # Two-pass corretto (Chan-Golub-LeVeque): il termine sottratto è zero
        # in aritmetica esatta e compensa l'errore di arrotondamento della
        # media, che con grandi offset vale circa ulp(offset).
        return float((np.sum(dx * dx) - np.sum(dx) ** 2 / n) / denom)

    w_sum = float(np.sum(weights))
    denom = w_sum - ddof
    if denom <= 0:
        raise ValueError(
            f"denominatore non positivo: sum(w) - ddof = {w_sum} - {ddof}"
        )

    dx = values - float(np.sum(weights * values) / w_sum)
    return float(
        (np.sum(weights * dx * dx) - np.sum(weights * dx) ** 2 / w_sum) / denom
    )


def covariance(x: ArrayLike, y: ArrayLike, w: ArrayLike | None = None) -> float:
    """
    Covariance between ``x`` and ``y``, optionally weighted.

    ``Cov(x, y) = E[(x - E[x]) (y - E[y])]``, normalized by ``N`` (or
    ``sum(w)``). The data are centered first (corrected two-pass
    algorithm) instead of using ``E[xy] - E[x] E[y]``, which suffers
    from cancellation with large offsets.

    Parameters
    ----------
    x : array-like
        First variable.
    y : array-like
        Second variable.
    w : array-like or None, optional
        Weights; ``None`` means all equal (default ``None``).

    Returns
    -------
    float
        Covariance between ``x`` and ``y``.

    Raises
    ------
    ValueError
        If ``x`` or ``y`` is empty, not one-dimensional, or contains
        non-finite values.
    ValueError
        If ``x`` and ``y`` have different lengths.
    ValueError
        If ``w`` does not have the same shape as ``x``, contains
        non-finite or non-positive values.
    """
    x_values = _as_float_vector("x", x)
    y_values = _as_float_vector("y", y)

    if x_values.shape != y_values.shape:
        raise ValueError("x e y devono avere la stessa lunghezza")

    weights = _validate_weights(x_values, w)
    if weights is None:
        weights = np.ones_like(x_values)

    w_sum = float(np.sum(weights))
    dx = x_values - float(np.sum(weights * x_values) / w_sum)
    dy = y_values - float(np.sum(weights * y_values) / w_sum)
    # Two-pass corretto: il termine sottratto è zero in aritmetica esatta e
    # compensa l'errore di arrotondamento delle medie.
    return float(
        (np.sum(weights * dx * dy) - np.sum(weights * dx) * np.sum(weights * dy) / w_sum)
        / w_sum
    )


def standard_deviation(
    x: ArrayLike,
    w: ArrayLike | None = None,
    ddof: int | float = 0,
) -> float:
    """
    Standard deviation of ``x``, optionally weighted.

    Computed as the square root of :func:`variance`.

    Parameters
    ----------
    x : array-like
        Data.
    w : array-like or None, optional
        Weights associated with the data. If ``None``, the unweighted
        formula is used (default ``None``).
    ddof : int or float, optional
        Delta degrees of freedom, passed to :func:`variance`. In the
        unweighted case ``var = sum((x - mean)**2) / (N - ddof)``
        (default ``0``).

    Returns
    -------
    float
        Standard deviation of ``x``.

    Raises
    ------
    ValueError
        If ``x`` is empty, not one-dimensional, or contains non-finite
        values.
    ValueError
        If ``w`` does not have the same shape as ``x``, contains
        non-finite or non-positive values.
    ValueError
        If the denominator is not positive.
    """
    return float(np.sqrt(variance(x, w=w, ddof=ddof)))
