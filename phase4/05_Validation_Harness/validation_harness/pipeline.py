"""
Validation pipeline orchestration.

Provides the main entry point for running validation scenarios,
coordinating fixture retrieval and check execution.
"""

from .config import ValidationRunConfig
from .fixtures import get_fixture_for_scenario
from .checks import perform_all_checks, ValidationRunResult


def run_validation(run_config: ValidationRunConfig) -> ValidationRunResult:
    """
    Run a complete validation using the provided configuration.
    
    This is the main entry point for validation execution. It:
    1. Validates the run configuration
    2. Retrieves fixture data for the scenario
    3. Executes all validation checks
    4. Returns aggregated results
    
    Args:
        run_config: ValidationRunConfig specifying what to validate
    
    Returns:
        ValidationRunResult containing all check results
    
    Raises:
        ValueError: If run_config is invalid or scenario not found
    """
    # Validate the configuration
    is_valid, error_msg = run_config.validate()
    if not is_valid:
        raise ValueError(f"Invalid ValidationRunConfig: {error_msg}")
    
    # Retrieve fixture data for the scenario
    try:
        encoded_states, pattern_results, trajectory_classification = (
            get_fixture_for_scenario(run_config.scenario.scenario_id)
        )
    except ValueError as e:
        raise ValueError(
            f"Failed to retrieve fixture for scenario "
            f"'{run_config.scenario.scenario_id}': {e}"
        )
    
    # Perform all validation checks
    result = perform_all_checks(
        run_config=run_config,
        encoded_states=encoded_states,
        pattern_results=pattern_results,
        trajectory_result=trajectory_classification,
    )
    
    return result
