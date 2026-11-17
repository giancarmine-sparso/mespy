# Modulo `stats_utils`

Cinque funzioni pubbliche di statistica descrittiva (anche pesata) appoggiate a due soli helper
di validazione. `standard_deviation` è la radice di `variance`; tutte le altre convertono e
controllano gli ingressi con `_as_float_vector` e, se ci sono pesi, con `_validate_weights`.

```mermaid
flowchart LR
    subgraph pub["API pubblica"]
        median["median()"]:::pubblico
        weighted_mean["weighted_mean()"]:::pubblico
        variance["variance()"]:::pubblico
        covariance["covariance()"]:::pubblico
        standard_deviation["standard_deviation()"]:::pubblico
    end

    subgraph helper["Helper interni"]
        afv["_as_float_vector()"]:::interno
        vw["_validate_weights()"]:::interno
    end

    hist["plot_utils.histogram()"]:::chiamante

    standard_deviation --> variance
    median --> afv
    weighted_mean --> afv
    weighted_mean --> vw
    variance --> afv
    variance --> vw
    covariance --> afv
    covariance --> vw
    vw --> afv
    hist -.-> afv
    hist -.-> standard_deviation

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef chiamante fill:#ffffff,stroke:#94a3b8,color:#475569
```

**Legenda** — blu: pubblico (`mespy.__all__`); grigio tratteggiato: helper interno; bianco:
chiamante da un altro modulo (freccia tratteggiata).
