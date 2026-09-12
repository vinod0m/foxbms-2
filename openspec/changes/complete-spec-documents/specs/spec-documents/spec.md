## Purpose

Defines generation of ten standalone, per-discipline specification documents (Markdown with embedded Mermaid diagrams, plus Word conversions) from the foxBMS 2 lifecycle artifact corpus, each presenting its engineering level with complete attributes, diagrams, traceability linkages, and requirement-to-test coverage.

## ADDED Requirements

### Requirement: Document set generation
The tool SHALL generate ten standalone documents under `docs/artifacts/spec-documents/`: stakeholder requirements specification, system requirements specification, system architecture specification, software requirements specification, software architecture specification, detailed design specification, software integration report, system verification report, software verification report, and implementation mapping document. Each SHALL be emitted as Markdown with embedded Mermaid diagrams, and as a `.docx` via pandoc when pandoc is available.

#### Scenario: All ten documents generated
- **WHEN** the tool runs against the corpus
- **THEN** all ten `.md` files exist, each with title, document control block, scope section, and corpus-derived content

#### Scenario: Pandoc absent
- **WHEN** pandoc is not installed on the machine
- **THEN** Markdown generation still succeeds and the tool reports that Word conversion was skipped

### Requirement: Stakeholder requirements specification content
The stakeholder requirements specification SHALL present the item definition, operational situation, modes, external systems, stakeholder needs, and use-case context derived from `governance/scope-and-applicability.json`, and SHALL state which corpus artifacts the premises trace to.

#### Scenario: Item definition rendered
- **WHEN** the document is generated
- **THEN** the item definition, boundaries, and stakeholder needs from the scope artifact appear with source artifact IDs cited

### Requirement: System requirements specification content
The system requirements specification SHALL render every safety goal and FSR of both profiles with full attributes: id, title, statement, rationale, ASIL allocation, safety goal reference, acceptance criteria, conditions/modes, source references, and assumption references.

#### Scenario: Full attribute rendering
- **WHEN** any safety goal or FSR is rendered
- **THEN** all nine attribute groups listed above are present

### Requirement: System architecture specification diagrams
The system architecture specification SHALL embed data-derived Mermaid diagrams for at least three viewpoints: system context (boundary + external actors from the scope artifact), functional block (protection chain blocks from link registries), and dynamic (sequence of the cell-voltage protection chain from hazard to contactor opening), each with a one-line caption readable without diagram rendering.

#### Scenario: Dynamic viewpoint follows the protection chain
- **WHEN** the dynamic diagram is rendered
- **THEN** its participants and messages correspond to the HAZ→SGO→FSR→TSR/SWR→DSN→TMS chain in the link registries

### Requirement: Software requirements specification content
The software requirements specification SHALL render every SWR and software-facing TSR with the full attribute set (statement, rationale, classification, ASIL, acceptance criteria, source and assumption references), grouped by parent FSR with the `allocated_to` linkage shown.

#### Scenario: Grouping by parent FSR
- **WHEN** SWRs are rendered
- **THEN** each SWR appears under its parent FSR with the link rationale quoted

### Requirement: Software architecture specification diagrams
The software architecture specification SHALL embed data-derived Mermaid diagrams for a static component viewpoint (SWRs, designs, and their `implements`/`allocated_to` relations) and a dynamic viewpoint per design artifact (state machines from `behavior_model.states`/`transitions`), plus a task/thread context diagram derived from the corpus timing budget elements.

#### Scenario: State diagrams reflect behavior models exactly
- **WHEN** a design artifact declares states and transitions
- **THEN** the generated state diagram contains exactly those states and transitions

### Requirement: Detailed design specification content
The detailed design specification SHALL render, per design artifact: responsibilities, decomposition, interfaces (signals with direction/unit/range), constraints, budgets, failure response, and per-component static and dynamic Mermaid diagrams derived from decomposition/interfaces/behavior_model; absent models SHALL be labeled "not specified in corpus" rather than omitted silently. Implementation requirements extracted from the design (timing, accuracy, resource budgets) SHALL be listed with their source design artifact.

#### Scenario: Interface tables complete
- **WHEN** a design declares interface signals
- **THEN** each signal is tabulated with name, direction, type, unit, range, and rate

### Requirement: Software integration report content
The software integration report SHALL list the integrated software components (from `implements` chains), the integration evidence available in the corpus (executions by kind), and every integration gap explicitly (e.g., no target-hardware integration runs), each gap with a disposition. No integration evidence SHALL be invented.

#### Scenario: Integration gaps stated, never fabricated
- **WHEN** the corpus has no component or integration-level executions
- **THEN** the report states the gap and cites the governance policy that evidence is blocked, not fabricated

### Requirement: System verification report content
The system verification report SHALL render system-level test specifications (objective, preconditions, steps, expected outcomes, oracle basis, environment), test cases, and execution reports from TMS/EXE artifacts, with outcome, execution_kind, environment, and evidence references per execution.

#### Scenario: Execution evidence rendered
- **WHEN** an execution artifact exists
- **THEN** its outcome, execution kind, tool versions, and evidence refs appear in the report

### Requirement: Software verification report content
The software verification report SHALL have distinct sections for unit, component, integration, and HIL testing, each section containing test specification, test cases, and execution report content derived from corpus artifacts; every execution SHALL be labeled with its `execution_kind`, and actual host runs SHALL be visually distinguished from synthetic fixtures per governance policy.

#### Scenario: HIL section distinguishes evidence classes
- **WHEN** the HIL section is rendered
- **THEN** each listed execution states its execution_kind and the section notes that no target-HIL executions exist in the corpus if that is the case

### Requirement: Implementation mapping document
The implementation mapping document SHALL present, per design artifact, its implementation mapping entries (source file, symbol, status), and for each SWR a full chain: SWR → implementing design → mapped source files → test measures verifying the SWR, every step hyperlinked/cited by artifact ID.

#### Scenario: Mapping chain traversable
- **WHEN** the document is read for any SWR
- **THEN**the reader can follow design, source files, and verifying tests by artifact ID

### Requirement: Requirement-to-test coverage matrix
The implementation mapping document SHALL contain a coverage matrix listing every requirement artifact of both profiles with columns: direct verifies links, indirect coverage via allocated children, coverage status (COVERED-DIRECT / COVERED-INDIRECT / UNCOVERED), and the verifying test measures. UNCOVERED requirements SHALL be listed explicitly with a gap note; the matrix SHALL include TSRs, FSRs, and SWRs — not only FSRs.

#### Scenario: Uncovered requirements explicit
- **WHEN** the matrix is generated
- **THEN** every requirement without direct or indirect test coverage appears with status UNCOVERED and a gap note

#### Scenario: All requirement classes included
- **WHEN** the matrix is generated
- **THEN** it contains one row per requirement artifact across FSR, TSR, SWR, and management requirement classes in both profiles

### Requirement: Deterministic regeneration
The generation SHALL be deterministic: two runs over an unchanged corpus produce byte-identical Markdown output (excluding an explicit generation-timestamp line), and the tool SHALL exit nonzero if required corpus inputs are missing or unparseable.

#### Scenario: Byte-identical regeneration
- **WHEN** the tool runs twice on the same corpus state
- **THEN** all ten Markdown files are identical except the timestamp line

### Requirement: Per-document integrity check
The tool SHALL provide a `--check` mode verifying for each document: (a) required section headings present; (b) every corpus artifact ID owned by that document's discipline appears at least once; (c) the coverage matrix contains a row for every requirement artifact. Failures SHALL name the missing IDs and exit nonzero.

#### Scenario: Missing requirement detected
- **WHEN** a requirement artifact is absent from its document
- **THEN** the integrity check fails naming that artifact ID
