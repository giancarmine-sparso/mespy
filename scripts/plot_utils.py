import matplotlib.pyplot as plt
import numpy as np

from script import stats_utils as my

# --- colori colorblind safe ---
C_BAR = "#4878CF"  # blu       — barre istogramma
C_MEAN = "#D65F5F"  # rosso     — linea media
C_BAND_A = "#4878CF"  # blu       — banda σ_A
C_BAND_B = "#EE854A"  # arancione — banda σ_tot


def histogram(
    x,
    bins="auto",
    label="Dati",
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
    """
    Istogramma di una distribuzione sperimentale.

    Disegna un istogramma a conteggi dei dati contenuti in x,
    con la possibilità di evidenziare la media aritmetica
    (linea tratteggiata) e la fascia ±1σ (banda trasparente).

    Se non viene fornito un asse (ax), la funzione crea
    autonomamente una figura; altrimenti disegna sull'asse
    ricevuto, permettendo composizioni con più subplot.

    Parametri
    ---------
    x : array-like
        Dati da rappresentare. Viene convertito internamente
        in un array NumPy float64 tramite np.asarray.
    bins : int o str, default "auto"
        Numero di bin o strategia numpy per la scelta automatica.
        Strategie disponibili: "auto", "sturges", "fd", "sqrt".
        Con "auto" numpy confronta Sturges e Freedman-Diaconis
        e sceglie quella che produce più bin.
    show_mean : bool, default True
        Se True traccia una linea verticale tratteggiata
        in corrispondenza della media aritmetica dei dati.
    show_std : bool, default True
        Se True disegna una banda trasparente nell'intervallo
        [media − σ, media + σ], dove σ è la deviazione standard
        descrittiva (divisore N).
    label : str, default "Dati"
        Etichetta delle barre nella legenda.
    xlabel : str, default "Valore"
        Etichetta dell'asse x.
    ylabel : str o None
        Etichetta dell'asse y. Se None viene impostata
        automaticamente a "Conteggi".
    title : str, default "Istogramma"
        Titolo del grafico.
    figsize : tuple, default (8, 5)
        Dimensioni della figura in pollici (larghezza, altezza).
    dpi : int, default 300
        Risoluzione della figura, usata sia per la visualizzazione
        a schermo sia per il salvataggio su file.
    save_path : str o None
        Percorso per il salvataggio automatico della figura
        (es. "figure/hist.pdf"). Se None la figura non viene salvata.
        Il formato viene dedotto dall'estensione del file.
    ax : matplotlib.axes.Axes o None
        Asse su cui disegnare. Se None la funzione crea una nuova
        figura con plt.subplots(); se viene passato un asse esistente,
        la funzione disegna su quello e risale alla figura madre
        con ax.get_figure().

    Restituisce
    -----------
    fig : matplotlib.figure.Figure
        La figura che contiene il grafico.
    ax  : matplotlib.axes.Axes
        L'asse su cui è stato disegnato l'istogramma.
    """
    x = np.asarray(x, dtype=float)

    # --- Figura ---
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi, constrained_layout=True)
    else:
        fig = ax.get_figure()

    # --- Istogramma ---
    counts, bin_edges, patches = ax.hist(
        x,
        bins=bins,
        density=False,
        color="#4878CF",
        edgecolor="white",
        alpha=0.85,
        label=label,
    )

    # --- statistiche ---
    mu = np.mean(x)
    sigma = my.standard_deviation(x)

    # --- linea media ---
    if show_mean:
        ax.axvline(
            mu,
            color=C_MEAN,
            linestyle="--",
            linewidth=1.2,
            label=rf"$\bar{{x}} = {mu:.3g}$",
        )

    # --- linee +- sigma ---
    if show_std:
        ax.axvspan(
            mu - sigma,
            mu + sigma,
            color="#D65F5F",
            alpha=0.15,
            label=rf"$\pm 1\sigma = {sigma:.3g}$",
        )

    # --- etichette ---
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel if ylabel is not None else "Conteggi")
    ax.set_title(title)

    ax.legend(fontsize=9, framealpha=0.9)

    # --- salvataggio ---
    if save_path is not None:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")

    return fig, ax
