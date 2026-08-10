"""Tier 2 extractor: tree-sitter AST for Python.

Single-file parsing only. An import's module string and a call's callee
chain are emitted exactly as the AST states them -- resolving either
against another file's definitions is Stage 2 (graph assembly)'s job, not
this tier's. See docs/tier2_ast_schema.md for the emission contract this
module implements.
"""
from __future__ import annotations

from pathlib import Path

from tree_sitter import Language, Node, Parser
import tree_sitter_python as tspython

from archilens.extract.schema import EdgeRecord, EvidenceRecord

TIER = 2
CONFIDENCE = 1.0

_SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
}

_LANGUAGE = Language(tspython.language())


def _iter_py_files(repo_path: Path):
    for path in repo_path.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def _text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _line(node: Node) -> int:
    return node.start_point[0] + 1


def _flatten_callee(node: Node, source: bytes) -> list[str]:
    """Turn a call's `function` field into an attribute chain list, e.g.
    `writer.put_object` -> ["writer", "put_object"]. Falls back to the raw
    source text as a single-element chain for shapes that aren't a plain
    identifier/attribute walk (e.g. `foo()()`) -- rare, and still a
    faithful (if unstructured) record of what's there."""
    if node.type == "identifier":
        return [_text(node, source)]
    if node.type == "attribute":
        obj = node.child_by_field_name("object")
        attr = node.child_by_field_name("attribute")
        chain = _flatten_callee(obj, source) if obj is not None else []
        if attr is not None:
            chain = chain + [_text(attr, source)]
        return chain
    return [_text(node, source)]


def parse_python_ast(repo_path: str | Path) -> tuple[list[EvidenceRecord], list[EdgeRecord]]:
    repo_path = Path(repo_path)
    parser = Parser(_LANGUAGE)

    nodes: list[EvidenceRecord] = []
    edges: list[EdgeRecord] = []

    for py_file in _iter_py_files(repo_path):
        try:
            source = py_file.read_bytes()
            tree = parser.parse(source)
        except Exception:
            # Malformed/unreadable file: degrade gracefully, don't crash the scan.
            continue

        file_str = str(py_file)
        import_table: dict[str, str] = {}

        def scope_identity(scope_stack: list[str]) -> str:
            return f"{file_str}:{'.'.join(scope_stack)}" if scope_stack else file_str

        def handle_import(node: Node, scope_stack: list[str]) -> None:
            raw = _text(node, source)
            line = _line(node)
            src_identity = scope_identity(scope_stack)

            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        module = _text(child, source)
                        import_table[module.split(".")[0]] = module
                        emit_import(src_identity, module, [], raw, line)
                    elif child.type == "aliased_import":
                        dotted = child.child_by_field_name("name")
                        alias = child.child_by_field_name("alias")
                        module = _text(dotted, source) if dotted is not None else ""
                        alias_name = _text(alias, source) if alias is not None else module
                        import_table[alias_name] = module
                        emit_import(src_identity, module, [], raw, line)
            else:  # import_from_statement
                module_node = node.child_by_field_name("module_name")
                module = _text(module_node, source) if module_node is not None else ""
                names: list[str] = []
                for child in node.children:
                    if module_node is not None and child.start_byte == module_node.start_byte and child.end_byte == module_node.end_byte:
                        continue
                    if child.type == "dotted_name":
                        name = _text(child, source)
                        names.append(name)
                        import_table[name] = f"{module}.{name}"
                    elif child.type == "aliased_import":
                        dotted = child.child_by_field_name("name")
                        alias = child.child_by_field_name("alias")
                        name = _text(dotted, source) if dotted is not None else ""
                        alias_name = _text(alias, source) if alias is not None else name
                        names.append(name)
                        import_table[alias_name] = f"{module}.{name}"
                    elif child.type == "wildcard_import":
                        names.append("*")
                emit_import(src_identity, module, names, raw, line)

        def emit_import(src_identity: str, module: str, names: list[str], raw: str, line: int) -> None:
            edges.append(
                EdgeRecord(
                    src=src_identity,
                    dst=module,
                    file=file_str,
                    line=line,
                    tier=TIER,
                    confidence=CONFIDENCE,
                    attrs={"kind": "import", "module": module, "names": names, "raw": raw},
                )
            )

        def handle_call(node: Node, scope_stack: list[str]) -> None:
            func = node.child_by_field_name("function")
            if func is None:
                return
            chain = _flatten_callee(func, source)
            if not chain:
                return
            likely_alias = chain[0] in import_table
            edges.append(
                EdgeRecord(
                    src=scope_identity(scope_stack),
                    dst=".".join(chain),
                    file=file_str,
                    line=_line(node),
                    tier=TIER,
                    confidence=CONFIDENCE,
                    attrs={"callee_chain": chain, "likely_import_alias": likely_alias},
                )
            )

        def visit_def_or_class(node: Node, scope_stack: list[str], kind: str) -> None:
            name_node = node.child_by_field_name("name")
            name = _text(name_node, source) if name_node is not None else "<anonymous>"
            qualname = ".".join(scope_stack + [name])
            nodes.append(
                EvidenceRecord(
                    kind=kind,
                    identity=f"{file_str}:{qualname}",
                    file=file_str,
                    line=_line(node),
                    tier=TIER,
                    confidence=CONFIDENCE,
                    attrs={"name": name, "qualname": qualname},
                )
            )
            body = node.child_by_field_name("body")
            if body is not None:
                walk(body, scope_stack + [name])

        def visit(node: Node, scope_stack: list[str]) -> None:
            if node.type == "decorated_definition":
                for deco in node.children:
                    if deco.type == "decorator":
                        walk(deco, scope_stack)
                inner = node.child_by_field_name("definition")
                if inner is not None:
                    visit(inner, scope_stack)
                return
            if node.type == "function_definition":
                visit_def_or_class(node, scope_stack, "function")
                return
            if node.type == "class_definition":
                visit_def_or_class(node, scope_stack, "class")
                return
            if node.type in ("import_statement", "import_from_statement"):
                handle_import(node, scope_stack)
                return
            if node.type == "call":
                handle_call(node, scope_stack)
                walk(node, scope_stack)
                return
            walk(node, scope_stack)

        def walk(node: Node, scope_stack: list[str]) -> None:
            for child in node.children:
                visit(child, scope_stack)

        walk(tree.root_node, [])

    return nodes, edges
