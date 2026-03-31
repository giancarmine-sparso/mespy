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


def test_histogram_single_point_uses_population_default_ddof():
    fig, ax = histogram([1.0])

    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)
    assert ax.get_legend() is not None
    plt.close("all")


def test_histogram_no_mean_no_band():
    data = np.random.normal(size=100)
    fig, ax = histogram(data, show_mean=False, show_band=False)
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
        band_alpha=0.25,
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


def test_histogram_requires_keyword_only_optional_arguments():
    data = np.linspace(-1.0, 1.0, 40)
    with pytest.raises(TypeError):
        histogram(data, 1)
    plt.close("all")


def test_histogram_show_band_false_does_not_draw_band():
    data = np.linspace(-2.0, 2.0, 50)
    fig, ax = histogram(data, bins=6, show_band=False, band_alpha=0.27)

    labels = [text.get_text() for text in ax.get_legend().get_texts()]

    assert not any(r"\pm 1\sigma" in label for label in labels)
    assert not any(
        patch.get_alpha() == pytest.approx(0.27)
        for patch in ax.patches
        if patch.get_alpha() is not None
    )
    plt.close("all")


def test_histogram_show_legend_false_hides_legend():
    data = np.random.normal(size=80)
    fig, ax = histogram(data, show_legend=False)

    assert ax.get_legend() is None
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


def test_histogram_rejects_empty_or_non_finite_input():
    with pytest.raises(ValueError, match="x deve contenere almeno un valore"):
        histogram([])

    with pytest.raises(ValueError, match="x deve contenere solo valori finiti"):
        histogram([1.0, np.nan])

    plt.close("all")


def test_histogram_rejects_invalid_hist_range():
    data = np.random.normal(size=20)

    with pytest.raises(ValueError, match="hist_range deve avere 2 elementi"):
        histogram(data, hist_range=(0.0,))

    with pytest.raises(ValueError, match="Serve xmin < xmax"):
        histogram(data, hist_range=(2.0, 1.0))

    plt.close("all")
