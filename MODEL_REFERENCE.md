# 3QP Model Reference — Technical and Scientific Basis

**Document version**: 1.1
**Corresponds to**: `params.py` SCHEMA_VERSION = "1.1"

---

## 1. The Third-Quarter Phenomenon — What the Model Represents

The **Third-Quarter Phenomenon (TQP)** is a well-documented pattern of behavioral and psychological deterioration that occurs approximately 50–75% through long-duration isolated and confined missions. Originally identified in Antarctic overwintering crews (Stuster, 1996), it has since been observed in:

- Antarctic winterover stations (Halley, Concordia, McMurdo)
- Space analog simulations (MARS-500, HI-SEAS, HERA)
- Polar expedition crews
- Early ISS long-duration missions

**Characteristic signatures** (Kanas & Manzey, 2008; Gushin et al., 1997):
- Declining crew cohesion and interpersonal friction peaking in the third quarter
- Increased conflict with Mission Control
- Reduced motivation, increased boredom, procedural shortcuts
- Psychophysiological evidence: cortisol elevation, sleep disruption, circadian entrainment loss
- Partial rebound as mission end approaches (terminal effect)

The TQP is not a single-cause phenomenon. It emerges from the interaction of:
1. **Monotony accumulation** — sustained identical environment, routine, and task set
2. **Psychological strain** — cumulative workload without sufficient recovery
3. **Social cohesion erosion** — dyadic friction compounding over time from repeated conflict
4. **Executive function degradation** — sleep debt and stress impairing planning and coordination

3QP models these as causally linked state variables, not as time-indexed statistical regularities.

---

## 2. Model Architecture

3QP is a layered causal simulation. Each layer reads from the one below; no layer writes back up.

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 6: Narrative & KPIs                              │
│  mission_story.py, mission_kpis.py                      │
├─────────────────────────────────────────────────────────┤
│  LAYER 5: Task Performance                              │
│  task_performance.py                                    │
│  4 task types × per-agent impairment × backlog load     │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: Per-Agent Internal State                      │
│  internal_state/astronaut_state.py                      │
│  7 variables: stress, morale, fatigue, boredom,         │
│               burnout, trust_in_crew, frustration       │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: Beliefs                                       │
│  beliefs/belief_engine.py                               │
│  Per-agent: scarcity, fairness, mc_support,             │
│             crew_cohesion, resupply_reliability         │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Perception                                    │
│  perception/perception_model.py                         │
│  Personality-filtered view of resources                 │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Resource Model                                │
│  resources/resource_model.py                            │
│  Objective consumables: food, coffee, sleep,            │
│  comms delay, equipment reliability                     │
├─────────────────────────────────────────────────────────┤
│  LAYER 0: Physics Engine (Ruthless Core)                │
│  phase4/06_Ruthless_Core_Model/ruthless_core.py         │
│  4 state variables: M, S, C, Q                          │
└─────────────────────────────────────────────────────────┘
```

**Key design invariants**:
- No internal state variable has a time-indexed drift term — all changes trace to belief inputs
- Resource scarcity never touches internal state directly — always via perception → belief
- Communication delay never directly reduces trust — must pass through interpretation
- Isolation duration alone does not bias state in any direction
- Same random seed always produces identical outputs

---

## 3. Physics Layer — The Ruthless Core Model

**File**: `phase4/06_Ruthless_Core_Model/ruthless_core.py`

The physics engine implements four coupled discrete-time difference equations. These run once per simulated day and produce the core state variables that feed all higher layers.

### 3.1 State Variables

| Variable | Symbol | Range | Interpretation |
|----------|--------|-------|----------------|
| Monotony | M(t) | [0, ∞) | Accumulated environmental sameness; grows daily, reduced by novelty |
| Strain | S(t) | [0, 1] | Psychological stress load; driven by workload and monotony |
| Cohesion | C(t) | [0.05, 1.2] | Crew social bond quality; eroded by strain and TQ pressure |
| TQ Pressure | Q(t) | [0, 1] | Emergent third-quarter pressure derived from M, S, C |

### 3.2 Difference Equations

**Monotony**:
```
M(t+1) = max(0,  M(t) + m_base  −  m_novelty × novelty(t))
```
Monotony accumulates at a fixed daily rate and is interrupted by novelty events. There is no spontaneous decay — a uniform environment remains monotonous unless disrupted.

**Strain**:
```
S(t+1) = max(0,  S(t)
              +  s_workload × workload(t)
              +  s_mono     × M(t)
              −  s_recovery × recovery(t)
              −  s_leak     × S(t))
```
Strain is driven by workload and amplified by monotony (boredom-induced strain). Recovery and a proportional leak term (physiological adaptation) prevent unbounded accumulation. The leak reflects the empirical finding that crews partially habituate to sustained strain (Kanas & Manzey, 2008, p. 142).

**TQ Pressure** (endogenous):
```
Q(t) = c_q_m × (M(t)/2.0)  +  c_q_s × S(t)  +  c_q_c × max(0, 1 − C(t))
```
Q is not a Gaussian hump centered on the calendar — it emerges from the crew's actual condition. A crew that maintains cohesion and manages strain will not exhibit a third-quarter crisis even mid-mission. A crew that deteriorates early can enter TQ pressure state before mission midpoint. This is the core causal claim: the TQP is a predictable consequence of state accumulation, not a calendar artifact.

**Cohesion**:
```
C(t+1) = clamp(C(t)
            −  c_strain × S(t)
            −  c_q      × Q(t)
            +  c_shared_success × success(t)
            +  c_rebound × (1 − C(t))  [if Q(t+1) < Q(t)])
```
Cohesion degrades under strain and TQ pressure, is partially restored by shared success events, and rebounds slightly when TQ pressure is actively falling. The rebound term captures the terminal effect: as the end of mission approaches and Q falls, crews often experience a cohesion recovery (Stuster, 2010).

### 3.3 Default Parameter Values and Basis

| Parameter | Value | Basis |
|-----------|-------|-------|
| `m_base` | 0.008 | Monotony reaches ~1.6 in 200 days with zero novelty; consistent with analog mission saturation reports |
| `m_novelty` | 0.20 | Novelty events (EVA, experiment milestone, supply arrival) observed to produce ~1–3 day monotony relief |
| `s_workload` | 0.03 | Moderate workload (0.6) produces ~0.018/day strain increase; reaches equilibrium with typical recovery |
| `s_mono` | 0.004 | Monotony-to-strain coupling; monotony at 1.0 adds 0.004/day strain — measurable but secondary to workload |
| `s_recovery` | 0.04 | Recovery rate matching empirical sleep/rest restoration observations |
| `s_leak` | 0.030 | Proportional adaptation; prevents strain from exceeding ~0.5 under normal load |
| `c_q_m` | 0.15 | Monotony contributes ~15% weight to TQ pressure at saturation |
| `c_q_s` | 0.20 | Strain contributes ~20% weight; primary Q driver |
| `c_q_c` | 0.10 | Cohesion deficit contributes ~10%; amplifier once cohesion degrades |
| `c_strain` | 0.008 | Strain erodes cohesion slowly; 0.5 strain → 0.004/day cohesion loss |
| `c_q` | 0.033 | TQ pressure erodes cohesion; peak Q → ~0.033/day loss |
| `c_shared_success` | 0.06 | Shared success events restore ~6% cohesion each |
| `c_rebound` | 0.01 | Terminal rebound limited to ~1% of cohesion deficit per day when Q is falling |

**Calibration status**: The physics engine has a complete Nelder-Mead fitting pipeline (`calibration/fit_cohesion.py`) ready to fit against empirical cohesion time-series data. The values above are structurally grounded but not yet fit to a real analog dataset. See Section 8 (Limitations).

---

## 4. Per-Agent Layer

Above the physics engine, each crew member is represented by independent perceptual, belief, and internal-state tracks.

### 4.1 Perception

Each agent perceives shared resources through a personality filter. An agent high in neuroticism perceives resource scarcity as more severe than an agent high in agreeableness perceiving the same objective availability. This is grounded in research on individual differences in threat appraisal (Lazarus & Folkman, 1984).

### 4.2 Beliefs (Named State)

Six named belief variables update daily from perception:

| Belief | Drives |
|--------|--------|
| `belief_scarcity` | Stress, frustration |
| `belief_fairness` | Trust in crew, frustration |
| `belief_mc_support` | Stress modulation, compliance with interventions |
| `belief_crew_cohesion` | Social behavior, action selection |
| `belief_resupply_reliability` | Long-horizon anxiety |
| `belief_personal_safety` | Stress, withdrawal behavior |

### 4.3 Internal State

Seven per-agent internal state variables drift daily:

| Variable | Key Drivers |
|----------|-------------|
| `stress` | belief_scarcity, workload, belief_personal_safety |
| `morale` | belief_fairness, success events, belief_mc_support |
| `fatigue` | sleep_debt, workload |
| `boredom` | monotony, low novelty |
| `burnout` | sustained high fatigue + low morale |
| `trust_in_crew` | belief_crew_cohesion, conflict events |
| `frustration_scarcity` | belief_scarcity, fairness violations |

### 4.4 Per-Agent Impairment

Each agent's operational impairment is computed from fatigue and stress:

```
impairment(agent) = clamp(fatigue × W_fatigue + stress × W_stress)

W_fatigue = AGENT_IMPAIRMENT_FATIGUE_WEIGHT = 0.50
W_stress  = AGENT_IMPAIRMENT_STRESS_WEIGHT  = 0.50
```

The worst-impaired agent in the crew becomes the `weakest_link_agent` for coordination tasks (Section 5.2).

**Basis**: Equal weighting of fatigue and stress reflects the joint contribution of physiological and psychological degradation to operational performance, consistent with cognitive impairment models of operator reliability (Wickens et al., 2015).

---

## 5. Task Performance Layer

**File**: `integration/runtime/task_performance.py`

Tasks are classified into four vulnerability channels. Each channel has a different physiological/psychological driver, grounded in occupational performance literature.

### 5.1 Task Types and Failure Equations

**Attention-Dependent Tasks** (checklists, monitoring, equipment checks):
```
fail_prob = clamp(monotony × W_attn_mono + (1 − sleep_quality) × W_attn_sleep)

W_attn_mono  = ATTN_MONOTONY_WEIGHT      = 0.30
W_attn_sleep = ATTN_SLEEP_DEFICIT_WEIGHT = 0.45
```
*Basis*: Vigilance decrements under sustained monotony are among the most replicated findings in applied psychology (Mackworth, 1948; Warm et al., 2008). Sleep deprivation produces attention failures at rates measurable in real operational settings (Harrison & Horne, 2000).

**Coordination Tasks** (joint EVA, crew handoffs, procedure requiring multi-person execution):
```
base_prob  = clamp(strain × W_coord_strain)
fail_prob  = clamp(base_prob × (1 + max_agent_impairment × COORD_WEAKEST_LINK_AMP))

W_coord_strain       = COORD_STRAIN_WEIGHT       = 1.20
COORD_WEAKEST_LINK_AMP = COORD_WEAKEST_LINK_AMP = 0.80
```
*Basis*: Interpersonal coordination under stress is disproportionately impaired by the least-capable team member — the weakest-link principle (Laughlin et al., 2002). The amplification factor of 0.80 reflects that the weakest link degrades coordination faster than would be predicted by averaging across agents.

The higher base coefficient (1.20) reflects research showing coordination tasks are more sensitive to strain than individual tasks (Starcke & Brand, 2012).

**Planning and Multi-Step Tasks** (task scheduling, procedure development, complex maintenance):
```
fail_prob = clamp(strain × W_plan_strain)

W_plan_strain = PLAN_STRAIN_WEIGHT = 0.90
```
*Basis*: Executive function (planning, working memory, cognitive flexibility) is reliably impaired by psychological strain, with effect sizes larger than for simple task performance (Shields et al., 2016).

**Persistence Tasks** (recurring maintenance, documentation, logs):
```
fail_prob = clamp(monotony × W_persist_mono)

W_persist_mono = PERSIST_MONOTONY_WEIGHT = 0.25
```
*Basis*: Routine maintenance and documentation tasks are primarily vulnerable to motivational depletion from monotony and boredom. The relationship between sustained monotony and procedural shortcutting is well-documented in aviation and long-duration mission analog research (Thackray, 1981; Stuster, 2010).

### 5.2 Weakest-Link Coordination

For coordination tasks, the most-impaired crew member is identified daily:

```
weakest_link_agent = argmax(impairment[agent] for agent in crew)
max_agent_impairment = max(impairment values)
```

The weakest-link agent and their impairment level are recorded in every coordination task's causal trace. This enables post-mission analysis of which crew member was the proximate failure contributor.

### 5.3 Backlog Dynamics

Skipped persistence tasks do not disappear — they accumulate as deferred maintenance load and feed forward into workload:

```
backlog(t+1) = (backlog(t) + skipped_tasks(t)) × BACKLOG_NATURAL_DECAY

backlog_pressure = min(BACKLOG_MAX_LOAD, backlog × BACKLOG_WORKLOAD_PER_SKIP)
effective_workload(t) = clamp(effective_workload(t) + backlog_pressure)

BACKLOG_WORKLOAD_PER_SKIP = 0.008   # workload added per skip in backlog
BACKLOG_MAX_LOAD          = 0.10    # maximum backlog-induced workload addition
BACKLOG_NATURAL_DECAY     = 0.97    # 3% daily decay (tasks completed, superseded, or expired)
```

*Basis*: Maintenance backlog is a real operational phenomenon in long-duration missions. ISS maintenance logs document deferred tasks compounding into crew overtime and increased failure risk. The decay term reflects that some deferred tasks become moot as circumstances change.

---

## 6. Dyadic Conflict Memory

Social dynamics between specific agent pairs are tracked separately from crew-level cohesion:

```
dyad_conflict[i,j](t+1) = dyad_conflict[i,j](t) × DYAD_CONFLICT_DECAY

# On conflict event:
dyad_conflict[i,j] += DYAD_CONFLICT_INCREMENT / n_pairs

# Cohesion suppression per agent:
suppression = min(DYAD_TRUST_SUPPRESSOR, max_conflict × DYAD_TRUST_SUPPRESSOR)
belief_crew_cohesion(agent) -= suppression

DYAD_CONFLICT_INCREMENT = 0.12    # conflict penalty per event (distributed)
DYAD_CONFLICT_DECAY     = 0.97    # daily decay (forgiveness / memory fade)
DYAD_TRUST_SUPPRESSOR   = 0.30    # max cohesion suppression from dyadic conflict
```

*Basis*: Dyadic interpersonal conflicts in confined crews do not resolve spontaneously — they establish negative interaction patterns that persist and compound (Kanas et al., 2006; Stuster, 1996). Individual pair tensions are documented as the precipitating cause in several historical crew conflict incidents, distinct from crew-wide morale decline.

---

## 7. Executive Function and Circadian Degradation

### 7.1 Executive Function Impairment

High mean fatigue and stress reduce the effective quality of workload execution:

```
exec_impairment = clamp((mean_fatigue × W_exec_fatigue + mean_stress × W_exec_stress − EXEC_THRESHOLD) × EXEC_SCALE)

At full impairment:
effective_workload  = clamp(effective_workload × (1 + exec_impairment × EXEC_WORKLOAD_AMP))
effective_recovery  = clamp(effective_recovery × (1 − exec_impairment × EXEC_RECOVERY_SUPPRESS))

EXEC_FATIGUE_WEIGHT      = 0.55   W_exec_fatigue
EXEC_STRESS_WEIGHT       = 0.45   W_exec_stress
EXEC_THRESHOLD           = 0.35   impairment activates above ~0.35 mean
EXEC_SCALE               = 1.40
EXEC_WORKLOAD_AMP        = 0.25   +25% effective workload at full impairment
EXEC_RECOVERY_SUPPRESS   = 0.20   −20% effective recovery at full impairment
```

*Basis*: Higher weighting on fatigue (0.55) reflects the stronger dose-response curve between sleep deprivation and executive function compared to acute stress (Van Dongen et al., 2003). The threshold at 0.35 means well-rested, low-stress crews are unaffected.

### 7.2 Circadian Drift

Sleep debt accumulates a circadian phase drift that compounds sleep quality degradation:

```
if sleep_debt > CIRCADIAN_ACCUM_THRESHOLD:
    circadian_drift += CIRCADIAN_ACCUM_RATE × sleep_debt
else:
    circadian_drift = max(0, circadian_drift − CIRCADIAN_RECOVERY_RATE)

sleep_quality_effective = sleep_quality − circadian_drift

CIRCADIAN_ACCUM_THRESHOLD = 0.04
CIRCADIAN_ACCUM_RATE      = 0.0008
CIRCADIAN_RECOVERY_RATE   = 0.0004
```

*Basis*: Circadian misalignment in long-duration spaceflight is a documented and measurable phenomenon (Monk et al., 1992; Barger et al., 2014). The slow accumulation (0.0008/day) and slower recovery (0.0004/day) reflects empirical findings that circadian disruption takes longer to reverse than to acquire.

---

## 8. Intervention Compliance Scaling

Mission Control communications are not uniformly effective. Severely strained or frustrated agents show reduced compliance:

```
strain_reactance     = max(0, (stress − COMPLIANCE_STRAIN_THRESHOLD)     × COMPLIANCE_STRAIN_SCALE)
frustration_reactance = max(0, (frustration − COMPLIANCE_FRUSTRATION_THRESHOLD) × COMPLIANCE_FRUSTRATION_SCALE)

compliance = max(COMPLIANCE_FLOOR, 1 − strain_reactance − frustration_reactance)
effective_delta = comm_delta × compliance

COMPLIANCE_STRAIN_THRESHOLD       = 0.50
COMPLIANCE_FRUSTRATION_THRESHOLD  = 0.50
COMPLIANCE_STRAIN_SCALE           = 0.60
COMPLIANCE_FRUSTRATION_SCALE      = 0.40
COMPLIANCE_FLOOR                  = 0.35
```

*Basis*: Reactance theory (Brehm, 1966) and operational research on crew-MC relationships (Kanas et al., 2000) document that stressed or frustrated crews often reject or minimally comply with Mission Control directives. The floor at 0.35 ensures interventions are never entirely inert — even resistant crews retain some response.

---

## 9. Phase-Aware Event Generation

The `MicroEventEngine` generates daily stochastic events with phase-dependent probabilities:

| Event Type | TQ Window (50–74%) | Late Phase (75–100%) |
|------------|-------------------|---------------------|
| Conflict events | ×1.8 | ×1.0 |
| Schedule slips | ×1.3 | ×1.5 |
| Novel tasks | ×0.5 | ×0.3 |
| Wins/successes | ×0.6 | ×0.4 |
| Equipment failures | ×1.0 | ×1.4 |

*Basis*: Phase variation preserves endogenous causal emergence (the simulation doesn't know it's in TQ — it just processes inputs). The multipliers reflect documented real mission patterns: conflict frequency increases in the third quarter, novelty decreases as the environment becomes fully explored, and equipment failure rates increase over mission duration (NASA Human Research Program, 2021).

---

## 10. Collapse Taxonomy

Phase D counterfactual validation identified four distinct failure modes:

| Mode | Signature | Primary Cause | Typical Onset |
|------|-----------|---------------|---------------|
| **Cohesion-Led** | Gradual C decline, Q rises late | Accumulated strain + low success events | 55–70% |
| **Strain-Spike** | Rapid S increase, fast C collapse | High workload burst, insufficient recovery | 20–40% |
| **Dyadic Fracture** | Crew-level C intact, one pair extremes | Specific dyad conflict escalation | Variable |
| **Monotony Erosion** | S low, M high, disengagement | No novelty, low workload variance | 60–80% |

These modes were reproduced across 11 controlled counterfactual experiments varying mission duration, crew composition, and intervention timing.

---

## 11. Validation and Testing

### 11.1 Internal Validation (Phase D)

11 controlled experiments validate causal mechanisms:
1. Baseline TQP emergence (200-day mission)
2. Extended mission TQP timing shift
3. Short mission (no TQP)
4. High-cohesion crew resistance
5. Fragile crew early onset
6. Late intervention (day 150+) — limited effect
7. Early intervention (day 50–80) — protective effect
8. Intervention during TQP — partial recovery
9. Crew size effects
10. Workload variation effects
11. Monotony reduction (novelty injection) effects

All 11 pass validation checks in `phase_d/validate_phase_d.py`.

### 11.2 Sensitivity Analysis

The sensitivity sweep (`sensitivity.py`) tests ±20% variation across 8 parameters:

**Fast sweep** (task coefficient re-evaluation):
- `ATTN_MONOTONY_WEIGHT`, `ATTN_SLEEP_DEFICIT_WEIGHT`
- `COORD_STRAIN_WEIGHT`, `COORD_WEAKEST_LINK_AMP`
- `PLAN_STRAIN_WEIGHT`, `PERSIST_MONOTONY_WEIGHT`

**Full-rerun sweep** (requires simulation rerun):
- `BACKLOG_WORKLOAD_PER_SKIP`
- `PHASE_MULTIPLIER_SCALE`

**Acceptance criteria**:
- Coordination failure rate increases in TQ window vs early phase (PASS/FAIL)
- Maintenance skip rate increases in TQ window vs early phase (PASS/FAIL)
- Planning failure rate non-decreasing across phases (PASS/WARN)

### 11.3 Reproducibility

Every run produces a `run_manifest.json` containing the complete parameter registry, random seed, and a `hash_summary` of deterministic outputs. Any run can be exactly reproduced from its manifest using `replay.py`.

---

## 12. Known Limitations and Calibration Gaps

| Limitation | Status | Path to Resolution |
|------------|--------|--------------------|
| **No empirical calibration** | Physics parameters are structurally grounded but not fit to real data | Calibration pipeline ready (`calibration/fit_cohesion.py`); requires MARS-500, HERA, or HI-SEAS cohesion time-series |
| **No external validation** | Model not yet compared against held-out real mission outcomes | Requires a labeled dataset of crew performance degradation |
| **Task dependency graph** | Tasks are currently independent; a skipped EVA prep does not elevate EVA failure probability | Planned feature (see implementation roadmap) |
| **Discrete time** | Daily time step; no intra-day dynamics | Acceptable for mission-level analysis; insufficient for shift-level scheduling |
| **Crew size** | Dyadic conflict model scales with pairs; tested up to 4 agents | Larger crews (6–7 astronauts) should be tested |
| **No heterogeneous task capacity** | All agents are equally capable of all task types | Planned: specialty mapping per crew member |
| **LLM narrative not integrated** | `narrative_renderer.py` exists but is not called by TwinRunner | Requires OpenAI API key; optional overlay |
| **No real NASA validation** | System designed to be validated but has not been tested against actual ISS data | Requires data sharing agreement |

---

## 13. Literature References

Barger, L.K., et al. (2014). *Prevalence of sleep deficiency and use of hypnotic drugs in astronauts before, during, and after spaceflight*. The Lancet Neurology, 13(9), 904–912.

Brehm, J.W. (1966). *A Theory of Psychological Reactance*. Academic Press.

Gushin, V.I., et al. (1997). *Subject's perceptions of the crew interaction dynamics under prolonged isolation*. Aviation, Space, and Environmental Medicine, 68(6), 556–561.

Harrison, Y., & Horne, J.A. (2000). *The impact of sleep deprivation on decision making: A review*. Journal of Experimental Psychology: Applied, 6(3), 236–249.

Kanas, N., & Manzey, D. (2008). *Space Psychology and Psychiatry* (2nd ed.). Springer.

Kanas, N., et al. (2000). *Crewmember and mission control personnel interactions during International Space Station missions*. Aviation, Space, and Environmental Medicine, 71(11), 1073–1076.

Kanas, N., et al. (2006). *Psychosocial issues affecting simulated planetary missions*. Acta Astronautica, 60(4), 666–672.

Laughlin, P.R., et al. (2002). *Groups perform better than the best individuals on letters-to-numbers problems: Effects of group size*. Journal of Personality and Social Psychology, 90(4), 644–651.

Lazarus, R.S., & Folkman, S. (1984). *Stress, Appraisal, and Coping*. Springer.

Mackworth, N.H. (1948). *The breakdown of vigilance during prolonged visual search*. Quarterly Journal of Experimental Psychology, 1(1), 6–21.

Monk, T.H., et al. (1992). *Circadian rhythms in human performance and mood under constant conditions*. Journal of Sleep Research, 1(2), 95–101.

NASA Human Research Program (2021). *Evidence Report: Risk of Adverse Cognitive or Behavioral Conditions and Psychiatric Disorders*. Johnson Space Center.

Shields, G.S., et al. (2016). *The effects of acute stress on core executive functions: A meta-analysis and comparison with cortisol*. Neuroscience & Biobehavioral Reviews, 68, 651–668.

Starcke, K., & Brand, M. (2012). *Decision making under stress: A selective review*. Neuroscience & Biobehavioral Reviews, 36(4), 1228–1248.

Stuster, J. (1996). *Bold Endeavors: Lessons from Polar and Space Exploration*. Naval Institute Press.

Stuster, J. (2010). *Behavioral Issues Associated with Long-Duration Space Expeditions: Review and Analysis of Astronaut Journals*. NASA/TM-2010-216130.

Thackray, R.I. (1981). *The stress of boredom and monotony: A consideration of the evidence*. Psychosomatic Medicine, 43(2), 165–176.

Van Dongen, H.P.A., et al. (2003). *The cumulative cost of additional wakefulness: Dose-response effects on neurobehavioral functions and sleep physiology from chronic sleep restriction and total sleep deprivation*. Sleep, 26(2), 117–126.

Warm, J.S., et al. (2008). *Vigilance requires hard mental work and is stressful*. Human Factors, 50(3), 433–441.

Wickens, C.D., et al. (2015). *Engineering Psychology and Human Performance* (4th ed.). Psychology Press.

---

## 14. Contact and Attribution

**Developer**: Rhys O'Neill, The MITRE Corporation
**Purpose**: NASA behavioral health training and mission planning tool
**Status**: Research prototype — calibration against empirical data pending

This model is built to be publishable. Contributions to calibration, validation, and peer review are actively sought.
