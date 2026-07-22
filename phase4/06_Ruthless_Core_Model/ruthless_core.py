"""
Ruthless Core Model - Minimal Third Quarter Dynamics Engine

This module implements a simple, transparent dynamical model for simulating
psychological strain, social cohesion, monotony, and third quarter pressure
in long-duration isolated confined environments.

DESIGN PHILOSOPHY:
- Simple discrete-time difference equations
- Transparent, calibratable parameters
- No hidden state or complex feedback loops
- Designed for visual calibration and interpretation

This is NOT a full BDI agent model. It is a minimal dynamical core that
can generate plausible third quarter trajectories for validation and
calibration purposes.

Author: 3QP Development Team
Version: 0.1.0
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RuthlessCoreConfig:
    """
    Configuration for Ruthless Core Model.
    
    Parameters:
        mission_length_days: Total mission duration in days
        
        # Initial conditions
        initial_monotony: Starting monotony level
        initial_strain: Starting psychological strain
        initial_cohesion: Starting social cohesion (normalized to ~1.0)
        
        # Monotony parameters
        m_base: Daily baseline increase in monotony
        m_novelty: Monotony reduction per novelty event
        
        # Strain parameters
        s_workload: Strain increase per unit workload
        s_mono: Strain increase per unit monotony
        s_recovery: Strain decrease per unit recovery
        
        # Third quarter pressure parameters
        q_peak: Peak amplitude of third quarter pressure term
        q_center: Center position in mission fraction (e.g., 0.7 for 70%)
        q_width: Width/spread of the Gaussian hump
        
        # Cohesion parameters
        c_strain: Cohesion decrease per unit strain
        c_q: Cohesion decrease per unit third quarter pressure
        c_shared_success: Cohesion increase per success event
        
        # Input schedules (if None, defaults will be generated)
        workload_schedule: Daily workload values [0, 1]
        recovery_schedule: Daily recovery values [0, 1]
        novelty_events: Binary novelty event indicators per day
        success_events: Binary shared success event indicators per day
    """
    # Mission parameters
    mission_length_days: int = 200
    
    # Initial conditions
    initial_monotony: float = 0.0
    initial_strain: float = 0.0
    initial_cohesion: float = 1.0
    
    # Monotony parameters
    m_base: float = 0.008  # Daily monotony accumulation
    m_novelty: float = 0.2  # Novelty event impact
    
    # Strain parameters
    s_workload: float = 0.03  # Workload -> strain coefficient
    s_mono: float = 0.004  # Monotony -> strain coefficient
    s_recovery: float = 0.04  # Recovery -> strain reduction
    s_leak: float = 0.030  # Strain adaptation/leak (prevents unbounded growth)
    
    # Third quarter pressure parameters (legacy Gaussian — unused, kept for compatibility)
    q_peak: float = 0.55
    q_center: float = 0.62
    q_width: float = 0.08

    # Endogenous TQ pressure coefficients
    # Q emerges from state: Q = c_q_m*M + c_q_s*S + c_q_c*(1-C)
    c_q_m: float = 0.15   # Monotony contribution to TQ pressure
    c_q_s: float = 0.20   # Strain contribution to TQ pressure
    c_q_c: float = 0.10   # Cohesion-deficit contribution to TQ pressure

    # Cohesion parameters
    c_strain: float = 0.008  # Strain -> cohesion decrease
    c_q: float = 0.033  # TQ pressure -> cohesion decrease
    c_shared_success: float = 0.06  # Success -> cohesion increase
    c_rebound: float = 0.01  # Cohesion recovery when Q is actively falling
    
    # Input schedules (optional, will be generated if None)
    workload_schedule: Optional[List[float]] = None
    recovery_schedule: Optional[List[float]] = None
    novelty_events: Optional[List[int]] = None
    success_events: Optional[List[int]] = None
    
    def __post_init__(self):
        """Generate default schedules if not provided."""
        if self.workload_schedule is None:
            # Constant moderate workload with slight variation
            self.workload_schedule = [0.6 + 0.1 * math.sin(2 * math.pi * t / 30) 
                                      for t in range(self.mission_length_days)]
        
        if self.recovery_schedule is None:
            # Modest constant recovery
            self.recovery_schedule = [0.4] * self.mission_length_days
        
        if self.novelty_events is None:
            # High novelty early, then rare
            self.novelty_events = [1 if t < 20 or (t % 40 == 0) else 0 
                                   for t in range(self.mission_length_days)]
        
        if self.success_events is None:
            # Occasional shared successes
            self.success_events = [1 if t % 30 == 15 else 0 
                                   for t in range(self.mission_length_days)]


@dataclass
class RuthlessCoreOutput:
    """
    Output container for Ruthless Core Model simulation.
    
    Contains time series for all state variables plus metadata.
    
    Attributes:
        days: Day indices [0, 1, ..., T-1]
        strain: Psychological strain S(t)
        cohesion: Social cohesion C(t)
        monotony: Monotony M(t)
        tq_pressure: Third quarter pressure Q(t)
        metadata: Additional simulation metadata
    """
    days: List[int]
    strain: List[float]
    cohesion: List[float]
    monotony: List[float]
    tq_pressure: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Return number of time steps."""
        return len(self.days)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return {
            "days": self.days,
            "strain": self.strain,
            "cohesion": self.cohesion,
            "monotony": self.monotony,
            "tq_pressure": self.tq_pressure,
            "metadata": self.metadata,
        }


class RuthlessCoreModel:
    """
    Ruthless Core Model - Minimal third quarter dynamics simulator.
    
    This model implements discrete-time difference equations for four
    state variables that evolve over the course of a long-duration mission:
    
    - M(t): Monotony - accumulates over time, reduced by novelty
    - S(t): Psychological strain - driven by workload, monotony, moderated by recovery
    - Q(t): Third quarter pressure - Gaussian hump centered in third quarter
    - C(t): Social cohesion - eroded by strain and TQ pressure, boosted by shared success
    
    The model is deterministic and fully transparent. All parameters are
    exposed in RuthlessCoreConfig for calibration.
    
    Example:
        >>> config = RuthlessCoreConfig(mission_length_days=180)
        >>> model = RuthlessCoreModel(config)
        >>> output = model.run()
        >>> print(f"Final cohesion: {output.cohesion[-1]:.3f}")
    """
    
    def __init__(self, config: RuthlessCoreConfig):
        """
        Initialize model with configuration.
        
        Args:
            config: RuthlessCoreConfig instance with all parameters
        """
        self.config = config
        self.T = config.mission_length_days
    
    def compute_tq_pressure(self, M: float, S: float, C: float) -> float:
        """
        Compute endogenous third quarter pressure from current state variables.

        Q emerges from the crew's actual condition — not from the mission clock.
        High monotony, elevated strain, and eroded cohesion drive TQ pressure up.
        Pressure falls when the crew recovers, producing a rebound opportunity.

        Formula:
            Q = c_q_m * (M/2) + c_q_s * S + c_q_c * max(0, 1 - C)
            where M is normalised to a typical maximum of 2.0.

        Args:
            M: Current monotony level
            S: Current strain level
            C: Current cohesion level

        Returns:
            Third quarter pressure value [0.0, 1.0]
        """
        m_norm = min(M / 2.0, 1.0)  # Normalise M to [0, 1] (typical max ≈ 2.0)
        c_deficit = max(0.0, 1.0 - C)
        raw = (
            self.config.c_q_m * m_norm
            + self.config.c_q_s * S
            + self.config.c_q_c * c_deficit
        )
        return max(0.0, min(1.0, raw))
    
    def run(self) -> RuthlessCoreOutput:
        """
        Run the simulation for the full mission duration.
        
        Implements discrete-time update equations for all state variables.
        
        Returns:
            RuthlessCoreOutput containing full time series
        """
        # Initialize storage
        days = list(range(self.T))
        M = [0.0] * self.T  # Monotony
        S = [0.0] * self.T  # Strain
        Q = [0.0] * self.T  # TQ pressure
        C = [0.0] * self.T  # Cohesion
        
        # Set initial conditions
        M[0] = self.config.initial_monotony
        S[0] = self.config.initial_strain
        C[0] = self.config.initial_cohesion
        Q[0] = self.compute_tq_pressure(M[0], S[0], C[0])

        # Time stepping
        for t in range(self.T - 1):
            # Get inputs for this day
            workload = self.config.workload_schedule[t]
            recovery = self.config.recovery_schedule[t]
            novelty = self.config.novelty_events[t]
            success = self.config.success_events[t]

            # Update monotony
            M[t + 1] = M[t] + self.config.m_base - self.config.m_novelty * novelty
            M[t + 1] = max(0.0, M[t + 1])  # Non-negative

            # Update strain
            strain_increase = (
                self.config.s_workload * workload +
                self.config.s_mono * M[t]
            )
            strain_decrease = self.config.s_recovery * recovery
            strain_leak = self.config.s_leak * S[t]  # Proportional adaptation
            S[t + 1] = S[t] + strain_increase - strain_decrease - strain_leak
            S[t + 1] = max(0.0, S[t + 1])  # Non-negative

            # Endogenous TQ pressure from updated M and S, prior C
            Q[t + 1] = self.compute_tq_pressure(M[t + 1], S[t + 1], C[t])

            # Update cohesion
            cohesion_decrease = (
                self.config.c_strain * S[t] +
                self.config.c_q * Q[t]
            )
            cohesion_increase = self.config.c_shared_success * success

            # Cohesion rebound fires when TQ pressure is actively falling
            cohesion_rebound = (
                self.config.c_rebound * (1.0 - C[t])
                if Q[t + 1] < Q[t] else 0.0
            )

            C[t + 1] = C[t] - cohesion_decrease + cohesion_increase + cohesion_rebound
            # Cohesion bounded [0.05, 1.2] to maintain reasonable range
            C[t + 1] = max(0.05, min(1.2, C[t + 1]))
        
        # Package output
        output = RuthlessCoreOutput(
            days=days,
            strain=S,
            cohesion=C,
            monotony=M,
            tq_pressure=Q,
            metadata={
                "model": "RuthlessCoreModel",
                "version": "0.1.0",
                "mission_length_days": self.T,
                "config_summary": {
                    "q_center": self.config.q_center,
                    "q_peak": self.config.q_peak,
                    "m_base": self.config.m_base,
                }
            }
        )
        
        return output


# ============================================================================
# Phase 4 Integration Adapters
# ============================================================================

def to_phase4_encoded_states(output: RuthlessCoreOutput) -> List[Dict[str, Any]]:
    """
    Convert RuthlessCoreOutput to Phase 4 WS2 encoded states format.
    
    This adapter transforms ruthless core time series into the list[dict]
    format expected by Phase 4 trajectory analyzers.
    
    Args:
        output: RuthlessCoreOutput from model run
        
    Returns:
        List of encoded state dicts, one per day
    """
    encoded_states = []
    
    for i in range(len(output)):
        state = {
            "day": output.days[i],
            "mission_progress": output.days[i] / len(output),
            "domains": {
                "physiological": {
                    "strain_level": output.strain[i],
                    "qualitative_state": _classify_strain(output.strain[i]),
                },
                "social": {
                    "cohesion": output.cohesion[i],
                    "qualitative_state": _classify_cohesion(output.cohesion[i]),
                },
                "environmental": {
                    "monotony": output.monotony[i],
                    "qualitative_state": _classify_monotony(output.monotony[i]),
                },
                "trajectory_indicators": {
                    "tq_pressure": output.tq_pressure[i],
                }
            },
            "metadata": {
                "source": "ruthless_core_model",
                "version": "0.1.0",
            }
        }
        encoded_states.append(state)
    
    return encoded_states


def to_phase4_trajectory_result(
    output: RuthlessCoreOutput,
    archetype_id: str = "third_quarter"
) -> Dict[str, Any]:
    """
    Convert RuthlessCoreOutput to a Phase 4 trajectory classification result.
    
    This is a lightweight adapter that creates a minimal trajectory result
    suitable for validation harness integration.
    
    Args:
        output: RuthlessCoreOutput from model run
        archetype_id: Trajectory archetype identifier
        
    Returns:
        Dictionary compatible with Phase 4 TrajectoryClassificationResult
    """
    # Detect if third quarter dip occurred
    min_cohesion_idx = output.cohesion.index(min(output.cohesion))
    min_cohesion_progress = output.days[min_cohesion_idx] / len(output)
    
    # Check if minimum is in third quarter range
    is_third_quarter = 0.50 <= min_cohesion_progress <= 0.90
    
    result = {
        "archetype_id": archetype_id if is_third_quarter else "stable_adaptation",
        "label": "Third Quarter Trajectory" if is_third_quarter else "Stable Adaptation",
        "support_strength": "STRONG" if is_third_quarter else "MODERATE",
        "evidence": [
            {
                "item_type": "cohesion_minimum",
                "description": f"Minimum cohesion at day {output.days[min_cohesion_idx]} "
                              f"({min_cohesion_progress:.1%} progress)",
                "support": "STRONG" if is_third_quarter else "WEAK",
            }
        ],
        "metadata": {
            "source": "ruthless_core_model",
            "version": "0.1.0",
            "min_cohesion": min(output.cohesion),
            "min_cohesion_day": output.days[min_cohesion_idx],
        }
    }
    
    return result


# ============================================================================
# Helper Functions
# ============================================================================

def _classify_strain(strain: float) -> str:
    """Classify strain level into qualitative category."""
    if strain < 0.3:
        return "low"
    elif strain < 0.6:
        return "moderate"
    elif strain < 1.0:
        return "elevated"
    else:
        return "high"


def _classify_cohesion(cohesion: float) -> str:
    """Classify cohesion level into qualitative category."""
    if cohesion > 0.8:
        return "strong"
    elif cohesion > 0.6:
        return "adequate"
    elif cohesion > 0.4:
        return "fragile"
    else:
        return "degraded"


def _classify_monotony(monotony: float) -> str:
    """Classify monotony level into qualitative category."""
    if monotony < 0.5:
        return "low"
    elif monotony < 1.5:
        return "moderate"
    elif monotony < 3.0:
        return "high"
    else:
        return "extreme"
