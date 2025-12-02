"""
Validation hooks interface.

Defines the interface that modules must implement to support validation,
and provides adapter pattern for integrating with existing modules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from .types import (
    ModuleInitializationStatus,
    ModuleStateSnapshot,
    ConsistencySignals,
    IntegrityIndicators,
)


class ValidationHooks(ABC):
    """
    Abstract interface for module validation hooks.
    
    Modules implement these methods to provide validation data
    to the validation subsystem.
    """
    
    @abstractmethod
    def validate_initialization(self) -> ModuleInitializationStatus:
        """
        Validate module initialization status.
        
        Returns:
            Initialization status including success/failure and diagnostics
        """
        pass
    
    @abstractmethod
    def validate_state(self) -> ModuleStateSnapshot:
        """
        Capture current module state snapshot for validation.
        
        Returns:
            Complete state snapshot including consistency and integrity signals
        """
        pass
    
    @abstractmethod
    def validate_output(self, time_step: int) -> Dict[str, Any]:
        """
        Validate module output for a given time step.
        
        Args:
            time_step: Time step to validate output for
            
        Returns:
            Dictionary with output_valid, output_data, and validation_errors
        """
        pass
    
    @abstractmethod
    def get_consistency_signals(self) -> ConsistencySignals:
        """
        Get current consistency signals from module.
        
        Returns:
            Consistency signals including violations
        """
        pass
    
    @abstractmethod
    def get_integrity_metrics(self) -> IntegrityIndicators:
        """
        Get current data integrity metrics from module.
        
        Returns:
            Integrity indicators including completeness and compliance
        """
        pass


class ModuleValidationAdapter:
    """
    Adapter for modules that don't natively implement ValidationHooks.
    
    Provides default implementations and best-effort validation
    for modules without explicit validation support.
    """
    
    def __init__(self, module_id: str, module_instance: Any):
        """
        Initialize adapter for a module.
        
        Args:
            module_id: Unique module identifier
            module_instance: The module instance to adapt
        """
        self.module_id = module_id
        self.module = module_instance
    
    def validate_initialization(self) -> ModuleInitializationStatus:
        """
        Provide default initialization validation.
        
        Checks if module has basic required attributes.
        """
        from datetime import datetime
        from .types import InitializationResult
        
        # Check if module has required methods
        has_update = hasattr(self.module, 'update')
        
        return ModuleInitializationStatus(
            module_id=self.module_id,
            module_name=getattr(self.module, '__class__.__name__', self.module_id),
            module_version=getattr(self.module, '__version__', '0.0.0'),
            initialization_result=InitializationResult.SUCCESS if has_update else InitializationResult.FAILURE,
            timestamp=datetime.now(),
            configuration_valid=True,
            dependencies_satisfied=True,
            interfaces_ready=has_update,
            error_messages=[] if has_update else ["Module missing update method"]
        )
    
    def validate_state(self) -> ModuleStateSnapshot:
        """
        Provide default state snapshot validation.
        
        Uses basic introspection to capture module state.
        """
        from datetime import datetime
        import hashlib
        import json
        
        # Extract state data
        state_data = {}
        if hasattr(self.module, '__dict__'):
            for key, value in self.module.__dict__.items():
                if not key.startswith('_'):
                    try:
                        # Only include serializable values
                        json.dumps(value)
                        state_data[key] = value
                    except (TypeError, ValueError):
                        # Skip non-serializable values
                        pass
        
        # Compute state hash
        state_str = json.dumps(state_data, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()
        
        # Default consistency signals
        consistency = ConsistencySignals(
            internal_consistency_valid=True,
            referential_integrity_valid=True,
            constraint_violations=[],
            invariant_violations=[]
        )
        
        # Default integrity indicators
        integrity = IntegrityIndicators(
            data_completeness=1.0 if state_data else 0.0,
            corruption_detected=False,
            schema_compliance=True,
            null_field_count=0,
            out_of_range_count=0
        )
        
        return ModuleStateSnapshot(
            module_id=self.module_id,
            time_step=0,  # Default, should be updated by caller
            timestamp=datetime.now(),
            state_version=1,
            state_hash=state_hash,
            state_data=state_data,
            consistency_signals=consistency,
            integrity_indicators=integrity
        )
    
    def validate_output(self, time_step: int) -> Dict[str, Any]:
        """
        Provide default output validation.
        
        Args:
            time_step: Time step to validate
            
        Returns:
            Basic output validation result
        """
        return {
            "module_id": self.module_id,
            "time_step": time_step,
            "output_valid": True,
            "output_data": {},
            "validation_errors": []
        }
    
    def get_consistency_signals(self) -> ConsistencySignals:
        """
        Provide default consistency signals.
        
        Returns:
            Default signals indicating no violations
        """
        return ConsistencySignals(
            internal_consistency_valid=True,
            referential_integrity_valid=True,
            constraint_violations=[],
            invariant_violations=[]
        )
    
    def get_integrity_metrics(self) -> IntegrityIndicators:
        """
        Provide default integrity metrics.
        
        Returns:
            Default metrics indicating no issues
        """
        return IntegrityIndicators(
            data_completeness=1.0,
            corruption_detected=False,
            schema_compliance=True,
            null_field_count=0,
            out_of_range_count=0
        )
