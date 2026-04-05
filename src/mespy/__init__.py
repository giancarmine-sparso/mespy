from importlib.resources import files

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


def _register_style() -> None:
    """
    Registra lo stile 'mespy' nella libreria di stili di Matplotlib.

    Dopo l'import di mespy, l'utente può attivare lo stile con
    plt.style.use("mespy") da qualsiasi notebook o script.
    """
    from importlib.resources import as_file

    resource = files("mespy").joinpath("stylelib/mespy.mplstyle")
    with as_file(resource) as style_path:
        style_dict = mpl.rc_params_from_file(
            str(style_path),
            use_default_template=False,
        )
        mplstyle.library["mespy"] = style_dict
        mplstyle.available[:] = sorted(mplstyle.library.keys())


_register_style()


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
