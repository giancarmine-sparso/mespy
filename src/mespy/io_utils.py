from pathlib import Path

import pandas as pd


def load_csv(
    path,
    sep=",",
    decimal=".",
    rename_columns=None,
    required_columns=None,
    drop_missing=False,
):
    """
    Carica un file CSV in un DataFrame pandas con validazione.

    Wrapper di ``pd.read_csv`` che aggiunge gestione di separatori,
    decimali, rinominazione colonne, controllo colonne richieste
    e trattamento dei valori mancanti.

    Parametri
    ---------
    path : str o Path
        Percorso del file CSV.
    sep : str, default ","
        Separatore di campo.
    decimal : str, default "."
        Carattere decimale (es. "," per formato italiano).
    rename_columns : dict o None
        Mappa {nome_vecchio: nome_nuovo} per rinominare le colonne.
    required_columns : list o None
        Colonne che devono essere presenti nel DataFrame.
        Solleva ValueError se mancano.
    drop_missing : bool, default False
        Se True, rimuove le righe con valori mancanti.
        Se False, solleva ValueError in presenza di NaN.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame con i dati caricati e validati.
    """
    df = pd.read_csv(Path(path), sep=sep, decimal=decimal, comment='#', skipinitialspace=True)  # carica i dati

    if rename_columns:
        df = df.rename(columns=rename_columns)

    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Colonne mancanti: {missing}")

    if drop_missing:
        df = df.dropna()
    elif df.isna().any().any():
        raise ValueError("Il file contiene valori mancanti")

    return df
