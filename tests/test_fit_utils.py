import matplotlib
import numpy as np
import pytest

from mespy import lin_fit
from mespy.fit_utils import LinearFitResult


matplotlib.use("Agg")


def make_placebo_data():
    rng = np.random.default_rng(42)
    x = np.arange(1, 11, dtype=float)
    sigma_y = np.full_like(x, 0.8)
    m_true = 0.6
    c_true = 1.2
    rumore = rng.normal(0.0, 0.8, size=x.size)
    y = c_true + m_true * x + rumore
    return x, y, sigma_y, m_true, c_true


def make_placebo_data_with_sigma_x():
    rng = np.random.default_rng(123)
    x_true = np.linspace(1.0, 10.0, 16)
    sigma_x = np.linspace(0.08, 0.22, x_true.size)
    sigma_y = np.full_like(x_true, 0.35)
    m_true = 1.7
    c_true = 0.9
    x_obs = x_true + rng.normal(0.0, sigma_x)
    y = c_true + m_true * x_true + rng.normal(0.0, sigma_y)
    return x_obs, y, sigma_y, sigma_x, m_true, c_true


def test_lin_fit_returns_typed_result_and_expected_parameters():
    x, y, sigma_y, m_true, c_true = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        xlabel="x placebo",
        ylabel="y placebo",
        show_band=True,
        show_plot=True,
    )

    assert isinstance(result, LinearFitResult)
    assert result.slope == pytest.approx(m_true, abs=0.10)
    assert result.intercept == pytest.approx(c_true, abs=0.20)
    assert result.figure is not None
    assert len(result.figure.axes) == 2
    assert len(result.residuals) == len(x)
    assert result.slope_std > 0
    assert result.intercept_std > 0
    assert result.residual_std > 0
    assert result.chi2 > 0
    assert result.reduced_chi2 == pytest.approx(result.chi2 / result.dof)
    assert result.dof == len(x) - 2
    assert result.iterations == 0
    assert result.converged is True


def test_lin_fit_accepts_custom_plot_styling_kwargs():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        show_plot=True,
        title="Fit placebo",
        title_fontsize=16,
        title_pad=12,
        legend_fontsize=11,
        legend_loc="upper left",
        show_grid=False,
        data_alpha=0.6,
        band_alpha=0.35,
    )

    ax_fit = result.figure.axes[0]
    legenda = ax_fit.get_legend()

    assert ax_fit.get_title() == "Fit placebo"
    assert ax_fit.title.get_fontsize() == pytest.approx(16)
    assert legenda is not None
    assert legenda.get_texts()[0].get_fontsize() == pytest.approx(11)
    assert not any(line.get_visible() for line in ax_fit.get_ygridlines())
    assert any(
        collection.get_alpha() == pytest.approx(0.35)
        for collection in ax_fit.collections
        if collection.get_alpha() is not None
    )


def test_lin_fit_with_sigma_x_uses_iterative_effective_variance():
    x, y, sigma_y, sigma_x, m_true, c_true = make_placebo_data_with_sigma_x()

    result_base = lin_fit(x, y, sigma_y, show_plot=False)
    result_sigma_x = lin_fit(
        x,
        y,
        sigma_y,
        sigma_x=sigma_x,
        show_plot=False,
    )

    assert result_sigma_x.slope == pytest.approx(m_true, abs=0.05)
    assert result_sigma_x.intercept == pytest.approx(c_true, abs=0.20)
    assert result_sigma_x.iterations > 0
    assert result_sigma_x.converged is True
    assert result_sigma_x.slope_std > result_base.slope_std
    assert result_sigma_x.intercept_std > result_base.intercept_std


def test_lin_fit_without_plot_returns_no_figure():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, show_plot=False)

    assert result.figure is None


def test_lin_fit_show_band_false_does_not_draw_band():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(
        x,
        y,
        sigma_y,
        show_plot=True,
        show_band=False,
        band_alpha=0.17,
    )

    ax_fit = result.figure.axes[0]
    legenda = ax_fit.get_legend()
    labels = [text.get_text() for text in legenda.get_texts()]

    assert not any(r"\pm 1 \sigma" in label for label in labels)
    assert not any(
        collection.get_alpha() == pytest.approx(0.17)
        for collection in ax_fit.collections
        if collection.get_alpha() is not None
    )


def test_lin_fit_show_legend_false_hides_legend():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, show_plot=True, show_legend=False)

    ax_fit = result.figure.axes[0]
    assert ax_fit.get_legend() is None


def test_lin_fit_show_fit_params_adds_coefficients_to_legend():
    x, y, sigma_y, _, _ = make_placebo_data()

    result = lin_fit(x, y, sigma_y, show_plot=True, show_fit_params=True)

    ax_fit = result.figure.axes[0]
    labels = [text.get_text() for text in ax_fit.get_legend().get_texts()]

    assert any(label.startswith("Fit: m=") for label in labels)


def test_lin_fit_save_path_saves_figure(tmp_path):
    x, y, sigma_y, _, _ = make_placebo_data()
    path = tmp_path / "fit.png"

    lin_fit(x, y, sigma_y, show_plot=True, save_path=str(path))

    assert path.exists()


def test_lin_fit_save_path_requires_show_plot():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="show_plot=True"):
        lin_fit(x, y, sigma_y, show_plot=False, save_path="fit.png")


def test_lin_fit_raises_on_invalid_input():
    with pytest.raises(ValueError, match="stessa lunghezza"):
        lin_fit([1.0, 2.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], show_plot=False)

    with pytest.raises(ValueError, match="almeno 3 punti"):
        lin_fit([1.0, 2.0], [1.0, 2.0], [0.1, 0.1], show_plot=False)


def test_lin_fit_rejects_non_finite_values():
    with pytest.raises(ValueError, match="solo valori finiti"):
        lin_fit(
            [1.0, np.nan, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, 0.1, 0.1],
            show_plot=False,
        )

    with pytest.raises(ValueError, match="solo valori finiti"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, np.inf, 3.0],
            [0.1, 0.1, 0.1],
            show_plot=False,
        )

    with pytest.raises(ValueError, match="solo valori finiti"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, np.nan, 0.1],
            show_plot=False,
        )


def test_lin_fit_rejects_non_positive_sigma():
    with pytest.raises(ValueError, match="strettamente positivi"):
        lin_fit([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.1, 0.0, 0.1], show_plot=False)

    with pytest.raises(ValueError, match="strettamente positivi"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, -0.2, 0.1],
            show_plot=False,
        )

    with pytest.raises(ValueError, match="sigma_x"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, 0.1, 0.1],
            sigma_x=[0.1, 0.0, 0.1],
            show_plot=False,
        )


def test_lin_fit_rejects_constant_x():
    with pytest.raises(ValueError, match="valori distinti"):
        lin_fit([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], show_plot=False)


def test_lin_fit_rejects_scalar_axis_limits_when_plotting():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="xlim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, show_plot=True, xlim=1)

    with pytest.raises(ValueError, match="ylim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, show_plot=True, ylim=1)


def test_lin_fit_rejects_invalid_tol_and_max_iter():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="tol deve essere un numero finito strettamente positivo"):
        lin_fit(x, y, sigma_y, show_plot=False, tol=0.0)

    with pytest.raises(ValueError, match="max_iter deve essere un intero positivo"):
        lin_fit(x, y, sigma_y, show_plot=False, max_iter=0)


def test_lin_fit_raises_when_sigma_x_fit_does_not_converge():
    x, y, sigma_y, sigma_x, _, _ = make_placebo_data_with_sigma_x()

    with pytest.raises(RuntimeError, match="non converge"):
        lin_fit(
            x,
            y,
            sigma_y,
            sigma_x=sigma_x,
            tol=1e-30,
            max_iter=1,
            show_plot=False,
        )
