You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 12: Changelog & Notes.

This module defines the system-wide change management structure, version tracking rules, update documentation procedures, and architectural note-keeping framework for 3QP. It MUST remain project-oriented, structural, and administrative. It MUST NOT describe simulation behavior, psychology, physiology, or mission events.

============================================================
SCOPE OF THIS MODULE
============================================================

You must generate FIVE files:
1. README.md
2. spec.md
3. theory_basis.md
4. data_contract.md
5. implementation_notes.md

You MUST NOT:
- Generate code
- Generate tests
- Describe internal logic of any module
- Define behavioral, physiological, cognitive, or social processes
- Reference mission scenarios or narratives
- Predict simulation output or agent behaviors

This module governs documentation structure and version control discipline only.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Modify or reinterpret any other module’s responsibilities
- Include psychological terminology
- Describe event sequences or simulation outcomes
- Refer to implementation languages or code repositories

You MAY:
- Define version tracking procedures
- Define rules for structured changelog entries
- Establish documentation update workflow
- Describe how module versions should be frozen
- Define architectural note-keeping conventions
- Specify system-wide traceability expectations

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the Changelog & Notes module
- Scope: project documentation tracking, version discipline, architectural notes
- Boundaries: not simulation content, not behavioral or operational notes
- High-level description of version management structure
- Explanation of the role this module plays in scientific reproducibility

Tone: engineering and administrative.

-------------------------
spec.md requirements
-------------------------
Provide a complete specification including:

1. Changelog structure and required fields  
2. Version number format and increment rules  
3. Rules for freezing module versions  
4. Documentation lifecycle (draft → review → freeze)  
5. Requirements for cross-module traceability  
6. System-wide version governance  
7. Storage and retention expectations  
8. Update review and approval rules  
9. Error handling (incorrect versioning, conflicting changes)  
10. Extensibility (support for future modules or submodules)  

This must follow the style of NASA documentation governance protocols.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- Engineering and scientific rationale for strict version control  
- Importance of traceability in complex agent-based simulations  
- Why changelog discipline is critical for reproducibility  
- The conceptual basis for separating system documentation from model content  

Prohibited:
- Behavioral theory
- Simulation narratives
- Psychological explanation

-------------------------
data_contract.md requirements
-------------------------
Define ONLY:
- Inputs (module updates, specification changes, version increments)
- Outputs (system changelog entries, version tables, revision reports)
- Required metadata fields for every entry
- Timing and procedural triggers (e.g., upon module freeze)
- Constraints on what constitutes a valid changelog entry

These are *process-level* data contracts, not simulation data.

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Guidelines for maintaining changelog consistency
- Recommended directory structures
- Strategies for preventing accidental drift between versions
- Notes on module-to-module dependency updates
- Requirements for long-term maintenance
- Risks to documentation integrity

No programming languages may be referenced.

============================================================
STYLE REQUIREMENTS
============================================================

- Technical, engineering tone
- No narrative examples
- No behavioral content
- No emotion terminology
- No placeholders
- No references to code implementation
- Fully self-contained

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
