from __future__ import annotations

import os
import sys
from pathlib import Path

EXPECTED_EXPORTS = {
    "load_csv",
    "median",
    "weighted_mean",
    "variance",
    "covariance",
    "standard_deviation",
    "histogram",
    "lin_fit",
}


def _filter_repo_paths(repo_root: Path) -> None:
    excluded_subtrees = (
        repo_root / "src",
        repo_root / "tests",
        repo_root / "tools",
    )

    filtered_path = []
    for entry in sys.path:
        if not entry:
            filtered_path.append(entry)
            continue

        try:
            resolved = Path(entry).resolve()
        except OSError:
            filtered_path.append(entry)
            continue

        if resolved == repo_root:
            continue

        if any(
            resolved == excluded_root or excluded_root in resolved.parents
            for excluded_root in excluded_subtrees
        ):
            continue

        filtered_path.append(entry)

    sys.path[:] = filtered_path


def main() -> None:
    repo_root = Path(os.environ["REPO_ROOT"]).resolve()
    _filter_repo_paths(repo_root)

    import mespy as mlt

    module_path = Path(mlt.__file__).resolve()
    if module_path == repo_root or repo_root in module_path.parents:
        raise SystemExit(
            f"Smoke test imported editable sources instead of wheel: {module_path}"
        )

    missing_exports = EXPECTED_EXPORTS.difference(mlt.__all__)
    if missing_exports:
        raise SystemExit(f"Missing public exports: {sorted(missing_exports)}")

    if "matplotlib.pyplot" in sys.modules:
        raise SystemExit("Package import eagerly loaded matplotlib.pyplot")

    for symbol in ("load_csv", "weighted_mean", "histogram", "lin_fit"):
        if not callable(getattr(mlt, symbol)):
            raise SystemExit(f"Public symbol is not callable: {symbol}")

    print(f"Smoke imports ok from wheel: {module_path}")


if __name__ == "__main__":
    main()

"""
Smoke test that checks that `mespy` is imported from the distributed
wheel/installation and not from the repository's local sources.

Purpose of this file
--------------------
This script does not test the numerical behavior of the package's functions
in detail. Instead, its goal is to check the minimal "health" of the installed
distribution, i.e. to verify that the published/built package is actually
importable, exposes the expected public API, and does not introduce unwanted
side effects at import time.

Why it is needed
----------------
When working on a Python package it is easy, during local testing, to
accidentally import the repository's source files instead of the freshly built
and installed wheel. In that case a false positive is possible: the tests
appear to pass, but they are not actually exercising the distribution that a
user would install.

This smoke test avoids exactly that problem:
1. it removes from `sys.path` the entries that point to the local repository;
2. it imports `mespy`;
3. it checks that the imported module does not come from the project sources;
4. it verifies that the expected public exports are present;
5. it checks that importing the package stays lightweight, without eagerly
   loading heavy modules such as `matplotlib.pyplot`;
6. it verifies that some essential public symbols are actually usable as
   functions.

What it checks in practice
--------------------------
- `REPO_ROOT`:
  read from the environment to locate the repository root precisely.

- `_filter_repo_paths(repo_root)`:
  filters `sys.path` by removing:
    * the repository root;
    * any paths under `src/`, `tests/` and `tools/`.
  This reduces the risk that `import mespy` resolves the package from the
  local files rather than from the installed version.

- `import mespy as mlt`:
  imports the package, which is expected to come from the wheel installed
  in the test environment.

- check on `mlt.__file__`:
  the path of the imported module is compared with `repo_root`.
  If the module turns out to come from the local repository, the test fails,
  because it would mean we are not testing the real distribution.

- check on the public exports:
  the `EXPECTED_EXPORTS` set defines the symbols that must be part of the
  package's public API. The test compares this set with `mlt.__all__`
  and fails if even a single expected export is missing.

- "lightweight" import check:
  if `matplotlib.pyplot` appears in `sys.modules` after merely importing the
  package, the test fails. This ensures that the package does not eagerly
  load heavy dependencies when they are not needed, improving startup time
  and architectural cleanliness.

- callability check:
  some key public symbols (`load_csv`, `weighted_mean`, `histogram`,
  `lin_fit`) are retrieved with `getattr(...)` and checked with `callable(...)`.
  This is a minimal check to make sure that the exposed API does not contain
  names that are present but incorrectly defined.

Why it is called a "smoke test"
-------------------------------
A smoke test is a quick, shallow check that verifies that the essentials
work. It does not exercise all of the package's internal logic, but it
answers one fundamental question:

    "Is the installed distribution at least importable and consistent in its API?"

If this test fails, the problem is usually structural:
- incorrect packaging;
- missing exports;
- wrong import from the local repository;
- unwanted side effects at import time;
- public symbols that are not defined correctly.

What it does NOT guarantee
--------------------------
This script does not replace unit or integration tests. It does not verify:
- the mathematical correctness of the functions;
- the validity of the numerical results;
- the behavior on edge-case inputs;
- the quality of the generated plots;
- the full compatibility of the entire package.

It does, however, guarantee one very important thing:
the installed wheel exposes at least a minimal and consistent version of the
expected public API, without accidentally depending on the local sources.

Final output
------------
If all checks pass, the script prints a message such as:

    Smoke imports ok from wheel: <module_path>

This confirms that the package was imported correctly from the wheel
and that the minimal consistency checks were passed.
"""
