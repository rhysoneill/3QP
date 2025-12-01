You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 03: Architecture Overview.

This module defines the global system structure, high-level module boundaries, and the architectural principles governing how the 12 modules relate to one another. It documents major subsystems, their responsibilities, and allowed data flows. It does NOT define internal algorithms or behaviors for any module.

============================================================
SCOPE OF THIS MODULE
============================================================

You must generate FIVE files:
1. README.md
2. spec.md
3. theory_basis.md
4. data_contract.md
5. implementation_notes.md

You MUST NOT generate code.
You MUST NOT generate tests.
You MUST NOT describe internal logic for TQP Core, physiology, BDI, stressors, social networks, intervention systems, or any other module.

This module is a high-level architectural blueprint.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Specify the internal mechanics of any of the 12 modules
- Define behavioral, psychological, physiological, or social logic
- Create cross-module dependencies beyond allowed conceptual flows
- Provide detailed algorithmic descriptions

You MAY:
- Define abstract module boundaries
- Describe allowed directional data flows
- Establish the architectural principles governing all modules
- Specify how modules fit together at an abstract level
- Define system-wide sequencing at the architectural level

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose and function of the Architecture Overview module
- Role within the 3QP system
- Summary of high-level system structure
- How the 12 modules fit together conceptually
- Constraints and architectural commitments (e.g., modularity, determinism, reproducibility)

-------------------------
spec.md requirements
-------------------------
Provide a complete architecture specification including:

1. Global module map  
2. Allowed data flows  
3. High-level timing and sequencing relationships  
4. Module boundary rules  
5. Architectural constraints (e.g., statelessness where required, orthogonality between modules)  
6. Integration responsibilities  
7. The separation-of-concerns model  
8. System-level error handling philosophy  
9. Scalability considerations (4–6 agents, high fidelity)  
10. Extensibility requirements for future research modules  

This must read like a NASA-grade technical architecture document.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- Architectural principles guiding the system (microservices, modularity, separation of concerns, discrete-time behavioral simulation)
- Why modular decomposition is required for TQP research validity
- Why architecture must precede module implementation
- Rationale for isolating behavioral, physiological, cognitive, and structural subsystems

Do NOT include domain behavioral theory.

-------------------------
data_contract.md requirements
-------------------------
Define ONLY:
- The required module-level data exchange interfaces at a conceptual level
- High-level categories of data that may move between modules
- Directionality (who sends / who receives)
- Synchronization semantics (timing, granularity)
- Global validity constraints (consistency, format expectations)

No module-internal details are permitted.

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Guidance for implementers on how to maintain architectural integrity
- Recommendations for enforcing module boundaries
- Notes for future integration planning
- Potential risks to architecture purity
- Requirements for documentation consistency across modules
- How to maintain versioning discipline

Do NOT reference code or implementation languages.

============================================================
STYLE REQUIREMENTS
============================================================

- Technical, engineering tone
- No narrative examples
- No fictional mission scenarios
- No emotional language
- No placeholders
- No references to implementation code
- Self-contained and deterministic

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
