# Modulo `io_utils`

Il modulo contiene una sola funzione, `load_csv`, senza helper interni: è un involucro di
`pandas.read_csv` che trasforma i dati mancanti in una scelta esplicita (`missing`) invece di
lasciare `NaN` silenziosi. Il diagramma mostra quindi i passi interni della funzione, nell'ordine
in cui il codice li esegue.

```mermaid
flowchart TD
    load["load_csv(path, sep, decimal, rename_columns,<br/>required_columns, missing, comment, skip_initial_space)"]:::pubblico
    chk{"missing è 'error',<br/>'drop' o 'allow'?"}:::passo
    read["pandas.read_csv()"]:::esterno
    ren["DataFrame.rename(columns=rename_columns)<br/>solo se rename_columns è dato"]:::esterno
    req{"tutte le required_columns<br/>sono presenti?"}:::passo
    pol{"missing"}:::passo
    drop["DataFrame.dropna()"]:::esterno
    isna{"DataFrame.isna()<br/>trova valori mancanti?"}:::passo
    ok(["restituisce il DataFrame"]):::dato
    err(["ValueError"]):::errore

    load --> chk
    chk -->|"no"| err
    chk -->|"sì"| read --> ren --> req
    req -->|"no"| err
    req -->|"sì"| pol
    pol -->|"'drop'"| drop --> ok
    pol -->|"'error'"| isna
    pol -->|"'allow'"| ok
    isna -->|"sì"| err
    isna -->|"no"| ok

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef passo fill:#f1f5f9,stroke:#64748b,color:#0f172a
    classDef esterno fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef dato fill:#dcfce7,stroke:#15803d,color:#0f172a
    classDef errore fill:#fee2e2,stroke:#b91c1c,color:#0f172a
```

**Legenda** — blu: funzione pubblica; grigio: controlli scritti dentro `load_csv`; giallo:
chiamate a pandas; verde/rosso: esiti.
