You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 04: Slow–Fast Physiology Model.

This module defines the physiological subsystem that governs slow-time drift (cumulative change) and fast-time responses (acute physiological reactions). It provides abstract physiological state variables and update rules but MUST NOT include behavioral, psychological, or narrative content.

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
You MUST NOT provide medical recommendations.
You MUST NOT describe behavior, emotions, cognition, social dynamics, stressors, or interventions.

This module is a mechanistic, abstract physiology subsystem designed for simulation, not medicine.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Reference internal mechanics of TQP Core or other modules
- Define the logic of stressors, BDI cognition, social interactions, or interventions
- Describe psychological states or performance decrements
- Create clinical or diagnostic physiological detail
- Use narrative examples or mission scenarios

You MAY:
- Define physiological state variables
- Describe slow and fast update processes
- Establish how physiological drift interacts abstractly with the simulation kernel
- Define the tempo of physiological changes
- Specify computational models (e.g., drift equations, thresholds) in abstract form

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the physiology module within 3QP
- Scope of physiological modeling (slow vs fast systems)
- High-level description of state variables
- Boundaries (what is NOT included)
- Expected abstract interfaces with the simulation engine

Tone: engineering, mechanistic, non-medical.

-------------------------
spec.md requirements
-------------------------
Provide a complete physiology subsystem specification including:

1. Overview of the physiological model structure  
2. Definition of physiological state variables  
3. Slow-time processes (drift, cumulative load, long-term change)  
4. Fast-time processes (acute spikes, temporary deviations)  
5. Update cycle sequencing and timing  
6. Interaction points with the TQP Core (abstract only)  
7. Parameterization strategy (no numerical values)  
8. Model constraints and assumptions  
9. Error handling and stability considerations  
10. Extensibility for later integration with stressors and interventions (abstract)

This must read like a NASA engineering specification, not a biomedical paper.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- The conceptual foundation of slow–fast systems (hybrid dynamical models)
- Why physiological slow–fast dynamics are required in long-duration missions
- The rationale for computational abstraction (not medical fidelity)
- Constraints imposed to maintain modularity and scientific validity

Do NOT include:
- Medical mechanisms
- Behavioral theory
- Intervention theory

-------------------------
data_contract.md requirements
-------------------------
Define ONLY:
- Inputs this module expects (e.g., abstract stressor intensity, time-step signals)
- Outputs it provides (e.g., physiological state updates)
- Data types in pseudocode form
- Timing of data exchange (daily, intra-day)
- Validity rules and constraints for upstream/downstream modules

Do NOT describe:
- Internal logic of stressor modules
- How physiology influences behavior

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Guidance for implementers on designing the model
- Recommendations for data structures and update patterns
- Considerations for numerical stability
- Versioning strategy
- Known risks and architectural constraints
- Requirements for maintaining strict separation from behavior or emotion modeling

Do NOT reference code or libraries.

============================================================
STYLE REQUIREMENTS
============================================================

- Precise engineering tone
- No narrative examples
- No fictional mission descriptions
- No placeholder text
- No references to code implementation
- Self-contained and consistent

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
