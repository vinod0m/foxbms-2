## Why

The corpus holds every engineering artifact as canonical JSON, but there is no set of formal, standalone specification documents per engineering discipline. A safety/ASPICE review needs the classic document set — Stakeholder Req Spec, System Req Spec, System Architecture Spec, SW Req Spec, SW Architecture Spec, Detailed Design Spec, System Verification Report, SW Verification Report, SW Integration Report, Implementation Mapping — each with diagrams and full requirement-to-test coverage. Markdown/HTML monoliths exist, but not the per-discipline documents reviewers and assessors expect.

## What Changes

- Generate 10 standalone specification documents (Markdown with embedded Mermaid diagrams + Word via pandoc) from the canonical corpus JSON, one per engineering discipline:
  1. **Stakeholder Requirements Specification** — item definition, use case, stakeholder needs from scope-and-applicability + hazard analysis premises
  2. **System Requirements Specification** — safety goals, FSRs with full attributes (statement, rationale, ASIL, acceptance criteria, assumptions, conditions/modes)
  3. **System Architecture Specification** — multiple viewpoints (context, functional block, dynamic protection-chain sequence), each as Mermaid diagram derived from scope + link registries
  4. **Software Requirements Specification** — SWRs + SW-facing TSRs with full attributes
  5. **Software Architecture Specification** — static (component) and dynamic (state/sequence) viewpoint Mermaid diagrams from design artifacts + link registries
  6. **Detailed Design Specification** — per-component static + dynamic diagrams from decomposition/interfaces/behavior_model, plus implementation requirements
  7. **Software Integration Report** — integrated components, integration evidence present in corpus, integration gaps listed explicitly
  8. **System Verification Report** — system-level test specification, test cases, execution report from TMS/EXE artifacts
  9. **Software Verification Report** — unit/component/integration/HIL sections, each with test specification, cases, execution reports; execution_kind classifications made explicit
  10. **Implementation Mapping Document** — design element → source file/symbol/status, with requirement→design→code→test chains and full requirement-to-test coverage matrix (including uncovered requirements, explicitly listed)
- Add a generator tool `docs/artifacts/tools/render_spec_documents.py` that reads canonical corpus JSON (via corpus.py loaders) and emits all 10 documents deterministically
- Word (.docx) versions generated via pandoc for each document
- A per-document integrity check: every corpus requirement ID must appear in its owning document; every requirement-to-test coverage row must state COVERED (direct/indirect) or UNCOVERED (explicit gap)

## Capabilities

### New Capabilities
- `spec-documents`: Generation of the 10 standalone per-discipline specification documents from the corpus — content requirements per document (sections, attributes, coverage), diagram requirements (Mermaid viewpoints, static/dynamic, data-derived), coverage matrix requirements, and regeneration/determinism/integrity requirements.

### Modified Capabilities
- (none — corpus artifacts, schemas, link registries, and validation behavior are untouched; generation is additive)

## Impact

- **New tool**: `docs/artifacts/tools/render_spec_documents.py` (imports corpus.py loaders; stdlib only)
- **New outputs**: `docs/artifacts/spec-documents/*.md` (10 files) + matching `*.docx` via pandoc
- **No changes** to corpus JSON, schemas, link registries, validation logic, foxBMS source/config/tests
- **Dependencies**: Python 3 stdlib; pandoc for .docx conversion (optional, skipped gracefully if absent)
- **Relation to prior change**: `html-e2e-engineering-document` (planning complete, unimplemented) targets one combined HTML file; this change targets the per-discipline document set. Both read the same corpus; implementations should share rendering helpers where practical.
