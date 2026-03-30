import numpy as np
import pytest

from mech_lab_tools import covariance, median, standard_deviation, variance, weighted_mean


def test_weighted_mean_uniform_weights():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])
    assert weighted_mean(values, weights) == pytest.approx(2.0)


def test_variance_basic():
    values = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert variance(values) == pytest.approx(4.0)


def test_median_odd():
    values = np.array([3.0, 1.0, 2.0])
    assert median(values) == pytest.approx(2.0)
