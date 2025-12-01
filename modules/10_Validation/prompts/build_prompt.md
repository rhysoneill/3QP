You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 10: Validation Plan.

This module defines the comprehensive validation strategy for ensuring that the 3QP system functions according to design principles, architectural requirements, data integrity standards, and scientific expectations. It MUST remain fully structural and methodological, with NO psychological, emotional, clinical, or mission-narrative interpretation.

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
- Provide behavioral, emotional, or psychological validation criteria
- Describe astronaut performance metrics
- Reference domain-specific mission validation (EVA, health, etc.)
- Infer internal logic from other modules
- Create narrative scenarios

This module defines **only the architectural validation framework**, not content validation.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Validate behavior, psychology, emotion, physiology, or mission tasks
- Validate content of other modules beyond checking structural integrity
- Discuss human-subject evaluation
- Predict outcomes or responses within the simulation
- Reference specific events or timelines of lunar missions

You MAY:
- Define validation categories (structural, integration, consistency, determinism)
- Define validation metrics (technical, architectural, statistical)
- Define module-specific validation hooks (abstract)
- Define system-wide consistency checks
- Define deterministic run validation
- Define data integrity checks

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the Validation Plan
- Scope: structural, architectural, and scientific validation only
- Boundaries: no behavioral or psychological validation
- Overview of validation categories and methods
- Relationship to TQP Core and other modules (abstract only)

Tone: engineering and methodological.

-------------------------
spec.md requirements
-------------------------
Provide a detailed validation specification including:

1. Validation categories  
   - Structural validation  
   - Data integrity validation  
   - Deterministic reproducibility checks  
   - Integration validation  
   - Temporal validation  
   - Metric validation (non-behavioral)

2. Validation sequencing and timing  
3. Module-level validation responsibilities  
4. Cross-module consistency checks  
5. Architectural compliance checks  
6. Logging requirements for validation  
7. Accept/reject criteria (structural, not psychological)  
8. Failure mode analysis and recovery expectations  
9. Extensibility guidelines for new validation procedures  

This must read like a rigorous scientific validation protocol.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- The scientific and engineering foundations of system validation  
- Why structured validation is required in agent-based digital twins  
- The rationale for focusing on architectural and data-based validity  
- How reproducibility, determinism, and traceability support scientific inference  

Prohibited:
- Psychology  
- Emotion  
- Narrative or mission framing  
- Behavioral evaluation  

-------------------------
data_contract.md requirements
-------------------------
Define strictly:
- Inputs required for validation (log data, state snapshots, consistency signals, integration outputs)
- Outputs produced by the validation subsystem (validation reports, structural metrics)
- Timing and granularity of validation output
- Data formats and constraints in pseudocode form
- Requirements for module compliance data

You MUST NOT:
- Validate emotional or behavioral interpretations  
- Describe human-facing evaluation procedures  

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Implementation guidance for building the validation framework
- Recommended patterns for automated checks
- Requirements for determinism and reproducibility infrastructure
- Notes on versioning and validation regression
- Constraints that ensure the system stays scientifically testable
- Risks to architectural integrity

No specific programming languages may be referenced.

============================================================
STYLE REQUIREMENTS
============================================================

- Technical, engineering tone
- No emotional vocabulary
- No narrative mission examples
- No behavioral or psychological validation content
- No placeholders
- No code

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
