# Reproducibility Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Profiles:** `synthetic_reference` (primary), `as_is` (comparison)

> Reproducibility and determinism results only. Nothing here asserts ISO 26262
> conformity, ASIL capability, ASPICE capability level, certification, human
> approval or tool qualification. All 153 indexed records are
> `human_approval_status: pending` and `production_authorized: false`.
>
> Every claim in this report was measured on 2026-09-29 by running the tool
> twice and diffing.

## 1. Summary

| Property | Mechanism | Measured result |
|---|---|---|
| View rendering | `corpus.py render` | **byte-identical across two runs** once the `Generated:` timestamp line is excluded (10 files) |
| Graph export | `corpus.py export` | **byte-identical** across two runs apart from the `generated_at` field (4 files) |
| Export content hashes | SHA-256 in `exports/manifest.json` | **all 3 hashes identical** across two runs |
| Spec documents | `render_spec_documents.py` | `INTEGRITY CHECK PASSED`; `DETERMINISM: byte-identical across runs`; 10/10 documents converted |
| Source registry pinning | baseline commit check | pinned to `308028fb` |
| Acceptance suite | `corpus.py check` | `Acceptance suite: PASSED`, 10 gate lines PASS, 0 FAIL |
| Toolchain self-tests | `corpus.py selftest` | 11 PASS, 0 FAIL |
| Scenario suite | `corpus.py scenario-test` | 20/20 mutations on their own declared detector, 3/3 change lifecycles |

## 2. How Determinism Was Measured

The measurement is the point of this section, because "deterministic" is a claim
that is easy to assert and easy to get wrong.

```
$ python3 docs/artifacts/tools/corpus.py render      # run 1
$ python3 docs/artifacts/tools/corpus.py export      # run 1
$ cp -R docs/artifacts/views    /tmp/r1 ; cp -R docs/artifacts/exports /tmp/e1

$ python3 docs/artifacts/tools/corpus.py render      # run 2
$ python3 docs/artifacts/tools/corpus.py export      # run 2
$ cp -R docs/artifacts/views    /tmp/r2 ; cp -R docs/artifacts/exports /tmp/e2

$ diff -r -I '^Generated:'      /tmp/r1 /tmp/r2     # views
$ diff -r -I '"generated_at"'   /tmp/e1 /tmp/e2     # exports
```

### Views: 10 files, byte-identical

The only difference between the two runs is the timestamp in the preamble:

```
run 1: Generated: 2026-09-29T09:53:47Z | Baseline: BAS-REF-001 | 153 artifacts, 283 links
run 2: Generated: 2026-09-29T09:55:06Z | Baseline: BAS-REF-001 | 153 artifacts, 283 links
```

`diff -r -I '^Generated:'` reports **no differences across all 10 view files**.
The exclusion is narrowly scoped to that one line and nothing else; no other
line of any view is excluded from the comparison.

### Exports: 4 files, byte-identical apart from `generated_at`

```
$ diff -r /tmp/e1 /tmp/e2
9c9
<   "generated_at": "2026-09-29T09:54:57Z",
---
>   "generated_at": "2026-09-29T09:55:27Z",
```

That single line in `manifest.json` is the only difference. `nodes.jsonl`,
`edges.jsonl` and `trace-matrix.csv` are byte-identical with no exclusions at
all.

### Export content hashes

`exports/manifest.json` carries a `content_hashes` map. Across the two runs the
key sets are identical and **all 3 hashes match**. This is the same property the
acceptance gate `[6/8] deterministic export hashes` asserts, and it is what makes
the export usable as a change-detection baseline.

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

The property was verified empirically, not just by inspection:

1. Set `SYS.2`'s disposition to `mapped` in the coverage plan.
2. Re-render.
3. `views/system/system.md` immediately read
   ``SYS.2` (System Requirements Analysis) is recorded `mapped``.
4. Restore the corrected plan (`gap`) and re-render.
5. The view reads ``is recorded `gap``` again.

The generated text now tracks the governance file in both directions, so a
future correction cannot leave a stale claim behind.

## 4. Source Registry Pinning

The source registry is pinned to baseline commit **`308028fb`**. A dedicated
self-test asserts the pinning and passes.

This is what makes `as_is` records auditable: a record marked `source_observed`
points at a specific blob at a specific commit, so a later drift in the working
tree is a detectable event rather than a silent change of meaning.

## 5. What Is Deliberately *Not* Deterministic

Two timestamps are excluded from the determinism comparison, and only these two:

| Field | File | Why |
|---|---|---|
| `Generated:` | preamble of each of the 10 views | A report that never says when it was made is less useful, not more |
| `generated_at` | `exports/manifest.json` | Same reason |

Everything else in both trees is byte-identical. No content, no ordering, no
guard field, no count and no prose varies between runs.

## 6. Verification Toolchain Self-Tests

`corpus.py selftest` → **11 PASS, 0 FAIL**:

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

## 7. Acceptance Suite Reproducibility

`corpus.py check` is itself reproducible and internally cross-checking. It runs
`validate`, `inventory`, `coverage`, a trace reachability check, the scenario
suite, and the export twice — comparing the two export manifests' content hashes
— before the governance-semantics and final-status gates.

| Gate | Result |
|---|---|
| `[1/8] validate` | PASS |
| `[2/8] inventory` | PASS |
| `[3/8] negative_scenario_validation = 20/20 mutations` | PASS (20/20 scenarios present; detection is `[5/8]`) |
| `[3/8] change lifecycles = 3/3` | PASS |
| `[4/8] hazard present` | PASS |
| `[5/8] scenario-test` | PASS (23/23 lines; 20/20 mutations detected on their own declared detector) |
| `[6/8] export` | PASS |
| `[6/8] deterministic export hashes` | PASS |
| `[7/8] no production_authorized/approved artifacts` | PASS (0 violations this run) |
| `[8/8] final status recorded` | PASS (`synthetic_ready_with_limitations`) |

**`Acceptance suite: PASSED`**

Note that gate `[7/8]` re-runs the validators with a **fresh** findings set
rather than reusing an earlier one, so a governance violation cannot be masked
by a stale findings list from a previous stage.

## 8. Reproducibility Limitations

1. **One Python interpreter and one host.** Determinism is verified on a single
   machine with a single `python3`. Cross-platform and cross-version
   reproducibility of the tool itself is not demonstrated.
2. **The verification environment is not fully reproducible.** The macOS host
   test run in `verification-evidence-report.md` depends on the host's Ruby,
   the shipped Ceedling configuration, and the local HALCoGen stub set under
   `.work/verification-env/`. The 177 blocked tests remain blocked on any host.
3. **Mermaid diagram validation depends on the host.** The renderer checks
   Mermaid blocks with `mermaid-cli` when it is available and states plainly in
   each view whether that check ran. On a host without `mermaid-cli` the
   diagrams are emitted unvalidated, and the view says so rather than claiming
   validation.
4. **`render` is slow** — roughly 60 s on this host, dominated by Mermaid
   validation. This does not affect determinism, only turnaround.
5. **A redundant link registry copy** exists under `corpus/`; it is
   de-duplicated by the tool, so it does not affect any output, but a future
   change to the de-duplication rule would change the export. Reported, not
   deleted.
