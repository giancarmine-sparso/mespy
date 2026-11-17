# Modulo `plot_utils`

Una funzione pubblica, `histogram`, e sette helper: tre validano gli argomenti, quattro
gestiscono lo stile Matplotlib temporaneo e la visualizzazione nei notebook. `_style_context` è
l'unico helper usato anche da un altro modulo (`fit_utils`). La costante `STYLELIB` è definita
ma non è referenziata né nel pacchetto né nei test.

```mermaid
flowchart LR
    histogram["histogram()"]:::pubblico

    subgraph valid["Validazione degli argomenti"]
        vdec["_validate_decimals()"]:::interno
        vlim["_validate_axis_limits()<br/>xlim · ylim · hist_range"]:::interno
        vfig["_validate_figsize()"]:::interno
    end

    subgraph stile["Stile e notebook"]
        resolve["_resolve_style()"]:::interno
        ctx["_style_context()<br/>context manager"]:::interno
        inipy["_in_ipython()"]:::interno
        disp["_display_new_figures()"]:::interno
        stylelib_const["STYLELIB<br/>costante non usata"]:::interno
    end

    subgraph st["da stats_utils"]
        afv["_as_float_vector()"]:::interno
        sd["standard_deviation()"]:::pubblico
    end

    plotfit["fit_utils._plot_linear_fit()"]:::chiamante
    mpl["matplotlib.pyplot<br/>plt.style.context()"]:::esterno
    ipython["IPython.display"]:::esterno

    histogram --> afv
    histogram --> vdec
    histogram --> resolve
    histogram --> ctx
    histogram --> vlim
    histogram --> vfig
    histogram --> sd
    plotfit -.-> ctx
    ctx --> inipy
    ctx --> disp
    ctx --> mpl
    disp --> ipython

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef esterno fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef chiamante fill:#ffffff,stroke:#94a3b8,color:#475569
```

**Legenda** — blu: pubblico; grigio tratteggiato: helper interno; giallo: libreria esterna;
bianco: chiamante da un altro modulo. Il percorso completo dello stile è in
[stili.md](stili.md).
