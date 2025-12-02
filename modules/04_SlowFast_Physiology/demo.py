"""
Example usage and demonstration of the Slow-Fast Physiology Module.

Demonstrates:
- Basic initialization and configuration
- Running epochs with stressor inputs
- Monitoring state evolution
- Response to acute and sustained stressors
"""

import matplotlib.pyplot as plt
from slowfast_physiology import (
    PhysiologyModule,
    PhysiologyState,
    PhysiologyParameters,
    TimescaleConfig,
    PhysiologyInitConfig,
    SlowTimeInput,
    FastTimeInput
)


def create_default_config():
    """Create a default configuration for demonstration."""
    # Initial state: healthy baseline with partial relaxation
    initial_state = PhysiologyState(
        C_base=1.0,
        L_cum=0.0,
        R_cap=1.0,
        A_resp=0.0,
        L_trans=0.0,
        xi=0.5  # Partially relaxed to allow acute response demonstration
    )
    
    # Parameters: moderate sensitivity
    parameters = PhysiologyParameters(
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
    
    # Timescale: 1 day slow, 1 hour fast
    timescale_config = TimescaleConfig(
        dt_slow=1.0,
        dt_fast=1.0/24.0,
        time_unit="days"
    )
    
    return PhysiologyInitConfig(
        initial_state=initial_state,
        parameters=parameters,
        timescale_config=timescale_config
    )


def example_1_basic_usage():
    """Example 1: Basic module initialization and single epoch."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Create configuration
    config = create_default_config()
    
    # Initialize module
    module = PhysiologyModule(config)
    print(f"Module initialized successfully")
    print(f"Initial state: C_base={module.state.C_base:.3f}, "
          f"L_cum={module.state.L_cum:.3f}")
    
    # Prepare inputs for one epoch (24 fast steps)
    slow_input = SlowTimeInput(t_slow=1.0, I_slow=0.5)
    fast_inputs = [
        FastTimeInput(t_fast=i/24.0, I_fast=0.0)
        for i in range(24)
    ]
    
    # Run one epoch
    slow_output, fast_outputs = module.run_epoch(slow_input, fast_inputs)
    
    print(f"After 1 epoch:")
    print(f"  C_base: {slow_output.state.C_base:.3f}")
    print(f"  L_cum: {slow_output.state.L_cum:.3f}")
    print(f"  R_cap: {slow_output.state.R_cap:.3f}")
    print(f"  Status: {slow_output.status}")
    print()


def example_2_sustained_stressor():
    """Example 2: Response to sustained slow-time stressor."""
    print("=" * 60)
    print("Example 2: Sustained Stressor Response")
    print("=" * 60)
    
    config = create_default_config()
    module = PhysiologyModule(config)
    
    # Track state evolution
    time_points = []
    C_base_values = []
    L_cum_values = []
    R_cap_values = []
    
    # Run 30 days with sustained stressor
    for day in range(30):
        slow_input = SlowTimeInput(t_slow=float(day+1), I_slow=1.0)
        fast_inputs = [
            FastTimeInput(t_fast=float(day) + i/24.0, I_fast=0.0)
            for i in range(24)
        ]
        
        slow_output, _ = module.run_epoch(slow_input, fast_inputs)
        
        time_points.append(day + 1)
        C_base_values.append(slow_output.state.C_base)
        L_cum_values.append(slow_output.state.L_cum)
        R_cap_values.append(slow_output.state.R_cap)
    
    # Print summary
    print(f"After 30 days of sustained stressor (I_slow=1.0):")
    print(f"  Initial C_base: 1.000 → Final: {C_base_values[-1]:.3f}")
    print(f"  Initial L_cum: 0.000 → Final: {L_cum_values[-1]:.3f}")
    print(f"  Initial R_cap: 1.000 → Final: {R_cap_values[-1]:.3f}")
    print()
    
    # Plot results
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    
    axes[0].plot(time_points, C_base_values, 'b-', linewidth=2)
    axes[0].set_ylabel('Baseline Capacity')
    axes[0].set_title('Slow-Time State Evolution (30 days, I_slow=1.0)')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(time_points, L_cum_values, 'r-', linewidth=2)
    axes[1].set_ylabel('Cumulative Load')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(time_points, R_cap_values, 'g-', linewidth=2)
    axes[2].set_ylabel('Recovery Capacity')
    axes[2].set_xlabel('Time (days)')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('sustained_stressor_response.png', dpi=150)
    print("Plot saved as 'sustained_stressor_response.png'")
    print()


def example_3_acute_stressor():
    """Example 3: Response to acute fast-time stressor."""
    print("=" * 60)
    print("Example 3: Acute Stressor Response")
    print("=" * 60)
    
    config = create_default_config()
    module = PhysiologyModule(config)
    
    # Track fast-time evolution for 2 days
    time_points = []
    A_resp_values = []
    xi_values = []
    
    for day in range(2):
        slow_input = SlowTimeInput(t_slow=float(day+1), I_slow=0.0)
        fast_inputs = []
        
        for hour in range(24):
            t_fast = float(day) + hour/24.0
            
            # Apply acute stressor at hour 5 of day 0
            if day == 0 and hour == 5:
                I_fast = 3.0
            else:
                I_fast = 0.0
            
            fast_inputs.append(FastTimeInput(t_fast=t_fast, I_fast=I_fast))
        
        slow_output, fast_outputs = module.run_epoch(slow_input, fast_inputs)
        
        # Record fast-time data
        for i, output in enumerate(fast_outputs):
            time_points.append(day + i/24.0)
            A_resp_values.append(output.state.A_resp)
            xi_values.append(output.state.xi)
    
    print(f"Acute stressor applied at t=5 hours (I_fast=3.0)")
    print(f"Peak A_resp: {max(A_resp_values):.3f}")
    print(f"A_resp at 24 hours: {A_resp_values[24]:.3f}")
    print(f"A_resp at 48 hours: {A_resp_values[-1]:.3f}")
    print()
    
    # Plot results
    fig, axes = plt.subplots(2, 1, figsize=(10, 6))
    
    axes[0].plot(time_points, A_resp_values, 'b-', linewidth=2)
    axes[0].axvline(x=5/24.0, color='r', linestyle='--', alpha=0.5, label='Stressor')
    axes[0].set_ylabel('Acute Response')
    axes[0].set_title('Fast-Time Response to Acute Stressor (48 hours)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(time_points, xi_values, 'g-', linewidth=2)
    axes[1].axvline(x=5/24.0, color='r', linestyle='--', alpha=0.5)
    axes[1].set_ylabel('Relaxation State (ξ)')
    axes[1].set_xlabel('Time (days)')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('acute_stressor_response.png', dpi=150)
    print("Plot saved as 'acute_stressor_response.png'")
    print()


def example_4_recovery():
    """Example 4: Recovery after stressor removal."""
    print("=" * 60)
    print("Example 4: Recovery Dynamics")
    print("=" * 60)
    
    config = create_default_config()
    module = PhysiologyModule(config)
    
    # Track state evolution
    time_points = []
    C_base_values = []
    L_cum_values = []
    C_eff_values = []
    
    # Phase 1: 20 days with stressor
    for day in range(20):
        slow_input = SlowTimeInput(t_slow=float(day+1), I_slow=1.2)
        fast_inputs = [
            FastTimeInput(t_fast=float(day) + i/24.0, I_fast=0.0)
            for i in range(24)
        ]
        
        slow_output, _ = module.run_epoch(slow_input, fast_inputs)
        
        time_points.append(day + 1)
        C_base_values.append(slow_output.state.C_base)
        L_cum_values.append(slow_output.state.L_cum)
        C_eff_values.append(module.state.C_eff)
    
    print(f"After 20 days of stressor:")
    print(f"  C_base: {C_base_values[-1]:.3f}")
    print(f"  L_cum: {L_cum_values[-1]:.3f}")
    print(f"  C_eff: {C_eff_values[-1]:.3f}")
    
    # Phase 2: 30 days recovery (no stressor)
    for day in range(20, 50):
        slow_input = SlowTimeInput(t_slow=float(day+1), I_slow=0.0)
        fast_inputs = [
            FastTimeInput(t_fast=float(day) + i/24.0, I_fast=0.0)
            for i in range(24)
        ]
        
        slow_output, _ = module.run_epoch(slow_input, fast_inputs)
        
        time_points.append(day + 1)
        C_base_values.append(slow_output.state.C_base)
        L_cum_values.append(slow_output.state.L_cum)
        C_eff_values.append(module.state.C_eff)
    
    print(f"\nAfter 30 days of recovery:")
    print(f"  C_base: {C_base_values[-1]:.3f}")
    print(f"  L_cum: {L_cum_values[-1]:.3f}")
    print(f"  C_eff: {C_eff_values[-1]:.3f}")
    print()
    
    # Plot results
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    
    axes[0].plot(time_points, C_base_values, 'b-', linewidth=2)
    axes[0].axvline(x=20, color='r', linestyle='--', alpha=0.5, label='Stressor removed')
    axes[0].set_ylabel('Baseline Capacity')
    axes[0].set_title('Recovery Dynamics (20 days stressor + 30 days recovery)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(time_points, L_cum_values, 'r-', linewidth=2)
    axes[1].axvline(x=20, color='r', linestyle='--', alpha=0.5)
    axes[1].set_ylabel('Cumulative Load')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(time_points, C_eff_values, 'g-', linewidth=2)
    axes[2].axvline(x=20, color='r', linestyle='--', alpha=0.5)
    axes[2].set_ylabel('Effective Capacity')
    axes[2].set_xlabel('Time (days)')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('recovery_dynamics.png', dpi=150)
    print("Plot saved as 'recovery_dynamics.png'")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Slow-Fast Physiology Module - Demonstration Examples")
    print("=" * 60 + "\n")
    
    # Run examples
    example_1_basic_usage()
    example_2_sustained_stressor()
    example_3_acute_stressor()
    example_4_recovery()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
