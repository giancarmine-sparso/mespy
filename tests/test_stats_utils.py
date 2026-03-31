import numpy as np
import pytest

from mespy import covariance, median, standard_deviation, variance, weighted_mean


def test_weighted_mean_uniform_weights():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])
    assert weighted_mean(values, weights) == pytest.approx(2.0)


def test_weighted_mean_non_uniform_weights():
    # E_w[x] = (3*1 + 1*2 + 1*3) / (3+1+1) = 8/5 = 1.6
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([3.0, 1.0, 1.0])
    assert weighted_mean(values, weights) == pytest.approx(1.6)


def test_variance_basic():
    values = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert variance(values) == pytest.approx(4.0)


def test_variance_raises_on_empty():
    with pytest.raises(ValueError, match="almeno un valore"):
        variance([])


def test_variance_raises_on_weight_shape_mismatch():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="stessa forma"):
        variance(values, weights)


def test_variance_raises_when_ddof_makes_unweighted_denominator_non_positive():
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="denominatore non positivo"):
        variance(values, ddof=3)


def test_variance_weighted():
    # x=[1,2,3], w=[1,1,2], sum_w=4
    # E_w[x] = (1+2+6)/4 = 2.25
    # E_w[x^2] = (1+4+18)/4 = 5.75
    # Var = 5.75 - 2.25^2 = 0.6875
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 2.0])
    assert variance(values, weights) == pytest.approx(0.6875)


def test_variance_raises_when_ddof_makes_weighted_denominator_non_positive():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])

    with pytest.raises(ValueError, match="denominatore non positivo"):
        variance(values, weights, ddof=3)


def test_covariance_basic():
    # x=[1,2,3], y=[2,4,6]
    # E[xy] = (2+8+18)/3 = 28/3
    # E[x]*E[y] = 2 * 4 = 8
    # Cov = 28/3 - 8 = 4/3
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    assert covariance(x, y) == pytest.approx(4.0 / 3.0)


def test_covariance_raises_on_length_mismatch():
    with pytest.raises(ValueError, match="stessa lunghezza"):
        covariance([1.0, 2.0], [1.0, 2.0, 3.0])


def test_standard_deviation_basic():
    values = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert standard_deviation(values) == pytest.approx(2.0)


def test_standard_deviation_raises_on_empty():
    with pytest.raises(ValueError, match="almeno un valore"):
        standard_deviation([])


def test_median_odd():
    values = np.array([3.0, 1.0, 2.0])
    assert median(values) == pytest.approx(2.0)
