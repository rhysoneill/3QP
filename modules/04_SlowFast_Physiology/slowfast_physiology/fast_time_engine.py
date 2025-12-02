"""
Fast-time engine for physiological state updates.

Implements fast-time dynamics according to spec.md:
- Acute response triggering
- Fast-time relaxation dynamics
- Exponential decay processes
"""

import math
from .types import PhysiologyState, PhysiologyParameters, StatusCode


class FastTimeEngine:
    """
    Manages fast-time state updates.
    
    Implements dynamics for:
    - A_resp (acute response)
    - L_trans (transient load)
    - xi (relaxation state)
    """
    
    def __init__(self, params: PhysiologyParameters):
        """
        Initialize fast-time engine.
        
        Args:
            params: Model parameters
        """
        self.params = params
        # Cache for modulated parameters (set by coupling)
        self.Delta_A_effective = params.Delta_A_0
        self.lambda_A_effective = params.lambda_A
    
    def set_coupling_params(self, Delta_A: float, lambda_A: float):
        """
        Update fast-time parameters based on slow-time coupling.
        
        Called at the start of each epoch by coupling manager.
        
        Args:
            Delta_A: Modulated acute response sensitivity
            lambda_A: Modulated relaxation rate
        """
        self.Delta_A_effective = Delta_A
        self.lambda_A_effective = lambda_A
    
    def apply_acute_input(
        self,
        state: PhysiologyState,
        I_fast: float
    ) -> tuple[PhysiologyState, StatusCode]:
        """
        Apply acute stressor input.
        
        Equation: A_resp(t_0) = A_resp(t_0^-) + Δ_A * I_fast * (1 - ξ)
        
        Args:
            state: Current state
            I_fast: Fast-time stressor intensity
            
        Returns:
            (updated_state, status_code)
        """
        # Compute acute response increment
        delta_A = self.Delta_A_effective * I_fast * (1.0 - state.xi)
        
        # Apply increment
        new_A_resp = state.A_resp + delta_A
        
        # Create new state
        new_state = PhysiologyState(
            C_base=state.C_base,
            L_cum=state.L_cum,
            R_cap=state.R_cap,
            A_resp=new_A_resp,
            L_trans=state.L_trans,
            xi=state.xi,
            gamma_drift=state.gamma_drift,
            L_total=state.L_total,
            C_eff=state.C_eff,
            t_slow=state.t_slow,
            t_fast=state.t_fast,
            epoch_number=state.epoch_number
        )
        
        # Enforce A_resp constraint
        new_state, status = self._clamp_acute_response(new_state)
        
        return new_state, status
    
    def compute_derivatives(
        self,
        state: PhysiologyState
    ) -> tuple[float, float, float]:
        """
        Compute fast-time relaxation derivatives.
        
        Args:
            state: Current physiological state
            
        Returns:
            (dA_resp_dt, dL_trans_dt, dxi_dt)
        """
        # Acute response relaxation
        # dA_resp/dt = -λ_A * A_resp
        dA_resp_dt = -self.lambda_A_effective * state.A_resp
        
        # Transient load dynamics
        # dL_trans/dt = -λ_L * L_trans + μ * A_resp
        dL_trans_dt = (
            -self.params.lambda_L * state.L_trans
            + self.params.mu * state.A_resp
        )
        
        # Relaxation state dynamics
        # dxi/dt = λ_ξ * (1 - ξ)
        dxi_dt = self.params.lambda_xi * (1.0 - state.xi)
        
        return dA_resp_dt, dL_trans_dt, dxi_dt
    
    def update(
        self,
        state: PhysiologyState,
        dt: float
    ) -> tuple[PhysiologyState, StatusCode]:
        """
        Perform fast-time relaxation update.
        
        Uses analytic exponential solution for stability.
        
        Args:
            state: Current state
            dt: Time step size
            
        Returns:
            (updated_state, status_code)
        """
        # Use analytic exponential relaxation for A_resp
        # y(t + dt) = y(t) * exp(-λ * dt)
        decay_A = math.exp(-self.lambda_A_effective * dt)
        new_A_resp = state.A_resp * decay_A
        
        # Transient load has forcing term, use Forward Euler
        dL_trans_dt = (
            -self.params.lambda_L * state.L_trans
            + self.params.mu * state.A_resp
        )
        new_L_trans = state.L_trans + dL_trans_dt * dt
        
        # Relaxation state - analytic solution
        # xi(t) = 1 - (1 - xi_0) * exp(-λ_ξ * t)
        decay_xi = math.exp(-self.params.lambda_xi * dt)
        new_xi = 1.0 - (1.0 - state.xi) * decay_xi
        
        # Create new state
        new_state = PhysiologyState(
            C_base=state.C_base,
            L_cum=state.L_cum,
            R_cap=state.R_cap,
            A_resp=new_A_resp,
            L_trans=new_L_trans,
            xi=new_xi,
            gamma_drift=state.gamma_drift,
            L_total=state.L_total,
            C_eff=state.C_eff,
            t_slow=state.t_slow,
            t_fast=state.t_fast,
            epoch_number=state.epoch_number
        )
        
        # Enforce constraints
        new_state, status = self._clamp_state(new_state)
        
        return new_state, status
    
    def _clamp_acute_response(
        self,
        state: PhysiologyState
    ) -> tuple[PhysiologyState, StatusCode]:
        """
        Enforce A_resp constraint.
        
        Args:
            state: State to clamp
            
        Returns:
            (clamped_state, status_code)
        """
        status = StatusCode.PHYS_OK
        
        if state.A_resp > self.params.A_max:
            state.A_resp = self.params.A_max
            status = StatusCode.PHYS_STATE_CLAMP
        elif state.A_resp < 0.0:
            state.A_resp = 0.0
            status = StatusCode.PHYS_STATE_CLAMP
        
        return state, status
    
    def _clamp_state(
        self,
        state: PhysiologyState
    ) -> tuple[PhysiologyState, StatusCode]:
        """
        Enforce fast-time state variable constraints.
        
        Args:
            state: State to clamp
            
        Returns:
            (clamped_state, status_code)
        """
        clamped = False
        status = StatusCode.PHYS_OK
        
        # Check for numeric errors
        for field_name in ['A_resp', 'L_trans', 'xi']:
            value = getattr(state, field_name)
            if math.isnan(value) or math.isinf(value):
                return state, StatusCode.PHYS_NUMERIC_ERROR
        
        # Clamp A_resp to [0, A_max]
        if state.A_resp < 0.0:
            state.A_resp = 0.0
            clamped = True
        elif state.A_resp > self.params.A_max:
            state.A_resp = self.params.A_max
            clamped = True
        
        # Clamp L_trans to [0, +inf)
        if state.L_trans < 0.0:
            state.L_trans = 0.0
            clamped = True
        
        # Clamp xi to [0, 1]
        if state.xi < 0.0:
            state.xi = 0.0
            clamped = True
        elif state.xi > 1.0:
            state.xi = 1.0
            clamped = True
        
        if clamped:
            status = StatusCode.PHYS_STATE_CLAMP
        
        return state, status
