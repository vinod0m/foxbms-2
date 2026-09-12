## Context

Corpus at `docs/artifacts/` (65 artifacts, 48 links, 42 anchors, 12 assumptions, 10 parameters) is validated by `corpus.py`, which already exposes stable loaders: `load_artifact_index` (profile-aware `(profile,id)` keys), `load_links` (profile-tagged, deduped), plus registries. An audit found requirement-to-test coverage is partial: as_is has 4/9 requirements covered (direct+indirect), synthetic_reference 0/12 — the coverage matrix must therefore show UNCOVERED rows explicitly rather than hiding them. A prior planned change (`html-e2e-engineering-document`) targets a single combined HTML file; this change targets the per-discipline document set. foxBMS source/config/tests must remain untouched.

## Goals / Non-Goals

**Goals:**
- Ten standalone per-discipline documents, each self-contained (scope, definitions where needed, corpus-derived content, cited artifact IDs)
- Mermaid diagrams data-derived from scope file, link registries, and design `behavior_model`/`decomposition`/`interfaces` — never hand-drawn
- Complete requirement-to-test coverage matrix across FSR/TSR/SWR in both profiles, with explicit UNCOVERED rows and gap notes
- Deterministic Markdown + optional pandoc .docx; per-document integrity check

**Non-Goals:**
- No corpus/schema/link/validation changes; no foxBMS source/config/test edits
- No evidence fabrication: gaps stay gaps, labeled per governance policy (blocked, not fabricated)
- No live-HTML interactivity; Markdown/Word are the deliverables
- No duplicate of the combined-HTML change; shared helpers may be extracted later if both are implemented

## Decisions

**1. One generator script, ten emit functions**
`docs/artifacts/tools/render_spec_documents.py` imports `corpus.py` loaders once, builds shared in-memory views (artifact index, link index by relation, coverage map), then calls one `emit_<doc>` function per document. Alternative: ten scripts — rejected (loading duplicated, drift risk).

**2. Document ownership map drives integrity checking**
Each document declares the artifact set it owns (e.g., SysRS owns `safety_goal` + `FSR`; SWRS owns `SWR` + SW-facing TSR). The `--check` mode verifies every owned ID appears in the rendered text. This makes the check data-driven instead of heading-heuristics only.

**3. Coverage computed via three passes, fixed status vocabulary**
For each requirement artifact (any `requirement` type incl. management): (a) direct `verifies`/`validates` links; (b) indirect coverage via `allocated_to` children; (c) embedded coverage via TMS `referenced_requirements`. Status ∈ {COVERED-DIRECT, COVERED-INDIRECT, COVERED-EMBEDDED, UNCOVERED}. The same function feeds the coverage matrix and the gap notes — single source of truth, matching the audit script's logic.

**4. Mermaid emitted as fenced blocks with caption fallback**
Diagrams are `flowchart`/`stateDiagram-v2`/`sequenceDiagram` sources derived purely from data; each block preceded by a one-line caption so Word/text readers stay usable. Pandoc renders fenced code as code blocks in .docx (acceptable per spec; captions carry the meaning). PlantUML considered and rejected: needs Java at view time.

**5. Profile presentation: one combined column set**
Documents render both profiles side-by-side where content overlaps (tables gain a "Profile" column) since artifacts share IDs across profiles; the coverage matrix keys rows by `(profile, id)`.

**6. Pandoc conversion guarded**
`shutil.which('pandoc')` check; per-doc `pandoc <md> -o <docx> --toc -M title=...` with `--metadata` from a per-document manifest; absence of pandoc logs a warning and continues (spec scenario).

**7. Determinism**
Sorted iteration everywhere; fixed doc order; only a `Generated: <iso8601>` line may vary, excluded from byte-compare in `--check`.

## Risks / Trade-offs

- [Sparse design models → thin diagrams] → fields absent in corpus render "not specified in corpus" labels; never dropped silently
- [Coverage matrix exposes 17 UNCOVERED requirements] → intentional: this is the honest state; gap notes cite the review dispositions that already track these gaps
- [Docx diagram fidelity via pandoc is code-block only] → captions + surrounding tables carry the normative content; HTML change covers rich rendering needs
- [Shared-loader import coupling] → import only stable helpers; generator fails fast at import time on signature drift

## Migration Plan

Additive: new script + `docs/artifacts/spec-documents/` outputs. No existing behavior changes. Rollback = delete script + outputs. `corpus.py check` untouched (integrity check runs via the new tool's `--check`).

## Open Questions

None — document set, viewpoints, coverage semantics, and integrity rules are fully pinned by the delta spec and the corpus audit.
