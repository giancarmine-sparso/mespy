import matplotlib
import pytest

matplotlib.use("Agg")

from mech_lab_tools import plot_utils


def test_histogram_runs(tmp_path):
    import numpy as np

    data = np.random.normal(size=100)
    fig = plot_utils.histogram(data, bins=10)
    assert fig is not None
