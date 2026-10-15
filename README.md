<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/mespy-logo-horizontal-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/brand/mespy-logo-horizontal.svg">
    <img src="assets/brand/mespy-logo-horizontal.svg" alt="MesPy" width="420">
  </picture>
</p>
<p align="center">
  <a href="https://pypi.org/project/mespy/">
    <img src="https://img.shields.io/pypi/v/mespy?label=pypi" alt="PyPI version">
  </a>
  <a href="https://pypi.org/project/mespy/">
    <img src="https://img.shields.io/pypi/pyversions/mespy?label=python" alt="Python versions">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </a>
  <a href="https://giancarmine-sparso.github.io/mespy/">
    <img src="https://img.shields.io/badge/docs-GitHub%20Pages-blue" alt="Documentation">
  </a>
</p>
<p align="center">
  <em>Small Python toolbox for mechanics laboratory data analysis.</em>
</p>
<p align="center">
  <a href="https://giancarmine-sparso.github.io/mespy/">
    <img src="https://img.shields.io/badge/Open%20the%20MesPy%20documentation-21558F?style=for-the-badge" alt="Open the MesPy documentation">
  </a>
</p>


`MesPy` started as a set of helper functions that kept reappearing across mechanics lab notebooks and classroom scripts: loading CSV measurements, computing descriptive and weighted statistics, plotting histograms, and running linear fits with uncertainties. The library brings those recurring tasks together into a single typed package with a small public API that is easy to use in notebooks, scripts, and teaching material.

## What It Provides

- CSV loading with explicit missing-data policies
- Descriptive and weighted statistics for one-dimensional data
- Histogram plotting for quick exploratory analysis
- Linear fitting with absolute or residual-scaled uncertainties and a typed result object
- Explicit validation of input shapes, finite data and valid weights; extreme numerical scales can still produce non-finite results

## Public API

The root package exports:

- `load_csv`
- `median`
- `weighted_mean`
- `variance`
- `covariance`
- `standard_deviation`
- `histogram`
- `lin_fit`

The root namespace stays intentionally small. Additional public types, such as `mespy.fit_utils.LinearFitResult`, live in submodules.

## Installation

`mespy` requires Python `>= 3.12`.

```bash
pip install mespy
```

## Development Setup

To set up a local development environment:

### Unix / macOS

```bash
git clone https://github.com/giancarmine-sparso/mespy
cd mespy
make setup
```

To activate the virtual environment manually:

```bash
source .venv/bin/activate
```

### Windows

```cmd
git clone https://github.com/giancarmine-sparso/mespy
cd mespy
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Documentation

The Sphinx source lives in `docs/source`, and the generated site is written to `docs/build/html`.

Build the documentation with:

```bash
make docs
```

The generated site includes both English and Italian outputs, with English as the default landing page. The documentation also includes usage examples for the available functions. Complete usage workflows and notebooks are available in `docs/source/examples`.

## Project Structure

```text
mespy/
├── .github/
│   └── workflows/          # automation for documentation publishing
├── data/
│   └── reference/          # reference datasets used by tests and examples
├── docs/
│   ├── source/             # Sphinx source, examples, and translations
│   ├── Makefile
│   └── make.bat
├── figures/                # exported example figures
├── src/
│   └── mespy/              # library package
├── tests/                  # pytest suite
├── tools/                  # release and smoke-test helpers
├── LICENSE
├── Makefile                # local setup, testing, release, and docs tasks
├── pyproject.toml          # package metadata and dependencies
├── README.md
└── uv.lock
```
