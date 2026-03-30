import numpy as np

import mech_lab_tools as mlt

C_BAR = "#4878CF"  # blu       — barre istogramma
C_MEAN = "#D65F5F"  # rosso     — linea media
C_BAND_A = "#4878CF"  # blu       — banda σ_A
C_BAND_B = "#EE854A"  # arancione — banda σ_to


# fit lineare con incertezza su una variabile
def lin_fit(
    x, y, sigma_y, xlabel="x [xu]", ylabel="y [uy]", dpi=300, band=True, plot=True
):

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    sigma_y = np.asarray(sigma_y, dtype=float)

    if not (len(x) == len(y) == len(sigma_y)):
        raise ValueError("x, y e sigma_y devono avere la stessa lunghezza")

    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and np.all(np.isfinite(sigma_y))):
        raise ValueError("x, y e sigma_y devono contenere solo valori finiti")

    n = len(x)
    if n < 3:
        raise ValueError("Servono almeno 3 punti per effettuare un fit lineare")

    if np.any(sigma_y <= 0):
        raise ValueError("sigma_y deve contenere solo valori strettamente positivi")

    # --- pesi p_i = 1 / sigma_yi^2 ---
    w = 1.0 / sigma_y**2

    # --- stima dei parametri ---
    # m = Cov_w(x,y) / Var_w(x)
    var_x = mlt.variance(x, w)
    if not np.isfinite(var_x) or np.isclose(var_x, 0.0):
        raise ValueError("x deve contenere almeno due valori distinti")

    cov_xy = mlt.covariance(x, y, w)

    m = cov_xy / var_x  # (14.12)
    c = mlt.weighted_mean(y, w) - m * mlt.weighted_mean(x, w)  # (14.13)

    # --- incertezze sui parametri (14.19, 14.20, 14.21) ---
    # Var[m] = 1 / (Var[x] * sum_i p_i)
    sum_w = np.sum(w)
    var_m = 1.0 / (var_x * sum_w)  # (14.19)
    var_c = mlt.weighted_mean(x**2, w) / (var_x * sum_w)  # (14.20)

    cov_mc = -mlt.weighted_mean(x, w) / (var_x * sum_w)  # (14.21)

    sigma_m = np.sqrt(var_m)
    sigma_c = np.sqrt(var_c)
    rho_mc = cov_mc / (sigma_m * sigma_c)

    # --- residui e sigma dai residui (14.27) ---
    r = y - m * x - c
    sigma_r = np.sqrt(np.sum(r**2) / (n - 2))

    # --- grafico dati + retta di fit ---
    fig = None
    if plot:
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
        ax_fit.plot(x_fit, y_fit, color=C_MEAN, linewidth=1.5, label="Fit")

        # banda +- sigma sulla retta
        if band:
            x_bar = mlt.weighted_mean(x, w)
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
