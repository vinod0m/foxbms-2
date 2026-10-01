# Reproducibility Report

**Generated:** 2026-10-01 (re-measured after the `CORR-COV-016` coverage-plan change)
**Baseline:** BAS-REF-001 — source pinned to commit `308028fb`, corpus authored at `2a408d5`
**Profiles:** `synthetic_reference` (primary), `as_is` (comparison)

> Reproducibility and determinism results only. Nothing here asserts ISO 26262
> conformity, ASIL capability, ASPICE capability level, certification, human
> approval or tool qualification. All 263 indexed records are
> `human_approval_status: pending` and `production_authorized: false`.
>
> Every claim in this report was measured by running the tool twice and diffing.
> The previous version was measured on 2026-09-29 and carried several stale
> figures; §1 records which.

## 1. Summary

| Property | Mechanism | Measured result |
|---|---|---|
| View rendering | `corpus.py render` | **byte-identical across two runs** once the `Generated:` timestamp line is excluded (**11 files**, re-verified 2026-10-01) |
| Graph export | `corpus.py export` | **byte-identical** across two runs apart from the `generated_at` field (4 files) |
| Export content hashes | SHA-256 in `exports/manifest.json` | **all 3 hashes identical** across two runs |
| Spec documents | `render_spec_documents.py --check` | `INTEGRITY CHECK PASSED`; `DETERMINISM: byte-identical across runs`; 10/10 documents converted |
| Source registry pinning | baseline commit check | pinned to `308028fb13d046ba29b98886895c2e17937b1437` |
| Acceptance suite | `corpus.py check` | `Acceptance suite: PASSED`, 10 gate lines PASS, 0 FAIL |
| Toolchain self-tests | `corpus.py selftest` | **48 PASS, 0 FAIL** (was 11, then 22, in earlier versions of this report) |
| Scenario suite | `corpus.py scenario-test` | 20/20 mutations on their own declared detector, 3/3 change lifecycles |
| HTML deliverable | `render_e2e_html.py --check` | **exits 1** — 14 `implementation` records have no owning section in the renderer. Tool-side; see §7. |
| Coverage-plan placeholders | none | `created_at`, `updated_at` and `repository_commit` carried literal `{{BUILD_TIMESTAMP}}` / `{{REPOSITORY_COMMIT}}` macros until 2026-10-01. Replaced; the pinned commit and the authoring commit are recorded in **separate fields**. |

## 2. How Determinism Was Measured

The measurement is the point of this section, because "deterministic" is a claim
that is easy to assert and easy to get wrong.

```
$ python3 docs/artifacts/tools/corpus.py render      # run 1
$ python3 docs/artifacts/tools/corpus.py export      # run 1
$ cp -R docs/artifacts/views    /tmp/v1 ; cp -R docs/artifacts/exports /tmp/e1

$ python3 docs/artifacts/tools/corpus.py render      # run 2
$ python3 docs/artifacts/tools/corpus.py export      # run 2
$ cp -R docs/artifacts/views    /tmp/v2 ; cp -R docs/artifacts/exports /tmp/e2

$ diff -r -I '^Generated:'      /tmp/v1 /tmp/v2     # views
$ diff -r                       /tmp/e1 /tmp/e2     # exports
```

### Views: 11 files, byte-identical

The only difference between the two runs is the timestamp in the preamble:

```
run 1: Generated: 2026-10-01T04:44:12Z | Baseline: BAS-REF-001 | 263 artifacts, 489 links
run 2: Generated: 2026-10-01T04:44:43Z | Baseline: BAS-REF-001 | 263 artifacts, 489 links
```

`diff -r -I '^Generated:'` reports **no differences across all 11 view files**.
The exclusion is narrowly scoped to that one line and nothing else; no other
line of any view is excluded from the comparison.

> The previous version of this report said "10 files" and quoted
> `153 artifacts, 283 links`. Both were stale: the renderer emits 11 views, and
> the corpus index held 263 records and 489 links on the day this was re-measured.

### Exports: 4 files, byte-identical apart from `generated_at`

```
$ diff -r /tmp/e1 /tmp/e2
9c9
<  "generated_at": "2026-10-01T04:44:12Z",
---
>  "generated_at": "2026-10-01T04:44:43Z",
```

That single line in `manifest.json` is the only difference. `nodes.jsonl`,
`edges.jsonl` and `trace-matrix.csv` are byte-identical with no exclusions at
all.

### Export content hashes

`exports/manifest.json` carries a `content_hashes` map over 3 files. Across the
two runs the key sets are identical and **all 3 hashes match**. This is the same
property the acceptance gate `[6/8] deterministic export hashes` asserts, and it
is what makes the export usable as a change-detection baseline.

Current export shape, read from the manifest: `node_count: 263`,
`edge_count: 489`, `repository_commit: 308028fb`.

## 3. What Is Deterministic and Why

| Element | Mechanism |
|---|---|
| Record ordering | The renderer sorts every record collection by ID, and the index is keyed on `(profile, id)` |
| Identifier scheme | Fixed pattern `FB2-<DOMAIN>-<TYPE>-<NNNNNN>`, never generated from a counter or a clock |
| Table rendering | Fixed column sets per view; cells escaped through one helper (`_cell`) |
| Coverage-plan quoting | Read live from `governance/coverage-plan.json` at render time, so a corrected plan changes the view and an unchanged plan cannot |
| Guard fields | Computed from the indexed records at render time, never asserted in prose |
| Graph export | Nodes and edges emitted from the link registry in stable order; `trace-matrix.csv` sorted |
| Source registry | Pinned to baseline commit `308028fb`; drift is a validation finding, not a silent re-read |

### The anti-drift property

The renderer was changed on 2026-09-29 so that generated prose can no longer
quote a frozen copy of the coverage plan. Previously two generated views embedded
literal strings describing what the coverage plan *used to claim*; when the plan
was corrected, those views kept asserting the superseded claim.

The property has now been verified twice, and the second verification is the
stronger one because it was a real governance change rather than a temporary
flip:

1. **2026-09-29, temporary flip.** Set `SYS.2`'s disposition to `mapped` in the
   coverage plan; re-render; `views/system/system.md` immediately read
   ``SYS.2` (System Requirements Analysis) is recorded `mapped``; restore the
   corrected plan and re-render, and the view read ``is recorded `gap``` again.
2. **2026-10-01, real change.** `CORR-COV-016` demoted 23 of the 28 applicable
   ASPICE processes and 8 of the 10 applicable ISO parts. After `render` with no
   view file edited by hand,
   `views/standards-mapping/standards-mapping.md` moved from
   `12 mapped / 10 partially_mapped / 6 gap` to
   **`4 mapped / 21 partially_mapped / 3 gap`**, and
   `views/traceability/traceability-document.md` picked up `standards_mapping
   33/38` and the new ISO tally. Both views now agree with
   `governance/coverage-plan.json` because they read it at render time.

The generated text now tracks the governance file in both directions, so a
future correction cannot leave a stale claim behind.

## 4. Source Registry Pinning, and the second commit

The source registry is pinned to baseline commit
**`308028fb13d046ba29b98886895c2e17937b1437`** (foxBMS 2 v1.11.0, 2026-04-20).
A dedicated self-test asserts the pinning and passes.

This is what makes `as_is` records auditable: a record marked `source_observed`
points at a specific blob at a specific commit, so a later drift in the working
tree is a detectable event rather than a silent change of meaning.

**Two commits, deliberately not conflated.** Until 2026-10-01
`governance/coverage-plan.json` carried the literal string
`"repository_commit": "{{REPOSITORY_COMMIT}}"` — an unsubstituted template macro
in a canonical governance record, never rendered, so any reader received that
string as data. It is now:

| Field | Value | Meaning |
|---|---|---|
| `repository_commit` | `308028fb13d046ba29b98886895c2e17937b1437` | the commit the **source** is pinned to; identical to `sources/source-registry.json.repository_commit` and `exports/manifest.json.repository_commit` |
| `repository_commit_meaning` | prose | what the field has always meant, and the caveat |
| `corpus_authored_at_commit` | `2a408d573b41c2f3ab75edccb31f28768adcf9f2` | the commit the **corpus content** was authored on top of (`git log -1`, 2026-10-01) |
| `corpus_authored_at_commit_meaning` | prose | that every number in every report was measured against this tree |

They are different values and neither is put in the other's field. The corpus
content does not exist at `308028fb` — `git ls-tree -r 308028fb` has no
`docs/artifacts` entry — and the pinned source at `308028fb` was not re-audited
on every pass. `git merge-base --is-ancestor 308028fb HEAD` returns true, so the
pin is a genuine ancestor of the authoring head.

`created_at` is derived from the commit that first added the file
(`8aaa774`, 2026-09-08T12:12:59+02:00, normalised to UTC) and `updated_at` from
`date -u` at the moment of the edit. Both derivations are recorded in the file's
own `placeholders_replaced` block.

## 5. What Is Deliberately *Not* Deterministic

Two timestamps are excluded from the determinism comparison, and only these two:

| Field | File | Why |
|---|---|---|
| `Generated:` | preamble of each of the **11** views | A report that never says when it was made is less useful, not more |
| `generated_at` | `exports/manifest.json` | Same reason |

Everything else in both trees is byte-identical. No content, no ordering, no
guard field, no count and no prose varies between runs.

## 6. Verification Toolchain Self-Tests

`corpus.py selftest` → **48 PASS, 0 FAIL**:

| # | Test | What it proves |
|---|---|---|
| 1 | dangling link detected | the link validator catches an unresolvable target |
| 2 | invalid link type detected | the validator rejects a relation type outside the allowed set |
| 3 | invalid evidence state detected | `execution_kind` / `outcome` enums are enforced |
| 4 | FTTI budget violation detected | timing-budget arithmetic is checked, not assumed |
| 5 | profile contamination detected | a record cannot import a fact across profiles |
| 6 | `production_authorized=true` rejected | the guard cannot be set to true |
| 7 | invalid schema rejected | a malformed schema is refused by the validator itself |
| 8 | duplicate ID detection | the duplicate detector fires |
| 9 | invalid state change rejected | illegal lifecycle transitions are caught |
| 10 | export round-trip deterministic | export → re-read → re-export is stable |
| 11 | source registry pinned to baseline commit | the baseline pin is asserted, not assumed |
| 12–48 | 37 further tests | the growth from 11 to 48 is deliberate; see the grouping below |

The 37 added since the 11-test version of this report are grouped by what they
protect, because "48 PASS" without that is not evidence of anything:

| Group | n | Protects |
|---|---:|---|
| Provenance verification | 9 | a wrong digest is caught and a right one is not; a placeholder digest is permitted only with a note; an anchor whose symbol is absent from its file is caught; an out-of-bounds line range is caught; placeholder `content_hash` is reported not skipped; a missing evidence file is caught |
| Chain traversal | 4 | the §13 chain reaches the stages the corpus actually links; fails when the link graph is emptied; does not follow the weak `related_to` relation |
| Change lifecycle | 2 | nine null fields are rejected; an unresolved referenced id is rejected |
| `standards_mapping` | 2 | measured by backing, not by counting inventory keys; drops when a backing artefact is renamed |
| Coverage / scenario wiring | 3 | `negative_scenario_validation` measures passes not files; the coverage dimension and the acceptance gate share one scenario measurement; FTTI is resolved from a bound parameter |
| Governance gate | 2 | the gate runs a detector and goes red on an injected violation; the gate was empty by construction before the repair |
| Wiring | 1 | provenance checks run inside `_run_detectors`, so every finding-counting path sees them |

The last group is the most important: it is a test that the *provenance* checks
are on every path that counts findings. Without it, a green gate could coexist
with an unverified digest.

## 7. Acceptance Suite Reproducibility

`corpus.py check` is itself reproducible and internally cross-checking. It runs
`validate`, `inventory`, `coverage`, a trace reachability check, the scenario
suite, and the export twice — comparing the two export manifests' content hashes
— before the governance-semantics and final-status gates.

| Gate | Result |
|---|---|
| `[1/8] validate` | PASS (286 artefacts validated, 4 findings, 0 errors) |
| `[2/8] inventory` | PASS (612/612 source files) |
| `[3/8] negative_scenario_validation = 20/20 mutations` | PASS (measured: 20 scenarios executed, 20 passing) |
| `[3/8] change lifecycles = 3/3` | PASS (19/19 content checks per record) |
| `[4/8] hazard present` | PASS (both profiles) |
| `[5/8] scenario-test` | PASS (23/23 lines; 20/20 mutations detected on their own declared detector) |
| `[6/8] export` | PASS (263 nodes, 489 edges) |
| `[6/8] deterministic export hashes` | PASS |
| `[7/8] no production_authorized/approved artifacts` | PASS (0 violations this run; 263 records scanned) |
| `[7b/8] provenance verification` | PASS (229 digests, 101 anchors, 46 log hashes, 34 evidence-file entries; 4 findings, none an error) |
| `[8/8] final status recorded` | PASS (`synthetic_ready_with_limitations`) |

**`Acceptance suite: PASSED`** — re-run on 2026-10-01 after the coverage-plan
change, so the demotion is confirmed not to have broken any gate.

Note that gate `[7/8]` re-runs the validators with a **fresh** findings set
rather than reusing an earlier one, so a governance violation cannot be masked
by a stale findings list from a previous stage.

### The HTML deliverable's integrity check currently fails

`render_e2e_html.py --check` exits **1**, with one failure class repeated 14
times:

```
UNMAPPED artifact type: as_is/FB2-SW-IMP-00000N (artifact_type 'implementation' has no owning section)
UNMAPPED artifact type: synthetic_reference/FB2-SW-IMP-00000N (artifact_type 'implementation' has no owning section)
```

Every `artifact_type: implementation` record in the corpus — 10 in `as_is`,
4 in `synthetic_reference` — has no owning section in the renderer. This is a
**renderer gap, not a corpus gap**: the records validate, are linked and are
exported. The previously committed HTML was additionally stale (missing 16 owned
records, 24 link rows and 6 gap rows); regenerating it cleared every one of
those and left only the 14 above.

`--audit-guard` on the regenerated file **passes**: no affirmative conformity
claim, and every "human approved" occurrence sits inside a negation. The fix is
an owning section for `implementation` in `render_e2e_html.py`, which is outside
this workstream's write boundary.

## 8. Reproducibility Limitations

1. **One Python interpreter and one host.** Determinism is verified on a single
   machine with a single `python3`. Cross-platform and cross-version
   reproducibility of the tool itself is not demonstrated.
2. **The verification environment is not fully reproducible from the
   distribution.** The SIL host run documented in
   `verification-evidence-report.md` depends on the host's Ruby, the shipped
   CeeDling configuration and a SIL harness. The harness's *instructions* are
   **tracked** (`evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/RUNBOOK.md`),
   but the harness working tree itself lives under the **gitignored**
   `docs/artifacts/.work/verification-env/`. Five execution records additionally
   carry an `output_hashes` digest that resolves only to a file in that
   gitignored tree rather than to the evidence file they name. A fresh clone can
   reproduce the run from the tracked runbook; it cannot verify those five
   digests.
3. **Mermaid diagram validation depends on the host.** The renderer checks
   Mermaid blocks with `mermaid-cli` when it is available and states plainly in
   each view whether that check ran. On a host without `mermaid-cli` the
   diagrams are emitted unvalidated, and the view says so rather than claiming
   validation.
4. **`render` is slow** — dominated by Mermaid validation. This does not affect
   determinism, only turnaround.
5. **A redundant link registry copy** exists under `corpus/`
   (`links-cell-voltage.json`, 51 links, a strict subset of the canonical 195);
   it is de-duplicated by the tool, so it does not affect any output, but a
   future change to the de-duplication rule would change the export. Reported,
   not deleted. Its sibling `links-concept-lifecycle.json` (177 links) is the
   **only** copy of those links and is load-bearing, not redundant.
6. **Determinism is not correctness.** Link revision currency is not implemented,
   so 326 of 489 links record an endpoint revision that differs from the
   endpoint artefact's current revision, and all 489 are marked
   `change_suspect_status: false`. The export reproduces that exactly, staleness
   included.
