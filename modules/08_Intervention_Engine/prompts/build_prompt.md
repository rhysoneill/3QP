You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 08: Intervention Engine.

This module defines the computational framework for representing, scheduling, activating, and evaluating interventions within the 3QP simulation. It MUST remain entirely abstract and mechanistic. It does NOT define the content, behavioral meaning, psychological mechanism, or physiological mechanism of any intervention. Only structure, timing, triggers, and data flow are allowed.

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
- Describe psychological or emotional effects of interventions
- Describe medical or clinical interventions
- Describe behavioral outcomes
- Create narrative mission scenarios
- Define content or logic of stressor, physiology, BDI, or social modules
- Reference internal implementation of other modules

This module is about **structural representation** of interventions only.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Describe the meaning, purpose, or therapeutic effect of interventions
- Infer psychological traits, emotions, or states
- Mention clinical mental health or medical protocols
- Describe interactions with other modules beyond abstract interfaces
- Predict outcomes or responses to interventions

You MAY:
- Define intervention types at a structural level (categories, tags)
- Define intervention activation conditions (abstract triggers)
- Define timing rules (daily, event-driven, scheduled)
- Define duration, decay, or reset patterns
- Define evaluation metrics (structural signals only)
- Specify integration hooks with TQP Core (abstract)

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the Intervention Engine
- Scope: structural representation of triggers, timing, scheduling, and activation
- Boundaries: not psychological, not therapeutic, not behavioral
- High-level description of intervention flow and signals
- Abstract interactions with TQP Core and other modules

Tone: engineering-grade, non-medical.

-------------------------
spec.md requirements
-------------------------
Provide a full engineering specification including:

1. Intervention representation (identifiers, categories, metadata)
2. Activation rules (threshold-based, time-based, event-based)
3. Schedules and cadence definitions
4. Intervention lifecycle states (armed, active, expired)
5. Structural effects (abstract signals; no content)
6. Update cycle sequencing (activation → duration → decay)
7. Integration hooks for receiving and emitting signals
8. Module constraints and validation rules
9. Error handling for invalid triggers or timing
10. Extensibility for future intervention categories

This must read like a NASA systems engineering spec, not a behavioral or medical paper.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- Why an intervention subsystem is needed in long-duration mission simulations
- Principles of abstract intervention modeling (state machines, triggers, activation logic)
- How modular intervention design prevents contamination of behavioral or physiological modules
- Why interventions must be represented structurally rather than semantically

Prohibited:
- Therapeutic or clinical explanations
- Emotional or cognitive descriptions
- Behavioral interpretations

-------------------------
data_contract.md requirements
-------------------------
Define strictly:
- Inputs this module receives (abstract signals, thresholds, time-step data)
- Outputs it produces (intervention activation flags, structural state changes)
- Timing/granularity of data exchange
- Data shape and constraints in pseudocode form
- Validity rules for downstream consumers

You MUST NOT:
- Describe what interventions “mean”
- Describe psychological effects

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Guidance for implementing a clean intervention subsystem
- Recommended data structures (state machines, registries)
- Constraints for preventing semantic contamination
- Notes on scalability for multiple simultaneous interventions
- Versioning and extension strategy
- Risks to architectural purity

Do NOT reference specific programming languages.

============================================================
STYLE REQUIREMENTS
============================================================

- Technical, engineering tone
- No psychological concepts
- No emotional vocabulary
- No narrative examples
- No references to code implementation
- Complete and self-contained

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
