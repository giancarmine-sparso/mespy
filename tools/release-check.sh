#!/usr/bin/env bash
set -euo pipefail  # attiva modalità bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" # trova la root del progetto
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}" # sceglie quale python usare

if [ ! -x "$PYTHON_BIN" ]; then  # controlla che l'interprete esista
    echo "Python interpreter not found: $PYTHON_BIN"
    echo "Run 'make setup' first or set PYTHON_BIN explicitly."
    exit 1
fi

TMP_DIR="$(mktemp -d)" # creare una directory temporanea
trap 'rm -rf "$TMP_DIR"' EXIT

ARTIFACT_DIR="$TMP_DIR/dist"                # prepara cartelle e variabili 
TARGET_DIR="$TMP_DIR/site"                  # temporanee       
export MPLCONFIGDIR="$TMP_DIR/mplconfig"
export PIP_CACHE_DIR="$TMP_DIR/pip-cache"
export PIP_DISABLE_PIP_VERSION_CHECK=1

# questi comandi fanno girare i test
echo "[1/6] Running pytest"
PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" -m pytest -q

echo "[2/6] Compiling sources"
"$PYTHON_BIN" -m compileall src tests

echo "[3/6] Checking installed dependencies"
"$PYTHON_BIN" -m pip check

echo "[4/6] Building sdist and wheel"
"$PYTHON_BIN" -m build --sdist --wheel --no-isolation --outdir "$ARTIFACT_DIR"

echo "[5/6] Validating artifacts with twine"
"$PYTHON_BIN" -m twine check "$ARTIFACT_DIR"/*

# cerca il file whell
WHEEL_PATH="$(find "$ARTIFACT_DIR" -maxdepth 1 -type f -name '*.whl' | head -n 1)"
if [ -z "$WHEEL_PATH" ]; then
    echo "No wheel artifact found in $ARTIFACT_DIR"
    exit 1
fi

# smoke test
echo "[6/6] Installing wheel into an isolated target and smoke testing imports"
"$PYTHON_BIN" -m pip install --no-deps --target "$TARGET_DIR" "$WHEEL_PATH"
(
    cd "$TMP_DIR"
    PYTHONPATH="$TARGET_DIR" REPO_ROOT="$ROOT_DIR" "$PYTHON_BIN" "$ROOT_DIR/tools/smoke_imports.py"
)

echo "Release checks passed."
