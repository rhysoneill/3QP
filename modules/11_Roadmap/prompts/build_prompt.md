You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 11: Implementation Roadmap.

This module defines the phased engineering plan for implementing 3QP after all architecture modules are completed. It MUST remain structural, project-oriented, and engineering-focused. It does NOT describe code, data, behavior, psychology, physiology, mission events, or model internals.

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
- Write code
- Write tests
- Describe internal logic of any module
- Include behavioral, psychological, or physiological elements
- Describe operational lunar tasks or mission narratives
- Predict outcomes or system behavior

This module defines a project execution roadmap, not simulation functionality.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Alter the design or responsibilities of any other module
- Define or modify subsystem internal algorithms
- Describe emotional or cognitive processes
- Reference mission events or astronaut scenarios

You MAY:
- Define development phases
- Define integration sequencing
- Specify testing milestones (architecture-level only)
- Define project risk categories
- Specify documentation and versioning requirements
- Establish long-term extensibility roadmap

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the Implementation Roadmap
- Scope: engineering plan, milestones, integration sequencing
- Boundaries: no technical model details, no code
- High-level summary of project phases
- Expected alignment with NASA-style systems engineering processes

Tone: formal, engineering, project-management oriented.

-------------------------
spec.md requirements
-------------------------
Provide a complete roadmap specification including:

1. Development phases (architecture → module implementation → integration → validation)
2. Module implementation sequence and dependencies
3. Integration sequence and gating conditions
4. Documentation workflow and version control strategy
5. Architecture compliance checkpoints
6. System maturity milestones (alpha, beta, review-ready)
7. Requirements for reproducibility and scientific transparency
8. Resource considerations (modular build, incremental integration)
9. Failure modes in development (not simulation) and mitigation
10. Long-term extensibility (future modules, expansions, refactoring expectations)

This must read like a NASA program execution plan.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- The engineering and systems-theory rationale for structured implementation planning
- How modular development reduces complexity and preserves architectural integrity
- Why sequencing matters for scientific validity
- Why architecture-first development is required for agent-based digital twins

Prohibited:
- Mission narrative
- Behavior/emotion/cognition explanations
- Code-level detail

-------------------------
data_contract.md requirements
-------------------------
Define ONLY:
- Inputs this roadmap module “expects” conceptually (architecture modules completed, specifications finalized)
- Outputs this module provides (implementation phases, milestones, sequencing)
- Any process-level signals or control markers (conceptual only)
- Requirements for readiness before a module can be implemented

Important:
- These are *process-level data contracts*, not simulation data contracts.
- No technical model data should appear here.

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Recommendations for structuring the overall development workflow
- Notes on maintaining version discipline
- Suggestions for integration pacing
- Risks to the project timeline and architecture purity
- Long-term maintenance planning
- Requirements for eventual transition from architectural spec → implementation code

No programming language references allowed.

============================================================
STYLE REQUIREMENTS
============================================================

- Technical, engineering, and procedural tone
- No narrative or fictional mission examples
- No psychological or emotional vocabulary
- No implementation code
- No placeholders
- Self-contained and complete

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
