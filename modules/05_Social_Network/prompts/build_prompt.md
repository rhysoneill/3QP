You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 05: Social Network & Clique Formation.

This module defines the structural and computational mechanisms describing interpersonal ties, relationship strengths, clique formation dynamics, and social drift patterns in small crews. It MUST remain abstract and mechanistic, with NO psychological, emotional, or narrative content.

============================================================
SCOPE OF THIS MODULE
============================================================

Your output must produce FIVE files:
1. README.md
2. spec.md
3. theory_basis.md
4. data_contract.md
5. implementation_notes.md

You MUST NOT:
- Generate code
- Generate tests
- Describe emotional states
- Describe behavioral outcomes
- Create narrative or mission examples
- Define cognitive or stressor logic
- Define interventions or performance effects

You ARE defining a purely structural and computational subsystem.

This module is about ties, weights, adjacency, cliques, drift, and change rules — NOT subjective or behavioral meaning.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Infer internal logic of TQP Core, BDI, Physiology, Stressors, or Interventions
- Describe why ties strengthen/weaken in psychological terms
- Create situational examples
- Introduce emotional or cognitive states

You MAY:
- Define network structures (nodes, edges, weights)
- Define functions that modify ties (mechanistic drift)
- Define clique identification and evolution rules
- Define metrics used by downstream modules
- Define time-update sequencing within the network subsystem

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the Social Network module
- Scope: structural graph modeling, tie evolution rules, clique emergence
- Boundaries: not psychological, not emotional, not behavioral
- High-level flow of social graph updates
- Abstract description of network output to the rest of 3QP

Tone: engineering-grade, structural, non-interpretive.

-------------------------
spec.md requirements
-------------------------
Provide a complete engineering specification including:

1. Representation of the social graph  
2. Definition of nodes, edges, weights, and metadata  
3. Tie-update mechanisms (abstract functions)  
4. Drift processes (strengthening, weakening, stabilization)  
5. Clique detection and persistence modeling  
6. Social fragmentation / cohesion metrics (structural only)  
7. Update cycle sequencing and timing  
8. Integration hooks with TQP Core (abstract only)  
9. Error handling for unstable graphs  
10. Constraints, assumptions, and scalability considerations  

Must read like a structural network-science subsystem specification.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- The network-science principles underlying the module  
- Why small-group social network modeling is essential for third-quarter research  
- The rationale behind structural modeling (not psychological interpretation)  
- How modular graph models enforce scientific clarity  

Prohibited:  
- Psychology  
- Emotion  
- Behavioral narratives  
- Crew scenarios  

-------------------------
data_contract.md requirements
-------------------------
Define ONLY:
- Inputs this module receives (abstract signals such as “interaction intensity,” “update tick”)
- Outputs it produces (graph structure, weights, clique indicators)
- Timing/granularity of exchanges (per time-step)
- Data types and constraints in pseudocode forms
- Validity rules for downstream use

Do NOT include any behavioral explanations of graph changes.

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Guidance on constructing the subsystem during implementation
- Suggested data structures (adjacency matrix, edge list, etc.)
- Maintaining stability, normalization, and drift boundaries
- Versioning and extension strategies
- Risks to architectural integrity if psychological or narrative content is introduced

Do NOT reference any programming language or code.

============================================================
STYLE REQUIREMENTS
============================================================

- Precise engineering tone
- No narrative or fictional examples
- No psychological vocabulary
- No emotional content
- No placeholders
- No references to code
- Fully self-contained and deterministic

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
