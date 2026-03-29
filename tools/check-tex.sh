#!/usr/bin/env bash
set -euo pipefail

missing=()

check_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        missing+=("$1")
    fi
}

check_cmd latexmk
check_cmd lualatex

if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing LaTeX prerequisites: ${missing[*]}"
    echo "Install a LaTeX distribution that provides these commands."
    echo "Examples:"
    echo "  - TeX Live (Linux)"
    echo "  - MacTeX (macOS)"
    echo "  - MiKTeX (Windows)"
    exit 1
fi

echo "LaTeX prerequisites found."