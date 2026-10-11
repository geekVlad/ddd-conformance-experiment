import ast

from ddd_conformance.model import ClassUnit, SourceUnit


def _import_names(tree: ast.Module) -> tuple[str, ...]:
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names.extend(f"{module}.{alias.name}".strip(".") for alias in node.names)
    return tuple(sorted(names))


def _self_fields(method: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    fields = {
        node.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }
    return tuple(sorted(fields))


def _self_method_calls(method: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    calls = {
        node.func.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
    }
    return tuple(sorted(calls))


def _decorator_name(decorator: ast.expr) -> str:
    return ast.unparse(decorator)


def parse_python(source: str, path: str) -> SourceUnit:
    tree = ast.parse(source, filename=path)
    classes: list[ClassUnit] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods = [
            child
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        accesses = {method.name: _self_fields(method) for method in methods}
        calls = {method.name: _self_method_calls(method) for method in methods}
        fields = tuple(sorted({field for values in accesses.values() for field in values}))
        decorators = {
            method.name: tuple(_decorator_name(item) for item in method.decorator_list)
            for method in methods
        }
        classes.append(
            ClassUnit(
                name=node.name,
                methods=tuple(method.name for method in methods),
                fields=fields,
                method_field_accesses=accesses,
                method_calls=calls,
                bases=tuple(ast.unparse(base) for base in node.bases),
                constructors=tuple(method.name for method in methods if method.name == "__init__"),
                static_methods=tuple(
                    method.name
                    for method in methods
                    if set(decorators[method.name]) & {"staticmethod", "classmethod"}
                ),
                accessor_methods=tuple(
                    method.name
                    for method in methods
                    if any(
                        decorator == "property"
                        or decorator.endswith((".getter", ".setter", ".deleter"))
                        for decorator in decorators[method.name]
                    )
                ),
            )
        )
    return SourceUnit(
        language="python",
        path=path,
        imports=_import_names(tree),
        classes=tuple(classes),
    )
