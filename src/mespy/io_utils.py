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
    Load a CSV file into a pandas DataFrame with validation.

    Wrapper around ``pd.read_csv`` that adds handling of separators,
    decimal marks, column renaming, required-column checks, and an
    explicit policy for missing values.

    Parameters
    ----------
    path : str or Path
        Path to the CSV file.
    sep : str, optional
        Field separator (default ``","``).
    decimal : str, optional
        Decimal mark, e.g. ``","`` for Italian-formatted numbers
        (default ``"."``).
    rename_columns : mapping or None, optional
        Mapping ``{old_name: new_name}`` used to rename columns
        (default ``None``).
    required_columns : collection or None, optional
        Columns that must be present in the DataFrame after any
        renaming (default ``None``).
    missing : {"error", "drop", "allow"}, optional
        Policy for missing values (default ``"error"``):

        - ``"error"``: raise ``ValueError`` if any NaN is present
        - ``"drop"``: drop rows containing NaN
        - ``"allow"``: keep NaN in the DataFrame
    comment : str or None, optional
        If set, passed to ``pd.read_csv`` as the comment character
        (default ``None``).
    skip_initial_space : bool, optional
        If ``True``, skip whitespace right after the separator
        (default ``True``).

    Returns
    -------
    pandas.DataFrame
        DataFrame with the loaded and validated data.

    Raises
    ------
    ValueError
        If ``missing`` is not ``"error"``, ``"drop"`` or ``"allow"``.
    ValueError
        If any of ``required_columns`` is missing.
    ValueError
        If ``missing="error"`` and the file contains missing values.
    """
    if missing not in {"error", "drop", "allow"}:
        raise ValueError("missing must be one of: 'error', 'drop', 'allow'")

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
            raise ValueError(f"Missing columns: {missing_columns}")

    if missing == "drop":
        return df.dropna()

    if missing == "error" and df.isna().any().any():
        raise ValueError("The file contains missing values")

    return df
