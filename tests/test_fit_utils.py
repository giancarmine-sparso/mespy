import matplotlib
import numpy as np
import pytest

from mespy import lin_fit


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


def test_lin_fit_returns_expected_parameters_and_plot():
    x, y, sigma_y, m_true, c_true = make_placebo_data()

    risultato = lin_fit(
        x,
        y,
        sigma_y,
        xlabel="x placebo",
        ylabel="y placebo",
        band=True,
        plot=True,
    )

    assert risultato["m"] == pytest.approx(m_true, abs=0.10)
    assert risultato["c"] == pytest.approx(c_true, abs=0.20)
    assert risultato["fig"] is not None
    assert len(risultato["fig"].axes) == 2
    assert len(risultato["r"]) == len(x)
    assert risultato["sigma_m"] > 0
    assert risultato["sigma_c"] > 0
    assert risultato["sigma_r"] > 0


def test_lin_fit_accepts_custom_plot_styling_kwargs():
    x, y, sigma_y, _, _ = make_placebo_data()

    risultato = lin_fit(
        x,
        y,
        sigma_y,
        plot=True,
        title="Fit placebo",
        title_fontsize=16,
        title_pad=12,
        legend_fontsize=11,
        legend_loc="upper left",
        show_grid=False,
        data_alpha=0.6,
        std_alpha=0.35,
    )

    ax_fit = risultato["fig"].axes[0]
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

    risultato_base = lin_fit(x, y, sigma_y, plot=False)
    risultato_sigma_x = lin_fit(x, y, sigma_y, sigma_x=sigma_x, plot=False)

    assert risultato_sigma_x["m"] == pytest.approx(m_true, abs=0.05)
    assert risultato_sigma_x["c"] == pytest.approx(c_true, abs=0.20)
    assert risultato_sigma_x["n_iter"] > 0
    assert risultato_sigma_x["sigma_m"] > risultato_base["sigma_m"]
    assert risultato_sigma_x["sigma_c"] > risultato_base["sigma_c"]


def test_lin_fit_without_plot_returns_no_figure():
    x, y, sigma_y, _, _ = make_placebo_data()

    risultato = lin_fit(x, y, sigma_y, plot=False)

    assert risultato["fig"] is None


def test_lin_fit_raises_on_invalid_input():
    with pytest.raises(ValueError, match="stessa lunghezza"):
        lin_fit([1.0, 2.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], plot=False)

    with pytest.raises(ValueError, match="almeno 3 punti"):
        lin_fit([1.0, 2.0], [1.0, 2.0], [0.1, 0.1], plot=False)


def test_lin_fit_rejects_non_finite_values():
    with pytest.raises(ValueError, match="valori finiti"):
        lin_fit([1.0, np.nan, 3.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], plot=False)

    with pytest.raises(ValueError, match="valori finiti"):
        lin_fit([1.0, 2.0, 3.0], [1.0, np.inf, 3.0], [0.1, 0.1, 0.1], plot=False)

    with pytest.raises(ValueError, match="valori finiti"):
        lin_fit([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.1, np.nan, 0.1], plot=False)


def test_lin_fit_rejects_non_positive_sigma():
    with pytest.raises(ValueError, match="strettamente positivi"):
        lin_fit([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.1, 0.0, 0.1], plot=False)

    with pytest.raises(ValueError, match="strettamente positivi"):
        lin_fit([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.1, -0.2, 0.1], plot=False)

    with pytest.raises(ValueError, match="sigma_x"):
        lin_fit(
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [0.1, 0.1, 0.1],
            sigma_x=[0.1, 0.0, 0.1],
            plot=False,
        )


def test_lin_fit_rejects_constant_x():
    with pytest.raises(ValueError, match="valori distinti"):
        lin_fit([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], plot=False)


def test_lin_fit_rejects_scalar_axis_limits_when_plotting():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="xlim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, plot=True, xlim=1)

    with pytest.raises(ValueError, match="ylim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, plot=True, ylim=1)
