# mespy

> Documentation: [giancarmine-sparso.github.io/mespy](https://giancarmine-sparso.github.io/mespy/index.html#)

Small Python toolbox for mechanics laboratory data analysis.

`mespy` started as a set of helper functions that kept reappearing across mechanics lab notebooks and classroom scripts: loading CSV measurements, computing descriptive and weighted statistics, plotting histograms, and running linear fits with uncertainties. The library brings those recurring tasks together into a single typed package with a small public API that is easy to use in notebooks, scripts, and teaching material.

## What It Provides

- CSV loading with explicit missing-data policies
- Descriptive and weighted statistics for one-dimensional data
- Histogram plotting for quick exploratory analysis
- Weighted linear fitting with a typed result object
- Clear validation errors instead of silent `nan` propagation

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
pip install git+https://github.com/giancarmine-sparso/mespy.git
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
