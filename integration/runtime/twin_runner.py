"""
Twin Runner — Day-by-Day Mission Twin Orchestrator

Runs the full per-agent behavioral twin pipeline day by day:

    Resource Layer → Perception Layer → Belief Engine → Internal State Drift
        → Action Selection → Physics Step

Each day produces a complete DayState snapshot serialized to JSON.

HermitClaw is NOT part of this simulation. It is an external JSON reader
(brendanhogan/hermitclaw) for checking on astronaut state day-to-day without
launching a full interface. Point it at the output directory to get readouts.

MC communications to crew can be injected externally via inject_mc_communication().

Usage:
    config = TwinRunnerConfig(
        mission_name="lunar_test",
        mission_length_days=180,
        crew_profile=my_crew,
        resource_config=ResourceConfig(),
    )
    runner = TwinRunner(config)
    result = runner.run()

DESIGN INVARIANTS:
    - Resource states are never written from this layer — only ResourceEngine writes them
    - Belief states are never written from this layer — only BeliefUpdateEngine writes them
    - All intermediate state is persisted in DayState and serialized to JSON
    - Batch MissionRunner is preserved and unmodified
"""

import json
import logging
import math
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- path setup ---
_ROOT = Path(__file__).parent.parent.parent
_PHASE4 = _ROOT / "phase4" / "06_Ruthless_Core_Model"
_SOCIAL_NET = _ROOT / "modules" / "05_Social_Network"
for p in [str(_ROOT), str(_PHASE4), str(_SOCIAL_NET)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Physics engine (frozen, read-only usage)
from ruthless_core import RuthlessCoreConfig

# Simulation layers
from resources.resource_model import ResourceConfig, ResourceEngine
from perception.perception_model import PerceptionEngine, SocialProximityMap, MCCommSignal
from beliefs.belief_engine import BeliefUpdateEngine, AstronautBeliefState
from internal_state.astronaut_state import AstronautInternalState, StateDriftEngine
from agents.per_agent_selector import PerAgentSelector
from agents.actions import AgentAction, ActionType
from crew.profile import CrewProfile, CrewMember
from crew.personality_to_config import PersonalityToConfigMapper
from mission_control.mc_types import (
    MCCommunication,
    PlannedIntervention,
    CrewReport,
)

# Social network (Module 05 — full graph dynamics)
from social_network import (
    SocialNetworkModule,
    NodeDefinition,
    EdgeDefinition,
    InteractionSignal,
)

# Task performance layer
from task_performance import TaskPerformanceEngine, DayTaskOutcomes

# Reproducibility and KPI layers
from run_manifest import write_run_manifest
from mission_kpis import compute_kpis, MissionKPIs
from mission_story import write_mission_story

# Parameter registry — single source of truth for all model constants
from params import (
    SCHEMA_VERSION,
    TQ_PHASE_START, TQ_PHASE_END, LATE_PHASE_START,
    TQ_MULTIPLIERS, LATE_MULTIPLIERS,
    CIRCADIAN_ACCUM_THRESHOLD, CIRCADIAN_ACCUM_RATE, CIRCADIAN_RECOVERY_RATE,
    SLEEP_DEBT_DECAY_FACTOR,
    EXEC_FATIGUE_WEIGHT, EXEC_STRESS_WEIGHT, EXEC_THRESHOLD, EXEC_SCALE,
    EXEC_WORKLOAD_AMP, EXEC_RECOVERY_SUPPRESS,
    EFFORT_BURNOUT_THRESHOLD, EFFORT_BURNOUT_SCALE,
    COMPLIANCE_STRAIN_THRESHOLD, COMPLIANCE_STRAIN_SCALE,
    COMPLIANCE_FRUSTRATION_THRESHOLD, COMPLIANCE_FRUSTRATION_SCALE,
    COMPLIANCE_FLOOR,
    AGENT_IMPAIRMENT_FATIGUE_WEIGHT, AGENT_IMPAIRMENT_STRESS_WEIGHT,
    BACKLOG_WORKLOAD_PER_SKIP, BACKLOG_MAX_LOAD, BACKLOG_NATURAL_DECAY,
    DYAD_CONFLICT_INCREMENT, DYAD_CONFLICT_DECAY, DYAD_TRUST_SUPPRESSOR,
)

# Suppress verbose per-step logging from Module 05 internals
logging.getLogger("social_network").setLevel(logging.ERROR)


# ---------------------------------------------------------------------------
# Micro-Events — daily frictions and small wins
# ---------------------------------------------------------------------------

@dataclass
class MicroEvent:
    """
    A low-level daily occurrence that perturbs one or more resource dimensions.

    Micro-events provide the day-to-day variance that prevents every day from
    being identical. They are the only source of intra-mission variability in
    the absence of externally injected MC communications.

    All resource deltas are added to the current baseline; managed resources
    (task_load, sleep_quality) carry forward until overridden again.

    DESIGN: Events do NOT directly modify beliefs or internal state.
    The causal path is always: event → resource override → perception → belief → state.
    """
    name: str
    task_load_delta: float = 0.0        # Added to baseline task_load for this day
    sleep_quality_delta: float = 0.0    # Added to sleep debt accumulator
    is_novel: bool = False              # Counts as a novelty event for physics
    is_success: bool = False            # Counts as a shared success event
    is_conflict: bool = False           # Minor interpersonal friction (task_load +0.05)

    def describe(self) -> str:
        return self.name


class MicroEventEngine:
    """
    Generates one optional micro-event per day using a seeded RNG.

    Deterministic: same seed always produces the same event sequence.
    Roughly 55% of days have some event; 45% are uneventful.

    Event catalogue:
        schedule_slip       — unexpected schedule overrun; workload spike
        minor_task_failure  — procedure fails; workload spike, morale dip via strain
        sleep_disruption    — noise/equipment; sleep debt accumulates
        minor_conflict      — interpersonal friction; slight workload + tension
        maintenance_surge   — unplanned maintenance; workload spike
        small_win           — task completes ahead of schedule; success signal
        comms_glitch        — brief comms interruption; no resource delta
        novel_task          — unexpected interesting task; novelty signal
    """

    #                          name                prob  task_δ  sleep_δ  novel  win   conflict
    _CATALOGUE = [
        ("schedule_slip",       0.07, +0.12,   0.00,  False, False, False),
        ("minor_task_failure",  0.06, +0.08,   0.00,  False, False, False),
        ("sleep_disruption",    0.06,  0.00,  -0.10,  False, False, False),
        ("minor_conflict",      0.05, +0.05,   0.00,  False, False, True),
        ("maintenance_surge",   0.07, +0.10,   0.00,  False, False, False),
        ("small_win",           0.10,  0.00,   0.00,  False, True,  False),
        ("comms_glitch",        0.05,  0.00,   0.00,  False, False, False),
        ("novel_task",          0.06,  0.00,   0.00,  True,  False, False),
    ]  # Cumulative probability ≈ 0.52; ~52% of days have an event

    def __init__(self, seed: int = 42, mission_length: int = 200):
        self._rng = random.Random(seed)
        self._mission_length = mission_length

    def roll(self, day: int) -> Optional[MicroEvent]:
        """Return a MicroEvent for this day, or None if no event occurs.

        Event probabilities shift by mission phase (Fix #2):
          Early (0–49%):    Baseline distribution
          TQ window (50–74%): More conflict and friction, fewer wins and novelty
          Late (75–100%):   More failures and slippage, novelty nearly exhausted

        This preserves endogenous causal emergence — agent state still drives
        deterioration — but reflects that real mission environments change over
        time (novelty decay, task repetition, goal-proximity stress).
        """
        phase = day / max(1, self._mission_length)

        # Phase probability multipliers (from params.TQ_MULTIPLIERS / LATE_MULTIPLIERS)
        if TQ_PHASE_START <= phase < TQ_PHASE_END:
            _mult = TQ_MULTIPLIERS
        elif phase >= LATE_PHASE_START:
            _mult = LATE_MULTIPLIERS
        else:
            _mult = {}

        r = self._rng.random()
        cumulative = 0.0
        for name, prob, task_delta, sleep_delta, is_novel, is_success, is_conflict in self._CATALOGUE:
            cumulative += prob * _mult.get(name, 1.0)
            if r < cumulative:
                return MicroEvent(
                    name=name,
                    task_load_delta=task_delta,
                    sleep_quality_delta=sleep_delta,
                    is_novel=is_novel,
                    is_success=is_success,
                    is_conflict=is_conflict,
                )
        return None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class TwinRunnerConfig:
    """
    Configuration for a day-by-day twin simulation run.

    Attributes:
        mission_name:         Human-readable mission identifier
        mission_length_days:  Total mission duration
        crew_profile:         Full crew profile (determines per-agent engines)
        resource_config:      Resource depletion rates and initial stock levels
        core_config:          Optional RuthlessCoreConfig; derived from crew if None
        output_dir:           Directory for JSON output files
        resupply_eta_days:    Default transit time for physical interventions
        verbose:              Print day-by-day progress
        random_seed:          Optional fixed seed for MicroEventEngine. If None,
                              seed is derived from mission_name hash (default).
                              Set to a fixed value across counterfactual runs so
                              all scenarios share identical daily micro-events.
    """
    mission_name: str
    mission_length_days: int
    crew_profile: CrewProfile
    resource_config: ResourceConfig = field(default_factory=ResourceConfig)
    core_config: Optional[RuthlessCoreConfig] = None
    output_dir: str = "output"
    resupply_eta_days: int = 21
    verbose: bool = False
    random_seed: Optional[int] = None


# ---------------------------------------------------------------------------
# DayState — complete per-day snapshot
# ---------------------------------------------------------------------------

@dataclass
class DayState:
    """
    Complete simulation state snapshot for one day.

    Serializable to JSON via to_dict(). Written to
    output/{mission_name}/day_{day:04d}.json by TwinRunner.

    physics_* fields are the effective inputs injected into the
    RuthlessCoreModel physics step for this day (after crew action modifiers).
    core_* fields are the physics outputs for this day.
    """
    day: int
    # Layer outputs
    resource_state_dict: dict         # ResourceState.to_dict()
    perceived_states: dict            # {agent_id: PerceivedState.to_dict()}
    belief_states: dict               # {agent_id: AstronautBeliefState.to_dict()}
    internal_states: dict             # {agent_id: AstronautInternalState.to_dict()}
    crew_actions: dict                # {agent_id: AgentAction.to_dict()}
    crew_report: dict                 # CrewReport.to_dict()
    # MC outputs
    mc_communication: Optional[dict]  # MCCommunication.to_dict() or None
    hermitclaw_advisory: Optional[dict]
    divergence_report: Optional[dict]
    # Physics inputs (aggregated from per-agent actions)
    physics_workload: float
    physics_recovery: float
    physics_novelty: float
    physics_success: float
    # Physics outputs (RuthlessCoreModel state after this day)
    core_strain: float
    core_cohesion: float
    core_monotony: float
    core_tq_pressure: float
    # Micro-event that occurred this day (None if uneventful)
    micro_event: Optional[str] = None
    # Social network graph metrics snapshot
    social_network: Optional[dict] = None
    # Task performance outcomes (per-task results + aggregate failure rates)
    task_outcomes: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "resource": self.resource_state_dict,
            "perceived": self.perceived_states,
            "beliefs": self.belief_states,
            "internal": self.internal_states,
            "actions": self.crew_actions,
            "crew_report": self.crew_report,
            "mc_communication": self.mc_communication,
            "hermitclaw_advisory": self.hermitclaw_advisory,
            "divergence_report": self.divergence_report,
            "micro_event": self.micro_event,
            "physics_inputs": {
                "workload": round(self.physics_workload, 4),
                "recovery": round(self.physics_recovery, 4),
                "novelty": round(self.physics_novelty, 4),
                "success": round(self.physics_success, 4),
            },
            "core_physics": {
                "strain": round(self.core_strain, 4),
                "cohesion": round(self.core_cohesion, 4),
                "monotony": round(self.core_monotony, 4),
                "tq_pressure": round(self.core_tq_pressure, 4),
            },
            "social_network": self.social_network,
            "task_outcomes":  self.task_outcomes,
        }


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class TwinMissionResult:
    """Final output of a TwinRunner.run() call."""
    config: TwinRunnerConfig
    day_states: List[DayState]
    hermitclaw_log: dict
    metadata: dict
    kpis: Optional[dict] = None   # MissionKPIs.to_dict() or None

    def get_summary(self) -> dict:
        cohesions = [d.core_cohesion for d in self.day_states]

        min_c = min(cohesions) if cohesions else 0.0
        min_c_day = cohesions.index(min_c) if cohesions else 0

        advisories = self.hermitclaw_log.get("advisory_log", [])
        n_critical = sum(1 for a in advisories if a.get("urgency", 0) >= 0.65)

        return {
            "schema_version": SCHEMA_VERSION,
            "mission_name": self.config.mission_name,
            "mission_length_days": self.config.mission_length_days,
            "crew_size": len(self.config.crew_profile.members),
            "physics": {
                "min_cohesion": round(min_c, 4),
                "min_cohesion_day": min_c_day,
                "final_cohesion": round(cohesions[-1], 4) if cohesions else 0.0,
            },
            "hermitclaw": {
                "advisories_generated": len(advisories),
                "critical_advisories": n_critical,
            },
            "kpis": self.kpis,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Twin Runner
# ---------------------------------------------------------------------------

class TwinRunner:
    """
    Day-by-day orchestrator for the 3QP behavioral mission twin.

    Runs the full per-agent pipeline each day and writes JSON output files.
    All sub-engines are initialized from the provided TwinRunnerConfig.

    Preserves the existing batch MissionRunner/run_simulation.py interface.
    Invoked via: python run_simulation.py --mode twin ...
    """

    def __init__(
        self,
        config: TwinRunnerConfig,
    ) -> None:
        self._cfg = config
        self._T = config.mission_length_days
        agent_ids = [m.name for m in config.crew_profile.members]
        self._agent_ids = agent_ids
        self._n = len(agent_ids)

        # Derive RuthlessCoreConfig from crew personality if not provided
        if config.core_config is not None:
            self._core_config = config.core_config
        else:
            mapper = PersonalityToConfigMapper()
            self._core_config = mapper.map_to_ruthless_config(
                config.crew_profile,
                mission_length_days=config.mission_length_days,
            )

        # Resource engine
        self._resource_engine = ResourceEngine(config.resource_config, agent_ids)

        # Per-agent perception, belief, and drift engines
        self._perception_engines: Dict[str, PerceptionEngine] = {}
        self._belief_engines: Dict[str, BeliefUpdateEngine] = {}
        self._drift_engines: Dict[str, StateDriftEngine] = {}

        for member in config.crew_profile.members:
            aid = member.name
            p = member.personality
            self._perception_engines[aid] = PerceptionEngine(aid, p)
            self._belief_engines[aid] = BeliefUpdateEngine(aid, p)
            self._drift_engines[aid] = StateDriftEngine(aid, p)

        # Per-agent selector
        self._selector = PerAgentSelector(
            config.crew_profile,
            mission_length=config.mission_length_days,
        )

        # Per-agent running state (initialized below)
        self._beliefs: Dict[str, AstronautBeliefState] = {}
        self._internal: Dict[str, AstronautInternalState] = {}
        self._social: Dict[str, SocialProximityMap] = {}
        self._prev_mc_reliability: Dict[str, float] = {}

        # Initialize per-agent states
        self._init_agent_states()

        # Running physics state
        self._M = self._core_config.initial_monotony
        self._S = self._core_config.initial_strain
        self._C = self._core_config.initial_cohesion
        self._Q = self._compute_tq_pressure(self._M, self._S, self._C)

        # Pending MC communications and physical interventions
        self._pending_mc_comm: Optional[MCCommunication] = None
        self._planned_interventions: List[PlannedIntervention] = []

        # Micro-events engine (deterministic RNG)
        # Use explicit random_seed if provided; otherwise derive from mission name hash.
        # Counterfactual comparisons should pass a shared seed so all scenarios
        # experience identical daily events — isolating the intervention effect.
        _event_seed = (
            config.random_seed
            if config.random_seed is not None
            else hash(config.mission_name) % (2**31)
        )
        self._micro_events = MicroEventEngine(seed=_event_seed, mission_length=config.mission_length_days)

        # Store resolved event seed for run manifest
        self._event_seed = _event_seed

        # Task performance engine — same seed base, offset internally to avoid RNG correlation
        self._task_engine = TaskPerformanceEngine(seed=_event_seed)

        # Social network — full graph dynamics (Module 05)
        _nodes = [NodeDefinition(node_id=aid) for aid in agent_ids]
        _edges = [
            EdgeDefinition(source_node_id=a, target_node_id=b, initial_weight=0.70)
            for i, a in enumerate(agent_ids)
            for b in agent_ids[i + 1:]
        ]
        self._social_net = SocialNetworkModule(nodes=_nodes, edges=_edges)

        # Scheduled MC comms: {day: [MCCommunication, ...]}
        self._comm_schedule: Dict[int, List[MCCommunication]] = {}

        # Tracked managed-resource baselines and running state
        self._sleep_quality_baseline: float = config.resource_config.initial_sleep_quality
        self._sleep_debt: float = 0.0           # Accumulated sleep disruption; decays ~2 days
        self._circadian_drift: float = 0.0      # Persistent baseline erosion from chronic disruption
        self._consumption_modifier: float = 1.0  # Updated from prev-day actions; starts nominal

        # Backlog dynamics (#5): skipped tasks carry forward as workload pressure
        self._maintenance_backlog: float = 0.0

        # Task dependency graph: last day's outcomes feed into next day's fail probs
        self._last_task_outcomes = None  # type: Optional[object]  # DayTaskOutcomes

        # Reputation memory / dyadic conflict (#7): {min_id:max_id → conflict score}
        self._dyad_conflicts: Dict[str, float] = {}

        # Output
        self._day_states: List[DayState] = []
        self._output_path = Path(config.output_dir) / config.mission_name
        self._output_path.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------
    # Run
    # -------------------------------------------------------------------

    def run(self) -> TwinMissionResult:
        """Execute the full mission day by day and return results."""
        start_time = datetime.now()

        if self._cfg.verbose:
            print(f"[TwinRunner] Starting twin simulation: {self._cfg.mission_name}")
            print(f"[TwinRunner] Crew: {[m.name for m in self._cfg.crew_profile.members]}")
            print(f"[TwinRunner] Days: {self._T}")

        # Write reproducibility manifest (#8) before any simulation state changes
        write_run_manifest(
            config=self._cfg,
            event_seed=self._event_seed,
            output_path=self._output_path,
        )

        for day in range(1, self._T + 1):
            day_state = self._run_day(day)
            self._day_states.append(day_state)

            # Write daily JSON
            day_file = self._output_path / f"day_{day:04d}.json"
            with open(day_file, "w", encoding="utf-8") as f:
                json.dump(day_state.to_dict(), f, indent=2)

            if self._cfg.verbose and day % 10 == 0:
                print(
                    f"[TwinRunner] Day {day:3d}/{self._T} | "
                    f"C={self._C:.3f} S={self._S:.3f} M={self._M:.3f}"
                )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        metadata = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "output_path": str(self._output_path),
        }

        # Compute mission outcome KPIs (#6) from accumulated day states
        kpis_obj = compute_kpis(self._day_states)
        kpis_dict = kpis_obj.to_dict() if kpis_obj is not None else None

        # Write KPIs to kpis.json for standalone access
        if kpis_dict is not None:
            kpis_file = self._output_path / "kpis.json"
            with open(kpis_file, "w", encoding="utf-8") as f:
                json.dump({"schema_version": SCHEMA_VERSION, **kpis_dict}, f, indent=2)

        # Write narrative mission story from causal traces
        write_mission_story(self._day_states, self._output_path)

        # Write summary
        result = TwinMissionResult(
            config=self._cfg,
            day_states=self._day_states,
            hermitclaw_log={},
            metadata=metadata,
            kpis=kpis_dict,
        )
        summary_file = self._output_path / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(result.get_summary(), f, indent=2)

        if self._cfg.verbose:
            print(f"[TwinRunner] Complete in {duration:.1f}s.")
            print(f"[TwinRunner] Output: {self._output_path}")

        return result

    def get_state_history(self) -> List[DayState]:
        """Return all DayState snapshots accumulated so far."""
        return list(self._day_states)

    def inject_mc_communication(self, comm: MCCommunication) -> None:
        """
        Inject an MC communication for delivery on the next simulation day.

        Use this for real-time external injection during a live run. For
        pre-scheduled comms, prefer schedule_mc_communication().
        """
        self._pending_mc_comm = comm

    def schedule_mc_communication(self, day: int, comm: MCCommunication) -> None:
        """
        Schedule an MC communication to be delivered automatically on a specific day.

        Multiple comms can be scheduled for the same day; the first in the list
        is delivered. Call before runner.run() to pre-load an intervention schedule.

        Args:
            day:  Simulation day (1-indexed) to deliver the comm.
            comm: MCCommunication to inject on that day.
        """
        if day not in self._comm_schedule:
            self._comm_schedule[day] = []
        self._comm_schedule[day].append(comm)

    # -------------------------------------------------------------------
    # Day pipeline (13 steps)
    # -------------------------------------------------------------------

    def _run_day(self, day: int) -> DayState:
        """
        Execute one day of the twin pipeline.

        Steps:
          1.  ResourceEngine.step()
          2.  PerceptionEngine.compute_perception() per agent
          3.  BeliefUpdateEngine.update() per agent + MC comm belief deltas
          4.  StateDriftEngine.step() per agent
          5.  Update social proximity maps
          6.  PerAgentSelector.select_action() per agent
          7.  PerAgentSelector.aggregate_crew_inputs()
          8.  Physics step (inline RuthlessCoreModel equations)
          9.  Build CrewReport
          10. Clear pending_mc_comm (only set by external injection; never by any sim component)
        """
        # --- Step 0: Roll today's micro-event ---
        # Decay all dyad conflict scores daily before processing today's events
        for dyad_key in list(self._dyad_conflicts.keys()):
            self._dyad_conflicts[dyad_key] *= DYAD_CONFLICT_DECAY

        event = self._micro_events.roll(day)

        # Check comm schedule — inject any pre-scheduled comm for today
        if day in self._comm_schedule and self._comm_schedule[day]:
            self._pending_mc_comm = self._comm_schedule[day][0]

        # Dyad conflict increment: spread DYAD_CONFLICT_INCREMENT across all pairs
        if event and event.is_conflict and len(self._agent_ids) > 1:
            n_pairs = len(self._agent_ids) * (len(self._agent_ids) - 1) // 2
            per_pair = DYAD_CONFLICT_INCREMENT / max(1, n_pairs)
            for i, a in enumerate(self._agent_ids):
                for b in self._agent_ids[i + 1:]:
                    dyad_key = f"{min(a, b)}:{max(a, b)}"
                    self._dyad_conflicts[dyad_key] = (
                        self._dyad_conflicts.get(dyad_key, 0.0) + per_pair
                    )

        # --- Step 1: Resource step ---
        # Sleep debt: accumulate disruptions, decay with ~1.5-day half-life
        if event and event.sleep_quality_delta < 0:
            self._sleep_debt = _clamp(self._sleep_debt + abs(event.sleep_quality_delta))
        self._sleep_debt *= SLEEP_DEBT_DECAY_FACTOR

        # Circadian drift: persistent baseline erosion from repeated disruptions.
        # Accumulates only when sleep debt exceeds threshold — causal, not time-indexed.
        # Recovers slowly during undisturbed stretches.
        if self._sleep_debt > CIRCADIAN_ACCUM_THRESHOLD:
            self._circadian_drift = _clamp(self._circadian_drift + CIRCADIAN_ACCUM_RATE * self._sleep_debt)
        else:
            self._circadian_drift = max(0.0, self._circadian_drift - CIRCADIAN_RECOVERY_RATE)

        # Task load: nominal baseline + today's micro-event spike
        task_today = _clamp(
            self._cfg.resource_config.initial_task_load
            + (event.task_load_delta if event else 0.0)
        )
        # Sleep quality: baseline minus acute debt minus accumulated circadian drift
        sleep_today = _clamp(self._sleep_quality_baseline - self._sleep_debt - self._circadian_drift)

        # Resource engine uses PREVIOUS day's consumption modifier (actions known too late)
        resource = self._resource_engine.step(
            day,
            consumption_modifier=self._consumption_modifier,
            sleep_quality_override=sleep_today,
            task_load_override=task_today,
        )

        # --- Step 2: Perception per agent ---
        # Consume pending MC comm from yesterday (crew receives it today)
        mc_signal_today = _comm_to_signal(self._pending_mc_comm)
        perceived_states = {}
        for aid in self._agent_ids:
            perceived_states[aid] = self._perception_engines[aid].compute_perception(
                resource_state=resource,
                social_proximity=self._social[aid],
                mc_signal=mc_signal_today,
                prior_mc_reliability=self._prev_mc_reliability.get(aid, 0.7),
                day=day,
            )
            self._prev_mc_reliability[aid] = perceived_states[aid].perceived_comms_reliability

        # --- Steps 3+4: Belief update + MC comm deltas + state drift ---
        resupply_arrived = self._check_resupply_arrived(day)
        overdue_days = self._get_overdue_days(day)

        new_beliefs: Dict[str, AstronautBeliefState] = {}
        new_internal: Dict[str, AstronautInternalState] = {}

        for aid in self._agent_ids:
            # Belief update from perception
            new_belief = self._belief_engines[aid].update(
                perceived=perceived_states[aid],
                prior=self._beliefs[aid],
                resupply_arrived_today=resupply_arrived,
                resupply_overdue_days=overdue_days,
            )

            # Apply MC comm belief deltas with compliance scaling (Fix #4)
            if self._pending_mc_comm is not None:
                new_belief = _apply_comm_deltas(new_belief, self._pending_mc_comm, self._internal[aid])

            new_beliefs[aid] = new_belief

            # State drift
            new_internal[aid] = self._drift_engines[aid].step(
                prior=self._internal[aid],
                belief=new_belief,
                perceived=perceived_states[aid],
                social_proximity=self._social[aid],
                day=day,
            )

        self._beliefs = new_beliefs
        self._internal = new_internal

        # Dyad conflict cohesion suppression (#7): high pairwise conflict history
        # suppresses each agent's belief_crew_cohesion by up to DYAD_TRUST_SUPPRESSOR.
        if self._dyad_conflicts:
            for aid in self._agent_ids:
                max_conflict = max(
                    (self._dyad_conflicts.get(f"{min(aid, o)}:{max(aid, o)}", 0.0)
                     for o in self._agent_ids if o != aid),
                    default=0.0,
                )
                if max_conflict > 0.0:
                    suppression = min(DYAD_TRUST_SUPPRESSOR, max_conflict * DYAD_TRUST_SUPPRESSOR)
                    b = self._beliefs[aid]
                    self._beliefs[aid] = AstronautBeliefState(
                        agent_id=b.agent_id,
                        day=b.day,
                        belief_coffee_scarcity=b.belief_coffee_scarcity,
                        belief_distribution_fairness=b.belief_distribution_fairness,
                        belief_resupply_reliability=b.belief_resupply_reliability,
                        belief_mission_control_support=b.belief_mission_control_support,
                        belief_crew_cohesion=_clamp(b.belief_crew_cohesion - suppression),
                        belief_mission_viability=b.belief_mission_viability,
                    )

        # --- Step 5: Action selection ---
        actions: Dict[str, AgentAction] = {}
        for aid in self._agent_ids:
            actions[aid] = self._selector.select_action(
                agent_id=aid,
                internal_state=self._internal[aid],
                belief_state=self._beliefs[aid],
                crew_states=self._internal,
                day=day,
            )

        # --- Step 6: Update social network (full graph dynamics) ---
        # Actions generate interaction signals → graph updates → tomorrow's perception
        self._update_social_proximity(event, actions, day)
        _sn_summary = self._social_net.get_summary()

        # --- Step 7: Aggregate physics inputs from resource state + events ---
        # Workload drives from live task_load (not a sinusoidal schedule)
        base_workload = resource.task_load

        # Recovery from sleep quality + food variety + crew morale composite.
        # Raw sum over normalized [0,1] inputs averages ~0.80 under nominal conditions.
        # Scale by 0.5 to align with the batch-mode recovery range (~0.40 nominal)
        # that the RuthlessCoreConfig physics coefficients were calibrated against.
        # Degraded conditions (poor sleep, low food, low morale) → lower recovery → more
        # strain accumulation, which is physically correct.
        mean_morale = sum(self._internal[a].morale for a in self._agent_ids) / max(1, self._n)
        base_recovery = _clamp(
            (
                0.35 * resource.sleep_quality
                + 0.25 * resource.food_variety
                + 0.25 * mean_morale
                + 0.15  # Baseline irreducible biological recovery
            ) * 0.45  # Rescale to batch-model physics range
        )

        wmod, rmod, novelty_boost, success_boost = self._selector.aggregate_crew_inputs(
            actions, self._internal
        )
        effective_workload = _clamp(base_workload * wmod)
        effective_recovery = _clamp(base_recovery * rmod)

        # Executive function degradation: chronic fatigue + stress reduce
        # coordination quality. Manifests as increased effective workload and reduced
        # recovery efficiency. Effect activates above EXEC_THRESHOLD combined impairment.
        mean_fatigue = sum(self._internal[a].fatigue for a in self._agent_ids) / max(1, self._n)
        mean_stress  = sum(self._internal[a].stress  for a in self._agent_ids) / max(1, self._n)
        exec_impairment = _clamp((mean_fatigue * EXEC_FATIGUE_WEIGHT + mean_stress * EXEC_STRESS_WEIGHT - EXEC_THRESHOLD) * EXEC_SCALE)
        effective_workload = _clamp(effective_workload * (1.0 + exec_impairment * EXEC_WORKLOAD_AMP))
        effective_recovery = _clamp(effective_recovery * (1.0 - exec_impairment * EXEC_RECOVERY_SUPPRESS))

        # Backlog pressure (#5): accumulated skipped tasks feed forward as workload.
        # Uses previous day's backlog so causal order is preserved (skip → next day pressure).
        backlog_pressure = min(BACKLOG_MAX_LOAD, self._maintenance_backlog * BACKLOG_WORKLOAD_PER_SKIP)
        effective_workload = _clamp(effective_workload + backlog_pressure)

        # MC workload relief: rest_authorization or schedule_relief reduces effective workload.
        # Capped at 30% of effective_workload to prevent unphysical zeroing.
        if self._pending_mc_comm is not None and self._pending_mc_comm.workload_relief_factor > 0.0:
            relief = min(0.30, self._pending_mc_comm.workload_relief_factor)
            effective_workload = _clamp(effective_workload * (1.0 - relief))

        # Structural competence degradation: high fatigue + boredom reduces
        # quality of ENGAGE and SUPPORT contributions.
        mean_burnout = sum(
            self._internal[a].fatigue * 0.5 + self._internal[a].boredom * 0.5
            for a in self._agent_ids
        ) / max(1, self._n)
        effort_quality = _clamp(1.0 - max(0.0, (mean_burnout - EFFORT_BURNOUT_THRESHOLD)) * EFFORT_BURNOUT_SCALE)
        novelty_boost *= effort_quality
        success_boost *= effort_quality

        # Novelty: comms received today OR a novel micro-event — no calendar schedule
        base_novelty = 1.0 if (
            mc_signal_today.received or (event is not None and event.is_novel)
        ) else 0.0
        effective_novelty = _clamp(base_novelty + novelty_boost)

        # Success: small_win micro-event — no calendar schedule
        base_success = 1.0 if (event is not None and event.is_success) else 0.0
        effective_success = _clamp(base_success + success_boost)

        # Update consumption modifier for NEXT day (today's actions determine tomorrow's use)
        self._consumption_modifier = self._compute_consumption_modifier(actions, resource)

        # --- Step 8: Physics step ---
        M_new, S_new, Q_new, C_new = self._physics_step(
            day=day,
            workload=effective_workload,
            recovery=effective_recovery,
            novelty=effective_novelty,
            success=effective_success,
        )
        self._M = M_new
        self._S = S_new
        self._Q = Q_new
        self._C = C_new

        # --- Step 9: Crew report ---
        crew_report = self._build_crew_report(day, actions)

        # --- Step 10: Task performance evaluation ---
        # Uses physics-layer accumulation variables — read-only w.r.t. agent state.
        # Per-agent impairment computed from individual fatigue+stress for weakest-link
        # coordination failure model (#4).
        per_agent_impairment = {
            aid: _clamp(
                self._internal[aid].fatigue * AGENT_IMPAIRMENT_FATIGUE_WEIGHT
                + self._internal[aid].stress  * AGENT_IMPAIRMENT_STRESS_WEIGHT
            )
            for aid in self._agent_ids
        }
        task_outcomes = self._task_engine.evaluate(
            day=day,
            core_strain=self._S,
            core_monotony=self._M,
            sleep_quality=resource.sleep_quality,
            circadian_drift=self._circadian_drift,
            per_agent_impairment=per_agent_impairment,
            prior_day_outcomes=self._last_task_outcomes,
        )

        # Backlog update (#5): skipped tasks carry forward; decay resolves completed work
        skip_count = sum(1 for t in task_outcomes.task_results if t.outcome == "skipped")
        self._maintenance_backlog = (self._maintenance_backlog + skip_count) * BACKLOG_NATURAL_DECAY

        # Store for task dependency graph (passed to next day's evaluate)
        self._last_task_outcomes = task_outcomes

        # --- Step 11: pending_mc_comm for next day ---
        # Only set by external injection (inject_mc_communication()), never by HermitClaw.
        # self._pending_mc_comm carries forward whatever was externally injected (or None).
        # Clear after consumption so a single injected comm doesn't persist multiple days.
        self._pending_mc_comm = None

        # --- Step 13: Package DayState ---
        return DayState(
            day=day,
            resource_state_dict=resource.to_dict(),
            perceived_states={
                aid: perceived_states[aid].to_dict() for aid in self._agent_ids
            },
            belief_states={
                aid: self._beliefs[aid].to_dict() for aid in self._agent_ids
            },
            internal_states={
                aid: self._internal[aid].to_dict() for aid in self._agent_ids
            },
            crew_actions={
                aid: actions[aid].to_dict() for aid in self._agent_ids
            },
            crew_report=crew_report.to_dict(),
            mc_communication=None,  # Only set via external inject_mc_communication()
            hermitclaw_advisory=None,
            divergence_report=None,
            micro_event=event.name if event else None,
            social_network=_sn_summary,
            task_outcomes=task_outcomes.to_dict(),
            physics_workload=round(effective_workload, 4),
            physics_recovery=round(effective_recovery, 4),
            physics_novelty=round(effective_novelty, 4),
            physics_success=round(effective_success, 4),
            core_strain=round(self._S, 4),
            core_cohesion=round(self._C, 4),
            core_monotony=round(self._M, 4),
            core_tq_pressure=round(self._Q, 4),
        )

    # -------------------------------------------------------------------
    # Physics
    # -------------------------------------------------------------------

    def _physics_step(
        self,
        day: int,
        workload: float,
        recovery: float,
        novelty: float,
        success: float,
    ) -> Tuple[float, float, float, float]:
        """
        Apply one RuthlessCoreModel step using the explicit physics equations.

        Mirrors the updated equations in RuthlessCoreModel.run().
        Q is now endogenous — derived from M, S, C — not from day/mission_length.
        Cohesion rebound fires when Q is actively declining (not when r > q_center).

        Returns (M_new, S_new, Q_new, C_new).
        """
        cfg = self._core_config
        M, S, Q, C = self._M, self._S, self._Q, self._C

        # Monotony
        M_new = max(0.0, M + cfg.m_base - cfg.m_novelty * novelty)

        # Strain
        S_new = (
            S
            + cfg.s_workload * workload
            + cfg.s_mono * M
            - cfg.s_recovery * recovery
            - cfg.s_leak * S
        )
        S_new = max(0.0, S_new)

        # Endogenous TQ pressure from updated M and S, prior C
        Q_new = self._compute_tq_pressure(M_new, S_new, C)

        # Cohesion
        cohesion_decrease = cfg.c_strain * S + cfg.c_q * Q
        cohesion_increase = cfg.c_shared_success * success
        # Rebound fires when Q is actively falling (pressure easing, not by calendar)
        cohesion_rebound = cfg.c_rebound * (1.0 - C) if Q_new < Q else 0.0
        C_new = C - cohesion_decrease + cohesion_increase + cohesion_rebound
        C_new = max(0.05, min(1.2, C_new))

        return M_new, S_new, Q_new, C_new

    def _compute_tq_pressure(self, M: float, S: float, C: float) -> float:
        """
        Endogenous TQ pressure from current state variables.

        Q emerges when monotony accumulates, strain is elevated, and cohesion erodes.
        Mirrors RuthlessCoreModel.compute_tq_pressure() exactly.
        """
        cfg = self._core_config
        m_norm = min(M / 2.0, 1.0)
        c_deficit = max(0.0, 1.0 - C)
        raw = cfg.c_q_m * m_norm + cfg.c_q_s * S + cfg.c_q_c * c_deficit
        return max(0.0, min(1.0, raw))

    def _compute_consumption_modifier(
        self, actions: Dict, resource
    ) -> float:
        """
        Derive next-day consumption modifier from today's crew actions and task load.

        Activity scores by action type:
            withdraw  → 0.60 (less active, fewer consumables used)
            maintain  → 1.00 (nominal)
            support   → 1.20
            escalate  → 1.10
            engage    → 1.35 (high activity)

        Task load scales overall consumption: busy days use more resources.
        Result clamped to [0.3, 2.0].
        """
        _activity = {
            "withdraw": 0.60,
            "maintain": 1.00,
            "support": 1.20,
            "escalate": 1.10,
            "engage": 1.35,
        }
        mean_activity = sum(
            _activity.get(a.action_type.value, 1.0) for a in actions.values()
        ) / max(1, len(actions))
        # High task load = more resource use overall
        task_scale = 0.6 + resource.task_load * 0.8  # [0.60, 1.40] for task_load [0, 1]
        return _clamp(mean_activity * task_scale, 0.3, 2.0)

    # -------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------

    def _init_agent_states(self) -> None:
        """Initialize per-agent beliefs, internal states, and social proximity."""

        for member in self._cfg.crew_profile.members:
            aid = member.name
            p = member.personality

            # Initial beliefs (nominal mission start)
            initial_scarcity = _clamp(
                (1.0 - self._cfg.resource_config.initial_coffee) * 0.5
            )
            self._beliefs[aid] = AstronautBeliefState(
                agent_id=aid,
                day=0,
                belief_coffee_scarcity=initial_scarcity,
                belief_distribution_fairness=0.80,
                belief_resupply_reliability=0.75,
                belief_mission_control_support=0.70,
                belief_crew_cohesion=0.75,
                belief_mission_viability=0.80,
            )

            # Initial internal state (personality-modulated)
            init_stress = _clamp(0.10 + (p.neuroticism - 0.5) * 0.10)
            init_morale = _clamp(0.80 - (p.neuroticism - 0.5) * 0.10)
            init_boredom = _clamp(0.10 + (p.extraversion - 0.5) * 0.10)
            init_fatigue = 0.15
            init_trust = 0.70
            init_frustration = 0.05
            init_outlook = _clamp(0.80 - (p.neuroticism - 0.5) * 0.10)

            engine = self._drift_engines[aid]
            init_coop = engine.compute_cooperation_threshold(
                AstronautInternalState(
                    agent_id=aid, day=0,
                    stress=init_stress, morale=init_morale,
                    fatigue=init_fatigue, boredom=init_boredom,
                    trust_in_crew=init_trust,
                    frustration_scarcity=init_frustration,
                    future_outlook=init_outlook,
                    cooperation_threshold=0.0,
                )
            )
            self._internal[aid] = AstronautInternalState(
                agent_id=aid, day=0,
                stress=init_stress, morale=init_morale,
                fatigue=init_fatigue, boredom=init_boredom,
                trust_in_crew=init_trust,
                frustration_scarcity=init_frustration,
                future_outlook=init_outlook,
                cooperation_threshold=init_coop,
            )

            # Initial social proximity — weights at init_trust (not fractional share)
            # mean_trust() returns the arithmetic mean of these weights, so they must
            # be on the same 0–1 scale as trust_in_crew, not as allocation fractions.
            self._social[aid] = SocialProximityMap(
                agent_id=aid,
                neighbor_weights={
                    other: init_trust
                    for other in self._agent_ids if other != aid
                },
            )

            # Initial perceived comms reliability
            self._prev_mc_reliability[aid] = 0.7

    # -------------------------------------------------------------------
    # Social proximity update
    # -------------------------------------------------------------------

    def _update_social_proximity(
        self,
        event: Optional[MicroEvent],
        actions: Dict[str, AgentAction],
        day: int,
    ) -> None:
        """
        Update the social network using per-agent actions as interaction signals.

        Each agent broadcasts a signal to all crewmates with intensity determined
        by their action type. Conflict/success micro-events shift all signals.
        After the graph update, SocialProximityMap weights are rebuilt from actual
        graph edge weights so tomorrow's perception sees full graph dynamics.

        Action → signal intensity mapping:
            SUPPORT   → 0.80  (cooperative, high-contact)
            ENGAGE    → 0.60  (active, medium-positive)
            MAINTAIN  → 0.30  (neutral, low contact)
            ESCALATE  → 0.15  (conflict-adjacent)
            WITHDRAW  → 0.10  (avoidance, minimal contact)

        Micro-event modifiers (crew-wide):
            conflict  → -0.15
            success   → +0.10
            novel     → +0.05
        """
        _action_intensity = {
            "support":  0.80,
            "engage":   0.60,
            "maintain": 0.30,
            "escalate": 0.15,
            "withdraw": 0.10,
        }
        _event_modifier = 0.0
        if event is not None:
            if event.is_conflict:
                _event_modifier = -0.15
            elif event.is_success:
                _event_modifier = +0.10
            elif event.is_novel:
                _event_modifier = +0.05

        signals = []
        for source, action in actions.items():
            base_intensity = _action_intensity.get(action.action_type.value, 0.30)
            intensity = _clamp(base_intensity + _event_modifier)
            for target in self._agent_ids:
                if target == source:
                    continue
                signals.append(InteractionSignal(
                    source_node_id=source,
                    target_node_id=target,
                    intensity=intensity,
                    duration=1,
                    timestamp=day,
                ))

        self._social_net.update(signals, step_number=day)

        # Rebuild SocialProximityMap from actual graph edge weights
        for aid in self._agent_ids:
            updated_weights = {}
            for other in self._agent_ids:
                if other == aid:
                    continue
                w = self._social_net.query_edge_weight(aid, other)
                updated_weights[other] = w if w is not None else 0.10
            self._social[aid] = SocialProximityMap(
                agent_id=aid,
                neighbor_weights=updated_weights,
            )

    # -------------------------------------------------------------------
    # CrewReport builder
    # -------------------------------------------------------------------

    def _build_crew_report(
        self,
        day: int,
        actions: Dict[str, AgentAction],
    ) -> CrewReport:
        """Build CrewReport from per-agent actions and surface-visible state."""
        n = len(self._agent_ids)
        if n == 0:
            return CrewReport(
                day=day,
                mean_morale_reported=0.5,
                dominant_action="maintain",
                action_distribution={},
                withdrawal_count=0,
                escalation_count=0,
                cooperation_rate=0.0,
            )

        # Morale as crew would self-report: future_outlook proxy
        mean_morale = sum(
            self._internal[aid].future_outlook for aid in self._agent_ids
        ) / n

        # Count action types
        dist: Dict[str, int] = {}
        for action in actions.values():
            key = action.action_type.value
            dist[key] = dist.get(key, 0) + 1

        dominant = max(dist, key=dist.get) if dist else "maintain"
        withdrawal_count = dist.get(ActionType.WITHDRAW.value, 0)
        escalation_count = dist.get(ActionType.ESCALATE.value, 0)
        cooperative = sum(
            1 for a in actions.values()
            if a.action_type in (ActionType.SUPPORT, ActionType.ENGAGE)
        )
        cooperation_rate = cooperative / n

        return CrewReport(
            day=day,
            mean_morale_reported=round(mean_morale, 4),
            dominant_action=dominant,
            action_distribution=dist,
            withdrawal_count=withdrawal_count,
            escalation_count=escalation_count,
            cooperation_rate=round(cooperation_rate, 4),
        )

    # -------------------------------------------------------------------
    # Resupply tracking
    # -------------------------------------------------------------------

    def _check_resupply_arrived(self, day: int) -> bool:
        """Return True if any scheduled resupply arrived today."""
        for resupply in self._resource_engine.get_pending_resupplies():
            # After step(), applied resupplies are marked True
            pass
        # Check resource_engine history for resupply applied on this day
        # Simpler: check planned interventions
        for intervention in self._planned_interventions:
            if intervention.arrival_day == day and not intervention.applied:
                intervention.applied = True
                return True
        return False

    def _get_overdue_days(self, day: int) -> int:
        """
        Return how many days past ETA the most recently promised resupply is.
        Returns 0 if no resupply was promised or if it arrived on time.
        """
        overdue = 0
        for intervention in self._planned_interventions:
            if not intervention.applied and day > intervention.arrival_day:
                days_late = day - intervention.arrival_day
                overdue = max(overdue, days_late)
        return overdue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


def _comm_to_signal(comm: Optional[MCCommunication]) -> MCCommSignal:
    """Convert an MCCommunication (or None) to an MCCommSignal for PerceptionEngine."""
    if comm is None:
        return MCCommSignal(received=False)
    return MCCommSignal(
        received=True,
        message_type=comm.message_type,
        resupply_promised=(comm.belief_resupply_reliability_delta > 0),
        eta_days=0,
    )


def _apply_comm_deltas(
    belief: AstronautBeliefState,
    comm: MCCommunication,
    internal: Optional[AstronautInternalState] = None,
) -> AstronautBeliefState:
    """
    Apply immediate belief deltas from an MCCommunication.

    Returns a new AstronautBeliefState with updated fields.
    Called the day AFTER the comm was dispatched (crew receives it today).

    Compliance scaling (Fix #4): high-strain, high-frustration agents are less
    receptive. Psychological reactance and message fatigue reduce uptake.
    Deltas are scaled to a floor of 0.35× — interventions never become inert.
    """
    # Compliance: high stress + frustration reduce intervention uptake
    compliance = 1.0
    if internal is not None:
        strain_reactance      = max(0.0, (internal.stress - COMPLIANCE_STRAIN_THRESHOLD) * COMPLIANCE_STRAIN_SCALE)
        frustration_reactance = max(0.0, (internal.frustration_scarcity - COMPLIANCE_FRUSTRATION_THRESHOLD) * COMPLIANCE_FRUSTRATION_SCALE)
        compliance = max(COMPLIANCE_FLOOR, 1.0 - strain_reactance - frustration_reactance)

    new_mc_support = _clamp(
        belief.belief_mission_control_support + comm.belief_mc_support_delta * compliance
    )
    new_reliability = _clamp(
        belief.belief_resupply_reliability + comm.belief_resupply_reliability_delta * compliance
    )
    new_cohesion = _clamp(
        belief.belief_crew_cohesion + comm.belief_crew_cohesion_delta * compliance
    )
    return AstronautBeliefState(
        agent_id=belief.agent_id,
        day=belief.day,
        belief_coffee_scarcity=belief.belief_coffee_scarcity,
        belief_distribution_fairness=belief.belief_distribution_fairness,
        belief_resupply_reliability=new_reliability,
        belief_mission_control_support=new_mc_support,
        belief_crew_cohesion=new_cohesion,
        belief_mission_viability=belief.belief_mission_viability,
    )
