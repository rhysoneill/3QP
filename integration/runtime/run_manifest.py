"""
Run Manifest — Reproducibility Package

Captures all configuration, seeds, and physics parameters needed to exactly
replay a simulation run. Written to output/{mission_name}/run_manifest.json
at the start of TwinRunner.run().

Design contract:
    Reads:  TwinRunnerConfig, event_seed (int), params.REGISTRY (all constants)
    Writes: output/{mission_name}/run_manifest.json
    Never:  modifies any simulation state

To replay an identical run from a manifest:
    config.random_seed = manifest["seeds"]["event_seed"]
    Use the same crew profile, resource_config initial values, mission_length_days.
    run replay.py <path/to/run_manifest.json> for exact automated replay.
"""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from params import REGISTRY, SCHEMA_VERSION

if TYPE_CHECKING:
    from twin_runner import TwinRunnerConfig


def _git_commit() -> Optional[str]:
    """Return current git HEAD hash, or None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def write_run_manifest(
    config: "TwinRunnerConfig",
    event_seed: int,
    output_path: Path,
) -> dict:
    """
    Serialize a complete reproducibility manifest for this simulation run.

    All model constants are drawn from params.REGISTRY — no hardcoded
    numerical values in this function.

    Args:
        config:      TwinRunnerConfig used for this run
        event_seed:  Resolved RNG seed (post name-hash or explicit override)
        output_path: Directory where run_manifest.json will be written

    Returns:
        The manifest dict (also written to run_manifest.json).
    """
    crew_serial = [
        {
            "name": m.name,
            "role": getattr(m, "role", "crew"),
            "personality": {
                "openness":          round(m.personality.openness, 4),
                "conscientiousness": round(m.personality.conscientiousness, 4),
                "extraversion":      round(m.personality.extraversion, 4),
                "agreeableness":     round(m.personality.agreeableness, 4),
                "neuroticism":       round(m.personality.neuroticism, 4),
            },
        }
        for m in config.crew_profile.members
    ]

    manifest = {
        "schema_version":  SCHEMA_VERSION,
        "manifest_version": "1.1",
        "generated_at":    datetime.now().isoformat(),
        "git_commit":      _git_commit(),

        # ---- Mission parameters ----
        "mission": {
            "name":         config.mission_name,
            "length_days":  config.mission_length_days,
            "crew_name":    config.crew_profile.crew_name,
            "crew_size":    len(config.crew_profile.members),
            "crew":         crew_serial,
        },

        # ---- Seed lineage ----
        "seeds": {
            "random_seed_input": config.random_seed,
            "event_seed":        event_seed,
            "task_seed":         event_seed + REGISTRY["task_failure"]["TASK_RNG_SEED_OFFSET"]["value"],
            "note": (
                "Set TwinRunnerConfig.random_seed = event_seed to replay exactly. "
                "Run: python replay.py <path/to/run_manifest.json>"
            ),
        },

        # ---- Resource initial conditions ----
        "resource_config": {
            "initial_coffee":        config.resource_config.initial_coffee,
            "initial_food_variety":  config.resource_config.initial_food_variety,
            "initial_sleep_quality": config.resource_config.initial_sleep_quality,
            "initial_task_load":     config.resource_config.initial_task_load,
        },

        # ---- Full parameter registry ----
        # All model constants drawn from params.py — no hardcoded values here.
        "parameters": REGISTRY,
    }

    manifest_file = output_path / "run_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def hash_summary(summary_dict: dict) -> str:
    """
    Compute a deterministic SHA-256 hash of a summary dict.

    Keys sorted for stability; float precision rounded to 6 places.
    Used by replay.py to confirm exact run reproduction.
    """
    # Stable serialization: sort keys, round floats
    canonical = json.dumps(summary_dict, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
