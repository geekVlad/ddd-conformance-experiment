import re

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from ddd_conformance.model import ClassUnit, SourceUnit


def _walk(node: Node):
    yield node
    for child in node.named_children:
        yield from _walk(child)


def _text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def _variable_name(node: Node, source: bytes) -> str:
    return _text(node, source).lstrip("$")


def parse_php(source: str, path: str) -> SourceUnit:
    encoded = source.encode("utf-8")
    tree = get_parser("php").parse(encoded)
    if tree.root_node.has_error:
        raise SyntaxError(f"PHP parse error in {path}")

    imports = tuple(
        sorted(
            _text(qualified, encoded)
            for declaration in tree.root_node.named_children
            if declaration.type == "namespace_use_declaration"
            for qualified in declaration.named_children
            if qualified.type == "namespace_use_clause"
        )
    )

    classes: list[ClassUnit] = []
    for class_node in (node for node in _walk(tree.root_node) if node.type == "class_declaration"):
        name_node = class_node.child_by_field_name("name")
        body = class_node.child_by_field_name("body")
        if name_node is None or body is None:
            continue

        bases = tuple(
            _text(name, encoded)
            for clause in class_node.named_children
            if clause.type in {"base_clause", "class_interface_clause"}
            for name in clause.named_children
            if name.type in {"name", "qualified_name"}
        )

        fields = {
            _variable_name(variable, encoded)
            for declaration in body.named_children
            if declaration.type == "property_declaration"
            for variable in _walk(declaration)
            if variable.type == "variable_name"
        }
        methods: list[str] = []
        constructors: list[str] = []
        static_methods: list[str] = []
        accessor_methods: list[str] = []
        accesses: dict[str, tuple[str, ...]] = {}
        calls: dict[str, tuple[str, ...]] = {}
        for method in (child for child in body.named_children if child.type == "method_declaration"):
            method_name = method.child_by_field_name("name")
            if method_name is None:
                continue
            name = _text(method_name, encoded)
            methods.append(name)
            if name.lower() == "__construct":
                constructors.append(name)
            if any(child.type == "static_modifier" for child in method.named_children):
                static_methods.append(name)
            method_fields = {
                _text(member_name, encoded).lstrip("$")
                for member in _walk(method)
                if member.type == "member_access_expression"
                if (object_node := member.child_by_field_name("object")) is not None
                and _text(object_node, encoded) == "$this"
                if (member_name := member.child_by_field_name("name")) is not None
            }
            accesses[name] = tuple(sorted(method_fields))
            method_calls = {
                _text(member_name, encoded)
                for call in _walk(method)
                if call.type == "member_call_expression"
                if (object_node := call.child_by_field_name("object")) is not None
                and _text(object_node, encoded) == "$this"
                if (member_name := call.child_by_field_name("name")) is not None
            }
            calls[name] = tuple(sorted(method_calls))
            fields.update(method_fields)
            if (
                re.match(r"^(?:get|set|is|has)[A-Z_]", name)
                and len(method_fields) <= 1
                and not method_calls
            ):
                accessor_methods.append(name)

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
        language="php",
        path=path,
        imports=imports,
        classes=tuple(classes),
    )
