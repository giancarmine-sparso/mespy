from __future__ import annotations

import math
import os
import tempfile
import warnings
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.stats import chi2 as chi2_distribution

from ._toml import _mespy_header, _normalize_toml_path, _write_toml_document
from .plot_utils import _style_context

if TYPE_CHECKING:
    from matplotlib.figure import Figure

FloatVector = NDArray[np.float64]
FitMethod = Literal["ols", "wls"]

_LINEAR_FIT_SCHEMA_VERSION = 2


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
    # NumPy silently promotes booleans mixed with numbers in lists/tuples.
    if raw.dtype.kind == "b" or (
        isinstance(values, (list, tuple))
        and any(
            isinstance(v, (bool, np.bool_))
            for v in np.asarray(values, dtype=object).flat
        )
    ):
        raise TypeError(
            f"{name}: i valori booleani non sono ammessi; servono numeri interi o floating-point"
        )
    if raw.dtype.kind not in "iuf":
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


def _fit_origin_values(
    origin: float, offsets: FloatVector, exponent: int
) -> FloatVector:
    """Restore ordinates from local offsets, cancelling before restoring units."""
    return np.array(
        [
            _fit_scaled_sum("previsione", (origin, 0), (float(value), exponent))
            for value in offsets
        ]
    )


@dataclass(frozen=True, slots=True)
class _FitLocalAxis:
    """Coordinate offsets in units of 2**exponent; the original origin is retained."""

    origin: float
    exponent: int
    offsets: FloatVector
    mean: float
    correction: float
    centered: FloatVector

    def local_offsets(self, values: FloatVector) -> FloatVector:
        """Express new x values relative to the retained origin and binary scale."""
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
        return local

    def deviations(self, values: FloatVector) -> FloatVector:
        """Center new x values without reconstructing a large global mean."""
        return (self.local_offsets(values) - self.mean) - self.correction


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
    exact_line: bool

    def predict(self, x: FloatVector) -> FloatVector:
        try:
            with np.errstate(over="ignore", invalid="ignore"):
                if self.exact_line:
                    offsets = self.local_slope * self.x_axis.local_offsets(x)
                else:
                    offsets = (
                        self.y_axis.mean
                        + self.y_axis.correction
                        + self.local_slope * self.x_axis.deviations(x)
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
                        (
                            0.0 if self.exact_line else self.y_axis.mean,
                            self.y_axis.exponent,
                        ),
                        (
                            0.0 if self.exact_line else self.y_axis.correction,
                            self.y_axis.exponent,
                        ),
                        (
                            slope_part * delta_part,
                            slope_power
                            + delta_power
                            + delta_shift
                            + self.y_axis.exponent
                            - self.x_axis.exponent,
                        ),
                        (
                            (
                                0.0
                                if self.exact_line
                                else -self.local_slope * self.x_axis.mean
                            ),
                            self.y_axis.exponent,
                        ),
                        (
                            (
                                0.0
                                if self.exact_line
                                else -self.local_slope * self.x_axis.correction
                            ),
                            self.y_axis.exponent,
                        ),
                    )
                )
            return np.array(predictions)
        return _fit_origin_values(self.y_axis.origin, offsets, self.y_axis.exponent)

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
    Exact local lines are checked against every original observation before
    assigning zero residual dispersion; no numerical tolerance is applied.
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

    # Exact equality in the original local offsets avoids creating artificial
    # OLS dispersion through rounded moment products. No tolerance is applied.
    pivot = int(np.argmax(np.abs(x_axis.offsets)))
    candidate = float(y_axis.offsets[pivot] / x_axis.offsets[pivot])
    exact_line = np.array_equal(y_axis.offsets, candidate * x_axis.offsets)
    if exact_line:
        # Subtraction at the y origin can hide a perturbation of an input.
        # Only accept the exact branch if prediction reproduces every y.
        try:
            reconstructed = _fit_origin_values(
                y_axis.origin, candidate * x_axis.offsets, y_axis.exponent
            )
            exact_line = np.array_equal(reconstructed, data.y)
        except FloatingPointError:
            exact_line = False
    largest_y = float(np.max(np.abs(weighted_y)))
    if exact_line:
        local_slope = candidate
    elif largest_y == 0:
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
    intercept_terms = [
        (y_axis.origin, 0),
        (-slope_mantissa * origin_mantissa, slope_power + origin_power),
    ]
    if not exact_line:
        intercept_terms.extend(
            [
                (y_axis.mean, y_axis.exponent),
                (y_axis.correction, y_axis.exponent),
                (-local_slope * x_axis.mean, y_axis.exponent),
                (-local_slope * x_axis.correction, y_axis.exponent),
            ]
        )
    intercept = _fit_scaled_sum("intercept", *intercept_terms)
    local_residuals = (
        np.zeros_like(data.y)
        if exact_line
        else y_axis.centered - local_slope * x_axis.centered
    )
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
        slope=slope,
        intercept=intercept,
        slope_std=slope_std,
        intercept_std=intercept_std,
        covariance=covariance,
        correlation=correlation,
        residuals=residuals,
        residual_std=residual_std,
        chi2=chi2,
        reduced_chi2=reduced_chi2,
        p_value=p_value,
        dof=dof,
        fit_method="ols" if data.sigma_y is None else "wls",
        x_axis=x_axis,
        y_axis=y_axis,
        local_slope=local_slope,
        center_std=center_std,
        exact_line=exact_line,
    )


_CORE_RESULT_FIELDS = (
    "slope",
    "intercept",
    "slope_std",
    "intercept_std",
    "covariance",
    "correlation",
    "residual_std",
    "chi2",
    "reduced_chi2",
    "p_value",
    "dof",
    "fit_method",
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
    For results returned by lin_fit, the retained fit is the only source of
    the numerical fields: dataclasses.replace() may change the figure, but
    altering a fitted field raises ValueError instead of mixing two fits.
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
    _plot_metadata: Mapping[str, Any] | None = field(
        default=None, repr=False, compare=False, kw_only=True
    )

    def __post_init__(self) -> None:
        residuals = np.array(self.residuals, dtype=np.float64, copy=True)
        residuals.setflags(write=False)
        object.__setattr__(self, "residuals", residuals)
        if (self._data is None) != (self._core is None):
            raise ValueError(
                "LinearFitResult: _data e _core devono essere forniti insieme"
            )
        if self._core is not None:
            # predict() and TOML data follow _core; public copies must agree.
            mismatched = [
                name
                for name in _CORE_RESULT_FIELDS
                if getattr(self, name) != getattr(self._core, name)
            ]
            if not np.array_equal(residuals, self._core.residuals):
                mismatched.append("residuals")
            if mismatched:
                raise ValueError(
                    f"LinearFitResult: {', '.join(mismatched)} incoerenti con il fit "
                    "calcolato; per parametri diversi esegui un nuovo lin_fit"
                )
        if self._plot_metadata is not None:
            object.__setattr__(
                self, "_plot_metadata", MappingProxyType(dict(self._plot_metadata))
            )

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
        """Save the fit as schema-2 TOML, overwriting the destination atomically.

        Results from lin_fit retain x, y, effective sigma_y and the original
        plot options, so the numerical fit can be rerun. Manually constructed
        results export the supplied numerical fields without inventing inputs.
        Undefined fields are omitted; floats are not rounded for presentation.
        Figure edits and the full Matplotlib state are not serialized.
        A missing suffix becomes .toml. The destination directory must exist.
        """
        try:
            return _write_toml_document(_linear_fit_document(self), path)
        except OSError as exc:
            raise _fit_export_error(exc, _normalize_toml_path(path)) from exc


def _make_linear_fit_result(
    data: _LinearFitData,
    core: _LinearFitCore,
    *,
    plot_metadata: Mapping[str, Any] | None = None,
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
        figure=None,
        fit_method=core.fit_method,
        p_value=core.p_value,
        _data=data,
        _core=core,
        _plot_metadata=plot_metadata,
    )


def _linear_fit_document(result: LinearFitResult) -> dict[str, Any]:
    """Serialize schema 2 using original data/options and unrounded numerics."""
    fit: dict[str, Any] = {
        "fit_method": str(result.fit_method),
        "slope": float(result.slope),
        "slope_std": float(result.slope_std),
        "intercept": float(result.intercept),
        "intercept_std": float(result.intercept_std),
        "covariance": float(result.covariance),
    }
    if result.correlation is not None:
        fit["correlation"] = float(result.correlation)
    diagnostics: dict[str, Any] = {"dof": int(result.dof)}
    for name in ("chi2", "reduced_chi2", "p_value", "residual_std", "estimated_sigma"):
        value = getattr(result, name)
        if value is not None:
            diagnostics[name] = float(value)
    document: dict[str, Any] = {
        "mespy": _mespy_header("linear_fit", _LINEAR_FIT_SCHEMA_VERSION),
    }
    if result._data is not None:
        document["data"] = {"x": result._data.x.tolist(), "y": result._data.y.tolist()}
        if result._data.sigma_y is not None:
            document["data"]["sigma_y"] = result._data.sigma_y.tolist()
    document.update(
        {
            "fit": fit,
            "diagnostics": diagnostics,
            "residuals": {"values": result.residuals.tolist()},
        }
    )
    if result._plot_metadata is not None:
        document["plot"] = dict(result._plot_metadata)
    return document


def _validate_fit_flag(name: str, value: object) -> bool:
    """Accept only Python or NumPy booleans, never truthy strings or numbers."""
    if not isinstance(value, (bool, np.bool_)):
        raise TypeError(
            f"{name}: serve un booleano (True o False), non {type(value).__name__}"
        )
    return bool(value)


def _validate_fit_label(name: str, value: object, *, optional: bool = False) -> str | None:
    """Accept text labels only; None is allowed (and omitted in TOML) for title."""
    if value is None and optional:
        return None
    if not isinstance(value, str):
        hint = "o None" if optional else '(usa "" per nessuna etichetta)'
        raise TypeError(
            f"{name}: serve una stringa {hint}, non {type(value).__name__}"
        )
    return str(value)


# Final suffixes that denote a file rather than part of a base name. Other
# dots (molla_k0.5, run.v2) are kept: .pdf/.toml are appended, not substituted.
_FIT_OUTPUT_EXTENSIONS = frozenset(
    {
        ".pdf", ".toml",
        ".png", ".svg", ".svgz", ".eps", ".ps", ".pgf",
        ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".raw", ".rgba",
        ".csv", ".tsv", ".txt", ".dat", ".json", ".xlsx", ".ods",
        ".gz", ".bz2", ".xz", ".zip", ".tar",
    }
)  # fmt: skip


def _fit_output_target(base: Path, suffix: str) -> Path:
    """Append an artifact suffix to the base name, never replacing its dots."""
    return base.with_name(base.name + suffix)


def _validate_fit_output(output: str | Path) -> Path:
    """Require a file base without a file extension; never reinterpret save_path."""
    if not isinstance(output, (str, Path)):
        raise TypeError("output: serve un percorso base str o Path senza estensione")
    if isinstance(output, str) and (not output or output.endswith(os.sep)):
        raise ValueError("output: serve un percorso base di file, non una directory")
    path = Path(output)
    if path.name in ("", ".", "..") or "\x00" in str(path) or path.is_dir():
        raise ValueError(
            "output: serve un percorso base di file valido, non una directory"
        )
    if path.name.endswith("."):
        raise ValueError("output: il percorso base non può terminare con un punto")
    if path.suffix.lower() in _FIT_OUTPUT_EXTENSIONS:
        raise ValueError(
            f"output: usa un percorso base senza l'estensione '{path.suffix}', ad esempio 'risultati/molla' invece di 'risultati/molla.pdf'; .pdf e .toml vengono aggiunti automaticamente"
        )
    return path


def _fit_export_error(error: OSError, target: Path) -> OSError:
    """Preserve errno/subclass while identifying the requested destination."""
    return OSError(
        error.errno,
        f"MesPy: esportazione fallita: {error.strerror or error}",
        str(target),
    )


def _replace_fit_export(source: Path, target: Path) -> None:
    """Replace one completely prepared artifact atomically."""
    try:
        os.replace(source, target)
    except OSError as exc:
        raise _fit_export_error(exc, target) from exc


def _missing_fit_directories(directory: Path) -> list[Path]:
    """Ancestors that mkdir(parents=True) would create, deepest first."""
    missing = []
    while not directory.exists() and directory != directory.parent:
        missing.append(directory)
        directory = directory.parent
    return missing


def _remove_empty_fit_directories(directories: list[Path]) -> None:
    """Undo directory creation after a failed export, never removing content."""
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            return


def _export_linear_fit(
    result: LinearFitResult,
    base: Path,
    draw: Callable[[Callable[[Figure], None]], Figure] | None,
) -> Figure | None:
    """Stage every requested file before replacement, on the target filesystem.

    The PDF is rendered and both files committed within the plotting style
    context, before notebook display. Each replacement is atomic; the pair
    is not a filesystem transaction and may be partially replaced on error.
    """
    toml_target = _fit_output_target(base, ".toml")
    pdf_target = _fit_output_target(base, ".pdf")
    created = _missing_fit_directories(base.parent)
    try:
        try:
            base.parent.mkdir(parents=True, exist_ok=True)
            staging = tempfile.TemporaryDirectory(
                prefix=f".{base.name}.", dir=base.parent
            )
        except OSError as exc:
            raise _fit_export_error(exc, toml_target) from exc
        with staging as folder:
            toml_temp = Path(folder) / toml_target.name
            try:
                _write_toml_document(_linear_fit_document(result), toml_temp)
            except OSError as exc:
                raise _fit_export_error(exc, toml_target) from exc
            if draw is None:
                _replace_fit_export(toml_temp, toml_target)
                return None

            def export_figure(figure: Figure) -> None:
                pdf_temp = Path(folder) / pdf_target.name
                try:
                    figure.savefig(pdf_temp, format="pdf")
                except OSError as exc:
                    raise _fit_export_error(exc, pdf_target) from exc
                _replace_fit_export(pdf_temp, pdf_target)
                _replace_fit_export(toml_temp, toml_target)

            return draw(export_figure)
    except BaseException:
        # Style, rendering or I/O failures must not leave new empty folders.
        _remove_empty_fit_directories(created)
        raise


def _plot_linear_fit(
    data: _LinearFitData,
    core: _LinearFitCore,
    *,
    xlabel: str,
    ylabel: str,
    title: str | None,
    style: str | None,
    normalize_residuals: bool,
    on_ready: Callable[[Figure], None] | None = None,
) -> Figure:
    """Draw data, fitted mean ± one standard uncertainty and physical/normalized residuals.

    Artist dimensions, typography, grid, layout and savefig settings belong
    to the temporary style. Only the two-panel composition, cycle colors,
    band opacity and dashed zero reference are part of the fit presentation.
    """
    low, high = float(data.x.min()), float(data.x.max())
    if math.isfinite(high - low):
        x_fit = np.linspace(low, high, 200)
    else:
        # Convex interpolation avoids overflowing a full-range difference.
        fraction = np.linspace(0.0, 1.0, 200)
        x_fit = (1 - fraction) * low + fraction * high
    y_fit = core.predict(x_fit)
    mean_std = core.mean_std(x_fit)
    residuals = core.residuals
    residual_error = data.sigma_y
    residuals_label = "Residuals"
    if normalize_residuals:
        denominator = data.sigma_y if data.sigma_y is not None else core.residual_std
        residuals = core.residuals / denominator
        residual_error = (
            np.ones_like(data.sigma_y) if data.sigma_y is not None else None
        )
        residuals_label = (
            r"Residuals / $\sigma_y$" if data.sigma_y is not None else "Residuals / s"
        )

    figure = None
    try:
        with _style_context(style):
            import matplotlib as mpl
            import matplotlib.pyplot as plt

            colors = mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])
            point_color = colors[0] if colors else "C0"
            fit_color = colors[1] if len(colors) > 1 else point_color
            existing_figures = set(plt.get_fignums())
            try:
                figure, (ax_fit, ax_res) = plt.subplots(
                    2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1]}
                )
                if data.sigma_y is None:
                    ax_fit.plot(data.x, data.y, "o", color=point_color)
                else:
                    ax_fit.errorbar(
                        data.x, data.y, yerr=data.sigma_y, fmt="o", color=point_color
                    )
                ax_fit.plot(x_fit, y_fit, color=fit_color, label="Fit")
                ax_fit.fill_between(
                    x_fit,
                    y_fit - mean_std,
                    y_fit + mean_std,
                    color=fit_color,
                    alpha=0.20,
                    label=r"$\pm 1 \sigma$ media prevista",
                )
                ax_fit.set_ylabel(ylabel)
                if title is not None:
                    ax_fit.set_title(title)
                ax_fit.legend()
                if residual_error is None:
                    ax_res.plot(data.x, residuals, "o", color=point_color)
                else:
                    ax_res.errorbar(
                        data.x,
                        residuals,
                        yerr=residual_error,
                        fmt="o",
                        color=point_color,
                    )
                ax_res.axhline(0, color=fit_color, linestyle="--")
                ax_res.set_xlabel(xlabel)
                ax_res.set_ylabel(residuals_label)
                if on_ready is not None:
                    on_ready(figure)
            except BaseException:
                if figure is None:
                    # subplots itself can fail after creating a partial figure.
                    for number in set(plt.get_fignums()) - existing_figures:
                        plt.close(number)
                else:
                    plt.close(figure)
                raise
    except BaseException:
        # The notebook display performed on context exit can also fail.
        if figure is not None:
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
    style selects a temporary Matplotlib style (default "report"), including
    registered styles, Matplotlib styles and .mplstyle files. None retains
    the active style. The style controls figure size, DPI, fonts, grid,
    line widths, marker sizes, cap sizes and layout. The band shows ± one
    standard uncertainty of the predicted mean, not a prediction interval
    for new observations. OLS points have no error bars; normalized WLS
    residuals have unit error bars referencing the observation uncertainties.

    output is an extension-free str/Path base, for example "risultati/molla".
    If supplied, missing directories are created and molla.toml is exported,
    plus molla.pdf when plot=True. Existing files are replaced atomically
    one at a time, after both requested artifacts are prepared; the pair
    is not an atomic transaction. PDF rendering honors savefig.* within
    the selected style. With output=None no file is written. to_toml(path)
    exports the same schema-2 document without creating missing directories.

    Breaking changes: fit_method, sigma_x, tol, max_iter and aesthetic
    overrides have been removed. Use plot in place of show_plot; save_path
    is removed in favor of the output workflow. iterations, converged and
    scale_factor are no longer result fields. TOML uses schema version 2.
    No legacy keywords are accepted.

    Invalid data raise ValueError; incompatible types raise TypeError.
    Unrepresentable numerical results raise FloatingPointError. x must
    contain at least two distinct values, without an absolute tolerance.
    """
    data = _validate_linear_fit_data(x, y, sigma_y)
    plot = _validate_fit_flag("plot", plot)
    normalize_residuals = _validate_fit_flag("normalize_residuals", normalize_residuals)
    xlabel = _validate_fit_label("xlabel", xlabel)
    ylabel = _validate_fit_label("ylabel", ylabel)
    title = _validate_fit_label("title", title, optional=True)
    base = _validate_fit_output(output) if output is not None else None
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
    plot_metadata: dict[str, Any] = {
        "enabled": bool(plot),
        "normalize_residuals": bool(normalize_residuals),
        "xlabel": xlabel,
        "ylabel": ylabel,
    }
    if style is not None:
        plot_metadata["style"] = str(style)
    if title is not None:
        plot_metadata["title"] = title
    result = _make_linear_fit_result(data, core, plot_metadata=plot_metadata)

    def draw(on_ready: Callable[[Figure], None] | None = None) -> Figure:
        return _plot_linear_fit(
            data,
            core,
            xlabel=xlabel,
            ylabel=ylabel,
            title=title,
            style=style,
            normalize_residuals=normalize_residuals,
            on_ready=on_ready,
        )

    if base is not None:
        figure = _export_linear_fit(result, base, draw if plot else None)
    else:
        figure = draw() if plot else None
    return replace(result, figure=figure) if figure is not None else result
