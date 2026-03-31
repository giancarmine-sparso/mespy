.PHONY: all help setup venv install test dist twine-check upload release-check check-tex docs docs-clean dist-clean clean

PYTHON := python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
PIP := $(VENV_PYTHON) -m pip
PYTEST := $(VENV_PYTHON) -m pytest
BUILD := $(VENV_PYTHON) -m build
TWINE := $(VENV_PYTHON) -m twine
PACKAGE_NAME := mespy
PACKAGE_VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -n 1)
SDIST := dist/$(PACKAGE_NAME)-$(PACKAGE_VERSION).tar.gz
WHEEL := dist/$(PACKAGE_NAME)-$(PACKAGE_VERSION)-py3-none-any.whl
ARTIFACTS := $(SDIST) $(WHEEL)

MAIN := main
TEX := $(MAIN).tex
DOCS_DIR := docs
TEX_CACHE_DIR := $(abspath $(DOCS_DIR)/.texmf-var)

all: help

help:
	@echo "Available targets:"
	@echo "  make setup      - create the Python virtual environment and install dependencies"
	@echo "  make venv       - create the virtual environment"
	@echo "  make install    - install the local package and development dependencies"
	@echo "  make test       - run the pytest suite"
	@echo "  make dist       - build the sdist and wheel in dist/"
	@echo "  make twine-check - validate the current release artifacts"
	@echo "  make upload     - upload only the current release artifacts"
	@echo "  make release-check - run the full pre-release gate"
	@echo "  make check-tex  - verify LaTeX prerequisites"
	@echo "  make docs       - compile the PDF documentation"
	@echo "  make docs-clean - remove LaTeX temporary files"
	@echo "  make dist-clean - remove Python build artifacts"
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
	@if [ -f pyproject.toml ]; then \
		PIP_DISABLE_PIP_VERSION_CHECK=1 $(PIP) install -e ".[dev]" && \
		echo "Installed local package and development dependencies in editable mode"; \
	else \
		echo "No pyproject.toml found, skipping editable package installation"; \
	fi

test: venv
	@PYTHONPATH=src $(PYTEST) -q

dist: dist-clean venv
	@$(BUILD) --sdist --wheel --no-isolation

twine-check: dist
	@$(TWINE) check $(ARTIFACTS)

upload: dist
	@$(TWINE) upload $(ARTIFACTS)

release-check: venv
	@PYTHON_BIN="$(abspath $(VENV_PYTHON))" bash tools/release-check.sh

check-tex:
	@bash tools/check-tex.sh

docs: check-tex
	@mkdir -p $(TEX_CACHE_DIR)
	@cd $(DOCS_DIR) && TEXMFVAR="$(TEX_CACHE_DIR)" TEXMFCACHE="$(TEX_CACHE_DIR)" latexmk -lualatex -shell-escape -interaction=nonstopmode -halt-on-error $(TEX)

docs-clean:
	@mkdir -p $(TEX_CACHE_DIR)
	@cd $(DOCS_DIR) && TEXMFVAR="$(TEX_CACHE_DIR)" TEXMFCACHE="$(TEX_CACHE_DIR)" latexmk -c $(TEX)
	@rm -rf $(TEX_CACHE_DIR)
	@rm -rf $(DOCS_DIR)/_minted-$(MAIN)
	@rm -f $(DOCS_DIR)/*.fdb_latexmk $(DOCS_DIR)/*.fls $(DOCS_DIR)/*.synctex.gz

dist-clean:
	@rm -rf build dist src/*.egg-info

clean: docs-clean dist-clean
