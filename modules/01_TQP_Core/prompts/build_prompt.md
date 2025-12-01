You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). You are responsible for generating a complete, standalone specification for Module 01: TQP Core — the Deep Internal Engine.

This prompt defines strict isolation boundaries, output formatting, and scientific requirements. Follow them precisely.

============================================================
MODULE ISOLATION RULES
============================================================

1. You are ONLY allowed to construct Module 01: TQP Core.
2. You may NOT design or speculate about:
   - Social network models
   - Physiological models
   - Stressors
   - BDI logic
   - Interventions
   - Logging systems
   - Validation systems
   - Mission-specific events
3. You MAY reference those modules ONLY as abstract external systems that exchange data via future data_contract.md files.
4. You MUST NOT create or describe the internals of any other module.
5. All reasoning, algorithms, variables, and mechanisms must be contained entirely within TQP Core.
6. The module must be implementable as a standalone component with no required knowledge of other module internals.

============================================================
SCIENTIFIC AND ENGINEERING CONSTRAINTS
============================================================

The TQP Core is:
- The global internal update engine that drives agent state evolution.
- The execution kernel for time-steps.
- The mechanism that synchronizes slow vs fast processes.
- The source of emergent, causal trajectories.
- NOT a behavioral theory module.
- NOT a psychology model module.
- NOT an intervention system.

The TQP Core must support:
- Deterministic and stochastic updates
- Agent memory update calls
- State variable progression
- Subsystem data exchange hooks
- A complete internal simulation loop
- Temporal segmentation (daily, weekly, intra-day)

The language must be:
- Technical
- Auditable
- Mechanistic
- Clear enough for a NASA BHP engineering reviewer

Avoid narrative language entirely.

============================================================
OUTPUT FORMAT REQUIREMENTS
============================================================

You must generate the following files as separate clearly titled sections in your output:

1. README.md  
2. spec.md  
3. theory_basis.md  
4. data_contract.md  
5. implementation_notes.md  

Do NOT merge them.  
Do NOT skip any.  
Each must be fully self-contained.

============================================================
FILE CONTENT REQUIREMENTS
============================================================

-------------------------
README.md
-------------------------
Provide:
- Purpose of the module
- Scope
- Role within 3QP
- High-level description of its responsibilities
- Clear boundaries showing what this module does NOT do
- Expected interfaces (in abstract terms only)

Tone: concise, engineering-grade.

-------------------------
spec.md
-------------------------
Provide a detailed technical specification including:

1. Overview of the internal engine  
2. Agent internal state model (variables, containers, representations)  
3. Core update cycle  
4. Time-step semantics  
5. Slow–fast process reconciliation (abstracted)  
6. Hooks for external modules (but no internal details of those modules)  
7. Determinism vs stochasticity  
8. Error handling  
9. Computational efficiency considerations  
10. Extensibility for later modules  

This must be written as a specification a NASA software engineer could implement.

-------------------------
theory_basis.md
-------------------------
Clarify:
- The theoretical principles that justify having a central engine (NOT psychological theory)
- System architecture foundations (discrete-time simulation, hybrid dynamical systems, microservice coordination)
- Why a unified internal kernel is needed for Third-Quarter emergence

Do NOT include behavioral theory here.

-------------------------
data_contract.md
-------------------------
Define ONLY:
- What data the TQP Core EXPECTS to receive from other modules
- What data the TQP Core EMITS to other modules
- Update frequencies
- Validity constraints
- Data types or structures (engineering-level pseudocode only)

Do NOT speculate about other modules' internal logic.

-------------------------
implementation_notes.md
-------------------------
Provide:
- Recommended implementation path
- Order of operations
- Recommended data structures and programming patterns
- Notes for maintaining module purity
- Future extension stubs
- Failure mode considerations

This is for implementers, not reviewers.

============================================================
OUTPUT RULES
============================================================

- Write in a precise, technical tone.
- No narrative elements.
- No hypothetical astronaut stories.
- No emotional language.
- No system-wide behavior; only TQP Core.
- All outputs must be deterministic and complete.
- No placeholders like “TBD”.

============================================================
BEGIN NOW
============================================================

Generate all five files.
