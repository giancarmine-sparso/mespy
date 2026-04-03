# Funzionamento

Questa pagina descrive il flusso interno di `load_csv` e l'ordine con cui vengono applicati i controlli. A differenza di [Panoramica](panoramica.md), qui l'obiettivo non e ripetere la lista dei parametri, ma chiarire come la funzione costruisce e valida il `DataFrame`.

## Sequenza di esecuzione

L'implementazione segue una sequenza semplice e prevedibile:

1. Controlla subito che `missing` sia una delle policy supportate: `"error"`, `"drop"` oppure `"allow"`.
2. Chiama `pd.read_csv(...)` passando:
   - `Path(path)` come percorso del file
   - `sep`
   - `decimal`
   - `comment`
   - `skipinitialspace=skip_initial_space`
3. Se `rename_columns` e valorizzato, rinomina le colonne del `DataFrame`.
4. Se `required_columns` e valorizzato, verifica che tutte le colonne richieste siano presenti dopo l'eventuale rinomina.
5. Applica la policy sui valori mancanti:
   - con `missing="drop"` restituisce `df.dropna()`
   - con `missing="error"` controlla se esiste almeno un `NaN` e, in quel caso, solleva `ValueError`
   - con `missing="allow"` non modifica il `DataFrame`
6. Restituisce il `DataFrame` finale.

In forma compatta, il comportamento e equivalente a questo schema:

```python
if missing not in {"error", "drop", "allow"}:
    raise ValueError(...)

df = pd.read_csv(
    Path(path),
    sep=sep,
    decimal=decimal,
    comment=comment,
    skipinitialspace=skip_initial_space,
)

if rename_columns:
    df = df.rename(columns=rename_columns)

if required_columns:
    ...

if missing == "drop":
    return df.dropna()

if missing == "error" and df.isna().any().any():
    raise ValueError(...)

return df
```

## Ordine dei controlli

L'ordine dei passaggi e parte del contratto pratico della funzione.

- `path` e l'unico parametro posizionale: tutti gli altri sono keyword-only.
- La validazione di `missing` avviene prima di leggere il file. Se la policy non e supportata, la funzione fallisce subito.
- `required_columns` viene controllato dopo `rename_columns`. Questo permette di chiedere colonne con il nome finale, non con il nome originale del file.
- `comment` e `skip_initial_space` non introducono logica aggiuntiva: sono passthrough controllati verso `pandas.read_csv`.
- Il controllo dei `NaN` con `missing="error"` non avviene durante la lettura, ma sul `DataFrame` gia caricato.

Questo ordine rende il comportamento facile da prevedere nei notebook e negli script: prima si importa il file, poi si normalizzano i nomi, poi si verifica la struttura, e solo alla fine si decide come trattare i valori mancanti.

## Policy sui valori mancanti

La gestione dei `NaN` e esplicita e dipende interamente dal parametro `missing`.

- `missing="error"`: e il default. Dopo il caricamento, la funzione controlla l'intero `DataFrame` con `df.isna().any().any()`. Se trova almeno un valore mancante, solleva `ValueError`.
- `missing="drop"`: il caricamento non fallisce per la presenza di `NaN`. Le righe incomplete vengono eliminate con `DataFrame.dropna()`, e il `DataFrame` restituito puo quindi avere meno righe del file originale.
- `missing="allow"`: la funzione non rimuove nulla e non solleva errori per i `NaN`. I valori mancanti restano nel `DataFrame` e vengono gestiti eventualmente a valle.

Dal punto di vista operativo:

- `error` e utile quando il file deve essere completo prima di passare alle analisi.
- `drop` e utile quando si vuole un comportamento conservativo ma non bloccante.
- `allow` e utile quando la gestione dei dati mancanti viene demandata a passaggi successivi.

Se `missing` riceve un valore diverso da `"error"`, `"drop"` o `"allow"`, la funzione solleva subito `ValueError` senza tentare la lettura del CSV.

## Interazioni tra parametri

Alcune combinazioni di parametri definiscono il comportamento pratico piu importante della funzione.

### Rinomina e colonne richieste

La rinomina avviene prima del controllo su `required_columns`. Per esempio, se il file contiene una colonna `x` e si passa `rename_columns={"x": "alfa"}`, allora `required_columns=["alfa"]` e valido. Questo evita di dover ragionare contemporaneamente su nomi originali e nomi finali.

Se dopo la rinomina manca ancora una colonna richiesta, la funzione solleva `ValueError` con l'elenco delle colonne assenti.

### Separatore e separatore decimale

`sep` e `decimal` vengono inoltrati direttamente a `pandas.read_csv`. Questo permette di leggere senza logica extra sia CSV "classici" con `,` e `.` sia file con formato piu comune in contesto italiano, ad esempio `;` come separatore di colonna e `,` come separatore decimale.

La funzione non esegue conversioni manuali dei numeri: si appoggia al comportamento standard di pandas.

### Commenti espliciti

Il parametro `comment` e opzionale e ha comportamento opt-in:

- se `comment=None`, i caratteri come `#` restano parte del contenuto testuale
- se `comment="#"`, le righe che iniziano con `#` vengono trattate come commenti da `read_csv`

Questo dettaglio e importante per evitare che simboli presenti nei dati vengano interpretati come commenti senza una richiesta esplicita.

### Spazi dopo il separatore

`skip_initial_space=True` viene tradotto in `skipinitialspace=True` nella chiamata a pandas. In pratica, gli spazi immediatamente successivi al separatore vengono ignorati gia in fase di lettura, senza passaggi di pulizia aggiuntivi nel `DataFrame`.

## Esempio commentato

```python
from mespy import load_csv

df = load_csv(
    "data/reference/test_misure.csv",
    rename_columns={"misura_n": "n", "lunghezza_mm": "lunghezza", "sigma_mm": "sigma"},
    required_columns=["n", "lunghezza", "sigma"],
    missing="drop",
)
```

In questo esempio:

- il file di esempio viene letto direttamente dalla cartella `data/reference`
- le colonne vengono rinominate subito dopo il caricamento
- il controllo su `required_columns` verifica i nomi finali `n`, `lunghezza` e `sigma`
- eventuali righe con valori mancanti vengono rimosse prima della restituzione

Il risultato finale e un `DataFrame` gia pronto per essere passato alle funzioni di analisi e plotting del package.
