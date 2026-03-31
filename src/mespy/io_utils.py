from __future__ import annotations

from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Literal

import pandas as pd

MissingPolicy = Literal["error", "drop", "allow"]


def load_csv(
    path: str | Path,
    *,
    sep: str = ",",
    decimal: str = ".",
    rename_columns: Mapping[str, str] | None = None,
    required_columns: Collection[str] | None = None,
    missing: MissingPolicy = "error",
    comment: str | None = None,
    skip_initial_space: bool = True,
) -> pd.DataFrame:
    """
    Carica un file CSV in un DataFrame pandas con validazione.

    Wrapper di ``pd.read_csv`` che aggiunge gestione di separatori,
    decimali, rinominazione colonne, controllo colonne richieste
    e trattamento esplicito dei valori mancanti.

    Parametri
    ---------
    path : str o Path
        Percorso del file CSV.
    sep : str, default ","
        Separatore di campo.
    decimal : str, default "."
        Carattere decimale (es. "," per formato italiano).
    rename_columns : mapping o None
        Mappa {nome_vecchio: nome_nuovo} per rinominare le colonne.
    required_columns : collection o None
        Colonne che devono essere presenti nel DataFrame dopo
        l'eventuale rinomina.
    missing : {"error", "drop", "allow"}, default "error"
        Politica di gestione dei valori mancanti:
        - ``"error"``: solleva ValueError in presenza di NaN
        - ``"drop"``: rimuove le righe con NaN
        - ``"allow"``: lascia i NaN nel DataFrame
    comment : str o None, default None
        Se valorizzato, passa il carattere di commento a ``pd.read_csv``.
    skip_initial_space : bool, default True
        Se True, ignora gli spazi immediatamente successivi al separatore.

    Restituisce
    -----------
    pd.DataFrame
        DataFrame con i dati caricati e validati.
    """
    if missing not in {"error", "drop", "allow"}:
        raise ValueError("missing deve essere uno tra: 'error', 'drop', 'allow'")

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
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colonne mancanti: {missing_columns}")

    if missing == "drop":
        return df.dropna()

    if missing == "error" and df.isna().any().any():
        raise ValueError("Il file contiene valori mancanti")

    return df
