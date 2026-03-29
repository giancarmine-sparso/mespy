import numpy as np
import matplotlib.pyplot as plt

# colori colorblind safe
C_BAR = "#4878CF"  # blu    — barre istogramma
C_MEAN = "#D65F5F"  # rosso  — linea media
C_BAND_A = "#4878CF"  # blu    — banda σ_A
C_BAND_B = "#EE854A"  # arancione — banda σ_tot


def histogram(
    x,
    bins="auto",
    xlabel="Valore1",
    ylabel=None,
    title="Istogramma",
    figsize=(8, 5),
    save_path=None,
    show_mean=True,
    show_std=True,
    dpi=300,
    ax=None,
):

    x = np.asarray(x, dtype=float)

    # -- Figura --
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi, constrained_layout=True)
    else:
        fig = ax.get_figure()

    return 0
