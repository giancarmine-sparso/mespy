# Mappa visiva di MesPy

Diagrammi Mermaid che descrivono il pacchetto così com'è in `src/mespy/`: ogni nodo porta il
nome reale di un modulo, una funzione, una classe o un file. Questa cartella sta fuori da
`docs/source/`, quindi Sphinx non la legge. GitHub e gli editor con anteprima Markdown
disegnano i diagrammi direttamente; le versioni SVG sono in [`svg/`](svg/).

## Vista d'insieme

| File | Contenuto |
|---|---|
| [overview.md](overview.md) | Architettura a moduli e dipendenze interne/esterne |
| [workflow-studente.md](workflow-studente.md) | Il percorso tipico: dati grezzi → fit → incertezze → grafico (per la presentazione) |
| [classes.md](classes.md) | Le quattro dataclass di `fit_utils` |

## Un diagramma per modulo

| File | Modulo | Contenuto |
|---|---|---|
| [init.md](init.md) | `mespy/__init__.py` | Riesportazioni e registrazione degli stili |
| [io_utils.md](io_utils.md) | `mespy.io_utils` | I passi interni di `load_csv` |
| [stats_utils.md](stats_utils.md) | `mespy.stats_utils` | Cinque funzioni pubbliche e due helper |
| [plot_utils.md](plot_utils.md) | `mespy.plot_utils` | `histogram` e gli helper di validazione e stile |
| [fit_utils.md](fit_utils.md) | `mespy.fit_utils` | `lin_fit` in quattro sottodiagrammi |
| [toml.md](toml.md) | `mespy._toml` | Helper di scrittura TOML |

## Sottosistemi

| File | Contenuto |
|---|---|
| [toml-export.md](toml-export.md) | Esportazione TOML/PDF dei fit: sequenza e struttura del documento |
| [stili.md](stili.md) | I tre stili Matplotlib (`mespy`, `column`, `report`) e come vengono applicati |

## Dati di partenza

[inventory.md](inventory.md) è l'elenco di funzioni, classi, metodi e chiamate interne da cui
sono stati ricavati i diagrammi. Si rigenera con:

```sh
.venv/bin/python scripts/inventory.py
```

## Rigenerare gli SVG

```sh
cd docs/_diagrams
for f in overview workflow-studente classes init io_utils stats_utils plot_utils fit_utils toml toml-export stili; do
    npx -p @mermaid-js/mermaid-cli mmdc -i "$f.md" -o "svg/$f.svg"
done
```

Con un ingresso Markdown `mmdc` scrive un file per diagramma, numerandoli: `svg/overview-1.svg`,
`svg/fit_utils-1.svg` … `svg/fit_utils-4.svg`, e così via.

## Convenzioni grafiche

| Aspetto | Significato |
|---|---|
| Blu, bordo spesso | Pubblico: nome in `mespy.__all__` |
| Azzurro | Pubblico solo nel sottomodulo (`LinearFitResult` e i suoi metodi) |
| Grigio tratteggiato | Helper interno (underscore iniziale) o funzione annidata |
| Giallo | Libreria esterna |
| Verde | Dati e file |
| Bianco | Elemento definito in un altro modulo |
| Freccia tratteggiata | Chiamata indiretta (callback), import pigro o chiamante esterno al modulo |
