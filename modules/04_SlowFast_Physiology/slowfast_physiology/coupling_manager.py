"""
Coupling manager for slow-fast timescale interactions.

Implements bidirectional coupling according to spec.md:
- Slow → Fast: Modulates fast-time parameters based on slow-time state
- Fast → Slow: Aggregates fast-time activity for slow-time updates
"""

from typing import List
from .types import PhysiologyState, PhysiologyParameters


class CouplingManager:
    """
    Manages coupling between slow and fast timescales.
    
    Coordinates parameter modulation and state aggregation.
    """
    
    def __init__(self, params: PhysiologyParameters):
        """
        Initialize coupling manager.
        
        Args:
            params: Model parameters
        """
        self.params = params
    
    def compute_slow_to_fast_coupling(
        self,
        state: PhysiologyState
    ) -> tuple[float, float]:
        """
        Compute fast-time parameters from slow-time state.
        
        Implements:
        - Delta_A = Delta_A_0 * C_base
        - lambda_A = lambda_A_0 / (1 + sigma * L_cum)
        
        Args:
            state: Current physiological state
            
        Returns:
            (Delta_A_effective, lambda_A_effective)
        """
        # Modulate acute response sensitivity by baseline capacity
        Delta_A_effective = self.params.Delta_A_0 * state.C_base
        
        # Increase relaxation time if cumulative load is high
        # (decrease relaxation rate)
        lambda_A_effective = self.params.lambda_A / (
            1.0 + self.params.sigma * state.L_cum
        )
        
        return Delta_A_effective, lambda_A_effective
    
    def aggregate_fast_activity(
        self,
        fast_states: List[PhysiologyState]
    ) -> float:
        """
        Aggregate fast-time activity for slow-time update.
        
        Computes time-averaged transient load over the epoch.
        
        Args:
            fast_states: List of fast-time states from the epoch
            
        Returns:
            Time-averaged L_trans
        """
        if not fast_states:
            return 0.0
        
        # Time-averaged transient load
        L_trans_values = [state.L_trans for state in fast_states]
        L_trans_avg = sum(L_trans_values) / len(L_trans_values)
        
        return L_trans_avg
    
    def compute_derived_quantities(
        self,
        state: PhysiologyState
    ) -> tuple[float, float]:
        """
        Compute derived quantities from state.
        
        Implements:
        - L_total = L_cum + L_trans
        - C_eff = C_base * f(L_total) where f(x) = 1 / (1 + x)
        
        Args:
            state: Current physiological state
            
        Returns:
            (L_total, C_eff)
        """
        # Total load
        L_total = state.L_cum + state.L_trans
        
        # Effective capacity with saturation function
        # f(L_total) = 1 / (1 + L_total)
        C_eff = state.C_base / (1.0 + L_total)
        
        return L_total, C_eff
    
    def update_derived_state(
        self,
        state: PhysiologyState
    ) -> PhysiologyState:
        """
        Update derived quantities in state.
        
        Args:
            state: State to update
            
        Returns:
            State with updated L_total and C_eff
        """
        L_total, C_eff = self.compute_derived_quantities(state)
        
        state.L_total = L_total
        state.C_eff = C_eff
        
        return state
