"""
Module registry and execution management.

This module handles registration, ordering, and invocation of external modules.
"""

from typing import Dict, List
from .module_interface import ModuleRegistration
from .types import ProcessType


class ModuleRegistry:
    """
    Registry for managing module registration and execution order.
    """
    
    def __init__(self):
        self.modules: Dict[str, ModuleRegistration] = {}
        self.slow_modules: List[ModuleRegistration] = []
        self.fast_modules: List[ModuleRegistration] = []
        self._sorted = False
    
    def register(self, registration: ModuleRegistration) -> None:
        """
        Register a module with the core.
        
        Args:
            registration: Module registration data
            
        Raises:
            ValueError: If module_id is already registered
        """
        if registration.module_id in self.modules:
            raise ValueError(f"Module '{registration.module_id}' is already registered")
        
        self.modules[registration.module_id] = registration
        
        if registration.process_type == ProcessType.SLOW:
            self.slow_modules.append(registration)
        else:
            self.fast_modules.append(registration)
        
        self._sorted = False
    
    def _ensure_sorted(self) -> None:
        """Sort modules by execution priority (higher priority first)."""
        if not self._sorted:
            self.slow_modules.sort(key=lambda m: m.execution_priority, reverse=True)
            self.fast_modules.sort(key=lambda m: m.execution_priority, reverse=True)
            self._sorted = True
    
    def get_module(self, module_id: str) -> ModuleRegistration:
        """
        Get a registered module by ID.
        
        Args:
            module_id: Module identifier
            
        Returns:
            ModuleRegistration
            
        Raises:
            KeyError: If module is not registered
        """
        return self.modules[module_id]
    
    def get_slow_modules(self) -> List[ModuleRegistration]:
        """Get all slow modules in priority order."""
        self._ensure_sorted()
        return self.slow_modules.copy()
    
    def get_fast_modules(self) -> List[ModuleRegistration]:
        """Get all fast modules in priority order."""
        self._ensure_sorted()
        return self.fast_modules.copy()
    
    def get_all_modules(self) -> List[ModuleRegistration]:
        """Get all modules."""
        return list(self.modules.values())
    
    def validate_dependencies(self) -> None:
        """
        Validate that all module dependencies are registered and have appropriate priority.
        
        Raises:
            ValueError: If dependencies are invalid
        """
        for module_id, registration in self.modules.items():
            dependencies = registration.module.get_dependencies()
            
            for dep_id in dependencies:
                if dep_id not in self.modules:
                    raise ValueError(
                        f"Module '{module_id}' depends on unregistered module '{dep_id}'"
                    )
                
                dep_registration = self.modules[dep_id]
                
                # Dependencies should have higher priority (execute first)
                if dep_registration.execution_priority < registration.execution_priority:
                    raise ValueError(
                        f"Module '{module_id}' depends on '{dep_id}' but '{dep_id}' "
                        f"has lower priority ({dep_registration.execution_priority} < "
                        f"{registration.execution_priority})"
                    )
