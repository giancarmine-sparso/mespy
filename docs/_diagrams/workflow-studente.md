# Il percorso dello studente

Dalla tabella di misure al grafico per la relazione, usando soltanto l'API pubblica
(`import mespy`). La propagazione delle incertezze avviene dentro `lin_fit`: `sigma_y` pesa i
punti e determina le incertezze sui parametri; `sigma_x` entra nel calcolo solo con
`x_error_method="iterate"`. I nomi dei file (`misure.csv`, `molla`) sono esempi.

```mermaid
flowchart LR
    csv[/"misure.csv<br/>dati grezzi"/]:::dato
    load["load_csv()<br/>lettura e controlli"]:::pubblico
    df[("DataFrame<br/>x, y, sigma_y")]:::dato

    subgraph s1["Descrivere le misure"]
        stats["median() · weighted_mean()<br/>variance() · standard_deviation()<br/>covariance()"]:::pubblico
        hist["histogram()<br/>media e banda ±σ"]:::pubblico
    end

    subgraph s2["Interpolare"]
        fit["lin_fit(x, y, sigma_y,<br/>output='molla')"]:::pubblico
        res["LinearFitResult<br/>slope ± slope_std<br/>intercept ± intercept_std<br/>covariance · chi2 · p_value"]:::risultato
    end

    subgraph s3["Presentare"]
        fig["Figura<br/>retta, banda ±1σ, residui"]:::dato
        files[/"molla.pdf<br/>molla.toml"/]:::dato
        pred["predict(x_new)<br/>valori previsti"]:::risultato
    end

    csv --> load --> df
    df --> stats
    df --> hist
    df --> fit
    fit -->|"propaga sigma_y<br/>(e sigma_x, se richiesto)"| res
    res --> fig
    res --> files
    res --> pred

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef risultato fill:#ede9fe,stroke:#6d28d9,color:#0f172a
    classDef dato fill:#dcfce7,stroke:#15803d,color:#0f172a
```

**Legenda** — blu: funzioni di `mespy`; viola: l'oggetto restituito da `lin_fit` e i suoi
metodi; verde: dati e file. Lo stile grafico si sceglie con `style=` (`"mespy"`, `"column"`,
`"report"`): vedi [stili.md](stili.md).

> MesPy non ha una funzione generale di propagazione degli errori per grandezze derivate
> (per esempio `g` ricavata dalla pendenza): quel passaggio lo studente lo svolge a mano
> partendo da `slope_std`, `intercept_std` e `covariance`.
