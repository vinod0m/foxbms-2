# Tasks: html-e2e-engineering-document

## Phase 1: Generator scaffolding

- [x] 1.1 Create `docs/artifacts/tools/render_e2e_html.py` with CLI (`--check` flag for integrity verification, `--out` path defaulting to `docs/artifacts/reports/e2e-engineering-document.html`); import `load_artifact_index`, `load_links`, `Findings` from `corpus.py`
- [x] 1.2 Implement corpus data loading: both profiles' artifacts, both link registries, parameter/assumption/source registries, scope-and-applicability; fail nonzero on missing/unparseable input
- [x] 1.3 Implement HTML skeleton: doctype, embedded CSS (collapsible sections, tables, anchor styles), Mermaid CDN loader with `<noscript>` fallback, sticky table of contents, `data-generated-at` marker (the only run-varying field)

## Phase 2: Content sections (data → HTML)

- [x] 2.1 Render stakeholder & system requirements section: per artifact, id/title anchor, statement, rationale, classification, ASIL, acceptance criteria, conditions/modes, source_refs (resolved to anchor strings), assumption_refs
- [x] 2.2 Render system architecture section: context viewpoint diagram (scope boundaries/external systems), functional block diagram (SGO→FSR→TSR/SWR chain), dynamic sequence diagram of the cell-voltage protection chain — all Mermaid, data-derived from scope file and link registries
- [x] 2.3 Render software requirements and software architecture sections: requirement cards with full attribute set; static component viewpoint diagram (SWR/DSN via `implements` links) and dynamic state diagrams from each design's `behavior_model`
- [x] 2.4 Render detailed design per component: decomposition, interfaces, constraints, budgets, failure response; per-component static and dynamic Mermaid diagrams derived from design artifacts; label absent models as "not specified in corpus"
- [x] 2.5 Render implementation mapping tables: per design artifact, mapped source file/symbol/status, hyperlinked chain SWR → design → source → verifying test measures
- [x] 2.6 Render software integration report section: integrated components, integration evidence available in corpus, and integration gaps explicitly listed (never fabricated)
- [x] 2.7 Render system verification section: test specifications (steps, oracles, environment), test cases, and execution reports from TMS/EXE artifacts with outcome and execution_kind
- [x] 2.8 Render software verification section with unit/component/integration/HIL subsections; classify each execution by `execution_kind` and test type; distinguish actual_host_run from synthetic_fixture per governance policy
- [x] 2.9 Render traceability matrix appendix: all 48+ links per profile with link_id, endpoints (anchor links), relation_type, rationale, provenance, review_state, change_suspect_status

## Phase 3: Integrity verification & acceptance

- [x] 3.1 Implement `--check` integrity mode: assert all required section headings exist; assert every requirement artifact ID of both profiles appears ≥ once; assert every link ID appears in the matrix; on failure print missing IDs and exit nonzero
- [x] 3.2 Implement determinism check: generate twice, byte-compare ignoring the `data-generated-at` attribute; document result in run output
- [x] 3.3 Run `python3 docs/artifacts/tools/corpus.py validate` and full `check` — must remain 0 errors / PASSED with the new file present
- [x] 3.4 Manually verify generated HTML in a browser: sections, anchors, diagrams (online), fallback text (offline)
- [x] 3.5 Wire integrity check into acceptance suite behind a non-breaking option (or document standalone usage) so default `corpus.py check` behavior is unchanged

---

## Implementation notes

Recorded after implementation so the task list reflects what was actually built
and where the build departs from the letter of the task text. The deliverable is
`docs/artifacts/reports/e2e-engineering-document.html`; the generator is
`docs/artifacts/tools/render_e2e_html.py`.

### Commands

```
python3 docs/artifacts/tools/render_e2e_html.py                  # generate
python3 docs/artifacts/tools/render_e2e_html.py --check          # integrity + determinism
python3 docs/artifacts/tools/render_e2e_html.py --audit-guard    # guard/conformity audit
python3 docs/artifacts/tools/render_e2e_html.py --validate-mermaid
```

### Deviations from the task text, with reasons

1. **Task 2.9 says "all 48+ links per profile".** The link registries hold 460
   links (111 `as_is`, 349 `synthetic_reference`) at implementation time, not 48.
   The document renders every one of them, not a subset. The "48" figure in
   `design.md` predates the current registry growth.
2. **Task 3.5 — standalone, not wired into `corpus.py check`.** The task offers
   "behind a non-breaking option **or** document standalone usage"; the second
   option was taken, because `docs/artifacts/tools/corpus.py` is owned by a
   concurrent agent and must not be edited. `design.md` decision 1 already
   declines to extend `corpus.py` "to keep the acceptance tool stable and
   auditable". `corpus.py check` is unchanged and still PASSES. Wiring it later
   is a one-line call to `render_e2e_html.verify_html()`.
3. **Task 1.3 — anchors are `art-<profile>-<id>`, not `art-<id>`.** The same
   artifact identifier exists in both profiles as two different records by
   corpus design, so an un-namespaced HTML `id` cannot address both and would be
   an invalid duplicate id. The convention is stated in the document itself.
4. **Task 3.4 — "manually verify in a browser" was performed as a structural
   and tooling verification, not a human reading of a rendered window.** What
   was actually done and is evidenced: HTML element balance checked tag by tag;
   every one of the 33 Mermaid blocks syntax-checked and rendered to SVG with
   `mermaid-cli` against local Chrome (33/33); the offline fallback path checked
   by reading the emitted markup (each diagram is a `<pre>` holding its own
   source plus a `<noscript>` block). A visual check in a browser window was not
   performed and is not claimed.
5. **Diagram validation is not embedded in the document.** Embedding the
   `mermaid-cli` result would make the file depend on an external tool's outcome
   and would break the byte-determinism task 3.2 requires. Section 13 of the
   document states this and records, per diagram, its id, Mermaid type, viewpoint
   and derivation — and explicitly records that no diagram was syntax-checked by
   the file. The check runs as the separate `--validate-mermaid` step.
