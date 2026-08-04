from __future__ import annotations

import argparse

from archilens.extract.tier0_iac.compose import parse_compose
from archilens.extract.tier0_iac.k8s import parse_k8s
from archilens.extract.tier0_iac.terraform import parse_terraform

TIER0_EXTRACTORS = [
    ("terraform", parse_terraform),
    ("compose", parse_compose),
    ("k8s", parse_k8s),
]


def scan(repo_path: str) -> None:
    all_nodes = []
    all_edges = []
    for source_name, extractor in TIER0_EXTRACTORS:
        nodes, edges = extractor(repo_path)
        for n in nodes:
            print(f"[node:{source_name}] {n.kind:<10} {n.identity:<40} {n.file}:{n.line}")
        for e in edges:
            print(f"[edge:{source_name}] {e.src} -> {e.dst}  {e.file}:{e.line}")
        all_nodes.extend(nodes)
        all_edges.extend(edges)
    print(f"\n{len(all_nodes)} nodes, {len(all_edges)} edges (tier 0, no LLM)")


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
