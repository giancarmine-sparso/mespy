import numpy as np

from .plot_utils import C_BAND_B, C_BAR, C_MEAN, _validate_axis_limits
from .stats_utils import covariance, variance, weighted_mean


def lin_fit(
    x,
    y,
    sigma_y,
    xlabel="x [xu]",
    ylabel="y [uy]",
    dpi=300,
    band=True,
    plot=True,
    xlim=None,
    ylim=None,
    decimals=3,
    legend=True,
    legend_coefficient=False,
):
    """
    Fit lineare pesato y = m*x + c con propagazione delle incertezze.

    Stima pendenza e intercetta tramite minimi quadrati pesati
    (pesi w_i = 1/sigma_y_i^2), calcola le incertezze sui parametri,
    i residui e, opzionalmente, genera un grafico a due pannelli
    (dati + retta, residui).

    Parametri
    ---------
    x : array-like
        Ascisse dei punti sperimentali.
    y : array-like
        Ordinate dei punti sperimentali.
    sigma_y : array-like
        Incertezze sulle ordinate (strettamente positive).
    xlabel : str, default "x [xu]"
        Etichetta asse x nel grafico.
    ylabel : str, default "y [uy]"
        Etichetta asse y nel grafico.
    dpi : int, default 300
        Risoluzione della figura.
    band : bool, default True
        Se True, disegna la banda di incertezza sulla retta.
    plot : bool, default True
        Se True, genera il grafico; se False restituisce fig=None.
    xlim : tuple di 2 float, opzionale
        Limiti asse x (min, max) per il grafico.
    ylim : tuple di 2 float, opzionale
        Limiti asse y (min, max) per il pannello superiore.
    decimals : int, default 3
        Numero di cifre decimali per i coefficienti in legenda.
    legend : bool, default True
        Se True, mostra la legenda nel pannello superiore.
    legend_coefficient : bool, default False
        Se True, mostra m e c formattati nella legenda della retta.

    Restituisce
    -----------
    dict
        m, c : float — pendenza e intercetta
        sigma_m, sigma_c : float — incertezze su m e c
        cov_mc : float — covarianza tra m e c
        rho_mc : float — coefficiente di correlazione tra m e c
        r : ndarray — residui (y - m*x - c)
        sigma_r : float — deviazione standard dei residui
        fig : Figure o None — figura matplotlib (None se plot=False)
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    sigma_y = np.asarray(sigma_y, dtype=float)

    if not (len(x) == len(y) == len(sigma_y)):
        raise ValueError("x, y e sigma_y devono avere la stessa lunghezza")

    if not (
        np.all(np.isfinite(x))
        and np.all(np.isfinite(y))
        and np.all(np.isfinite(sigma_y))
    ):
        raise ValueError("x, y e sigma_y devono contenere solo valori finiti")

    n = len(x)
    if n < 3:
        raise ValueError("Servono almeno 3 punti per effettuare un fit lineare")

    if np.any(sigma_y <= 0):
        raise ValueError("sigma_y deve contenere solo valori strettamente positivi")

    # --- formato decimali ---
    fmt = f".{decimals}f"

    # --- pesi p_i = 1 / sigma_yi^2 ---
    w = 1.0 / sigma_y**2

    # --- stima dei parametri ---
    # m = Cov_w(x,y) / Var_w(x)
    var_x = variance(x, w)
    if not np.isfinite(var_x) or np.isclose(var_x, 0.0):
        raise ValueError("x deve contenere almeno due valori distinti")

    cov_xy = covariance(x, y, w)

    m = cov_xy / var_x  # (14.12)
    c = weighted_mean(y, w) - m * weighted_mean(x, w)  # (14.13)

    # --- incertezze sui parametri (14.19, 14.20, 14.21) ---
    # Var[m] = 1 / (Var[x] * sum_i p_i)
    sum_w = np.sum(w)
    var_m = 1.0 / (var_x * sum_w)  # (14.19)
    var_c = weighted_mean(x**2, w) / (var_x * sum_w)  # (14.20)

    cov_mc = -weighted_mean(x, w) / (var_x * sum_w)  # (14.21)

    sigma_m = np.sqrt(var_m)
    sigma_c = np.sqrt(var_c)
    rho_mc = cov_mc / (sigma_m * sigma_c)

    # --- residui e sigma dai residui (14.27) ---
    r = y - m * x - c
    sigma_r = np.sqrt(np.sum(r**2) / (n - 2))

    # --- grafico dati + retta di fit ---
    fig = None
    if plot:
        if xlim is not None:
            xlim = _validate_axis_limits(
                xlim,
                name="xlim",
                min_label="xmin",
                max_label="xmax",
            )

        if ylim is not None:
            ylim = _validate_axis_limits(
                ylim,
                name="ylim",
                min_label="ymin",
                max_label="ymax",
            )

        import matplotlib.pyplot as plt

        # figura con subplots
        fig, (ax_fit, ax_res) = plt.subplots(
            2,
            1,
            figsize=(8, 6),
            dpi=dpi,
            gridspec_kw={"height_ratios": [3, 1]},
            sharex=True,
            constrained_layout=True,
        )

        # pannello superiore: dati con error bar + retta
        ax_fit.errorbar(
            x,
            y,
            yerr=sigma_y,
            fmt="o",
            color=C_BAR,
            markersize=4,
            ecolor=C_BAR,
            elinewidth=1,
            capsize=3,
        )

        x_fit = np.linspace(x.min(), x.max(), 200)
        y_fit = m * x_fit + c
        fit_label = (
            f"Fit: m={m:{fmt}}, c={c:{fmt}}" if legend_coefficient else "Fit"
        )
        ax_fit.plot(x_fit, y_fit, color=C_MEAN, linewidth=1.5, label=fit_label)

        # banda +- sigma sulla retta
        if band:
            x_bar = weighted_mean(x, w)
            sigma_y_fit = np.sqrt(1.0 / sum_w + (x_fit - x_bar) ** 2 / (var_x * sum_w))
            ax_fit.fill_between(
                x_fit,
                y_fit - sigma_y_fit,
                y_fit + sigma_y_fit,
                color=C_BAND_B,
                alpha=0.20,
                label=r"$\pm 1 \sigma$ retta",
            )

        ax_fit.set_ylabel(ylabel)
        ax_fit.grid(True, axis="y", linestyle="-", linewidth=0.5, alpha=0.3, zorder=0)
        if legend:
            ax_fit.legend(fontsize=9, framealpha=0.9)

        # pannello inferiore: residui
        ax_res.errorbar(
            x,
            r,
            yerr=sigma_y,
            fmt="o",
            color=C_BAR,
            markersize=4,
            ecolor=C_BAR,
            elinewidth=1,
            capsize=3,
        )
        ax_res.axhline(0, color=C_MEAN, linewidth=1, linestyle="--")
        ax_res.set_xlabel(xlabel)
        ax_res.set_ylabel("Residui")

        # --- limiti assi ---
        if xlim is not None:
            ax_fit.set_xlim(xlim)
            ax_res.set_xlim(xlim)
        if ylim is not None:
            ax_fit.set_ylim(ylim)

    return {
        "m": m,
        "c": c,
        "sigma_m": sigma_m,
        "sigma_c": sigma_c,
        "cov_mc": cov_mc,
        "rho_mc": rho_mc,
        "r": r,
        "sigma_r": sigma_r,
        "fig": fig,
    }
