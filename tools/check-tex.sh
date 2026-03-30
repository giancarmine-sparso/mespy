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
check_cmd pygmentize

if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing LaTeX prerequisites: ${missing[*]}"
    echo "Install a LaTeX distribution and Pygments so these commands are available."
    echo "Examples:"
    echo "  - TeX Live (Linux)"
    echo "  - MacTeX (macOS)"
    echo "  - MiKTeX (Windows)"
    exit 1
fi

echo "LaTeX prerequisites found."
