# Sottosistema: esportazione TOML dei fit

Nel codice non esiste una cache: MesPy **scrive** il fit in TOML ma non lo rilegge mai (nessun
lettore in `src/mespy/`), quindi ogni chiamata a `lin_fit` ricalcola tutto. Quello che esiste è
un'esportazione atomica, con due ingressi: `lin_fit(..., output=base)` (crea le cartelle e
scrive `base.toml`, più `base.pdf` se `plot=True`) e `LinearFitResult.to_toml(path)` (solo TOML,
la cartella deve già esistere).

## Sequenza di `lin_fit(..., output="results/spring")`

I file vengono prima preparati in una cartella temporanea accanto alla destinazione e poi
spostati con `os.replace`: un file esistente non resta mai troncato. La coppia PDF + TOML non
è però una transazione unica.

```mermaid
sequenceDiagram
    actor S as Studente
    participant LF as lin_fit()
    participant EX as _export_linear_fit()
    participant PL as _plot_linear_fit()
    participant TM as _write_toml_document()
    participant FS as File system

    S->>LF: lin_fit(x, y, sigma_y, output="results/spring")
    LF->>LF: _validate_fit_output() rifiuta estensioni e cartelle
    LF->>LF: _solve_linear_fit() e _make_linear_fit_result()
    LF->>EX: _export_linear_fit(result, base, draw)
    EX->>FS: _missing_fit_directories(), mkdir, TemporaryDirectory
    EX->>EX: _linear_fit_document(result)
    EX->>TM: _write_toml_document(documento, file temporaneo)
    TM->>FS: spring.toml nella cartella temporanea
    alt plot=True
        EX->>PL: draw(export_figure)
        PL->>PL: disegna dentro _style_context(style)
        PL->>EX: on_ready(figure), cioè export_figure(figure)
        EX->>FS: figure.savefig() di spring.pdf nella cartella temporanea
        EX->>FS: _replace_fit_export() sposta spring.pdf, poi spring.toml
        PL-->>EX: Figure
        EX-->>LF: Figure
    else plot=False
        EX->>FS: _replace_fit_export() sposta spring.toml
        EX-->>LF: None
    end
    Note over EX,FS: In caso di errore _remove_empty_fit_directories() elimina le cartelle appena create
    LF-->>S: LinearFitResult
```

## Struttura del documento

`_linear_fit_document()` costruisce un dizionario con sei tabelle. I campi indefiniti
(`None`) vengono omessi. Lo schema è 2 per i fit con sola `sigma_y`, 3 quando è presente
`sigma_x` o `x_error_method` è diverso da `"none"`.

```mermaid
flowchart LR
    result["LinearFitResult"]:::sottomodulo
    doc["_linear_fit_document()"]:::interno
    header["_toml._mespy_header()"]:::altro

    subgraph file["documento TOML"]
        t_mespy["[mespy]<br/>schema_version · mespy_version · result_type"]:::dato
        t_data["[data]<br/>x · y · sigma_y · sigma_x"]:::dato
        t_fit["[fit]<br/>fit_method · slope · slope_std · intercept<br/>intercept_std · covariance · correlation · x_error_method"]:::dato
        t_diag["[diagnostics]<br/>dof · chi2 · reduced_chi2 · p_value<br/>residual_std · estimated_sigma"]:::dato
        t_res["[residuals]<br/>values"]:::dato
        t_plot["[plot]<br/>enabled · normalize_residuals · xlabel<br/>ylabel · style · title"]:::dato
    end

    result --> doc
    doc --> header
    header --> t_mespy
    doc -->|"solo se _data è presente"| t_data
    doc --> t_fit
    doc --> t_diag
    doc --> t_res
    doc -->|"solo se _plot_metadata è presente"| t_plot

    classDef sottomodulo fill:#e0f2fe,stroke:#0284c7,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef altro fill:#ffffff,stroke:#94a3b8,color:#475569
    classDef dato fill:#dcfce7,stroke:#15803d,color:#0f172a
```

**Legenda** — azzurro: tipo pubblico del sottomodulo; grigio tratteggiato: helper interno;
bianco: helper di `_toml`; verde: tabelle del file. Le chiamate fra funzioni sono in
[toml.md](toml.md) e [fit_utils.md](fit_utils.md).
