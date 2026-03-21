from pathlib import Path

import pandas as pd


def load_csv(
    path,
    sep="",
    decimal="",
    rename_columns=None,
    required_columns=None,
    drop_missing=False,
):
    df = pd.read_csv(Path(path), sep=sep, decimal=decimal)  # carica i dati

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
