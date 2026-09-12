# foxBMS 2 — Software Integration Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Integration Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-12T01:01:53Z |

## Scope

Integrated software components, available integration evidence, and explicit integration gaps. Per governance policy, evidence is blocked, not fabricated.

## Profile: `as_is`

### Integrated Components

| Design | Implements SWR | Link rationale |
|---|---|---|
| `FB2-SW-DSN-000001` | `FB2-SW-SWR-000001` | Design implements software requirement |
| `FB2-SW-DSN-000002` | `FB2-SW-SWR-000002` | Design implements software requirement |
| `FB2-SW-DSN-000003` | `FB2-SW-SWR-000003` | Design implements software requirement |

### Integration Evidence

- `FB2-VER-EXE-000001`: kind=`actual_host_run`, outcome=`pass`

### Integration Gaps

| Gap | Disposition |
|---|---|
| No component-level test measures | Gap documented; synthetic_reference to add per review disposition FB2-FND-000005 |
| No integration-level executions (only unit `actual_host_run` exists) | Per governance policy: actual product evidence = 0 — blocked, not fabricated |
| No target-hardware integration runs | as_is gap documented in review `FB2-REV-000001` (finding FB2-FND-000002) |

## Profile: `synthetic_reference`

### Integrated Components

| Design | Implements SWR | Link rationale |
|---|---|---|
| `FB2-SW-DSN-000001` | `FB2-SW-SWR-000001` | Design implements software requirement |
| `FB2-SW-DSN-000002` | `FB2-SW-SWR-000002` | Design implements software requirement |
| `FB2-SW-DSN-000003` | `FB2-SW-SWR-000003` | Design implements software requirement |

### Integration Evidence

No execution artifacts in this profile. Integration-level executions: **none in corpus**.

### Integration Gaps

| Gap | Disposition |
|---|---|
| No component-level test measures | Gap documented; synthetic_reference to add per review disposition FB2-FND-000005 |
| No integration-level executions (only unit `actual_host_run` exists) | Per governance policy: actual product evidence = 0 — blocked, not fabricated |
| No target-hardware integration runs | as_is gap documented in review `FB2-REV-000001` (finding FB2-FND-000002) |


---

*Generated: 2026-09-12T01:01:53Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
