"""
Adapter layer for external validation integration.

Provides protocol-based integration with Module 10 Validation System
without requiring the module to exist. Uses dependency injection
pattern for extensibility.
"""

from typing import Protocol

from .checks import ValidationRunResult
from .reporting import render_dict_report


class ExternalValidationClient(Protocol):
    """
    Protocol defining the interface for external validation clients.
    
    Any external validation implementation should match this interface
    to be compatible with the validation harness.
    """
    
    def submit_validation_outcome(self, payload: dict) -> None:
        """
        Submit a validation outcome to external validation system.
        
        Args:
            payload: Dictionary containing validation result data
        """
        ...


class NoOpExternalValidationClient:
    """
    No-operation external validation client.
    
    This default implementation does nothing, allowing the harness
    to function without an external validation system present.
    """
    
    def submit_validation_outcome(self, payload: dict) -> None:
        """
        No-op implementation - does nothing.
        
        Args:
            payload: Dictionary containing validation result data (ignored)
        """
        pass


def get_default_validation_client() -> ExternalValidationClient:
    """
    Get the default external validation client.
    
    Returns:
        ExternalValidationClient instance (currently NoOpExternalValidationClient)
    
    TODO: Integrate with Module 10 Validation System
    
    When Module 10 is available, update this factory to:
    1. Import from modules.10_Validation.validation
    2. Create appropriate validator instance
    3. Handle configuration
    
    Example future implementation:
        try:
            from modules.10_Validation.validation import ValidationEngine
            engine = ValidationEngine()
            return RealValidationClient(engine)
        except ImportError:
            return NoOpExternalValidationClient()
    """
    return NoOpExternalValidationClient()


def submit_run_for_external_validation(
    client: ExternalValidationClient,
    result: ValidationRunResult,
) -> None:
    """
    Submit a validation run result to external validation system.
    
    This is a convenience function that:
    1. Converts the ValidationRunResult to a dict payload
    2. Sends it to the external validation client
    
    Args:
        client: ExternalValidationClient instance to use
        result: ValidationRunResult to submit
    """
    payload = render_dict_report(result)
    client.submit_validation_outcome(payload)


# Example of how to create a real validation client adapter:
# (This is commented out since Module 10 may not exist yet)
#
# class Module10ValidationClient:
#     """Adapter for Module 10 Validation System."""
#     
#     def __init__(self, validation_engine):
#         """
#         Initialize with Module 10 validation engine.
#         
#         Args:
#             validation_engine: Validation engine instance from Module 10
#         """
#         self.engine = validation_engine
#     
#     def submit_validation_outcome(self, payload: dict) -> None:
#         """
#         Submit validation outcome using Module 10.
#         
#         Args:
#             payload: Dictionary containing validation result data
#         """
#         self.engine.record_validation(
#             validation_type="phase4_harness",
#             run_id=payload["run_id"],
#             scenario_id=payload["scenario_id"],
#             passed=payload["passed"],
#             details=payload,
#         )
