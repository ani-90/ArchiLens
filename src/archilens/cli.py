from __future__ import annotations

import argparse

from archilens.cache import ExtractionCache
from archilens.extract.tier0_iac.compose import parse_compose
from archilens.extract.tier0_iac.k8s import parse_k8s
from archilens.extract.tier0_iac.terraform import parse_terraform
from archilens.extract.tier1_rules.engine import parse_tier1_rules
from archilens.extract.tier2_ast.python import parse_python_ast
from archilens.extract.tier2_ast.typescript import parse_typescript_ast
from archilens.graph.assemble import assemble_graph
from archilens.graph.resolve import (
    resolve_build_context_containment,
    resolve_cross_file_calls,
    resolve_same_scope_calls,
)

EXTRACTORS = [
    ("terraform", parse_terraform),
    ("compose", parse_compose),
    ("k8s", parse_k8s),
    ("tier1", parse_tier1_rules),
    ("python", parse_python_ast),
    ("typescript", parse_typescript_ast),
]

# Tier 0 IaC extractors are cheap (few files, no tree-sitter parsing) and
# aren't wired into the cache yet -- only the two AST parsers and the
# regex-per-source-file tier 1 engine, where re-parsing on every scan is
# actually expensive, opt in.
_CACHEABLE = {"tier1", "python", "typescript"}


def scan(repo_path: str) -> None:
    cache = ExtractionCache(repo_path)

    all_nodes = []
    all_edges = []
    for source_name, extractor in EXTRACTORS:
        if source_name in _CACHEABLE:
            nodes, edges = extractor(repo_path, cache=cache)
        else:
            nodes, edges = extractor(repo_path)
        for n in nodes:
            print(f"[node:{source_name}] {n.kind:<10} {n.identity:<40} {n.file}:{n.line}")
        for e in edges:
            print(f"[edge:{source_name}] {e.src} -> {e.dst}  {e.file}:{e.line}")
        all_nodes.extend(nodes)
        all_edges.extend(edges)
    cache.flush()
    print(f"\n{len(all_nodes)} nodes, {len(all_edges)} edges (tiers 0-2, no LLM)")

    result = assemble_graph(all_nodes, all_edges)
    before_same_scope = len(result.dropped_edges)
    result = resolve_same_scope_calls(result)
    resolved_same_scope = before_same_scope - len(result.dropped_edges)

    before_cross_file = len(result.dropped_edges)
    result = resolve_cross_file_calls(result)
    resolved_cross_file = before_cross_file - len(result.dropped_edges)

    before_containment_edges = result.graph.number_of_edges()
    result = resolve_build_context_containment(result)
    resolved_containment = result.graph.number_of_edges() - before_containment_edges

    print(
        f"assembled graph: {result.graph.number_of_nodes()} nodes, "
        f"{result.graph.number_of_edges()} edges, "
        f"{len(result.dropped_edges)} edges dropped (no matching node), "
        f"{resolved_same_scope} resolved via same-scope calls, "
        f"{resolved_cross_file} resolved via cross-file calls, "
        f"{resolved_containment} added via build-context containment"
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="archilens")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Structural graph only, no LLM")
    scan_p.add_argument("repo_path")

    args = parser.parse_args()
    if args.command == "scan":
        scan(args.repo_path)


if __name__ == "__main__":
    main()
