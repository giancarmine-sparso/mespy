.PHONY: all help setup venv install check-tex docs docs-clean clean

PYTHON := python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
PIP := $(VENV_PYTHON) -m pip

MAIN := main
TEX := $(MAIN).tex
DOCS_DIR := docs

all: help

help:
	@echo "Available targets:"
	@echo "  make setup      - create the Python virtual environment and install dependencies"
	@echo "  make venv       - create the virtual environment"
	@echo "  make install    - install the local package and development dependencies"
	@echo "  make check-tex  - verify LaTeX prerequisites"
	@echo "  make docs       - compile the PDF documentation"
	@echo "  make docs-clean - remove LaTeX temporary files"
	@echo "  make clean      - remove temporary files"

setup: venv install

venv:
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
		echo "Created virtual environment in $(VENV)"; \
	else \
		echo "Virtual environment already exists"; \
	fi

install: venv
	@$(VENV_PYTHON) -m ensurepip --upgrade >/dev/null
	@$(PIP) install --upgrade pip
	@if [ -f pyproject.toml ]; then \
		$(PIP) install -e ".[dev]"; \
		echo "Installed local package and development dependencies in editable mode"; \
	else \
		echo "No pyproject.toml found, skipping editable package installation"; \
	fi

check-tex:
	@bash tools/check-tex.sh

docs: check-tex
	@cd $(DOCS_DIR) && latexmk -lualatex -interaction=nonstopmode -halt-on-error $(TEX)

docs-clean:
	@cd $(DOCS_DIR) && latexmk -c $(TEX)
	@rm -f $(DOCS_DIR)/*.fdb_latexmk $(DOCS_DIR)/*.fls $(DOCS_DIR)/*.synctex.gz

clean: docs-clean
