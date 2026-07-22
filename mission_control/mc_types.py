"""
MC Types — Shared types for the Mission Control layer.

All types in this module are plain dataclasses — no logic, no imports
from other simulation layers. They are passed between HermitClaw, the
TwinRunner, and the output serializer.

Types:
    MCCommunication    — Message from Mission Control to the crew
    PlannedIntervention — Scheduled physical intervention (resupply, etc.)
    CrewReport          — What MC can observe from crew behavior
    DivergenceReport    — HermitClaw's read on crew-belief vs objective state
    HermitClawAdvisory  — HermitClaw's recommended action for MC
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Outbound communications (MC → crew)
# ---------------------------------------------------------------------------

@dataclass
class MCCommunication:
    """
    A directed message from Mission Control to the crew.

    Belief impacts are applied immediately on receipt via BeliefUpdateEngine.
    Content text is template-derived for Weke/HermitClaw natural language readout.

    message_type values:
        "reassurance"           - Psychological support; MC acknowledges difficulty
        "resupply_announcement" - Promise of incoming resupply + ETA
        "acknowledgment"        - MC validates crew concerns
        "direction"             - Task redirect or protocol clarification

    Attributes:
        day:                             Simulation day this comm was dispatched
        sender:                          Always "hermitclaw" (rule engine)
        message_type:                    Category; governs belief impact
        content:                         Template-generated text content
        belief_mc_support_delta:         Applied to belief_mission_control_support
        belief_resupply_reliability_delta: Applied to belief_resupply_reliability
    """
    day: int
    sender: str
    message_type: str
    content: str
    belief_mc_support_delta: float = 0.0
    belief_resupply_reliability_delta: float = 0.0
    belief_crew_cohesion_delta: float = 0.0   # direct cohesion belief boost (celebration, peer_check)
    workload_relief_factor: float = 0.0        # fraction removed from effective_workload [0, 0.30]

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "sender": self.sender,
            "message_type": self.message_type,
            "content": self.content,
            "belief_mc_support_delta": round(self.belief_mc_support_delta, 4),
            "belief_resupply_reliability_delta": round(self.belief_resupply_reliability_delta, 4),
            "belief_crew_cohesion_delta": round(self.belief_crew_cohesion_delta, 4),
            "workload_relief_factor": round(self.workload_relief_factor, 4),
        }


# ---------------------------------------------------------------------------
# Physical interventions (MC → resource layer, delayed)
# ---------------------------------------------------------------------------

@dataclass
class PlannedIntervention:
    """
    A scheduled physical intervention dispatched from Mission Control.

    Physical effects (payload) arrive on arrival_day via ResourceEngine.
    Crew belief effects (MC notified crew of ETA) arrive on dispatch_day
    via a companion MCCommunication with type "resupply_announcement".

    Delayed mechanics (executed in TwinRunner day loop):
        - dispatch_day: HermitClaw advisory triggers this intervention
        - Days in transit: if crew was notified, belief_resupply_reliability
          stays elevated (maintained by BeliefUpdateEngine)
        - arrival_day: ResourceEngine.schedule_resupply() applies the payload
        - Overdue (arrival_day passed, not received): belief_resupply_reliability
          decays sharply via resupply_overdue_days parameter

    Attributes:
        intervention_id:         Unique identifier
        intervention_type:       Semantic category (e.g. "resupply_coffee")
        dispatch_day:            Day HermitClaw triggered this
        eta_days:                Transit days before physical arrival
        arrival_day:             dispatch_day + eta_days
        predicted_morale_impact: Estimated mean morale gain [0, 1]
        predicted_trust_impact:  Estimated mean trust gain [0, 1]
        payload:                 resource_name -> amount to add
        applied:                 Set True by TwinRunner when payload arrives
    """
    intervention_id: str
    intervention_type: str
    dispatch_day: int
    eta_days: int
    arrival_day: int
    predicted_morale_impact: float
    predicted_trust_impact: float
    payload: Dict[str, float] = field(default_factory=dict)
    applied: bool = False

    def to_dict(self) -> dict:
        return {
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "dispatch_day": self.dispatch_day,
            "eta_days": self.eta_days,
            "arrival_day": self.arrival_day,
            "predicted_morale_impact": round(self.predicted_morale_impact, 4),
            "predicted_trust_impact": round(self.predicted_trust_impact, 4),
            "payload": self.payload,
            "applied": self.applied,
        }


# ---------------------------------------------------------------------------
# Inbound observations (crew behavior → MC)
# ---------------------------------------------------------------------------

@dataclass
class CrewReport:
    """
    Crew behavioral signal as observable by Mission Control.

    This is what MC would observe from telemetry and crew reports —
    NOT internal state, NOT resource engine, NOT belief engine.

    Computed by TwinRunner from per-agent actions and surface behavior.
    HermitClaw (full-access supervisor) receives this alongside objective state.

    Attributes:
        day:                   Simulation day
        mean_morale_reported:  Crew self-assessed morale proxy (mean future_outlook)
        dominant_action:       Most frequent ActionType value this day
        action_distribution:   {action_type.value: count}
        withdrawal_count:      Number of WITHDRAW actions
        escalation_count:      Number of ESCALATE actions
        cooperation_rate:      Fraction of crew in SUPPORT or ENGAGE
    """
    day: int
    mean_morale_reported: float
    dominant_action: str
    action_distribution: Dict[str, int]
    withdrawal_count: int
    escalation_count: int
    cooperation_rate: float

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "mean_morale_reported": round(self.mean_morale_reported, 4),
            "dominant_action": self.dominant_action,
            "action_distribution": self.action_distribution,
            "withdrawal_count": self.withdrawal_count,
            "escalation_count": self.escalation_count,
            "cooperation_rate": round(self.cooperation_rate, 4),
        }


# ---------------------------------------------------------------------------
# HermitClaw outputs
# ---------------------------------------------------------------------------

@dataclass
class DivergenceReport:
    """
    HermitClaw's daily read on crew-belief vs objective simulation state.

    Captures the gap between what the crew believes about their situation
    and what the twin engine has actually computed as their state.

    crew_belief_divergence interpretation:
        > 0:  Crew is more optimistic than their computed morale supports
              (MC comms or fairness beliefs are overtiding computed state)
        < 0:  Crew underestimates their own resilience
        = 0:  Belief and objective state are aligned

    high_risk_agents: agents with morale < 0.35 OR cooperation_threshold >= 0.70

    predicted_collapse_day: day when mean trust_in_crew would reach 0.25 at
        current 7-day linear drift rate; None if trend is stable or improving
    """
    day: int
    objective_morale_avg: float
    crew_believed_morale_avg: float
    crew_belief_divergence: float
    high_risk_agents: List[str]
    predicted_collapse_day: Optional[int]
    belief_distribution_fairness_avg: float
    trust_erosion_detected: bool
    mean_trust_in_crew: float

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "objective_morale_avg": round(self.objective_morale_avg, 4),
            "crew_believed_morale_avg": round(self.crew_believed_morale_avg, 4),
            "crew_belief_divergence": round(self.crew_belief_divergence, 4),
            "high_risk_agents": self.high_risk_agents,
            "predicted_collapse_day": self.predicted_collapse_day,
            "belief_distribution_fairness_avg": round(self.belief_distribution_fairness_avg, 4),
            "trust_erosion_detected": self.trust_erosion_detected,
            "mean_trust_in_crew": round(self.mean_trust_in_crew, 4),
        }


@dataclass
class HermitClawAdvisory:
    """
    HermitClaw's recommended intervention for Mission Control.

    All fields are rule-derived — no LLM, no stochastic logic.

    urgency interpretation:
        0.0–0.25: Nominal. Monitor only.
        0.25–0.50: Elevated. Consider proactive communication.
        0.50–0.75: High. Intervention recommended.
        0.75–1.00: Critical. Immediate action.

    Attributes:
        day:                      Simulation day
        recommended_intervention: Intervention type string, or None if nominal
        urgency:                  [0.0, 1.0]
        rationale:                Rule-derived explanation string (for Weke)
        divergence_report:        DivergenceReport used to generate this advisory
    """
    day: int
    recommended_intervention: Optional[str]
    urgency: float
    rationale: str
    divergence_report: DivergenceReport

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "recommended_intervention": self.recommended_intervention,
            "urgency": round(self.urgency, 4),
            "rationale": self.rationale,
            "divergence_report": self.divergence_report.to_dict(),
        }
