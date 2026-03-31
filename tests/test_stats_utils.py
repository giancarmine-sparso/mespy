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
    with pytest.raises(ValueError, match="almeno un valore"):
        weighted_mean([])

    with pytest.raises(ValueError, match="solo valori finiti"):
        weighted_mean([1.0, np.nan, 3.0])

    with pytest.raises(ValueError, match="stessa forma"):
        weighted_mean([1.0, 2.0, 3.0], [1.0, 2.0])

    with pytest.raises(ValueError, match="strettamente positivi"):
        weighted_mean([1.0, 2.0, 3.0], [1.0, 0.0, 1.0])

    with pytest.raises(ValueError, match="strettamente positivi"):
        weighted_mean([1.0, 2.0, 3.0], [1.0, -1.0, 2.0])


def test_variance_basic():
    values = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert variance(values) == pytest.approx(4.0)


def test_variance_raises_on_empty():
    with pytest.raises(ValueError, match="almeno un valore"):
        variance([])


def test_variance_raises_on_non_finite_values():
    with pytest.raises(ValueError, match="solo valori finiti"):
        variance([1.0, np.inf, 3.0])


def test_variance_raises_on_weight_shape_mismatch():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 2.0])

    with pytest.raises(ValueError, match="stessa forma"):
        variance(values, weights)


def test_variance_raises_on_non_positive_weights():
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="strettamente positivi"):
        variance(values, [1.0, 0.0, 1.0])

    with pytest.raises(ValueError, match="strettamente positivi"):
        variance(values, [1.0, -1.0, 2.0])


def test_variance_raises_when_ddof_makes_unweighted_denominator_non_positive():
    values = np.array([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="denominatore non positivo"):
        variance(values, ddof=3)


def test_variance_weighted():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 2.0])
    assert variance(values, weights) == pytest.approx(0.6875)


def test_variance_raises_when_ddof_makes_weighted_denominator_non_positive():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])

    with pytest.raises(ValueError, match="denominatore non positivo"):
        variance(values, weights, ddof=3)


def test_covariance_basic():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    assert covariance(x, y) == pytest.approx(4.0 / 3.0)


def test_covariance_raises_on_length_mismatch():
    with pytest.raises(ValueError, match="stessa lunghezza"):
        covariance([1.0, 2.0], [1.0, 2.0, 3.0])


def test_covariance_rejects_non_finite_values_and_invalid_weights():
    with pytest.raises(ValueError, match="solo valori finiti"):
        covariance([1.0, 2.0], [1.0, np.nan])

    with pytest.raises(ValueError, match="strettamente positivi"):
        covariance([1.0, 2.0], [1.0, 2.0], [1.0, 0.0])


def test_standard_deviation_basic():
    values = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert standard_deviation(values) == pytest.approx(2.0)


def test_standard_deviation_raises_on_empty():
    with pytest.raises(ValueError, match="almeno un valore"):
        standard_deviation([])


def test_standard_deviation_weighted_matches_variance_square_root():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 2.0])
    assert standard_deviation(values, weights) == pytest.approx(np.sqrt(0.6875))


def test_median_odd():
    values = np.array([3.0, 1.0, 2.0])
    assert median(values) == pytest.approx(2.0)


def test_median_rejects_empty_or_non_finite_values():
    with pytest.raises(ValueError, match="almeno un valore"):
        median([])

    with pytest.raises(ValueError, match="solo valori finiti"):
        median([1.0, np.nan, 2.0])
