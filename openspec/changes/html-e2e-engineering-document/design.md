## Context

The corpus under `docs/artifacts/` holds 65+ artifacts as canonical JSON (requirements, designs, analyses, tests, executions, reviews, scenarios), two per-profile link registries (48 typed links with rationale/provenance/review_state/change_suspect_status), a 42-anchor source registry, and shared parameter/assumption registries. `corpus.py` already provides load/link/index helpers (`load_artifact_index`, `load_links`) and an acceptance suite. A markdown TRACEABILITY_DOCUMENT.md exists but is flat text; the requested deliverable is a rich, navigable HTML engineering document with diagrams. foxBMS source, config, and tests must remain untouched.

## Goals / Non-Goals

**Goals:**
- One self-contained HTML file presenting every engineering level with full attributes, linkages, rationale
- Mermaid diagrams (system context, functional block, dynamic; software static/dynamic; per-component design static/dynamic) generated from corpus data, not hand-drawn
- Every link-registry entry rendered with metadata; every artifact ID anchor-navigable
- Deterministic, offline-capable generation wired into the acceptance tooling

**Non-Goals:**
- No changes to corpus artifacts, schemas, links, or validation rules
- No server, build pipeline, or JS framework; no modification of foxBMS source/config/tests
- No interactive graph editing; read-only presentation
- Mermaid rendering itself is not a build step — diagrams render client-side

## Decisions

**1. Generator: standalone Python script `docs/artifacts/tools/render_e2e_html.py`**
Reuses `corpus.py` by import (same directory) for artifact/link loading, guaranteeing the HTML always agrees with the validator's view. Alternative: extend `corpus.py` with a `render` subcommand — rejected for now to keep the acceptance tool stable and auditable while the generator iterates; a thin `corpus.py render-html` wrapper may call the script later.

**2. Single-file HTML, template rendered via `string.Template` / f-strings, no Jinja**
Stdlib-only keeps the offline determinism guarantee and zero new dependencies. Alternative: Jinja2 — rejected (new dependency, heavier than needed for straight-line section rendering).

**3. Mermaid embedded as fenced code in HTML; CDN loader with `<noscript>`/fallback text**
Each diagram is emitted as a `<pre class="mermaid">` block with a textual caption fallback. Loader script from CDN initializes `mermaid.run()`; if the CDN is unreachable, the raw diagram source remains readable as text. Alternative: server-side mermaid-cli rendering to inline SVG — rejected: adds Node build dependency and breaks "python3 only" regeneration.

**4. Diagrams are data-derived**
- System context: from `scope-and-applicability.json` boundaries/external systems
- Functional block + system dynamic: from SGO/FSR statements + link registries (chain HAZ→SG→FSR→TSR/SWR→DSN→TMS)
- Software static: `implements`/`allocated_to` links between SWR/DSN/components
- State machines: directly from each design artifact's `behavior_model.states`/`transitions`
- Per-component design diagrams: from `decomposition` and `interfaces` fields
This makes regeneration faithful to corpus changes with no manual diagram maintenance.

**5. Section layout mirrors the engineering order requested**
Stakeholder → System reqs → System architecture → SW reqs → SW architecture → Detailed design → Implementation mapping → SW integration report → System verification → SW verification (unit/component/integration/HIL) → Traceability matrix appendix. HIL/levels derived from `execution_kind` and test type; actual runs vs synthetic fixtures labeled explicitly per governance policy.

**6. Anchors + cross-reference convention**
Every artifact gets `id="art-<ARTIFACT_ID>"`; every link reference renders as `<a href="#art-...">` with hover title carrying rationale. Traceability matrix table lists link ID, endpoints, relation, rationale, provenance, review_state, change_suspect_status.

**7. Integrity check as part of acceptance**
A new `verify_html` function (callable from `corpus.py check` or standalone flag) asserts: all required section headings present; every requirement artifact ID of both profiles appears ≥ once; every link ID appears in the matrix. Failure names missing IDs (spec scenario).

**8. Determinism**
Sorted iteration over all collections, `json.dumps(..., sort_keys=True)` for any embedded data, fixed HTML template. Only a `data-generated-at` attribute may differ between runs; excluded from the byte-compare in the check.

## Risks / Trade-offs

- [CDN unavailable offline → diagrams show raw Mermaid text] → captions carry one-line summaries; all textual content independent of Mermaid
- [Corpus grows (23+ scenarios, more profiles) → file size] → collapsible `<details>` sections keep navigation cheap; single file still < a few MB at current scale
- [Design artifacts with sparse behavior models → thin diagrams] → renderer skips absent fields gracefully and states "model not specified in corpus"
- [Import coupling to corpus.py internals] → import only stable helpers (`load_artifact_index`, `load_links`, `Findings`); if those change, generator fails fast at import time

## Migration Plan

Additive only: new script + new generated file + optional acceptance hook. Rollback = delete script and HTML; corpus unaffected. If acceptance hook is added behind a flag, default behavior of `corpus.py check` stays unchanged unless the hook is wired in.

## Open Questions

None material — section set, diagram viewpoints, and integrity rules are fully specified by the user request and the delta spec.
