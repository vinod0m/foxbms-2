# Declared gap: no as_is management-level record

**This directory is intentionally empty of corpus artifact records.**
This file is a factual declaration of *why*, so that the emptiness is visible
rather than silent. It is not an artifact. It has no `id`, it is not a link
endpoint, and it is deliberately **not** a JSON record — see
"Why this is a `.md` and not a `.json` record" below.

- Profile: `as_is`
- Baseline commit investigated: `308028fb`
- Investigation date: 2026-09-29
- Guard posture for this directory: no record here is human-approved
  (`human_approval_status` would be `pending` on any record), none is
  `production_authorized` (`false`), and none carries
  `product_verification_credit` (`false`). No approval of any kind is claimed.

## What was searched for

The `as_is` profile may only record what the pinned source actually
demonstrates, marked `origin: "source_observed"`. The validator hard-fails an
`as_is` artifact claiming `origin: "synthetic"`. The following read-only
searches were run against the pinned tree:

1. `graft ask` over the indexed graph for *"project plan, risk register, risk
   management, measurement plan, process improvement records"*. Ranked retrieval
   returned only lexical noise on code symbols (`MXM_BATTERY_MANAGEMENT_COMMAND_t`
   — an AFE register typedef; `run_process` — a Python subprocess helper; and
   `docs/artifacts/tools/corpus.py` itself). No management artifact surfaced.
2. Enumeration of every `.rst` / `.md` file in the pinned `docs/` tree: **237
   files**, screened by name for
   `plan|risk|measur|improvest|metric|kpi|lessons|process`.
3. Content search across pinned `docs/` for `risk register|project plan|
   measurement plan|capability level`: **zero matching files**.
4. Path search across the whole pinned tree for `plan|risk|measur|improvest`:
   no management-document hits.

**Important negative control.** Three filenames surfaced in step 2 —
`aspice-process-map.md`, `execution-plan.md` and `supporting-processes.md`.
These are **corpus outputs under `docs/artifacts/`, not pinned source**. They
were excluded: `git cat-file -e 308028fb:<path>` fails for each, and
`git ls-tree 308028fb` does not list them. Treating them as source evidence
would have been a category error. The same control was applied to
`TRACEABILITY_DOCUMENT.md` at the repository root, which is likewise **not** in
`git ls-tree 308028fb` and is therefore corpus output rather than pinned source.

## What was found

The pinned tree does contain process- and team-related documentation, and it is
listed here in full so the boundary of the gap is auditable:

| Pinned file | Present at `308028fb` | What it actually is |
|---|---|---|
| `docs/developer-manual/software/software-development-process.rst` | yes | 49 lines describing the branch-and-review workflow: work starts from an issue, a feature branch is created, changes are reviewed, and a branch merges only under stated conditions. A **process description**, not a project plan. No schedule, no resource plan, no milestones, no progress reporting. |
| `docs/general/team.rst` | yes | A team / contact page. Not a project organisation or resource plan. |
| `docs/general/motivation.rst` | yes | Project motivation prose. Not management records. |
| `docs/general/releases.rst` + `releases.csv` | yes | A release **version history**: version, release date, documentation link per row. Not a Release Plan or Release Checklist. |
| `docs/general/safety/safety.rst` | yes | Safety disclaimer prose. Not a safety management plan record. |

## Why no record was created

ASPICE PAM 4.1 management and supporting expectations are specific, and none is
satisfied by the material above:

| Process | Expected artifacts | Pinned-source evidence | Present? |
|---|---|---|---|
| `MAN.3` Project Management | Project Plan, Schedule, Resource Plan, Progress Reports | `software-development-process.rst` (workflow only), `team.rst` (contacts only) | none |
| `MAN.5` Risk Management | Risk Register, Risk Analyses, Mitigation Plans | no risk register, no risk analysis, no mitigation plan in the pinned tree | none |
| `MAN.6` Measurement | Measurement Plan, Metrics Definitions, Measurement Results | no measurement plan, no metric definitions, no results | none |
| `PIM.3` Process Improvement | Improvement Proposals, Improvement Records, Effectiveness Evaluation | no improvement record in the pinned tree | none |

Two specific reasons not to force a record:

1. **A process description is not a plan.** `software-development-process.rst`
   is genuinely `source_observed` and genuinely useful, but a workflow
   description has no schedule, no resources, no milestones and no progress
   reporting. Recording it as `MAN.3 Project Management` would assert a project
   plan exists where only a workflow narrative does.
2. **`supporting-processes.md` is not corroboration.** The nearest-named file
   is corpus output, not source. Citing it as pinned evidence would have
   manufactured a self-referential loop: the corpus citing itself as proof
   about the product.

A corpus-wide search for `risk register|measurement plan|improvement
proposal|release plan|release notes|release checklist|project plan` across
`docs/artifacts/corpus/` returned exactly one file,
`safety/tara-communication-attack-surface.json`, and that is a TARA threat
record containing a risk **analysis table**, not a project risk **register**.
It does not satisfy `MAN.5` and was not repurposed as if it did.

## Consequence for the coverage plan

`MAN.3`, `MAN.5`, `MAN.6` and `PIM.3` currently read `mapped` in
`docs/artifacts/governance/coverage-plan.json` and were **not** corrected by
this task, which was scoped to three reported overclaims. They are recorded here
as verified remaining overclaims, with the evidence needed to correct them:

- `MAN.3` — `"mapped - synthetic project plan created"`. No project plan exists.
  The only `management`-domain record is `FB2-MAN-SCO-000001`, whose
  `artifact_type` is `requirement` and whose title is *"Project Scope"*. A
  project **scope** statement is not a project **plan**; `expected_artifacts`
  also requires a Schedule, a Resource Plan and Progress Reports, none of which
  exist in either profile.
- `MAN.5` — `"mapped - synthetic risk register created"`. No risk register exists.
- `MAN.6` — `"mapped - synthetic measurement plan created"`. No measurement plan exists.
- `PIM.3` — `"mapped - synthetic improvement records created"`. No improvement record exists.

These four are the same defect class as the three corrected entries and should
be corrected in a follow-up pass. They are reported rather than fixed here so
that this task's change set stays inside the scope it was given.

Note that the disposition counts rendered into
`docs/artifacts/views/management/management.md` will continue to count these as
`mapped` until they are corrected. The supporting-processes view already reports
`SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.6` and `PIM.3` as coverage gaps with no
process-definition record, which contradicts the `mapped` dispositions in the
plan. That contradiction is the finding.

## What would legitimately close this gap

Only real work, not a new file: a project plan, a risk register, a measurement
plan and a process-improvement record for the pinned baseline, each with
identifiers, owners, review state and approval records. None exists, so the gap
stands.

## Why this is a `.md` and not a `.json` record

`docs/artifacts/tools/corpus.py` indexes artifact records by globbing `*.json`
under `corpus/` and `reviews/`. A JSON file here would be picked up and
validated as an artifact. A declaration of emptiness is not an artifact, and
forcing it into the artifact model would require inventing an `id` and an
`artifact_type` outside `ARTIFACT_TYPE_SCHEMAS`, which the validator reports as
a high-severity *"schema … missing"* finding. A Markdown note is the honest
representation: visible, inert to the tooling, and incapable of inflating any
coverage count.
