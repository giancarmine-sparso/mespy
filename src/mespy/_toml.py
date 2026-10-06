"""Private helpers for exporting mespy results to TOML files."""

from __future__ import annotations

import os
import uuid
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


def _mespy_version() -> str:
    try:
        return version("mespy")
    except PackageNotFoundError:
        return "unknown"


def _mespy_header(result_type: str, schema_version: int) -> dict[str, Any]:
    """``[mespy]`` table shared by every exported result."""
    return {
        "schema_version": schema_version,
        "mespy_version": _mespy_version(),
        "result_type": result_type,
    }


def _normalize_toml_path(path: str | Path) -> Path:
    """Append ``.toml`` only if *path* has no extension yet."""
    toml_path = Path(path)
    if toml_path.suffix == "":
        toml_path = toml_path.with_suffix(".toml")
    return toml_path


def _write_toml_document(document: dict[str, Any], path: str | Path) -> Path:
    """Atomically write *document* to *path* and return the written path.

    The document is fully serialized in memory before touching the disk,
    then written to a temporary file in the same directory and moved into
    place with ``os.replace``: an existing file is never left truncated.
    """
    import tomli_w

    toml_path = _normalize_toml_path(path)
    data = tomli_w.dumps(document).encode("utf-8")

    tmp_path = toml_path.with_name(f".{toml_path.name}.{uuid.uuid4().hex}.tmp")
    # os.open con 0o666 rispetta l'umask: il file finale ha i permessi usuali.
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(fd, "wb") as tmp_file:
            tmp_file.write(data)
        os.replace(tmp_path, toml_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    return toml_path
