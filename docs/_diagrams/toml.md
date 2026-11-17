# Modulo `_toml`

Modulo interno (underscore nel nome) con quattro helper per scrivere documenti TOML in modo
atomico. Non contiene alcuna funzione di lettura: MesPy esporta i risultati ma non li ricarica.
Oggi l'unico utilizzatore è `fit_utils`.

```mermaid
flowchart LR
    subgraph fit["fit_utils (chiamanti)"]
        doc["_linear_fit_document()"]:::chiamante
        totoml["LinearFitResult.to_toml()"]:::chiamante
        export["_export_linear_fit()"]:::chiamante
    end

    subgraph tm["_toml"]
        header["_mespy_header()<br/>tabella [mespy]"]:::interno
        version["_mespy_version()"]:::interno
        write["_write_toml_document()"]:::interno
        norm["_normalize_toml_path()<br/>aggiunge .toml se manca l'estensione"]:::interno
    end

    meta["importlib.metadata.version('mespy')"]:::esterno
    dumps["tomli_w.dumps()"]:::esterno
    replace["file temporaneo + os.replace()"]:::esterno

    doc --> header
    totoml --> write
    totoml --> norm
    export --> write
    header --> version
    version --> meta
    write --> norm
    write --> dumps
    write --> replace

    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef esterno fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef chiamante fill:#ffffff,stroke:#94a3b8,color:#475569
```

**Legenda** — grigio tratteggiato: helper interni di `_toml`; bianco: chiamanti in
`fit_utils`; giallo: libreria standard o esterna. Il flusso completo dell'esportazione è in
[toml-export.md](toml-export.md).
