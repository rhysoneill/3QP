"""
3QP Five-Minute Demo
====================

Runs two matched simulations (fragile crew, with and without MC intervention),
then optionally a high-cohesion crew for personality contrast, and produces a
single comparison chart.

Usage:
    cd integration/runtime
    python -X utf8 demo.py

Output:
    output/demo_comparison.png  (saved)
    Chart displayed on screen

No arguments required. All parameters are hard-coded for a clean, reproducible demo.
"""

import json
import sys
import warnings
from pathlib import Path

# --- path setup ---
_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent
_PHASE4 = _ROOT / "phase4" / "06_Ruthless_Core_Model"
_SOCIAL_NET = _ROOT / "modules" / "05_Social_Network"
for p in [str(_ROOT), str(_PHASE4), str(_SOCIAL_NET)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from twin_runner import TwinRunner, TwinRunnerConfig
from resources.resource_model import ResourceConfig
from mission_control.mc_types import MCCommunication
from crew import get_crew_preset

# ---------------------------------------------------------------------------
# Demo parameters
# ---------------------------------------------------------------------------

MISSION_DAYS = 200
MC_COMMS_START_DAY = 100
MC_COMMS_FREQ = 7       # Every 7 days
DEMO_SEED = 42          # Shared seed: all scenarios experience identical daily events
OUTPUT_DIR = str(_HERE / "output")
CHART_PATH = str(_HERE / "output" / "demo_comparison.png")


def _reassurance_comm(day: int) -> MCCommunication:
    return MCCommunication(
        day=day,
        sender="mission_control",
        message_type="reassurance",
        content=f"MC psychological support check-in (day {day})",
        belief_mc_support_delta=0.08,
        belief_resupply_reliability_delta=0.0,
    )


def run_scenario(label: str, crew_preset: str, inject_comms: bool) -> list:
    """
    Run one twin simulation and return list of per-day physics dicts.
    Returns: [{"day": N, "cohesion": C, "strain": S, "monotony": M,
               "tq_pressure": Q, "social_cohesion": SC}, ...]
    """
    print(f"  Running: {label}...", end=" ", flush=True)
    crew = get_crew_preset(crew_preset)
    config = TwinRunnerConfig(
        mission_name=f"demo_{crew_preset}_{'mc' if inject_comms else 'no_mc'}",
        mission_length_days=MISSION_DAYS,
        crew_profile=crew,
        resource_config=ResourceConfig(),
        output_dir=OUTPUT_DIR,
        verbose=False,
        random_seed=DEMO_SEED,
    )
    runner = TwinRunner(config)

    if inject_comms:
        for day in range(MC_COMMS_START_DAY, MISSION_DAYS + 1, MC_COMMS_FREQ):
            runner.schedule_mc_communication(day, _reassurance_comm(day))

    result = runner.run()

    rows = []
    for ds in result.day_states:
        sn  = ds.social_network or {}
        to  = ds.task_outcomes   or {}
        tm  = to.get("metrics", {})
        # Critical completion rate from per-task results
        task_results = to.get("task_results", [])
        high_tasks = [t for t in task_results if t.get("criticality") == "high"]
        critical_rate = (
            sum(1 for t in high_tasks if t["outcome"] == "completed") / len(high_tasks)
            if high_tasks else None
        )
        rows.append({
            "day":                      ds.day,
            "cohesion":                 ds.core_cohesion,
            "strain":                   ds.core_strain,
            "monotony":                 ds.core_monotony,
            "tq_pressure":              ds.core_tq_pressure,
            "social_cohesion":          sn.get("global_cohesion", None),
            "coord_failure_rate":       tm.get("coordination_failure_rate", 0.0),
            "checklist_miss_rate":      tm.get("checklist_miss_rate", 0.0),
            "planning_error_rate":      tm.get("planning_error_rate", 0.0),
            "maintenance_skip_rate":    tm.get("maintenance_skip_rate", 0.0),
            "critical_completion_rate": critical_rate,
        })

    print(f"done (strain peak: {max(r['strain'] for r in rows):.3f})")
    return rows


def plot(scenarios: dict) -> None:
    """
    Produce a 3-panel comparison chart and save to CHART_PATH.
    scenarios: {label: [rows]}
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend; safe on any machine
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("\n[demo] matplotlib not installed — skipping chart.")
        print("[demo] Install with: pip install matplotlib")
        _print_text_summary(scenarios)
        return

    days = list(range(1, MISSION_DAYS + 1))

    # Color palette
    COLORS = {
        "Fragile crew — no MC support":         "#E05C5C",   # red
        "Fragile crew — MC support from day 100": "#4A90D9", # blue
        "High-cohesion crew — no MC support":    "#5CA85C",  # green
    }
    STYLES = {
        "Fragile crew — no MC support":         "-",
        "Fragile crew — MC support from day 100": "-",
        "High-cohesion crew — no MC support":    "--",
    }

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(
        "3QP — Lunar Crew Behavioral Twin: 200-Day Mission Comparison",
        fontsize=14, fontweight="bold", y=0.98
    )

    # Panel 1: Cohesion
    ax = axes[0]
    for label, rows in scenarios.items():
        c_vals = [r["cohesion"] for r in rows]
        ax.plot(days, c_vals, color=COLORS[label], linestyle=STYLES[label],
                linewidth=2, label=label)
    ax.axvspan(0.5 * MISSION_DAYS, 0.75 * MISSION_DAYS, alpha=0.07,
               color="orange", label="Third quarter window")
    ax.axvline(MC_COMMS_START_DAY, color="#4A90D9", linestyle=":", linewidth=1.2,
               alpha=0.7, label=f"MC support begins (day {MC_COMMS_START_DAY})")
    ax.set_ylabel("Cohesion (C)", fontsize=10)
    ax.set_title("Social cohesion over mission", fontsize=10)
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    # Panel 2: Strain
    ax = axes[1]
    for label, rows in scenarios.items():
        s_vals = [r["strain"] for r in rows]
        ax.plot(days, s_vals, color=COLORS[label], linestyle=STYLES[label],
                linewidth=2)
    ax.axvspan(0.5 * MISSION_DAYS, 0.75 * MISSION_DAYS, alpha=0.07, color="orange")
    ax.axvline(MC_COMMS_START_DAY, color="#4A90D9", linestyle=":", linewidth=1.2,
               alpha=0.7)
    ax.set_ylabel("Strain (S)", fontsize=10)
    ax.set_title("Accumulated psychological strain", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    # Panel 3: Social network cohesion (from Module 05 graph)
    ax = axes[2]
    for label, rows in scenarios.items():
        sc_vals = [r["social_cohesion"] for r in rows if r["social_cohesion"] is not None]
        sc_days = [r["day"] for r in rows if r["social_cohesion"] is not None]
        if sc_vals:
            ax.plot(sc_days, sc_vals, color=COLORS[label], linestyle=STYLES[label],
                    linewidth=2)
    ax.axvspan(0.5 * MISSION_DAYS, 0.75 * MISSION_DAYS, alpha=0.07, color="orange")
    ax.axvline(MC_COMMS_START_DAY, color="#4A90D9", linestyle=":", linewidth=1.2,
               alpha=0.7)
    ax.set_ylabel("Graph edge weight", fontsize=10)
    ax.set_title("Social network cohesion (Module 05 — full graph dynamics)", fontsize=10)
    ax.set_xlabel("Mission day", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    # Annotation: key findings
    fragile_no_mc = scenarios.get("Fragile crew — no MC support", [])
    fragile_mc    = scenarios.get("Fragile crew — MC support from day 100", [])
    if fragile_no_mc and fragile_mc:
        s_peak_no_mc = max(r["strain"] for r in fragile_no_mc)
        s_peak_mc    = max(r["strain"] for r in fragile_mc)
        reduction    = (s_peak_no_mc - s_peak_mc) / s_peak_no_mc * 100 if s_peak_no_mc > 0 else 0
        fig.text(
            0.72, 0.04,
            f"MC support effect:\n"
            f"Peak strain  {s_peak_no_mc:.3f}  →  {s_peak_mc:.3f}\n"
            f"Reduction: {reduction:.0f}%",
            fontsize=9,
            verticalalignment="bottom",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8F4FD", edgecolor="#4A90D9",
                      alpha=0.9),
        )

    plt.tight_layout(rect=[0, 0.05, 1, 0.97])

    Path(CHART_PATH).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(CHART_PATH, dpi=150, bbox_inches="tight")
    print(f"\n  Chart saved: {CHART_PATH}")

    # Try to display; silently skip if headless
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.show()
    except Exception:
        pass


def _print_text_summary(scenarios: dict) -> None:
    """Fallback text summary when matplotlib is unavailable."""
    print("\n--- TEXT SUMMARY ---")
    for label, rows in scenarios.items():
        s_peak = max(r["strain"] for r in rows)
        c_min  = min(r["cohesion"] for r in rows)
        c_min_day = next(r["day"] for r in rows if r["cohesion"] == c_min)
        print(f"\n{label}")
        print(f"  Peak strain:       {s_peak:.4f}")
        print(f"  Min cohesion:      {c_min:.4f}  (day {c_min_day})")
    print()


def main():
    print("=" * 60)
    print("3QP — Five-Minute Demo")
    print("=" * 60)
    print(f"\nMission: {MISSION_DAYS} days | Crew: 4 astronauts")
    print(f"MC support: reassurance every {MC_COMMS_FREQ} days from day {MC_COMMS_START_DAY}")
    print()

    scenarios = {}

    scenarios["Fragile crew — no MC support"] = run_scenario(
        "Fragile crew — no MC support",
        crew_preset="fragile_team",
        inject_comms=False,
    )
    scenarios["Fragile crew — MC support from day 100"] = run_scenario(
        "Fragile crew — MC support from day 100",
        crew_preset="fragile_team",
        inject_comms=True,
    )
    scenarios["High-cohesion crew — no MC support"] = run_scenario(
        "High-cohesion crew — no MC support",
        crew_preset="high_cohesion_team",
        inject_comms=False,
    )

    print("\nGenerating comparison chart...")
    plot(scenarios)
    print("\nDone.")


if __name__ == "__main__":
    main()
