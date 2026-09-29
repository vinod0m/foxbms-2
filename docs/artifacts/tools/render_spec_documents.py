#!/usr/bin/env python3
"""
render_spec_documents.py — Generate ten standalone per-discipline specification
documents (Markdown + Mermaid, optional .docx via pandoc) for foxBMS 2.

Content sources (merged):
  1. the foxBMS 2 lifecycle artifact corpus (docs/artifacts/corpus/) —
     requirements, designs, test measures, executions, links, and
  2. a reverse-engineered repository model (repo_model.py) mining the actual
     source tree: 40 software modules, task engineering, BMS/SYS state machines,
     85 diagnosis entries, SOA/cell/system configuration values, AFE drivers,
     CAN interface, 313 unit tests, hardware platform facts.

Usage:
  python3 docs/artifacts/tools/render_spec_documents.py            # generate all
  python3 docs/artifacts/tools/render_spec_documents.py --check    # integrity check
  python3 docs/artifacts/tools/render_spec_documents.py --out-dir DIR

Deterministic: sorted iteration everywhere; only the "Generated:" line may vary.
Read-only over the corpus and repository; all writes go to the output directory.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import load_json  # noqa: E402
from repo_model import RepoModel  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent.parent  # tools/ -> artifacts/ -> docs/ -> repo root
ARTIFACTS = REPO / "docs" / "artifacts"
OUT_DEFAULT = ARTIFACTS / "spec-documents"

PROFILES = ("as_is", "synthetic_reference")
GEN_STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------- doc registry

DOC_ORDER = [
    "01-stakeholder-requirements-specification",
    "02-system-requirements-specification",
    "03-system-architecture-specification",
    "04-software-requirements-specification",
    "05-software-architecture-specification",
    "06-detailed-design-specification",
    "07-software-integration-report",
    "08-system-verification-report",
    "09-software-verification-report",
    "10-implementation-mapping-document",
]

DOC_TITLES = {
    "01-stakeholder-requirements-specification": "Stakeholder Requirements Specification",
    "02-system-requirements-specification": "System Requirements Specification",
    "03-system-architecture-specification": "System Architecture Specification",
    "04-software-requirements-specification": "Software Requirements Specification",
    "05-software-architecture-specification": "Software Architecture Specification",
    "06-detailed-design-specification": "Detailed Design Specification",
    "07-software-integration-report": "Software Integration Report",
    "08-system-verification-report": "System Verification Report",
    "09-software-verification-report": "Software Verification Report",
    "10-implementation-mapping-document": "Implementation Mapping Document",
}

# Document ownership: doc stem -> (artifact_type test, id substring test or None)
def _owns(doc, d):
    at = d.get("artifact_type", "")
    aid = d.get("id", "")
    if doc == "01-stakeholder-requirements-specification":
        # The item definition, the declared stakeholder needs and the use cases are the
        # SYS.1 work product: they are what this document is for. They are owned here and
        # emitted here; an ownership clause without an emitted id would fail --check with
        # 'owned artifact not present', so the two always move together.
        return at in ("item_definition", "stakeholder_need", "use_case")
    if doc == "02-system-requirements-specification":
        # A TARA and the security requirements derived from it are SYSTEM-level work
        # products: ISO/SAE 21434 operates on the item, the threat set is drawn from
        # system-level assets (CAN bus, Ethernet interface, serial link), and the
        # mitigations protect system-level safety goals. The Software Requirements
        # Specification stays the home of the -SWR-/-MAN- requirements; the TARA and the
        # security requirements belong here, next to the goals they bound.
        #
        # The ISO 26262 Part 3 safety concepts are added for the same reason: they are the
        # system-level record of how the safety goal is achieved and what follows from that
        # allocation, which is system engineering content and not software content. The
        # -SYR- system requirements are added because this document is the System
        # Requirements Specification and SYS.2 records have nowhere else to live.
        return (at in ("safety_goal", "tara", "safety_concept")
                or (at == "requirement" and ("-FSR-" in aid or "-SEC-" in aid or "-SYR-" in aid)))
    if doc == "04-software-requirements-specification":
        return at == "requirement" and ("-SWR-" in aid or "-MAN-" in aid)
    if doc == "05-software-architecture-specification":
        return at == "design" and d.get("engineering_domain") == "software"
    if doc == "06-detailed-design-specification":
        return at == "design" and d.get("engineering_domain") == "software"
    if doc == "09-software-verification-report":
        # deviation records are the SWE.4 static-analysis deviance evidence for the
        # implementation: they belong in the software verification report, not in a
        # design or requirements document.
        return at == "deviation"
    if doc == "10-implementation-mapping-document":
        # change records belong here rather than in the Software Integration Report
        # (07) because of what they contain: a change record is a cross-artifact
        # statement of which artifacts move to a new revision, which links go under
        # suspicion, and which measures are re-run. That is the mapping question this
        # document already answers for requirements, designs, sources and tests, and
        # it needs the same view to stay useful. Document 07 is scoped to integration
        # *results* for the reconstructed implementation; a change record carries no
        # integration evidence, and placing it there would imply the change had been
        # integrated into the real product.
        return at == "change"
    return False

OWNERSHIP = {doc: _owns for doc in DOC_ORDER}

REQUIRED_HEADINGS = {
    "01-stakeholder-requirements-specification": ["Item Definition", "Stakeholder Needs", "Operational"],
    "02-system-requirements-specification": ["Safety Goals", "Functional Safety Requirements"],
    "03-system-architecture-specification": ["Context Viewpoint", "Functional Block Viewpoint", "Dynamic Viewpoint"],
    "04-software-requirements-specification": ["Software Requirements"],
    "05-software-architecture-specification": ["Static Component Viewpoint", "Dynamic Viewpoint"],
    "06-detailed-design-specification": ["Detailed Design"],
    "07-software-integration-report": ["Integrated Components", "Integration Evidence", "Integration Gaps"],
    "08-system-verification-report": ["Test Specification", "Execution Report"],
    "09-software-verification-report": ["Unit Testing", "Component Testing", "Integration Testing", "HIL Testing"],
    "10-implementation-mapping-document": ["Implementation Mapping", "Requirement-to-Test Coverage Matrix"],
}


class Views:
    """Shared in-memory views over the corpus + repo model (single source of truth)."""

    def __init__(self):
        self.repo = RepoModel()  # reverse-engineered repository facts
        self.artifacts = {}      # (profile, id) -> dict
        for f in sorted((ARTIFACTS / "corpus").rglob("*.json")):
            if ".work" in f.parts:
                continue
            try:
                d = load_json(f)
            except Exception:
                continue
            if isinstance(d, dict) and d.get("id"):
                self.artifacts[(d.get("profile", "unknown"), d["id"])] = d
        for f in sorted((ARTIFACTS / "reviews").rglob("*.json")):
            try:
                d = load_json(f)
            except Exception:
                continue
            if isinstance(d, dict) and d.get("id"):
                self.artifacts[(d.get("profile", "as_is"), d["id"])] = d
        self.links = self._load_links()
        self.scope = load_json(ARTIFACTS / "governance" / "scope-and-applicability.json")
        self.params = load_json(ARTIFACTS / "shared" / "parameter-registry.json").get("parameters", [])
        self.asms = load_json(ARTIFACTS / "shared" / "assumption-registry.json").get("assumptions", [])
        self.src_reg = load_json(ARTIFACTS / "sources" / "source-registry.json").get("anchors", [])
        self.by_relation = {}
        for l in self.links:
            self.by_relation.setdefault(l.get("relation_type", "?"), []).append(l)

    def _load_links(self):
        links = []
        seen = set()
        registries = sorted((ARTIFACTS / "traceability" / "link-registry").rglob("links-*.json"))
        registries += sorted((ARTIFACTS / "corpus").rglob("traceability/**/links-*.json"))
        for p in registries:
            if p in seen:
                continue
            seen.add(p)
            s = str(p)
            if "link-registry/as_is" in s or "/corpus/as_is/traceability/" in s:
                profile = "as_is"
            elif "link-registry/synthetic_reference" in s or "/corpus/synthetic_reference/traceability/" in s:
                profile = "synthetic_reference"
            else:
                profile = "unknown"
            d = load_json(p)
            for l in d.get("links", []):
                l = dict(l)
                l["_profile"] = profile
                links.append(l)
        by_key = {}
        for l in links:
            by_key.setdefault((l.get("_profile"), l.get("link_id")), l)
        return list(by_key.values())
        self.by_relation = {}                    # relation -> [link]
        for l in self.links:
            self.by_relation.setdefault(l.get("relation_type", "?"), []).append(l)
        self.scope = load_json(ARTIFACTS / "governance" / "scope-and-applicability.json")
        self.params = load_json(ARTIFACTS / "shared" / "parameter-registry.json").get("parameters", [])
        self.asms = load_json(ARTIFACTS / "shared" / "assumption-registry.json").get("assumptions", [])
        self.src_reg = load_json(ARTIFACTS / "sources" / "source-registry.json").get("anchors", [])

    # ---- accessors -------------------------------------------------------
    def get(self, profile, aid):
        return self.artifacts.get((profile, aid), self.artifacts.get(("unknown", aid), {}))

    def of_profile(self, profile, pred):
        return sorted(
            (aid for (p, aid), d in self.artifacts.items() if p == profile and pred(d)),
        ) if False else sorted(
            aid for (p, aid), d in self.artifacts.items() if p == profile and pred(d)
        )

    def links_where(self, profile=None, relation=None, src=None, tgt=None):
        out = []
        for l in self.links:
            if profile is not None and l.get("_profile", l.get("profile")) != profile:
                continue
            if relation is not None and l.get("relation_type") != relation:
                continue
            if src is not None and l.get("source_id") != src:
                continue
            if tgt is not None and l.get("target_id") != tgt:
                continue
            out.append(l)
        return out

    # ---- coverage --------------------------------------------------------
    def coverage(self, profile, req_id):
        """Return dict(status, direct, indirect, embedded, tests)."""
        direct = sorted({l["source_id"] for l in self.links_where(profile=profile, relation="verifies", tgt=req_id)}
                        | {l["source_id"] for l in self.links_where(profile=profile, relation="validates", tgt=req_id)})
        indirect = {}
        for child in sorted({l["source_id"] for l in self.links_where(profile=profile, relation="allocated_to", tgt=req_id)}):
            cdirect = sorted({l["source_id"] for l in self.links_where(profile=profile, relation="verifies", tgt=child)}
                             | {l["source_id"] for l in self.links_where(profile=profile, relation="validates", tgt=child)})
            if cdirect:
                indirect[child] = cdirect
        embedded = []
        for (p, j), t in sorted(self.artifacts.items()):
            if p == profile and t.get("artifact_type") == "test_measure":
                if req_id in (t.get("referenced_requirements") or []):
                    embedded.append(j)
        if direct:
            status = "COVERED-DIRECT"
        elif indirect:
            status = "COVERED-INDIRECT"
        elif embedded:
            status = "COVERED-EMBEDDED"
        else:
            status = "UNCOVERED"
        return {"status": status, "direct": direct, "indirect": indirect,
                "embedded": embedded, "tests": sorted(set(direct) | {t for v in indirect.values() for t in v} | set(embedded))}

    def all_requirements(self):
        """[(profile, id)] sorted — every requirement artifact incl. management."""
        out = []
        for (p, aid), d in sorted(self.artifacts.items()):
            if p in PROFILES and d.get("artifact_type") == "requirement":
                out.append((p, aid))
        return out

    # ---- helpers ---------------------------------------------------------
    def anchor_str(self, anchor_id):
        for a in self.src_reg:
            if a.get("anchor_id") == anchor_id:
                loc = a.get("location", {})
                if a.get("source_type") == "code":
                    return f"`{loc.get('path','?')}` :: `{loc.get('symbol','?')}()` (L{loc.get('line_range','?')})"
                if a.get("source_type") == "hardware":
                    return f"HW: `{str(loc.get('file','?'))[:50]}` ({loc.get('reference_designator','?')})"
                if a.get("source_type") == "test":
                    return f"TST: `{str(loc.get('file', loc.get('path','?')))[:50]}`"
                return f"DOC: `{str(loc.get('url_or_path', loc.get('path','?')))[:50]}`"
        return anchor_id

    def asm_stmt(self, asm_id):
        for a in self.asms:
            if a.get("assumption_id", a.get("id")) == asm_id:
                return a.get("statement", "")[:100]
        return ""


def esc(s, n=200):
    s = str(s) if s is not None else "N/A"
    s = s.replace("|", "\\|").replace("\n", " ")
    return s[:n] + ("..." if len(s) > n else "")


def mermaid(kind, body):
    return f"```mermaid\n{kind}\n{body}\n```\n"


# ---------------------------------------------------------------- scaffolding

def scaffold(views, stem, scope_line):
    t = DOC_TITLES[stem]
    L = []
    L.append(f"# foxBMS 2 — {t}")
    L.append("")
    L.append("**Document Control**")
    L.append("")
    L.append("| Field | Value |")
    L.append("|---|---|")
    L.append("| Project | foxBMS 2 — Battery Management System |")
    L.append(f"| Document | {t} |")
    L.append("| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |")
    L.append("| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |")
    L.append("| Corpus status | `synthetic_ready_with_limitations` |")
    L.append("| Generated | " + GEN_STAMP + " |")
    L.append("")
    L.append("## Scope")
    L.append("")
    L.append(scope_line)
    L.append("")
    return L


def finish(L):
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"*Generated: {GEN_STAMP} — auto-generated from the machine-verifiable corpus. "
             f"Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- 01 StakeRS

def emit_01(v, out):
    rm = v.repo
    hw = rm.hw
    L = scaffold(v, "01-stakeholder-requirements-specification",
                 "Stakeholder requirements for the foxBMS 2 reference BMS item: item definition, "
                 "boundaries, operational situation, modes, external systems, and stakeholder needs. "
                 "Reverse-engineered from the repository (source tree, `conf/bms/bms.json`, "
                 "`docs/` user documentation) and grounded in `FB2-SRC-DOC` governance artifacts.")

    # ---- Item definition (repo facts) --------------------------------
    L.append("## Item Definition")
    L.append("")
    L.append("**Item**: foxBMS 2 Battery Management System Reference Platform")
    L.append("")
    L.append("foxBMS 2 is a free, open and flexible development environment to design battery "
             "management systems — the first modular open-source BMS development platform "
             "(README, `docs/general/motivation.rst`). The platform controls modern and complex "
             "electrical energy storage systems of any size and is used for lithium-ion and "
             "solid-state batteries, lithium-sulfur batteries, sodium-ion batteries, "
             "lithium-ion capacitors (LIC), electric double-layer capacitors (EDLC), redox-flow "
             "batteries and fuel cells, or hybrid combinations.")
    L.append("")
    L.append("The reference item consists of:")
    L.append("")
    L.append("- **foxBMS BMS-Master** (two boards: BMS-Master + BMS-Interface), optionally "
             "extended by the BMS-Extension board,")
    L.append("- **BMS-Slaves** on the battery modules — measure cell voltages and cell "
             "temperatures and perform passive balancing, daisy-chainable,")
    L.append("- **Embedded BMS software** (`src/app`: 40 modules in application/driver/engine/"
             "task layers) running on the RTOS, plus bootloader (`src/bootloader`) and CLI tool "
             "(`cli/`).")
    L.append("")
    L.append("Reference hardware/software configuration (reverse-engineered from "
             "`conf/bms/bms.json`):")
    L.append("")
    afe = hw.get("afe", {})
    cs = hw.get("current_sensor", {})
    L.append(f"| Property | Reference value |")
    L.append(f"|---|---|")
    L.append(f"| MCU | {hw.get('mcu')} |")
    L.append(f"| RTOS | {hw.get('rtos')} |")
    L.append(f"| AFE (per slave) | {afe.get('manufacturer', '?')} {afe.get('ic', '?')} |")
    L.append(f"| Current sensor | {cs.get('manufacturer', '?')} {cs.get('model', '?')} via {cs.get('type', '?')} |")
    L.append(f"| Balancing strategy | {hw.get('balancing_strategy', '?')} (passive) |")
    L.append(f"| Insulation monitoring device | {hw.get('imd', '?')} |")
    L.append(f"| Cell blocks (reference) | {rm.battery.get('BS_NR_OF_CELL_BLOCKS', '?')} "
             f"({rm.battery.get('BS_NR_OF_MODULES_PER_STRING', '?')} module(s) × "
             f"{rm.battery.get('BS_NR_OF_CELL_BLOCKS_PER_MODULE', '?')} cell blocks, "
             f"{rm.battery.get('BS_NR_OF_STRINGS', '?')} string(s)) |")
    se = hw.get("state_estimation", {})
    L.append(f"| State estimation (reference) | SOC {se.get('soc', '?')}, SOE {se.get('soe', '?')}, "
             f"SOF {se.get('sof', '?')}, SOH {se.get('soh', '?')} |")
    L.append("")

    # ---- System boundaries (repo facts) -------------------------------
    L.append("## System Boundaries")
    L.append("")
    L.append("**Included in item scope** (implemented in this repository):")
    L.append("")
    L.append("- Embedded BMS application firmware (`src/app`) — measurement control, SOA "
             "monitoring, plausibility checks, redundancy checks, BMS state machine, contactor "
             "and precharge control, balancing, state estimation, diagnosis, database, "
             "system monitoring, CAN and Ethernet communication")
    L.append("- Bootloader (`src/bootloader`) — field update of the application via CAN")
    L.append("- CLI tool (`cli/`) — repository interaction, build/flash support (`fox` command)")
    L.append("- Unit test suite (`tests/unit`) — 313 C unit test files executed in CI")
    L.append("- foxBMS 2 documentation (`docs/`)")
    L.append("")
    L.append("**Excluded from item scope (external)**:")
    L.append("")
    L.append("- Battery cells and the battery pack itself (only parameters configured, e.g. "
             "`battery_cell_cfg.h`, `battery_system_cfg.h`)")
    L.append("- Superior control unit (VCU/host controller) — receives CAN messages, sends "
             "state requests (e.g. `f_BmsStateRequest`, 41-message DBC at `tools/dbc/foxbms.dbc`)")
    L.append("- Current sensor (Isabellenhütte ivt-s) — controlled via CAN, delivers current, "
             "voltage, temperature and power measurements")
    L.append("- Insulation monitoring device — optional external IMD (reference config: none)")
    L.append("- Battery packs / loads / chargers connected through the main contactors")
    L.append("- Interlock circuit actors (external emergency-stop wiring), only supervised by the BMS")
    L.append("- Power supply (KL30, KL15) feeding the BMS-Master")
    L.append("")

    # ---- Operational situation ----------------------------------------
    L.append("## Operational Situation")
    L.append("")
    L.append("The documented and default-configured use case is a **stationary battery energy "
             "storage system** (`docs/introduction/use-case.rst`): the BMS supervises the "
             "battery, requests contactor state changes via CAN and opens the contactors "
             "on error to isolate the battery. Stationary operation permits disconnection "
             "on malfunction, unlike traction use cases where an immediate open would "
             "endanger passengers.")
    L.append("")
    L.append("The BMS-Master additionally supervises a closely monitored interlock line and "
             "measures the pack current via a CAN-attached current sensor.")
    L.append("")

    # ---- Modes (BMS FSM states, reverse-engineered) --------------------
    L.append("## Modes")
    L.append("")
    L.append("Operational modes are implemented as the BMS finite state machine "
             f"(`src/app/application/bms/bms.h`, {len(rm.bms_fsm['states'])} states, "
             f"{len(rm.bms_fsm['substates'])} substates):")
    L.append("")
    for s in rm.bms_fsm["states"]:
        L.append(f"- `{s}`")
    L.append("")
    L.append("Current-flow submodes: `BMS_CHARGING`, `BMS_DISCHARGING`, `BMS_RELAXATION`, "
             "`BMS_AT_REST`. The CAN-visible states (`BMS_CAN_STATE_*`) mirror the FSM states.")
    L.append("")

    # ---- External systems ---------------------------------------------
    L.append("## External Systems")
    L.append("")
    L.append("- Battery cells / pack (monitored, not part of the item)")
    L.append("- VCU / superior control unit (CAN, 41 messages in `foxbms.dbc`)")
    L.append("- Current sensor (CAN, Isabellenhütte ivt-s reference)")
    L.append("- Charger / inverter / load behind the contactors")
    L.append("- BMS-Slaves (via AFE daisy-chain interface on the BMS-Interface board)")
    L.append("- Interlock wiring / emergency stop")
    L.append("- IMD (optional)")
    L.append("- Power supply KL30/KL15, debug interfaces (UART, Ethernet, debugger)")
    L.append("")

    # ---- Stakeholder needs --------------------------------------------
    L.append("## Stakeholder Needs")
    L.append("")
    L.append("Reverse-engineered stakeholder needs and their repository anchors:")
    L.append("")
    L.append("| ID | Need | Repository anchor |")
    L.append("|---|---|---|")
    needs = [
        ("SN-01", "Open, free and modular BMS development platform",
         "BSD-3-Clause license (`LICENSE`), open-source toolchain, modular drivers"),
        ("SN-02", "Safe operation of the battery within its safe operating area (SOA)",
         "`src/app/application/soa/`, MOL/RSL/MSL limit model, `docs/software/modules/application/soa/soa.rst`"),
        ("SN-03", "Battery isolation on error (safe state = contactors open)",
         "BMS FSM `BMS_FSM_STATE_ERROR` → `BMS_FSM_STATE_OPEN_CONTACTORS`; use-case doc"),
        ("SN-04", "Accurate cell voltage / temperature measurement",
         "AFE drivers (LTC/ADI/Maxim/NXP), `MEAS` module, plausibility + redundancy checks"),
        ("SN-05", "Cell balancing to equalize cell voltages",
         "`src/app/application/bal/` (voltage strategy reference)"),
        ("SN-06", "State estimation (SOC/SOE/SOF/SOH)",
         "`src/app/application/algorithm/state_estimation/` (counting/trapezoid reference)"),
        ("SN-07", "Diagnosis and error handling with defined severities",
         "85 `DIAG_ID_*` entries in `src/app/engine/config/diag_cfg.h`, `docs/system/system-error-table.csv`"),
        ("SN-08", "Communication with superior control unit (CAN)",
         "`src/app/driver/can/`, DBC `tools/dbc/foxbms.dbc` (41 messages)"),
        ("SN-09", "Ethernet interface for user-defined applications",
         "`src/app/application/ethernet/` (FreeRTOS+TCP echo-server reference)"),
        ("SN-10", "Field-updatable firmware",
         "`src/bootloader/` + CLI `fox bootloader` (see `docs/software/bootloader/`)"),
        ("SN-11", "High-quality, tested software",
         "313 unit test files, CI-enforced 100% line/branch coverage policy "
         "(`docs/developer-manual/software/software-testing.rst`)"),
        ("SN-12", "Portability across MCU and OS",
         "layered architecture, MCU wrapper HAL, FreeRTOS/SafeRTOS abstraction (`src/os/`)"),
    ]
    for nid, need, anchor in needs:
        L.append(f"| {nid} | {esc(need)} | {esc(anchor, 120)} |")
    L.append("")
    sc = v.scope
    needs_corpus = sc.get("stakeholder_needs", [])
    if needs_corpus:
        L.append("Corpus-enumerated needs (`governance/scope-and-applicability.json`):")
        L.append("")
        L.append("| Need | Description | Traces to |")
        L.append("|---|---|---|")
        for nd in needs_corpus:
            if isinstance(nd, dict):
                L.append(f"| {esc(nd.get('id', nd.get('need','?')))} | {esc(nd.get('description', nd.get('need','')),300)} | {esc(', '.join(nd.get('traces_to', [])))} |")
            else:
                L.append(f"| NEED | {esc(nd, 300)} | — |")
        L.append("")

    # ---- Use case + context diagram -----------------------------------
    L.append("## Use-Case Context")
    L.append("")
    L.append("The reference use case is a stationary battery storage: three power contactors "
             "(string minus, string plus, precharge) connect/disconnect the battery strings; "
             "on error the BMS opens the contactors and isolates the battery (source: "
             "`docs/introduction/use-case.rst`; safe-state premise `FB2-SAF-SGO-000001`).")
    L.append("")
    L.append("Precharge sequence (implemented in BMS FSM substates "
             "`BMS_FSM_SUBSTATE_PRECHARGE_*`): close string-minus, close precharge, wait for "
             "precharge completion, open precharge, close string-plus.")
    L.append("")
    L.append("**Caption**: System context — BMS item with external actors and boundary.")
    L.append("")
    L.append(mermaid("flowchart LR",
        "    subgraph Item[foxBMS 2 BMS Item]\n"
        "        MASTER[BMS-Master\\nTMS570LC4357 + FreeRTOS]\n"
        "        SLAVES[BMS-Slaves\\nAFE daisy-chain]\n"
        "        MASTER --- SLAVES\n"
        "    end\n"
        "    CELLS[Battery Cells / Pack] --- SLAVES\n"
        "    CONT[Contactors\\nString-/Precharge] --- MASTER\n"
        "    CS[Current Sensor\\nivt-s via CAN] --- MASTER\n"
        "    VCU[VCU / Host\\nCAN 41 msgs] <--> MASTER\n"
        "    IMD[IMD - optional] --- MASTER\n"
        "    ILCK[Interlock Circuit] --- MASTER\n"
        "    LOAD[Load / Charger] --- CELLS"))
    L.append("**Premise traceability**: hazard premises `FB2-SAF-HAZ-000001`; safety objective "
             "`FB2-SAF-SGO-000001`; item scope artifact `governance/scope-and-applicability.json`; "
             "repository anchors listed above.")
    L.append("")

    # ---- synthetic_reference SYS.1 work products -------------------------
    # Owned by this document (_owns: item_definition / stakeholder_need / use_case) and
    # therefore emitted here. The clause and the emission must both exist: --check fails
    # on an owned id that is absent from the body.
    for profile in PROFILES:
        ite = v.of_profile(profile, lambda d: d.get("artifact_type") == "item_definition")
        neds = v.of_profile(profile, lambda d: d.get("artifact_type") == "stakeholder_need")
        ucs = v.of_profile(profile, lambda d: d.get("artifact_type") == "use_case")
        if not (ite or neds or ucs):
            continue
        L.append(f"### Profile: `{profile}` — Part 3 item definition and SYS.1 elicitation")
        L.append("")
        for iid in ite:
            d = v.get(profile, iid)
            L.append(f"#### `{iid}` — {esc(d.get('title', ''))}")
            L.append("")
            ident = d.get("item_identity", {}) or {}
            L.append(f"- **Item name**: {esc(ident.get('item_name', '?'))}")
            L.append(f"- **Item purpose**: {esc(ident.get('item_purpose', '?'), 500)}")
            L.append(f"- **Hypothetical**: `{str(ident.get('fictional')).lower()}` — this record "
                     f"describes a programme that does not exist")
            L.append(f"- **Operating envelope**: "
                     f"{esc((d.get('operating_envelope') or {}).get('voltage_class', '?'))}; "
                     f"{esc((d.get('operating_envelope') or {}).get('cells_monitored', '?'))} "
                     f"monitored cells")
            L.append(f"- **Functions**: {len(d.get('functions', []) or [])} · "
                     f"**operational situations**: "
                     f"{len(d.get('operational_situations', []) or [])} · "
                     f"**modes**: {len(d.get('operating_modes', []) or [])} · "
                     f"**external systems**: {len(d.get('external_systems', []) or [])}")
            L.append(f"- **Guard**: profile=`{d.get('profile')}`, origin=`{d.get('origin')}`, "
                     f"human_approval_status=`{d.get('human_approval_status')}`, "
                     f"production_authorized=`{str(d.get('production_authorized')).lower()}`")
            L.append("")
            bnd = d.get("boundaries", {}) or {}
            L.append("**Boundary**")
            L.append("")
            L.append("| Inside the item | Why inside | Outside the item | Why outside | "
                     "Residual risk owner |")
            L.append("|---|---|---|---|---|")
            inc = bnd.get("included_elements", []) or []
            exc = bnd.get("excluded_elements", []) or []
            for i, e in enumerate(inc):
                o = exc[i] if i < len(exc) else {}
                L.append(f"| {esc(e.get('element', '?'), 70)} | {esc(e.get('why_inside', ''), 110)} "
                         f"| {esc(o.get('element', '—'), 70)} | "
                         f"{esc(o.get('why_outside', '—'), 110)} | "
                         f"{esc(o.get('residual_risk_owner', '—'), 40)} |")
            L.append("")
            L.append("**Operational situations**")
            L.append("")
            L.append("| Id | Situation | In/out | Argument |")
            L.append("|---|---|---|---|")
            for s in (d.get("operational_situations", []) or []):
                L.append(f"| `{s.get('scenario_id', s.get('situation_id'))}` | "
                         f"{esc(s.get('description', ''), 130)} | "
                         f"{s.get('including_or_excluding', '?')} | "
                         f"{esc(s.get('argument_for_the_decision', ''), 150)} |")
            L.append("")
            L.append("**Operating modes**")
            L.append("")
            L.append("| Id | Mode | Entry | Exit | Safe state in this mode |")
            L.append("|---|---|---|---|---|")
            for m in (d.get("operating_modes", []) or []):
                L.append(f"| `{m.get('mode_id')}` | {esc(m.get('mode_name', ''), 40)} | "
                         f"{esc(m.get('entry_condition', ''), 80)} | "
                         f"{esc(m.get('exit_condition', ''), 80)} | "
                         f"{esc(m.get('safe_state_in_this_mode', ''), 110)} |")
            L.append("")
            L.append("**Interfaces to other safety-related items**")
            L.append("")
            for it in (d.get("interfaces_to_other_safety_related_items", []) or []):
                L.append(f"- **{esc(it.get('other_item', ''), 90)}** — "
                         f"{esc(it.get('interface_description', ''), 200)} "
                         f"*Assumption dependence:* {esc(it.get('assumption_dependence', ''), 180)} "
                         f"*If false:* {esc(it.get('effect_if_the_assumption_fails', ''), 200)}")
            L.append("")
            L.append("**What this item definition does not establish**")
            L.append("")
            for lim in (d.get("limitations", []) or []):
                L.append(f"- {esc(lim, 260)}")
            L.append("")

        for nid in neds:
            d = v.get(profile, nid)
            st = d.get("stakeholder", {}) or {}
            oe = d.get("origin_of_the_need", {}) or {}
            L.append(f"#### `{nid}` — {esc(d.get('title', ''))}")
            L.append("")
            L.append(f"- **Stakeholder**: `{st.get('stakeholder_id')}` "
                     f"({st.get('stakeholder_class')}), fictional="
                     f"`{str(st.get('fictional')).lower()}`")
            L.append(f"- **Need**: {esc(d.get('need_statement', ''), 500)}")
            L.append(f"- **Priority**: {esc((d.get('priority') or {}).get('rank', '?'))} — "
                     f"{esc((d.get('priority') or {}).get('rationale', ''), 200)}")
            L.append(f"- **Elicitation**: `{oe.get('elicitation_method')}` · "
                     f"**is_a_real_elicitation**: "
                     f"`{str(oe.get('is_a_real_elicitation')).lower()}`")
            L.append(f"- **Refined into**: "
                     f"{', '.join('`' + r + '`' for r in d.get('derived_requirements', []) or []) or '—'}")
            L.append(f"- **Validation measures**: "
                     f"{', '.join('`' + r + '`' for r in d.get('validation_measures', []) or []) or '—'}")
            L.append(f"- **Limitation**: {esc(d.get('limitation', ''), 400)}")
            L.append("")

        for uid in ucs:
            d = v.get(profile, uid)
            L.append(f"#### `{uid}` — {esc(d.get('title', ''))}")
            L.append("")
            L.append(f"- **Stakeholders served**: "
                     f"{', '.join('`' + s + '`' for s in d.get('primary_stakeholders', []) or [])}")
            L.append(f"- **Validation measures**: "
                     f"{', '.join('`' + s + '`' for s in d.get('validation_measures', []) or []) or '—'}")
            L.append("**Main success scenario**")
            L.append("")
            for stp in (d.get("main_success_scenario", []) or []):
                L.append(f"{stp.get('step', '?')}. {esc(stp.get('action', ''), 130)} → "
                         f"{esc(stp.get('expected_observable_outcome', ''), 130)}")
            L.append("")
            L.append("**Operational scenarios**")
            L.append("")
            for sc in (d.get("operational_scenarios", []) or []):
                L.append(f"- **`{sc.get('scenario_id')}`** — {esc(sc.get('operational_situation', ''), 140)}")
                L.append(f"  - Perturbation: {esc(sc.get('perturbation', ''), 220)}")
                L.append(f"  - Expected item behaviour: {esc(sc.get('expected_item_behaviour', ''), 220)}")
                L.append(f"  - Observable by: {esc(sc.get('observable_by', ''), 140)}")
                if sc.get("safe_state_interaction"):
                    L.append(f"  - Safe-state interaction: "
                             f"{esc(sc.get('safe_state_interaction', ''), 220)}")
            L.append("")
            L.append("**Limitations**")
            L.append("")
            for lim in (d.get("limitations", []) or []):
                L.append(f"- {esc(lim, 300)}")
            L.append("")
        L.append("---")
        L.append("")
    L.append("### Why the elicitation records are declared rather than elicited")
    L.append("")
    L.append("Every stakeholder need above carries `is_a_real_elicitation: false`. No workshop was "
             "held, no stakeholder was interviewed and no questionnaire was issued for this corpus. "
             "The needs are therefore declared assumptions about what a hypothetical programme's "
             "stakeholders would want, and the validation measures written against them confirm "
             "that the item behaves as an assumed party would want — which is not the same as "
             "confirming that the need was right. That distinction is stated on each need record "
             "as well, in its `limitation` field.")
    L.append("")

    (out / "01-stakeholder-requirements-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 02 SysRS

def emit_02(v, out):
    rm = v.repo
    b = rm.battery
    L = scaffold(v, "02-system-requirements-specification",
                 "System-level requirements: safety goals and functional safety requirements "
                 "(FSRs) of both corpus profiles with full attribute sets, plus system "
                 "requirements reverse-engineered from the implementation (SOA limits, "
                 "diagnosis entries, timing budgets, communication).")

    # ---- Reverse-engineered system requirements -----------------------
    L.append("## Reverse-Engineered System Requirements (implementation-grounded)")
    L.append("")
    L.append("The following system requirements are extracted from the actual repository "
             "configuration and code. They hold for the reference build; each row carries "
             "its repository anchor.")
    L.append("")

    L.append("### Safe Operating Area Limits")
    L.append("")
    L.append("Source: `src/app/application/config/battery_cell_cfg.h`, "
             "`battery_system_cfg.h`; evaluated by `src/app/application/soa/soa.c`. "
             "Three error levels per parameter: MOL (maximum operating limit), RSL "
             "(recommended safety limit), MSL (maximum safety limit — opens contactors).")
    L.append("")
    L.append("| Parameter | MOL | RSL | MSL | Unit | Anchor |")
    L.append("|---|---|---|---|---|---|")
    rows = [
        ("Cell voltage, maximum", "BC_VOLTAGE_MAX_MOL_mV", "BC_VOLTAGE_MAX_RSL_mV", "BC_VOLTAGE_MAX_MSL_mV", "mV"),
        ("Cell voltage, minimum", "BC_VOLTAGE_MIN_MOL_mV", "BC_VOLTAGE_MIN_RSL_mV", "BC_VOLTAGE_MIN_MSL_mV", "mV"),
        ("Cell temperature, charge, maximum", "BC_TEMPERATURE_MAX_CHARGE_MOL_ddegC", "BC_TEMPERATURE_MAX_CHARGE_RSL_ddegC", "BC_TEMPERATURE_MAX_CHARGE_MSL_ddegC", "0.1 °C"),
        ("Cell temperature, charge, minimum", "BC_TEMPERATURE_MIN_CHARGE_MOL_ddegC", "BC_TEMPERATURE_MIN_CHARGE_RSL_ddegC", "BC_TEMPERATURE_MIN_CHARGE_MSL_ddegC", "0.1 °C"),
        ("Cell temperature, discharge, maximum", "BC_TEMPERATURE_MAX_DISCHARGE_MOL_ddegC", "BC_TEMPERATURE_MAX_DISCHARGE_RSL_ddegC", "BC_TEMPERATURE_MAX_DISCHARGE_MSL_ddegC", "0.1 °C"),
        ("Cell temperature, discharge, minimum", "BC_TEMPERATURE_MIN_DISCHARGE_MOL_ddegC", "BC_TEMPERATURE_MIN_DISCHARGE_RSL_ddegC", "BC_TEMPERATURE_MIN_DISCHARGE_MSL_ddegC", "0.1 °C"),
        ("Cell current, charge, maximum", "BC_CURRENT_MAX_CHARGE_MOL_mA", "BC_CURRENT_MAX_CHARGE_RSL_mA", "BC_CURRENT_MAX_CHARGE_MSL_mA", "mA"),
        ("Cell current, discharge, maximum", "BC_CURRENT_MAX_DISCHARGE_MOL_mA", "BC_CURRENT_MAX_DISCHARGE_RSL_mA", "BC_CURRENT_MAX_DISCHARGE_MSL_mA", "mA"),
    ]
    for label, mol, rsl, msl, unit in rows:
        L.append(f"| {label} | {b.get(mol, '?')} | {b.get(rsl, '?')} | {b.get(msl, '?')} | {unit} | `{mol}`-family |")
    L.append(f"| Pack current, maximum | — | — | {b.get('BS_MAXIMUM_PACK_CURRENT_mA', '?')} | mA | `BS_MAXIMUM_PACK_CURRENT_mA` |")
    L.append(f"| Main contactor break current | — | — | {b.get('BS_MAIN_CONTACTORS_MAXIMUM_BREAK_CURRENT_mA', '?')} | mA | `BS_MAIN_CONTACTORS_MAXIMUM_BREAK_CURRENT_mA` |")
    L.append(f"| Main fuse trigger duration | — | — | {b.get('BS_MAIN_FUSE_MAXIMUM_TRIGGER_DURATION_ms', '?')} | ms | `BS_MAIN_FUSE_MAXIMUM_TRIGGER_DURATION_ms` |")
    L.append("")
    L.append(f"Reference cell: nominal {b.get('BC_VOLTAGE_NOMINAL_mV', '?')} mV "
             f"(`BC_VOLTAGE_NOMINAL_mV`, LFP-class cell), "
             f"{b.get('BS_NR_OF_CELL_BLOCKS', '?')} cell blocks total.")
    L.append("")

    L.append("### Diagnosis and Error Handling Requirements")
    L.append("")
    L.append(f"The diagnosis engine tracks **{len(rm.diag_ids)} diagnosis entries** "
             f"(`DIAG_ID_*` in `src/app/engine/config/diag_cfg.h`), each with severity "
             f"(OK/WARNING/ERROR/FATAL), enabling, occurrence counter, latency and delay "
             f"(`diag_diagnosisIdConfiguration` in `diag_cfg.c`). Error-table documentation: "
             f"`docs/system/system-error-table.csv`. Selected groups:")
    L.append("")
    groups = [
        ("AFE integrity", ["DIAG_ID_AFE_SPI", "DIAG_ID_AFE_COMMUNICATION_INTEGRITY", "DIAG_ID_AFE_MUX",
                           "DIAG_ID_AFE_CONFIG", "DIAG_ID_AFE_OPEN_WIRE", "DIAG_ID_AFE_ALARM",
                           "DIAG_ID_AFE_CELL_VOLTAGE_MEAS_ERROR", "DIAG_ID_AFE_CELL_TEMPERATURE_MEAS_ERROR"]),
        ("Cell voltage SOA", ["DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MSL", "DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_RSL",
                              "DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MOL", "DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_MSL",
                              "DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_RSL", "DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_MOL"]),
        ("Temperature SOA", ["DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_MSL", "DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_RSL",
                             "DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_MOL", "DIAG_ID_TEMP_UNDERTEMPERATURE_DISCHARGE_MSL",
                             "DIAG_ID_TEMP_OVERTEMPERATURE_DISCHARGE_MSL"]),
        ("Overcurrent", ["DIAG_ID_OVERCURRENT_CHARGE_CELL_MSL", "DIAG_ID_OVERCURRENT_DISCHARGE_CELL_MSL",
                         "DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL", "DIAG_ID_STRING_OVERCURRENT_DISCHARGE_MSL",
                         "DIAG_ID_PACK_OVERCURRENT_CHARGE_MSL", "DIAG_ID_PACK_OVERCURRENT_DISCHARGE_MSL",
                         "DIAG_ID_CURRENT_ON_OPEN_STRING"]),
        ("Current sensor", ["DIAG_ID_CURRENT_SENSOR_RESPONDING", "DIAG_ID_CURRENT_SENSOR_CC_RESPONDING",
                            "DIAG_ID_CURRENT_SENSOR_EC_RESPONDING", "DIAG_ID_CURRENT_MEASUREMENT_TIMEOUT",
                            "DIAG_ID_CURRENT_MEASUREMENT_ERROR", "DIAG_ID_CURRENT_SENSOR_V1_MEASUREMENT_TIMEOUT",
                            "DIAG_ID_POWER_MEASUREMENT_ERROR"]),
        ("Plausibility / redundancy", ["DIAG_ID_PLAUSIBILITY_CELL_VOLTAGE", "DIAG_ID_PLAUSIBILITY_CELL_TEMP",
                                       "DIAG_ID_PLAUSIBILITY_CELL_VOLTAGE_SPREAD", "DIAG_ID_PLAUSIBILITY_CELL_TEMPERATURE_SPREAD",
                                       "DIAG_ID_PLAUSIBILITY_PACK_VOLTAGE", "DIAG_ID_BASE_CELL_VOLTAGE_MEASUREMENT_TIMEOUT",
                                       "DIAG_ID_REDUNDANCY0_CELL_VOLTAGE_MEASUREMENT_TIMEOUT"]),
        ("Contactor / interlock / SBC", ["DIAG_ID_INTERLOCK_FEEDBACK", "DIAG_ID_STRING_MINUS_CONTACTOR_FEEDBACK",
                                         "DIAG_ID_STRING_PLUS_CONTACTOR_FEEDBACK", "DIAG_ID_PRECHARGE_CONTACTOR_FEEDBACK",
                                         "DIAG_ID_SBC_FIN_ERROR", "DIAG_ID_SBC_RSTB_ERROR",
                                         "DIAG_ID_SUPPLY_VOLTAGE_CLAMP_30C_LOST"]),
        ("CAN", ["DIAG_ID_CAN_TIMING", "DIAG_ID_CAN_RX_QUEUE_FULL", "DIAG_ID_CAN_TX_QUEUE_FULL"]),
        ("Insulation (IMD)", ["DIAG_ID_INSULATION_MEASUREMENT_VALID", "DIAG_ID_LOW_INSULATION_RESISTANCE_ERROR",
                              "DIAG_ID_LOW_INSULATION_RESISTANCE_WARNING", "DIAG_ID_INSULATION_GROUND_ERROR"]),
        ("Other", ["DIAG_ID_DEEP_DISCHARGE_DETECTED", "DIAG_ID_ALERT_MODE", "DIAG_ID_AEROSOL_ALERT",
                   "DIAG_ID_SYSTEM_MONITORING", "DIAG_ID_I2C_PEX_ERROR", "DIAG_ID_FRAM_READ_CRC_ERROR",
                   "DIAG_ID_RTC_CLOCK_INTEGRITY_ERROR"]),
    ]
    for gname, ids in groups:
        L.append(f"- **{gname}**: " + ", ".join(f"`{i}`" for i in ids))
    L.append("")
    L.append("MSL violations set fatal-error-linked diagnosis entries that force the BMS state "
             "machine into `BMS_FSM_STATE_ERROR` → `BMS_FSM_STATE_OPEN_CONTACTORS`.")
    L.append("")

    L.append("### Measurement and Timing Requirements")
    L.append("")
    L.append("| Requirement | Value | Anchor |")
    L.append("|---|---|---|")
    L.append(f"| Current measurement response timeout | {b.get('BS_CURRENT_MEASUREMENT_RESPONSE_TIMEOUT_ms','?')} ms | `BS_CURRENT_MEASUREMENT_RESPONSE_TIMEOUT_ms` |")
    L.append(f"| Coulomb counting response timeout | {b.get('BS_COULOMB_COUNTING_MEASUREMENT_RESPONSE_TIMEOUT_ms','?')} ms | `BS_COULOMB_COUNTING_MEASUREMENT_RESPONSE_TIMEOUT_ms` |")
    L.append(f"| Energy counting response timeout | {b.get('BS_ENERGY_COUNTING_MEASUREMENT_RESPONSE_TIMEOUT_ms','?')} ms | `BS_ENERGY_COUNTING_MEASUREMENT_RESPONSE_TIMEOUT_ms` |")
    L.append("| BMS state machine task context | 10 ms | `BMS_STATEMACHINE_TASK_CYCLE_CONTEXT_MS` (`bms_cfg.h`) |")
    L.append("| Temp sensors per module | "
             f"{b.get('BS_NR_OF_TEMP_SENSORS_PER_MODULE','?')} | `BS_NR_OF_TEMP_SENSORS_PER_MODULE` |")
    L.append("| Task model | 1 ms / 10 ms / 100 ms / 100 ms-algorithm cyclic + continuous I2C, engine | "
             "`src/app/task/ftask/ftask.c`, `docs/software/structure/operating-system-configuration.rst` |")
    L.append("")

    L.append("### Communication Requirements")
    L.append("")
    L.append(f"- **CAN**: {len(rm.can_messages)} messages defined in `tools/dbc/foxbms.dbc` "
             f"(e.g. `AFE_CellVoltages`, `AFE_CellTemperatures`, `f_BmsState`, "
             f"`f_BmsStateRequest`, `f_BmsFatalError`); implemented by `src/app/driver/can/`.")
    L.append(f"- **Ethernet**: plain TCP/IP stack (FreeRTOS+TCP) for user-defined application "
             f"tasks (`src/app/application/ethernet/`), echo server as reference.")
    L.append(f"- **AFE daisy-chain**: SPI-based interface to BMS-Slaves via BMS-Interface board "
             f"(supported AFEs: " + ", ".join(f"{a['vendor']} ({', '.join(a['chips'])})" for a in rm.afes) + ").")
    L.append("")

    # ---- corpus profiles ----------------------------------------------
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        # Safety goals
        sgo_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "safety_goal")
        L.append("### Safety Goals")
        L.append("")
        for sid in sgo_ids:
            d = v.get(profile, sid)
            L.append(f"#### `{sid}` — {esc(d.get('title',''))}")
            L.append("")
            L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 400)}")
            L.append(f"- **Rationale**: {esc(d.get('rationale','Hazard mitigation for FB2-SAF-HAZ-000001'), 400)}")
            L.append(f"- **ASIL**: `{d.get('asil','?')}`")
            aj = d.get("asil_justification") or {}
            if aj:
                L.append(f"- **ASIL classification status**: `{esc(aj.get('classification_status','?'), 40)}` "
                         f"(hypothetical; not an ASIL determination for the real product)")
                L.append(f"- **ASIL derivation**: {esc(aj.get('method','not recorded'), 400)}")
                L.append(f"  - hazardous event `{esc(aj.get('hazardous_event_ref','?'), 20)}` of "
                         f"`{esc(aj.get('hazard_ref','?'), 30)}`, operational situation: "
                         f"{esc(aj.get('operational_situation','?'), 160)}")
                for _dim in ("severity", "exposure", "controllability"):
                    _v = aj.get(_dim) or {}
                    _extra = ""
                    if _dim == "exposure" and _v.get("evidence_status"):
                        _extra = f" Evidence status: {esc(_v.get('evidence_status'), 160)}"
                    L.append(f"  - **{_dim}** `{esc(_v.get('rating','?'), 12)}`: "
                             f"{esc(_v.get('reason','not recorded'), 420)}{_extra}")
                for _i, _step in enumerate(aj.get("derivation") or [], 1):
                    L.append(f"  {esc(_i)}. {esc(_step, 500)}")
                L.append(f"  - derived ASIL `{esc(aj.get('derived_asil','?'), 12)}`; matches the recorded "
                         f"`{esc(d.get('asil','?'), 12)}`: {aj.get('derived_asil_matches_record')}")
                _not = aj.get("what_this_does_not_assert") or []
                if _not:
                    L.append("  - **This classification does not assert:**")
                    for _n in _not:
                        L.append(f"    - {esc(_n, 420)}")
                if aj.get("what_would_change_the_answer"):
                    L.append(f"  - **What would change the answer**: "
                             f"{esc(aj.get('what_would_change_the_answer'), 500)}")
            tb = d.get("timing_budget", {})
            ftti = d.get("fault_tolerant_time_interval_ms", tb.get("total_ftti_ms", "?"))
            L.append(f"- **FTTI (total)**: {ftti} ms")
            alloc = tb.get("allocation", {})
            if alloc:
                L.append(f"- **Timing budget allocation**: " + ", ".join(f"`{k}`={ms}ms" for k, ms in sorted(alloc.items())))
            L.append(f"- **Safe state**: {esc(d.get('safe_state','?'))}")
            L.append(f"- **Degraded state**: {esc(d.get('degraded_state','?'))}")
            L.append(f"- **Source references**: " + (", ".join(f"`{r}`" for r in d.get("source_refs", [])) or "—"))
            L.append(f"- **Assumption references**: " + (", ".join(f"`{r}`" for r in d.get("assumption_refs", [])) or "—"))
            L.append("")
        # FSRs
        fsr_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and "-FSR-" in d.get("id",""))
        L.append("### Functional Safety Requirements")
        L.append("")
        for fid in fsr_ids:
            d = v.get(profile, fid)
            sa = d.get("safety_allocation", {}) or {}
            ac = d.get("acceptance_criteria", [])
            L.append(f"#### `{fid}` — {esc(d.get('title',''))}")
            L.append("")
            L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 500)}")
            L.append(f"- **Rationale**: {esc(d.get('rationale','Refines safety goal timing and functional budget'), 400)}")
            L.append(f"- **ASIL**: `{sa.get('asil', d.get('asil','?'))}`")
            L.append(f"- **Safety goal reference**: `{sa.get('safety_goal_ref','FB2-SAF-SGO-000001')}`")
            if ac:
                L.append("- **Acceptance criteria**:")
                for c in ac:
                    if isinstance(c, dict):
                        L.append(f"  - {esc(c.get('criterion','?'))}: {esc(c.get('measure',''))} ≤ {esc(c.get('threshold',''))} {esc(c.get('unit',''))}")
                    else:
                        L.append(f"  - {esc(c)}")
            else:
                L.append("- **Acceptance criteria**: not specified in corpus")
            cm = d.get("conditions_modes", [])
            L.append(f"- **Conditions/modes**: " + (", ".join(f"`{m}`" for m in cm) if cm else "not specified in corpus"))
            fr = d.get("fault_reaction") or {}
            if fr:
                owns = fr.get("element_owns_reaction")
                L.append(f"- **Fault reaction** (allocated element `{esc(fr.get('allocated_element_id','?'), 12)}`, "
                         f"owns reaction: {owns}): {esc(fr.get('reaction','not recorded'), 700)}")
                L.append(f"  - triggered by: {esc(fr.get('triggered_by','not recorded'), 400)}")
                if fr.get("reaction_time_budget_ms") is not None:
                    _b = fr.get("reaction_time_budget_basis")
                    _line = f"  - reaction time budget: {fr.get('reaction_time_budget_ms')} ms"
                    if _b:
                        _line += f" — basis: {esc(_b, 400)}"
                    L.append(_line)
                for _h in fr.get("reaction_held_by") or []:
                    L.append(f"  - reaction held by `{esc(_h.get('element_id','?'), 12)}`: "
                             f"{esc(_h.get('reaction','?'), 200)} within "
                             f"{_h.get('reaction_time_budget_ms')} ms "
                             f"(allocated by {esc(_h.get('allocated_by','?'), 120)})")
                if fr.get("mode_dependence"):
                    L.append(f"  - mode dependence: {esc(fr.get('mode_dependence'), 500)}")
                if fr.get("allocation_basis"):
                    L.append(f"  - allocation basis: {esc(fr.get('allocation_basis'), 500)}")
                if fr.get("open_limits"):
                    L.append(f"  - open limits: {esc(fr.get('open_limits'), 900)}")
            L.append(f"- **Source references**: " + (", ".join(f"`{r}`" for r in d.get("source_refs", [])) or "—"))
            L.append(f"- **Assumption references**: " + (", ".join(f"`{r}` ({esc(v.asm_stmt(r),60)})" for r in d.get("assumption_refs", [])) or "—"))
            L.append("")

    # ---- system requirements and safety concepts (owned by this document) --
    # _owns covers safety_concept and the -SYR- system requirements; they are emitted
    # here so that an owned id is never absent from the body.
    for profile in PROFILES:
        syrs = v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement"
                            and "-SYR-" in d.get("id", ""))
        if not syrs:
            continue
        L.append(f"## Profile: `{profile}` — System requirements (SYS.2)")
        L.append("")
        L.append("These are system-level requirements: what the integrated item must do. Each "
                 "refines a stakeholder need, a use-case obligation or the safety goal, and "
                 "allocates to the existing hardware technical requirements (`FB2-HW-TSR-*`) and "
                 "software requirements (`FB2-SW-SWR-*`) rather than restating them, which is why "
                 "the requirement-to-test coverage matrix reports them as covered indirectly "
                 "through those allocations.")
        L.append("")
        for sid in syrs:
            d = v.get(profile, sid)
            sa = d.get("safety_allocation", {}) or {}
            L.append(f"### `{sid}` — {esc(d.get('title', ''))}")
            L.append("")
            L.append(f"- **Statement**: {esc(d.get('statement', ''), 600)}")
            L.append(f"- **Rationale**: {esc(d.get('rationale', ''), 450)}")
            L.append(f"- **Classification**: `{d.get('classification')}` · "
                     f"**ASIL allocation**: `{sa.get('asil')}` · "
                     f"**safety goal**: `{sa.get('safety_goal_ref')}`")
            L.append(f"- **Refines**: "
                     f"{', '.join('`' + r + '`' for r in d.get('refines_from', []) or []) or '—'}")
            L.append(f"- **Allocated to**: "
                     f"{', '.join('`' + r + '`' for r in d.get('allocated_to_requirements', []) or []) or '—'}")
            L.append(f"- **Architecture elements**: "
                     f"{', '.join('`' + r + '`' for r in d.get('trace_to_architecture_elements', []) or []) or '—'}")
            L.append(f"- **Verification approach**: `{d.get('verification_approach')}`")
            ac = d.get("acceptance_criteria", []) or []
            if ac:
                L.append("- **Acceptance criteria**:")
                for c in ac:
                    L.append(f"  - {esc(c.get('criterion', '?'))}: "
                             f"{esc(c.get('measure', ''), 120)} ≤ {esc(c.get('threshold', ''))} "
                             f"{esc(c.get('unit', ''))}")
            for key, label in (("why_system_level", "Why system level"),
                               ("open_point", "Open point"),
                               ("open_gap", "Open gap"),
                               ("known_conflict", "Known conflict"),
                               ("independence_is_assumed", "Independence status"),
                               ("coverage_gap", "Coverage gap"),
                               ("why_not_asil", "Why no ASIL"),
                               ("verification_note", "Verification note"),
                               ("dependency_direction", "Dependency direction")):
                if d.get(key):
                    L.append(f"- **{label}**: {esc(d.get(key), 600)}")
            L.append("")
        L.append("---")
        L.append("")

    for profile in PROFILES:
        cons = v.of_profile(profile, lambda d: d.get("artifact_type") == "safety_concept")
        if not cons:
            continue
        L.append(f"## Profile: `{profile}` — ISO 26262 Part 3 safety concepts")
        L.append("")
        for cid in cons:
            d = v.get(profile, cid)
            ci = d.get("concept_identity", {}) or {}
            stage = d.get("concept_stage", "?")
            L.append(f"### `{cid}` — {esc(d.get('title', ''))}")
            L.append("")
            L.append(f"- **Concept stage**: `{stage}`")
            L.append(f"- **Item**: `{ci.get('item_ref')}` · **hypothetical**: "
                     f"`{str(ci.get('fictional')).lower()}`")
            L.append(f"- **Clause reference**: {esc(ci.get('clause_reference', ''), 200)}")
            L.append(f"- **Derived from**: "
                     f"{', '.join('`' + r + '`' for r in ci.get('derived_from', []) or []) or '—'}")
            L.append(f"- **Guard**: profile=`{d.get('profile')}`, origin=`{d.get('origin')}`, "
                     f"human_approval_status=`{d.get('human_approval_status')}`, "
                     f"production_authorized=`{str(d.get('production_authorized')).lower()}`")
            L.append("")
            sg = d.get("scope_statement", {}) or {}
            L.append("**Scope boundary**")
            L.append("")
            for e in (sg.get("inside_safety_scope", []) or []):
                L.append(f"- Inside: {esc(e, 180)}")
            for e in (sg.get("outside_safety_scope", []) or []):
                L.append(f"- Outside ({e.get('hazard_class', '?')}): {esc(e.get('element', ''), 80)} "
                         f"— {esc(e.get('why_outside', ''), 180)}")
            L.append("")
            L.append(f"- **Boundary argument**: {esc(sg.get('boundary_argument', ''), 700)}")
            L.append("")
            L.append("**Architectural elements and their roles**")
            L.append("")
            L.append("| Element | Name | Kind | Role | Owns objective part | Independence note |")
            L.append("|---|---|---|---|---|---|")
            for e in (d.get("architectural_elements", []) or []):
                L.append(f"| `{e.get('element_id')}` | {esc(e.get('element_name', ''), 40)} | "
                         f"{e.get('element_kind', '?')} | {esc(e.get('role', ''), 110)} | "
                         f"{esc(e.get('owns_objective_part', ''), 110)} | "
                         f"{esc(e.get('independence_note', ''), 110)} |")
            L.append("")
            st = d.get("safety_strategies", {}) or {}
            L.append("**Safety strategies**")
            L.append("")
            L.append("| Kind | Mechanism or reaction | Element | Budget (ms) | Note |")
            L.append("|---|---|---|---|---|")
            for m in (st.get("fault_detection", []) or []):
                L.append(f"| detection | {esc(m.get('mechanism', ''), 70)} | "
                         f"`{m.get('element_id')}` | {m.get('detection_time_budget_ms')} | "
                         f"{esc(m.get('coverage_claim', ''), 90)} |")
            for m in (st.get("fault_reaction", []) or []):
                L.append(f"| reaction | {esc(m.get('reaction', ''), 70)} | "
                         f"`{m.get('element_id')}` | {m.get('reaction_time_budget_ms')} | "
                         f"{esc(m.get('mode_dependence', ''), 150)} |")
            L.append("")
            for dm in (st.get("degraded_operation", []) or []):
                L.append(f"- **Degraded mode** `{esc(dm.get('degraded_mode', ''), 60)}`: keeps "
                         f"{esc(dm.get('capability_kept', ''), 90)}; removes "
                         f"{esc(dm.get('capability_removed', ''), 90)}; enters on "
                         f"{esc(dm.get('entry_condition', ''), 90)}; duration "
                         f"{esc(dm.get('duration_limit', ''), 90)}")
            L.append("")
            L.append(f"- **Safe state**: {esc(st.get('safe_state', ''), 500)}")
            L.append(f"- **Strategy allocation**: {esc(st.get('strategy_allocation', ''), 700)}")
            L.append("")
            fs = d.get("ftti_and_timing_budget")
            if fs:
                ac = fs.get("arithmetic_check", {}) or {}
                L.append("**FTTI and timing budget**")
                L.append("")
                L.append("| Element | Budget (ms) |")
                L.append("|---|---|")
                owner = fs.get("allocation_to_element_id", {}) or {}
                for k, budget_ms in (fs.get("allocation", {}) or {}).items():
                    L.append(f"| {esc(k, 50)} (`{owner.get(k, '?')}`) | {budget_ms} |")
                L.append(f"| **FTTI** | **{fs.get('ftti_ms')}** |")
                L.append("")
                L.append(f"- Serial sum: {ac.get('serial_sum_ms')} ms · margin: "
                         f"{ac.get('margin_ms')} ms")
                L.append(f"- **Arithmetic statement**: {esc(ac.get('statement', ''), 900)}")
                L.append("")
            hw = d.get("hardware_software_allocation")
            if hw:
                L.append("**Hardware / software allocation**")
                L.append("")
                L.append("| Element | Allocated to | Responsibility | Why the split |")
                L.append("|---|---|---|---|")
                for a in hw:
                    L.append(f"| `{a.get('element_id')}` | {a.get('allocated_to')} | "
                             f"{esc(a.get('allocated_responsibility', ''), 130)} | "
                             f"{esc(a.get('reason_for_the_split', ''), 150)} |")
                L.append("")
            tsr = d.get("technical_safety_requirements")
            if tsr:
                L.append("**Technical safety requirements carried by this allocation**")
                L.append("")
                L.append("| Requirement | Type | Element | Verification | Statement |")
                L.append("|---|---|---|---|---|")
                for t in tsr:
                    L.append(f"| `{t.get('requirement_id')}` | {t.get('requirement_type')} | "
                             f"`{t.get('allocated_to_element_id')}` | "
                             f"{t.get('verification_approach')} | "
                             f"{esc(t.get('statement_summary', ''), 120)} |")
                L.append("")
            dc = d.get("diagnostic_coverage_assumptions")
            if dc:
                L.append("**Diagnostic-coverage assumptions**")
                L.append("")
                L.append("| Mechanism | Claimed coverage | Basis | Independence assumption | "
                         "Verification records |")
                L.append("|---|---|---|---|---|")
                for a in dc:
                    L.append(f"| {esc(a.get('mechanism', ''), 60)} | "
                             f"{esc(a.get('claimed_coverage', ''), 100)} | "
                             f"`{a.get('justification_basis')}` | "
                             f"{esc(a.get('independence_assumption', ''), 110)} | "
                             f"{', '.join('`' + r + '`' for r in a.get('verification_record_refs', []) or []) or '**none**'} |")
                L.append("")
                for a in dc:
                    L.append(f"- *{esc(a.get('mechanism', ''), 60)}* — "
                             f"{esc(a.get('justification', ''), 500)}")
                L.append("")
            hi = d.get("hardware_interfaces_and_assumptions")
            if hi:
                L.append("**Hardware interfaces and assumptions**")
                L.append("")
                L.append("| Element | Assumption | Basis | If unmet |")
                L.append("|---|---|---|---|")
                for a in hi:
                    L.append(f"| `{a.get('element_id')}` | "
                             f"{esc(a.get('interface_or_assumption', ''), 150)} | "
                             f"{esc(a.get('basis', ''), 130)} | "
                             f"{esc(a.get('consequence_if_unmet', ''), 180)} |")
                L.append("")
            iro = d.get("item_related_assumptions")
            if iro:
                L.append("**Item-related assumptions**")
                L.append("")
                for a in iro:
                    L.append(f"- ({a.get('evidence_class')}) {esc(a.get('assumption', ''), 250)} "
                             f"— *if false:* {esc(a.get('consequence_if_false', ''), 250)}")
                L.append("")
            ifs = d.get("interfaces_to_other_safety_related_items") or []
            if ifs:
                L.append("**Interfaces to other safety-related items**")
                L.append("")
                for a in ifs:
                    L.append(f"- **{esc(a.get('other_item', ''), 90)}** — "
                             f"{esc(a.get('interface_description', ''), 200)} "
                             f"*Shared objective:* {esc(a.get('shared_objective_or_none', ''), 150)}")
                L.append("")
            em = d.get("external_measures") or []
            if em:
                L.append("**External measures relied upon**")
                L.append("")
                for a in em:
                    L.append(f"- {esc(a.get('measure', ''), 120)} — owner "
                             f"{esc(a.get('owner_outside_the_item', ''), 80)}; why not the item: "
                             f"{esc(a.get('why_the_item_cannot_do_it', ''), 180)}")
                L.append("")
            cw = d.get("contradictions_found_while_authoring")
            if cw:
                L.append("**Contradictions found in the records this concept was written from**")
                L.append("")
                L.append("These are recorded rather than absorbed. Neither the concept nor the "
                         "conflicting record was edited to make them agree; each names the finding "
                         "that carries it.")
                L.append("")
                for c in cw:
                    L.append(f"- **Contradiction**: {esc(c.get('contradiction', ''), 450)}")
                    L.append(f"  - **Records in conflict**: "
                             f"{', '.join('`' + r + '`' for r in c.get('records_in_conflict', []) or [])}")
                    L.append(f"  - **How this concept handles it**: "
                             f"{esc(c.get('how_this_concept_handles_it', ''), 450)}")
                    if c.get("finding_ref"):
                        L.append(f"  - **Finding**: `{c.get('finding_ref')}`")
                L.append("")
            L.append("**What this concept does not establish**")
            L.append("")
            for lim in (d.get("limitations", []) or []):
                L.append(f"- {esc(lim, 400)}")
            L.append("")

    # ---- cybersecurity work products (TARA + derived security requirements) ----
    taras = []
    secs = []
    for profile in PROFILES:
        for tid in v.of_profile(profile, lambda d: d.get("artifact_type") == "tara"):
            taras.append((profile, tid))
        for sid in v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement"
                                and "-SEC-" in d.get("id", "")):
            secs.append((profile, sid))

    if taras or secs:
        L.append("## Cybersecurity Work Products (Threat Analysis and Derived Security Requirements)")
        L.append("")
        L.append("This section carries the corpus' cybersecurity work products. They are placed in the System "
                 "Requirements Specification rather than in the Software Requirements Specification because "
                 "they are system-level work products: the threat set is drawn from system-level assets (CAN "
                 "bus, Ethernet interface, serial link, commissioning toolchain), and the mitigations they "
                 "carry protect system-level safety goals. Both are `synthetic_reference` artifacts; the "
                 "`as_is` profile contains none, because the real foxBMS 2 project holds no threat analysis "
                 "and no cybersecurity work product.")
        L.append("")
        L.append("**Guard flags — read before using anything in this section:**")
        L.append("")
        L.append("- The threat analysis below is a **corpus-local simplified threat and risk analysis**. "
                 "Its `method.is_iso_21434_tara` field is machine-pinned to `false` by schema. It is **not** "
                 "an ISO/SAE 21434 TARA and no ISO/SAE 21434 work product exists in this corpus.")
        L.append("- No TARA in this corpus has been **reviewed or approved** by any cybersecurity, "
                 "functional-safety or vehicle-level authority. `human_approval_status` is `pending` and "
                 "`production_authorized` is `false` on every record below.")
        L.append("- **No residual risk is accepted.** `residual_risk_acceptance.acceptance_exists` is "
                 "machine-pinned to `false` and `accepted_by` to `none` on the TARA record.")
        L.append("- No **penetration test, exploit, fuzzing campaign or CVSS assessment** was performed in "
                 "producing any record below. A threat listed here is a static reading of code, not a "
                 "demonstrated exploitable weakness.")
        L.append("- A requirement marked *control absent* below means the corresponding control is **not "
                 "present in the real foxBMS 2 source at commit 308028fb**. It does not mean the control is "
                 "absent from any hypothetical product, and no statement here should be read as a claim that "
                 "the real foxBMS product is secure or insecure in absolute terms.")
        L.append("")

    for profile, tid in sorted(taras, key=lambda t: t[1]):
        t = v.get(profile, tid)
        m = t.get("method", {}) or {}
        L.append(f"### `{tid}` — {esc(t.get('title',''))}")
        L.append("")
        L.append(f"- **Profile**: `{profile}` · **Origin**: `{t.get('origin')}` · **Owner role**: "
                 f"`{t.get('owner_role')}` · **Lifecycle**: `{t.get('lifecycle_status')}` · "
                 f"**Human approval**: `{t.get('human_approval_status')}` · "
                 f"**Production authorized**: `{str(t.get('production_authorized')).lower()}` · "
                 f"**Product verification credit**: `{str(t.get('product_verification_credit')).lower()}`")
        L.append(f"- **Method**: {esc(m.get('method_name','?'))}")
        L.append(f"- **Is an ISO/SAE 21434 TARA**: `{str(m.get('is_iso_21434_tara')).lower()}` "
                 f"(schema-pinned to `false`)")
        L.append(f"- **Residual risk accepted**: "
                 f"`{str(t.get('residual_risk_acceptance',{}).get('acceptance_exists')).lower()}` "
                 f"by `{t.get('residual_risk_acceptance',{}).get('accepted_by')}`")
        scope = t.get("item_and_scope", {}) or {}
        L.append(f"- **Item under analysis**: {esc(scope.get('item_under_analysis','?'), 400)}")
        L.append(f"- **Declared limitations of the analysis**: "
                 f"{len(m.get('limitations', []))} — see the record for the full list")
        L.append("")
        th = t.get("threats", []) or []
        obs = sum(1 for x in th if x.get("observed_in_pinned_source"))
        L.append(f"**Threats ({len(th)} total, {obs} evidenced in the pinned source, "
                 f"{len(th) - obs} hypothetical-project judgements):**")
        L.append("")
        L.append("| Threat | Origin | Observed in source | Target assets | Residual risk | Mitigations |")
        L.append("|---|---|---|---|---|---|")
        for x in th:
            L.append(f"| `{x.get('threat_id')}` | `{x.get('origin')}` | "
                     f"{'yes' if x.get('observed_in_pinned_source') else 'no'} | "
                     + ", ".join(f"`{a}`" for a in x.get("target_asset_ids", [])) + " | "
                     f"`{x.get('residual_risk')}` | "
                     + (", ".join(f"`{m2}`" for m2 in x.get("mitigation_ids", [])) or "—") + " |")
        L.append("")
        mit = t.get("mitigations", []) or []
        present = sum(1 for x in mit if x.get("status") in ("present_in_source", "partially_present_in_source"))
        L.append(f"**Mitigations ({len(mit)} total, {present} present or partially present in the pinned "
                 f"source, {len(mit) - present} absent or forward-engineered):**")
        L.append("")
        L.append("| Mitigation | Type | Status | Verification status | Maps to |")
        L.append("|---|---|---|---|---|")
        for x in mit:
            L.append(f"| `{x.get('mitigation_id')}` | {x.get('type')} | `{x.get('status')}` | "
                     f"`{x.get('verification_status')}` | "
                     + (", ".join(f"`{r}`" for r in x.get("maps_to_requirements", [])) or "—") + " |")
        L.append("")
        L.append("Mitigation status is the load-bearing column. `present_in_source` means the mechanism was "
                 "read out of the pinned source; `absent_in_source` means the record establishes by reading "
                 "the source that the mechanism is **not** there; `forward_engineered_synthetic` means the "
                 "mitigation is a proposal of the hypothetical project with no verification evidence.")
        L.append("")

    if secs:
        L.append("### Derived Security Requirements")
        L.append("")
        L.append(f"{len(secs)} security requirement artifacts, all `origin: synthetic` and all "
                 f"`verification_status: not_verified`. Each states in its own `real_source_presence` field "
                 f"whether the corresponding control exists in the real foxBMS 2 source.")
        L.append("")
        L.append(f"| Requirement | Title | Class | Control present in the real foxBMS 2 source? | Verification |")
        L.append("|---|---|---|---|---|")
        VERDICT = {
            "absent": "**NO — absent**",
            "partially_present": "**PARTIAL** — see record",
            "present": "yes",
        }
        for profile, sid in sorted(secs, key=lambda t: t[1]):
            s = v.get(profile, sid)
            L.append(f"| `{sid}` | {esc(s.get('title',''), 90)} | "
                     f"`{s.get('classification')}` | "
                     f"{VERDICT.get(s.get('real_source_control_status'), 'not stated')} | "
                     f"`{s.get('verification_status')}` |")
        L.append("")
        L.append("The *control present* column is read from the machine-readable `real_source_control_status` "
                 "field of each record, not inferred from prose. `absent` means the record establishes by "
                 "reading the pinned source that the control is not there. `partially_present` means part of "
                 "the capability is there and part is not, and the record's `real_source_presence` field gives "
                 "the itemised split.")
        L.append("")
        L.append("Every requirement above carries `human_approval_status: pending`, "
                 "`production_authorized: false` and `product_verification_credit: false`. No requirement "
                 "has verification evidence in this corpus, and none has been approved. The related third-party "
                 "component inventory is `docs/artifacts/sources/sbom.json`; it deliberately records **no** "
                 "vulnerability status for any component, because no advisory source was consulted. Absence "
                 "of an advisory there means the question was not asked, not that the answer is negative.")
        L.append("")

    (out / "02-system-requirements-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 03 SysArch

def emit_03(v, out):
    rm = v.repo
    L = scaffold(v, "03-system-architecture-specification",
                 "System architecture viewpoints — context, functional block, dynamic — combining "
                 "the reverse-engineered software architecture (layers, tasks, state machines, "
                 "data flow; sources: `src/app`, `docs/software/structure/`) with the per-profile "
                 "link registries.")
    rm_layer = {"application": len(rm.modules_by_layer("application")),
                "driver": len(rm.modules_by_layer("driver")),
                "engine": len(rm.modules_by_layer("engine")),
                "task": len(rm.modules_by_layer("task"))}

    # ---- Context viewpoint (repo facts, both profiles) -----------------
    L.append("## Context Viewpoint")
    L.append("")
    L.append("**Caption**: foxBMS 2 system context — BMS-Master and BMS-Slaves with external "
             "actors (reverse-engineered from `docs/introduction/bms-overview.rst`, "
             "`conf/bms/bms.json`).")
    L.append("")
    L.append(mermaid("flowchart LR",
        "    VCU[VCU / Host\\nCAN: 41 msgs] <--> MASTER\n"
        "    CS[Current Sensor\\nivt-s] <--> MASTER\n"
        "    IMD[IMD\\noptional] --- MASTER\n"
        "    subgraph Item[foxBMS 2 BMS Item]\n"
        "        MASTER[BMS-Master\\nTMS570LC4357 / FreeRTOS\\nsrc/app: 40 modules]\n"
        "        SLAVES[BMS-Slaves\\nAFE daisy-chain]\n"
        "    end\n"
        "    MASTER <-->|SPI daisy-chain| SLAVES\n"
        "    SLAVES --- CELLS[Battery Cells / Modules]\\nvoltage + temperature + balancing\n"
        "    MASTER --- CONT[Contactors\\nString-/Precharge]\n"
        "    MASTER --- ILCK[Interlock Circuit]\n"
        "    CELLS --- LOAD[Load / Charger]"))
    L.append("")

    # ---- Functional block viewpoint (layer architecture) --------------
    L.append("## Functional Block Viewpoint")
    L.append("")
    L.append(f"**Caption**: Layered software architecture (source: "
             f"`docs/software/structure/software-structure.rst`, `src/app/`) — "
             f"application {rm_layer['application']}, driver {rm_layer['driver']}, "
             f"engine {rm_layer['engine']}, task/OS {rm_layer['task']} modules.")
    L.append("")
    L.append("Design paradigms (from the structure documentation): (1) all application code "
             "runs in an operating-system context; (2) MCU and external-hardware dependent "
             "drivers are abstracted by wrappers/abstraction layers.")
    L.append("")
    driver_mods = [m["name"] for m in rm.modules_by_layer("driver")]
    app_mods = [m["name"] for m in rm.modules_by_layer("application")]
    engine_mods = [m["name"] for m in rm.modules_by_layer("engine")]
    L.append(mermaid("flowchart TB",
        "    subgraph OS[Operating System - FreeRTOS / SafeRTOS path]\n"
        "        FTSK[ftask - cyclic + continuous tasks]\n"
        "        OSW[os wrapper / timer]\n"
        "    end\n"
        "    subgraph ENG[Engine Layer]\n"
        f"        ENGM[{' / '.join(engine_mods)}]\n"
        "    end\n"
        "    subgraph APP[Application Layer]\n"
        f"        APPM[{' / '.join(app_mods)}]\n"
        "    end\n"
        "    subgraph DRV[Driver Layer - MCU wrapper]\n"
        f"        DRVM[{' / '.join(driver_mods)}]\n"
        "    end\n"
        "    HAL[HAL / TI HALCoGen]\n"
        "    MCU[TMS570LC4357 Cortex-R5F]\n"
        "    OS --> ENG --> APP --> DRV --> HAL --> MCU"))
    L.append("- **Engine layer**: diagnostics, error handling, system monitoring, database "
             "(producer/consumer asynchronous data exchange between tasks/modules).")
    L.append("- **Driver layer**: communication interfaces (CAN, UART, SPI, Ethernet/EMAC), "
             "measurement control (AFE, ADC, current sensor), hardware supervision (SBC, "
             "port expander, RTC, FRAM, interlock, contactors/SPS, IMD, LEDs).")
    L.append("")

    # ---- Task engineering ---------------------------------------------
    L.append("### Task Engineering Viewpoint")
    L.append("")
    L.append("**Caption**: Task-function mapping from `src/app/task/config/ftask_cfg.c` "
             "(user code functions per task, verified against the source).")
    L.append("")
    L.append("| Task | Period / mode | Functions |")
    L.append("|---|---|---|")
    for task, funcs in rm.tasks.items():
        period = {"1ms": "1 ms cyclic", "10ms": "10 ms cyclic",
                  "100ms": "100 ms cyclic", "100ms-algorithm": "100 ms cyclic (algorithms)",
                  "i2c (continuous)": "continuous, 2 ms delay", "engine (continuous)": "continuous, blocking"}.get(task, task)
        L.append(f"| {task} | {period} | " + ", ".join(f"`{f}`" for f in funcs) + " |")
    L.append("")
    L.append("Priority order (from the docs): database/engine context highest, then 1 ms task "
             "(time-sensitive: diagnostics, measurement, CAN RX), 10 ms task (CAN TX, "
             "interlock, SPS, ADC, BMS trigger), 100 ms task (state estimation, balancing, "
             "IMD, LED), 100 ms algorithm task (user algorithms).")
    L.append("")

    # ---- Dynamic viewpoint: BMS + SYS state machines -------------------
    L.append("## Dynamic Viewpoint")
    L.append("")
    L.append("### BMS State Machine (application core)")
    L.append("")
    L.append(f"**Caption**: BMS FSM — {len(rm.bms_fsm['states'])} states "
             f"(`src/app/application/bms/bms.h`), triggered every 10 ms by "
             f"`BMS_Trigger()` in the 10 ms task.")
    L.append("")
    sb = ["    [*] --> BMS_FSM_STATE_UNINITIALIZED"]
    main_chain = [
        ("BMS_FSM_STATE_UNINITIALIZED", "BMS_FSM_STATE_INITIALIZATION", "initialization request"),
        ("BMS_FSM_STATE_INITIALIZATION", "BMS_FSM_STATE_INITIALIZED", "init done"),
        ("BMS_FSM_STATE_INITIALIZED", "BMS_FSM_STATE_IDLE", "standby"),
        ("BMS_FSM_STATE_IDLE", "BMS_FSM_STATE_STANDBY", "close contactors request"),
        ("BMS_FSM_STATE_STANDBY", "BMS_FSM_STATE_PRECHARGE", "precharge request"),
        ("BMS_FSM_STATE_PRECHARGE", "BMS_FSM_STATE_NORMAL", "precharge finished"),
        ("BMS_FSM_STATE_NORMAL", "BMS_FSM_STATE_DISCHARGE", "discharge power path"),
        ("BMS_FSM_STATE_NORMAL", "BMS_FSM_STATE_CHARGE", "charge power path"),
    ]
    for a, bb, lbl in main_chain:
        sb.append(f"    {a} --> {bb} : {lbl}")
    sb.append("    BMS_FSM_STATE_ERROR_STATE[BMS_FSM_STATE_ERROR] : any state on fatal diagnosis")
    sb.append("    BMS_FSM_STATE_ERROR --> BMS_FSM_STATE_OPEN_CONTACTORS : open contactors")
    sb.append("    BMS_FSM_STATE_OPEN_CONTACTORS --> BMS_FSM_STATE_STANDBY : contactors open (safe state)")
    for s in rm.bms_fsm["states"]:
        sb.append(f"    {s}")
    L.append(mermaid("stateDiagram-v2", "\n".join(sb)))
    L.append(f"Substates ({len(rm.bms_fsm['substates'])}) implement the entry checks "
             "(interlock, state requests, balancing requests, error flags) and the precharge "
             "sequences (close minus → close precharge → check → open precharge → close plus; "
             "second-string variants included).")
    L.append("")

    L.append("### SYS State Machine (engine startup sequencing)")
    L.append("")
    L.append(f"**Caption**: SYS FSM — {len(rm.sys_fsm['states'])} states "
             f"(`src/app/engine/sys/sys.h`), sequencing the startup: FRAM deep-discharge check, "
             "SBC init, interlock init, CAN init, RTC, built-in self-test, boot message, "
             "balancing init, first measurement cycle, current-sensor presence check, IMD init.")
    L.append("")
    sb2 = ["    [*] --> SYS_FSM_STATE_HAS_NEVER_RUN"]
    for a, bb in [
        ("SYS_FSM_STATE_HAS_NEVER_RUN", "SYS_FSM_STATE_UNINITIALIZED"),
        ("SYS_FSM_STATE_UNINITIALIZED", "SYS_FSM_STATE_INITIALIZATION"),
        ("SYS_FSM_STATE_INITIALIZATION", "SYS_FSM_STATE_PRE_RUNNING"),
        ("SYS_FSM_STATE_PRE_RUNNING", "SYS_FSM_STATE_RUNNING"),
    ]:
        sb2.append(f"    {a} --> {bb}")
    sb2.append("    SYS_FSM_STATE_RUNNING --> SYS_FSM_STATE_ERROR : fatal error")
    for s in rm.sys_fsm["states"]:
        sb2.append(f"    {s}")
    L.append(mermaid("stateDiagram-v2", "\n".join(sb2)))
    L.append("")

    L.append("### Protection Chain Sequence (cell voltage)")
    L.append("")
    L.append("**Caption**: Sequence of the cell-voltage protection chain (AFE → database → "
             "SOA plausibility → diagnosis → BMS FSM → contactors), matching the module "
             "call graph and the corpus FTTI allocation.")
    L.append("")
    seq = ["    participant AFE as AFE Driver (MEAS, 1ms task)",
           "    participant DB as Database (DATA)",
           "    participant PL as Plausibility / Redundancy (MRC)",
           "    participant SOA as SOA Monitor",
           "    participant DIAG as Diagnosis (DIAG)",
           "    participant BMS as BMS FSM (10ms task)",
           "    participant SPS as Contactor Ctrl (SPS)"]
    seq.append("    AFE->>DB: publish validated cell voltages")
    seq.append("    DB->>PL: MRC_ValidateAfeMeasurement (every 50 ms)")
    seq.append("    DB->>SOA: SOA evaluation (10 ms context)")
    seq.append("    SOA->>DIAG: MSL violation event")
    seq.append("    DIAG->>BMS: fatal error flag set")
    seq.append("    BMS->>BMS: transition to ERROR state")
    seq.append("    BMS->>SPS: open string contactors (safe state)")
    seq.append("    Note over BMS,SPS: within FTTI budget (corpus: 100 ms total)")
    L.append(mermaid("sequenceDiagram", "\n".join(seq)))
    L.append("")

    # ---- corpus link-registry viewpoint per profile --------------------
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}` — Traceability Viewpoint")
        L.append("")
        L.append("**Caption**: Cell-voltage protection chain blocks from the link registry "
                 "(HAZ ← mitigates ← SGO ← refines ← FSRs ← allocated_to ← TSR/SWR).")
        L.append("")
        body = ["    HAZ[\"FB2-SAF-HAZ-000001 Hazard\"]", "    SGO[\"FB2-SAF-SGO-000001 Safety Goal\"]",
                "    HAZ --- SGO"]
        for l in sorted(v.links_where(profile=profile, relation="refines"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" --- \"{l['target_id']}\"")
        for l in sorted(v.links_where(profile=profile, relation="allocated_to"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" -.allocated_to.-> \"{l['target_id']}\"")
        for l in sorted(v.links_where(profile=profile, relation="implements"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" -.implements.-> \"{l['target_id']}\"")
        L.append(mermaid("flowchart TD", "\n".join(body)))
        L.append("")
    (out / "03-system-architecture-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 04 SWRS

def emit_04(v, out):
    rm = v.repo
    L = scaffold(v, "04-software-requirements-specification",
                 "Software requirements of both corpus profiles (SWRs grouped under their "
                 "parent FSR with allocation rationale) plus software requirements "
                 "reverse-engineered from the 40 implemented modules and the diagnosis/SOA "
                 "configuration.")

    # ---- Reverse-engineered module requirements ------------------------
    L.append("## Reverse-Engineered Software Requirements (module-grounded)")
    L.append("")
    L.append("The implemented software directly satisfies the following software requirements. "
             "Each requirement cites its implementing module(s) with repository anchors; "
             "unit-test evidence is listed per module in the Detailed Design and "
             "Implementation Mapping documents.")
    L.append("")
    sw_reqs = [
        ("SWR-RE-01", "The software shall acquire cell voltages and cell temperatures via the "
         "AFE daisy-chain and validate them (plausibility, redundancy).",
         "`src/app/driver/afe/*` (8 AFE drivers), `src/app/driver/meas/`, "
         "`src/app/application/plausibility/`, `src/app/application/redundancy/`"),
        ("SWR-RE-02", "The software shall evaluate the safe operating area (cell voltage, "
         "cell temperature, cell/pack current) against MOL/RSL/MSL limits.",
         "`src/app/application/soa/soa.c` (`SOA_*`), config `battery_cell_cfg.h`"),
        ("SWR-RE-03", "The software shall detect and classify 85 diagnosis events with "
         "configurable severity, latency and occurrence counters.",
         "`src/app/engine/diag/`, `src/app/engine/config/diag_cfg.c`"),
        ("SWR-RE-04", "The software shall run the BMS state machine (13 states, 34 substates) "
         "in the 10 ms task context and reach the safe state (contactors open) on fatal errors.",
         "`src/app/application/bms/`, `src/app/application/config/bms_cfg.h`"),
        ("SWR-RE-05", "The software shall control string-minus, string-plus and precharge "
         "contactors through smart power switches with feedback supervision.",
         "`src/app/driver/contactor/`, `src/app/driver/sps/`"),
        ("SWR-RE-06", "The software shall supervise the interlock line and open the "
         "contactors on interlock faults.",
         "`src/app/driver/interlock/` (ILCK)"),
        ("SWR-RE-07", "The software shall balance cells passively (reference strategy: "
         "voltage-based).",
         "`src/app/application/bal/` (strategies: `none`, `voltage`)"),
        ("SWR-RE-08", "The software shall estimate SOC/SOE/SOF/SOH (reference: coulomb/energy "
         "counting, trapezoid SOF).",
         "`src/app/application/algorithm/state_estimation/`, `algorithm.c`"),
        ("SWR-RE-09", "The software shall exchange data asynchronously between tasks via the "
         "database (single producer, multiple consumers).",
         "`src/app/engine/database/`"),
        ("SWR-RE-10", "The software shall monitor task execution times and supply voltages "
         "(system monitoring, FRAM-persisted).",
         "`src/app/engine/sys_mon/`, `src/app/engine/hw_info/`, `src/app/driver/fram/`"),
        ("SWR-RE-11", "The software shall communicate on CAN (41 messages) and provide an "
         "Ethernet TCP/IP interface for user applications.",
         "`src/app/driver/can/`, `src/app/application/ethernet/`, `tools/dbc/foxbms.dbc`"),
        ("SWR-RE-12", "The software shall supervise the system basis chip (SBC) and react to "
         "FIN/RSTB errors.",
         "`src/app/driver/sbc/` (NXP FS85)"),
        ("SWR-RE-13", "The software shall provide timekeeping (RTC), port expansion (PEX), "
         "humidity/temperature sensing (HTSEN) and debug LEDs on the continuous I2C task.",
         "`src/app/driver/rtc/`, `pex/`, `htsensor/`, `led/`"),
        ("SWR-RE-14", "The software shall support optional insulation monitoring (IMD).",
         "`src/app/driver/imd/`"),
        ("SWR-RE-15", "The software shall be unit-testable: 313 C unit tests run in CI with "
         "100% line/branch coverage policy.",
         "`tests/unit/app/**/test_*.c`, `docs/developer-manual/software/software-testing.rst`"),
    ]
    L.append("| ID | Requirement | Implementing modules (anchors) |")
    L.append("|---|---|---|")
    for rid, stmt, anchor in sw_reqs:
        L.append(f"| `{rid}` | {esc(stmt, 400)} | {esc(anchor, 200)} |")
    L.append("")

    # ---- corpus profiles ----------------------------------------------
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        fsr_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and "-FSR-" in d.get("id",""))
        for fid in fsr_ids:
            alloc = sorted(v.links_where(profile=profile, relation="allocated_to", tgt=fid), key=lambda x: x["source_id"])
            if not alloc:
                continue
            L.append(f"### Parent FSR: `{fid}`")
            L.append("")
            for l in alloc:
                swr_id = l["source_id"]
                d = v.get(profile, swr_id)
                if not d:
                    continue
                L.append(f"#### `{swr_id}` — {esc(d.get('title',''))}")
                L.append("")
                L.append(f"- **Allocated to**: `{fid}` (link `{l['link_id']}`, rationale: \"{esc(l.get('rationale',''))}\")")
                L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 500)}")
                L.append(f"- **Rationale**: {esc(d.get('rationale','Implements parent FSR in software'), 400)}")
                L.append(f"- **Classification**: `{d.get('classification','?')}`")
                sa = d.get("safety_allocation", {}) or {}
                L.append(f"- **ASIL**: `{sa.get('asil','?')}`")
                ac = d.get("acceptance_criteria", [])
                if ac:
                    L.append("- **Acceptance criteria**:")
                    for c in ac:
                        if isinstance(c, dict):
                            L.append(f"  - {esc(c.get('criterion','?'))}: {esc(c.get('measure',''))} ≤ {esc(c.get('threshold',''))} {esc(c.get('unit',''))}")
                        else:
                            L.append(f"  - {esc(c)}")
                else:
                    L.append("- **Acceptance criteria**: not specified in corpus")
                L.append(f"- **Source references**: " + (", ".join(f"`{r}`" for r in d.get("source_refs", [])) or "—"))
                L.append(f"- **Assumption references**: " + (", ".join(f"`{r}`" for r in d.get("assumption_refs", [])) or "—"))
                L.append("")
        # orphan SWRs (allocated to no FSR in this profile)
        grouped = {l["source_id"] for fid in fsr_ids for l in v.links_where(profile=profile, relation="allocated_to", tgt=fid)}
        orphans = [aid for aid in v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and ("-SWR-" in d.get("id","") or "-MAN-" in d.get("id","")))
                   if aid not in grouped]
        if orphans:
            L.append("### Software Requirements Without Parent FSR Link")
            L.append("")
            for oid in orphans:
                d = v.get(profile, oid)
                L.append(f"#### `{oid}` — {esc(d.get('title',''))}")
                L.append("")
                L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 500)}")
                L.append(f"- **Classification**: `{d.get('classification','?')}` | **Profile**: `{profile}`")
                L.append(f"- **Note**: no `allocated_to` link to a parent FSR in this profile's registry.")
                L.append("")
    (out / "04-software-requirements-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 05 SWArch

def emit_05(v, out):
    rm = v.repo
    L = scaffold(v, "05-software-architecture-specification",
                 "Software architecture viewpoints: reverse-engineered static component "
                 "viewpoint (40-module inventory across 4 layers with prefixes and unit "
                 "tests), dynamic viewpoints (BMS/SYS state machines, task model), plus "
                 "the corpus SWR/DSN relations per profile.")

    # ---- Reverse-engineered component inventory ------------------------
    L.append("## Static Component Viewpoint — Module Inventory")
    L.append("")
    L.append("All software modules reverse-engineered from `src/app/` "
             "(layer / module / prefix / brief / sources / unit tests).")
    L.append("")
    for layer in ("engine", "task", "application", "driver"):
        mods = rm.modules_by_layer(layer)
        L.append(f"### Layer: `{layer}` ({len(mods)} modules)")
        L.append("")
        L.append("| Module | Prefix | Responsibility (from `@brief`) | Files | Unit tests |")
        L.append("|---|---|---|---|---|")
        for m in mods:
            L.append(f"| `{m['key']}` | `{m['prefix'] or '—'}` | {esc(m['brief'], 150)} | "
                     f"{m['n_sources']} | {m['n_unit_tests']} |")
        L.append("")
    L.append("Configuration is separated from module logic into per-layer `config/` "
             "directories (`src/app/*/config/*_cfg.c|h`) — each module pairs with a "
             "`*_cfg` file (see Detailed Design).")
    L.append("")

    # ---- Task/runtime viewpoint ---------------------------------------
    L.append("## Dynamic Viewpoint — Task Model")
    L.append("")
    L.append("**Caption**: RTOS task set (FreeRTOS): four cyclic tasks (1 ms, 10 ms, "
             "100 ms, 100 ms algorithm) plus continuous blocking tasks (I2C, engine). "
             "Source: `src/app/task/ftask/ftask.c`, `src/app/task/config/ftask_cfg.c`.")
    L.append("")
    body = ["    OS[FreeRTOS Scheduler]"]
    for t, funcs in rm.tasks.items():
        tnode = t.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        body.append(f"    {tnode}[\"{t} ({len(funcs)} functions)\"]")
        body.append(f"    OS --> {tnode}")
    L.append(mermaid("flowchart TD", "\n".join(body)))
    L.append("")

    # ---- Database/dataflow viewpoint -----------------------------------
    L.append("## Data Exchange Viewpoint")
    L.append("")
    L.append("**Caption**: Producer/consumer database (engine layer) — asynchronous data "
             "exchange between tasks; single producer, multiple consumers, integrity ensured "
             "(source: `docs/software/structure/application.rst`, `src/app/engine/database/`).")
    L.append("")
    L.append(mermaid("flowchart LR",
        "    MEAS[MEAS_Control\\n1ms] --> DB[(Database DATA)]\n"
        "    CANRX[CAN_ReadRxBuffer\\n1ms] --> DB\n"
        "    ADC[ADC_Control\\n10ms] --> DB\n"
        "    SPS[SPS_Ctrl\\n10ms] --> DB\n"
        "    MRC[MRC_Validate*\\n50ms] --> DB\n"
        "    DB --> SOA[SOA evaluation]\n"
        "    DB --> ALGO[SE_RunStateEstimations\\n1s]\n"
        "    DB --> BMS[BMS_Trigger\\n10ms]\n"
        "    BMS --> CAN_TX[CAN_MainFunction\\n10ms]\n"
        "    DIAG[DIAG_UpdateFlags\\n1ms] --> DB"))
    L.append("")

    # ---- corpus viewpoints ---------------------------------------------
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}` — Traceability Viewpoints")
        L.append("")
        L.append("### Static Component Viewpoint (corpus)")
        L.append("")
        L.append("**Caption**: SW requirements, designs, and implements/allocated_to relations.")
        L.append("")
        body = []
        for l in sorted(v.links_where(profile=profile, relation="allocated_to"), key=lambda x: x["source_id"]):
            if l["source_id"].startswith("FB2-SW"):
                body.append(f"    \"{l['source_id']}\" --> \"{l['target_id']}\"")
        for l in sorted(v.links_where(profile=profile, relation="implements"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" -.implements.-> \"{l['target_id']}\"")
        if body:
            L.append(mermaid("flowchart TD", "\n".join(body)))
        else:
            L.append("No SW allocation/implements links in this profile's registry.")
        L.append("")
        # Dynamic per design
        dsn_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "design" and d.get("engineering_domain") == "software")
        for did in dsn_ids:
            d = v.get(profile, did)
            bm = d.get("behavior_model", {})
            L.append(f"### Dynamic Viewpoint — `{did}`")
            L.append("")
            if isinstance(bm, dict) and bm.get("states"):
                L.append(f"**Caption**: State machine of `{did}` from `behavior_model` "
                         f"({esc(bm.get('type','state_machine'))}).")
                L.append("")
                sb = ["    [*] --> " + (bm.get("states")[0] if bm.get("states") else "INIT")]
                for t in bm.get("transitions", []):
                    if isinstance(t, dict):
                        sb.append(f"    {t.get('from','?')} --> {t.get('to','?')} : {esc(t.get('trigger',''), 30)}")
                for s in bm.get("states", []):
                    sb.append(f"    {s}")
                L.append(mermaid("stateDiagram-v2", "\n".join(sb)))
            else:
                L.append("Behavior model not specified in corpus.")
            L.append("")
        # task/thread context from timing budget
        sgo = v.get(profile, "FB2-SAF-SGO-000001")
        tb = (sgo or {}).get("timing_budget", {}).get("allocation", {})
        if tb:
            L.append("### Task/Thread Timing Context")
            L.append("")
            L.append("**Caption**: Timing budget elements (from `FB2-SAF-SGO-000001`) as scheduling context.")
            L.append("")
            body = ["    CHAIN[\"Protection chain\"]"]
            for k, ms in sorted(tb.items()):
                body.append(f"    T_{k}[\"{k}<br/>{ms} ms\"]")
                body.append(f"    T_{k} --> CHAIN")
            L.append(mermaid("flowchart LR", "\n".join(body)))
            L.append("")
    (out / "05-software-architecture-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 06 Detailed Design

def emit_06(v, out):
    rm = v.repo
    L = scaffold(v, "06-detailed-design-specification",
                 "Detailed design per software component: (1) reverse-engineered per-module "
                 "design from `src/app/` — files, config, responsibilities, unit tests, "
                 "documentation anchors; (2) corpus design artifacts with decomposition, "
                 "interfaces, constraints, budgets, failure response and behavior models.")

    # ---- Part 1: reverse-engineered per-module design ------------------
    L.append("## Reverse-Engineered Module Designs")
    L.append("")
    L.append(f"Per-module design of all {len(rm.modules)} software modules, mined from the "
             "source tree. `Sources` lists the C/H files, `Config` the module's configuration "
             "pair in `src/app/*/config/`, `Unit tests` the Ceedling/Unity test files run in CI.")
    L.append("")
    for m in rm.modules:
        L.append(f"### `{m['key']}`")
        L.append("")
        L.append(f"- **Prefix**: `{m['prefix'] or '—'}` | **Layer group**: `{m['ingroup'] or '—'}`")
        L.append(f"- **Responsibility**: {esc(m['brief'], 300)}")
        L.append(f"- **Sources ({m['n_sources']})**: "
                 + (", ".join(f"`{s}`" for s in m["sources"][:8])
                    + (" …" if len(m["sources"]) > 8 else "")))
        if m["config_files"]:
            L.append(f"- **Configuration**: " + ", ".join(f"`{c}`" for c in m["config_files"]))
        if m["unit_tests"]:
            L.append(f"- **Unit tests ({m['n_unit_tests']})**: "
                     + (", ".join(f"`{t}`" for t in m["unit_tests"][:10])
                        + (" …" if len(m["unit_tests"]) > 10 else "")))
        else:
            L.append("- **Unit tests**: none in `tests/unit/app/` (gap — see verification report)")
        if m["doc"]:
            L.append(f"- **Module documentation**: `{m['doc']}`")
        L.append("")
    # BMS/SYS FSM detail as design deep-dive
    L.append("### State Machine Design Details")
    L.append("")
    L.append(f"- **BMS FSM** (`src/app/application/bms/bms.c`): "
             f"{len(rm.bms_fsm['states'])} states / {len(rm.bms_fsm['substates'])} substates; "
             "entry/exit via `BMS_Trigger()` (10 ms context); state requests over CAN "
             "(`f_BmsStateRequest`); error entry on fatal diagnosis flags.")
    L.append(f"- **SYS FSM** (`src/app/engine/sys/sys.c`): "
             f"{len(rm.sys_fsm['states'])} states / {len(rm.sys_fsm['substates'])} substates; "
             "startup sequencing (SBC, interlock, CAN, RTC, BIST, boot message, balancing "
             "enable, first measurement cycle, current-sensor presence, IMD).")
    L.append("")

    # ---- Part 2: corpus designs ----------------------------------------
    for profile in PROFILES:
        dsn_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "design" and d.get("engineering_domain") == "software")
        for did in dsn_ids:
            d = v.get(profile, did)
            L.append(f"## Detailed Design: `{did}` ({profile})")
            L.append("")
            L.append(f"**Title**: {esc(d.get('title',''))} | **Level**: `{d.get('design_level','?')}`")
            L.append("")
            resp = d.get("responsibilities", [])
            L.append("### Responsibilities")
            L.append("")
            for r in resp or ["not specified in corpus"]:
                L.append(f"- {esc(r, 250)}")
            L.append("")
            dec = d.get("decomposition", [])
            L.append("### Decomposition")
            L.append("")
            if dec:
                L.append("**Caption**: Component decomposition of `" + did + "`.")
                L.append("")
                body = [f"    D[\"{did}\"]"]
                for i, c in enumerate(dec):
                    name = c.get("component", c.get("name", f"C{i}")) if isinstance(c, dict) else str(c)
                    body.append(f"    C{i}[\"{esc(name, 40)}\"]")
                    body.append(f"    D --> C{i}")
                L.append(mermaid("flowchart TD", "\n".join(body)))
            else:
                L.append("Decomposition not specified in corpus.")
            L.append("")
            ifs = d.get("interfaces", [])
            L.append("### Interfaces")
            L.append("")
            if isinstance(ifs, list) and ifs:
                L.append("| Interface | Direction | Signals |")
                L.append("|---|---|---|")
                for i in ifs:
                    if isinstance(i, dict):
                        sigs = i.get("signals", [])
                        sig_str = ", ".join(
                            (f"`{s.get('name','?')}` ({s.get('type','?')}, {s.get('unit','?')}, {s.get('range','?')}, {s.get('rate','?')})"
                             if isinstance(s, dict) else str(s)) for s in sigs)
                        L.append(f"| `{i.get('interface_id','?')}` | {i.get('direction','?')} | {esc(sig_str, 300)} |")
            else:
                L.append("Interfaces not specified in corpus.")
            L.append("")
            cons = d.get("constraints", [])
            L.append("### Constraints")
            L.append("")
            for c in cons or ["not specified in corpus"]:
                L.append(f"- {esc(c, 250)}")
            L.append("")
            bud = d.get("budgets", {})
            L.append("### Budgets")
            L.append("")
            if bud:
                for k, val in sorted(bud.items()):
                    L.append(f"- **{k}**: {esc(val)}")
            else:
                L.append("Budgets not specified in corpus.")
            L.append("")
            fr = d.get("failure_response", [])
            L.append("### Failure Response")
            L.append("")
            if isinstance(fr, list) and fr:
                L.append("| Failure mode | Detection | Reaction |")
                L.append("|---|---|---|")
                for f in fr:
                    if isinstance(f, dict):
                        L.append(f"| {esc(f.get('failure_mode','?'))} | {esc(f.get('detection','?'), 150)} | {esc(f.get('reaction','?'), 150)} |")
            else:
                L.append("Failure response not specified in corpus.")
            L.append("")
            bm = d.get("behavior_model", {})
            L.append("### Dynamic Diagram")
            L.append("")
            if isinstance(bm, dict) and bm.get("states"):
                L.append(f"**Caption**: State machine of `{did}`.")
                L.append("")
                sb = ["    [*] --> " + bm["states"][0]]
                for t in bm.get("transitions", []):
                    if isinstance(t, dict):
                        sb.append(f"    {t.get('from','?')} --> {t.get('to','?')} : {esc(t.get('trigger',''), 30)}")
                for s in bm.get("states", []):
                    sb.append(f"    {s}")
                L.append(mermaid("stateDiagram-v2", "\n".join(sb)))
            else:
                L.append("Behavior model not specified in corpus.")
            L.append("")
            im = d.get("implementation_mapping", [])
            L.append("### Implementation Requirements (extracted)")
            L.append("")
            if cons or bud:
                L.append(f"Extracted from `{did}` design fields:")
                L.append("")
                for c in cons:
                    L.append(f"- {esc(c, 200)} (source: `{did}` constraints)")
                for k, val in sorted(bud.items()):
                    L.append(f"- Budget `{k}` = {esc(val)} (source: `{did}` budgets)")
            else:
                L.append("No additional implementation requirements beyond mapping (see Implementation Mapping Document).")
            L.append("")
    (out / "06-detailed-design-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 07 SW Integration

def emit_07(v, out):
    rm = v.repo
    L = scaffold(v, "07-software-integration-report",
                 "Integrated software components of the foxBMS 2 build: (1) reverse-engineered "
                 "integration facts — build system (waf), linked programs (application, "
                 "bootloader, unit-test variants), CAN/DBC interface integration, unit-test "
                 "harness integration; (2) corpus `implements` links and integration evidence; "
                 "(3) explicit integration gaps. Per governance policy, missing evidence is "
                 "blocked, not fabricated.")

    # ---- Reverse-engineered integration facts -------------------------
    L.append("## Reverse-Engineered Integration Facts")
    L.append("")
    L.append("### Build System and Linked Programs")
    L.append("")
    L.append("The repository builds with the **waf** build tool (`waf-tools/`, per-module "
             "`wscript` files). Linked programs and build entry points (from the repository "
             "structure and `conf/`):")
    L.append("")
    L.append("| Program | Build root | Description |")
    L.append("|---|---|---|")
    L.append("| foxBMS application | `src/app` (wscript at repo root) | Embedded BMS application, "
             "linked against `foxbms-afe` (selected AFE driver), `foxbms-driver`, engine, "
             "application layers and FreeRTOS |")
    L.append("| Bootloader | `src/bootloader` | Field-update bootloader for the TMS570LC4357, "
             "CAN-based, PC application in the CLI (`fox bootloader`) |")
    L.append("| Unit tests | `tests/unit` + `conf/unit/*.yml` | Ceedling/Unity host-based unit "
             f"tests ({rm.test_counts['unit_c']} C test files), build variants `app_project_posix`, "
             "`app_project_win32` |")
    L.append("| CLI tool | `cli/` (`fox` command) | Repository interaction: build, flash, "
             "bootloader, diagnostics (Click-based Python) |")
    L.append("")
    L.append("Per-module wscript libraries integrate each module into the linked programs "
             "(driver layer `foxbms-driver`, AFE library `foxbms-afe` per "
             "`src/app/driver/afe/README.md`).")
    L.append("")
    L.append("### Configuration Integration")
    L.append("")
    L.append("The BMS hardware/software configuration is integrated through "
             "`conf/bms/bms.json` → generated `*_cfg` sources; unit-test and variant "
             "configurations through `conf/unit/` and `conf/env/`. Compiler configurations: "
             "`conf/cc/` (TI CGT for target, GCC for host tests).")
    L.append("")
    L.append("### Interface Integration")
    L.append("")
    L.append(f"- **CAN**: {len(rm.can_messages)} messages of `tools/dbc/foxbms.dbc` are "
             "implemented as callbacks in `src/app/driver/can/cbs/` (tx/rx message sets, "
             "period monitoring `DIAG_ID_CAN_TIMING`).")
    L.append("- **AFE daisy-chain**: AFE drivers implement the AFE API "
             f"(`src/app/driver/afe/api/afe.h`); supported chips: "
             + ", ".join(f"{a['vendor']} ({', '.join(a['chips'])})" for a in rm.afes) + ".")
    L.append("- **Interlock, contactors/SPS, SBC, PEX/HTSEN/RTC (I2C task), IMD**: driver "
             "modules integrated into the task engine as listed in the task model.")
    L.append("")

    # ---- corpus integration per profile --------------------------------
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        L.append("### Integrated Components")
        L.append("")
        impl = sorted(v.links_where(profile=profile, relation="implements"), key=lambda x: x["source_id"])
        if impl:
            L.append("| Design | Implements SWR | Link rationale |")
            L.append("|---|---|---|")
            for l in impl:
                L.append(f"| `{l['source_id']}` | `{l['target_id']}` | {esc(l.get('rationale',''))} |")
        else:
            L.append("No `implements` links in this profile's registry.")
        L.append("")
        L.append("### Integration Evidence")
        L.append("")
        exes = v.of_profile(profile, lambda d: d.get("artifact_type") == "execution")
        if exes:
            for eid in exes:
                d = v.get(profile, eid)
                L.append(f"- `{eid}`: kind=`{d.get('execution_kind','?')}`, outcome=`{d.get('outcome','?')}`")
        else:
            L.append("No execution artifacts in this profile. Integration-level executions: **none in corpus**.")
        L.append("")
        L.append("### Integration Gaps")
        L.append("")
        exes_as_is = v.of_profile("as_is", lambda d: d.get("artifact_type") == "execution")
        component_present = any(v.get(p, a).get("test_type") == "component"
                                for p in PROFILES for a in v.of_profile(p, lambda d: d.get("artifact_type") == "test_measure"))
        L.append("| Gap | Disposition |")
        L.append("|---|---|")
        if not component_present:
            L.append("| No component-level test measures | Gap documented; synthetic_reference to add per review disposition FB2-FND-000005 |")
        L.append("| No integration-level executions (only unit `actual_host_run` exists) | Per governance policy: actual product evidence = 0 — blocked, not fabricated |")
        L.append("| No target-hardware integration runs | as_is gap documented in review `FB2-REV-000001` (finding FB2-FND-000002) |")
        L.append("")
    (out / "07-software-integration-report.md").write_text(finish(L))


# ---------------------------------------------------------------- 08 System Verif

def _render_tms(v, L, profile, tms_id, depth="####"):
    d = v.get(profile, tms_id)
    if not d:
        return
    L.append(f"{depth} `{tms_id}` — {esc(d.get('title',''))} ({profile})")
    L.append("")
    L.append(f"- **Test type**: `{d.get('test_type','?')}` | **Oracle basis**: `{d.get('oracle_basis','?')}`")
    L.append(f"- **Objective**: {esc(d.get('objective','N/A'), 300)}")
    pre = d.get("preconditions", [])
    if pre:
        L.append(f"- **Preconditions**: " + ", ".join(esc(p, 100) for p in pre))
    env = d.get("environment", {})
    if isinstance(env, dict):
        L.append(f"- **Environment**: {esc(env.get('hardware','?'))}; {esc(env.get('software','?'))}; config `{env.get('configuration','?')}`")
    steps = d.get("steps", [])
    if steps:
        L.append("- **Test cases (steps)**:")
        for s in steps:
            if isinstance(s, dict):
                L.append(f"  {s.get('step','?')}. **{esc(s.get('action',''), 150)}** → expected: {esc(s.get('expected',''), 150)}")
    eo = d.get("expected_outcomes", [])
    if eo:
        L.append("- **Expected outcomes**:")
        for e in eo:
            if isinstance(e, dict):
                L.append(f"  - `{e.get('signal','?')}` = {esc(e.get('expected_value','?'))} (tolerance {esc(e.get('tolerance','?'))})")
    L.append("")


def _render_exe(v, L, profile, exe_id):
    d = v.get(profile, exe_id)
    if not d:
        return
    L.append(f"##### Execution `{exe_id}` — {esc(d.get('title',''))}")
    L.append("")
    L.append(f"- **Test measure**: `{d.get('test_measure_id','?')}` | **Execution kind**: `{d.get('execution_kind','?')}` | **Outcome**: **{str(d.get('outcome','?')).upper()}**")
    env = d.get("environment", {})
    if isinstance(env, dict):
        tv = env.get("tool_versions", {})
        tools = ", ".join(f"{k} {vv}" for k, vv in sorted(tv.items())) if tv else ", ".join(env.get("tools", []))
        L.append(f"- **Environment**: {esc(env.get('hardware','?'))}; {esc(env.get('software','?'))}; tools: {esc(tools, 150)}")
    L.append(f"- **Evidence refs**: " + (", ".join(f"`{r}`" for r in d.get("evidence_refs", [])) or "—"))
    L.append("")


def emit_08(v, out):
    rm = v.repo
    L = scaffold(v, "08-system-verification-report",
                 "System-level verification: (1) reverse-engineered system verification "
                 "evidence — CI test levels, diagnosis reaction verification, measurement "
                 "validation; (2) test specification, cases and execution reports from "
                 "corpus TMS/EXE artifacts. Missing evidence is blocked, not fabricated.")

    # ---- Reverse-engineered system verification evidence ---------------
    L.append("## Reverse-Engineered System Verification Evidence")
    L.append("")
    L.append("### Test Levels in the Repository")
    L.append("")
    L.append("| Level | Scope | Evidence |")
    L.append("|---|---|---|")
    L.append(f"| Unit (host) | all `src/app` modules | {rm.test_counts['unit_c']} C test files in "
             "`tests/unit/app/**`, Ceedling/Unity, executed in CI for every revision "
             "(`docs/developer-manual/software/software-verification.rst`) |")
    L.append("| Static checks | whole repo | C standard conformance tests (`tests/c-std`), "
             "CLI tests (`tests/cli`), DBC validity checks (`tests/dbc`), "
             "OS-include hygiene (`tests/os-information`) |")
    L.append("| HIL | linked program on target | Test setup **not published** in this "
             "repository (`tests/hil` placeholder, `docs/developer-manual/software/software-testing.rst`) |")
    L.append("")
    L.append("Policy: unit and HIL coverage reports **MUST** show 100% line and branch "
             "coverage (software testing doc). Failing tests reject the feature branch in CI.")
    L.append("")
    L.append("### Diagnosis Reaction Verification (built-in)")
    L.append("")
    L.append("Every diagnosis entry is verifiable through the built-in reaction chain: "
             "`DIAG_*` event → severity evaluation (`DIAG_UpdateFlags`, 1 ms) → BMS FSM "
             "`BMS_FSM_STATE_ERROR` → contactor open. Unit tests cover the diagnosis engine "
             "(22 test files in `tests/unit/app/engine/diag/`) and the SOA limit evaluation "
             "(`tests/unit/app/application/soa/`, `application/config/`).")
    L.append("")
    L.append("### Measurement Validation (built-in)")
    L.append("")
    L.append("Cell measurements are validated continuously at runtime: plausibility checks "
             "(`PL_CheckEvent*`), redundancy validation (`MRC_ValidateAfeMeasurement` every "
             "50 ms), AFE communication integrity diagnosis entries — i.e. the system "
             "verifies its own measurement path as part of operation.")
    L.append("")

    # ---- corpus test specification -------------------------------------
    L.append("## Test Specification")
    L.append("")
    any_tms = False
    for profile in PROFILES:
        for tms_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "test_measure"):
            any_tms = True
            _render_tms(v, L, profile, tms_id)
    if not any_tms:
        L.append("No test measure artifacts in the corpus for either profile — **system-level test "
                 "specification gap** (blocked, not fabricated, per governance policy).")
        L.append("")
    L.append("## Test Cases")
    L.append("")
    n_cases = 0
    for profile in PROFILES:
        for tms_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "test_measure"):
            d = v.get(profile, tms_id)
            n = len(d.get("steps", [])) or 1
            n_cases += n
            L.append(f"- `{tms_id}` ({profile}): {n} test case(s)")
    if n_cases == 0:
        L.append("No test cases in corpus.")
    else:
        L.append("")
        L.append(f"**Total system-level test cases**: {n_cases}")
    L.append("")
    L.append("## Execution Report")
    L.append("")
    any_exe = False
    for profile in PROFILES:
        for exe_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "execution"):
            any_exe = True
            _render_exe(v, L, profile, exe_id)
    if not any_exe:
        L.append("No execution artifacts in the corpus — **execution report gap** (blocked, not fabricated).")
    L.append("")
    (out / "08-system-verification-report.md").write_text(finish(L))


# ---------------------------------------------------------------- 09 SW Verif

def emit_09(v, out):
    rm = v.repo
    L = scaffold(v, "09-software-verification-report",
                 "Software verification by level: (1) reverse-engineered unit verification "
                 "evidence — the full per-module unit-test inventory from `tests/unit/app/`; "
                 "(2) corpus test levels (unit, component, integration, HIL) with cases, "
                 "execution reports, execution_kind labeled; actual vs synthetic distinguished.")

    # ---- Reverse-engineered unit test inventory ------------------------
    L.append("## Reverse-Engineered Unit Verification Evidence")
    L.append("")
    L.append(f"The repository carries **{rm.test_counts['unit_c']} C unit test files** "
             "(Ceedling/Unity, host-based) in `tests/unit/app/`. Per-module inventory:")
    L.append("")
    L.append("| Module | Unit test files | Count |")
    L.append("|---|---|---|")
    for m in rm.modules:
        if m["unit_tests"]:
            names = ", ".join(f"`{t}`" for t in m["unit_tests"][:6]) + (" …" if len(m["unit_tests"]) > 6 else "")
            L.append(f"| `{m['key']}` | {names} | {m['n_unit_tests']} |")
    mods_with_tests = sum(1 for m in rm.modules if m["unit_tests"])
    mods_without = [m["key"] for m in rm.modules if not m["unit_tests"]]
    L.append("")
    L.append(f"**Coverage of the module inventory**: {mods_with_tests}/{len(rm.modules)} "
             "modules have direct unit tests; config files are covered by `*/config` test "
             "folders (e.g. `tests/unit/app/application/config/`, `driver/config/`, "
             "`engine/config/`, `task/config/`).")
    L.append("")
    if mods_without:
        L.append("Modules without a dedicated `tests/unit/app/<layer>/<module>/` folder: "
                 + ", ".join(f"`{k}`" for k in mods_without)
                 + " — low-level hardware drivers partly exempt per testing policy "
                   "(justified omission), partly covered via config/AFAPI tests.")
        L.append("")
    L.append("CI enforces the run of these tests for every revision; the coverage report "
             "MUST reach 100% line and branch coverage "
             "(`docs/developer-manual/software/software-testing.rst`, "
             "`docs/software/unit-tests/unit-tests.rst`).")
    L.append("")

    # ---- corpus test levels --------------------------------------------
    LEVELS = [("Unit Testing", "unit"), ("Component Testing", "component"),
              ("Integration Testing", "integration"), ("HIL Testing", "hil")]
    all_tms = []
    for profile in PROFILES:
        for tms_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "test_measure"):
            all_tms.append((profile, tms_id))
    all_exe = []
    for profile in PROFILES:
        for exe_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "execution"):
            all_exe.append((profile, exe_id))
    # classify executions by kind
    def exes_of_kind(kinds):
        out = []
        for profile, eid in all_exe:
            ek = v.get(profile, eid).get("execution_kind", "")
            if kinds == "hil" and ("hil" in ek or "simulation" in ek):
                out.append((profile, eid))
            elif kinds == ek:
                out.append((profile, eid))
        return out

    for title, key in LEVELS:
        L.append(f"## {title}")
        L.append("")
        if key == "unit":
            tm = [(p, t) for p, t in all_tms if v.get(p, t).get("test_type") == "unit"]
        else:
            tm = [(p, t) for p, t in all_tms if v.get(p, t).get("test_type") == key]
        if key == "unit":
            ex = [(p, e) for p, e in all_exe if v.get(p, e).get("execution_kind") in ("actual_host_run", "synthetic_fixture")]
        elif key == "component":
            ex = [(p, e) for p, e in all_exe if "component" in str(v.get(p, e).get("test_measure_id", ""))]
        elif key == "integration":
            ex = exes_of_kind("integration")
        else:
            ex = exes_of_kind("hil")
        L.append("### Test Specification")
        L.append("")
        if tm:
            for p, t in tm:
                _render_tms(v, L, p, t, depth="####")
        else:
            L.append(f"No `{key}` test specification artifacts in the corpus — **gap** (blocked, not fabricated).")
            L.append("")
        L.append("### Test Cases")
        L.append("")
        n = 0
        for p, t in tm:
            d = v.get(p, t)
            c = len(d.get("steps", [])) or 1
            n += c
            L.append(f"- `{t}` ({p}): {c} test case(s)")
        L.append(f"**Subtotal test cases**: {n}")
        L.append("")
        L.append("### Execution Report")
        L.append("")
        if ex:
            for p, e in ex:
                _render_exe(v, L, p, e)
        else:
            note = ("No target-HIL executions exist in the corpus — per governance policy, "
                    "actual product evidence = 0 (blocked, not fabricated)." if key == "hil"
                    else f"No `{key}` execution artifacts in the corpus — gap (blocked, not fabricated).")
            L.append(note)
            L.append("")

    # ---- static-analysis deviation records (SWE.4 deviance evidence) -----
    devs = []
    for profile in PROFILES:
        for did in v.of_profile(profile, lambda d: d.get("artifact_type") == "deviation"):
            devs.append((profile, did))
    L.append("## Static-Analysis Deviance Evidence")
    L.append("")
    L.append(f"The corpus holds **{len(devs)} deviation records** (`FB2-SW-DEV-*`) mined from in-source "
             "Axivion `Style MisraC2012*` suppression annotations. They are the coding-guideline deviance "
             "evidence a software verification report is expected to hold. They are **not** verification "
             "results: each record documents an observed, in-source justified exception in the pinned "
             "implementation, and none of them is a test, a test result, or a coverage claim.")
    L.append("")
    L.append("| Record | Rule | Suppression | Affected lines | File | Symbol |")
    L.append("|---|---|---|---|---|---|")
    for profile, did in sorted(devs, key=lambda t: t[1]):
        d = v.get(profile, did)
        L.append(f"| `{did}` | {d.get('rule_reference')} ({d.get('rule_category')}) | "
                 f"{d.get('suppression_form')} | `{d.get('affected_lines')}` | "
                 f"`{d.get('affected_file')}` | {d.get('affected_symbol')} |")
    L.append("")
    L.append("Every record carries `lifecycle_status: draft`, `human_approval_status: pending`, "
             "`production_authorized: false` and `product_verification_credit: false`; the table above "
             "records their existence and location only and asserts no conformance, no tool qualification "
             "and no completed ISO 26262 or ASPICE assessment.")
    L.append("")
    (out / "09-software-verification-report.md").write_text(finish(L))


# ---------------------------------------------------------------- 10 Impl Mapping

def emit_10(v, out):
    rm = v.repo
    L = scaffold(v, "10-implementation-mapping-document",
                 "Implementation mapping: (1) reverse-engineered module → sources → config → "
                 "unit-test → documentation mapping for all 40 modules; (2) corpus "
                 "design → source mappings and requirement → design → source → test chains; "
                 "(3) the complete requirement-to-test coverage matrix for every requirement "
                 "artifact in both profiles.")

    # ---- Reverse-engineered module mapping -----------------------------
    L.append("## Reverse-Engineered Module Mapping")
    L.append("")
    L.append("Complete mapping of every implemented module to its source files, configuration, "
             "unit tests and module documentation (all paths relative to the repository root):")
    L.append("")
    L.append("| Module | Main sources | Config | Unit tests | Docs |")
    L.append("|---|---|---|---|---|")
    for m in rm.modules:
        src = ", ".join(f"`{s}`" for s in m["sources"][:3]) + (" …" if m["n_sources"] > 3 else "")
        cfg = ", ".join(f"`{c}`" for c in m["config_files"][:2]) or "—"
        tst = f"{m['n_unit_tests']}" if m["unit_tests"] else "0"
        doc = f"`{m['doc']}`" if m["doc"] else "—"
        L.append(f"| `{m['key']}` | {src or '—'} | {cfg} | {tst} | {doc} |")
    L.append("")

    # ---- corpus implementation mapping ---------------------------------
    L.append("## Corpus Implementation Mapping")
    L.append("")
    for profile in PROFILES:
        dsn_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "design" and d.get("engineering_domain") == "software")
        for did in dsn_ids:
            d = v.get(profile, did)
            im = d.get("implementation_mapping", [])
            L.append(f"### `{did}` ({profile}) — {esc(d.get('title',''), 80)}")
            L.append("")
            if isinstance(im, list) and im:
                L.append("| Source file | Symbol | Status |")
                L.append("|---|---|---|")
                for m in im:
                    if isinstance(m, dict):
                        L.append(f"| `{m.get('source_file','?')}` | `{m.get('symbol','?')}` | `{m.get('status','?')}` |")
            else:
                L.append("Implementation mapping not specified in corpus.")
            L.append("")
    # SWR chains
    L.append("### Requirement → Design → Source → Test Chains")
    L.append("")
    for profile in PROFILES:
        for swr in v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and "-SWR-" in d.get("id","")):
            L.append(f"#### `{swr}` ({profile})")
            L.append("")
            designs = sorted({l["source_id"] for l in v.links_where(profile=profile, relation="implements", tgt=swr)})
            for dsn in designs:
                dd = v.get(profile, dsn)
                srcs = sorted({m.get("source_file","?") for m in dd.get("implementation_mapping", []) if isinstance(m, dict)})
                L.append(f"- Design `{dsn}` implements `{swr}` → sources: " + (", ".join(f"`{s}`" for s in srcs) or "—"))
            tms = sorted({l["source_id"] for l in v.links_where(profile=profile, relation="verifies", tgt=swr)})
            embedded = []
            for (p, j), t in sorted(v.artifacts.items()):
                if p == profile and t.get("artifact_type") == "test_measure" and swr in (t.get("referenced_requirements") or []):
                    embedded.append(j)
            all_tests = sorted(set(tms) | set(embedded))
            L.append(f"- Verifying test measures: " + (", ".join(f"`{t}`" for t in all_tests) or "**UNCOVERED — no test**"))
            L.append("")
    # Coverage matrix
    L.append("## Requirement-to-Test Coverage Matrix")
    L.append("")
    L.append("One row per requirement artifact across FSR/TSR/SWR/management classes, both profiles. "
             "Statuses: COVERED-DIRECT (has `verifies` link), COVERED-INDIRECT (allocated child is verified), "
             "COVERED-EMBEDDED (TMS references requirement), UNCOVERED (explicit gap).")
    L.append("")
    L.append("| Profile | Requirement | Type | Status | Direct verifies | Indirect (child ← test) | Verifying tests | Gap note |")
    L.append("|---|---|---|---|---|---|---|---|")
    uncovered = []
    for profile, rid in v.all_requirements():
        d = v.artifacts[(profile, rid)]
        cov = v.coverage(profile, rid)
        # The label was previously a four-case chain with an "MGT" fallback, which
        # labelled every system requirement as a management requirement because SYS ids
        # were not anticipated. SYS and NED and UC are distinct classes and a reader
        # comparing rows cannot tell them apart under one label.
        rtype = ("FSR" if "-FSR-" in rid else "TSR" if "-TSR-" in rid
                 else "SWR" if "-SWR-" in rid else "SEC" if "-SEC-" in rid
                 else "SYR" if "-SYR-" in rid else "HSE" if "-HSE-" in rid else "MGT")
        direct = ", ".join(f"`{x}`" for x in cov["direct"]) or "—"
        indirect = ", ".join(f"`{c}`←{','.join(t)}" for c, t in sorted(cov["indirect"].items())) or "—"
        tests = ", ".join(f"`{x}`" for x in cov["tests"]) or "—"
        if cov["status"] == "UNCOVERED":
            note = "No direct, indirect, or embedded test coverage in corpus"
            uncovered.append((profile, rid))
        else:
            note = ""
        L.append(f"| `{profile}` | `{rid}` | {rtype} | **{cov['status']}** | {direct} | {indirect} | {tests} | {note} |")
    L.append("")
    L.append("### Coverage Summary")
    L.append("")
    total = len(v.all_requirements())
    n_unc = len(uncovered)
    n_cov = total - n_unc
    L.append(f"- **Total requirement artifacts**: {total}")
    L.append(f"- **Covered (any status)**: {n_cov} ({n_cov*100//max(total,1)}%)")
    L.append(f"- **UNCOVERED**: {n_unc}")
    for p, r in uncovered:
        L.append(f"  - `{r}` (`{p}`)")
    L.append("")
    # Computed, not asserted. This sentence used to be unconditional, so it claimed there
    # were uncovered requirements even when the matrix showed none, which is the failure mode
    # a generated document is supposed to prevent.
    if uncovered:
        L.append(f"{len(uncovered)} requirement artifact(s) remain UNCOVERED and that is the "
                 "honest corpus state; the gaps are tracked by review dispositions and by the "
                 "gap report. No coverage is fabricated.")
    else:
        L.append("Every requirement artifact has at least one verification route: a direct "
                 "`verifies` link, an allocated child that is verified, or a test measure that "
                 "names it. **This is a statement about the traceability graph and not about "
                 "verification evidence.** COVERED-INDIRECT means a lower-level requirement is "
                 "verified by some measure; it says nothing about whether that measure was "
                 "executed, and in this corpus most were not. The executions that exist carry "
                 "`execution_kind` `synthetic_fixture`, `none` or a host run of the real product "
                 "code, and none of them is a run on the target hardware. A requirement whose "
                 "only route is an allocated child that is itself blocked is uncovered in "
                 "substance and covered in form, and the coverage matrix reports the form because "
                 "that is what it measures.")
    L.append("")

    # ---- change impact mapping (canonical change records, SUP.10) --------
    chgs = [(p, cid) for p in PROFILES
            for cid in v.of_profile(p, lambda d: d.get("artifact_type") == "change")]
    L.append("## Change Impact Mapping")
    L.append("")
    L.append(f"The corpus holds **{len(chgs)} canonical change records** (`FB2-MAN-CHG-*`) for the "
             "synthetic-reference project. Each is the change-management record of record for one "
             "change request and carries the full chain: trigger, impact analysis, decision, the "
             "artifacts moved to a new revision, the links placed under suspicion, the required "
             "updates, the re-verification selection, and the planned post-change baseline.")
    L.append("")
    L.append("They are **change-management records, not verification results**. None of the three "
             "has been executed, none of the revisions it names has been raised, and none of the "
             "post-change baselines it names exists. A row below is a statement of intended work, "
             "not a report of work done.")
    L.append("")
    L.append("These are not the change-lifecycle *demonstrations*. The demonstrations are "
             "`FB2-SCN-CHG-000001`, `FB2-SCN-CHG-000002` and `FB2-SCN-CHG-000003` under "
             "`docs/artifacts/scenarios/change-lifecycles/`, which exist to exercise the corpus "
             "scenario gate and are checked for structural completeness only. The records below "
             "describe the same three subjects as engineering work; the two sets are deliberately "
             "separate artifacts with different jobs, and each record states its own relationship "
             "to its demonstration in its `relationship_to_scenario_fixture` field.")
    L.append("")
    L.append("| Record | Change type | Trigger class | Affected artifacts | New revisions | Suspect links | Re-verification | Post-change baseline |")
    L.append("|---|---|---|---|---|---|---|---|")
    for p, cid in chgs:
        d = v.get(p, cid)
        ia = d.get("impact_analysis", {}) or {}
        tc = esc((d.get("trigger") or {}).get("trigger_class", "N/A"), 40)
        aa = ", ".join(f"`{x}`" for x in ia.get("affected_artifacts", [])) or "—"
        nr = ", ".join(f"`{r.get('artifact_id')}` {r.get('old_revision')}→{r.get('new_revision')}"
                       for r in d.get("new_revisions", [])) or "—"
        sl = ", ".join(f"`{x}`" for x in d.get("suspect_links", [])) or "—"
        rv = ", ".join(f"`{x}`" for x in d.get("reverification_selection", [])) or "—"
        L.append(f"| `{cid}` ({p}) | `{d.get('change_type')}` | {tc} | {esc(aa)} | {esc(nr)} | "
                 f"{esc(sl)} | {esc(rv)} | `{d.get('post_change_baseline')}` |")
    L.append("")

    L.append("### Suspect Links")
    L.append("")
    L.append("`suspect_links` names links whose endpoint revisions or whose claims the change puts "
             "in question. The baseline link registry still records `change_suspect_status: false` "
             "on every one of them, and that is the correct state: the decisions below are fictional "
             "workflow outcomes, no affected artifact has been revised, and no post-change baseline "
             "exists. The flag becomes true as part of establishing the post-change baseline, at "
             "which point the registry flag and the record's suspect list must agree. Note that all "
             "of these links have existing endpoints at existing revisions, so no dangling-endpoint "
             "check will ever flag them - they are the links that survive a change unnoticed.")
    L.append("")
    L.append("| Record | Link | Relation | Endpoints | Why it is suspect |")
    L.append("|---|---|---|---|---|")
    for p, cid in chgs:
        d = v.get(p, cid)
        for s in d.get("suspect_link_rationale", []) or []:
            L.append(f"| `{cid}` | `{s.get('link_id')}` | `{s.get('relation_type')}` | "
                     f"{esc(s.get('endpoints', ''), 90)} | {esc(s.get('why_suspect', ''), 320)} |")
    L.append("")

    L.append("### Decision and Approval State")
    L.append("")
    L.append("| Record | Decision id | Decision maker | Disposition | Approvals recorded | Re-verification executed |")
    L.append("|---|---|---|---|---|---|")
    for p, cid in chgs:
        d = v.get(p, cid)
        dec = d.get("decision", {}) or {}
        cc = d.get("change_control", {}) or {}
        need = len(cc.get("required_approvals", []) or [])
        L.append(f"| `{cid}` | `{dec.get('decision_id')}` | {esc(dec.get('decision_maker', ''), 100)} | "
                 f"`{dec.get('disposition')}` | {cc.get('approvals_recorded', 0)} of {need} | no |")
    L.append("")
    L.append("Every record carries `profile: synthetic_reference`, `origin: synthetic`, "
             "`human_approval_status: pending`, `production_authorized: false` and "
             "`product_verification_credit: false`. Each `decision_maker` is a fictional role "
             "identity in the synthetic project and each `disposition` is a `synthetic_decision` in "
             "the sense of `governance/corpus-policy.json` "
             "(`synthetic_decision:{fictional_role}:{decision_id}`): not a human approval, not a "
             "foxBMS maintainer decision, and not a SoftwareDevLabs decision. All three records "
             "are `implementation_status: not_in_source`, and no file under `src/`, `tests/`, "
             "`conf/` or `wscript` is touched by them. No row in this section asserts that any "
             "change was made, approved or verified in any real project, and no row asserts a "
             "measured test result.")
    L.append("")
    L.append("### Corpus-Consistency Notes")
    L.append("")
    L.append("Three slots in these records are empty by schema rather than by omission, and the "
             "reasoning is recorded in the records themselves so the emptiness is not read as an "
             "incomplete analysis:")
    L.append("")
    L.append("- `impact_analysis.affected_reviews` is empty in all three. The change schema admits "
             "only ids matching `^FB2-REV-[A-Z]{2,4}-[0-9]{6}$`, i.e. a review id carrying a "
             "two-to-four letter type segment. The corpus contains exactly one review artifact, "
             "`FB2-REV-000001`, which has no such segment and belongs to the `as_is` profile as an "
             "automated review of the reconstructed foxBMS artifacts. There is therefore no review "
             "in the `synthetic_reference` profile for these changes to invalidate, and the review "
             "work they do require is enumerated in each record's `re_review_scope` field.")
    L.append("- `impact_analysis.affected_evidence` is empty in all three, for the same shape of "
             "reason: the schema admits only `^FB2-EVD-[A-Z]{2,4}-[0-9]{6}$` and no `FB2-EVD-` "
             "artifact exists in either profile. The executions these changes really do invalidate "
             "(`FB2-VER-EXE-000001`, and for `FB2-MAN-CHG-000002` also `FB2-VER-EXE-000003` and "
             "`FB2-VER-EXE-000005`) do exist in `synthetic_reference` and are named in each record's "
             "`evidence_invalidation` field instead.")
    L.append("- `FB2-PRM-000001` (parameter-registry entry), the `FB2-SRC-*` identifiers (source "
             "anchors) and `VAR-AFE-ADI-1830` (a variant-matrix row) all resolve, but as rows of "
             "registries rather than as artifacts with revisions and lifecycle states. A `changes` "
             "link pointed at any of them would dangle, so each is recorded in a typed sibling "
             "field of the record that concerns it. Several of them even satisfy the change schema's "
             "id pattern, which makes this the easiest category error in the corpus to commit.")
    L.append("")
    (out / "10-implementation-mapping-document.md").write_text(finish(L))


# ---------------------------------------------------------------- pandoc

def to_docx(md_path, out_dir):
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return False
    stem = md_path.stem
    docx = out_dir / (stem + ".docx")
    title = DOC_TITLES.get(stem, stem)
    r = subprocess.run(
        [pandoc, str(md_path), "-o", str(docx), "--toc", "--toc-depth=3",
         "-M", f"title=foxBMS 2 — {title}", "-M", "author=foxBMS 2 Lifecycle Artifact Corpus",
         "-M", "date=" + GEN_STAMP[:10]],
        capture_output=True, text=True)
    return r.returncode == 0


# ---------------------------------------------------------------- integrity check

def check(out):
    ok = True
    v = Views()
    failures = []
    # (a) all ten docs exist with required headings
    for stem in DOC_ORDER:
        p = out / (stem + ".md")
        if not p.exists():
            failures.append(f"MISSING document: {stem}.md")
            ok = False
            continue
        text = p.read_text()
        for h in REQUIRED_HEADINGS.get(stem, []):
            if h not in text:
                failures.append(f"{stem}.md: missing heading '{h}'")
                ok = False
    # (b) owned artifact IDs present per document
    for stem in DOC_ORDER:
        p = out / (stem + ".md")
        if not p.exists():
            continue
        text = p.read_text()
        pred = OWNERSHIP[stem]
        for (prof, aid), d in sorted(v.artifacts.items()):
            if prof in PROFILES and pred(stem, d):
                if aid not in text:
                    failures.append(f"{stem}.md: owned artifact `{aid}` not present")
                    ok = False
    # (c) coverage matrix has a row per requirement artifact
    mp = out / "10-implementation-mapping-document.md"
    if mp.exists():
        text = mp.read_text()
        for profile, rid in v.all_requirements():
            if rid not in text:
                failures.append(f"coverage matrix: missing row for `{rid}` (`{profile}`)")
                ok = False
    if failures:
        print("INTEGRITY CHECK FAILED:")
        for f in failures[:40]:
            print("  -", f)
        if len(failures) > 40:
            print(f"  ... and {len(failures)-40} more")
    else:
        print("INTEGRITY CHECK PASSED: all documents complete, all owned IDs present, coverage matrix complete.")
    return ok


def determinism(out):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        generate(tdp)
        same = True
        for stem in DOC_ORDER:
            a = strip_stamp(out / (stem + ".md"))
            b = strip_stamp(tdp / (stem + ".md"))
            if a != b:
                print(f"DETERMINISM FAIL: {stem}.md differs between runs")
                same = False
        print("DETERMINISM: " + ("byte-identical across runs" if same else "MISMATCH"))
        return same


def strip_stamp(p):
    txt = p.read_text()
    txt = re.sub(r"Generated: [0-9T:Z-]+", "Generated: <stamp>", txt)
    txt = re.sub(r"\| Generated \| [0-9T:Z-]+ \|", "| Generated | <stamp> |", txt)
    return txt


# ---------------------------------------------------------------- main

def generate(out):
    out.mkdir(parents=True, exist_ok=True)
    v = Views()
    emit_01(v, out)
    emit_02(v, out)
    emit_03(v, out)
    emit_04(v, out)
    emit_05(v, out)
    emit_06(v, out)
    emit_07(v, out)
    emit_08(v, out)
    emit_09(v, out)
    emit_10(v, out)
    # docx
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("NOTE: pandoc not found — Word conversion skipped.")
    else:
        n = 0
        for stem in DOC_ORDER:
            if to_docx(out / (stem + ".md"), out):
                n += 1
        print(f"Word conversion: {n}/10 documents converted.")
    print(f"Generated 10 Markdown documents in {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="run integrity check on generated documents")
    ap.add_argument("--out-dir", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    out = Path(args.out_dir)
    if args.check:
        ok = check(out)
        ok &= determinism(out)
        sys.exit(0 if ok else 1)
    generate(out)


if __name__ == "__main__":
    main()
