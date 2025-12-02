"""
Intensity function implementations for different stressor dynamics.

Provides pluggable intensity computation strategies for accumulation,
decay, periodic variation, and spike dynamics.
"""

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StressorState:
    """Internal state variables for a stressor."""
    current_intensity: float
    baseline: float
    max_intensity: float
    accumulated_exposure: float
    last_update_time: float
    last_spike_time: Optional[float]
    spike_count: int
    
    # Optional state for specific dynamics
    ou_noise_state: float = 0.0  # Ornstein-Uhlenbeck process state


class IntensityFunction(ABC):
    """Abstract base class for stressor intensity computation."""
    
    @abstractmethod
    def compute(
        self,
        state: StressorState,
        current_time: float,
        delta_time: float,
    ) -> float:
        """
        Compute stressor intensity at current time.
        
        Args:
            state: Current internal state of the stressor
            current_time: Absolute mission time (days from start)
            delta_time: Time elapsed since last update (days)
            
        Returns:
            Intensity value in [0, 1]
        """
        pass


class ConstantIntensity(IntensityFunction):
    """Constant baseline intensity (no dynamics)."""
    
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        return state.baseline


class ExponentialDecay(IntensityFunction):
    """
    Exponential decay to baseline.
    
    dI/dt = -(I - I_baseline) / tau_decay
    """
    
    def __init__(self, decay_tau: float):
        """
        Args:
            decay_tau: Decay time constant (days)
        """
        if decay_tau <= 0:
            raise ValueError(f"decay_tau must be positive, got {decay_tau}")
        self.decay_tau = decay_tau
    
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        # I(t + dt) = I_baseline + (I(t) - I_baseline) * exp(-dt / tau)
        intensity_above_baseline = state.current_intensity - state.baseline
        decay_factor = math.exp(-delta_time / self.decay_tau)
        new_intensity = state.baseline + intensity_above_baseline * decay_factor
        return max(0.0, min(1.0, new_intensity))


class LinearAccumulation(IntensityFunction):
    """
    Linear accumulation with saturation.
    
    dI/dt = alpha (saturates at max_intensity)
    """
    
    def __init__(self, accumulation_rate: float):
        """
        Args:
            accumulation_rate: Rate of intensity increase (per day)
        """
        self.accumulation_rate = accumulation_rate
    
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        new_intensity = state.current_intensity + self.accumulation_rate * delta_time
        return max(0.0, min(state.max_intensity, new_intensity))


class PeriodicCadence(IntensityFunction):
    """
    Sinusoidal variation around baseline.
    
    I(t) = I_baseline + A * sin(2π * t / T + phi)
    """
    
    def __init__(self, period: float, amplitude: float, phase_offset: float = 0.0):
        """
        Args:
            period: Oscillation period (days)
            amplitude: Oscillation amplitude
            phase_offset: Phase offset (radians)
        """
        if period <= 0:
            raise ValueError(f"period must be positive, got {period}")
        self.period = period
        self.amplitude = amplitude
        self.phase_offset = phase_offset
    
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        angular_freq = 2.0 * math.pi / self.period
        oscillation = self.amplitude * math.sin(
            angular_freq * current_time + self.phase_offset
        )
        new_intensity = state.baseline + oscillation
        return max(0.0, min(1.0, new_intensity))


class GaussianSpike(IntensityFunction):
    """
    Gaussian pulse spike.
    
    I_spike(t) = A * exp(-((t - t_spike) / sigma)^2)
    """
    
    def __init__(self, spike_time: float, amplitude: float, width: float):
        """
        Args:
            spike_time: Time of spike peak (days from mission start)
            amplitude: Spike amplitude
            width: Spike width (standard deviation in days)
        """
        self.spike_time = spike_time
        self.amplitude = amplitude
        self.width = width
    
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        time_from_spike = current_time - self.spike_time
        spike_intensity = self.amplitude * math.exp(
            -((time_from_spike / self.width) ** 2)
        )
        new_intensity = state.baseline + spike_intensity
        return max(0.0, min(1.0, new_intensity))


class OrnsteinUhlenbeckNoise(IntensityFunction):
    """
    Ornstein-Uhlenbeck process for correlated noise.
    
    dX = -X/tau * dt + sigma * sqrt(dt) * dW
    """
    
    def __init__(
        self,
        noise_intensity: float,
        correlation_time: float,
        random_state: random.Random,
    ):
        """
        Args:
            noise_intensity: Noise amplitude
            correlation_time: Correlation time constant (days)
            random_state: Random number generator
        """
        if correlation_time <= 0:
            raise ValueError(f"correlation_time must be positive, got {correlation_time}")
        self.noise_intensity = noise_intensity
        self.correlation_time = correlation_time
        self.random_state = random_state
    
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        # OU process update
        decay = math.exp(-delta_time / self.correlation_time)
        variance = self.noise_intensity ** 2 * (1 - decay ** 2)
        
        # Update OU state
        noise = self.random_state.gauss(0, math.sqrt(variance))
        state.ou_noise_state = state.ou_noise_state * decay + noise
        
        # Add noise to baseline
        new_intensity = state.current_intensity + state.ou_noise_state
        return max(0.0, min(1.0, new_intensity))


class CompositeIntensity(IntensityFunction):
    """
    Composite of multiple intensity functions.
    
    Combines baseline dynamics with periodic variation, spikes, and noise.
    """
    
    def __init__(self, functions: list[IntensityFunction], combination_mode: str = "additive"):
        """
        Args:
            functions: List of intensity functions to combine
            combination_mode: "additive" or "multiplicative"
        """
        self.functions = functions
        self.combination_mode = combination_mode
    
    def compute(self, state: StressorState, current_time: float, delta_time: float) -> float:
        if self.combination_mode == "additive":
            # Start from baseline, add contributions
            total_intensity = state.baseline
            for func in self.functions:
                contribution = func.compute(state, current_time, delta_time)
                total_intensity += (contribution - state.baseline)
            return max(0.0, min(1.0, total_intensity))
        
        elif self.combination_mode == "multiplicative":
            # Multiply factors
            total_intensity = state.baseline
            for func in self.functions:
                factor = func.compute(state, current_time, delta_time) / state.baseline
                total_intensity *= factor
            return max(0.0, min(1.0, total_intensity))
        
        else:
            raise ValueError(f"Unknown combination mode: {self.combination_mode}")
