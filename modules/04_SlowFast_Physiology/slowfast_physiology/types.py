"""
Data types and structures for the Slow-Fast Physiology Model.

Implements all data contracts specified in data_contract.md.
"""

from dataclasses import dataclass
from enum import Enum
import math


class StatusCode(Enum):
    """Module status codes."""
    PHYS_OK = 0                    # Update successful, no issues
    PHYS_INPUT_INVALID = 1         # Input out of range or malformed
    PHYS_STATE_CLAMP = 2           # State variable clamped (warning)
    PHYS_NUMERIC_ERROR = 3         # Numerical instability detected (critical error)


@dataclass
class PhysiologyState:
    """
    Complete physiological state representation.
    
    Combines slow-time and fast-time state variables.
    """
    # Slow-time state
    C_base: float      # Baseline capacity [0.0, 1.0]
    L_cum: float       # Cumulative load [0.0, +inf)
    R_cap: float       # Recovery capacity [0.0, 1.0]
    
    # Fast-time state
    A_resp: float      # Acute response [0.0, A_max]
    L_trans: float     # Transient load [0.0, +inf)
    xi: float          # Relaxation state [0.0, 1.0]
    
    # Derived quantities (cached)
    gamma_drift: float = 0.0  # Current drift rate
    L_total: float = 0.0      # Total load (L_cum + L_trans)
    C_eff: float = 1.0        # Effective capacity
    
    # Metadata
    t_slow: float = 0.0
    t_fast: float = 0.0
    epoch_number: int = 0
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate state variable constraints.
        
        Returns:
            (is_valid, error_message)
        """
        # Check for NaN or Inf
        for field_name in ['C_base', 'L_cum', 'R_cap', 'A_resp', 'L_trans', 'xi']:
            value = getattr(self, field_name)
            if math.isnan(value) or math.isinf(value):
                return False, f"{field_name} is NaN or Inf: {value}"
        
        # Check ranges
        if not (0.0 <= self.C_base <= 1.0):
            return False, f"C_base out of range [0, 1]: {self.C_base}"
        
        if self.L_cum < 0.0:
            return False, f"L_cum must be non-negative: {self.L_cum}"
        
        if not (0.0 <= self.R_cap <= 1.0):
            return False, f"R_cap out of range [0, 1]: {self.R_cap}"
        
        if self.L_trans < 0.0:
            return False, f"L_trans must be non-negative: {self.L_trans}"
        
        if not (0.0 <= self.xi <= 1.0):
            return False, f"xi out of range [0, 1]: {self.xi}"
        
        return True, ""


@dataclass
class PhysiologyParameters:
    """
    Model parameters for slow and fast dynamics.
    
    All parameters are immutable after initialization.
    """
    # Slow-time parameters
    alpha_deg: float        # Degradation coefficient
    beta_rec: float         # Recovery coefficient
    omega_in: float         # Load accumulation rate
    omega_out: float        # Load dissipation rate
    kappa_rec: float        # Recovery restoration rate
    kappa_fatigue: float    # Fatigue degradation rate
    
    # Fast-time parameters
    Delta_A_0: float        # Baseline acute response sensitivity
    lambda_A: float         # Acute response relaxation rate
    lambda_L: float         # Transient load relaxation rate
    lambda_xi: float        # Relaxation state rate
    mu: float               # Coupling coefficient
    A_max: float            # Maximum acute response
    
    # Coupling parameters
    sigma: float            # Load-dependent modulation coefficient
    
    # Default values (must come after required fields)
    R_cap_max: float = 1.0  # Max recovery capacity
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate parameter constraints.
        
        Returns:
            (is_valid, error_message)
        """
        # All rate constants must be positive
        positive_params = [
            'alpha_deg', 'beta_rec', 'omega_in', 'omega_out',
            'kappa_rec', 'kappa_fatigue', 'Delta_A_0',
            'lambda_A', 'lambda_L', 'lambda_xi', 'A_max'
        ]
        
        for param_name in positive_params:
            value = getattr(self, param_name)
            if value <= 0.0:
                return False, f"{param_name} must be positive: {value}"
        
        # Non-negative parameters
        if self.mu < 0.0:
            return False, f"mu must be non-negative: {self.mu}"
        
        if self.sigma < 0.0:
            return False, f"sigma must be non-negative: {self.sigma}"
        
        if self.R_cap_max <= 0.0 or self.R_cap_max > 1.0:
            return False, f"R_cap_max must be in (0, 1]: {self.R_cap_max}"
        
        return True, ""


@dataclass
class TimescaleConfig:
    """
    Timescale configuration for slow and fast processes.
    """
    dt_slow: float          # Slow time step (e.g., 1.0 day)
    dt_fast: float          # Fast time step (e.g., 1.0/24 day = 1 hour)
    time_unit: str = "days" # Metadata only
    
    def __post_init__(self):
        """Validate and compute derived values."""
        if self.dt_fast >= self.dt_slow:
            raise ValueError(f"dt_fast ({self.dt_fast}) must be < dt_slow ({self.dt_slow})")
        
        # Compute number of fast steps per slow step
        ratio = self.dt_slow / self.dt_fast
        self.N_fast = int(round(ratio))
        
        # Verify it's close to an integer
        if abs(ratio - self.N_fast) > 0.01:
            raise ValueError(
                f"dt_slow / dt_fast must be an integer, got {ratio}"
            )


@dataclass
class SlowTimeInput:
    """Input data for slow-time update."""
    t_slow: float           # Current slow-time timestamp
    I_slow: float = 0.0     # Slow-time stressor intensity


@dataclass
class FastTimeInput:
    """Input data for fast-time update."""
    t_fast: float           # Current fast-time timestamp
    I_fast: float = 0.0     # Fast-time stressor intensity


@dataclass
class SlowTimeState:
    """Slow-time state variables for output."""
    C_base: float
    L_cum: float
    R_cap: float
    gamma_drift: float


@dataclass
class FastTimeState:
    """Fast-time state variables for output."""
    A_resp: float
    L_trans: float
    xi: float


@dataclass
class SlowTimeOutput:
    """Output data from slow-time update."""
    t_slow: float
    state: SlowTimeState
    status: StatusCode


@dataclass
class FastTimeOutput:
    """Output data from fast-time update."""
    t_fast: float
    state: FastTimeState
    status: StatusCode


@dataclass
class PhysiologyDerivedOutput:
    """Derived quantities output."""
    t: float
    L_total: float          # L_cum + L_trans
    C_eff: float            # Effective capacity


@dataclass
class PhysiologyInitConfig:
    """Complete initialization configuration."""
    initial_state: PhysiologyState
    parameters: PhysiologyParameters
    timescale_config: TimescaleConfig
