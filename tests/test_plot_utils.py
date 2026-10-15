import warnings

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

matplotlib.use("Agg")

from mespy import histogram
from mespy.plot_utils import _resolve_style

STAT_MODES = ("count", "probability", "density")


def test_resolve_style_supports_none_and_bundled_styles():
    assert _resolve_style(None) is None
    for style in ("mespy", "report", "column"):
        resolved = _resolve_style(style)
        assert resolved is not None
        assert resolved.endswith(f"{style}.mplstyle")


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


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_accepts_custom_plot_styling_kwargs(stat):
    data = np.linspace(-2.0, 2.0, 50)
    fig, ax = histogram(
        data,
        stat,
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


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_uses_mespy_style_by_default_and_can_disable_it(stat):
    data = np.linspace(-1.0, 1.0, 20)
    custom_facecolor = "xkcd:pale pink"

    with plt.rc_context({"axes.facecolor": custom_facecolor}):
        fig_default, ax_default = histogram(
            data,
            stat,
            show_grid=False,
            show_legend=False,
        )
        fig_none, ax_none = histogram(
            data,
            stat,
            style=None,
            show_grid=False,
            show_legend=False,
        )

    assert ax_default.get_facecolor() == pytest.approx(matplotlib.colors.to_rgba("white"))
    assert ax_none.get_facecolor() == pytest.approx(
        matplotlib.colors.to_rgba(custom_facecolor)
    )
    plt.close("all")


def test_histogram_requires_keyword_only_arguments_after_stat():
    data = np.linspace(-1.0, 1.0, 40)
    with pytest.raises(TypeError):
        histogram(data, "count", 1)
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


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_show_legend_false_hides_legend(stat):
    data = np.random.normal(size=80)
    fig, ax = histogram(data, stat, show_legend=False)

    assert ax.get_legend() is None
    plt.close("all")


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_save_path(tmp_path, stat):
    data = np.random.normal(size=100)
    path = tmp_path / "hist.png"
    histogram(data, stat, save_path=str(path))
    assert path.exists()
    plt.close("all")


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_external_ax(stat):
    fig_ext, ax_ext = plt.subplots()
    data = np.random.normal(size=50)
    fig, ax = histogram(data, stat, ax=ax_ext)
    assert ax is ax_ext
    assert fig is fig_ext
    plt.close("all")


def test_histogram_rejects_scalar_axis_limits():
    data = np.random.normal(size=20)

    with pytest.raises(ValueError, match="xlim must be a sequence of 2 elements"):
        histogram(data, xlim=1)

    with pytest.raises(ValueError, match="ylim must be a sequence of 2 elements"):
        histogram(data, ylim=1)

    plt.close("all")


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_rejects_empty_or_non_finite_input(stat):
    with pytest.raises(ValueError, match="x must contain at least one value"):
        histogram([], stat)

    with pytest.raises(ValueError, match="x must contain only finite values"):
        histogram([1.0, np.nan], stat)

    plt.close("all")


@pytest.mark.parametrize(
    "stat, expected, ylabel",
    [
        ("count", [2, 3], "Conteggi"),
        ("probability", [0.4, 0.6], "Frequenza relativa"),
        ("density", [0.4, 0.3], "Densità di frequenza"),
    ],
)
def test_histogram_unequal_bins_normalize_included_observations(stat, expected, ylabel):
    fig, ax = histogram(
        [-2, 0, 0.5, 1, 2.5, 3, 9],
        stat=stat,
        bins=[0, 1, 3],
        show_mean=False,
        show_band=False,
    )
    bars = ax.containers[0]
    heights = np.array([bar.get_height() for bar in bars])
    widths = np.array([bar.get_width() for bar in bars])
    np.testing.assert_allclose(heights, expected)
    np.testing.assert_allclose(widths, [1, 2])
    np.testing.assert_allclose([bar.get_x() for bar in bars], [0, 1])
    np.testing.assert_allclose(ax.get_xticks(), [0, 1, 3])
    assert ax.get_ylabel() == ylabel
    if stat == "probability":
        assert heights.sum() == pytest.approx(1)
    elif stat == "density":
        assert np.sum(heights * widths) == pytest.approx(1)
    plt.close(fig)


@pytest.mark.parametrize("stat", STAT_MODES)
@pytest.mark.parametrize(
    "kwargs, edges, counts",
    [
        ({"bins": 2, "hist_range": (0, 3)}, [0, 1.5, 3], [2, 2]),
        # Explicit edges determine inclusion even when hist_range is provided.
        ({"bins": [0, 1, 3], "hist_range": (0.2, 2.2)}, [0, 1, 3], [2, 2]),
        # bin_width expands the range to whole multiples, as before.
        ({"bin_width": 1, "hist_range": (0.2, 2.2)}, [0, 1, 2, 3], [2, 1, 1]),
    ],
)
def test_histogram_range_and_bin_width(stat, kwargs, edges, counts):
    fig, ax = histogram(
        [-1, 0.1, 0.8, 1.5, 2.7, 4],
        stat,
        show_mean=False,
        show_band=False,
        **kwargs,
    )
    bars = ax.containers[0]
    heights = np.array([bar.get_height() for bar in bars])
    expected = np.array(counts, dtype=float)
    if stat != "count":
        expected /= 4
    if stat == "density":
        expected /= np.diff(edges)
    np.testing.assert_allclose(heights, expected)
    np.testing.assert_allclose([bar.get_x() for bar in bars], edges[:-1])
    np.testing.assert_allclose([bar.get_width() for bar in bars], np.diff(edges))
    plt.close(fig)


@pytest.mark.parametrize("stat", STAT_MODES)
@pytest.mark.parametrize("bins", ["auto", "sqrt", 4, [-2, 0, 0.25, 2]])
def test_histogram_binning_matches_numpy(stat, bins):
    data = [-2, -0.5, 0, 0.25, 0.5, 1.5, 2]
    counts, edges = np.histogram(data, bins=bins)
    fig, ax = histogram(data, stat, bins=bins, show_mean=False, show_band=False)
    heights = np.array([bar.get_height() for bar in ax.containers[0]])
    expected = counts.astype(float)
    if stat != "count":
        expected /= len(data)
    if stat == "density":
        expected /= np.diff(edges)
    np.testing.assert_allclose(heights, expected)
    np.testing.assert_allclose(ax.get_xticks(), edges)
    plt.close(fig)


@pytest.mark.parametrize("stat", STAT_MODES)
@pytest.mark.parametrize(
    "kwargs",
    [
        {"bins": [0, 1, 3]},
        {"bins": 2, "hist_range": (0, 3)},
        {"bin_width": 1, "hist_range": (0, 3)},
    ],
)
def test_histogram_no_included_observations_has_zero_bars_without_warnings(stat, kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        fig, ax = histogram([4, 5], stat, show_mean=False, show_band=False, **kwargs)
    heights = [bar.get_height() for bar in ax.containers[0]]
    assert heights
    np.testing.assert_array_equal(heights, np.zeros(len(heights)))
    plt.close(fig)


@pytest.mark.parametrize(
    "stat", ["invalid", "Count", "", None, 1, [], np.array(["count", "density"])]
)
def test_histogram_rejects_invalid_stat_before_creating_figure(stat):
    existing = plt.get_fignums()
    with pytest.raises(ValueError, match="'stat'.*'count'.*'probability'.*'density'"):
        histogram([0, 1, 2], stat)
    assert plt.get_fignums() == existing


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_bin_width_validation_is_unchanged(stat):
    with pytest.raises(ValueError, match="'bin_width' must be > 0"):
        histogram([0, 1], stat, bin_width=0)
    with pytest.raises(ValueError, match="mutually exclusive"):
        histogram([0, 1], stat, bins=2, bin_width=1)
    plt.close("all")


@pytest.mark.parametrize("bins", [[0, 1, 2], np.array([0.0, 1.0, 2.0]), "fd"])
def test_histogram_bin_width_rejects_any_explicit_bins(bins):
    with pytest.raises(ValueError, match="mutually exclusive"):
        histogram([0, 1], bins=bins, bin_width=0.5)
    plt.close("all")


def test_histogram_bin_width_edges_stop_at_the_covering_multiple():
    width = 0.1
    for i in range(1, 300):
        xmax = i * width
        fig, ax = histogram(
            [0.0, xmax], bin_width=width, show_mean=False, show_band=False
        )
        edges = ax.get_xticks()
        expected_last = np.ceil(xmax / width) * width
        assert edges[-1] == pytest.approx(expected_last)
        assert len(edges) == int(np.ceil(xmax / width)) + 1
        plt.close(fig)


@pytest.mark.parametrize("stat", STAT_MODES)
def test_histogram_custom_ylabel_and_bar_styles(stat):
    fig, ax = histogram(
        [0, 1, 2],
        stat,
        bins=[0, 1, 3],
        ylabel="Personalizzata",
        bar_color="red",
        edgecolor="black",
        hist_alpha=0.4,
        grid_alpha=0.2,
        label="Misure",
        show_mean=False,
        show_band=False,
    )
    assert ax.get_ylabel() == "Personalizzata"
    for bar in ax.containers[0]:
        assert bar.get_facecolor() == pytest.approx(
            matplotlib.colors.to_rgba("red", 0.4)
        )
        assert bar.get_edgecolor() == pytest.approx(
            matplotlib.colors.to_rgba("black", 0.4)
        )
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["Misure"]
    assert all(
        line.get_alpha() == pytest.approx(0.2) for line in ax.get_ygridlines()
    )
    plt.close(fig)


@pytest.mark.parametrize("stat", ["probability", "density"])
def test_histogram_normalized_bars_preserve_mespy_style_and_full_sample_statistics(stat):
    data = [-2, 0, 0.5, 1, 2.5, 3, 9]
    fig_count, ax_count = histogram(data, bins=[0, 1, 3], ddof=1)
    fig, ax = histogram(data, stat, bins=[0, 1, 3], ddof=1)
    reference = ax_count.containers[0][0]
    bar = ax.containers[0][0]
    assert bar.get_facecolor() == pytest.approx(reference.get_facecolor())
    assert bar.get_edgecolor() == pytest.approx(reference.get_edgecolor())
    assert bar.get_linewidth() == pytest.approx(reference.get_linewidth())
    np.testing.assert_allclose(ax.lines[0].get_xdata(), ax_count.lines[0].get_xdata())
    # The band uses a rectangle in data coordinates; compare its horizontal extent.
    assert ax.patches[-1].get_x() == pytest.approx(ax_count.patches[-1].get_x())
    assert ax.patches[-1].get_width() == pytest.approx(ax_count.patches[-1].get_width())
    assert [t.get_text() for t in ax.get_legend().get_texts()] == [
        t.get_text() for t in ax_count.get_legend().get_texts()
    ]
    assert any(line.get_visible() for line in ax.get_ygridlines())
    plt.close(fig_count)
    plt.close(fig)


def test_histogram_default_count_matches_explicit_count():
    fig_default, ax_default = histogram([0, 0.5, 1, 3], bins=[0, 1, 3])
    fig_count, ax_count = histogram([0, 0.5, 1, 3], "count", bins=[0, 1, 3])
    for first, second in zip(ax_default.containers[0], ax_count.containers[0]):
        assert first.get_bbox().bounds == pytest.approx(second.get_bbox().bounds)
        assert first.get_facecolor() == second.get_facecolor()
        assert first.get_edgecolor() == second.get_edgecolor()
    assert ax_default.get_ylabel() == ax_count.get_ylabel() == "Conteggi"
    np.testing.assert_allclose(ax_default.get_ylim(), ax_count.get_ylim())
    plt.close(fig_default)
    plt.close(fig_count)


@pytest.mark.parametrize("stat, expected_height", [("probability", 0.75), ("density", 25)])
def test_histogram_normalized_autoscaling_and_explicit_limits(stat, expected_height):
    fig, ax = histogram(
        [0, 0.01, 0.02, 0.03], stat, bins=[0, 0.01, 0.04],
        show_mean=False, show_band=False,
    )
    assert max(bar.get_height() for bar in ax.containers[0]) == pytest.approx(
        expected_height
    )
    assert ax.get_ylim()[1] > expected_height
    assert ax.get_ylim()[1] < 1.1 * expected_height
    plt.close(fig)
    fig, ax = histogram(
        [0, 0.01, 0.02, 0.03], stat, bins=[0, 0.01, 0.04], ylim=(0, 50)
    )
    assert ax.get_ylim() == pytest.approx((0, 50))
    plt.close(fig)


def test_histogram_rejects_invalid_hist_range():
    data = np.random.normal(size=20)

    with pytest.raises(ValueError, match="hist_range must have 2 elements"):
        histogram(data, hist_range=(0.0,))

    with pytest.raises(ValueError, match="requires xmin < xmax"):
        histogram(data, hist_range=(2.0, 1.0))

    plt.close("all")
