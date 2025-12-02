# 3QP Module Implementation Prompt (Universal Core)

You are implementing one module within the 3QP system.  
Follow these instructions precisely.

## Your role
Implement this module strictly according to:
- its spec.md
- its theory_basis.md
- its data_contract.md
- its implementation_notes.md
- its documented dependencies within the architecture

Do not alter architecture decisions.  
Do not invent new abstractions.  
Stay within the module’s defined responsibilities.

## Coding requirements
- Use clear, modular Python code.  
- Adhere to the system-wide architecture patterns defined in Module 03_Architecture.  
- All classes and functions must match names and shapes defined in data_contract.md.  
- Implement all required interfaces and lifecycle methods.
- Include TODO comments for any externally dependent sections not implemented yet.

## Integration rules
- Respect all upstream dependencies; import only allowed components.
- Do not reference downstream modules.
- Ensure outputs exactly match the data contract schemas.
- Emit logging events using the Logging_System interface.
- Support validation hooks defined in module 10_Validation.

## Scientific and behavioral correctness
- Implement theory-driven logic as described in theory_basis.md.
- Preserve constraints, thresholds, and causal relationships.
- Do not simplify mechanisms unless explicitly allowed.

## Testing expectations
- Write basic self-tests for internal functions.
- Provide example input/output pairs whenever appropriate.
- Ensure error-handling paths match the documented failure modes.

## Deliverables
Produce:
- Python module code
- Any required helper classes
- Internal documentation
- Inline explanations only when necessary for clarity

Stop when the module is complete and ready for integration.

# Now load the module-specific instructions below.
# Module-Specific Instructions: 02_Breakthrough_Impact

## Responsibilities
Compute which interventions flatten the 3QP curve.
Perform scenario comparisons and impact analyses.

## Requirements
Use outputs from:
- Physiology
- Social Network
- BDI Cycle
- Stressor Model
- Interventions

Produce structured impact scores as defined in data_contract.md.
