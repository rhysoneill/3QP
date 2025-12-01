You are the dedicated systems architect for the 3QP Project (Third-Quarter Phenomenon Behavioral Twin). Your task is to fully generate the architectural documentation for Module 09: Language & Log Output System.

This module defines the structured logging and output specification for all 3QP modules. It governs how internal states, transitions, events, and subsystem outputs are captured, stored, serialized, summarized, and exported for downstream analysis. It MUST remain structurally and architecturally focused, with NO narrative generation, psychological language, or interpretation.

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
- Generate narrative logs or example story-like output
- Interpret agent behavior in any way
- Produce psychological or emotional descriptors
- Reference the internal mechanics of other modules
- Generate code or tests

The module concerns ONLY data structures, formats, serialization patterns, and logging rules.

============================================================
MODULE ISOLATION RULES
============================================================

You may NOT:
- Offer interpretations or summaries of logs
- Introduce semantic or narrative meaning to logs
- Describe how logs relate to emotional, behavioral, or cognitive phenomena
- Reference specific events or scenarios
- Inspect or describe internal logic of other modules

You MAY:
- Define log types (state logs, event logs, cycle logs)
- Define schemas and required fields
- Define serialization patterns (JSON-like, dictionary-like)
- Define log rotation, retention, and batching concepts
- Define the structure of language output (only formats, not content)

============================================================
FILE REQUIREMENTS
============================================================

-------------------------
README.md requirements
-------------------------
Include:
- Purpose of the Logging System module
- Scope: structured recording of 3QP module outputs
- Boundaries: no narrative, no behavioral interpretation
- Summary of log categories and structures
- Abstract interactions with the TQP Core and other modules

Tone: engineering-grade, format-focused.

-------------------------
spec.md requirements
-------------------------
Provide a complete logging architecture specification including:

1. Log categories (internal state, events, metrics, update cycles)
2. Format specifications (field structure, naming conventions)
3. Log granularity and timing rules
4. Data schemas for each log category
5. Batch processing and compression constraints
6. Log lifecycle (creation → rotation → retention → export)
7. Integration hooks with TQP Core for time-step alignment
8. Error handling for malformed or missing logs
9. Extensibility for new log types
10. Requirements for downstream researchers (readability, consistency)

This must resemble NASA systems log specifications.

-------------------------
theory_basis.md requirements
-------------------------
Explain:
- The principles of structured logging in simulation environments
- Why deterministic logging is required for scientific reproducibility
- How structured output enables later narrative reconstruction (not performed here)
- Why logging must be strictly separated from psychological or behavioral interpretation

Prohibited:
- Emotional or narrative language
- Case studies or examples
- Behavioral explanations

-------------------------
data_contract.md requirements
-------------------------
Define ONLY:
- Inputs received from modules (abstract signals like “state update object,” “event record”)
- Outputs produced by the logger (structured log artifacts)
- Timing of log production (per time-step, per event)
- Data shapes defined in pseudocode
- Validity checks (required fields, timestamps)

You MUST NOT:
- Describe the internal logic of the modules providing the data
- Include any example outputs with narrative or behavioral meaning

-------------------------
implementation_notes.md requirements
-------------------------
Provide:
- Recommended architectural patterns (append-only logs, ring buffers, structured serialization)
- Tips for ensuring log determinism across runs
- Requirements for file organization
- Versioning and extension considerations
- Safeguards to prevent semantic or narrative leakage into logs

Do NOT reference specific programming languages.

============================================================
STYLE REQUIREMENTS
============================================================

- Technical, engineering tone
- No psychological terms
- No narrative examples or sample logs
- No placeholders
- No references to implementation code
- Complete and self-contained

============================================================
BEGIN OUTPUT
============================================================

Generate all five files as separate clearly labeled sections.
