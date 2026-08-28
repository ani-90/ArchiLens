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

## Working agreement

- At the start of a session, read this status section and just proceed — don't ask the user where the project stands.
- After any commit that finishes or advances a phase, update the "Current status" section above (and the date) in the same turn.
