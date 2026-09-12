## Purpose

Defines generation of a complete, self-contained end-to-end HTML engineering document from the foxBMS 2 lifecycle artifact corpus, presenting all engineering levels (stakeholder requirements through HIL test evidence) with full attributes, traceability linkages, and rationale in a single navigable file with embedded Mermaid diagrams.

## ADDED Requirements

### Requirement: Single-file HTML engineering document
The system SHALL generate a single self-contained HTML file (`docs/artifacts/reports/e2e-engineering-document.html`) from the canonical corpus JSON that presents every engineering process level in one document, requiring no server and viewable offline in a standard browser.

#### Scenario: File opens standalone in browser
- **WHEN** the generated HTML file is opened directly in a browser without a network connection
- **THEN** all textual content, tables, linkages, and section structure render correctly (diagrams render via CDN when online, with readable fallback text offline)

### Requirement: Document section coverage
The generated document SHALL contain, in engineering order, the following sections with the specified content sourced from the corpus: (a) stakeholder requirements; (b) system requirements with statement, rationale, classification, acceptance criteria, assumptions, and verification approach; (c) system architecture with multiple viewpoint diagrams; (d) software requirements with the same attribute set; (e) software architecture with static and dynamic viewpoint diagrams; (f) detailed design per component with static and dynamic diagrams plus implementation requirements; (g) software integration report; (h) system verification artifacts — test specifications, test cases, and test execution reports; (i) software verification artifacts — unit, component, integration, and HIL test specifications, cases, and execution reports; (j) implementation mapping linking each design element to source file and symbol.

#### Scenario: All corpus requirement attributes appear
- **WHEN** any requirement artifact from the corpus is rendered in the document
- **THEN** its id, title, statement, rationale, classification, ASIL allocation, acceptance criteria, conditions/modes, source references, and assumption references are all present in the rendered entry

#### Scenario: HIL and test levels are distinguishable
- **WHEN** the verification sections are rendered
- **THEN** unit, component, integration, and HIL evidence are separately identified by execution kind and coverage level, with actual-host runs distinguished from synthetic fixtures

### Requirement: Architecture and design diagrams with viewpoints
The document SHALL embed Mermaid diagrams for: (a) system context viewpoint (system boundary, external actors); (b) system functional block viewpoint (blocks and flows); (c) system dynamic viewpoint (sequence or flow of the protection chain); (d) software static component viewpoint; (e) software dynamic state-machine viewpoint; (f) per-component detailed design static and dynamic diagrams derived from each design artifact's behavior model and decomposition.

#### Scenario: Diagrams are valid Mermaid
- **WHEN** the document is viewed with Mermaid.js available
- **THEN** every embedded diagram block parses and renders without error

#### Scenario: Dynamic diagrams reflect design behavior models
- **WHEN** a design artifact declares a state machine with states and transitions
- **THEN** the generated dynamic diagram contains exactly those states and transitions

### Requirement: Traceability linkages with rationale
Every cross-artifact relationship in the document (hazard→safety goal, FSR→safety goal, TSR/SWR→FSR, design→SWR, test→requirement, execution→test, review→artifact) SHALL be rendered as a hyperlinked reference carrying the link's rationale, provenance, review state, and change-suspect status from the link registry.

#### Scenario: Every registry link appears in the document
- **WHEN** the document is generated
- **THEN** each link in each profile's link registry is presented at least once with its full metadata, and its endpoints are anchor-navigable

### Requirement: Implementation mapping presentation
The document SHALL present, per design artifact, an implementation mapping table listing each mapped source file, symbol, and status, with a traceability chain from the software requirement through the design artifact to the mapped source code and onward to the verification measures covering that requirement.

#### Scenario: Mapping chains from requirement to code
- **WHEN** a reader follows the rendered chain for any SWR
- **THEN** they reach the implementing design, its mapped source files, and the test measures that verify the requirement, each step hyperlinked

### Requirement: Deterministic regeneration
The generation tool SHALL be deterministic: regenerating the document from an unchanged corpus produces a byte-identical HTML file (excluding any explicit generation-timestamp marker), and the tool SHALL fail with a nonzero exit if required corpus inputs are missing or unparseable.

#### Scenario: Regeneration is byte-identical
- **WHEN** the tool runs twice against the same corpus state
- **THEN** the generated HTML content is identical apart from the declared timestamp field

### Requirement: Verification of document integrity
The corpus acceptance tooling SHALL gain a check that the generated HTML document exists, contains all required section headings, contains no unresolved corpus artifact IDs that lack a corresponding section, and that every corpus requirement artifact ID appears at least once in the document.

#### Scenario: Missing artifact detected
- **WHEN** the HTML is generated while a corpus requirement artifact is omitted from the document content
- **THEN** the integrity check fails naming the missing artifact ID
