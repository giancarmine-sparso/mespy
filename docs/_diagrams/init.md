# Modulo `mespy` (`__init__.py`)

La radice del pacchetto fa due cose: riesporta le otto funzioni pubbliche elencate in
`__all__` e, al momento dell'import, esegue `_register_styles()` per rendere disponibili a
Matplotlib gli stili contenuti in `stylelib/`. `LinearFitResult` non è riesportata: resta in
`mespy.fit_utils`.

```mermaid
flowchart LR
    imp(["import mespy"]):::dato

    subgraph all["mespy.__all__"]
        load_csv["load_csv()"]:::pubblico
        median["median()"]:::pubblico
        weighted_mean["weighted_mean()"]:::pubblico
        variance["variance()"]:::pubblico
        covariance["covariance()"]:::pubblico
        standard_deviation["standard_deviation()"]:::pubblico
        lin_fit["lin_fit()"]:::pubblico
        histogram["histogram()"]:::pubblico
    end

    io["io_utils"]:::modulo
    stats["stats_utils"]:::modulo
    fit["fit_utils"]:::modulo
    plot["plot_utils"]:::modulo

    reg["_register_styles()"]:::interno
    stylelib[("stylelib/*.mplstyle")]:::dato
    lib["matplotlib.style.library<br/>matplotlib.style.available"]:::esterno

    imp --> all
    imp -->|"all'import"| reg
    load_csv --> io
    median --> stats
    weighted_mean --> stats
    variance --> stats
    covariance --> stats
    standard_deviation --> stats
    lin_fit --> fit
    histogram --> plot
    stylelib -->|"un file per stile"| reg
    reg -->|"registra per nome"| lib

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef modulo fill:#ffffff,stroke:#1d4ed8,color:#0f172a
    classDef esterno fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef dato fill:#dcfce7,stroke:#15803d,color:#0f172a
```

**Legenda** — blu pieno: nome pubblico; bordo blu: sottomodulo in cui è definito; grigio
tratteggiato: helper interno; giallo: libreria esterna; verde: dati o azione dell'utente.
