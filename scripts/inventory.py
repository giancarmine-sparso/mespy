"""Inventario statico di MesPy (script temporaneo, usa solo ``ast``).

Per ogni modulo in ``src/mespy/`` elenca funzioni, classi, metodi e funzioni
annidate, ne classifica la visibilita' e risolve le chiamate verso altri
elementi di MesPy. Il risultato e' una tabella Markdown.

Uso::

    .venv/bin/python scripts/inventory.py            # scrive docs/_diagrams/inventory.md
    .venv/bin/python scripts/inventory.py --stdout   # stampa soltanto

Il codice non viene mai importato: l'analisi e' puramente sintattica. Le
chiamate a metodi sono risolte con un'inferenza dei tipi minima (annotazioni
dei parametri, campi delle dataclass, tipo di ritorno delle funzioni MesPy);
cio' che non si risolve finisce nella sezione "Segnalazioni".
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "mespy"
OUTPUT = ROOT / "docs" / "_diagrams" / "inventory.md"

# Decorator che non registrano nulla: non rendono ambigua la mappa.
KNOWN_DECORATORS = {"dataclass", "property", "contextmanager", "staticmethod", "classmethod"}
DYNAMIC_CALLS = {"import_module", "__import__", "eval", "exec"}


@dataclass
class Entity:
    module: str
    qualname: str
    kind: str  # funzione | classe | metodo | property | funzione annidata
    line: int
    node: ast.AST
    owner: str | None = None  # classe (metodi) o funzione esterna (annidate)
    decorators: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    callbacks: list[str] = field(default_factory=list)
    lazy_imports: list[str] = field(default_factory=list)
    returns: str | None = None

    @property
    def name(self) -> str:
        return self.qualname.rsplit(".", 1)[-1]


@dataclass
class Module:
    name: str
    path: Path
    tree: ast.Module
    entities: dict[str, Entity] = field(default_factory=dict)
    # nome locale -> (modulo MesPy, nome originale)
    imports: dict[str, tuple[str, str]] = field(default_factory=dict)
    fields: dict[str, dict[str, str]] = field(default_factory=dict)  # classe -> campo -> tipo
    all_names: list[str] = field(default_factory=list)
    module_calls: list[str] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


def decorator_name(node: ast.expr) -> str:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else ast.unparse(node)


def annotation_classes(node: ast.expr | None, classes: set[str]) -> list[str]:
    """Classi MesPy nominate in un'annotazione (``A | None`` -> ``[A]``)."""
    if node is None:
        return []
    return [n.id for n in ast.walk(node) if isinstance(n, ast.Name) and n.id in classes]


def collect(module: Module) -> None:
    for node in module.tree.body:
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            for alias in node.names:
                module.imports[alias.asname or alias.name] = (node.module, alias.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        module.all_names = [ast.literal_eval(e) for e in node.value.elts]
                    elif target.id.lstrip("_").isupper():
                        module.constants.append(target.id)
                    elif not target.id.startswith("__"):
                        module.aliases.append(target.id)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            module.module_calls.append(ast.unparse(node.value.func))
        elif isinstance(node, ast.FunctionDef):
            add_function(module, node, node.name, "funzione", None)
        elif isinstance(node, ast.ClassDef):
            add_class(module, node)


def add_function(
    module: Module, node: ast.FunctionDef, qualname: str, kind: str, owner: str | None
) -> None:
    decorators = [decorator_name(d) for d in node.decorator_list]
    if kind == "metodo" and "property" in decorators:
        kind = "property"
    entity = Entity(module.name, qualname, kind, node.lineno, node, owner, decorators)
    module.entities[qualname] = entity
    for child in direct_statements(node):
        if isinstance(child, ast.FunctionDef):
            add_function(
                module, child, f"{qualname}.<locals>.{child.name}", "funzione annidata", qualname
            )


def add_class(module: Module, node: ast.ClassDef) -> None:
    decorators = [decorator_name(d) for d in node.decorator_list]
    module.entities[node.name] = Entity(
        module.name, node.name, "classe", node.lineno, node, None, decorators
    )
    module.fields[node.name] = {}
    for child in node.body:
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            module.fields[node.name][child.target.id] = ast.unparse(child.annotation)
        elif isinstance(child, ast.FunctionDef):
            add_function(module, child, f"{node.name}.{child.name}", "metodo", node.name)


def direct_statements(func: ast.FunctionDef):
    """Nodi del corpo di *func*, senza entrare nelle funzioni annidate."""
    stack = list(func.body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))


class Resolver:
    def __init__(self, modules: dict[str, Module]) -> None:
        self.modules = modules
        self.classes = {
            e.qualname: e for m in modules.values() for e in m.entities.values() if e.kind == "classe"
        }
        self.class_names = set(self.classes)
        for module in modules.values():
            for entity in module.entities.values():
                if isinstance(entity.node, ast.FunctionDef):
                    found = annotation_classes(entity.node.returns, self.class_names)
                    entity.returns = found[0] if found else None

    def lookup(self, module: Module, name: str) -> Entity | None:
        """Risolvi un nome a livello di modulo (definizione locale o import relativo)."""
        if name in module.entities:
            return module.entities[name]
        if name in module.imports:
            source, original = module.imports[name]
            return self.modules[source].entities.get(original) if source in self.modules else None
        return None

    def field_type(self, cls: str, attr: str) -> str | None:
        owner = self.modules[self.classes[cls].module]
        annotation = owner.fields.get(cls, {}).get(attr)
        if annotation is None:
            return None
        found = sorted(_names(annotation) & self.class_names)
        return found[0] if found else None

    def expr_type(self, module: Module, env: dict[str, str], node: ast.expr) -> str | None:
        """Classe MesPy di un'espressione, quando e' deducibile sintatticamente."""
        if isinstance(node, ast.Name):
            return env.get(node.id)
        if isinstance(node, ast.Attribute):
            base = self.expr_type(module, env, node.value)
            return self.field_type(base, node.attr) if base else None
        if isinstance(node, ast.IfExp):
            return self.expr_type(module, env, node.body) or self.expr_type(module, env, node.orelse)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "replace" and node.args:  # dataclasses.replace
                    return self.expr_type(module, env, node.args[0])
                target = self.lookup(module, node.func.id)
                if target is not None:
                    return target.qualname if target.kind == "classe" else target.returns
        return None

    def analyse(self, module: Module, entity: Entity, notes: list[str]) -> None:
        func = entity.node
        if not isinstance(func, ast.FunctionDef):
            return
        env: dict[str, str] = {}
        params: set[str] = set()
        callable_params: set[str] = set()
        all_args = func.args.posonlyargs + func.args.args + func.args.kwonlyargs
        for arg in all_args:
            params.add(arg.arg)
            found = annotation_classes(arg.annotation, self.class_names)
            if found:
                env[arg.arg] = found[0]
            if arg.annotation is not None and "Callable" in ast.unparse(arg.annotation):
                callable_params.add(arg.arg)
        if entity.kind in ("metodo", "property") and all_args:
            env[all_args[0].arg] = entity.owner or ""

        nested = {
            e.name: e for e in module.entities.values() if e.owner == entity.qualname and e.kind == "funzione annidata"
        }
        statements = sorted(direct_statements(func), key=lambda n: (getattr(n, "lineno", 0), getattr(n, "col_offset", 0)))
        for node in statements:  # tipi delle variabili locali
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                inferred = self.expr_type(module, env, node.value)
                if inferred:
                    env.setdefault(node.targets[0].id, inferred)

        def record(target: str) -> None:
            if target not in entity.calls:
                entity.calls.append(target)

        for node in statements:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [node.module] if isinstance(node, ast.ImportFrom) and node.module else [a.name for a in node.names]
                for name in names:
                    if name not in entity.lazy_imports:
                        entity.lazy_imports.append(name)
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            if isinstance(callee, ast.Name):
                if callee.id in DYNAMIC_CALLS:
                    notes.append(f"`{module.name}.{entity.qualname}` (riga {node.lineno}): chiamata dinamica `{callee.id}`")
                if callee.id in nested:
                    record(nested[callee.id].qualname)
                elif callee.id in callable_params:
                    entity.callbacks.append(callee.id)
                elif callee.id not in params:
                    target = self.lookup(module, callee.id)
                    if target is not None:
                        record(target.qualname + ("()" if target.kind == "classe" else ""))
            elif isinstance(callee, ast.Attribute):
                if callee.attr in DYNAMIC_CALLS:
                    notes.append(f"`{module.name}.{entity.qualname}` (riga {node.lineno}): chiamata dinamica `{ast.unparse(callee)}`")
                receiver = self.expr_type(module, env, callee.value)
                if receiver:
                    owner = self.modules[self.classes[receiver].module]
                    method = owner.entities.get(f"{receiver}.{callee.attr}")
                    if method is not None:
                        record(method.qualname)
            # funzioni annidate passate come argomento (callback)
            for value in list(node.args) + [k.value for k in node.keywords]:
                for sub in ast.walk(value):
                    if isinstance(sub, ast.Name) and sub.id in nested and isinstance(callee, ast.Name) and callee.id not in nested:
                        notes.append(
                            f"`{module.name}.{entity.qualname}` (riga {node.lineno}): passa la funzione annidata "
                            f"`{sub.id}` come callback a `{callee.id}`"
                        )
        for name in dict.fromkeys(entity.callbacks):
            notes.append(
                f"`{module.name}.{entity.qualname}`: invoca il parametro `{name}` (Callable); "
                "il bersaglio reale dipende dal chiamante"
            )
        entity.callbacks = list(dict.fromkeys(entity.callbacks))


def _names(annotation: str) -> set[str]:
    return {n.id for n in ast.walk(ast.parse(annotation, mode="eval")) if isinstance(n, ast.Name)}


def visibility(entity: Entity, root_all: list[str]) -> str:
    parts = [p for p in entity.qualname.split(".") if p != "<locals>"]
    if entity.kind == "funzione annidata":
        return "interno (closure)"
    if any(p.startswith("_") and not p.startswith("__") for p in parts):
        return "interno"
    if parts[-1].startswith("__") and parts[-1].endswith("__"):
        return "speciale (dunder)"
    if entity.module.startswith("_"):
        return "interno"
    if parts[0] in root_all and len(parts) == 1:
        return "**pubblico** (`mespy.__all__`)"
    return "pubblico (solo sottomodulo)"


def render(modules: dict[str, Module], notes: list[str]) -> str:
    root_all = modules["__init__"].all_names
    lines = [
        "# Inventario di MesPy",
        "",
        "Generato da `scripts/inventory.py` con analisi statica (`ast`) di `src/mespy/`: nessun modulo",
        "viene importato. *Visibilità*: «pubblico (`mespy.__all__`)» = riesportato dalla radice del",
        "pacchetto; «pubblico (solo sottomodulo)» = senza underscore ma raggiungibile solo da",
        "`mespy.<modulo>`; «interno» = nome (o classe, o modulo) con underscore iniziale.",
        "La colonna *Chiama* elenca soltanto elementi di MesPy, nell'ordine in cui compaiono.",
        "",
        "## Riepilogo",
        "",
        "| Modulo | Righe | Funzioni | Classi | Metodi/property | Annidate | Pubblici | Interni |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for module in modules.values():
        entities = list(module.entities.values())
        count = lambda kinds: sum(e.kind in kinds for e in entities)  # noqa: E731
        public = sum("pubblico" in visibility(e, root_all) for e in entities)
        lines.append(
            f"| `{module.name}` | {len(module.path.read_text(encoding='utf-8').splitlines())} "
            f"| {count({'funzione'})} | {count({'classe'})} | {count({'metodo', 'property'})} "
            f"| {count({'funzione annidata'})} | {public} | {len(entities) - public} |"
        )
    lines += ["", f"`mespy.__all__` = `{root_all}`", ""]

    for module in modules.values():
        lines += [f"## `mespy.{module.name}`" if module.name != "__init__" else "## `mespy` (`__init__.py`)", ""]
        if module.imports:
            grouped: dict[str, list[str]] = {}
            for local, (source, _) in module.imports.items():
                grouped.setdefault(source, []).append(local)
            lines.append(
                "Importa da MesPy: "
                + "; ".join(f"`{src}` → {', '.join(f'`{n}`' for n in names)}" for src, names in grouped.items())
                + "."
            )
            lines.append("")
        if module.constants:
            lines += ["Costanti di modulo: " + ", ".join(f"`{c}`" for c in module.constants) + ".", ""]
        if module.aliases:
            lines += ["Alias di tipo: " + ", ".join(f"`{a}`" for a in module.aliases) + ".", ""]
        if module.module_calls:
            lines += [
                "Chiamate eseguite all'import: " + ", ".join(f"`{c}()`" for c in module.module_calls) + ".",
                "",
            ]
        if not module.entities:
            lines += ["_Nessuna funzione o classe._", ""]
            continue
        lines += ["| Riga | Nome | Tipo | Visibilità | Chiama (MesPy) | Note |", "|---:|---|---|---|---|---|"]
        for entity in sorted(module.entities.values(), key=lambda e: e.line):
            remarks = []
            if entity.decorators:
                remarks.append("decorator: " + ", ".join(f"`@{d}`" for d in entity.decorators))
            if entity.callbacks:
                remarks.append("invoca callback: " + ", ".join(f"`{c}`" for c in entity.callbacks))
            if entity.lazy_imports:
                remarks.append("import locale: " + ", ".join(f"`{i}`" for i in entity.lazy_imports))
            calls = ", ".join(f"`{c}`" for c in entity.calls) or "—"
            lines.append(
                f"| {entity.line} | `{entity.qualname}` | {entity.kind} | {visibility(entity, root_all)} "
                f"| {calls} | {'; '.join(remarks) or '—'} |"
            )
        lines.append("")

    lines += ["## Segnalazioni", ""]
    lines += [f"- {note}" for note in notes] or ["- Nessuna."]
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    modules: dict[str, Module] = {}
    for path in sorted(PACKAGE.glob("*.py")):
        module = Module(path.stem, path, ast.parse(path.read_text(encoding="utf-8")))
        collect(module)
        modules[module.name] = module

    resolver = Resolver(modules)
    notes: list[str] = []
    for module in modules.values():
        for entity in module.entities.values():
            unknown = [d for d in entity.decorators if d not in KNOWN_DECORATORS]
            if unknown:
                notes.append(
                    f"`{module.name}.{entity.qualname}`: decorator non riconosciuto "
                    + ", ".join(f"`@{d}`" for d in unknown)
                )
            resolver.analyse(module, entity, notes)
        for call in module.module_calls:
            notes.append(f"`{module.name}`: `{call}()` viene eseguita all'import del modulo (effetto collaterale)")
        if module.name != "__init__" and module.all_names:
            notes.append(f"`{module.name}` definisce un proprio `__all__`")

    # Nomi di metodo condivisi da più classi: la risoluzione dipende dal tipo del ricevente.
    methods: dict[str, list[str]] = {}
    for module in modules.values():
        for entity in module.entities.values():
            if entity.kind in ("metodo", "property"):
                methods.setdefault(entity.name, []).append(entity.qualname)
    for name, owners in methods.items():
        if len(owners) > 1:
            notes.append(
                f"metodo omonimo `{name}` in " + ", ".join(f"`{o}`" for o in owners)
                + ": risolto tramite il tipo annotato del ricevente"
            )

    text = render(modules, list(dict.fromkeys(notes)))
    if "--stdout" in sys.argv:
        print(text)
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"Scritto {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
