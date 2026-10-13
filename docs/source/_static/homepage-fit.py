"""Bounded, browser-only execution adapter for the real MesPy public API.

Accept a small editable fitting example, not a general-purpose Python shell.
This module runs unchanged in Pyodide and in the documentation integration tests.
"""
import ast
import io
import json
from pathlib import Path
import tempfile
import tomllib
import warnings

MAX_SOURCE = 20000
MAX_POINTS = 1000


class ExampleError(ValueError):
    """An unsupported editor construct, with a translatable error code."""


def _literal(node):
    if not all(isinstance(part, (ast.Constant, ast.List, ast.Tuple, ast.UnaryOp,
                                 ast.UAdd, ast.USub, ast.Load)) for part in ast.walk(node)):
        raise ExampleError("literals")
    value = ast.literal_eval(node)
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_POINTS:
            raise ExampleError("points")
        if any(not isinstance(item, (int, float)) or isinstance(item, bool) for item in value):
            raise ExampleError("numbers")
    elif not isinstance(value, (int, float, str, bool, type(None))):
        raise ExampleError("literals")
    return value


def validate_example(source):
    if not isinstance(source, str) or len(source) > MAX_SOURCE:
        raise ExampleError("size")
    tree = ast.parse(source, filename="<MesPy example>", mode="exec")
    statements = tree.body
    if not statements:
        raise ExampleError("structure")
    first = statements[0]
    if not (isinstance(first, ast.ImportFrom) and first.module == "mespy"
            and first.level == 0 and len(first.names) == 1
            and first.names[0].name == "lin_fit" and first.names[0].asname is None):
        raise ExampleError("import")
    assigned = set()
    for statement in statements[1:-1]:
        if not (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)):
            raise ExampleError("structure")
        name = statement.targets[0].id
        if name not in {"x", "y", "sigma_y"} or name in assigned:
            raise ExampleError("structure")
        assigned.add(name)
        _literal(statement.value)
    last = statements[-1]
    if not (isinstance(last, ast.Expr) and isinstance(last.value, ast.Call)
            and isinstance(last.value.func, ast.Name) and last.value.func.id == "lin_fit"):
        raise ExampleError("call")
    call = last.value
    if len(call.args) not in (2, 3) or not {"x", "y"} <= assigned:
        raise ExampleError("call")
    for node, name in zip(call.args, ("x", "y", "sigma_y")):
        if not isinstance(node, ast.Name) or node.id != name or name not in assigned:
            raise ExampleError("call")
    keywords = set()
    for keyword in call.keywords:
        if keyword.arg not in {"sigma_y", "xlabel", "ylabel", "title", "style", "normalize_residuals"} or keyword.arg in keywords:
            raise ExampleError("call")
        keywords.add(keyword.arg)
        if keyword.arg == "sigma_y" and isinstance(keyword.value, ast.Name):
            if keyword.value.id != "sigma_y" or "sigma_y" not in assigned:
                raise ExampleError("call")
        else:
            value = _literal(keyword.value)
            if keyword.arg == "style" and value not in ("report", "mespy"):
                raise ExampleError("style")
            if keyword.arg in {"xlabel", "ylabel", "title"} and (not isinstance(value, str) or len(value) > 100):
                raise ExampleError("labels")
    # Capture the value of the actual final lin_fit call, without wrapping or
    # replacing it. The user-visible source remains independently executable.
    tree.body[-1] = ast.copy_location(ast.Assign(
        targets=[ast.Name(id="_homepage_result", ctx=ast.Store())], value=call), last)
    return ast.fix_missing_locations(tree)


def execute_fit(source):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        tree = validate_example(source)
        namespace = {"__builtins__": {"__import__": __import__}}
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            exec(compile(tree, "<MesPy example>", "exec"), namespace)
        result = namespace["_homepage_result"]
        # Both artifacts come from this single result. The temporary directory
        # is isolated per run, removed on success and on every error path.
        with tempfile.TemporaryDirectory(prefix="mespy-homepage-") as directory:
            toml_path = Path(directory) / "fit.toml"
            result.to_toml(toml_path)
            svg = io.StringIO()
            style = tomllib.loads(toml_path.read_text())["plot"].get("style", "report")
            with plt.style.context(style):
                result.figure.savefig(svg, format="svg")
            return json.dumps({"ok": True, "svg": svg.getvalue(),
                               "toml": toml_path.read_text(encoding="utf-8"),
                               "warnings": [str(w.message) for w in recorded
                                            if issubclass(w.category, UserWarning)]})
    except ExampleError as error:
        return json.dumps({"ok": False, "code": str(error)})
    except (SyntaxError, ValueError, TypeError, FloatingPointError) as error:
        line = f" (line {error.lineno})" if isinstance(error, SyntaxError) else ""
        return json.dumps({"ok": False, "error": f"{type(error).__name__}{line}: {error}"})
    finally:
        plt.close("all")
