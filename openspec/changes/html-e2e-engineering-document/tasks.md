# Tasks: html-e2e-engineering-document

## Phase 1: Generator scaffolding

- [ ] 1.1 Create `docs/artifacts/tools/render_e2e_html.py` with CLI (`--check` flag for integrity verification, `--out` path defaulting to `docs/artifacts/reports/e2e-engineering-document.html`); import `load_artifact_index`, `load_links`, `Findings` from `corpus.py`
- [ ] 1.2 Implement corpus data loading: both profiles' artifacts, both link registries, parameter/assumption/source registries, scope-and-applicability; fail nonzero on missing/unparseable input
- [ ] 1.3 Implement HTML skeleton: doctype, embedded CSS (collapsible sections, tables, anchor styles), Mermaid CDN loader with `<noscript>` fallback, sticky table of contents, `data-generated-at` marker (the only run-varying field)

## Phase 2: Content sections (data → HTML)

- [ ] 2.1 Render stakeholder & system requirements section: per artifact, id/title anchor, statement, rationale, classification, ASIL, acceptance criteria, conditions/modes, source_refs (resolved to anchor strings), assumption_refs
- [ ] 2.2 Render system architecture section: context viewpoint diagram (scope boundaries/external systems), functional block diagram (SGO→FSR→TSR/SWR chain), dynamic sequence diagram of the cell-voltage protection chain — all Mermaid, data-derived from scope file and link registries
- [ ] 2.3 Render software requirements and software architecture sections: requirement cards with full attribute set; static component viewpoint diagram (SWR/DSN via `implements` links) and dynamic state diagrams from each design's `behavior_model`
- [ ] 2.4 Render detailed design per component: decomposition, interfaces, constraints, budgets, failure response; per-component static and dynamic Mermaid diagrams derived from design artifacts; label absent models as "not specified in corpus"
- [ ] 2.5 Render implementation mapping tables: per design artifact, mapped source file/symbol/status, hyperlinked chain SWR → design → source → verifying test measures
- [ ] 2.6 Render software integration report section: integrated components, integration evidence available in corpus, and integration gaps explicitly listed (never fabricated)
- [ ] 2.7 Render system verification section: test specifications (steps, oracles, environment), test cases, and execution reports from TMS/EXE artifacts with outcome and execution_kind
- [ ] 2.8 Render software verification section with unit/component/integration/HIL subsections; classify each execution by `execution_kind` and test type; distinguish actual_host_run from synthetic_fixture per governance policy
- [ ] 2.9 Render traceability matrix appendix: all 48+ links per profile with link_id, endpoints (anchor links), relation_type, rationale, provenance, review_state, change_suspect_status

## Phase 3: Integrity verification & acceptance

- [ ] 3.1 Implement `--check` integrity mode: assert all required section headings exist; assert every requirement artifact ID of both profiles appears ≥ once; assert every link ID appears in the matrix; on failure print missing IDs and exit nonzero
- [ ] 3.2 Implement determinism check: generate twice, byte-compare ignoring the `data-generated-at` attribute; document result in run output
- [ ] 3.3 Run `python3 docs/artifacts/tools/corpus.py validate` and full `check` — must remain 0 errors / PASSED with the new file present
- [ ] 3.4 Manually verify generated HTML in a browser: sections, anchors, diagrams (online), fallback text (offline)
- [ ] 3.5 Wire integrity check into acceptance suite behind a non-breaking option (or document standalone usage) so default `corpus.py check` behavior is unchanged
