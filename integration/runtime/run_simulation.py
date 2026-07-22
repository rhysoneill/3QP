"""
Phase 5 Runtime Entrypoint - Run Simulation

Command-line interface for running the 3QP mission simulation with the
Ruthless Core Model.

This script:
1. Loads runtime configuration
2. Runs mission simulation via mission_runner (batch) or twin_runner (twin)
3. Logs outputs via logger
4. Validates trajectory via validator
5. Prints summary to console

Usage:
    python run_simulation.py [--config CONFIG_PATH] [--mission-name NAME] [--days DAYS]
    python run_simulation.py --mode twin --crew-preset chapea_a --mission-name twin_test --days 180

Examples:
    # Run with defaults (batch mode)
    python run_simulation.py

    # Run with custom config file
    python run_simulation.py --config my_mission.json

    # Run with custom parameters
    python run_simulation.py --mission-name test_mission --days 180

    # Run twin mode with crew preset
    python run_simulation.py --mode twin --crew-preset chapea_a --days 180

    # Run quiet (minimal output)
    python run_simulation.py --quiet
"""

import sys
import shutil
import argparse
from pathlib import Path

# Add runtime module to path
sys.path.insert(0, str(Path(__file__).parent))

from runtime_config import RuntimeConfig, get_default_config
from mission_runner import run_mission
from logger import write_mission_outputs
from validator import validate_mission_result
from twin_runner import TwinRunner, TwinRunnerConfig

# Add crew module to path for personality-based configuration
_crew_path = str(Path(__file__).parent.parent.parent)
if _crew_path not in sys.path:
    sys.path.insert(0, _crew_path)
from crew import get_crew_preset, PersonalityToConfigMapper


def _deliver_to_sojourner(mission_name: str, output_dir: str, verbose: bool = True) -> None:
    """
    Copy key 3QP output files into sojourner_box/ so HermitClaw picks them up.

    Delivers: summary, collapse fingerprint, trajectory classification.
    Skips silently if sojourner_box doesn't exist.
    Files are prefixed with '3qp_' to avoid collisions in the box.
    """
    sojourner_box = (
        Path(__file__).parent.parent.parent.parent / "hermitclaw" / "sojourner_box"
    )
    if not sojourner_box.exists():
        return

    output_path = Path(output_dir).resolve()
    to_deliver = [
        f"{mission_name}_summary.json",
        f"{mission_name}_collapse_fingerprint.json",
        f"{mission_name}_trajectory.json",
    ]

    delivered = []
    for fname in to_deliver:
        src = output_path / fname
        if src.exists():
            shutil.copy2(src, sojourner_box / f"3qp_{fname}")
            delivered.append(fname)

    if verbose and delivered:
        print(f"  → Sojourner: {', '.join(delivered)}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run 3QP mission simulation with Ruthless Core Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_simulation.py
  python run_simulation.py --config my_mission.json
  python run_simulation.py --mission-name test_mission --days 180
  python run_simulation.py --quiet
        """
    )
    
    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["batch", "twin"],
        default="batch",
        help="Simulation mode: 'batch' (default) or 'twin' (day-by-day per-agent twin)"
    )

    # Configuration options
    parser.add_argument(
        "--config",
        type=str,
        help="Path to runtime configuration JSON file"
    )
    
    parser.add_argument(
        "--mission-name",
        type=str,
        help="Mission name (overrides config file)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        help="Mission length in days (overrides config file)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for results (default: output)"
    )
    
    # Control flags
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip trajectory validation"
    )
    
    parser.add_argument(
        "--no-logging",
        action="store_true",
        help="Skip writing output files"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal console output"
    )

    parser.add_argument(
        "--crew-preset",
        type=str,
        dest="crew_preset",
        help="Crew personality preset name (required for --mode twin). "
             "Options: high_cohesion_team, fragile_team, extroverted_explorers"
    )

    parser.add_argument(
        "--inject-comms",
        type=str,
        dest="inject_comms",
        default=None,
        help=(
            "Schedule MC communications for twin mode. "
            "Format: 'type:day' (once) or 'type:start_day:freq' (recurring every freq days). "
            "Comma-separate multiple entries. "
            "Types: reassurance, direction, support, acknowledgment, resupply_announcement, "
            "celebration, peer_check, rest_authorization, schedule_relief. "
            "Run 'python interventions.py' for full catalogue. "
            "Example: --inject-comms 'celebration:120,rest_authorization:140:14'"
        ),
    )

    return parser.parse_args()


def load_runtime_config(args) -> RuntimeConfig:
    """
    Load runtime configuration from arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        RuntimeConfig instance
    """
    # Start with config file or defaults
    if args.config:
        print(f"Loading configuration from {args.config}")
        config = RuntimeConfig.from_json(args.config)
    else:
        config = get_default_config()
    
    # Apply command-line overrides
    if args.mission_name:
        config.mission_name = args.mission_name
    
    if args.days:
        config.mission_length_days = args.days
    
    if args.output_dir:
        config.output_dir = args.output_dir
    
    if args.no_validation:
        config.enable_validation = False
    
    if args.no_logging:
        config.enable_logging = False
    
    if args.quiet:
        config.verbose = False
    
    return config


def _parse_inject_comms(inject_comms_str: str, mission_length_days: int):
    """
    Parse --inject-comms string into a list of (day, MCCommunication) tuples.

    Format: 'type:day' or 'type:start_day:freq', comma-separated.
    Returns list of (day, MCCommunication) for all scheduled delivery days.

    All intervention types are defined in interventions.INTERVENTION_CATALOGUE.
    Run 'python interventions.py' to see a full formatted list.

    Examples:
        reassurance:150:7           reassurance every 7 days from day 150
        celebration:120             one-time celebration on day 120
        rest_authorization:140:14   rest day every 14 days from day 140
        schedule_relief:160         one-time schedule relief on day 160
    """
    from interventions import INTERVENTION_CATALOGUE, make_comm

    scheduled = []
    for entry in inject_comms_str.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) < 2:
            print(f"[WARNING] Skipping invalid --inject-comms entry: '{entry}'")
            continue
        msg_type = parts[0].strip()
        if msg_type not in INTERVENTION_CATALOGUE:
            print(f"[WARNING] Unknown comm type '{msg_type}' — skipping. "
                  f"Run 'python interventions.py' to see valid types.")
            continue
        try:
            start_day = int(parts[1].strip())
            freq = int(parts[2].strip()) if len(parts) >= 3 else 0
        except ValueError:
            print(f"[WARNING] Skipping invalid --inject-comms entry: '{entry}'")
            continue

        days_to_schedule = [start_day] if freq == 0 else list(
            range(start_day, mission_length_days + 1, freq)
        )
        for d in days_to_schedule:
            if 1 <= d <= mission_length_days:
                scheduled.append((d, make_comm(msg_type, day=d)))

    return scheduled


def run_twin_mode(args, config: RuntimeConfig) -> None:
    """
    Run simulation in twin mode (day-by-day per-agent behavioral twin).

    Requires --crew-preset to be specified (twin mode is per-agent and needs
    a crew profile). The TwinRunner writes per-day JSON files and a summary.

    Args:
        args:   Parsed CLI arguments
        config: RuntimeConfig (used for mission_name, days, output_dir, verbose)
    """
    crew_preset = getattr(args, "crew_preset", None) or config.crew_preset
    if not crew_preset:
        print("\n[ERROR] --mode twin requires --crew-preset to be specified.")
        print("  Example: python run_simulation.py --mode twin --crew-preset chapea_a --days 180")
        sys.exit(1)

    try:
        crew_profile = get_crew_preset(crew_preset)
    except KeyError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to load crew preset: {e}")
        sys.exit(1)

    from resources.resource_model import ResourceConfig
    twin_config = TwinRunnerConfig(
        mission_name=config.mission_name,
        mission_length_days=config.mission_length_days,
        crew_profile=crew_profile,
        resource_config=ResourceConfig(),
        output_dir=config.output_dir,
        verbose=config.verbose,
    )

    if config.verbose:
        print(f"[TwinRunner] Mode: twin")
        print(f"[TwinRunner] Crew preset: {crew_preset} ({crew_profile.crew_name})")
        print(f"[TwinRunner] Members: {[m.name for m in crew_profile.members]}")
        print()

    try:
        runner = TwinRunner(twin_config)

        # Schedule any MC communications provided via --inject-comms
        inject_comms_str = getattr(args, "inject_comms", None)
        if inject_comms_str:
            scheduled = _parse_inject_comms(inject_comms_str, config.mission_length_days)
            for day, comm in scheduled:
                runner.schedule_mc_communication(day, comm)
            if config.verbose and scheduled:
                print(f"[TwinRunner] Scheduled {len(scheduled)} MC communication(s)")

        result = runner.run()
    except Exception as e:
        print(f"\n[ERROR] Twin simulation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    summary = result.get_summary()
    print()
    print(f"Twin simulation complete: {twin_config.mission_name}")
    print(f"  Final cohesion: {summary['physics']['final_cohesion']:.3f}")
    print(f"  Min cohesion: {summary['physics']['min_cohesion']:.3f} (day {summary['physics']['min_cohesion_day']})")
    print(f"  HermitClaw advisories: {summary['hermitclaw']['advisories_generated']}"
          f" ({summary['hermitclaw']['critical_advisories']} critical)")
    print(f"  Output: {result.metadata['output_path']}")

    # Deliver key files to Sojourner
    _sojourner_box = (
        Path(__file__).parent.parent.parent.parent / "hermitclaw" / "sojourner_box"
    )
    if _sojourner_box.exists():
        twin_output = Path(result.metadata["output_path"]).resolve()
        delivered = []
        for src, dst in [
            ("summary.json", f"3qp_{twin_config.mission_name}_twin_summary.json"),
            ("hermitclaw_log.json", f"3qp_{twin_config.mission_name}_hermitclaw_log.json"),
        ]:
            if (twin_output / src).exists():
                shutil.copy2(twin_output / src, _sojourner_box / dst)
                delivered.append(src)
        if config.verbose and delivered:
            print(f"  → Sojourner: {', '.join(delivered)}")


def main():
    """Main entrypoint for simulation."""
    print("="*60)
    print("3QP Phase 5 Runtime - Mission Simulation")
    print("="*60)
    print()
    
    # Parse arguments and load configuration
    args = parse_args()
    config = load_runtime_config(args)
    
    if config.verbose:
        print(f"Configuration:")
        print(f"  Mission: {config.mission_name}")
        print(f"  Duration: {config.mission_length_days} days")
        print(f"  Output: {config.output_dir}")
        print(f"  Validation: {'enabled' if config.enable_validation else 'disabled'}")
        if config.crew_preset:
            print(f"  Crew Preset: {config.crew_preset}")
        print()
    
    # Dispatch to twin mode if requested
    if args.mode == "twin":
        run_twin_mode(args, config)
        return

    # --- Batch mode (existing behavior, unchanged) ---
    # Handle crew-based configuration if preset is specified
    core_config = None
    crew_profile = None
    if config.crew_preset:
        try:
            if config.verbose:
                print(f"Loading crew preset: {config.crew_preset}")
            
            crew_profile = get_crew_preset(config.crew_preset)
            mapper = PersonalityToConfigMapper()
            core_config = mapper.map_to_ruthless_config(
                crew_profile,
                config.mission_length_days
            )
            
            if config.verbose:
                print(f"  Crew: {crew_profile.crew_name}")
                print(f"  Members: {len(crew_profile.members)}")
                traits = crew_profile.aggregate_traits()
                print(f"  Aggregate Traits:")
                print(f"    Openness: {traits.openness:.2f}")
                print(f"    Conscientiousness: {traits.conscientiousness:.2f}")
                print(f"    Extraversion: {traits.extraversion:.2f}")
                print(f"    Agreeableness: {traits.agreeableness:.2f}")
                print(f"    Neuroticism: {traits.neuroticism:.2f}")
                print(f"  Mapped to RuthlessCoreConfig with adjusted parameters")
                print()
        except KeyError as e:
            print(f"\n[ERROR] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Failed to load crew preset: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Run mission simulation
    try:
        result = run_mission(config, core_config=core_config, crew_profile=crew_profile)
        
        # Add crew information to metadata if used
        if crew_profile is not None:
            result.metadata["crew_name"] = crew_profile.crew_name
            result.metadata["crew_preset"] = config.crew_preset
            traits = crew_profile.aggregate_traits()
            result.metadata["crew_traits"] = {
                "openness": traits.openness,
                "conscientiousness": traits.conscientiousness,
                "extraversion": traits.extraversion,
                "agreeableness": traits.agreeableness,
                "neuroticism": traits.neuroticism,
            }
    except Exception as e:
        print(f"\n[ERROR] Mission simulation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Write outputs
    if config.enable_logging:
        try:
            write_mission_outputs(
                result,
                output_dir=config.output_dir,
                verbose=config.verbose
            )
            _deliver_to_sojourner(
                config.mission_name,
                output_dir=config.output_dir,
                verbose=config.verbose,
            )
        except Exception as e:
            print(f"\n[WARNING] Failed to write outputs: {e}")
    
    # Run validation
    if config.enable_validation:
        try:
            validation_result = validate_mission_result(
                result,
                output_dir=config.output_dir,
                verbose=config.verbose
            )
            
            # Print validation status
            if validation_result["overall_status"] == "PASS":
                print("\n✓ Validation PASSED - TQP trajectory correctly detected")
            else:
                print("\n✗ Validation FAILED - See validation report for details")
                sys.exit(1)
        except Exception as e:
            print(f"\n[WARNING] Failed to run validation: {e}")
    
    print("\nSimulation complete.")
    if config.crew_preset:
        print(f"  Crew: {crew_profile.crew_name} ({config.crew_preset})")
    print(f"Results available in: {Path(config.output_dir).absolute()}")


if __name__ == "__main__":
    main()
