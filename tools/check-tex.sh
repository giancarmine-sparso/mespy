#!/usr/bin/env bash
set -euo pipefail

missing=()
missing_fonts=()
required_fonts=(
    "Libertinus Serif"
    "Libertinus Math"
    "Libertinus Sans"
    "JetBrains Mono"
    "Inter Display"
)

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

if command -v fc-match >/dev/null 2>&1; then
    check_font() {
        local font_name="$1"
        local matched_family

        matched_family="$(fc-match -f '%{family}\n' "$font_name" 2>/dev/null | head -n 1 || true)"
        if [[ -z "$matched_family" || "$matched_family" != *"$font_name"* ]]; then
            missing_fonts+=("$font_name")
        fi
    }

    for font_name in "${required_fonts[@]}"; do
        check_font "$font_name"
    done

    if [ ${#missing_fonts[@]} -gt 0 ]; then
        echo "Missing documentation fonts: ${missing_fonts[*]}"
        echo "Install the required fonts before running 'make docs'."
        exit 1
    fi

    echo "LaTeX prerequisites and required documentation fonts found."
else
    echo "LaTeX prerequisites found."
    echo "Font check skipped because 'fc-match' is not available."
    echo "The docs also require: ${required_fonts[*]}"
fi
