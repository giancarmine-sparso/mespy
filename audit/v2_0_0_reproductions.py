"""Controesempi dell'audit v2, senza modificare dati o sorgenti.

Eseguire dalla root: .venv/bin/python audit/v2_0_0_reproductions.py
PRESENTE segnala il difetto osservato; ASSENTE indica che non si riproduce.
Questo script diagnostico non sostituisce i regression test proposti nel report.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import warnings


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    with tempfile.TemporaryDirectory(prefix="mespy-audit-") as cache:
        os.environ["MPLCONFIGDIR"] = cache
        os.environ["MPLBACKEND"] = "Agg"
        run()


def run() -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.optimize import minimize_scalar

    from mespy import histogram, lin_fit, variance, weighted_mean

    def finding(name, present, **values):
        print(f"{'PRESENTE' if present else 'ASSENTE'}: {name}")
        for key, value in values.items():
            print(f"  {key}: {value}")

    # Oracle esatto del criterio profilato x/y, caso isotropo TLS.
    x = np.array([0., 1., 2.])
    y = np.array([0., 0., 2.])
    expected_m = (1 + np.sqrt(37)) / 6
    expected_q = 2 / 3 - expected_m
    expected_chi2 = (7 - np.sqrt(37)) / 3

    def objective(m):
        return np.sum(((y - y.mean()) - m * (x - x.mean())) ** 2) / (1 + m * m)

    oracle = minimize_scalar(objective, bracket=(.5, 1., 2.), method="brent")
    np.testing.assert_allclose(oracle.x, expected_m, rtol=1e-7)
    np.testing.assert_allclose(oracle.fun, expected_chi2, rtol=1e-12)
    result = lin_fit(x, y, np.ones(3), sigma_x=np.ones(3), show_plot=False)
    finding(
        "sigma_x: convergenza senza minimo del criterio",
        not np.isclose(result.slope, expected_m, rtol=1e-7),
        attuale=(result.slope, result.intercept, result.chi2, result.converged),
        atteso=(expected_m, expected_q, expected_chi2),
    )

    # Gli scarti x sono rappresentabili anche dopo questa traslazione.
    x = np.arange(1., 7.)
    y = .8 * x + .3 + np.array([.05, -.04, .02, -.03, .01, 0.])
    sy = np.array([.05, .04, .06, .05, .03, .05])
    baseline = lin_fit(x, y, sy, show_plot=False)
    shifted = lin_fit(1e15 + x, y, sy, show_plot=False)
    finding(
        "offset x: residui e goodness-of-fit alterati",
        not np.allclose(baseline.residuals, shifted.residuals, rtol=1e-8, atol=1e-12),
        chi2=(baseline.chi2, shifted.chi2),
        p_value=(baseline.p_value, shifted.p_value),
        residui_shift=shifted.residuals,
    )

    for name, kwargs in [
        ("overflow x**2 evitabile", dict(
            x=1e155 + 1e140 * np.arange(6.), y=np.arange(6.), sigma_y=np.ones(6))),
        ("overflow somma pesi evitabile", dict(
            x=[0, 1, 2], y=[1, 2, 3], sigma_y=[1e-154] * 3)),
    ]:
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            error = None
            try:
                lin_fit(**kwargs, show_plot=False)
            except (ValueError, FloatingPointError) as exc:
                error = str(exc)
            finding(name, error is not None, errore=error,
                    warnings=[str(w.message) for w in records])

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        mean = weighted_mean([1e154, 2e154], [1e155, 1e155])
    finding("media pesata infinita, risultato atteso finito", not np.isfinite(mean),
            attuale=mean, atteso=1.5e154)

    w = np.array([1., 1., 2.])
    v1 = variance([1, 2, 3], w, ddof=1)
    v2 = variance([1, 2, 3], 10 * w, ddof=1)
    finding("ddof pesato ambiguo per pesi relativi", not np.isclose(v1, v2),
            w=v1, dieci_w=v2)

    invalid_ddof = variance([1, 2, 3], ddof=np.nan)
    finding("ddof NaN non rifiutato", np.isnan(invalid_ddof), attuale=invalid_ddof)

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        slope = lin_fit(np.array([0, 1, 2]) + 1j, [1, 2, 3], [1] * 3,
                        show_plot=False).slope
    finding("complessi convertiti perdendo la parte immaginaria", True,
            slope=slope, warnings=[str(w.message) for w in records])

    exact = lin_fit([0, 1, 2], [1, 3, 5], fit_method="residual", show_plot=False)
    finding("correlazione numerica con covarianza stimata nulla",
            exact.slope_std == 0 and np.isfinite(exact.correlation),
            slope_std=exact.slope_std, correlation=exact.correlation)
    mutated = False
    try:
        exact.residuals[0] = 999
        mutated = True
    except ValueError:
        pass
    finding("risultato frozen con residui modificabili", mutated,
            residui=exact.residuals, chi2=exact.chi2)

    for name, values, kwargs, expected_count in [
        ("istogramma costante perde i conteggi", [1, 1, 1], dict(bin_width=1), 3),
        ("istogramma include dati fuori range", [.1, .5, 1.5, 1.9],
         dict(bin_width=1, hist_range=(.4, 1.6)), 2),
    ]:
        fig, ax = histogram(values, show_band=False, **kwargs)
        try:
            count = sum(patch.get_height() for patch in ax.patches)
            finding(name, count != expected_count, attuale=count, atteso=expected_count)
        finally:
            plt.close(fig)

    # Oracoli y-only che confermano le formule già corrette.
    for method, kwargs, expected in [
        ("OLS", dict(fit_method="residual"), (1.5, -1 / 6, 1 / 12, 5 / 36, -1 / 12)),
        ("WLS", dict(sigma_y=[1, 2, 1], fit_method="absolute"),
         (1.5, -1 / 18, 1 / 2, 17 / 18, -1 / 2)),
    ]:
        r = lin_fit([0, 1, 2], [0, 1, 3], show_plot=False, **kwargs)
        actual = (r.slope, r.intercept, r.slope_std ** 2, r.intercept_std ** 2, r.covariance)
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-15)
        print(f"ORACLE {method}: parametri e covarianza corretti")


if __name__ == "__main__":
    main()
