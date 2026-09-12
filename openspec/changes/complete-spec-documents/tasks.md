# Tasks: complete-spec-documents

## Phase 1: Generator scaffolding

- [x] 1.1 Create `docs/artifacts/tools/render_spec_documents.py` with CLI (positional `docs` selector optional; `--check` integrity mode; `--out-dir` default `docs/artifacts/spec-documents/`); import `load_artifact_index`, `load_links` from `corpus.py`; fail fast on missing/unparseable inputs
- [x] 1.2 Build shared in-memory views: profile-aware artifact index, links-by-relation index, document ownership map (doc → owned artifact classes), and coverage computation (direct verifies / indirect via allocated children / embedded TMS referenced_requirements; statuses COVERED-DIRECT / COVERED-INDIRECT / COVERED-EMBEDDED / UNCOVERED)
- [x] 1.3 Implement Markdown document scaffold: title, document control block, scope, section templates, `Generated:` timestamp line; pandoc availability guard + per-doc `.docx` conversion helper

## Phase 2: Requirement & architecture documents

- [x] 2.1 Emit Stakeholder Requirements Specification: item definition, boundaries, operational situations, modes, external systems, stakeholder needs from `governance/scope-and-applicability.json` with source artifact IDs cited
- [x] 2.2 Emit System Requirements Specification: every safety goal + FSR (both profiles) with 9 attribute groups (id, title, statement, rationale, ASIL, safety-goal ref, acceptance criteria, conditions/modes, source + assumption refs)
- [x] 2.3 Emit System Architecture Specification: Mermaid context viewpoint (scope boundaries/actors), functional block viewpoint (protection chain from links), dynamic sequence viewpoint (HAZ→SGO→FSR→TSR/SWR→DSN→TMS chain), each with caption fallback
- [x] 2.4 Emit Software Requirements Specification: every SWR + SW-facing TSR with full attributes, grouped under parent FSR with `allocated_to` rationale quoted
- [x] 2.5 Emit Software Architecture Specification: static component Mermaid diagram (SWR/DSN via `implements`), dynamic state diagrams from each `behavior_model`, task/thread context diagram from timing-budget elements
- [x] 2.6 Emit Detailed Design Specification: per design artifact — responsibilities, decomposition, interface signal tables (name/direction/type/unit/range/rate), constraints, budgets, failure response, static + dynamic per-component diagrams; "not specified in corpus" labels for absent models; implementation requirements extracted from design fields with source cited

## Phase 3: Verification, integration & mapping documents

- [x] 3.1 Emit Software Integration Report: integrated components (from `implements` chains), available integration evidence (executions by kind), explicit integration gap list with dispositions (blocked-not-fabricated policy cited)
- [x] 3.2 Emit System Verification Report: system-level test specs (objective, preconditions, steps, expected outcomes, oracle, environment), test cases, execution reports from TMS/EXE with outcome + execution_kind + evidence refs
- [x] 3.3 Emit Software Verification Report: unit / component / integration / HIL sections, each with test specification, cases, execution report; every execution labeled with execution_kind; actual_host_run vs synthetic_fixture visually distinguished; explicit note where no HIL evidence exists
- [x] 3.4 Emit Implementation Mapping Document: per design artifact, mapping entries (source file, symbol, status); per SWR the full chain SWR → design → source files → verifying TMS with artifact IDs cited
- [x] 3.5 Add requirement-to-test coverage matrix to the Implementation Mapping Document: one row per requirement artifact (FSR/TSR/SWR/management, both profiles) with direct links, indirect coverage, status (COVERED-DIRECT / COVERED-INDIRECT / COVERED-EMBEDDED / UNCOVERED), verifying TMS, and gap note for UNCOVERED rows

## Phase 4: Verification & acceptance

- [x] 4.1 Implement `--check` integrity mode: per document verify (a) required headings, (b) every owned artifact ID present, (c) coverage matrix has a row per requirement artifact; failures name missing IDs, exit nonzero
- [x] 4.2 Determinism check: run generator twice, byte-compare all ten Markdown files ignoring the `Generated:` line
- [x] 4.3 Run `python3 docs/artifacts/tools/corpus.py validate` and full `check` — must remain 0 errors / PASSED
- [x] 4.4 Generate all `.docx` versions via pandoc (guard for absence) and spot-check one Word file for section/table integrity
- [x] 4.5 Manual review pass: confirm UNCOVERED requirements are explicit in the matrix and match the coverage audit (as_is: FSR-001/004 + 3 HW TSRs + SWR-001; synthetic_reference: all 12)
