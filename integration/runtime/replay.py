"""
replay.py — Deterministic Mission Replay

Replays a simulation run from a run_manifest.json file and compares
deterministic summary fields to verify exact reproduction.

Usage:
    python replay.py output/mission_name/run_manifest.json
    python replay.py output/mission_name/run_manifest.json --verbose
    python replay.py output/mission_name/run_manifest.json --output-dir /tmp/replay_out

Exit codes:
    0  — replay successful (or no original summary to compare against)
    1  — manifest/input error
    2  — hash mismatch (replay diverged from original)

Seed lineage (from run_manifest.json):
    random_seed_input  — the value originally passed to TwinRunnerConfig.random_seed
    event_seed         — the derived RNG seed actually used by MicroEventEngine
    task_seed          — event_seed + TASK_RNG_SEED_OFFSET (TaskPerformanceEngine)

To replay exactly, set TwinRunnerConfig.random_seed = manifest["seeds"]["event_seed"].
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# --- path setup: mirror twin_runner.py so all module imports resolve ---
_RUNTIME_DIR = Path(__file__).parent
_ROOT = _RUNTIME_DIR.parent.parent
_PHASE4 = _ROOT / "phase4" / "06_Ruthless_Core_Model"
_SOCIAL_NET = _ROOT / "modules" / "05_Social_Network"
for _p in [str(_RUNTIME_DIR), str(_ROOT), str(_PHASE4), str(_SOCIAL_NET)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from crew.profile import CrewProfile, CrewMember
from resources.resource_model import ResourceConfig
from twin_runner import TwinRunner, TwinRunnerConfig
from run_manifest import hash_summary


# ---------------------------------------------------------------------------
# Personality proxy
# ---------------------------------------------------------------------------

@dataclass
class _Personality:
    """
    Duck-typed personality proxy for reconstruction from manifest data.

    Satisfies the attribute interface used by TwinRunner and PersonalityToConfigMapper:
        p.openness, p.conscientiousness, p.extraversion, p.agreeableness, p.neuroticism
    """
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float


# ---------------------------------------------------------------------------
# Manifest loading and config reconstruction
# ---------------------------------------------------------------------------

def load_manifest(manifest_path: Path) -> dict:
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


def reconstruct_crew(manifest: dict) -> CrewProfile:
    """Rebuild CrewProfile from manifest crew array."""
    members = []
    for m in manifest["mission"]["crew"]:
        p = m["personality"]
        members.append(CrewMember(
            name=m["name"],
            personality=_Personality(
                openness=p["openness"],
                conscientiousness=p["conscientiousness"],
                extraversion=p["extraversion"],
                agreeableness=p["agreeableness"],
                neuroticism=p["neuroticism"],
            ),
        ))
    return CrewProfile(
        crew_name=manifest["mission"]["crew_name"],
        members=members,
    )


def reconstruct_resource_config(manifest: dict) -> ResourceConfig:
    """Rebuild ResourceConfig from manifest resource_config block."""
    rc = manifest["resource_config"]
    return ResourceConfig(
        initial_coffee=rc["initial_coffee"],
        initial_food_variety=rc["initial_food_variety"],
        initial_sleep_quality=rc["initial_sleep_quality"],
        initial_task_load=rc["initial_task_load"],
    )


# ---------------------------------------------------------------------------
# Deterministic summary subset for hash comparison
# ---------------------------------------------------------------------------

def _deterministic_subset(summary: dict) -> dict:
    """
    Extract only deterministic fields from a summary dict for hash comparison.

    Excludes time-varying metadata (start_time, end_time, duration_seconds,
    output_path) so that hashes match across replays run at different times
    or written to different directories.
    """
    return {
        "schema_version": summary.get("schema_version"),
        "mission_name":   summary.get("mission_name"),
        "mission_length_days": summary.get("mission_length_days"),
        "crew_size":      summary.get("crew_size"),
        "physics":        summary.get("physics"),
        "hermitclaw":     summary.get("hermitclaw"),
        "kpis":           summary.get("kpis"),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay a 3QP mission run from run_manifest.json and verify reproducibility.",
    )
    parser.add_argument("manifest", help="Path to run_manifest.json")
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print day-by-day simulation progress",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help=(
            "Directory for replay output files. "
            "Defaults to the same parent as the original output (written to <mission>_replay/)."
        ),
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"Error: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(manifest_path)
    original_dir = manifest_path.parent

    # ── Read original summary for hash comparison ──
    original_hash: str | None = None
    original_summary_path = original_dir / "summary.json"
    if original_summary_path.exists():
        with open(original_summary_path, encoding="utf-8") as f:
            original_summary = json.load(f)
        original_hash = hash_summary(_deterministic_subset(original_summary))
        print(f"Original summary hash : {original_hash}")
    else:
        print(
            f"Warning: summary.json not found at {original_summary_path}. "
            "Hash comparison will be skipped.",
        )

    # ── Reconstruct config ──
    crew_profile    = reconstruct_crew(manifest)
    resource_config = reconstruct_resource_config(manifest)
    event_seed      = manifest["seeds"]["event_seed"]
    mission_name    = manifest["mission"]["name"]
    mission_length  = manifest["mission"]["length_days"]

    output_dir          = args.output_dir or str(original_dir.parent)
    replay_mission_name = f"{mission_name}_replay"

    config = TwinRunnerConfig(
        mission_name=replay_mission_name,
        mission_length_days=mission_length,
        crew_profile=crew_profile,
        resource_config=resource_config,
        random_seed=event_seed,   # must equal event_seed, not random_seed_input
        output_dir=output_dir,
        verbose=args.verbose,
    )

    print(f"Replaying : {mission_name}  ({mission_length} days, seed={event_seed})")
    runner = TwinRunner(config)
    result = runner.run()

    replay_hash = hash_summary(_deterministic_subset(result.get_summary()))
    print(f"Replay summary hash   : {replay_hash}")

    if original_hash is not None:
        if replay_hash == original_hash:
            print("PASS — Replay is bit-exact with original run.")
        else:
            print("FAIL — Hashes differ. Replay does not reproduce original.")
            print(
                "       Common causes: schema_version bump, params change, "
                "or crew/seed/resource_config mismatch.",
            )
            sys.exit(2)
    else:
        print(f"Replay complete. Output: {result.metadata['output_path']}")


if __name__ == "__main__":
    main()
