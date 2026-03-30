import numpy as np

from .stats_utils import standard_deviation

# --- colori colorblind safe ---
C_BAR = "#4878CF"  # blu       — barre istogramma
C_MEAN = "#D65F5F"  # rosso     — linea media
C_BAND_A = "#4878CF"  # blu       — banda σ_A
C_BAND_B = "#EE854A"  # arancione — banda σ_tot


def histogram(
    x,
    ddof=1,
    bins="auto",
    label="Dati",
    xlabel="Valore",
    ylabel=None,
    title="Istogramma",
    bin_ticks=True,
    tick_rotation=0,
    decimals=3,
    figsize=(8, 5),
    save_path=None,
    show_legend=True,
    show_mean=True,
    show_std=True,
    dpi=300,
    ax=None,
    xlim=None,
    ylim=None,
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
    ddof : int, default 1
        Gradi di libertà per il calcolo della deviazione
        standard (divisore N - ddof).
    bins : int o str, default "auto"
        Numero di bin o strategia numpy per la scelta automatica.
        Strategie disponibili: "auto", "sturges", "fd", "sqrt".
        Con "auto" numpy confronta Sturges e Freedman-Diaconis
        e sceglie quella che produce più bin.
    label : str, default "Dati"
        Etichetta delle barre nella legenda.
    xlabel : str, default "Valore"
        Etichetta dell'asse x.
    ylabel : str o None
        Etichetta dell'asse y. Se None viene impostata
        automaticamente a "Conteggi".
    title : str, default "Istogramma"
        Titolo del grafico.
    bin_ticks : bool, default True
        Se True posiziona i tick dell'asse x sui bordi dei bin
        e li formatta con il numero di decimali indicato da
        *decimals*.
    tick_rotation : int o float, default 0
        Angolo di rotazione (in gradi) delle etichette
        dell'asse x. Utile quando i tick si sovrappongono.
    decimals : int, default 3
        Numero di cifre decimali usato per formattare i tick
        dei bin e i valori di media e σ nella legenda.
    figsize : tuple, default (8, 5)
        Dimensioni della figura in pollici (larghezza, altezza).
    save_path : str o None
        Percorso per il salvataggio automatico della figura
        (es. "figures/hist.pdf"). Se None la figura non viene salvata.
        Il formato viene dedotto dall'estensione del file.
    show_legend : bool, default True
        Se True mostra la legenda sul grafico.
    show_mean : bool, default True
        Se True traccia una linea verticale tratteggiata
        in corrispondenza della media aritmetica dei dati.
    show_std : bool, default True
        Se True disegna una banda trasparente nell'intervallo
        [media - σ, media + σ], dove σ è la deviazione standard
        calcolata con il divisore N - ddof.
    dpi : int, default 300
        Risoluzione della figura, usata sia per la visualizzazione
        a schermo sia per il salvataggio su file.
    ax : matplotlib.axes.Axes o None
        Asse su cui disegnare. Se None la funzione crea una nuova
        figura con plt.subplots(); se viene passato un asse esistente,
        la funzione disegna su quello e risale alla figura madre
        con ax.get_figure().
    xlim : tuple o None
        Limiti dell'asse x come (xmin, xmax). Se None i limiti
        vengono determinati automaticamente da matplotlib.
    ylim : tuple o None
        Limiti dell'asse y come (ymin, ymax). Se None i limiti
        vengono determinati automaticamente da matplotlib.

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
        import matplotlib.pyplot as plt

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

    # --- formato decimali ---
    fmt = f".{decimals}f"

    # --- tick sui bordi del bin ---
    if bin_ticks:
        ax.set_xticks(bin_edges)
        ax.set_xticklabels([f"{edge:{fmt}}" for edge in bin_edges])

    # --- tick rotation ---
    if tick_rotation != 0:
        ax.tick_params(axis="x", rotation=tick_rotation)

    # --- statistiche ---
    mu = np.mean(x)
    sigma = standard_deviation(x, ddof)

    # --- linea media ---
    if show_mean:
        ax.axvline(
            mu,
            color=C_MEAN,
            linestyle="--",
            linewidth=1.2,
            label=rf"$\bar{{x}} = {mu:{fmt}}$",
        )

    # --- linee +- sigma ---
    if show_std:
        ax.axvspan(
            mu - sigma,
            mu + sigma,
            color="#D65F5F",
            alpha=0.15,
            label=rf"$\pm 1\sigma = {sigma:{fmt}}$",
        )

    # --- etichette ---
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel if ylabel is not None else "Conteggi")
    ax.set_title(title)

    ax.grid(True, axis="y", linestyle="-", linewidth=0.5, alpha=0.3, zorder=0)

    # --- legenda ---
    if show_legend:
        ax.legend(fontsize=9, framealpha=0.9)

    # --- limiti assi ---
    if xlim is not None:
        if len(xlim) != 2:
            raise ValueError(
                f"xlim deve avere 2 elementi (xmin, xmax) | ricevuti {len(xlim)}"
            )
        ax.set_xlim(xlim)

    if ylim is not None:
        if len(ylim) != 2:
            raise ValueError(
                f"ylim deve avere due elementi (ymin, ymax) | ricevuti: {len(ylim)}"
            )
        ax.set_ylim(ylim)

    # --- salvataggio ---
    if save_path is not None:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")

    return fig, ax
