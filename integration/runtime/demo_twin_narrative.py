"""
demo_twin_narrative.py — 30-day Twin Mission with Live LLM Narrative

Runs the full behavioral twin pipeline for 30 days (fragile_team preset),
then renders LLM-generated narrative for each agent each day.

Usage:
    cd integration/runtime
    python -X utf8 demo_twin_narrative.py

Estimated API cost: ~$0.03-0.05
    (30 days x 4 agents x 3 calls = 360 calls @ gpt-4o-mini)

What you're seeing:
    - Per-day physics output (crew-level strain, cohesion, monotony, TQ)
    - Per-agent internal state (stress, trust, boredom, outlook)
    - Per-agent action selection + LLM-rendered narrative
    - HermitClaw advisories flagged when urgency fires
    - MC communications when HermitClaw dispatches them
"""

import sys
import os
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent                     # integration/runtime/
_ROOT = _HERE.parent.parent                                 # 3QP/
_PHASE4 = _ROOT / "phase4" / "06_Ruthless_Core_Model"

for _p in [str(_ROOT), str(_PHASE4), str(_HERE)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Windows UTF-8 (handles checkmarks, em-dashes, etc.)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Imports ───────────────────────────────────────────────────────────────────
from twin_runner import TwinRunner, TwinRunnerConfig          # local to runtime/
from resources.resource_model import ResourceConfig
from crew.examples import get_crew_preset
from agents.actions import AgentState, AgentAction, ActionType
from agents.narrative_renderer import NarrativeRenderer
from agents.llm_backend import OpenAIBackend

# ── Config ────────────────────────────────────────────────────────────────────
MISSION_DAYS = 30
CREW_PRESET  = "fragile_team"
MISSION_NAME = "demo_twin_30d"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bar(value: float, width: int = 12) -> str:
    """ASCII progress bar for a [0,1] value."""
    filled = round(value * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _reconstruct_state(agent_id: str, day: int, internal: dict,
                       mission_length: int) -> AgentState:
    """
    Build AgentState from AstronautInternalState dict.

    Mapping (locked — do not change without updating per_agent_selector.py):
        strain         <- stress
        cohesion       <- trust_in_crew
        monotony       <- boredom
        tq_pressure    <- (1 - future_outlook) * 0.5
        mission_progress <- day / mission_length
    """
    return AgentState(
        agent_id=agent_id,
        day=day,
        strain=internal["stress"],
        cohesion=internal["trust_in_crew"],
        monotony=internal["boredom"],
        tq_pressure=(1.0 - internal["future_outlook"]) * 0.5,
        mission_progress=day / mission_length,
    )


def _reconstruct_action(agent_id: str, day: int,
                        action_dict: dict, state: AgentState) -> AgentAction:
    """Rebuild AgentAction from its to_dict() output."""
    return AgentAction(
        agent_id=agent_id,
        day=day,
        action_type=ActionType(action_dict["action_type"]),
        state_snapshot=state,
        metadata=action_dict.get("metadata"),
    )


def _short_name(agent_id: str) -> str:
    """Return first name only for compact display."""
    return agent_id.split()[0]


def _action_symbol(action_type_str: str) -> str:
    symbols = {
        "withdraw":  "(-)",
        "engage":    "(+)",
        "support":   "(^)",
        "escalate":  "(!)",
        "maintain":  "(=)",
    }
    return symbols.get(action_type_str.lower(), "(?)")


# ── Main demo ─────────────────────────────────────────────────────────────────

def run_demo():

    # --- Build crew and config ---------------------------------------------
    crew = get_crew_preset(CREW_PRESET)
    print(f"\n3QP Behavioral Twin — {MISSION_DAYS}-Day Demo")
    print(f"Crew preset  : {CREW_PRESET}")
    print(f"Crew members : {', '.join(m.name for m in crew.members)}")
    print(f"Mission days : {MISSION_DAYS}")
    print()

    # --- Initialise LLM backend -------------------------------------------
    try:
        llm = OpenAIBackend()
        print("LLM backend  : OpenAI gpt-4o-mini (live)")
    except Exception as exc:
        print(f"LLM backend  : rule-based fallback ({exc})")
        llm = None

    renderer = NarrativeRenderer(
        enable_dialogue=True,
        enable_narrative=True,
        llm_backend=llm,
    )

    print()

    # --- Run twin simulation ----------------------------------------------
    cfg = TwinRunnerConfig(
        mission_name=MISSION_NAME,
        mission_length_days=MISSION_DAYS,
        crew_profile=crew,
        resource_config=ResourceConfig(),
        verbose=False,
    )

    print("Running twin simulation ... ", end="", flush=True)
    runner = TwinRunner(cfg)
    result = runner.run()
    print(f"done. ({len(result.day_states)} day states)\n")

    agent_ids = [m.name for m in crew.members]

    # --- Iterate day states -----------------------------------------------
    for ds in result.day_states:

        day = ds.day

        # Physics header
        print("=" * 66)
        print(
            f"  DAY {day:>3d}  |  "
            f"Cohesion: {ds.core_cohesion:.3f}  "
            f"Strain: {ds.core_strain:.3f}  "
            f"TQ: {ds.core_tq_pressure:.3f}  "
            f"Monotony: {ds.core_monotony:.3f}"
        )
        if ds.micro_event:
            print(f"  EVENT: {ds.micro_event}")
        print("=" * 66)

        # Per-agent narrative
        for agent_id in agent_ids:
            internal_d = ds.internal_states.get(agent_id, {})
            action_d   = ds.crew_actions.get(agent_id, {})

            if not internal_d or not action_d:
                continue

            state  = _reconstruct_state(agent_id, day, internal_d, MISSION_DAYS)
            action = _reconstruct_action(agent_id, day, action_d, state)

            # Render (LLM or fallback)
            try:
                output = renderer.render(action, state)
            except Exception as exc:
                print(f"  [{agent_id}] render error: {exc}")
                continue

            at_str = action_d.get("action_type", "?").upper()
            sym    = _action_symbol(action_d.get("action_type", ""))
            name   = _short_name(agent_id)

            print(f"\n  {sym} {name:<10}  [{at_str}]")
            print(f"     Stress {_bar(internal_d['stress'])} "
                  f"{internal_d['stress']:.2f}  |  "
                  f"Trust {_bar(internal_d['trust_in_crew'])} "
                  f"{internal_d['trust_in_crew']:.2f}")
            print(f"     Boredom {_bar(internal_d['boredom'])} "
                  f"{internal_d['boredom']:.2f}  |  "
                  f"Outlook {_bar(internal_d['future_outlook'])} "
                  f"{internal_d['future_outlook']:.2f}")

            if output.expressed_intent:
                print(f"  >> {output.expressed_intent}")

            if output.dialogue:
                print(f'     "{output.dialogue}"')

            if output.narrative_summary:
                print(f"     {output.narrative_summary}")

        # HermitClaw advisory (only when it fires)
        if ds.hermitclaw_advisory:
            adv = ds.hermitclaw_advisory
            urgency = adv.get("urgency", 0.0)
            if urgency > 0:
                tag = "CRITICAL" if urgency >= 0.65 else "ADVISORY"
                print(f"\n  ** HERMITCLAW {tag} (urgency={urgency:.2f})")
                rec = adv.get("recommended_intervention") or adv.get("rationale", "")
                if rec:
                    print(f"     {rec}")

        # MC communication (only when dispatched)
        if ds.mc_communication:
            mc = ds.mc_communication
            msg_type = mc.get("message_type", "comms")
            content  = mc.get("content", "")
            print(f"\n  [MC -> Crew]  {msg_type.upper()}")
            if content:
                print(f"     {content}")

        print()

    # --- Mission summary --------------------------------------------------
    summary = result.get_summary()
    phys    = summary["physics"]
    hc      = summary["hermitclaw"]

    print("=" * 66)
    print("  MISSION COMPLETE — SUMMARY")
    print("=" * 66)
    print(f"  Crew         : {', '.join(m.name for m in crew.members)}")
    print(f"  Days run     : {summary['mission_length_days']}")
    print(f"  Final cohesion : {phys['final_cohesion']:.3f}")
    print(f"  Min cohesion   : {phys['min_cohesion']:.3f}  (day {phys['min_cohesion_day']})")
    print(f"  HermitClaw advisories: {hc['advisories_generated']}  "
          f"({hc['critical_advisories']} critical)")
    print("=" * 66)
    print()

    if llm is not None:
        print("Tip: All per-day JSON snapshots written to output/demo_twin_30d/")
        print("     Drop them into hermitclaw/ box dir for Weke readout.\n")


if __name__ == "__main__":
    run_demo()
