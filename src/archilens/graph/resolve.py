"""Identity resolution, step A: same-file/same-scope call resolution.

Tier 2's call edges record the callee exactly as written in source (e.g.
`this.validate`, `doLocalWork`) because the AST parser has no notion of
which name resolves to which declaration -- that's not its job. assemble_graph
correctly drops these as dangling, since the raw text doesn't match any
node's qualified identity.

This pass recovers the subset that's resolvable with zero ambiguity, using
only information already present on the edge and in the graph:

  - `self.foo` / `this.foo` (chain starts with self/this, length >= 2):
    the caller's own src identity tells us the enclosing class, so the
    target must be `{file}:{enclosing_class}.{foo}`.
  - bare calls (chain length 1, not flagged likely_import_alias): the
    target must be a module-level declaration in the same file,
    `{file}:{name}`.

Anything else (an import-aliased call like `write_object`, a call through a
non-self/this receiver like `obj.method()`) requires cross-file resolution
or type information this pass doesn't have, and is deliberately left
dropped rather than guessed at -- that's step B.
"""
from __future__ import annotations

from archilens.extract.schema import EdgeRecord
from archilens.graph.assemble import AssemblyResult


def _candidate_identity(edge: EdgeRecord) -> str | None:
    if edge.tier != 2:
        return None
    chain = edge.attrs.get("callee_chain")
    if not chain:
        return None

    file = edge.file
    qualname = edge.src[len(file) + 1 :] if edge.src.startswith(file + ":") else ""

    if len(chain) >= 2 and chain[0] in ("self", "this"):
        enclosing_class = qualname.split(".")[0] if qualname else None
        if enclosing_class is None:
            return None
        return f"{file}:{enclosing_class}.{'.'.join(chain[1:])}"

    if len(chain) == 1 and chain[0] not in ("self", "this"):
        if edge.attrs.get("likely_import_alias"):
            return None
        return f"{file}:{chain[0]}"

    return None


def resolve_same_scope_calls(assembly: AssemblyResult) -> AssemblyResult:
    graph = assembly.graph
    still_dropped: list[EdgeRecord] = []

    for edge in assembly.dropped_edges:
        candidate = _candidate_identity(edge)
        if (
            candidate is not None
            and graph.has_node(candidate)
            and graph.has_node(edge.src)
        ):
            graph.add_edge(edge.src, candidate, evidence=edge)
        else:
            still_dropped.append(edge)

    return AssemblyResult(graph=graph, dropped_edges=still_dropped)
