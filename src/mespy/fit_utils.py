from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.stats import chi2 as chi2_distribution

from ._toml import _mespy_header, _write_toml_document
from .plot_utils import _resolve_style, _style_context

if TYPE_CHECKING:
    from matplotlib.figure import Figure

FloatVector = NDArray[np.float64]
FitMethod = Literal["ols", "wls"]

_LINEAR_FIT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class _LinearFitData:
    """Independent float64 copies, validated for the OLS/WLS API."""

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
    fit_method: FitMethod
    x_axis: _FitLocalAxis
    y_axis: _FitLocalAxis
    local_slope: float
    center_std: float

    def predict(self, x: FloatVector) -> FloatVector:
        try:
            deviations = self.x_axis.deviations(x)
            with np.errstate(over="ignore", invalid="ignore"):
                offsets = (
                    self.y_axis.mean
                    + self.y_axis.correction
                    + self.local_slope * deviations
                )
            if not np.all(np.isfinite(offsets)):
                raise FloatingPointError("previsione fuori dalla scala locale")
        except FloatingPointError:
            # A finite prediction may lie beyond the local coordinate range.
            # Keep the offset and slope as binary-scaled parts in that case.
            slope_part, slope_power = math.frexp(self.local_slope)
            predictions = []
            for value in x:
                delta, delta_power = _fit_sum_parts(
                    (float(value), 0), (-self.x_axis.origin, 0)
                )
                delta_part, delta_shift = math.frexp(delta)
                predictions.append(
                    _fit_scaled_sum(
                        "previsione",
                        (self.y_axis.origin, 0),
                        (self.y_axis.mean, self.y_axis.exponent),
                        (self.y_axis.correction, self.y_axis.exponent),
                        (
                            slope_part * delta_part,
                            slope_power
                            + delta_power
                            + delta_shift
                            + self.y_axis.exponent
                            - self.x_axis.exponent,
                        ),
                        (-self.local_slope * self.x_axis.mean, self.y_axis.exponent),
                        (
                            -self.local_slope * self.x_axis.correction,
                            self.y_axis.exponent,
                        ),
                    )
                )
            return np.array(predictions)
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
    """Frozen numerical result of OLS or absolute WLS.

    Residuals are in the units of y and are read-only. OLS estimates one
    common dispersion from the residuals; its chi-squared diagnostics are
    absent. WLS treats sigma_y as absolute standard uncertainties, without
    rescaling the parameter covariance. With two WLS observations, only
    chi2 and dof are defined among the residual diagnostics.

    The Figure object can still be edited or saved after fitting. Its
    reference, like every other dataclass field, cannot be reassigned.
    """

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
    dof: int
    figure: Figure | None
    fit_method: FitMethod = "wls"
    p_value: float | None = None
    _data: _LinearFitData | None = field(
        default=None, repr=False, compare=False, kw_only=True
    )
    _core: _LinearFitCore | None = field(
        default=None, repr=False, compare=False, kw_only=True
    )

    def __post_init__(self) -> None:
        residuals = np.array(self.residuals, dtype=np.float64, copy=True)
        residuals.setflags(write=False)
        object.__setattr__(self, "residuals", residuals)

    @property
    def estimated_sigma(self) -> float | None:
        """Common vertical dispersion estimated in OLS; None for absolute WLS."""
        return self.residual_std if self.fit_method == "ols" else None

    def predict(self, x_new: ArrayLike) -> float | FloatVector:
        """Evaluate the fitted mean at a finite real scalar or 1D vector.

        Results returned by lin_fit use their retained local representation
        to preserve accuracy near large offsets. A scalar returns a float;
        a vector returns an independent float64 array, including empty vectors.
        Nonrepresentable predictions raise FloatingPointError.
        """
        values = _real_fit_array("x_new", x_new)
        if values.ndim > 1:
            raise ValueError("x_new: serve uno scalare o un vettore monodimensionale")
        scalar = values.ndim == 0
        vector = values.reshape(-1)
        if self._core is not None:
            predicted = self._core.predict(vector)
        else:
            # Manually constructed results have only the supplied parameters.
            slope_part, slope_power = math.frexp(self.slope)
            predicted = np.array(
                [
                    _fit_scaled_sum(
                        "previsione",
                        (
                            slope_part * math.frexp(float(value))[0],
                            slope_power + math.frexp(float(value))[1],
                        ),
                        (self.intercept, 0),
                    )
                    for value in vector
                ]
            )
        return float(predicted[0]) if scalar else predicted

    def to_toml(self, path: str | Path) -> Path:
        """Save numerical fields and physical residuals atomically as TOML.

        Undefined diagnostics are omitted. Figure and private numerical
        state are not serialized. A missing suffix becomes .toml; an
        existing file is overwritten. The destination directory must exist.
        The full data/plot export and schema 2 are introduced in phase 5.
        """
        return _write_toml_document(_linear_fit_document(self), path)


def _make_linear_fit_result(
    data: _LinearFitData, core: _LinearFitCore, figure: Figure | None = None
) -> LinearFitResult:
    """Construct the public result independently of calculation/presentation."""
    arrays = [data.x, data.y, core.residuals]
    if data.sigma_y is not None:
        arrays.append(data.sigma_y)
    for axis in (core.x_axis, core.y_axis):
        arrays.extend((axis.offsets, axis.centered))
    for array in arrays:
        array.setflags(write=False)
    return LinearFitResult(
        slope=core.slope,
        intercept=core.intercept,
        slope_std=core.slope_std,
        intercept_std=core.intercept_std,
        covariance=core.covariance,
        correlation=core.correlation,
        residuals=core.residuals,
        residual_std=core.residual_std,
        chi2=core.chi2,
        reduced_chi2=core.reduced_chi2,
        dof=core.dof,
        figure=figure,
        fit_method=core.fit_method,
        p_value=core.p_value,
        _data=data,
        _core=core,
    )


def _linear_fit_document(result: LinearFitResult) -> dict[str, Any]:
    """Serialize the existing numerical tables with the new optional fields."""
    fit = {
        "fit_method": str(result.fit_method),
        "slope": float(result.slope),
        "slope_std": float(result.slope_std),
        "intercept": float(result.intercept),
        "intercept_std": float(result.intercept_std),
        "covariance": float(result.covariance),
    }
    if result.correlation is not None:
        fit["correlation"] = float(result.correlation)
    diagnostics = {"dof": int(result.dof)}
    for name in ("chi2", "reduced_chi2", "p_value", "residual_std"):
        value = getattr(result, name)
        if value is not None:
            diagnostics[name] = float(value)
    return {
        "mespy": _mespy_header("linear_fit", _LINEAR_FIT_SCHEMA_VERSION),
        "fit": fit,
        "diagnostics": diagnostics,
        "residuals": {"values": result.residuals.tolist()},
    }


def _plot_linear_fit(
    data: _LinearFitData,
    core: _LinearFitCore,
    *,
    xlabel: str,
    ylabel: str,
    title: str | None,
    style: str | None,
    normalize_residuals: bool,
) -> Figure:
    """Present the new numerical model using the existing two-panel layout.

    Removing the remaining hardcoded artist/style overrides is phase 4.
    """
    with _style_context(_resolve_style(style)):
        import matplotlib as mpl
        import matplotlib.pyplot as plt

        colors = mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])
        point_color = colors[0] if colors else "C0"
        fit_color = colors[1] if len(colors) > 1 else point_color
        figure, (ax_fit, ax_res) = plt.subplots(
            2,
            1,
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
            constrained_layout=True,
        )
        try:
            errorbar_kwargs = {
                "fmt": "o",
                "markersize": 4,
                "elinewidth": 1,
                "capsize": 3,
                "color": point_color,
                "ecolor": point_color,
            }
            ax_fit.errorbar(data.x, data.y, yerr=data.sigma_y, **errorbar_kwargs)
            x_fit = np.linspace(data.x.min(), data.x.max(), 200)
            y_fit = core.predict(x_fit)
            mean_std = core.mean_std(x_fit)
            ax_fit.plot(x_fit, y_fit, color=fit_color, linewidth=1.5, label="Fit")
            ax_fit.fill_between(
                x_fit,
                y_fit - mean_std,
                y_fit + mean_std,
                color=fit_color,
                alpha=0.20,
                label=r"$\pm 1 \sigma$ retta",
            )
            ax_fit.set_ylabel(ylabel)
            if title is not None:
                ax_fit.set_title(title)
            ax_fit.legend()
            residuals = core.residuals
            residual_error = data.sigma_y
            residuals_label = "Residuals"
            if normalize_residuals:
                denominator = (
                    data.sigma_y if data.sigma_y is not None else core.residual_std
                )
                residuals = core.residuals / denominator
                residual_error = (
                    np.ones_like(data.sigma_y) if data.sigma_y is not None else None
                )
                residuals_label = (
                    r"Residuals / $\sigma_y$"
                    if data.sigma_y is not None
                    else "Residuals / s"
                )
            ax_res.errorbar(data.x, residuals, yerr=residual_error, **errorbar_kwargs)
            ax_res.axhline(0, color=fit_color, linewidth=1, linestyle="--")
            ax_res.set_xlabel(xlabel)
            ax_res.set_ylabel(residuals_label)
        except BaseException:
            plt.close(figure)
            raise
    return figure


def lin_fit(
    x: ArrayLike,
    y: ArrayLike,
    sigma_y: ArrayLike | None = None,
    *,
    xlabel: str = "x",
    ylabel: str = "y",
    title: str | None = None,
    style: str | None = "report",
    output: str | Path | None = None,
    plot: bool = True,
    normalize_residuals: bool = False,
) -> LinearFitResult:
    """Fit y = slope*x + intercept with exact x and independent y errors.

    x and y are finite real 1D sequences of equal length. Without sigma_y,
    ordinary least squares (OLS) requires at least three points, emits a
    UserWarning and estimates the common vertical dispersion from residuals.
    With sigma_y, absolute weighted least squares (WLS) requires two points;
    sigma_y may be a positive scalar or a same-length positive vector.
    WLS covariance is not rescaled by reduced chi-squared. Its p-value
    interpretation assumes independent Gaussian errors and a correct model.

    The frozen result contains parameters, their standard uncertainties,
    covariance, optional correlation, physical residuals, residual_std,
    optional chi2/reduced_chi2/p_value, dof, fit_method and figure. It also
    provides estimated_sigma (OLS only) and a stable predict(x_new) method.
    residual_std is sqrt(RSS/dof), descriptive in WLS, and None when dof=0.

    plot=False returns figure=None and never loads pyplot or resolves style.
    normalize_residuals affects only the lower plot panel, using sigma_y
    in WLS and estimated_sigma in OLS. An exact OLS line cannot be plotted
    with normalized residuals. xlabel, ylabel and title label the figure;
    style selects a temporary Matplotlib style (default "report").

    output reserves the extension-free str/Path base for automatic export
    in phase 5; until then any non-None value raises NotImplementedError.
    to_toml(path) remains available on the result for numerical export.

    Breaking changes: fit_method, sigma_x, tol, max_iter and aesthetic
    overrides have been removed. Use plot in place of show_plot; save_path
    is removed in favor of the forthcoming output workflow. No legacy
    keywords are accepted.

    Invalid data raise ValueError; incompatible types raise TypeError.
    Unrepresentable numerical results raise FloatingPointError. x must
    contain at least two distinct values, without an absolute tolerance.
    """
    data = _validate_linear_fit_data(x, y, sigma_y)
    if output is not None:
        raise NotImplementedError(
            "output: l'esportazione automatica è prevista nella fase 5 di plan.md; usa result.to_toml(path)"
        )
    core = _solve_linear_fit(data)
    if (
        plot
        and normalize_residuals
        and core.fit_method == "ols"
        and core.residual_std == 0
    ):
        raise ValueError(
            "normalize_residuals: dispersione OLS nulla; usa residui non normalizzati (normalize_residuals=False)"
        )
    if core.fit_method == "ols":
        warnings.warn(
            "MesPy: sigma_y non fornita. Eseguo un fit non pesato e stimo la dispersione dai residui. Le diagnostiche χ² non sono disponibili.",
            UserWarning,
            stacklevel=2,
        )
    figure = None
    if plot:
        figure = _plot_linear_fit(
            data,
            core,
            xlabel=xlabel,
            ylabel=ylabel,
            title=title,
            style=style,
            normalize_residuals=normalize_residuals,
        )
    return _make_linear_fit_result(data, core, figure)
