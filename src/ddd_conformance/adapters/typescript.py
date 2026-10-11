from pathlib import Path

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from ddd_conformance.model import ClassUnit, SourceUnit


def _walk(node: Node):
    yield node
    for child in node.named_children:
        yield from _walk(child)


def _text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def parse_typescript(source: str, path: str) -> SourceUnit:
    encoded = source.encode("utf-8")
    grammar = "tsx" if Path(path).suffix.lower() == ".tsx" else "typescript"
    tree = get_parser(grammar).parse(encoded)
    if tree.root_node.has_error:
        raise SyntaxError(f"TypeScript parse error in {path}")

    imports = tuple(
        sorted(
            _text(fragment, encoded)
            for statement in tree.root_node.named_children
            if statement.type == "import_statement"
            for fragment in _walk(statement)
            if fragment.type == "string_fragment"
        )
    )

    classes: list[ClassUnit] = []
    for class_node in (node for node in _walk(tree.root_node) if node.type == "class_declaration"):
        name_node = class_node.child_by_field_name("name")
        body = class_node.child_by_field_name("body")
        if name_node is None or body is None:
            continue

        heritage = next(
            (child for child in class_node.named_children if child.type == "class_heritage"),
            None,
        )
        heritage_children = heritage.named_children if heritage is not None else []
        bases = tuple(
            _text(value, encoded)
            for clause in heritage_children
            for value in clause.named_children
            if value.type in {"identifier", "type_identifier", "generic_type"}
        )

        fields = {
            _text(name, encoded)
            for child in body.named_children
            if child.type in {"public_field_definition", "property_signature"}
            if (name := child.child_by_field_name("name")) is not None
        }
        methods: list[str] = []
        constructors: list[str] = []
        static_methods: list[str] = []
        accessor_methods: list[str] = []
        accesses: dict[str, tuple[str, ...]] = {}
        calls: dict[str, tuple[str, ...]] = {}
        for method in (child for child in body.named_children if child.type == "method_definition"):
            method_name = method.child_by_field_name("name")
            if method_name is None:
                continue
            name = _text(method_name, encoded)
            methods.append(name)
            child_types = {child.type for child in method.children}
            if name == "constructor":
                constructors.append(name)
            if "static" in child_types:
                static_methods.append(name)
            if child_types & {"get", "set"}:
                accessor_methods.append(name)
            method_fields = {
                _text(property_node, encoded)
                for member in _walk(method)
                if member.type == "member_expression"
                if (object_node := member.child_by_field_name("object")) is not None
                and object_node.type == "this"
                if (property_node := member.child_by_field_name("property")) is not None
            }
            accesses[name] = tuple(sorted(method_fields))
            method_calls = {
                _text(property_node, encoded)
                for call in _walk(method)
                if call.type == "call_expression"
                if (function_node := call.child_by_field_name("function")) is not None
                and function_node.type == "member_expression"
                if (object_node := function_node.child_by_field_name("object")) is not None
                and object_node.type == "this"
                if (property_node := function_node.child_by_field_name("property")) is not None
            }
            calls[name] = tuple(sorted(method_calls))
            fields.update(method_fields)

        classes.append(
            ClassUnit(
                name=_text(name_node, encoded),
                methods=tuple(methods),
                fields=tuple(sorted(fields)),
                method_field_accesses=accesses,
                method_calls=calls,
                bases=bases,
                constructors=tuple(constructors),
                static_methods=tuple(static_methods),
                accessor_methods=tuple(accessor_methods),
            )
        )

    return SourceUnit(
        language="typescript",
        path=path,
        imports=imports,
        classes=tuple(classes),
    )
