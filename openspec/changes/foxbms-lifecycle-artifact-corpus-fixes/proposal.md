# Proposal: Fix foxBMS 2 Lifecycle Artifact Corpus — Source Registry, Mutations, Links, Evaluator Manifests

## Problem Statement

The previous `foxbms-lifecycle-artifact-corpus` change delivered a corpus that passed acceptance gates but has **critical fabrication and completeness gaps**:

1. **Source Registry Fabrication** — 30/42 registry symbols are fabricated (don't match actual code functions)
2. **Missing Mutations** — Only 2/20 minimum mutations implemented (18 missing)
3. **Missing Evaluator Manifests** — 0/5 required evaluator-only oracle manifests
4. **Dangling Links** — 2 links reference review artifact not in corpus/
4. **Unused Registry Anchors** — 22/42 anchors never referenced

## Scope

Fix all identified gaps in the existing corpus under `docs/artifacts/`:
- Regenerate `docs/artifacts/sources/source-registry.json` from actual AST (graphify)
- Implement 18 missing mutation scenarios + 5 evaluator manifests
- Fix dangling links (move review into corpus or update links)
- Create 5 missing evaluator manifests for existing scenarios
- Update all affected artifacts and re-validate

## Success Criteria

- Source registry: 100% anchors match actual code symbols (graphify-verified)
- Mutations: 20/20 implemented with evaluator manifests
- All 5 evaluator manifests created and validated
- All links resolve to corpus artifacts
- All acceptance gates pass (`python3 docs/artifacts/tools/corpus.py check` → PASSED)
- Corpus status: `synthetic_ready_with_limitations` (or better)

## Baseline

- Commit: 308028fb (v1.11.0)
- Branch: `foxbms-2-synthetic-data` (already exists, pushed)
- Corpus location: `docs/artifacts/`
- Tooling: `docs/artifacts/tools/corpus.py`

## Constraints

- Preserve existing foxBMS implementation, hardware files, configuration, tests
- Keep observed vs synthetic vs proposed vs actual execution explicitly distinguishable
- All task-created files under `docs/artifacts/`
- Do not modify foxBMS source code
