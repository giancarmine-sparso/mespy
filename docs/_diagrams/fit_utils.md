# Modulo `fit_utils`

È il modulo più grande (26 funzioni, 4 classi, 8 metodi): una sola funzione pubblica alla
radice, `lin_fit`, e il tipo `LinearFitResult` pubblico solo come `mespy.fit_utils.LinearFitResult`.
Supera i 25 nodi, quindi è diviso in quattro sottodiagrammi: orchestrazione, nucleo numerico,
oggetto risultato, grafico ed esportazione.

**Legenda comune** — blu pieno: pubblico (`mespy.__all__`); azzurro: pubblico solo nel
sottomodulo; grigio tratteggiato: helper interno; bianco: elemento di un altro modulo;
freccia tratteggiata: chiamata indiretta tramite callback.

## 1. Orchestrazione di `lin_fit`

`lin_fit` non calcola nulla direttamente: valida gli ingressi, sceglie il solutore in base a
`x_error_method` (`'none'` oppure `'iterate'`), costruisce
il risultato e poi, a seconda di `plot` e `output`, disegna e/o esporta. `draw` è una funzione
annidata in `lin_fit` che incapsula la chiamata a `_plot_linear_fit`.

```mermaid
flowchart LR
    lin_fit["lin_fit()"]:::pubblico

    subgraph val["1 · Validazione"]
        vxm["_validate_x_error_method()"]:::interno
        vdata["_validate_linear_fit_data()"]:::interno
        rfa["_real_fit_array()"]:::interno
        data["_LinearFitData"]:::interno
        vflag["_validate_fit_flag()<br/>plot · normalize_residuals"]:::interno
        vlabel["_validate_fit_label()<br/>xlabel · ylabel · title"]:::interno
        vout["_validate_fit_output()"]:::interno
    end

    subgraph sol["2 · Calcolo"]
        iter["_solve_iterative_linear_fit()"]:::interno
        solve["_solve_linear_fit()"]:::interno
        core["_LinearFitCore"]:::interno
    end

    subgraph out["3 · Risultato e uscite"]
        make["_make_linear_fit_result()"]:::interno
        result["LinearFitResult"]:::sottomodulo
        draw["draw()<br/>funzione annidata in lin_fit"]:::interno
        plotf["_plot_linear_fit()"]:::interno
        export["_export_linear_fit()"]:::interno
    end

    lin_fit --> vxm
    lin_fit --> vdata
    lin_fit --> vflag
    lin_fit --> vlabel
    lin_fit --> vout
    vdata --> rfa
    vdata -->|"crea"| data
    lin_fit -->|"'iterate'"| iter
    lin_fit -->|"'none'"| solve
    iter --> solve
    solve -->|"crea"| core
    lin_fit --> make
    make -->|"crea"| result
    lin_fit -->|"plot=True, output=None"| draw
    lin_fit -->|"output dato"| export
    draw --> plotf
    export -.->|"callback draw"| draw

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef sottomodulo fill:#e0f2fe,stroke:#0284c7,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
```

## 2. Nucleo numerico

Il fit è risolto in coordinate locali centrate e scalate per potenze di due, così che
overflow e cancellazioni emergano come `FloatingPointError` invece che come risultati
silenziosamente sbagliati. `_fit_scaled_value` è il mattone su cui poggia quasi tutto;
la modalità iterativa richiama più volte `_solve_linear_fit` con le incertezze efficaci.

```mermaid
flowchart LR
    subgraph solver["Solutori"]
        iter["_solve_iterative_linear_fit()"]:::interno
        solve["_solve_linear_fit()"]:::interno
        eff["_effective_fit_sigma()"]:::interno
    end

    subgraph axis["Coordinate locali"]
        fla["_fit_local_axis()"]:::interno
        axisc["_FitLocalAxis"]:::interno
        lo["_FitLocalAxis.local_offsets()"]:::interno
        dev["_FitLocalAxis.deviations()"]:::interno
    end

    subgraph arit["Aritmetica scalata"]
        sv["_fit_scaled_value()"]:::interno
        sp["_fit_sum_parts()"]:::interno
        ss["_fit_scaled_sum()"]:::interno
        fr["_fit_restore()"]:::interno
        fo["_fit_origin_values()"]:::interno
        fn["_fit_norm()"]:::interno
    end

    subgraph corec["Stato del fit"]
        core["_LinearFitCore"]:::interno
        cpred["_LinearFitCore.predict()"]:::interno
        cstd["_LinearFitCore.mean_std()"]:::interno
    end

    iter --> solve
    iter --> eff
    eff --> sv
    solve --> fla
    solve --> sv
    solve --> sp
    solve --> ss
    solve --> fr
    solve --> fo
    solve --> fn
    solve -->|"crea"| core
    fla -->|"crea"| axisc
    dev --> lo
    ss --> sp
    ss --> sv
    fo --> ss
    fn --> sv
    cpred --> lo
    cpred --> dev
    cpred --> sp
    cpred --> ss
    cpred --> fo
    cstd --> dev
    cstd --> sv

    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
```

## 3. L'oggetto `LinearFitResult`

`_make_linear_fit_result` costruisce il risultato congelato a partire dai dati validati e dallo
stato numerico. I metodi pubblici delegano: `predict` al nucleo conservato (`_core`), `to_toml`
al modulo `_toml`. `__post_init__` rifiuta risultati incoerenti con il fit calcolato.

```mermaid
flowchart LR
    make["_make_linear_fit_result()"]:::interno

    subgraph res["LinearFitResult"]
        result["LinearFitResult"]:::sottomodulo
        post["LinearFitResult.__post_init__()"]:::interno
        est["LinearFitResult.estimated_sigma<br/>property"]:::sottomodulo
        predict["LinearFitResult.predict()"]:::sottomodulo
        totoml["LinearFitResult.to_toml()"]:::sottomodulo
    end

    vxm["_validate_x_error_method()"]:::interno
    rfa["_real_fit_array()"]:::interno
    cpred["_LinearFitCore.predict()"]:::interno
    ss["_fit_scaled_sum()"]:::interno
    doc["_linear_fit_document()"]:::interno
    fee["_fit_export_error()"]:::interno

    subgraph tm["modulo _toml"]
        header["_mespy_header()"]:::altro
        write["_write_toml_document()"]:::altro
        norm["_normalize_toml_path()"]:::altro
    end

    make -->|"crea"| result
    result --> post
    post --> vxm
    predict --> rfa
    predict -->|"risultato di lin_fit"| cpred
    predict -->|"risultato costruito a mano"| ss
    totoml --> doc
    totoml --> write
    totoml -->|"in caso di OSError"| fee
    totoml --> norm
    doc --> header

    classDef sottomodulo fill:#e0f2fe,stroke:#0284c7,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef altro fill:#ffffff,stroke:#94a3b8,color:#475569
```

## 4. Grafico ed esportazione

Con `output` assente `lin_fit` chiama `draw` direttamente. Con `output` dato passa `draw` a
`_export_linear_fit`, che a sua volta le consegna `export_figure`: `_plot_linear_fit` la invoca
come `on_ready` quando la figura è pronta, ancora dentro il contesto di stile. In questo modo
il PDF viene salvato con lo stile scelto e prima della visualizzazione nel notebook.

```mermaid
flowchart LR
    lin_fit["lin_fit()"]:::pubblico
    draw["draw()<br/>funzione annidata in lin_fit"]:::interno

    subgraph gr["Grafico"]
        plotf["_plot_linear_fit()"]:::interno
        cpred["_LinearFitCore.predict()"]:::interno
        cstd["_LinearFitCore.mean_std()"]:::interno
        eff["_effective_fit_sigma()"]:::interno
        ctx["plot_utils._style_context()"]:::altro
    end

    subgraph ex["Esportazione"]
        export["_export_linear_fit()"]:::interno
        expfig["export_figure()<br/>funzione annidata in _export_linear_fit"]:::interno
        fot["_fit_output_target()<br/>aggiunge .toml / .pdf"]:::interno
        mfd["_missing_fit_directories()"]:::interno
        refd["_remove_empty_fit_directories()"]:::interno
        rfe["_replace_fit_export()"]:::interno
        fee["_fit_export_error()"]:::interno
        doc["_linear_fit_document()"]:::interno
        write["_toml._write_toml_document()"]:::altro
    end

    lin_fit -->|"output assente"| draw
    lin_fit -->|"output dato"| export
    draw --> plotf
    plotf --> cpred
    plotf --> cstd
    plotf --> eff
    plotf --> ctx
    export --> fot
    export --> mfd
    export --> doc
    export --> write
    export --> rfe
    export --> fee
    export -->|"se l'esportazione fallisce"| refd
    export -.->|"draw(export_figure)"| draw
    plotf -.->|"on_ready(figure)"| expfig
    expfig --> rfe
    expfig --> fee
    rfe --> fee

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef altro fill:#ffffff,stroke:#94a3b8,color:#475569
```
