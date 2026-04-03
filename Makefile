.PHONY: all help setup venv install test dist twine-check upload release-check docs docs-gettext docs-update-locale docs-build-locale docs-en docs-it docs-serve docs-clean dist-clean clean

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

SPHINX_DIR := docs
SPHINX_SOURCE_DIR := $(SPHINX_DIR)/source
SPHINX_BUILD_DIR := $(SPHINX_DIR)/build
SPHINX_HTML_DIR := $(SPHINX_BUILD_DIR)/html
SPHINX_HTML_EN_DIR := $(SPHINX_HTML_DIR)/en
SPHINX_HTML_IT_DIR := $(SPHINX_HTML_DIR)/it
SPHINX_GETTEXT_DIR := $(SPHINX_BUILD_DIR)/gettext
SPHINX_LOCALE_DIR := $(SPHINX_SOURCE_DIR)/locale
SPHINX := $(VENV_PYTHON) -m sphinx
SPHINX_INTL := $(VENV_PYTHON) -m sphinx_intl

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
	@echo "  make docs       - build the bilingual Sphinx HTML documentation"
	@echo "  make docs-gettext - extract gettext catalogs for the docs"
	@echo "  make docs-update-locale - update the English translation catalogs"
	@echo "  make docs-build-locale - compile the English translation catalogs"
	@echo "  make docs-en    - build only the English Sphinx HTML documentation"
	@echo "  make docs-it    - build only the Italian Sphinx HTML documentation"
	@echo "  make docs-serve - serve the built Sphinx HTML documentation locally"
	@echo "  make docs-clean - remove the Sphinx build artifacts"
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

docs: venv
	@$(MAKE) docs-clean
	@$(MAKE) docs-en
	@$(MAKE) docs-it
	@printf '%s\n' \
		'<!doctype html>' \
		'<html lang="en">' \
		'<head>' \
		'  <meta charset="utf-8" />' \
		'  <meta http-equiv="refresh" content="0; url=./en/" />' \
		'  <meta name="viewport" content="width=device-width, initial-scale=1" />' \
		'  <title>mespy documentation</title>' \
		'  <script>window.location.replace("./en/");</script>' \
		'</head>' \
		'<body>' \
		'  <p>Redirecting to the <a href="./en/">English documentation</a>. Per la versione italiana vai a <a href="./it/">./it/</a>.</p>' \
		'</body>' \
		'</html>' \
		> "$(SPHINX_HTML_DIR)/index.html"
	@touch "$(SPHINX_HTML_DIR)/.nojekyll"

docs-gettext: venv
	@rm -rf "$(SPHINX_GETTEXT_DIR)"
	@$(SPHINX) -W -D nb_execution_mode=off -b gettext "$(SPHINX_SOURCE_DIR)" "$(SPHINX_GETTEXT_DIR)"

docs-build-locale: venv
	@$(SPHINX_INTL) -c "$(SPHINX_SOURCE_DIR)/conf.py" build -l en

docs-build-locale: docs-update-locale
	@$(SPHINX_INTL) -c "$(SPHINX_SOURCE_DIR)/conf.py" build -l en

docs-en: venv docs-build-locale
	@$(SPHINX) -W -D nb_execution_mode=off -b html -D language=en "$(SPHINX_SOURCE_DIR)" "$(SPHINX_HTML_EN_DIR)"

docs-it: venv
	@$(SPHINX) -W -D nb_execution_mode=off -b html -D language=it "$(SPHINX_SOURCE_DIR)" "$(SPHINX_HTML_IT_DIR)"

docs-serve: docs
	@cd "$(SPHINX_HTML_DIR)" && "$(VENV_PYTHON)" -m http.server 8000

docs-clean:
	@rm -rf "$(SPHINX_BUILD_DIR)"
	@if [ -d "$(SPHINX_LOCALE_DIR)" ]; then find "$(SPHINX_LOCALE_DIR)" -name '*.mo' -delete; fi

dist-clean:
	@rm -rf build dist src/*.egg-info

clean: docs-clean dist-clean
