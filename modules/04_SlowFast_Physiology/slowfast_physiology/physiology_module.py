"""
Main PhysiologyModule implementation.

Integrates slow-time engine, fast-time engine, and coupling manager
to provide the complete slow-fast physiology model.
"""

from typing import List
from .types import (
    PhysiologyState,
    PhysiologyParameters,
    PhysiologyInitConfig,
    SlowTimeInput,
    FastTimeInput,
    SlowTimeOutput,
    FastTimeOutput,
    PhysiologyDerivedOutput,
    SlowTimeState,
    FastTimeState,
    StatusCode
)
from .slow_time_engine import SlowTimeEngine
from .fast_time_engine import FastTimeEngine
from .coupling_manager import CouplingManager


class PhysiologyModule:
    """
    Main Slow-Fast Physiology Module.
    
    Implements the complete hybrid dynamical system with slow and fast
    timescales according to Module 04 specification.
    """
    
    def __init__(self, config: PhysiologyInitConfig):
        """
        Initialize the physiology module.
        
        Args:
            config: Complete initialization configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        self._validate_config(config)
        
        # Store configuration
        self.params = config.parameters
        self.timescale = config.timescale_config
        self.state = config.initial_state
        
        # Initialize engines
        self.slow_engine = SlowTimeEngine(self.params)
        self.fast_engine = FastTimeEngine(self.params)
        self.coupling = CouplingManager(self.params)
        
        # Initialize derived quantities
        self.state = self.coupling.update_derived_state(self.state)
        
        # Storage for fast-time states in current epoch
        self._fast_states_buffer: List[PhysiologyState] = []
        
        # Module status
        self._status = StatusCode.PHYS_OK
    
    def _validate_config(self, config: PhysiologyInitConfig):
        """
        Validate initialization configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Validate state
        valid, error_msg = config.initial_state.validate()
        if not valid:
            raise ValueError(f"Invalid initial state: {error_msg}")
        
        # Validate parameters
        valid, error_msg = config.parameters.validate()
        if not valid:
            raise ValueError(f"Invalid parameters: {error_msg}")
        
        # Validate A_resp <= A_max
        if config.initial_state.A_resp > config.parameters.A_max:
            raise ValueError(
                f"Initial A_resp ({config.initial_state.A_resp}) "
                f"exceeds A_max ({config.parameters.A_max})"
            )
    
    def fast_time_step(
        self,
        fast_input: FastTimeInput
    ) -> FastTimeOutput:
        """
        Execute one fast-time step.
        
        Args:
            fast_input: Fast-time input data
            
        Returns:
            Fast-time output with updated state
        """
        # Update timestamp
        self.state.t_fast = fast_input.t_fast
        
        # Apply acute input if present
        if fast_input.I_fast > 0.0:
            self.state, status_acute = self.fast_engine.apply_acute_input(
                self.state,
                fast_input.I_fast
            )
            if status_acute != StatusCode.PHYS_OK:
                self._status = status_acute
        
        # Perform relaxation update
        self.state, status_relax = self.fast_engine.update(
            self.state,
            self.timescale.dt_fast
        )
        
        # Combine status codes (most severe wins)
        if status_relax == StatusCode.PHYS_NUMERIC_ERROR:
            self._status = StatusCode.PHYS_NUMERIC_ERROR
        elif status_relax == StatusCode.PHYS_STATE_CLAMP and self._status == StatusCode.PHYS_OK:
            self._status = StatusCode.PHYS_STATE_CLAMP
        
        # Update derived quantities
        self.state = self.coupling.update_derived_state(self.state)
        
        # Store state in buffer for epoch aggregation
        # Create a copy to avoid mutation issues
        state_copy = PhysiologyState(
            C_base=self.state.C_base,
            L_cum=self.state.L_cum,
            R_cap=self.state.R_cap,
            A_resp=self.state.A_resp,
            L_trans=self.state.L_trans,
            xi=self.state.xi,
            gamma_drift=self.state.gamma_drift,
            L_total=self.state.L_total,
            C_eff=self.state.C_eff,
            t_slow=self.state.t_slow,
            t_fast=self.state.t_fast,
            epoch_number=self.state.epoch_number
        )
        self._fast_states_buffer.append(state_copy)
        
        # Create output
        fast_state = FastTimeState(
            A_resp=self.state.A_resp,
            L_trans=self.state.L_trans,
            xi=self.state.xi
        )
        
        output = FastTimeOutput(
            t_fast=fast_input.t_fast,
            state=fast_state,
            status=self._status
        )
        
        # Reset status for next step
        self._status = StatusCode.PHYS_OK
        
        return output
    
    def slow_time_step(
        self,
        slow_input: SlowTimeInput
    ) -> SlowTimeOutput:
        """
        Execute one slow-time step.
        
        This should be called after all fast-time steps in the epoch.
        
        Args:
            slow_input: Slow-time input data
            
        Returns:
            Slow-time output with updated state
        """
        # Update timestamp
        self.state.t_slow = slow_input.t_slow
        
        # Aggregate fast-time activity (optional - currently not used in slow update)
        # L_trans_avg = self.coupling.aggregate_fast_activity(self._fast_states_buffer)
        
        # Perform slow-time update
        self.state, status = self.slow_engine.update(
            self.state,
            slow_input.I_slow,
            self.timescale.dt_slow
        )
        
        self._status = status
        
        # Update derived quantities
        self.state = self.coupling.update_derived_state(self.state)
        
        # Increment epoch number
        self.state.epoch_number += 1
        
        # Update fast-time parameters for next epoch (slow→fast coupling)
        Delta_A, lambda_A = self.coupling.compute_slow_to_fast_coupling(self.state)
        self.fast_engine.set_coupling_params(Delta_A, lambda_A)
        
        # Clear fast-time buffer for next epoch
        self._fast_states_buffer.clear()
        
        # Create output
        slow_state = SlowTimeState(
            C_base=self.state.C_base,
            L_cum=self.state.L_cum,
            R_cap=self.state.R_cap,
            gamma_drift=self.state.gamma_drift
        )
        
        output = SlowTimeOutput(
            t_slow=slow_input.t_slow,
            state=slow_state,
            status=self._status
        )
        
        # Reset status for next step
        self._status = StatusCode.PHYS_OK
        
        return output
    
    def run_epoch(
        self,
        slow_input: SlowTimeInput,
        fast_inputs: List[FastTimeInput]
    ) -> tuple[SlowTimeOutput, List[FastTimeOutput]]:
        """
        Run a complete epoch (slow-time step with nested fast-time steps).
        
        Args:
            slow_input: Slow-time input for this epoch
            fast_inputs: List of fast-time inputs (length should be N_fast)
            
        Returns:
            (slow_time_output, list_of_fast_time_outputs)
        """
        # Validate input count
        if len(fast_inputs) != self.timescale.N_fast:
            raise ValueError(
                f"Expected {self.timescale.N_fast} fast inputs, "
                f"got {len(fast_inputs)}"
            )
        
        # Execute fast-time steps
        fast_outputs = []
        for fast_input in fast_inputs:
            output = self.fast_time_step(fast_input)
            fast_outputs.append(output)
        
        # Execute slow-time step
        slow_output = self.slow_time_step(slow_input)
        
        return slow_output, fast_outputs
    
    def get_state(self) -> PhysiologyState:
        """
        Get current physiological state (read-only).
        
        Returns:
            Current state
        """
        return self.state
    
    def get_derived_output(self) -> PhysiologyDerivedOutput:
        """
        Get current derived quantities.
        
        Returns:
            Derived output with L_total and C_eff
        """
        return PhysiologyDerivedOutput(
            t=self.state.t_fast,
            L_total=self.state.L_total,
            C_eff=self.state.C_eff
        )
    
    def get_parameters(self) -> PhysiologyParameters:
        """
        Get model parameters (read-only).
        
        Returns:
            Model parameters
        """
        return self.params
