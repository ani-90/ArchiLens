# Eval cases

Test cases for the slicer (and later stages) discovered through real use, ahead of
the formal eval harness (phase 12). Each entry here is a candidate for that
harness's ground-truth suite once it exists — recorded now so the finding isn't
lost between now and then.

---

## Case 1: test file exclusion

**Discovered:** 2026-08-29, dogfooding `slice` against the ArchiLens repo itself.

**Query:** `slice("BM25 seeding for the slicer")`

**Expected:** returns source code nodes only — `slice.py`'s BM25/slicer functions
(`slice_graph`, `_bm25_scores`, `_relevant_ranked`, `_expand`, `_apply_cap`,
`_detect_ambiguity`), `assemble.py`'s `assemble_graph`, and the immediately
relevant pipeline stages that call into them.

**Failure mode observed (before fix):** the 60-node cap was dominated by test
files. `assemble_graph` is called by ~20 different `test_*.py` functions across
the suite; expansion is bidirectional (callers and callees both traversed), so
seeding near a widely-shared utility pulled in every test file that happens to
call it, at low hop-cost, crowding out the budget with test scaffolding instead
of the actual mechanism asked about. Confirmed reproducible — not a fixture
artifact — same pattern also hit `"resolve_cross_file_calls"` and `"hop budget
expansion"` in the same run.

**Root cause:** the extraction pipeline treats every `.py`/`.ts` file
identically — there is no distinction anywhere between production code and test
code, so a repo's own tests ride along as ordinary graph nodes with ordinary
call edges into the code they test.

**Pass condition (post-fix):** zero `test_*.py` nodes in any `slice_graph()`
result, for this query and in general.

**Status:** FIXED, 2026-08-29. Chose extraction-time exclusion (Option 1):
`tests`, `test`, `__tests__`, `spec`, `specs` added to `COMMON_SKIP_DIRS`
(`src/archilens/extract/__init__.py`) — same shared-constant mechanism as the
`.venv`/`node_modules` skip fix, so it applies to every extractor across every
tier automatically, not just the slicer. Directory-name matching only,
deliberately not filename-pattern matching (`foo.test.ts` alongside source is
still scanned) — consistent with every other entry in that set.

**Verified after fix:**
- `scan` on this repo: 354 → 98 nodes (test suite fully excluded from
  extraction, not just hidden from one query).
- `slice("BM25 seeding for the slicer")`: 11 nodes, 0 dropped for cap, every
  node is in `slice.py` (the actual implementation) or its one real caller
  (`cli.py:slice_cmd`) — zero `test_*.py` nodes. Pass condition met exactly.
- The other two queries that hit the cap in the same dogfooding run
  (`"resolve_cross_file_calls"`, `"hop budget expansion"`) also verified
  clean: 18 nodes/0 dropped, and correctly "no match" respectively.
- Determinism reconfirmed (two runs, byte-identical diff).
- Full test suite (177 tests) unaffected — no existing test passes the repo
  root into an extractor; all use narrow `tests/fixtures/...` paths, which
  are unaffected since `iter_files()` only prunes subdirectories discovered
  *during* the walk, never the walk's own starting directory or its
  ancestors.
