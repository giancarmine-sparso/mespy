# Panoramica

## Scopo

Caricare un file CSV in un `DataFrame` pandas con un insieme ristretto di opzioni e con controlli espliciti su colonne richieste e valori mancanti.

## Parametri

- `path`: percorso del file da leggere.
- `sep`: separatore di colonna passato a `pandas.read_csv`.
- `decimal`: separatore decimale, utile per file con formato italiano.
- `rename_columns`: mappa `{nome_origine: nome_destinazione}` applicata dopo il caricamento.
- `required_columns`: elenco di colonne che devono esistere dopo l'eventuale rinomina.
- `missing`: politica sui `NaN`. Puo essere `"error"`, `"drop"` oppure `"allow"`.
- `comment`: carattere di commento opzionale per `read_csv`.
- `skip_initial_space`: se vero, ignora gli spazi subito dopo il separatore.

## Restituisce

Un `pd.DataFrame` con i dati caricati e, se richiesto, gia rinominati o filtrati.

## Errori ed eccezioni

- `ValueError` se `missing` non e una policy supportata.
- `ValueError` se una o piu colonne richieste non sono presenti.
- `ValueError` se il file contiene valori mancanti e `missing="error"`.

## Esempio

```python
from mespy import load_csv

df = load_csv(
    "data/reference/test_misure.csv",
    rename_columns={"misura_n": "n", "lunghezza_mm": "lunghezza", "sigma_mm": "sigma"},
    required_columns=["n", "lunghezza", "sigma"],
    missing="drop",
)
```

## Note pratiche

- Il controllo su `required_columns` avviene dopo `rename_columns`.
- `missing="drop"` rimuove le righe incomplete con `DataFrame.dropna()`.
- La funzione non converte direttamente il `DataFrame` in array numerici: quel passaggio resta alle funzioni statistiche e di plotting.
