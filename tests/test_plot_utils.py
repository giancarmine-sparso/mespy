import matplotlib
import pytest
import numpy as np


matplotlib.use("Agg") # impedisce a matplotlib di aprire una finestra con il grafico durante il test

from mech_lab_tools import plot_utils


def test_histogram_runs(tmp_path):
    

    data = np.random.normal(size=100)
    fig = plot_utils.histogram(data, bins=10)
    assert fig is not None  # controlla che la funzione istogramma restituisca effettivamente fig
