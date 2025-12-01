You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 06: BDI Cognitive Cycle.

This module defines the computational structure underlying agent Beliefs, Desires, and Intentions, along with the update cycle governing how these internal cognitive states evolve. It MUST remain purely architectural and mechanistic, with NO emotional, psychological, narrative, or behavioral detail.

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
- Describe emotions or stress responses
- Define physiological mechanisms
- Define social behaviors
- Describe interventions or coping
- Create mission or crew scenarios
- Introduce psychological narratives

This module concerns ONLY the computational architecture of BDI reasoning.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Define internal algorithms of other modules
- Describe BDI → behavior mapping (behavior is out of scope)
- Integrate BDI with physiology, stressors, or the social network
- Assume cognitive biases, heuristics, or psychological constructs
- Use language describing affect, motivation, or personality

You MAY:
- Define belief containers
- Define desire representations
- Define intention structures
- Define the sequencing of BDI update cycles
- Define data that flows into/out of the BDI module
- Define abstract relationships (e.g., beliefs influence desires)

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the BDI module within 3QP
- Scope (belief, desire, intention representations; update cycles)
- Boundaries (not emotion, not behavior, not stress, not cognition beyond BDI)
- High-level flow of the BDI update cycle
- How BDI interacts *abstractly* with the TQP Core

Tone: engineering, formal, non-psychological.

-------------------------
spec.md requirements
-------------------------
Provide a full engineering specification including:

1. Representations of:
   - Beliefs
   - Desires
   - Intentions

2. Rules governing:
   - Belief update (abstract only)
   - Desire formation (abstract only)
   - Intention selection (abstract only)

3. BDI cycle sequencing and timing  
4. State persistence and memory constraints  
5. Hooks for TQP Core integration (abstract, no implementation details)  
6. Constraints (e.g., no emotional states, no behavioral outputs)  
7. Error handling for malformed belief/desire structures  
8. Extensibility (e.g., additional cognitive layers in future modules)

The document must read like a system architecture specification, not a psychology paper.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- Why BDI is chosen as the core cognitive architecture for 3QP
- The computational principles behind BDI (symbolic reasoning, structured state)
- How modular BDI architectures support long-duration mission modeling
- Why cognition must be isolated from emotion, physiology, and behavior

Prohibited:
- Psychological explanations
- Narrative examples
- Emotional or affective content

-------------------------
data_contract.md requirements
-------------------------
Define strictly:
- What information the BDI module receives (e.g., abstract environment signals, state updates)
- What information the BDI module emits (belief sets, selected intentions, etc.)
- Timing/granularity of BDI outputs
- Data shapes and constraints in pseudocode form
- Validity rules for downstream modules

Do NOT describe how beliefs → behavior or beliefs → emotion.

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Implementation guidance for the cognition subsystem
- Recommendations for data structures (symbolic lists, graphs, logic containers)
- Notes on preserving architectural separation
- Error containment strategies
- Versioning considerations during future extensions

Do NOT reference code or programming languages.

============================================================
STYLE REQUIREMENTS
============================================================

- Precise, engineering tone
- No narrative or fictional mission examples
- No emotional or psychological vocabulary
- No placeholders
- No references to implementation code
- Fully self-contained and deterministic

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
