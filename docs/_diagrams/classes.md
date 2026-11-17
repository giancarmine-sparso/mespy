# Classi

MesPy ha quattro classi, tutte in `fit_utils` e tutte dataclass congelate (`frozen=True,
slots=True`). Solo `LinearFitResult` è pubblica; le altre tre sono lo stato interno che il
risultato conserva per poter ricalcolare previsioni ed esportare i dati originali.
`_data` e `_core` sono presenti insieme (risultati di `lin_fit`) oppure entrambi assenti
(risultati costruiti a mano).

```mermaid
classDiagram
    direction LR

    class LinearFitResult {
        <<dataclass frozen>>
        +float slope
        +float intercept
        +float slope_std
        +float intercept_std
        +float covariance
        +float | None correlation
        +FloatVector residuals
        +float | None residual_std
        +float | None chi2
        +float | None reduced_chi2
        +int dof
        +Figure | None figure
        +FitMethod fit_method
        +float | None p_value
        +XErrorMethod x_error_method
        -_LinearFitData | None _data
        -_LinearFitCore | None _core
        -Mapping | None _plot_metadata
        +float | None estimated_sigma «property»
        +predict(x_new) float | FloatVector
        +to_toml(path) Path
        -\_\_post_init\_\_() None
    }

    class _LinearFitData {
        <<dataclass frozen>>
        +FloatVector x
        +FloatVector y
        +FloatVector | None sigma_y
        +FloatVector | None sigma_x
    }

    class _LinearFitCore {
        <<dataclass frozen>>
        +float slope
        +float intercept
        +float slope_std
        +float intercept_std
        +float covariance
        +float | None correlation
        +FloatVector residuals
        +float | None residual_std
        +float | None chi2
        +float | None reduced_chi2
        +float | None p_value
        +int dof
        +FitMethod fit_method
        +_FitLocalAxis x_axis
        +_FitLocalAxis y_axis
        +float local_slope
        +float center_std
        +bool exact_line
        +XErrorMethod x_error_method
        +predict(x) FloatVector
        +mean_std(x) FloatVector
    }

    class _FitLocalAxis {
        <<dataclass frozen>>
        +float origin
        +int exponent
        +FloatVector offsets
        +float mean
        +float correction
        +FloatVector centered
        +local_offsets(values) FloatVector
        +deviations(values) FloatVector
    }

    LinearFitResult "1" o-- "0..1" _LinearFitData : _data
    LinearFitResult "1" o-- "0..1" _LinearFitCore : _core
    _LinearFitCore "1" *-- "2" _FitLocalAxis : x_axis, y_axis
```

Chi le crea: `_validate_linear_fit_data()` → `_LinearFitData`; `_fit_local_axis()` →
`_FitLocalAxis`; `_solve_linear_fit()` → `_LinearFitCore`; `_make_linear_fit_result()` →
`LinearFitResult`. `estimated_sigma` è una property (non un campo).
