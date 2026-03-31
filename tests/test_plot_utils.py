import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

matplotlib.use("Agg")

from mespy import histogram


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


def test_histogram_accepts_custom_plot_styling_kwargs():
    data = np.linspace(-2.0, 2.0, 50)
    fig, ax = histogram(
        data,
        bins=6,
        title="Istogramma custom",
        title_fontsize=16,
        title_pad=12,
        legend_fontsize=11,
        legend_loc="upper left",
        show_grid=False,
        hist_alpha=0.4,
        mean_symbol=r"\mu",
        std_alpha=0.25,
    )

    legend = ax.get_legend()
    labels = [text.get_text() for text in legend.get_texts()]

    assert ax.get_title() == "Istogramma custom"
    assert ax.title.get_fontsize() == pytest.approx(16)
    assert legend is not None
    assert legend.get_texts()[0].get_fontsize() == pytest.approx(11)
    assert any(label.startswith(r"$\mu = ") for label in labels)
    assert not any(line.get_visible() for line in ax.get_ygridlines())
    assert any(
        patch.get_alpha() == pytest.approx(0.4)
        for patch in ax.patches
        if patch.get_alpha() is not None
    )
    assert any(
        patch.get_alpha() == pytest.approx(0.25)
        for patch in ax.patches
        if patch.get_alpha() is not None
    )
    plt.close("all")


def test_histogram_preserves_legacy_positional_arguments():
    data = np.linspace(-1.0, 1.0, 40)
    fig, ax = histogram(
        data,
        1,
        8,
        "Campione",
        "Asse x",
        "Conteggi custom",
        "Titolo storico",
        False,
        None,
        0,
        2,
        (6, 4),
        None,
        False,
        False,
        False,
        150,
    )

    assert ax.get_title() == "Titolo storico"
    assert ax.get_ylabel() == "Conteggi custom"
    assert ax.get_legend() is None
    assert len(ax.lines) == 0
    assert fig.dpi == pytest.approx(150)
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


def test_histogram_rejects_scalar_axis_limits():
    data = np.random.normal(size=20)

    with pytest.raises(ValueError, match="xlim deve essere una sequenza di 2 elementi"):
        histogram(data, xlim=1)

    with pytest.raises(ValueError, match="ylim deve essere una sequenza di 2 elementi"):
        histogram(data, ylim=1)

    plt.close("all")
