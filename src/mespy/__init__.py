from importlib.resources import as_file, files

import matplotlib as mpl
import matplotlib.style as mplstyle

from .fit_utils import lin_fit
from .io_utils import load_csv
from .plot_utils import histogram
from .stats_utils import (
    covariance,
    median,
    standard_deviation,
    variance,
    weighted_mean,
)


def _register_styles() -> None:
    """Registra tutti gli stili .mplstyle bundled in mespy/stylelib.

    Dopo l'import di mespy, gli stili sono attivabili per nome con
    ``plt.style.use("mespy")``, ``plt.style.use("report")``, oppure
    impilati: ``plt.style.use(["mespy", "report"])``.
    """
    stylelib = files("mespy").joinpath("stylelib")
    for resource in stylelib.iterdir():
        name = resource.name
        if not name.endswith(".mplstyle"):
            continue
        style_name = name.removesuffix(".mplstyle")
        with as_file(resource) as path:
            style_dict = mpl.rc_params_from_file(str(path), use_default_template=False)
        mplstyle.library[style_name] = style_dict
    mplstyle.available[:] = sorted(mplstyle.library.keys())


_register_styles()

__all__ = [
    "load_csv",
    "median",
    "weighted_mean",
    "variance",
    "covariance",
    "standard_deviation",
    "lin_fit",
    "histogram",
]
