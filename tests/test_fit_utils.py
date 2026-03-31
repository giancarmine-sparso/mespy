import matplotlib
import numpy as np
import pytest

from mech_lab_tools import lin_fit


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


def test_lin_fit_rejects_constant_x():
    with pytest.raises(ValueError, match="valori distinti"):
        lin_fit([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], [0.1, 0.1, 0.1], plot=False)


def test_lin_fit_rejects_scalar_axis_limits_when_plotting():
    x, y, sigma_y, _, _ = make_placebo_data()

    with pytest.raises(ValueError, match="xlim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, plot=True, xlim=1)

    with pytest.raises(ValueError, match="ylim deve essere una sequenza di 2 elementi"):
        lin_fit(x, y, sigma_y, plot=True, ylim=1)
