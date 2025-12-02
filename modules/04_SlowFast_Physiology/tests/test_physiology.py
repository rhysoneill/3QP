"""
Unit tests for the Slow-Fast Physiology Module.

Tests cover:
- Initialization and validation
- Slow-time dynamics
- Fast-time dynamics
- Coupling mechanisms
- Constraint enforcement
- Integration behavior
"""

import pytest
import math
from slowfast_physiology import (
    PhysiologyModule,
    PhysiologyState,
    PhysiologyParameters,
    TimescaleConfig,
    PhysiologyInitConfig,
    SlowTimeInput,
    FastTimeInput,
    StatusCode
)


@pytest.fixture
def default_params():
    """Default parameter set for testing."""
    return PhysiologyParameters(
        # Slow-time parameters
        alpha_deg=0.005,
        beta_rec=0.05,
        omega_in=0.1,
        omega_out=0.05,
        kappa_rec=0.01,
        kappa_fatigue=0.02,
        R_cap_max=1.0,
        # Fast-time parameters
        Delta_A_0=1.0,
        lambda_A=0.5,
        lambda_L=0.2,
        lambda_xi=1.0,
        mu=0.1,
        A_max=5.0,
        # Coupling parameters
        sigma=0.1
    )


@pytest.fixture
def default_timescale():
    """Default timescale configuration."""
    return TimescaleConfig(
        dt_slow=1.0,      # 1 day
        dt_fast=1.0/24.0, # 1 hour
        time_unit="days"
    )


@pytest.fixture
def default_initial_state():
    """Default initial state (healthy baseline)."""
    return PhysiologyState(
        C_base=1.0,
        L_cum=0.0,
        R_cap=1.0,
        A_resp=0.0,
        L_trans=0.0,
        xi=0.5  # Partially relaxed to allow acute response
    )


@pytest.fixture
def physiology_module(default_initial_state, default_params, default_timescale):
    """Initialized physiology module."""
    config = PhysiologyInitConfig(
        initial_state=default_initial_state,
        parameters=default_params,
        timescale_config=default_timescale
    )
    return PhysiologyModule(config)


class TestInitialization:
    """Test module initialization and validation."""
    
    def test_valid_initialization(self, default_initial_state, default_params, default_timescale):
        """Valid configuration should initialize successfully."""
        config = PhysiologyInitConfig(
            initial_state=default_initial_state,
            parameters=default_params,
            timescale_config=default_timescale
        )
        module = PhysiologyModule(config)
        
        assert module.state.C_base == 1.0
        assert module.state.L_cum == 0.0
        assert module.state.R_cap == 1.0
    
    def test_invalid_state_raises(self, default_params, default_timescale):
        """Invalid initial state should raise ValueError."""
        invalid_state = PhysiologyState(
            C_base=1.5,  # Out of range
            L_cum=0.0,
            R_cap=1.0,
            A_resp=0.0,
            L_trans=0.0,
            xi=1.0
        )
        
        config = PhysiologyInitConfig(
            initial_state=invalid_state,
            parameters=default_params,
            timescale_config=default_timescale
        )
        
        with pytest.raises(ValueError):
            PhysiologyModule(config)
    
    def test_invalid_params_raises(self, default_initial_state, default_timescale):
        """Invalid parameters should raise ValueError."""
        invalid_params = PhysiologyParameters(
            alpha_deg=-0.1,  # Negative (invalid)
            beta_rec=0.05,
            omega_in=0.1,
            omega_out=0.05,
            kappa_rec=0.01,
            kappa_fatigue=0.02,
            Delta_A_0=1.0,
            lambda_A=0.5,
            lambda_L=0.2,
            lambda_xi=1.0,
            mu=0.1,
            A_max=5.0,
            sigma=0.1
        )
        
        config = PhysiologyInitConfig(
            initial_state=default_initial_state,
            parameters=invalid_params,
            timescale_config=default_timescale
        )
        
        with pytest.raises(ValueError):
            PhysiologyModule(config)


class TestFastTimeDynamics:
    """Test fast-time state updates."""
    
    def test_acute_response_to_input(self, physiology_module):
        """Acute input should increase A_resp."""
        initial_A = physiology_module.state.A_resp
        
        fast_input = FastTimeInput(t_fast=0.0, I_fast=2.0)
        output = physiology_module.fast_time_step(fast_input)
        
        # A_resp should increase
        assert output.state.A_resp > initial_A
        assert output.status == StatusCode.PHYS_OK
    
    def test_relaxation_without_input(self, physiology_module):
        """Without input, A_resp should relax toward zero."""
        # First apply an input
        fast_input = FastTimeInput(t_fast=0.0, I_fast=2.0)
        physiology_module.fast_time_step(fast_input)
        
        A_after_input = physiology_module.state.A_resp
        
        # Then relax without input
        for i in range(5):
            fast_input = FastTimeInput(t_fast=float(i+1)/24.0, I_fast=0.0)
            output = physiology_module.fast_time_step(fast_input)
        
        # A_resp should decrease
        assert output.state.A_resp < A_after_input
    
    def test_xi_relaxation(self, physiology_module):
        """Relaxation state xi should approach 1.0."""
        # Set xi to low value
        physiology_module.state.xi = 0.5
        
        # Run several steps without input
        for i in range(10):
            fast_input = FastTimeInput(t_fast=float(i)/24.0, I_fast=0.0)
            output = physiology_module.fast_time_step(fast_input)
        
        # xi should have increased toward 1.0
        assert output.state.xi > 0.5
        assert output.state.xi <= 1.0
    
    def test_A_resp_clamping(self, physiology_module):
        """A_resp should be clamped to A_max."""
        # Apply very large input
        fast_input = FastTimeInput(t_fast=0.0, I_fast=100.0)
        output = physiology_module.fast_time_step(fast_input)
        
        # Should be clamped
        assert output.state.A_resp <= physiology_module.params.A_max
        assert output.status == StatusCode.PHYS_STATE_CLAMP


class TestSlowTimeDynamics:
    """Test slow-time state updates."""
    
    def test_load_accumulation_with_stressor(self, physiology_module):
        """Sustained stressor should increase L_cum."""
        initial_L_cum = physiology_module.state.L_cum
        
        # Apply sustained slow-time stressor
        slow_input = SlowTimeInput(t_slow=1.0, I_slow=1.0)
        output = physiology_module.slow_time_step(slow_input)
        
        # L_cum should increase
        assert output.state.L_cum > initial_L_cum
    
    def test_load_dissipation_without_stressor(self, physiology_module):
        """Without stressor, L_cum should dissipate."""
        # First accumulate some load
        physiology_module.state.L_cum = 1.0
        
        # Then remove stressor
        for i in range(5):
            slow_input = SlowTimeInput(t_slow=float(i+1), I_slow=0.0)
            output = physiology_module.slow_time_step(slow_input)
        
        # L_cum should decrease
        assert output.state.L_cum < 1.0
    
    def test_capacity_degradation_under_load(self, physiology_module):
        """High cumulative load should degrade C_base."""
        # Set high cumulative load
        physiology_module.state.L_cum = 5.0
        
        initial_C_base = physiology_module.state.C_base
        
        # Run several slow steps
        for i in range(10):
            slow_input = SlowTimeInput(t_slow=float(i+1), I_slow=0.5)
            output = physiology_module.slow_time_step(slow_input)
        
        # C_base should decrease
        assert output.state.C_base < initial_C_base
    
    def test_recovery_capacity_restoration(self, physiology_module):
        """Without load, R_cap should approach R_cap_max."""
        # Set R_cap to low value
        physiology_module.state.R_cap = 0.5
        physiology_module.state.L_cum = 0.0
        
        # Run without stressor
        for i in range(20):
            slow_input = SlowTimeInput(t_slow=float(i+1), I_slow=0.0)
            output = physiology_module.slow_time_step(slow_input)
        
        # R_cap should increase toward R_cap_max
        assert output.state.R_cap > 0.5


class TestCoupling:
    """Test slow-fast coupling mechanisms."""
    
    def test_slow_to_fast_coupling(self, physiology_module):
        """Reduced C_base should reduce acute response sensitivity."""
        # Set low baseline capacity
        physiology_module.state.C_base = 0.5
        
        # Update coupling for next epoch
        Delta_A, lambda_A = physiology_module.coupling.compute_slow_to_fast_coupling(
            physiology_module.state
        )
        
        # Delta_A should be reduced
        assert Delta_A < physiology_module.params.Delta_A_0
    
    def test_load_increases_relaxation_time(self, physiology_module):
        """High L_cum should decrease lambda_A (slower relaxation)."""
        # Set high cumulative load
        physiology_module.state.L_cum = 2.0
        
        Delta_A, lambda_A = physiology_module.coupling.compute_slow_to_fast_coupling(
            physiology_module.state
        )
        
        # lambda_A should be reduced (slower relaxation)
        assert lambda_A < physiology_module.params.lambda_A
    
    def test_derived_quantities(self, physiology_module):
        """Derived quantities should be computed correctly."""
        physiology_module.state.L_cum = 1.0
        physiology_module.state.L_trans = 0.5
        physiology_module.state.C_base = 0.8
        
        physiology_module.state = physiology_module.coupling.update_derived_state(
            physiology_module.state
        )
        
        # L_total should be sum
        assert physiology_module.state.L_total == 1.5
        
        # C_eff should be C_base / (1 + L_total)
        expected_C_eff = 0.8 / (1.0 + 1.5)
        assert abs(physiology_module.state.C_eff - expected_C_eff) < 0.001


class TestEpochExecution:
    """Test complete epoch execution."""
    
    def test_epoch_execution(self, physiology_module):
        """Complete epoch should execute all fast steps + slow step."""
        N_fast = physiology_module.timescale.N_fast
        
        # Create inputs
        slow_input = SlowTimeInput(t_slow=1.0, I_slow=0.5)
        fast_inputs = [
            FastTimeInput(t_fast=float(i)/24.0, I_fast=0.0)
            for i in range(N_fast)
        ]
        
        # Run epoch
        slow_output, fast_outputs = physiology_module.run_epoch(
            slow_input,
            fast_inputs
        )
        
        # Should get correct number of outputs
        assert len(fast_outputs) == N_fast
        assert slow_output.t_slow == 1.0
        
        # Epoch number should increment
        assert physiology_module.state.epoch_number == 1
    
    def test_wrong_number_of_fast_inputs_raises(self, physiology_module):
        """Wrong number of fast inputs should raise."""
        slow_input = SlowTimeInput(t_slow=1.0, I_slow=0.5)
        fast_inputs = [FastTimeInput(t_fast=0.0, I_fast=0.0)]  # Only 1 instead of 24
        
        with pytest.raises(ValueError):
            physiology_module.run_epoch(slow_input, fast_inputs)


class TestConstraintEnforcement:
    """Test state constraint enforcement."""
    
    def test_negative_load_clamped(self, physiology_module):
        """Negative loads should be clamped to zero."""
        # Manually set negative (shouldn't happen in practice)
        physiology_module.state.L_cum = -0.5
        
        slow_input = SlowTimeInput(t_slow=1.0, I_slow=0.0)
        output = physiology_module.slow_time_step(slow_input)
        
        # Should be clamped
        assert output.state.L_cum >= 0.0
    
    def test_capacity_bounds_enforced(self, physiology_module):
        """Capacities should stay in [0, 1]."""
        # Set extreme values
        physiology_module.state.C_base = 0.01
        physiology_module.state.L_cum = 10.0
        
        # Run several steps
        for i in range(10):
            slow_input = SlowTimeInput(t_slow=float(i+1), I_slow=2.0)
            output = physiology_module.slow_time_step(slow_input)
        
        # Should be bounded
        assert 0.0 <= output.state.C_base <= 1.0
        assert 0.0 <= output.state.R_cap <= 1.0


class TestStability:
    """Test numerical stability and convergence."""
    
    def test_no_input_convergence(self, physiology_module):
        """Without inputs, state should converge."""
        # Run many epochs without input
        for epoch in range(50):
            slow_input = SlowTimeInput(t_slow=float(epoch+1), I_slow=0.0)
            fast_inputs = [
                FastTimeInput(t_fast=float(epoch) + float(i)/24.0, I_fast=0.0)
                for i in range(physiology_module.timescale.N_fast)
            ]
            
            slow_output, _ = physiology_module.run_epoch(slow_input, fast_inputs)
        
        # State should be stable (no divergence)
        assert not math.isnan(slow_output.state.C_base)
        assert not math.isinf(slow_output.state.L_cum)
        
        # Fast variables should be near baseline
        assert physiology_module.state.A_resp < 0.01
        assert physiology_module.state.xi > 0.99
    
    def test_bounded_evolution_with_moderate_input(self, physiology_module):
        """Moderate sustained input should produce bounded evolution."""
        for epoch in range(100):
            slow_input = SlowTimeInput(t_slow=float(epoch+1), I_slow=0.5)
            fast_inputs = [
                FastTimeInput(t_fast=float(epoch) + float(i)/24.0, I_fast=0.1)
                for i in range(physiology_module.timescale.N_fast)
            ]
            
            slow_output, _ = physiology_module.run_epoch(slow_input, fast_inputs)
        
        # No unbounded growth
        assert slow_output.state.L_cum < 100.0  # Reasonable bound
        assert 0.0 <= slow_output.state.C_base <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
