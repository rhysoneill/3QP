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
# Module-Specific Instructions: 10_Validation

## Responsibilities
Implement validation harness:
- Cross-module tests
- Consistency checks
- Scientific KPIs
- 3QP curve validation

## Requirements
Use logs from Module 09 and metrics from Module 02.
Report validation results in structured formats.
# Module-Specific Instructions: 11_Roadmap

## Responsibilities
Generate internal planning artifacts:
- Future features
- Technical debt
- Release cycle notes

No code dependencies. Pure documentation generation.
