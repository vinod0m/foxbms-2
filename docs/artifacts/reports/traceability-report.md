# Traceability Report

**Generated:** 2026-09-20  
**Baseline:** BAS-REF-001  
**Profile:** synthetic_reference (primary), as_is (comparison)

## Overview

This report documents the traceability integrity of the foxBMS 2 lifecycle artifact corpus. The traceability graph implements 17 relation types supporting vertical, reverse, lateral, and lifecycle traversal.

## Link Registry Statistics

| Profile | Total Links | Link Types Used | Orphaned Links | Dangling Links |
|---------|-------------|-----------------|----------------|----------------|
| synthetic_reference | 45 | 7/17 | 0 | 0 |
| as_is | 25 | 7/17 | 0 | 0 |

## Link Type Coverage

| Relation Type | synthetic_reference | as_is | Required |
|---------------|---------------------|-------|----------|
| refines | 4 | 3 | ✅ |
| allocated_to | 6 | 6 | ✅ |
| implements | 3 | 3 | ✅ |
| verifies | 23 | 9 | ✅ |
| validates | 2 | 0 | ✅ |
| result_of | 6 | 1 | ✅ |
| supports | 0 | 0 | ❌ |
| mitigates | 1 | 1 | ✅ |
| specified_by | 0 | 0 | ❌ |
| consumes | 0 | 0 | ❌ |
| produces | 0 | 0 | ❌ |
| depends_on | 0 | 0 | ❌ |
| constrained_by | 0 | 0 | ❌ |
| reviewed_by | 0 | 2 | ✅ |
| changes | 0 | 0 | ⚠️ |
| supersedes | 0 | 0 | ❌ |

## Vertical Traceability Chains

### Chain 1: Cell Voltage Protection (Complete)

```
Operational scenario → Hazardous event → Safety goal
  → Functional safety requirement (FSR-001..004)
    → Technical safety requirement (HW TSR-001..003, SW SWR-001..003)
      → System architecture/allocation (HSI-001)
        → HW requirement (TSR-001..003) & SW requirement (SWR-001..003)
          → HW/SW architecture (HSI-001, SW-DSN-001..003)
            → Detailed design (HW-TSR-001..003, SW-DSN-001..003)
              → Implementation (AFE driver, SOA, Contactor, etc.)
                → Verification (TMS-001, TMS-002)
                  → Execution (EXE-001)
                    → Review (REV-001)
                      → Safety argument
```

### Chain 2: Temperature Protection (Partial - Parameters Only)

```
Hazard → Safety Goal → FSR (params) → TSR (params) → SWR (params)
```

### Chain 3: Current Protection (Partial - Parameters Only)

### Chain 4: Precharge/Contactor Control (Complete)

```
Hazard (weld) → SG → FSR-003 → TSR-003 → SWR-003 → DSN-003 → TMS-002 → EXE-002 → REV-001
```

### Chain 5: Communication/Watchdog Fault Response (Partial)

## Lateral Traceability

### HW/SW Interface Consistency (HSI Authority)

| HSI Signal | HW Spec | SW Spec | Status |
|------------|---------|---------|--------|
| SPI_CLK | 1 MHz max | 1 MHz configured | ✅ |
| SPI_MOSI/MISO | MSB first | MSB first | ✅ |
| PEC | CRC-15 | CRC-15 validated | ✅ |
| cell_voltage[mV] | 0-5000 mV | uint16_t[] mV | ✅ |
| Freshness | < 30 ms | < 25 ms publish | ✅ |

### Parameter Consistency

| Parameter | Safety Goal | FSR | TSR/SWR | Design | Test | Status |
|-----------|-------------|-----|---------|--------|------|--------|
| cell_voltage_max | 4200 mV | 4200 mV | 4200 mV | 4200 mV | 4200 mV | ✅ |
| ftti_ms | 100 ms | 100 ms budget | 100 ms | 100 ms | 100 ms | ✅ |
| contactor_mechanical_time_ms | 30 ms | 30 ms | 30 ms | 30 ms | 30 ms | ✅ |
| soa_debounce_count | 2 | 2 | 2 | 2 | 2 | ✅ |

## Change Impact Traceability

### Change SCN-CHG-001 (Voltage Threshold 4.2V→4.15V)

| Affected Artifact | Old Value | New Value | Link Impact |
|-------------------|-----------|-----------|-------------|
| FB2-PRM-000001 | 4200 mV | 4150 mV | - |
| FB2-SAF-FSR-000002 | 4200 mV | 4150 mV | Allocation valid |
| FB2-SW-DSN-000002 | 4200 mV | 4150 mV | Implements valid |
| FB2-HW-TSR-000001 | 4200 mV | 4150 mV | Allocation valid |
| FB2-VER-TMS-000001 | 4300/4200 | 4250/4150 | Test valid |
| FB2-LNK-SAF-000014 | verifies | verifies | Suspect → re-verify |

### Change SCN-CHG-002 (LTC6811 → ADI ADES1830)

| Affected Artifact | Change Type | Link Impact |
|-------------------|-------------|-------------|
| FB2-SYS-HSI-000001 | New interface spec | All HSI links suspect |
| FB2-HW-TSR-000001 | New accuracy | Allocation suspect |
| FB2-HW-TSR-000002 | SPI vs isoSPI | Link type may change |
| FB2-SW-SWR-000001 | New driver reqs | Allocation suspect |
| FB2-SW-DSN-000001 | New architecture | Implements suspect |
| FB2-VER-TMS-000001 | New test | Verifies suspect |

## Traceability Integrity Checks

| Check | synthetic_reference | as_is | Status |
|-------|---------------------|-------|--------|
| No duplicate IDs | ✅ | ✅ | Pass |
| No dangling links | ✅ | ✅ | Pass |
| All link types valid | ✅ | ✅ | Pass |
| All endpoints exist | ✅ | ✅ | Pass |
| Baseline consistency | ✅ | ✅ | Pass |
| Profile isolation | ✅ | ✅ | Pass |
| Variant applicability | ✅ | ✅ | Pass |
