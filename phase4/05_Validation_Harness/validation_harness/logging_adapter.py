"""
Adapter layer for logging integration.

Provides protocol-based integration with Module 09 Logging System
without requiring the module to exist. Uses dependency injection
pattern for extensibility.
"""

from typing import Protocol

from .checks import ValidationRunResult
from .reporting import render_dict_report


class LoggingClient(Protocol):
    """
    Protocol defining the interface for logging clients.
    
    Any logging implementation should match this interface to be
    compatible with the validation harness.
    """
    
    def log_validation_result(self, payload: dict) -> None:
        """
        Log a validation result.
        
        Args:
            payload: Dictionary containing validation result data
        """
        ...


class NoOpLoggingClient:
    """
    No-operation logging client.
    
    This default implementation does nothing, allowing the harness
    to function without a logging system present.
    """
    
    def log_validation_result(self, payload: dict) -> None:
        """
        No-op implementation - does nothing.
        
        Args:
            payload: Dictionary containing validation result data (ignored)
        """
        pass


def get_default_logging_client() -> LoggingClient:
    """
    Get the default logging client.
    
    Returns:
        LoggingClient instance (currently NoOpLoggingClient)
    
    TODO: Integrate with Module 09 Logging System
    
    When Module 09 is available, update this factory to:
    1. Import from modules.09_Logging_System.logging_system
    2. Create appropriate client instance
    3. Handle configuration
    
    Example future implementation:
        try:
            from modules.09_Logging_System.logging_system import create_logger
            logger = create_logger("validation_harness")
            return RealLoggingClient(logger)
        except ImportError:
            return NoOpLoggingClient()
    """
    return NoOpLoggingClient()


def log_run_result(
    logging_client: LoggingClient,
    result: ValidationRunResult,
) -> None:
    """
    Log a validation run result using the provided logging client.
    
    This is a convenience function that:
    1. Converts the ValidationRunResult to a dict payload
    2. Sends it to the logging client
    
    Args:
        logging_client: LoggingClient instance to use
        result: ValidationRunResult to log
    """
    payload = render_dict_report(result)
    logging_client.log_validation_result(payload)


# Example of how to create a real logging client adapter:
# (This is commented out since Module 09 may not exist yet)
#
# class Module09LoggingClient:
#     """Adapter for Module 09 Logging System."""
#     
#     def __init__(self, logger):
#         """
#         Initialize with Module 09 logger.
#         
#         Args:
#             logger: Logger instance from Module 09
#         """
#         self.logger = logger
#     
#     def log_validation_result(self, payload: dict) -> None:
#         """
#         Log validation result using Module 09.
#         
#         Args:
#             payload: Dictionary containing validation result data
#         """
#         self.logger.log_event(
#             event_type="validation_run",
#             data=payload,
#             severity="INFO" if payload["passed"] else "WARNING",
#         )
