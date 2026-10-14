from fractions import Fraction

import numpy as np
import pytest

from mespy import covariance, median, standard_deviation, variance, weighted_mean


def test_weighted_mean_uniform_weights():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])
    assert weighted_mean(values, weights) == pytest.approx(2.0)


def test_weighted_mean_non_uniform_weights():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([3.0, 1.0, 1.0])
    assert weighted_mean(values, weights) == pytest.approx(1.6)


def test_weighted_mean_without_weights_matches_arithmetic_mean():
    values = np.array([1.0, 2.0, 3.0])
    assert weighted_mean(values) == pytest.approx(2.0)


def test_weighted_mean_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="at least one value"):
        weighted_mean([])

    with pytest.raises(ValueError, match="only finite values"):
        weighted_mean([1.0, np.nan, 3.0])

    with pytest.raises(ValueError, match="same shape"):
        weighted_mean([1.0, 2.0, 3.0], [1.0, 2.0])

    with pytest.raises(ValueError, match="strictly positive"):
        weighted_mean([1.0, 2.0, 3.0], [1.0, 0.0, 1.0])

    with pytest.raises(ValueError, match="strictly positive"):
        weighted_mean([1.0, 2.0, 3.0], [1.0, -1.0, 2.0])


def test_variance_basic():
    values = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert variance(values) == pytest.approx(4.0)


def test_variance_raises_on_empty():
    with pytest.raises(ValueError, match="at least one value"):
        variance([])


def test_variance_raises_on_non_finite_values():
    with pytest.raises(ValueError, match="only finite values"):
        variance([1.0, np.inf, 3.0])


def test_variance_raises_on_weight_shape_mismatch():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="same shape"):
        variance(values, weights)


def test_variance_raises_on_non_positive_weights():
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="strictly positive"):
        variance(values, [1.0, 0.0, 1.0])

    with pytest.raises(ValueError, match="strictly positive"):
        variance(values, [1.0, -1.0, 2.0])


def test_variance_raises_when_ddof_makes_unweighted_denominator_non_positive():
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="non-positive denominator"):
        variance(values, ddof=3)


def test_variance_weighted():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 2.0])
    assert variance(values, weights) == pytest.approx(0.6875)


def test_variance_raises_when_ddof_makes_weighted_denominator_non_positive():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])

    with pytest.raises(ValueError, match="non-positive denominator"):
        variance(values, weights, ddof=3)


def test_covariance_basic():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    assert covariance(x, y) == pytest.approx(4.0 / 3.0)


OFFSET_X = np.arange(1.0, 7.0)
OFFSET_Y = 0.8 * OFFSET_X + 0.3 + np.array([0.05, -0.04, 0.02, -0.03, 0.01, 0.0])
OFFSET_W = 1.0 / np.array([0.05, 0.04, 0.06, 0.05, 0.03, 0.05]) ** 2


def test_covariance_weighted_matches_numpy():
    expected = np.cov(OFFSET_X, OFFSET_Y, bias=True, aweights=OFFSET_W)[0, 1]
    assert covariance(OFFSET_X, OFFSET_Y, OFFSET_W) == pytest.approx(expected, rel=1e-14)
    assert covariance(OFFSET_X, OFFSET_Y) == pytest.approx(
        np.cov(OFFSET_X, OFFSET_Y, bias=True)[0, 1], rel=1e-14
    )


@pytest.mark.parametrize("w", [None, OFFSET_W])
def test_covariance_large_offset(w):
    # 1e15 + [1..6] è esattamente rappresentabile in float64 (ulp = 0.125):
    # l'unica perdita possibile è quella dell'algoritmo.
    reference = covariance(OFFSET_X, OFFSET_Y, w)
    assert covariance(1e15 + OFFSET_X, OFFSET_Y, w) == pytest.approx(reference, rel=1e-12)


def _exact_covariance(x, y, w):
    """Exact (rational) covariance of the float64 values actually passed in."""
    xs = [Fraction(v) for v in x]
    ys = [Fraction(v) for v in y]
    ws = [Fraction(1)] * len(xs) if w is None else [Fraction(v) for v in w]
    w_sum = sum(ws)
    mean_x = sum(wi * xi for wi, xi in zip(ws, xs)) / w_sum
    mean_y = sum(wi * yi for wi, yi in zip(ws, ys)) / w_sum
    return float(
        sum(wi * (xi - mean_x) * (yi - mean_y) for wi, xi, yi in zip(ws, xs, ys)) / w_sum
    )


@pytest.mark.parametrize("w", [None, OFFSET_W])
@pytest.mark.parametrize(("c", "d"), [(1e3, -7.0), (-1e8, 1e6), (1e12, 1e12), (1e15, 0.0)])
def test_covariance_is_shift_invariant(w, c, d):
    # Il riferimento è calcolato sui valori shiftati già arrotondati a float64:
    # per y + 1e12 l'input perde ~1e-4 di risoluzione (ulp(1e12)) prima ancora
    # di arrivare a covariance, e quella perdita non è imputabile all'algoritmo.
    x_shifted = OFFSET_X + c
    y_shifted = OFFSET_Y + d
    expected = _exact_covariance(x_shifted, y_shifted, w)
    assert covariance(x_shifted, y_shifted, w) == pytest.approx(expected, rel=1e-12)

    if np.array_equal(x_shifted - c, OFFSET_X) and np.array_equal(y_shifted - d, OFFSET_Y):
        # Shift rappresentabile senza perdita: coincide col caso non shiftato.
        reference = covariance(OFFSET_X, OFFSET_Y, w)
        assert covariance(x_shifted, y_shifted, w) == pytest.approx(reference, rel=1e-12)


@pytest.mark.parametrize("w", [None, OFFSET_W])
def test_variance_large_offset(w):
    reference = variance(OFFSET_X, w)
    assert variance(1e15 + OFFSET_X, w) == pytest.approx(reference, rel=1e-12)


def test_covariance_raises_on_length_mismatch():
    with pytest.raises(ValueError, match="same length"):
        covariance([1.0, 2.0], [1.0, 2.0, 3.0])


def test_covariance_rejects_non_finite_values_and_invalid_weights():
    with pytest.raises(ValueError, match="only finite values"):
        covariance([1.0, 2.0], [1.0, np.nan])

    with pytest.raises(ValueError, match="strictly positive"):
        covariance([1.0, 2.0], [1.0, 2.0], [1.0, 0.0])


def test_standard_deviation_basic():
    values = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert standard_deviation(values) == pytest.approx(2.0)


def test_standard_deviation_raises_on_empty():
    with pytest.raises(ValueError, match="at least one value"):
        standard_deviation([])


def test_standard_deviation_weighted_matches_variance_square_root():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 2.0])
    assert standard_deviation(values, weights) == pytest.approx(np.sqrt(0.6875))


def test_median_odd():
    values = np.array([3.0, 1.0, 2.0])
    assert median(values) == pytest.approx(2.0)


def test_median_rejects_empty_or_non_finite_values():
    with pytest.raises(ValueError, match="at least one value"):
        median([])

    with pytest.raises(ValueError, match="only finite values"):
        median([1.0, np.nan, 2.0])
