# Sottosistema: i tre stili Matplotlib

`src/mespy/stylelib/` contiene tre fogli di stile distribuiti col pacchetto (package-data
`stylelib/*.mplstyle`): `mespy` (predefinito, schermo
e notebook), `column` (figura a colonna singola) e `report` (relazione A4). Arrivano a Matplotlib
per due strade indipendenti: la registrazione per nome fatta da `import mespy`, e lo stile
temporaneo applicato da `histogram` e `lin_fit` tramite `_style_context`.

```mermaid
flowchart TD
    f_mespy["stylelib/mespy.mplstyle<br/>predefinito · 8 × 5 in"]:::dato
    f_column["stylelib/column.mplstyle<br/>colonna singola · 3.5 × 2.6 in"]:::dato
    f_report["stylelib/report.mplstyle<br/>relazione A4 · 5.9 × 3.7 in"]:::dato

    subgraph reg["Strada 1 · registrazione all'import"]
        imp(["import mespy"]):::dato
        register["_register_styles()"]:::interno
        lib["matplotlib.style.library<br/>'mespy' · 'column' · 'report'"]:::esterno
        use["plt.style.use('report')<br/>scelto dall'utente"]:::esterno
    end

    subgraph tmp["Strada 2 · stile temporaneo per una figura"]
        hist["histogram(style=...)"]:::pubblico
        linfit["lin_fit(style=...)"]:::pubblico
        resolve["_resolve_style()<br/>cerca il nome in stylelib/"]:::interno
        plotf["_plot_linear_fit()"]:::interno
        ctx["_style_context()"]:::interno
        mplctx["plt.style.context()"]:::esterno
        inipy["_in_ipython()"]:::interno
        disp["_display_new_figures()"]:::interno
    end

    imp --> register
    f_mespy --> register
    f_column --> register
    f_report --> register
    register --> lib
    lib --> use

    hist --> resolve
    resolve -->|"percorso del file se il nome è in stylelib,<br/>altrimenti nome invariato"| ctx
    linfit --> plotf
    plotf -->|"style così com'è"| ctx
    ctx -->|"None: nessuno stile aggiuntivo<br/>'mespy': file del pacchetto<br/>altro: nome o percorso"| mplctx
    lib -.->|"risolve 'column' e 'report'<br/>passati per nome"| mplctx
    ctx --> inipy
    inipy -->|"in un kernel Jupyter"| disp

    classDef pubblico fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0f172a
    classDef interno fill:#f1f5f9,stroke:#64748b,stroke-dasharray:4 3,color:#0f172a
    classDef esterno fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef dato fill:#dcfce7,stroke:#15803d,color:#0f172a
```

**Legenda** — blu: API pubblica; grigio tratteggiato: helper interno; giallo: Matplotlib;
verde: file di stile e azione dell'utente.

Due dettagli che il diagramma rende visibili: `histogram` passa sempre da `_resolve_style`,
quindi anche `"mespy"` arriva a `_style_context` già come percorso; `lin_fit` invece passa il
nome così com'è, e sono il ramo `style == "mespy"` di `_style_context` e la registrazione
all'import a risolvere rispettivamente `"mespy"` e `"column"`/`"report"`.
