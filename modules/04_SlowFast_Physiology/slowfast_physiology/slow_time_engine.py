"""
Slow-time engine for physiological state updates.

Implements slow-time dynamics according to spec.md:
- Baseline capacity drift
- Cumulative load accumulation
- Recovery capacity dynamics
"""

from .types import PhysiologyState, PhysiologyParameters, StatusCode


class SlowTimeEngine:
    """
    Manages slow-time state updates.
    
    Implements differential equations for:
    - C_base (baseline capacity)
    - L_cum (cumulative load)
    - R_cap (recovery capacity)
    """
    
    def __init__(self, params: PhysiologyParameters):
        """
        Initialize slow-time engine.
        
        Args:
            params: Model parameters
        """
        self.params = params
    
    def compute_derivatives(
        self,
        state: PhysiologyState,
        I_slow: float
    ) -> tuple[float, float, float]:
        """
        Compute slow-time derivatives.
        
        Args:
            state: Current physiological state
            I_slow: Slow-time stressor intensity
            
        Returns:
            (dC_base_dt, dL_cum_dt, dR_cap_dt)
        """
        # Baseline capacity drift
        # dC_base/dt = γ_drift - α_deg * g(L_cum) + β_rec * R_cap * h(C_base)
        g_L_cum = state.L_cum  # Linear degradation function
        h_C_base = 1.0 - state.C_base  # Recovery saturation
        
        dC_base_dt = (
            state.gamma_drift
            - self.params.alpha_deg * g_L_cum
            + self.params.beta_rec * state.R_cap * h_C_base
        )
        
        # Cumulative load accumulation
        # dL_cum/dt = ω_in * I_slow - ω_out * R_cap * L_cum
        dL_cum_dt = (
            self.params.omega_in * I_slow
            - self.params.omega_out * state.R_cap * state.L_cum
        )
        
        # Recovery capacity dynamics
        # dR_cap/dt = κ_rec * (R_cap_max - R_cap) - κ_fatigue * L_cum * R_cap
        dR_cap_dt = (
            self.params.kappa_rec * (self.params.R_cap_max - state.R_cap)
            - self.params.kappa_fatigue * state.L_cum * state.R_cap
        )
        
        return dC_base_dt, dL_cum_dt, dR_cap_dt
    
    def update(
        self,
        state: PhysiologyState,
        I_slow: float,
        dt: float
    ) -> tuple[PhysiologyState, StatusCode]:
        """
        Perform slow-time state update.
        
        Uses forward Euler integration.
        
        Args:
            state: Current state
            I_slow: Slow-time stressor intensity
            dt: Time step size
            
        Returns:
            (updated_state, status_code)
        """
        # Compute derivatives
        dC_base_dt, dL_cum_dt, dR_cap_dt = self.compute_derivatives(state, I_slow)
        
        # Forward Euler integration
        new_C_base = state.C_base + dC_base_dt * dt
        new_L_cum = state.L_cum + dL_cum_dt * dt
        new_R_cap = state.R_cap + dR_cap_dt * dt
        
        # Store gamma_drift for output
        new_gamma_drift = dC_base_dt
        
        # Create new state
        new_state = PhysiologyState(
            C_base=new_C_base,
            L_cum=new_L_cum,
            R_cap=new_R_cap,
            A_resp=state.A_resp,
            L_trans=state.L_trans,
            xi=state.xi,
            gamma_drift=new_gamma_drift,
            L_total=state.L_total,
            C_eff=state.C_eff,
            t_slow=state.t_slow,
            t_fast=state.t_fast,
            epoch_number=state.epoch_number
        )
        
        # Enforce constraints and detect clamping
        new_state, status = self._clamp_state(new_state)
        
        return new_state, status
    
    def _clamp_state(
        self,
        state: PhysiologyState
    ) -> tuple[PhysiologyState, StatusCode]:
        """
        Enforce state variable constraints.
        
        Args:
            state: State to clamp
            
        Returns:
            (clamped_state, status_code)
        """
        clamped = False
        status = StatusCode.PHYS_OK
        
        # Check for numeric errors first
        valid, error_msg = state.validate()
        if not valid:
            if "NaN" in error_msg or "Inf" in error_msg:
                return state, StatusCode.PHYS_NUMERIC_ERROR
        
        # Clamp C_base to [0, 1]
        if state.C_base < 0.0:
            state.C_base = 0.0
            clamped = True
        elif state.C_base > 1.0:
            state.C_base = 1.0
            clamped = True
        
        # Clamp L_cum to [0, +inf) (just non-negativity)
        if state.L_cum < 0.0:
            state.L_cum = 0.0
            clamped = True
        
        # Clamp R_cap to [0, 1]
        if state.R_cap < 0.0:
            state.R_cap = 0.0
            clamped = True
        elif state.R_cap > 1.0:
            state.R_cap = 1.0
            clamped = True
        
        if clamped:
            status = StatusCode.PHYS_STATE_CLAMP
        
        return state, status
