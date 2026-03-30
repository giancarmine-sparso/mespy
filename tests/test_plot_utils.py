import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

matplotlib.use("Agg")

from mech_lab_tools import histogram


def test_histogram_returns_fig_and_ax():
    data = np.random.normal(size=100)
    fig, ax = histogram(data, bins=10)
    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close("all")


def test_histogram_no_mean_no_std():
    data = np.random.normal(size=100)
    fig, ax = histogram(data, show_mean=False, show_std=False)
    # senza media e banda, la legenda ha solo "Dati"
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert len(labels) == 1
    assert labels[0] == "Dati"
    plt.close("all")


def test_histogram_save_path(tmp_path):
    data = np.random.normal(size=100)
    path = tmp_path / "hist.png"
    histogram(data, save_path=str(path))
    assert path.exists()
    plt.close("all")


def test_histogram_external_ax():
    fig_ext, ax_ext = plt.subplots()
    data = np.random.normal(size=50)
    fig, ax = histogram(data, ax=ax_ext)
    assert ax is ax_ext
    assert fig is fig_ext
    plt.close("all")
