## Why

The corpus (`docs/artifacts/`) contains all lifecycle artifacts as JSON with machine-verified traceability links, but there is no single human-navigable document that presents the complete engineering story end-to-end. Reviewers, assessors, and new engineers must currently cross-reference dozens of JSON files to follow a stakeholder requirement down to a HIL test report. A self-contained HTML document with embedded diagrams (Mermaid), full attribute tables, and live linkages closes this gap.

## What Changes

- Generate a complete single-file HTML engineering document (`docs/artifacts/reports/e2e-engineering-document.html`) from the existing corpus data, containing:
  - Stakeholder requirements and system requirements (with attributes, rationale, acceptance criteria)
  - System architecture with multiple viewpoint diagrams (Mermaid): context, functional block, dynamic sequence/flow
  - Software requirements and software architecture with static (component) and dynamic (state/sequence) viewpoint diagrams
  - Detailed design of components with static and dynamic design diagrams per component
  - Implementation mapping (design element → source file/symbol with status)
  - System verification artifacts: test specifications, test cases, execution reports
  - Software verification artifacts: unit, component, integration, and HIL testing — specification, cases, execution report
  - Software integration report
  - Full traceability linkages (hazard → SG → FSR → TSR/SWR → design → code → test → evidence) with rationale at every link
- Add a `render-html` generation script/tool that reads canonical corpus JSON and emits the HTML (deterministic, offline, no external dependencies at view time — Mermaid rendered client-side from CDN with graceful fallback)
- Navigation: collapsible section hierarchy, per-artifact anchor IDs, and a traceability matrix section with hyperlinked cross-references

## Capabilities

### New Capabilities
- `html-e2e-document`: Generation of the end-to-end HTML engineering document from the corpus — content requirements (which sections, attributes, linkages, rationale must appear), diagram requirements (Mermaid viewpoints, static/dynamic), and regeneration/determinism requirements.

### Modified Capabilities
- (none — no existing spec requirements change; the corpus and validation behavior are untouched)

## Impact

- **New file**: `docs/artifacts/tools/render_e2e_html.py` (or equivalent generator) — reads corpus JSON only, writes one HTML file under `docs/artifacts/reports/`
- **New output**: `docs/artifacts/reports/e2e-engineering-document.html`
- **No changes** to corpus artifacts, schemas, link registries, validation logic, or foxBMS source code
- **Dependencies**: Python 3 stdlib + existing corpus files; Mermaid.js loaded from CDN at view time (no build-time dependency)
- **Existing docs**: TRACEABILITY_DOCUMENT.md remains; HTML document is a richer superset presentation
