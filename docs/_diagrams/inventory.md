# Inventario di MesPy

Generato da `scripts/inventory.py` con analisi statica (`ast`) di `src/mespy/`: nessun modulo
viene importato. *Visibilità*: «pubblico (`mespy.__all__`)» = riesportato dalla radice del
pacchetto; «pubblico (solo sottomodulo)» = senza underscore ma raggiungibile solo da
`mespy.<modulo>`; «interno» = nome (o classe, o modulo) con underscore iniziale.
La colonna *Chiama* elenca soltanto elementi di MesPy, nell'ordine in cui compaiono.

## Riepilogo

| Modulo | Righe | Funzioni | Classi | Metodi/property | Annidate | Pubblici | Interni |
|---|---:|---:|---:|---:|---:|---:|---:|
| `__init__` | 48 | 1 | 0 | 0 | 0 | 0 | 1 |
| `_toml` | 59 | 4 | 0 | 0 | 0 | 0 | 4 |
| `fit_utils` | 1243 | 26 | 4 | 8 | 2 | 5 | 35 |
| `io_utils` | 97 | 1 | 0 | 0 | 0 | 1 | 0 |
| `plot_utils` | 582 | 8 | 0 | 0 | 0 | 1 | 7 |
| `stats_utils` | 261 | 7 | 0 | 0 | 0 | 5 | 2 |

`mespy.__all__` = `['load_csv', 'median', 'weighted_mean', 'variance', 'covariance', 'standard_deviation', 'lin_fit', 'histogram']`

## `mespy` (`__init__.py`)

Importa da MesPy: `fit_utils` → `lin_fit`; `io_utils` → `load_csv`; `plot_utils` → `histogram`; `stats_utils` → `covariance`, `median`, `standard_deviation`, `variance`, `weighted_mean`.

Chiamate eseguite all'import: `_register_styles()`.

| Riga | Nome | Tipo | Visibilità | Chiama (MesPy) | Note |
|---:|---|---|---|---|---|
| 18 | `_register_styles` | funzione | interno | — | — |

## `mespy._toml`

| Riga | Nome | Tipo | Visibilità | Chiama (MesPy) | Note |
|---:|---|---|---|---|---|
| 12 | `_mespy_version` | funzione | interno | — | — |
| 19 | `_mespy_header` | funzione | interno | `_mespy_version` | — |
| 28 | `_normalize_toml_path` | funzione | interno | — | — |
| 36 | `_write_toml_document` | funzione | interno | `_normalize_toml_path` | import locale: `tomli_w` |

## `mespy.fit_utils`

Importa da MesPy: `_toml` → `_mespy_header`, `_normalize_toml_path`, `_write_toml_document`; `plot_utils` → `_style_context`.

Costanti di modulo: `_LINEAR_FIT_SCHEMA_VERSION`, `_X_ERROR_TOL`, `_X_ERROR_MAX_ITER`, `_CORE_RESULT_FIELDS`, `_FIT_OUTPUT_EXTENSIONS`.

Alias di tipo: `FloatVector`, `FitMethod`, `XErrorMethod`.

| Riga | Nome | Tipo | Visibilità | Chiama (MesPy) | Note |
|---:|---|---|---|---|---|
| 33 | `_LinearFitData` | classe | interno | — | decorator: `@dataclass` |
| 42 | `_real_fit_array` | funzione | interno | — | — |
| 73 | `_validate_linear_fit_data` | funzione | interno | `_real_fit_array`, `_LinearFitData()` | — |
| 122 | `_validate_x_error_method` | funzione | interno | — | — |
| 132 | `_fit_scaled_value` | funzione | interno | — | — |
| 161 | `_fit_sum_parts` | funzione | interno | — | — |
| 186 | `_fit_scaled_sum` | funzione | interno | `_fit_sum_parts`, `_fit_scaled_value` | — |
| 192 | `_fit_restore` | funzione | interno | — | — |
| 201 | `_fit_origin_values` | funzione | interno | `_fit_scaled_sum` | — |
| 214 | `_FitLocalAxis` | classe | interno | — | decorator: `@dataclass` |
| 224 | `_FitLocalAxis.local_offsets` | metodo | interno | — | — |
| 241 | `_FitLocalAxis.deviations` | metodo | interno | `_FitLocalAxis.local_offsets` | — |
| 246 | `_fit_local_axis` | funzione | interno | `_FitLocalAxis()` | — |
| 271 | `_fit_norm` | funzione | interno | `_fit_scaled_value` | — |
| 283 | `_LinearFitCore` | classe | interno | — | decorator: `@dataclass` |
| 306 | `_LinearFitCore.predict` | metodo | interno | `_FitLocalAxis.local_offsets`, `_FitLocalAxis.deviations`, `_fit_sum_parts`, `_fit_scaled_sum`, `_fit_origin_values` | — |
| 370 | `_LinearFitCore.mean_std` | metodo | interno | `_FitLocalAxis.deviations`, `_fit_scaled_value` | — |
| 386 | `_solve_linear_fit` | funzione | interno | `_fit_local_axis`, `_fit_scaled_value`, `_fit_origin_values`, `_fit_sum_parts`, `_fit_scaled_sum`, `_fit_restore`, `_fit_norm`, `_LinearFitCore()` | — |
| 572 | `_effective_fit_sigma` | funzione | interno | `_fit_scaled_value` | — |
| 591 | `_solve_iterative_linear_fit` | funzione | interno | `_solve_linear_fit`, `_effective_fit_sigma` | — |
| 635 | `LinearFitResult` | classe | pubblico (solo sottomodulo) | — | decorator: `@dataclass` |
| 678 | `LinearFitResult.__post_init__` | metodo | speciale (dunder) | `_validate_x_error_method` | — |
| 709 | `LinearFitResult.estimated_sigma` | property | pubblico (solo sottomodulo) | — | decorator: `@property` |
| 713 | `LinearFitResult.predict` | metodo | pubblico (solo sottomodulo) | `_real_fit_array`, `_LinearFitCore.predict`, `_fit_scaled_sum` | — |
| 746 | `LinearFitResult.to_toml` | metodo | pubblico (solo sottomodulo) | `_write_toml_document`, `_linear_fit_document`, `_fit_export_error`, `_normalize_toml_path` | — |
| 764 | `_make_linear_fit_result` | funzione | interno | `LinearFitResult()` | — |
| 802 | `_linear_fit_document` | funzione | interno | `_mespy_header` | — |
| 846 | `_validate_fit_flag` | funzione | interno | — | — |
| 855 | `_validate_fit_label` | funzione | interno | — | — |
| 880 | `_fit_output_target` | funzione | interno | — | — |
| 885 | `_validate_fit_output` | funzione | interno | — | — |
| 905 | `_fit_export_error` | funzione | interno | — | — |
| 914 | `_replace_fit_export` | funzione | interno | `_fit_export_error` | — |
| 922 | `_missing_fit_directories` | funzione | interno | — | — |
| 931 | `_remove_empty_fit_directories` | funzione | interno | — | — |
| 940 | `_export_linear_fit` | funzione | interno | `_fit_output_target`, `_missing_fit_directories`, `_fit_export_error`, `_write_toml_document`, `_linear_fit_document`, `_replace_fit_export`, `_remove_empty_fit_directories` | invoca callback: `draw` |
| 972 | `_export_linear_fit.<locals>.export_figure` | funzione annidata | interno (closure) | `_fit_export_error`, `_replace_fit_export` | — |
| 988 | `_plot_linear_fit` | funzione | interno | `_LinearFitCore.predict`, `_LinearFitCore.mean_std`, `_effective_fit_sigma`, `_style_context` | invoca callback: `on_ready`; import locale: `matplotlib`, `matplotlib.pyplot` |
| 1105 | `lin_fit` | funzione | **pubblico** (`mespy.__all__`) | `_validate_x_error_method`, `_validate_linear_fit_data`, `_validate_fit_flag`, `_validate_fit_label`, `_validate_fit_output`, `_solve_iterative_linear_fit`, `_solve_linear_fit`, `_make_linear_fit_result`, `_export_linear_fit`, `lin_fit.<locals>.draw` | — |
| 1227 | `lin_fit.<locals>.draw` | funzione annidata | interno (closure) | `_plot_linear_fit` | — |

## `mespy.io_utils`

Alias di tipo: `MissingPolicy`.

| Riga | Nome | Tipo | Visibilità | Chiama (MesPy) | Note |
|---:|---|---|---|---|---|
| 12 | `load_csv` | funzione | **pubblico** (`mespy.__all__`) | — | — |

## `mespy.plot_utils`

Importa da MesPy: `stats_utils` → `_as_float_vector`, `standard_deviation`.

Costanti di modulo: `STYLELIB`.

| Riga | Nome | Tipo | Visibilità | Chiama (MesPy) | Note |
|---:|---|---|---|---|---|
| 22 | `_resolve_style` | funzione | interno | — | — |
| 34 | `_validate_axis_limits` | funzione | interno | — | — |
| 65 | `_validate_figsize` | funzione | interno | — | — |
| 84 | `_validate_decimals` | funzione | interno | — | — |
| 100 | `_in_ipython` | funzione | interno | — | import locale: `IPython` |
| 114 | `_display_new_figures` | funzione | interno | — | import locale: `matplotlib.pyplot`, `IPython.display` |
| 137 | `_style_context` | funzione | interno | `_in_ipython`, `_display_new_figures` | decorator: `@contextmanager`; import locale: `matplotlib.pyplot` |
| 182 | `histogram` | funzione | **pubblico** (`mespy.__all__`) | `_as_float_vector`, `_validate_decimals`, `_style_context`, `_resolve_style`, `_validate_axis_limits`, `_validate_figsize`, `standard_deviation` | import locale: `matplotlib.pyplot`, `matplotlib` |

## `mespy.stats_utils`

Alias di tipo: `FloatVector`.

| Riga | Nome | Tipo | Visibilità | Chiama (MesPy) | Note |
|---:|---|---|---|---|---|
| 9 | `_as_float_vector` | funzione | interno | — | — |
| 25 | `_validate_weights` | funzione | interno | `_as_float_vector` | — |
| 46 | `median` | funzione | **pubblico** (`mespy.__all__`) | `_as_float_vector` | — |
| 70 | `weighted_mean` | funzione | **pubblico** (`mespy.__all__`) | `_as_float_vector`, `_validate_weights` | — |
| 107 | `variance` | funzione | **pubblico** (`mespy.__all__`) | `_as_float_vector`, `_validate_weights` | — |
| 168 | `covariance` | funzione | **pubblico** (`mespy.__all__`) | `_as_float_vector`, `_validate_weights` | — |
| 223 | `standard_deviation` | funzione | **pubblico** (`mespy.__all__`) | `variance` | — |

## Segnalazioni

- `__init__`: `_register_styles()` viene eseguita all'import del modulo (effetto collaterale)
- `fit_utils._export_linear_fit` (riga 981): passa la funzione annidata `export_figure` come callback a `draw`
- `fit_utils._export_linear_fit`: invoca il parametro `draw` (Callable); il bersaglio reale dipende dal chiamante
- `fit_utils._plot_linear_fit`: invoca il parametro `on_ready` (Callable); il bersaglio reale dipende dal chiamante
- `fit_utils.lin_fit` (riga 1240): passa la funzione annidata `draw` come callback a `_export_linear_fit`
- metodo omonimo `predict` in `_LinearFitCore.predict`, `LinearFitResult.predict`: risolto tramite il tipo annotato del ricevente
