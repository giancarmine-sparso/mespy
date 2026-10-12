from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.stats import chi2 as chi2_distribution

from ._toml import _mespy_header, _write_toml_document
from .plot_utils import (
    _resolve_style,
    _style_context,
    _validate_axis_limits,
    _validate_decimals,
    _validate_figsize,
)
from .stats_utils import _as_float_vector, weighted_mean
from .stats_utils import covariance as weighted_covariance
from .stats_utils import variance as weighted_variance

if TYPE_CHECKING:
    from matplotlib.figure import Figure

FloatVector = NDArray[np.float64]
FitMethod = Literal["absolute", "residual"]

_LINEAR_FIT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class _LinearFitData:
    """Independent float64 copies, validated for the future OLS/WLS API."""

    x: FloatVector
    y: FloatVector
    sigma_y: FloatVector | None


def _real_fit_array(name: str, values: ArrayLike) -> FloatVector:
    """Convert real numeric input once, without discarding masks or imaginary parts."""
    if np.ma.isMaskedArray(values):
        raise TypeError(f"{name}: i masked array non sono supportati")
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: serve un array numerico regolare") from exc
    if raw.dtype.kind not in "biuf":
        raise TypeError(f"{name}: servono numeri reali, non complessi o altri tipi")
    try:
        with np.errstate(over="ignore", invalid="ignore"):
            result = np.array(raw, dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name}: valori non convertibili in float64") from exc
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name}: tutti i valori devono essere finiti in float64")
    return result


def _validate_linear_fit_data(
    x: ArrayLike, y: ArrayLike, sigma_y: ArrayLike | None = None
) -> _LinearFitData:
    """Validate shape, sample size and absolute vertical uncertainties."""
    x_values = _real_fit_array("x", x)
    y_values = _real_fit_array("y", y)
    for name, values in (("x", x_values), ("y", y_values)):
        if values.ndim != 1 or values.size == 0:
            raise ValueError(f"{name}: serve un vettore monodimensionale non vuoto")
    if x_values.shape != y_values.shape:
        raise ValueError("y: deve avere la stessa lunghezza di x")

    sigma_values = None
    if sigma_y is not None:
        sigma_values = _real_fit_array("sigma_y", sigma_y)
        if sigma_values.ndim == 0:
            sigma_values = np.full(x_values.shape, float(sigma_values))
        elif sigma_values.ndim != 1 or sigma_values.shape != x_values.shape:
            raise ValueError(
                "sigma_y: serve uno scalare o un vettore della lunghezza di x"
            )
        if np.any(sigma_values <= 0):
            raise ValueError(
                "sigma_y: le incertezze devono essere strettamente positive"
            )

    minimum = 3 if sigma_values is None else 2
    if x_values.size < minimum:
        raise ValueError(f"x, y: servono almeno {minimum} punti per questo fit")
    if np.all(x_values == x_values[0]):
        raise ValueError("x: servono almeno due valori distinti")
    return _LinearFitData(x_values, y_values, sigma_values)


def _fit_scaled_value(
    name: str,
    *factors: float,
    divisors: tuple[float, ...] = (),
    exponent: int = 0,
) -> float:
    """Multiply/divide via binary exponents, checking only the final quantity."""
    mantissa = 1.0
    for factor in factors:
        part, power = math.frexp(factor)
        mantissa *= part
        exponent += power
    for divisor in divisors:
        part, power = math.frexp(divisor)
        if part == 0:
            raise FloatingPointError(f"lin_fit: {name}, perdita di rango numerico")
        mantissa /= part
        exponent -= power
    try:
        result = math.ldexp(mantissa, exponent)
    except OverflowError as exc:
        raise FloatingPointError(
            f"lin_fit: {name} non rappresentabile in float64"
        ) from exc
    if not math.isfinite(result) or (result == 0 and mantissa != 0):
        raise FloatingPointError(f"lin_fit: {name} non rappresentabile in float64")
    return result


def _fit_sum_parts(*terms: tuple[float, int]) -> tuple[float, int]:
    """Sum in a common binary scale, retaining quantities below float64 range."""
    parts = []
    for value, exponent in terms:
        if value != 0:
            mantissa, power = math.frexp(value)
            parts.append((mantissa, power + exponent))
    while parts:
        common = max(power for _, power in parts)
        scaled = []
        deferred = []
        for mantissa, power in parts:
            value = math.ldexp(mantissa, power - common)
            if value == 0:
                deferred.append((mantissa, power))
            else:
                scaled.append(value)
        total = math.fsum(scaled)
        if total != 0:
            return total, common
        # Exact cancellation of large terms may expose much smaller ones.
        parts = deferred
    return 0.0, 0


def _fit_scaled_sum(name: str, *terms: tuple[float, int]) -> float:
    """Restore a scaled sum only after cancellation has taken place."""
    total, common = _fit_sum_parts(*terms)
    return _fit_scaled_value(name, total, exponent=common)


def _fit_restore(name: str, values: FloatVector, exponent: int) -> FloatVector:
    """Restore vector units without emitting NumPy overflow/underflow warnings."""
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        restored = np.ldexp(values, exponent)
    if not np.all(np.isfinite(restored)) or np.any((values != 0) & (restored == 0)):
        raise FloatingPointError(f"lin_fit: {name} non rappresentabili in float64")
    return restored


@dataclass(frozen=True, slots=True)
class _FitLocalAxis:
    """Coordinate offsets in units of 2**exponent; the original origin is retained."""

    origin: float
    exponent: int
    offsets: FloatVector
    mean: float
    correction: float
    centered: FloatVector

    def deviations(self, values: FloatVector) -> FloatVector:
        # Prefer direct subtraction to preserve small representable differences
        # near a large origin. Only opposing extreme signs need prescaling.
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            differences = values - self.origin
            local = np.ldexp(differences, -self.exponent)
            if not np.all(np.isfinite(differences)):
                local = np.ldexp(values, -self.exponent) - math.ldexp(
                    self.origin, -self.exponent
                )
        if not np.all(np.isfinite(local)):
            raise FloatingPointError(
                "lin_fit: x della previsione fuori dalla scala locale"
            )
        return (local - self.mean) - self.correction


def _fit_local_axis(
    values: FloatVector, weights: FloatVector, sum_weights: float
) -> _FitLocalAxis:
    origin = float(values[0])
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        differences = values - origin
    prescale = 0
    if not np.all(np.isfinite(differences)):
        # Halving finite float64 inputs makes even a full-range difference safe.
        differences = np.ldexp(values, -1) - math.ldexp(origin, -1)
        prescale = 1
    largest = float(np.max(np.abs(differences)))
    exponent = math.frexp(largest)[1] if largest else 0
    offsets = np.ldexp(differences, -exponent)
    mean = math.fsum(float(w * v) for w, v in zip(weights, offsets)) / sum_weights
    centered = offsets - mean
    correction = (
        math.fsum(float(w * v) for w, v in zip(weights, centered)) / sum_weights
    )
    centered -= correction
    return _FitLocalAxis(
        origin, exponent + prescale, offsets, mean, correction, centered
    )


def _fit_norm(values: FloatVector) -> float:
    """Euclidean norm with no premature squaring in the original units."""
    largest = float(np.max(np.abs(values)))
    if largest == 0:
        return 0.0
    scaled = values / largest
    return _fit_scaled_value(
        "norma", largest, math.sqrt(math.fsum(float(v * v) for v in scaled))
    )


@dataclass(frozen=True, slots=True)
class _LinearFitCore:
    """Numerical state only; it does not construct public results or figures."""

    slope: float
    intercept: float
    slope_std: float
    intercept_std: float
    covariance: float
    correlation: float | None
    residuals: FloatVector
    residual_std: float | None
    chi2: float | None
    reduced_chi2: float | None
    p_value: float | None
    dof: int
    fit_method: Literal["ols", "wls"]
    x_axis: _FitLocalAxis
    y_axis: _FitLocalAxis
    local_slope: float
    center_std: float

    def predict(self, x: FloatVector) -> FloatVector:
        deviations = self.x_axis.deviations(x)
        offsets = (
            self.y_axis.mean + self.y_axis.correction + self.local_slope * deviations
        )
        return np.array(
            [
                _fit_scaled_sum(
                    "previsione",
                    (self.y_axis.origin, 0),
                    (float(v), self.y_axis.exponent),
                )
                for v in offsets
            ]
        )

    def mean_std(self, x: FloatVector) -> FloatVector:
        """One standard uncertainty of the predicted mean, evaluated locally."""
        deviations = self.x_axis.deviations(x)
        return np.array(
            [
                math.hypot(
                    self.center_std,
                    _fit_scaled_value(
                        "banda", self.slope_std, float(v), exponent=self.x_axis.exponent
                    ),
                )
                for v in deviations
            ]
        )


def _solve_linear_fit(data: _LinearFitData) -> _LinearFitCore:
    """Solve OLS or absolute WLS in O(N), using centered/scaled local coordinates.

    No generic solver, matrix inverse or public statistics helper participates.
    Sigma normalization retains its absolute scale for uncertainties and chi2.
    Quantities that cannot be represented raise a contextual FloatingPointError.
    """
    if data.sigma_y is None:
        sigma_scale = 1.0
        weights = np.ones_like(data.x)
    else:
        sigma_scale = float(np.min(data.sigma_y))
        with np.errstate(under="ignore"):
            weights = np.square(sigma_scale / data.sigma_y)
        if np.any(weights == 0):
            raise FloatingPointError(
                "lin_fit: sigma_y, pesi positivi ridotti a zero dalla normalizzazione"
            )

    sum_weights = math.fsum(float(w) for w in weights)
    x_axis = _fit_local_axis(data.x, weights, sum_weights)
    y_axis = _fit_local_axis(data.y, weights, sum_weights)
    root_weights = np.sqrt(weights)
    weighted_x = root_weights * x_axis.centered
    weighted_y = root_weights * y_axis.centered
    largest_x = float(np.max(np.abs(weighted_x)))
    if largest_x == 0:
        raise FloatingPointError("lin_fit: x, perdita di rango numerico")
    scaled_x = weighted_x / largest_x
    moment_xx = math.fsum(float(v * v) for v in scaled_x)
    norm_x = _fit_scaled_value("momento centrato x", largest_x, math.sqrt(moment_xx))

    largest_y = float(np.max(np.abs(weighted_y)))
    if largest_y == 0:
        local_slope = 0.0
    else:
        moment_xy = math.fsum(
            float(a * b) for a, b in zip(scaled_x, weighted_y / largest_y)
        )
        local_slope = _fit_scaled_value(
            "slope locale", moment_xy, largest_y, divisors=(largest_x, moment_xx)
        )
    slope = _fit_scaled_value(
        "slope", local_slope, exponent=y_axis.exponent - x_axis.exponent
    )

    x_mean, x_mean_exponent = _fit_sum_parts(
        (x_axis.origin, 0),
        (x_axis.mean, x_axis.exponent),
        (x_axis.correction, x_axis.exponent),
    )
    # Form the product in a common scale, so an overflowing m*x0 need not
    # overflow a representable intercept after cancellation with y0.
    slope_mantissa, slope_power = math.frexp(slope)
    origin_mantissa, origin_power = math.frexp(x_axis.origin)
    intercept = _fit_scaled_sum(
        "intercept",
        (y_axis.origin, 0),
        (-slope_mantissa * origin_mantissa, slope_power + origin_power),
        (y_axis.mean, y_axis.exponent),
        (y_axis.correction, y_axis.exponent),
        (-local_slope * x_axis.mean, y_axis.exponent),
        (-local_slope * x_axis.correction, y_axis.exponent),
    )
    local_residuals = y_axis.centered - local_slope * x_axis.centered
    residuals = _fit_restore("residui", local_residuals, y_axis.exponent)
    dof = data.x.size - 2
    residual_norm = _fit_norm(local_residuals)
    residual_std = (
        _fit_scaled_value(
            "residual_std",
            residual_norm,
            divisors=(math.sqrt(dof),),
            exponent=y_axis.exponent,
        )
        if dof > 0
        else None
    )
    uncertainty_scale = residual_std if data.sigma_y is None else sigma_scale
    assert uncertainty_scale is not None  # OLS validation guarantees dof > 0.
    slope_std = _fit_scaled_value(
        "slope_std", uncertainty_scale, divisors=(norm_x,), exponent=-x_axis.exponent
    )
    center_std = _fit_scaled_value(
        "incertezza al baricentro",
        uncertainty_scale,
        divisors=(math.sqrt(sum_weights),),
    )
    offset_std = _fit_scaled_value(
        "incertezza dell'intercetta", slope_std, x_mean, exponent=x_mean_exponent
    )
    intercept_std = math.hypot(center_std, offset_std)
    if not math.isfinite(intercept_std):
        raise FloatingPointError(
            "lin_fit: intercept_std non rappresentabile in float64"
        )
    covariance = _fit_scaled_value(
        "covariance", -x_mean, slope_std, slope_std, exponent=x_mean_exponent
    )
    correlation = (
        -offset_std / intercept_std if slope_std > 0 and intercept_std > 0 else None
    )

    chi2 = reduced_chi2 = p_value = None
    if data.sigma_y is not None:
        # Weighted norm stays local; even residual/sigma need not be squared
        # until its units have been accounted for through binary exponents.
        weighted_residual_norm = _fit_norm(root_weights * local_residuals)
        chi2 = _fit_scaled_value(
            "chi2",
            weighted_residual_norm,
            weighted_residual_norm,
            divisors=(sigma_scale, sigma_scale),
            exponent=2 * y_axis.exponent,
        )
        if dof > 0:
            reduced_chi2 = _fit_scaled_value(
                "reduced_chi2", chi2, divisors=(float(dof),)
            )
            p_value = float(chi2_distribution.sf(chi2, dof))

    return _LinearFitCore(
        slope,
        intercept,
        slope_std,
        intercept_std,
        covariance,
        correlation,
        residuals,
        residual_std,
        chi2,
        reduced_chi2,
        p_value,
        dof,
        "ols" if data.sigma_y is None else "wls",
        x_axis,
        y_axis,
        local_slope,
        center_std,
    )


@dataclass(frozen=True, slots=True)
class LinearFitResult:
    """Immutable result of a linear fit."""

    slope: float
    intercept: float
    slope_std: float
    intercept_std: float
    covariance: float
    correlation: float
    residuals: FloatVector
    residual_std: float
    chi2: float
    reduced_chi2: float
    dof: int
    iterations: int
    converged: bool
    figure: Figure | None
    fit_method: FitMethod = "absolute"
    scale_factor: float = 1.0
    p_value: float = math.nan

    def to_toml(self, path: str | Path) -> Path:
        """
        Save the numerical result of the fit to a TOML file.

        The file contains parameters, uncertainties, diagnostics and
        residuals, plus a ``[mespy]`` table with ``schema_version``,
        ``mespy_version`` and ``result_type``. The ``figure`` field is
        never saved.

        Parameters
        ----------
        path : str or Path
            Destination path. If it has no extension, ``.toml`` is
            appended. An existing file is overwritten atomically.

        Returns
        -------
        Path
            Path of the written file.
        """
        return _write_toml_document(_linear_fit_document(self), path)


def _linear_fit_document(result: LinearFitResult) -> dict[str, Any]:
    """Convert *result* into a TOML document made of native Python types only."""
    return {
        "mespy": _mespy_header("linear_fit", _LINEAR_FIT_SCHEMA_VERSION),
        "fit": {
            "fit_method": str(result.fit_method),
            "slope": float(result.slope),
            "slope_std": float(result.slope_std),
            "intercept": float(result.intercept),
            "intercept_std": float(result.intercept_std),
            "covariance": float(result.covariance),
            "correlation": float(result.correlation),
            "scale_factor": float(result.scale_factor),
        },
        "diagnostics": {
            "chi2": float(result.chi2),
            "reduced_chi2": float(result.reduced_chi2),
            "dof": int(result.dof),
            "p_value": float(result.p_value),
            "residual_std": float(result.residual_std),
            "iterations": int(result.iterations),
            "converged": bool(result.converged),
        },
        "residuals": {
            "values": np.asarray(result.residuals, dtype=float).tolist(),
        },
    }


def _validate_positive_vector(
    name: str,
    values: ArrayLike,
    *,
    expected_shape: tuple[int, ...] | None = None,
) -> FloatVector:
    vector = _as_float_vector(name, values)

    if expected_shape is not None and vector.shape != expected_shape:
        raise ValueError(f"{name} deve avere la stessa lunghezza di x, y e sigma_y")

    if np.any(vector <= 0):
        raise ValueError(f"{name} deve contenere solo valori strettamente positivi")

    return vector


def _validate_positive_scalar(name: str, value: float) -> float:
    try:
        is_valid = bool(np.isfinite(value)) and value > 0
    except (TypeError, ValueError):
        is_valid = False

    if not is_valid:
        raise ValueError(f"{name} deve essere un numero finito strettamente positivo")
    return float(value)


def _validate_max_iter(max_iter: int) -> int:
    if isinstance(max_iter, bool) or not isinstance(max_iter, (int, np.integer)):
        raise ValueError("max_iter deve essere un intero positivo")

    max_iter_int = int(max_iter)
    if max_iter_int <= 0:
        raise ValueError("max_iter deve essere un intero positivo")

    return max_iter_int


def _validate_fit_method(fit_method: str) -> FitMethod:
    if fit_method not in ("absolute", "residual"):
        raise ValueError("fit_method deve essere 'absolute' oppure 'residual'")

    return cast(FitMethod, fit_method)


def _fit_coefficients(
    x: FloatVector,
    y: FloatVector,
    weights: FloatVector,
) -> tuple[float, float, float]:
    # Condizione esatta e invariante di scala: un confronto con tolleranza
    # assoluta sulla varianza dipenderebbe dall'unita di misura di x.
    if np.all(x == x[0]):
        raise ValueError("x deve contenere almeno due valori distinti")

    var_x = weighted_variance(x, weights)
    if not np.isfinite(var_x) or var_x <= 0.0:
        raise ValueError(
            "la varianza di x non è rappresentabile in float64 "
            "(valori di x troppo piccoli o troppo grandi in modulo)"
        )

    cov_xy = weighted_covariance(x, y, weights)
    slope = cov_xy / var_x
    intercept = weighted_mean(y, weights) - slope * weighted_mean(x, weights)
    return float(slope), float(intercept), float(var_x)


def lin_fit(
    x: ArrayLike,
    y: ArrayLike,
    sigma_y: ArrayLike | None = None,
    *,
    fit_method: FitMethod | None = None,
    sigma_x: ArrayLike | None = None,
    tol: float = 1e-10,
    max_iter: int = 100,
    style: str | None = "mespy",
    xlabel: str = "x [xu]",
    ylabel: str = "y [uy]",
    residuals_label: str = "Residuals",
    normalize_residuals: bool = False,
    band_label: str = r"$\pm 1 \sigma$ retta",
    fit_label: str = r"Fit",
    title: str | None = None,
    decimals: int = 3,
    show_plot: bool = True,
    show_band: bool = True,
    show_legend: bool = True,
    show_fit_params: bool = False,
    show_grid: bool = True,
    xlim: ArrayLike | None = None,
    ylim: ArrayLike | None = None,
    figsize: ArrayLike | None = None,
    dpi: int | None = None,
    save_path: str | None = None,
    title_fontsize: int | float | None = None,
    title_pad: int | float | None = None,
    legend_fontsize: int | float | None = None,
    legend_loc: str | None = None,
    point_color: str | None = None,  # default: "C0" dal prop_cycle attivo
    fit_color: str | None = None,  # default: "C1" dal prop_cycle attivo
    band_color: str
    | None = None,  # default: "C1" dal prop_cycle attivo (o "C2", vedi sotto)
    res_line_color: str | None = None,
    data_alpha: float = 1.0,  # nessun rcParam equivalente
    band_alpha: float = 0.20,  # nessun rcParam equivalente
    grid_alpha: float | None = None,  # gestito da grid.alpha nello stile
) -> LinearFitResult:
    """
    Linear fit ``y = m * x + c`` with uncertainty propagation.

    Estimates slope and intercept through weighted least squares. In
    ``fit_method="absolute"`` mode, it uses absolute uncertainties on
    ``y`` and weights ``w_i = 1 / sigma_y_i**2``. In
    ``fit_method="residual"`` mode, it estimates the uncertainty scale
    from the residuals: without
    ``sigma_y`` this is the standard unweighted linear fit with one
    common vertical uncertainty estimated after the fit; with
    ``sigma_y`` the provided uncertainties define relative weights and
    the final covariance is scaled by the observed reduced chi-squared.
    If ``sigma_x`` is provided, the function iteratively updates the
    effective variance ``sigma_eff**2 = sigma_y**2 + m**2 * sigma_x**2``
    until the slope converges. It computes parameter uncertainties,
    covariance, residuals, and fit diagnostics (``chi2`` and reduced
    ``chi2``). Optionally, it generates a two-panel plot (data + fit
    line, regular or normalized residuals).

    Aesthetic parameters with an ``rcParams`` counterpart (``figsize``,
    ``dpi``, colors, grid, title, legend) are managed by the
    ``mespy.mplstyle`` style file when ``style="mespy"``. Passing an
    explicit value to the corresponding function parameters overrides
    the style for that call only.

    Parameters
    ----------
    x : array-like
        Values of the independent variable.
    y : array-like
        Values of the dependent variable; must have the same length as
        ``x``.
    sigma_y : array-like or None, optional
        Positive uncertainties on ``y``; must have the same length as
        ``x``. Required when ``fit_method="absolute"``. If omitted with
        ``fit_method="residual"``, the fit uses equal weights and
        estimates one common vertical uncertainty from the residuals.
        If omitted while ``fit_method`` is left unspecified, the call
        falls back to ``"residual"`` and emits a ``UserWarning``.
    fit_method : {"absolute", "residual"} or None, optional
        Uncertainty model. ``"absolute"`` treats ``sigma_y`` and
        ``sigma_x`` as absolute input uncertainties. ``"residual"``
        estimates one global scale factor from the residuals and
        applies it to parameter uncertainties, plotted error bars,
        normalized residuals, and the fit band. ``None`` means
        ``"absolute"``, with a fallback to ``"residual"`` (and a
        ``UserWarning``) when ``sigma_y`` is not provided
        (default ``None``).
    sigma_x : array-like or None, optional
        Positive uncertainties on ``x``. If provided, enables the
        effective variance update and iterative slope refinement
        (default ``None``).
    tol : float, optional
        Relative tolerance for the slope change between successive
        iterations; used only when ``sigma_x`` is provided
        (default ``1e-10``).
    max_iter : int, optional
        Maximum number of iterations for convergence; used only when
        ``sigma_x`` is provided (default ``100``).
    style : str or None, optional
        Name of the matplotlib style sheet to apply. ``None`` leaves
        the current style unchanged (default ``"mespy"``).
    xlabel : str, optional
        Label for the x-axis (default ``"x [xu]"``).
    ylabel : str, optional
        Label for the y-axis (default ``"y [uy]"``).
    residuals_label : str, optional
        Label for the residuals y-axis in the lower panel
        (default ``"Residuals"``).
    normalize_residuals : bool, optional
        If ``True``, the lower panel plots residuals normalized by
        ``sigma_eff``. This affects only the plot: the
        ``LinearFitResult.residuals`` field always contains the
        physical residuals ``y_i - (m * x_i + c)`` (default ``False``).
    band_label : str, optional
        Legend label for the +/-1 sigma band around the fit line;
        used only when ``show_band=True``
        (default ``"$\\pm 1 \\sigma$ retta"``).
    fit_label : str, optional
        Legend label for the fit line when ``show_fit_params=False``.
        If ``show_fit_params=True``, the legend label is generated
        automatically from slope and intercept (default ``"Fit"``).
    title : str or None, optional
        Plot title. ``None`` generates an automatic title
        (default ``None``).
    decimals : int, optional
        Number of decimal digits in the values displayed on the plot;
        must be between 0 and 20 (default ``3``).
    show_plot : bool, optional
        If ``True``, generates and shows the two-panel plot
        (default ``True``).
    show_band : bool, optional
        If ``True``, draws the +/-1 sigma band around the fit line
        (default ``True``).
    show_legend : bool, optional
        If ``True``, shows the legend (default ``True``).
    show_fit_params : bool, optional
        If ``True``, adds slope and intercept to the legend
        (default ``False``).
    show_grid : bool, optional
        If ``True``, shows the grid (default ``True``).
    xlim : array-like or None, optional
        Pair ``(min, max)`` for the x-axis limits. ``None`` uses
        automatic limits (default ``None``).
    ylim : array-like or None, optional
        Pair ``(min, max)`` for the y-axis limits. ``None`` uses
        automatic limits (default ``None``).
    figsize : array-like or None, optional
        Pair ``(width, height)`` in inches. ``None`` uses the value
        from the style file (default ``None``).
    dpi : int or None, optional
        Figure resolution in DPI. ``None`` uses the value from the
        style file (default ``None``).
    save_path : str or None, optional
        Path where the figure is automatically saved at the end.
        ``None`` disables saving (default ``None``).
    title_fontsize : int or float or None, optional
        Title font size. ``None`` uses the value from the style file
        (default ``None``).
    title_pad : int or float or None, optional
        Spacing in points between the title and the plot. ``None``
        uses the value from the style file (default ``None``).
    legend_fontsize : int or float or None, optional
        Legend font size. ``None`` uses the value from the style file
        (default ``None``).
    legend_loc : str or None, optional
        Legend position (for example ``"upper right"``). ``None`` uses
        the value from the style file (default ``None``).
    point_color : str or None, optional
        Color of the data points. ``None`` uses the color from the
        style file (default ``None``).
    fit_color : str or None, optional
        Color of the fit line. ``None`` uses the second color in the
        active style color cycle (default ``None``).
    band_color : str or None, optional
        Color of the +/-1 sigma band around the line. ``None`` uses
        the second color in the active style color cycle
        (default ``None``).
    res_line_color : str or None, optional
        Color of the zero reference line in the residuals panel.
        ``None`` uses the fit line color (default ``None``).
    data_alpha : float, optional
        Opacity of the data points, between 0 and 1 (default ``1.0``).
    band_alpha : float, optional
        Opacity of the +/-1 sigma band, between 0 and 1
        (default ``0.20``).
    grid_alpha : float or None, optional
        Grid opacity, between 0 and 1. ``None`` uses the value from
        the style file (default ``None``).

    Returns
    -------
    LinearFitResult
        Frozen dataclass with the following fields:

        - ``slope`` : float - estimated slope ``m``.
        - ``intercept`` : float - estimated intercept ``c``.
        - ``slope_std`` : float - uncertainty on the slope.
        - ``intercept_std`` : float - uncertainty on the intercept.
        - ``covariance`` : float - covariance between slope and intercept.
        - ``correlation`` : float - correlation between slope and intercept.
        - ``residuals`` : numpy.ndarray - residuals ``y_i - (m * x_i + c)``.
        - ``residual_std`` : float - standard deviation of the residuals.
        - ``chi2`` : float - chi-squared of the fit.
        - ``reduced_chi2`` : float - reduced chi-squared (``chi2 / dof``).
        - ``dof`` : int - degrees of freedom (``n - 2``).
        - ``iterations`` : int - number of performed iterations
          (0 if ``sigma_x`` is ``None``).
        - ``converged`` : bool - ``True`` if the fit converged.
        - ``figure`` : matplotlib.figure.Figure or None - generated
          figure, ``None`` if ``show_plot=False``.
        - ``fit_method`` : {"absolute", "residual"} - uncertainty model used.
        - ``scale_factor`` : float - factor applied to the input
          uncertainties in residual-scale mode (``1`` in absolute mode).
        - ``p_value`` : float - probability of obtaining a chi-squared
          greater than or equal to the observed one, ``P(chi2_dof >= chi2)``.
          ``nan`` with ``fit_method="residual"``, where ``chi2`` equals
          ``dof`` by construction and the test is not defined.

    Warns
    -----
    UserWarning
        If ``fit_method`` is not specified and ``sigma_y`` is missing:
        the call falls back to ``fit_method="residual"``.

    Raises
    ------
    ValueError
        If ``fit_method`` is not ``"absolute"``, ``"residual"`` or ``None``.
    ValueError
        If ``sigma_y`` is missing when ``fit_method="absolute"`` is given
        explicitly.
    ValueError
        If ``sigma_x`` is provided without ``sigma_y``.
    ValueError
        If ``x``, ``y``, and ``sigma_y`` have different lengths.
    ValueError
        If the number of points is smaller than 3.
    ValueError
        If ``sigma_y`` or ``sigma_x`` contains non-positive values.
    ValueError
        If the shape of ``sigma_x`` does not match ``x``.
    ValueError
        If ``decimals`` is not an integer or is outside the range
        ``[0, 20]``.
    ValueError
        If ``tol`` is not finite or is not positive.
    ValueError
        If ``max_iter`` is not positive.
    ValueError
        If ``xlim`` or ``ylim`` is not a finite two-element sequence.
    ValueError
        If ``save_path`` is specified but ``show_plot=False``.
    ValueError
        If ``x`` contains fewer than 2 distinct values.
    ValueError
        If the weighted variance of ``x`` underflows or overflows in
        ``float64`` (values of ``x`` extremely small or large in magnitude).
    RuntimeError
        If the fit does not converge within ``max_iter`` iterations
        (only when ``sigma_x`` is provided).
    """
    if fit_method is None:
        if sigma_y is not None:
            fit_method = "absolute"
        elif sigma_x is not None:
            raise ValueError("sigma_x richiede sigma_y")
        else:
            warnings.warn(
                "sigma_y non fornito: lin_fit usa fit_method='residual' e stima "
                "l'incertezza dai residui. Passa fit_method='residual' "
                "esplicitamente per non vedere questo avviso.",
                UserWarning,
                stacklevel=2,
            )
            fit_method = "residual"

    fit_method = _validate_fit_method(fit_method)
    use_residual_scale = fit_method == "residual"

    x_values = _as_float_vector("x", x)
    y_values = _as_float_vector("y", y)

    if sigma_y is None:
        if not use_residual_scale:
            raise ValueError("sigma_y è obbligatorio quando fit_method='absolute'")
        if sigma_x is not None:
            raise ValueError(
                "sigma_x può essere usato con fit_method='residual' solo se sigma_y è presente"
            )
        sigma_y_values = np.ones_like(x_values)
    else:
        sigma_y_values = _validate_positive_vector("sigma_y", sigma_y)

    if x_values.shape != y_values.shape or x_values.shape != sigma_y_values.shape:
        raise ValueError("x, y e sigma_y devono avere la stessa lunghezza")

    n = x_values.size
    if n < 3:
        raise ValueError("Servono almeno 3 punti per effettuare un fit lineare")

    decimals = _validate_decimals(decimals)

    tol_value = _validate_positive_scalar("tol", tol)
    max_iter_value = _validate_max_iter(max_iter)

    use_sigma_x = sigma_x is not None
    sigma_x_values: FloatVector | None = None
    if use_sigma_x:
        sigma_x_values = _validate_positive_vector(
            "sigma_x",
            sigma_x,
            expected_shape=x_values.shape,
        )

    sigma_y2 = sigma_y_values**2
    sigma_x2 = sigma_x_values**2 if sigma_x_values is not None else None
    weights = 1.0 / sigma_y2

    slope, intercept, var_x = _fit_coefficients(x_values, y_values, weights)
    iterations = 0
    converged = not use_sigma_x

    if use_sigma_x:
        previous_slope = slope

        for _ in range(max_iter_value):
            sigma_eff2 = sigma_y2 + slope**2 * sigma_x2
            weights = 1.0 / sigma_eff2
            iterations += 1

            next_slope, next_intercept, next_var_x = _fit_coefficients(
                x_values,
                y_values,
                weights,
            )

            rel_change = abs(next_slope - previous_slope) / max(
                abs(next_slope),
                1e-300,
            )
            if rel_change < tol_value:
                slope = next_slope
                intercept = next_intercept
                var_x = next_var_x
                converged = True
                break

            previous_slope = next_slope
            slope = next_slope
            intercept = next_intercept
            var_x = next_var_x
        else:
            raise RuntimeError(
                f"Il fit lineare non converge entro max_iter={max_iter_value}"
            )

    residuals = y_values - slope * x_values - intercept
    dof = n - 2
    residual_std = float(np.sqrt(np.sum(residuals**2) / dof))

    raw_sigma_fit2 = (
        sigma_y2 if sigma_x2 is None else sigma_y2 + slope**2 * sigma_x2
    )
    raw_chi2 = float(np.sum((residuals**2) / raw_sigma_fit2))
    raw_reduced_chi2 = float(raw_chi2 / dof)

    covariance_scale = raw_reduced_chi2 if use_residual_scale else 1.0
    scale_factor = float(np.sqrt(covariance_scale))

    sum_w = float(np.sum(weights))
    base_var_m = 1.0 / (var_x * sum_w)
    base_var_c = weighted_mean(x_values**2, weights) / (var_x * sum_w)
    base_cov_mc = -weighted_mean(x_values, weights) / (var_x * sum_w)

    base_sigma_m = float(np.sqrt(base_var_m))
    base_sigma_c = float(np.sqrt(base_var_c))
    rho_mc = float(base_cov_mc / (base_sigma_m * base_sigma_c))

    var_m = base_var_m * covariance_scale
    var_c = base_var_c * covariance_scale
    cov_mc = base_cov_mc * covariance_scale

    sigma_m = float(np.sqrt(var_m))
    sigma_c = float(np.sqrt(var_c))

    sigma_fit2 = raw_sigma_fit2 * covariance_scale
    if use_residual_scale:
        if covariance_scale > 0:
            chi2 = float(raw_chi2 / covariance_scale)
            reduced_chi2 = float(chi2 / dof)
        else:
            chi2 = 0.0
            reduced_chi2 = 0.0
    else:
        chi2 = raw_chi2
        reduced_chi2 = raw_reduced_chi2

    # Con la scala stimata dai residui il chi2 vale dof per costruzione:
    # il test di bonta del fit non e definito.
    p_value = (
        math.nan if use_residual_scale else float(chi2_distribution.sf(chi2, dof))
    )

    normalized_residuals = np.divide(
        residuals,
        np.sqrt(sigma_fit2),
        out=np.zeros_like(residuals),
        where=sigma_fit2 > 0,
    )
    plot_sigma_y_values = sigma_y_values * scale_factor
    plot_sigma_x_values = (
        sigma_x_values * scale_factor if sigma_x_values is not None else None
    )

    if save_path is not None and not show_plot:
        raise ValueError("save_path può essere usato solo se show_plot=True")

    fig = None

    if show_plot:
        with _style_context(_resolve_style(style)):
            import matplotlib as mpl

            cycle_colors = mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])
            point_plot_color = (
                point_color
                if point_color is not None
                else (cycle_colors[0] if len(cycle_colors) > 0 else "C0")
            )
            fit_plot_color = (
                fit_color
                if fit_color is not None
                else (cycle_colors[1] if len(cycle_colors) > 1 else "C1")
            )
            band_plot_color = (
                band_color
                if band_color is not None
                else (cycle_colors[1] if len(cycle_colors) > 1 else "C1")
            )

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

            subplots_kwargs: dict = {
                "gridspec_kw": {"height_ratios": [3, 1]},
                "sharex": True,
                "constrained_layout": True,
            }
            if figsize is not None:
                subplots_kwargs["figsize"] = _validate_figsize(figsize)
            if dpi is not None:
                subplots_kwargs["dpi"] = dpi

            import matplotlib.pyplot as plt

            fig, (ax_fit, ax_res) = plt.subplots(2, 1, **subplots_kwargs)

            errorbar_kwargs: dict = {
                "yerr": plot_sigma_y_values,
                "xerr": plot_sigma_x_values if use_sigma_x else None,
                "fmt": "o",
                "markersize": 4,
                "elinewidth": 1,
                "capsize": 3,
                "alpha": data_alpha,
            }
            if point_plot_color is not None:
                errorbar_kwargs["color"] = point_plot_color
                errorbar_kwargs["ecolor"] = point_plot_color

            ax_fit.errorbar(x_values, y_values, **errorbar_kwargs)

            fmt = f".{decimals}f"
            x_fit = np.linspace(x_values.min(), x_values.max(), 200)
            y_fit = slope * x_fit + intercept
            fit_label = (
                f"Fit: m={slope:{fmt}}, c={intercept:{fmt}}"
                if show_fit_params
                else fit_label
            )
            ax_fit.plot(
                x_fit,
                y_fit,
                color=fit_plot_color,
                linewidth=1.5,
                label=fit_label,
            )

            if show_band:
                x_bar = weighted_mean(x_values, weights)
                sigma_y_fit = scale_factor * np.sqrt(
                    1.0 / sum_w + (x_fit - x_bar) ** 2 / (var_x * sum_w)
                )
                ax_fit.fill_between(
                    x_fit,
                    y_fit - sigma_y_fit,
                    y_fit + sigma_y_fit,
                    color=band_plot_color,
                    alpha=band_alpha,
                    label=band_label,
                )

            ax_fit.set_ylabel(ylabel)

            if title is not None:
                title_kwargs: dict = {}
                if title_fontsize is not None:
                    title_kwargs["fontsize"] = title_fontsize
                if title_pad is not None:
                    title_kwargs["pad"] = title_pad
                ax_fit.set_title(title, **title_kwargs)

            if not show_grid:
                ax_fit.grid(False)
            elif grid_alpha is not None:
                ax_fit.grid(True, axis="y", alpha=grid_alpha)
            # altrimenti: la griglia e gestita dallo stile (axes.grid, grid.alpha, ...)

            if show_legend:
                legend_kwargs: dict = {}
                if legend_fontsize is not None:
                    legend_kwargs["fontsize"] = legend_fontsize
                if legend_loc is not None:
                    legend_kwargs["loc"] = legend_loc
                ax_fit.legend(**legend_kwargs)

            residuals_plot = (
                normalized_residuals if normalize_residuals else residuals
            )
            residuals_yerr = (
                np.ones_like(normalized_residuals)
                if normalize_residuals
                else plot_sigma_y_values
            )
            residuals_axis_label = (
                r"Residuals / $\sigma_\mathrm{eff}$"
                if normalize_residuals and residuals_label == "Residuals"
                else residuals_label
            )
            residuals_errorbar_kwargs = {
                **errorbar_kwargs,
                "yerr": residuals_yerr,
            }

            ax_res.errorbar(x_values, residuals_plot, **residuals_errorbar_kwargs)
            ax_res.axhline(
                0,
                color=res_line_color if res_line_color is not None else fit_plot_color,
                linewidth=1,
                linestyle="--",
            )
            ax_res.set_xlabel(xlabel)
            ax_res.set_ylabel(residuals_axis_label)

            if not show_grid:
                ax_res.grid(False)
            elif grid_alpha is not None:
                ax_res.grid(True, axis="y", alpha=grid_alpha)

            if xlim is not None:
                ax_fit.set_xlim(xlim)
                ax_res.set_xlim(xlim)
            if ylim is not None:
                ax_fit.set_ylim(ylim)

            if save_path is not None:
                save_path = Path(save_path)
                if save_path.suffix == "":
                    save_path = save_path.with_suffix(".pdf")
                savefig_kwargs: dict = {"bbox_inches": "tight"}
                if dpi is not None:
                    savefig_kwargs["dpi"] = dpi
                fig.savefig(save_path, **savefig_kwargs)

    return LinearFitResult(
        slope=float(slope),
        intercept=float(intercept),
        slope_std=sigma_m,
        intercept_std=sigma_c,
        covariance=float(cov_mc),
        correlation=rho_mc,
        residuals=residuals,
        residual_std=residual_std,
        chi2=chi2,
        reduced_chi2=reduced_chi2,
        dof=dof,
        iterations=iterations,
        converged=converged,
        figure=fig,
        fit_method=fit_method,
        scale_factor=scale_factor,
        p_value=p_value,
    )
