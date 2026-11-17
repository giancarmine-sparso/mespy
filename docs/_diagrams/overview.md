# Architettura a moduli

MesPy è un pacchetto piatto: sei file Python in `src/mespy/` più la cartella `stylelib/`.
Le frecce etichettate sono le dipendenze interne (con i nomi realmente importati); quelle verso
destra sono le librerie esterne. Freccia continua = import in cima al modulo; tratteggiata =
import eseguito solo dentro una funzione (pigro) oppure lettura di file a runtime.

```mermaid
flowchart LR
    init["mespy<br/>(__init__.py)"]:::pubblico
    io["io_utils"]:::pubblico
    stats["stats_utils"]:::pubblico
    plot["plot_utils"]:::pubblico
    fit["fit_utils"]:::pubblico
    toml["_toml"]:::interno
    stylelib[("stylelib/<br/>mespy · column · report<br/>(.mplstyle)")]:::dato

    subgraph ext["Librerie esterne"]
        pandas["pandas"]:::esterno
        numpy["numpy"]:::esterno
        scipy["scipy.stats"]:::esterno
        mpl["matplotlib"]:::esterno
        ipy["IPython<br/>(opzionale)"]:::esterno
        tomliw["tomli_w"]:::esterno
    end

    init -->|"load_csv"| io
    init -->|"median, weighted_mean, variance,<br/>covariance, standard_deviation"| stats
    init -->|"histogram"| plot
    init -->|"lin_fit"| fit
    init -.->|"_register_styles()<br/>all'import"| stylelib
    fit -->|"_style_context"| plot
    fit -->|"_mespy_header, _normalize_toml_path,<br/>_write_toml_document"| toml
    plot -->|"_as_float_vector,<br/>standard_deviation"| stats
    plot -.->|"legge i file di stile"| stylelib

    io --> pandas
    stats --> numpy
    plot --> numpy
    fit --> numpy
    fit --> scipy
    init --> mpl
    plot -.-> mpl
    fit -.-> mpl
    plot -.-> ipy
    toml -.-> tomliw

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef esterno fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef dato fill:#dcfce7,stroke:#15803d,color:#0f172a
```

**Legenda** — blu: moduli con API pubblica; grigio tratteggiato: modulo interno; verde: dati
distribuiti col pacchetto; giallo: dipendenze esterne.
