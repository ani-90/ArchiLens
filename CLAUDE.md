# ArchiLens — project instructions

MCP server that reads a repo and produces an evidence-cited (`file:line`-traceable) architecture graph. Full spec: see memory `project_archilens_spec.md`. 13-phase build order, phases 1-7 have zero LLM calls — don't add LLM code until phase 8.

## Current status (update this section whenever a phase completes or work resumes)

**Last updated:** 2026-08-28

Phases 0-4 complete and merged to `main` (clean tree, 164 tests passing):
- Phase 0: scaffold
- Phase 1: Tier 0 IaC extractors (Terraform, docker-compose, Dockerfile, k8s)
- Phase 2: Tier 1 YAML regex rule engine
- Phase 3: Tier 2 tree-sitter AST extractors (Python, TypeScript)
- Phase 4: graph assembly (NetworkX) + identity resolution + SHA-256 extraction cache

**Next up:** Phase 5 — slicer (BM25 seed + k-hop expand, ≤60 nodes).

Not started: slicer, IR schema + verifier, layout/draw.io rendering, abstraction LLM pass, MCP server surface, tier 3 LLM extraction, eval harness.

## V1 public release target: through Phase 10

Decided 2026-08-28. Phase 10 (full MCP surface) is the release bar, not earlier:
- Phases 0-6 only produce graphs/slices — no usable output, no MCP server. Not a product.
- Phase 7 (layout + draw.io renderer) gives a real output file, but it's raw structural nodes — unreadable as an architecture diagram.
- Phase 8 (abstraction LLM pass) is the first point where output looks like an actual architecture diagram (grouped/named components, not one box per function).
- Phase 9 (`trace_edge`) makes the evidence-cited claim actually checkable by a user — click an arrow, see why it's there.
- Phase 10 (full MCP surface: `scan`, `generate_diagram`, `trace_edge`, sampling for zero-API-key installs) is the actual product boundary — before this it's a CLI script, after this it's an installable MCP server.

**Explicitly deferred to v1.1+:**
- Phase 11 (tier 3 LLM extraction) — v1 ships with tier0-2 coverage (Python/TS/IaC); other languages just extract less, not blocking.
- Phase 12 (eval harness) — needed before making public hallucination-rate claims in marketing, but not a runtime dependency; do this right after v1 ships.
- Phase 13 (CI gating, `diff_against_commit`, freeform mode) — genuine v2 features.

So: **5 more phases after the current one (5→6→7→8→9→10)** stand between here and a public v1.

## Working agreement

- At the start of a session, read this status section and just proceed — don't ask the user where the project stands.
- After any commit that finishes or advances a phase, update the "Current status" section above (and the date) in the same turn.
- Also update the published "ArchiLens, explained" interview-FAQ artifact whenever a phase completes: https://claude.ai/code/artifact/85d1a127-451e-4688-ab14-f9f8f5c0946b — update the pipeline strip, status pills, footer phase count, and add/revise Q&A sections covering the newly completed work.
