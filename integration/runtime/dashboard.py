"""
3QP Mission Control Room — Interactive Behavioral Twin Dashboard

A mission-control-grade Streamlit dashboard for the 3QP behavioral twin system.
Showcases the full 6-layer causal pipeline, per-agent divergence, social network
dynamics, causal failure forensics, and counterfactual intervention analysis.

Launch:
    cd 3QP/integration/runtime
    streamlit run dashboard.py

Requires:
    pip install streamlit plotly
"""

import json
import inspect
import math
import sys
from pathlib import Path

# --- Path setup (before any project imports) ---
_HERE = Path(__file__).parent.resolve()
_ROOT = _HERE.parent.parent.resolve()
_PHASE4 = _ROOT / "phase4" / "06_Ruthless_Core_Model"
_SOCIAL_NET = _ROOT / "modules" / "05_Social_Network"
for _p in [str(_HERE), str(_ROOT), str(_PHASE4), str(_SOCIAL_NET)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from twin_runner import TwinRunner, TwinRunnerConfig
from interventions import INTERVENTION_CATALOGUE, make_comm
from resources.resource_model import ResourceConfig

try:
    from crew import get_crew_preset, list_available_presets
    _PRESETS = list_available_presets()
except Exception:
    from crew import get_crew_preset
    _PRESETS = ["high_cohesion_team", "fragile_team", "extroverted_explorers"]


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="3QP Mission Control",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# NASA-blue shell + black interactive visual surfaces
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Oxanium:wght@500;600;700&display=swap');

    :root {
        --nasa-blue-900: #071a38;
        --nasa-blue-800: #0d2b57;
        --nasa-blue-700: #15407f;
        --nasa-blue-500: #2f7dd3;
        --nasa-ink: #dbe9ff;
        --nasa-muted: #9fbde5;
        --nasa-line: #2a4f84;
        --viz-black: #05080f;
        --viz-grid: #182845;
        --accent: #5ca9ff;
        --warning: #f4ab54;
        --error: #ef7676;
        --success: #65d28d;
    }

    html, body, [class*="css"], .stApp {
        font-family: "Manrope", "Segoe UI", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(1200px 600px at -10% -20%, rgba(92,169,255,0.20) 0%, rgba(92,169,255,0.05) 50%, transparent 75%),
            radial-gradient(1000px 520px at 110% 15%, rgba(130,190,255,0.14) 0%, rgba(130,190,255,0.05) 46%, transparent 72%),
            linear-gradient(150deg, var(--nasa-blue-900) 0%, var(--nasa-blue-800) 40%, #143e73 100%);
        color: var(--nasa-ink);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #061227 0%, #0a2347 100%);
        border-right: 1px solid rgba(74, 144, 217, 0.35);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px 9px 0 0;
    }
    .stTabs [data-baseweb="tab"] p {
        font-family: "Oxanium", "Manrope", sans-serif;
        letter-spacing: 0.02em;
        font-weight: 600;
    }

    .stButton > button {
        border-radius: 8px;
        border: 1px solid rgba(116, 181, 255, 0.45);
        background: linear-gradient(180deg, rgba(19, 61, 113, 0.82) 0%, rgba(14, 47, 93, 0.92) 100%);
        color: #d7e8ff;
    }
    .stButton > button:hover {
        border-color: rgba(146, 201, 255, 0.72);
        color: #f4f9ff;
    }

    div[data-testid="stPlotlyChart"] {
        background: linear-gradient(165deg, rgba(6,9,16,0.98) 0%, rgba(6,11,20,0.95) 100%);
        border: 1px solid #1f3558;
        border-radius: 12px;
        padding: 6px 8px 2px;
        box-shadow:
            inset 0 0 0 1px rgba(125, 169, 230, 0.08),
            0 14px 28px rgba(2, 6, 16, 0.22);
        margin-bottom: 8px;
    }

    /* Header bar */
    .mc-header {
        background: linear-gradient(135deg, #082043 0%, #113566 100%);
        border: 1px solid var(--nasa-line);
        border-radius: 10px;
        padding: 22px 28px 18px;
        margin-bottom: 20px;
        box-shadow: 0 10px 24px rgba(2, 10, 24, 0.22);
    }
    .mc-eyebrow {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #8bc2ff;
        margin-bottom: 6px;
    }
    .mc-title {
        font-family: "Oxanium", "Manrope", sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #eef6ff;
        margin-bottom: 4px;
    }
    .mc-sub {
        font-size: 12px;
        color: #bed4f2;
    }

    /* KPI card row */
    .kpi-row {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .kpi-card {
        flex: 1;
        min-width: 140px;
        background: linear-gradient(180deg, rgba(11, 39, 79, 0.90) 0%, rgba(8, 31, 64, 0.94) 100%);
        border: 1px solid rgba(75, 128, 197, 0.45);
        border-radius: 10px;
        padding: 16px 18px;
    }
    .kpi-label {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #8eaed8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-family: "Oxanium", "Manrope", sans-serif;
        font-size: 26px;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 4px;
    }
    .kpi-sub {
        font-size: 10px;
        color: #9ab7df;
    }
    .kpi-value.red { color: var(--error); }
    .kpi-value.blue { color: var(--accent); }
    .kpi-value.green { color: var(--success); }
    .kpi-value.orange { color: var(--warning); }
    .kpi-value.white { color: #eef6ff; }

    /* Failure badge */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .badge-high { background: rgba(239,118,118,0.20); color: var(--error); border: 1px solid rgba(239,118,118,0.55); }
    .badge-medium { background: rgba(244,171,84,0.20); color: var(--warning); border: 1px solid rgba(244,171,84,0.55); }
    .badge-low { background: rgba(92,169,255,0.20); color: var(--accent); border: 1px solid rgba(92,169,255,0.55); }
    .badge-error { background: rgba(239,118,118,0.16); color: var(--error); }
    .badge-skip { background: rgba(160, 184, 214, 0.16); color: #adc2df; }
    .badge-delay { background: rgba(244,171,84,0.16); color: var(--warning); }

    /* Story panel */
    .story-panel {
        background: rgba(9, 34, 70, 0.75);
        border: 1px solid var(--nasa-line);
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 12px;
    }
    .story-sentence {
        font-size: 13px;
        color: #d3e4ff;
        line-height: 1.8;
        margin-bottom: 8px;
        padding-left: 12px;
        border-left: 2px solid #3b6ba8;
    }

    /* Causal chain */
    .causal-chain {
        background: rgba(9, 34, 70, 0.72);
        border: 1px solid var(--nasa-line);
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 12px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
        color: #bfd6f8;
        margin-top: 8px;
    }
    .causal-arrow { color: #70b5ff; font-weight: bold; margin: 0 8px; }
    .causal-value { color: #f0f6ff; font-weight: 600; }

    /* Tab section label */
    .section-label {
        font-family: "Oxanium", "Manrope", sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #a8c8f3;
        margin: 18px 0 10px;
    }

    /* Orbital explorer details */
    .orbit-detail-card {
        background: rgba(8, 28, 58, 0.78);
        border: 1px solid rgba(88, 145, 219, 0.5);
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }
    .orbit-detail-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #9dbde9;
        margin-bottom: 6px;
    }
    .orbit-detail-value {
        font-family: "Oxanium", "Manrope", sans-serif;
        font-size: 34px;
        font-weight: 700;
        line-height: 1;
        color: #f2f8ff;
        margin-bottom: 6px;
    }
    .orbit-meta {
        font-size: 11px;
        color: #bdd4f5;
        margin-bottom: 8px;
    }
    .planet-chip {
        display: inline-block;
        border: 1px solid rgba(96, 151, 224, 0.42);
        border-radius: 999px;
        padding: 3px 10px;
        margin: 3px 4px 0 0;
        font-size: 10px;
        color: #cadefb;
        background: rgba(16, 50, 96, 0.54);
    }
    .planet-chip-active {
        border-color: rgba(185, 223, 255, 0.82);
        background: rgba(44, 105, 177, 0.78);
        color: #f2f8ff;
    }

    /* Narrative sentence prefix */
    .phase-tag {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-right: 6px;
        vertical-align: middle;
    }
    .phase-early { background: #1e4b86; color: #93c8ff; }
    .phase-tq { background: #5d3b0d; color: #ffc47a; }
    .phase-late { background: #3b2b61; color: #cbb8f6; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Color palette & Plotly dark layout base
# ---------------------------------------------------------------------------

_PALETTE = {
    "strain":   "#ef7676",
    "cohesion": "#65d28d",
    "monotony": "#f4ab54",
    "tq":       "#8f8cf8",
    "accent":   "#5ca9ff",
    "muted":    "#95b3da",
    "text":     "#dbe9ff",
    "success":  "#65d28d",
    "warning":  "#f4ab54",
    "error":    "#ef7676",
}

_AGENT_COLORS = ["#5ca9ff", "#ef7676", "#65d28d", "#f4ab54", "#8f8cf8", "#2fc7bf"]

_DARK_LAYOUT = dict(
    paper_bgcolor="#05080f",
    plot_bgcolor="#05080f",
    font=dict(
        family='"Manrope", "Segoe UI", sans-serif',
        size=11,
        color="#bed4f5",
    ),
    xaxis=dict(
        gridcolor="#182845", zerolinecolor="#182845",
        tickcolor="#22385d", linecolor="#22385d",
    ),
    yaxis=dict(
        gridcolor="#182845", zerolinecolor="#182845",
        tickcolor="#22385d", linecolor="#22385d",
    ),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#0a1324", bordercolor="#29466f",
        font=dict(size=12, color="#dbe9ff"),
    ),
)


def _dl(**overrides) -> dict:
    """Return a copy of _DARK_LAYOUT merged with overrides."""
    import copy
    base = copy.deepcopy(_DARK_LAYOUT)
    base.update(overrides)
    return base


def _axis(**kw) -> dict:
    return dict(gridcolor="#182845", zerolinecolor="#182845",
                tickcolor="#22385d", linecolor="#22385d", **kw)


def _decorate(fig, tq_start, tq_end, comm_days, rows=1, cols=1, row_col_pairs=None):
    """Add TQ window shading and MC comm vertical lines to a figure."""
    pairs = row_col_pairs or [(r + 1, c + 1) for r in range(rows) for c in range(cols)]
    for r, c in pairs:
        fig.add_vrect(
            x0=tq_start, x1=tq_end,
            fillcolor="rgba(232,146,74,0.07)", line_width=0,
            row=r, col=c,
        )
        for cd in comm_days:
            fig.add_vline(
                x=cd, line_dash="dot",
                line_color="rgba(74,144,217,0.45)",
                row=r, col=c,
            )
    return fig


def _tqp_emergence_score(day_states, T):
    """Compute TQP Emergence Score: relative strain amplification in TQ window vs early."""
    early_end = int(T * 0.25)
    tq_start_i = int(T * 0.50)
    tq_end_i = int(T * 0.75)
    early_strains = [d.core_strain for d in day_states[:early_end]]
    tq_strains = [d.core_strain for d in day_states[tq_start_i:tq_end_i]]
    if not early_strains or not tq_strains:
        return 0.0
    mean_early = sum(early_strains) / len(early_strains)
    mean_tq = sum(tq_strains) / len(tq_strains)
    if mean_early < 0.001:
        return 0.0
    return (mean_tq - mean_early) / mean_early


def _collect_causal_traces(day_states):
    """Return flat list of (day, trace_dict) for all days with causal traces."""
    traces = []
    for ds in day_states:
        if ds.task_outcomes:
            for tr in ds.task_outcomes.get("causal_traces", []):
                traces.append((ds.day, tr))
    return traces


def _phase_label(day, T):
    frac = day / T
    if frac < 0.50:
        return "early"
    elif frac < 0.75:
        return "tq"
    else:
        return "late"


def _safe_plotly_chart(fig, key=None, enable_selection=False):
    """Render Plotly chart and enable point selection only when supported by Streamlit."""
    kwargs = {"use_container_width": True}
    if key is not None:
        kwargs["key"] = key

    if enable_selection:
        try:
            sig = inspect.signature(st.plotly_chart)
            if "on_select" in sig.parameters:
                kwargs["on_select"] = "rerun"
                kwargs["selection_mode"] = ("points",)
        except (TypeError, ValueError):
            pass

    return st.plotly_chart(fig, **kwargs)


def _extract_selected_point_index(selection_data):
    """Extract selected point index from Streamlit plotly selection payload."""
    if not isinstance(selection_data, dict):
        return None

    point_candidates = []

    if isinstance(selection_data.get("selection"), dict):
        point_candidates.extend(selection_data["selection"].get("points", []) or [])

    point_candidates.extend(selection_data.get("points", []) or [])

    if not point_candidates:
        return None

    first_point = point_candidates[0]
    if not isinstance(first_point, dict):
        return None

    for key in ("point_index", "pointNumber", "point_number", "pointIndex"):
        value = first_point.get(key)
        if isinstance(value, int):
            return value

    return None


def _series_value_at_day(series, day_value, days):
    """Read nearest series value for a selected mission day."""
    if not series:
        return 0.0
    idx = min(range(len(days)), key=lambda i: abs(days[i] - day_value))
    return series[idx]


def _orbital_insight(metric_key, value, delta):
    trend = "rising" if delta > 0.012 else "falling" if delta < -0.012 else "stable"

    if metric_key == "strain":
        if value >= 0.75:
            return f"Crew strain is {trend} in the high-risk band; expect execution volatility unless recovery gains are introduced."
        if value >= 0.55:
            return f"Crew strain remains elevated and {trend}; monitor scheduling load and protect sleep quality."
        return f"Crew strain is currently controlled and {trend}; resilience margin remains available."

    if metric_key == "cohesion":
        if value <= 0.42:
            return f"Cohesion is {trend} near fracture territory; conflict repair and support actions are priority."
        if value <= 0.62:
            return f"Cohesion is moderate and {trend}; the crew network is sensitive to additional stressors."
        return f"Cohesion remains strong and {trend}; social buffering is still protective."

    if metric_key == "monotony":
        if value >= 0.72:
            return f"Monotony is {trend} at suppressive levels; novelty insertion is likely needed to prevent disengagement drift."
        if value >= 0.52:
            return f"Monotony is building and {trend}; watch for boredom-driven drops in effort quality."
        return f"Monotony is manageable and {trend}; current novelty cadence is effective."

    if metric_key == "tq_pressure":
        if value >= 0.65:
            return f"Third-Quarter pressure is {trend} in a sharp amplification zone; small shocks may cascade quickly."
        if value >= 0.45:
            return f"Third-Quarter pressure is active and {trend}; mitigation timing is now consequential."
        return f"Third-Quarter pressure is low and {trend}; no acute signature currently dominates."

    if metric_key == "social_cohesion":
        if value <= 0.45:
            return f"Graph cohesion is {trend} in a fragmented regime; dyadic interventions should be prioritized."
        if value <= 0.62:
            return f"Graph cohesion is mid-band and {trend}; cliques may form under additional pressure."
        return f"Graph cohesion remains healthy and {trend}; trust pathways are still broadly connected."

    if metric_key == "recovery":
        if value <= 0.35:
            return f"Recovery capacity is {trend} in constrained territory; sustained output will degrade if this persists."
        if value <= 0.55:
            return f"Recovery capacity is moderate and {trend}; keep workload bursts bounded."
        return f"Recovery capacity is solid and {trend}; crew can absorb moderate volatility."

    return f"{metric_key.replace('_', ' ').title()} is {trend} at {value:.3f}."


# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div style="font-size:11px;font-weight:600;letter-spacing:0.12em;'
        'text-transform:uppercase;color:#4a90d9;margin-bottom:6px;">3QP MISSION CONTROL</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    crew_preset = st.selectbox(
        "Crew Preset",
        _PRESETS,
        help="Personality profile of the simulated crew.",
    )

    mission_days = st.slider(
        "Mission Duration (days)",
        min_value=30, max_value=365, value=120, step=10,
    )

    mission_name = st.text_input("Mission Name", value="mission_01")

    st.markdown("---")
    st.markdown(
        '<div style="font-size:10px;font-weight:600;letter-spacing:0.10em;'
        'text-transform:uppercase;color:#5b7099;margin-bottom:8px;">MC INTERVENTIONS</div>',
        unsafe_allow_html=True,
    )

    if "interventions" not in st.session_state:
        st.session_state.interventions = []

    comm_type = st.selectbox(
        "Type",
        list(INTERVENTION_CATALOGUE.keys()),
        label_visibility="collapsed",
    )
    spec = INTERVENTION_CATALOGUE[comm_type]
    st.caption(spec["description"].split(";")[0])

    comm_day = st.number_input(
        "On Day",
        min_value=1, max_value=mission_days,
        value=max(1, mission_days // 2),
        step=1,
    )

    c1, c2 = st.columns(2)
    if c1.button("Add", use_container_width=True):
        st.session_state.interventions.append((comm_type, int(comm_day)))
        st.session_state.interventions.sort(key=lambda x: x[1])
    if c2.button("Clear", use_container_width=True):
        st.session_state.interventions = []

    if st.session_state.interventions:
        st.markdown(
            '<div style="font-size:10px;color:#5b7099;margin-top:6px;'
            'text-transform:uppercase;letter-spacing:0.08em;">Scheduled</div>',
            unsafe_allow_html=True,
        )
        for _t, _d in st.session_state.interventions:
            st.markdown(
                f'<div style="font-size:11px;color:#9ab0d4;padding:2px 0;">'
                f'<span style="color:#4a90d9;font-weight:600;">Day {_d:3d}</span>'
                f'&nbsp;&nbsp;{_t}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    run_btn = st.button("▶  Run Simulation", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

for _key in ["result", "result_baseline", "run_cfg"]:
    if _key not in st.session_state:
        st.session_state[_key] = None
if "run_cfg" not in st.session_state or st.session_state.run_cfg is None:
    st.session_state.run_cfg = {}


# ---------------------------------------------------------------------------
# Run simulation
# ---------------------------------------------------------------------------

def _run(crew_preset, mission_days, mission_name, interventions, with_comms=True):
    crew_profile = get_crew_preset(crew_preset)
    seed = hash(mission_name) % (2 ** 31)
    cfg = TwinRunnerConfig(
        mission_name=mission_name if with_comms else f"{mission_name}_baseline",
        mission_length_days=mission_days,
        crew_profile=crew_profile,
        resource_config=ResourceConfig(),
        output_dir="output",
        verbose=False,
        random_seed=seed,  # same seed for both runs — isolates intervention effect
    )
    runner = TwinRunner(cfg)
    if with_comms:
        for _itype, _iday in interventions:
            runner.schedule_mc_communication(_iday, make_comm(_itype, day=_iday))
    return runner.run()


if run_btn:
    has_interventions = bool(st.session_state.interventions)
    label = f"Running {mission_days}-day simulation ({crew_preset})"
    if has_interventions:
        label += f" + baseline comparison"
    with st.spinner(label + "..."):
        try:
            result = _run(crew_preset, mission_days, mission_name,
                          st.session_state.interventions, with_comms=True)
            st.session_state.result = result
            st.session_state.run_cfg = {
                "crew_preset": crew_preset,
                "mission_days": mission_days,
                "mission_name": mission_name,
                "interventions": list(st.session_state.interventions),
            }

            # Run baseline (no comms, same seed) only when there are interventions
            if has_interventions:
                baseline = _run(crew_preset, mission_days, mission_name,
                                st.session_state.interventions, with_comms=False)
                st.session_state.result_baseline = baseline
            else:
                st.session_state.result_baseline = None

        except Exception as _e:
            st.error(f"Simulation failed: {_e}")
            import traceback
            st.code(traceback.format_exc())


# ---------------------------------------------------------------------------
# Welcome screen
# ---------------------------------------------------------------------------

if st.session_state.result is None:
    st.markdown("""
<div class="mc-header">
  <div class="mc-eyebrow">MITRE · Behavioral Health Modeling</div>
  <div class="mc-title">3QP — Lunar Crew Behavioral Twin</div>
  <div class="mc-sub">Configure a mission in the sidebar and click Run Simulation</div>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("### What this models")
        st.markdown("""
A long-duration isolated mission crew. Each day runs a **6-layer causal pipeline**:

| Layer | What it computes |
|---|---|
| **Resource** | Coffee depletion, sleep quality, food variety, task load |
| **Perception** | How each agent perceives the resource environment |
| **Belief** | Per-agent world-model update (scarcity, fairness, mc support…) |
| **Internal State** | Morale, fatigue, stress, boredom, trust, frustration drift |
| **Action** | maintain / engage / support / escalate / withdraw |
| **Physics** | Crew strain, cohesion, monotony, TQ pressure (coupled ODEs) |

The **Third Quarter Phenomenon** — psychological deterioration at 50–75% mission elapsed —
emerges from the equations, not from any hard-coded schedule.

Task failures have full **causal attribution**: sleep → circadian drift → impairment channel →
weakest-link agent → fail probability → outcome.
""")

    with col2:
        st.markdown("### Crew presets")
        st.markdown("""
**`high_cohesion_team`**
Low neuroticism, high agreeableness. Resilient under prolonged stress.

**`fragile_team`**
High neuroticism, low agreeableness. Deteriorates rapidly in TQ window.

**`extroverted_explorers`**
High extraversion and openness. Strong early performance, novelty-hungry.
""")
        st.markdown("### MC interventions")
        st.markdown("""
Add interventions before running to see counterfactual comparison.
`rest_authorization` — reduces workload 25%
`celebration` — boosts cohesion + MC support
`reassurance` — stabilises mission_viability belief
`peer_check` — prompts mutual support action
""")
    st.stop()


# ---------------------------------------------------------------------------
# Unpack results
# ---------------------------------------------------------------------------

result = st.session_state.result
run_cfg = st.session_state.run_cfg
result_bl = st.session_state.result_baseline

day_states = result.day_states
days = [d.day for d in day_states]
T = len(days)

agent_ids = sorted(day_states[0].internal_states.keys()) if day_states else []
crew_members = {m.name: m for m in result.config.crew_profile.members}

# Physics series
strains      = [d.core_strain      for d in day_states]
cohesions    = [d.core_cohesion    for d in day_states]
monotonies   = [d.core_monotony    for d in day_states]
tq_pressures = [d.core_tq_pressure for d in day_states]
workloads    = [d.physics_workload for d in day_states]
recoveries   = [d.physics_recovery for d in day_states]
social_cohesion_series = [
    (d.social_network or {}).get("global_cohesion", d.core_cohesion)
    for d in day_states
]

# TQ window (days)
tq_start = int(T * 0.50) + 1
tq_end   = int(T * 0.75) + 1

# Scheduled MC comm days
comm_days = sorted({_d for _, _d in run_cfg.get("interventions", [])})

# Mission KPIs
kpis = result.kpis or {}
mp = kpis.get("mission_performance", {})
pb = kpis.get("phase_breakdown", {})

# TQP emergence score
tqp_score = _tqp_emergence_score(day_states, T)

# Causal traces (all)
all_traces = _collect_causal_traces(day_states)

# Task outcomes
total_tasks     = 0
completed_tasks = 0
critical_fail   = 0
critical_total  = 0
for _ds in day_states:
    if _ds.task_outcomes:
        for _t in _ds.task_outcomes.get("task_results", []):
            total_tasks += 1
            if _t.get("outcome") == "completed":
                completed_tasks += 1
            if _t.get("criticality") == "high":
                critical_total += 1
                if _t.get("outcome") != "completed":
                    critical_fail += 1
completion_pct = completed_tasks / max(1, total_tasks) * 100
crit_completion = (critical_total - critical_fail) / max(1, critical_total) * 100

min_coh     = min(cohesions)
min_coh_day = days[cohesions.index(min_coh)]


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="mc-header">
  <div class="mc-eyebrow">MITRE · Behavioral Health Modeling · {run_cfg.get('crew_preset', '')} crew</div>
  <div class="mc-title">Mission: {run_cfg.get('mission_name', '').upper()}</div>
  <div class="mc-sub">
    {run_cfg.get('mission_days', T)}-day mission &nbsp;·&nbsp;
    {len(agent_ids)} crew members &nbsp;·&nbsp;
    {len(run_cfg.get('interventions', []))} MC intervention{'s' if len(run_cfg.get('interventions', [])) != 1 else ''}
    scheduled
    {'&nbsp;·&nbsp;<span style="color:#e8924a;font-weight:600;">⚡ Comparison mode active</span>'
     if result_bl else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# KPI strip
tqp_color = "error" if tqp_score > 0.5 else ("warning" if tqp_score > 0.2 else "green")
st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Critical Task Completion</div>
    <div class="kpi-value {'green' if crit_completion >= 85 else ('orange' if crit_completion >= 70 else 'red')}">{crit_completion:.0f}%</div>
    <div class="kpi-sub">{critical_fail} high-criticality failures</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">TQP Emergence Score</div>
    <div class="kpi-value {tqp_color}">{tqp_score:+.2f}</div>
    <div class="kpi-sub">TQ strain amplification vs early</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Peak Crew Strain</div>
    <div class="kpi-value red">{max(strains):.3f}</div>
    <div class="kpi-sub">Day {days[strains.index(max(strains))]}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Min Cohesion</div>
    <div class="kpi-value {'green' if min_coh > 0.6 else ('orange' if min_coh > 0.4 else 'red')}">{min_coh:.3f}</div>
    <div class="kpi-sub">Day {min_coh_day}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Causal Failures Traced</div>
    <div class="kpi-value blue">{len(all_traces)}</div>
    <div class="kpi-sub">full attribution chains</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Final Cohesion</div>
    <div class="kpi-value {'green' if cohesions[-1] > 0.7 else ('orange' if cohesions[-1] > 0.5 else 'red')}">{cohesions[-1]:.3f}</div>
    <div class="kpi-sub">vs {cohesions[0]:.3f} at start</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

TABS = ["Mission Overview", "Agent Deep-Dive", "Causal Forensics",
        "Social Network", "Tasks", "Resources", "Comparison"]
(tab_overview, tab_agent, tab_forensics,
 tab_social, tab_tasks, tab_res, tab_compare) = st.tabs(TABS)


###############################################################################
# TAB 1 — Mission Overview
###############################################################################

with tab_overview:
    st.markdown('<div class="section-label">3D Orbital Mission Explorer</div>',
                unsafe_allow_html=True)
    st.caption(
        "Rotate and zoom the scene to inspect system bodies. "
        "Click a planet (when click events are supported) or use the selector to drill into details."
    )

    if "orbital_day" not in st.session_state:
        st.session_state.orbital_day = min(max(tq_start, days[0]), days[-1])

    orbital_metrics = [
        {
            "key": "strain",
            "label": "Crew Strain",
            "series": strains,
            "color": _PALETTE["strain"],
            "radius": 1.25,
        },
        {
            "key": "cohesion",
            "label": "Crew Cohesion",
            "series": cohesions,
            "color": _PALETTE["cohesion"],
            "radius": 1.7,
        },
        {
            "key": "monotony",
            "label": "Monotony",
            "series": monotonies,
            "color": _PALETTE["monotony"],
            "radius": 2.15,
        },
        {
            "key": "tq_pressure",
            "label": "TQ Pressure",
            "series": tq_pressures,
            "color": _PALETTE["tq"],
            "radius": 2.55,
        },
        {
            "key": "social_cohesion",
            "label": "Social Cohesion",
            "series": social_cohesion_series,
            "color": "#8ed6f8",
            "radius": 2.95,
        },
        {
            "key": "recovery",
            "label": "Recovery Capacity",
            "series": recoveries,
            "color": "#74e4b5",
            "radius": 3.35,
        },
    ]

    metric_keys = [m["key"] for m in orbital_metrics]
    if "orbital_metric" not in st.session_state or st.session_state.orbital_metric not in metric_keys:
        st.session_state.orbital_metric = "cohesion"

    jump_targets = [("Day 1", days[0])]
    if comm_days:
        jump_targets.append(("MC Start", comm_days[0]))
    jump_targets.extend([
        ("TQ Start", tq_start),
        ("TQ End", tq_end),
        ("Final", days[-1]),
    ])

    jump_cols = st.columns(len(jump_targets))
    for col, (label, target_day) in zip(jump_cols, jump_targets):
        key_stub = label.lower().replace(" ", "_")
        if col.button(label, key=f"orbit_jump_{key_stub}", use_container_width=True):
            st.session_state.orbital_day = int(target_day)

    st.slider(
        "Mission day",
        min_value=days[0],
        max_value=days[-1],
        key="orbital_day",
    )

    selected_day = int(st.session_state.orbital_day)
    selected_idx = min(range(len(days)), key=lambda i: abs(days[i] - selected_day))
    selected_day = days[selected_idx]

    if "orbital_metric_picker" not in st.session_state:
        st.session_state.orbital_metric_picker = st.session_state.orbital_metric

    selected_metric_key = st.session_state.orbital_metric
    selected_metric_index = metric_keys.index(selected_metric_key)

    col_orbit, col_detail = st.columns([1.65, 1.0])

    with col_orbit:
        fig_orbit = go.Figure()

        ring_points = 96
        ring_angles = [2 * math.pi * i / ring_points for i in range(ring_points + 1)]
        for metric in orbital_metrics:
            ring_x = [metric["radius"] * math.cos(a) for a in ring_angles]
            ring_y = [metric["radius"] * math.sin(a) for a in ring_angles]
            ring_z = [0.0 for _ in ring_angles]
            fig_orbit.add_trace(go.Scatter3d(
                x=ring_x,
                y=ring_y,
                z=ring_z,
                mode="lines",
                line=dict(color="rgba(96, 137, 194, 0.34)", width=2),
                hoverinfo="skip",
                showlegend=False,
            ))

        fig_orbit.add_trace(go.Scatter3d(
            x=[0.0],
            y=[0.0],
            z=[0.0],
            mode="markers+text",
            marker=dict(size=16, color="#8ec7ff", symbol="diamond"),
            text=["Mission Core"],
            textposition="bottom center",
            textfont=dict(size=10, color="#dbe9ff"),
            hovertemplate="<b>Mission Core</b><extra></extra>",
            showlegend=False,
        ))

        orbit_phase = (selected_day / max(1, T)) * (2 * math.pi)
        body_x = []
        body_y = []
        body_z = []
        body_size = []
        body_color = []
        body_text = []
        body_custom = []
        for i, metric in enumerate(orbital_metrics):
            value = metric["series"][selected_idx]
            angle = orbit_phase * (0.7 + i * 0.13) + i * 1.32
            body_x.append(metric["radius"] * math.cos(angle))
            body_y.append(metric["radius"] * math.sin(angle))
            body_z.append((value - 0.5) * 2.8)
            body_size.append(12 + value * 22 + (8 if i == selected_metric_index else 0))
            body_color.append(metric["color"])
            body_text.append(metric["label"].split(" ")[0])
            body_custom.append([metric["key"], metric["label"], value])

        fig_orbit.add_trace(go.Scatter3d(
            x=body_x,
            y=body_y,
            z=body_z,
            mode="markers+text",
            marker=dict(
                size=body_size,
                color=body_color,
                opacity=0.96,
                line=dict(color="#f3f8ff", width=1.6),
            ),
            text=body_text,
            textposition="top center",
            textfont=dict(size=11, color="#dbe9ff"),
            customdata=body_custom,
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "Day " + str(selected_day) + " value: %{customdata[2]:.3f}<extra></extra>"
            ),
            showlegend=False,
        ))

        fig_orbit.update_layout(
            height=520,
            paper_bgcolor="#05080f",
            plot_bgcolor="#05080f",
            margin=dict(l=0, r=0, t=24, b=0),
            title=dict(
                text=f"Orbital State Map - Day {selected_day}",
                font=dict(family="Oxanium, Manrope, sans-serif", size=15, color="#dbe9ff"),
                x=0.02,
                xanchor="left",
            ),
            scene=dict(
                bgcolor="#05080f",
                xaxis=dict(
                    visible=False,
                    showbackground=True,
                    backgroundcolor="#05080f",
                    gridcolor="rgba(34, 55, 92, 0.45)",
                ),
                yaxis=dict(
                    visible=False,
                    showbackground=True,
                    backgroundcolor="#05080f",
                    gridcolor="rgba(34, 55, 92, 0.45)",
                ),
                zaxis=dict(
                    title=dict(text="Intensity", font=dict(size=10, color="#95b3da")),
                    tickfont=dict(size=9, color="#95b3da"),
                    range=[-1.6, 1.6],
                    showbackground=True,
                    backgroundcolor="#05080f",
                    gridcolor="rgba(34, 55, 92, 0.45)",
                    zerolinecolor="rgba(95, 135, 194, 0.62)",
                ),
                camera=dict(eye=dict(x=1.45, y=1.35, z=0.9)),
                aspectmode="cube",
                dragmode="orbit",
            ),
            clickmode="event+select",
        )

        selection_payload = _safe_plotly_chart(
            fig_orbit,
            key="orbital_scene",
            enable_selection=True,
        )
        clicked_idx = _extract_selected_point_index(selection_payload)
        if clicked_idx is not None and 0 <= clicked_idx < len(metric_keys):
            st.session_state.orbital_metric = metric_keys[clicked_idx]
            st.session_state.orbital_metric_picker = metric_keys[clicked_idx]
            selected_metric_key = metric_keys[clicked_idx]
            selected_metric_index = clicked_idx

        selected_metric_key = st.selectbox(
            "Selected body",
            metric_keys,
            format_func=lambda k: next(m["label"] for m in orbital_metrics if m["key"] == k),
            index=selected_metric_index,
            key="orbital_metric_picker",
        )
        st.session_state.orbital_metric = selected_metric_key

    with col_detail:
        selected_metric = next(m for m in orbital_metrics if m["key"] == selected_metric_key)
        sel_series = selected_metric["series"]
        sel_value = sel_series[selected_idx]
        prev_value = sel_series[max(0, selected_idx - 1)]
        delta = sel_value - prev_value

        favorable_if_up = selected_metric_key in {"cohesion", "social_cohesion", "recovery"}
        improving = (delta >= 0 and favorable_if_up) or (delta <= 0 and not favorable_if_up)
        if abs(delta) < 0.003:
            delta_color = _PALETTE["muted"]
        else:
            delta_color = _PALETTE["success"] if improving else _PALETTE["error"]

        phase_key = _phase_label(selected_day, T)
        phase_name = {
            "early": "Early Phase",
            "tq": "Third-Quarter Window",
            "late": "Late Phase",
        }[phase_key]

        chips = []
        for metric in orbital_metrics:
            chip_cls = "planet-chip planet-chip-active" if metric["key"] == selected_metric_key else "planet-chip"
            chips.append(
                f'<span class="{chip_cls}">{metric["label"]}: {metric["series"][selected_idx]:.3f}</span>'
            )

        st.markdown(
            f"""
<div class="orbit-detail-card">
  <div class="orbit-detail-title">{selected_metric['label']}</div>
  <div class="orbit-detail-value" style="color:{selected_metric['color']};">{sel_value:.3f}</div>
  <div class="orbit-meta">
    Day {selected_day} · {phase_name} · Daily delta
    <span style="color:{delta_color};font-weight:700;">{delta:+.3f}</span>
  </div>
  <div style="font-size:12px;color:#d4e4ff;line-height:1.6;">
    {_orbital_insight(selected_metric_key, sel_value, delta)}
  </div>
</div>
<div>{''.join(chips)}</div>
""",
            unsafe_allow_html=True,
        )

        fig_focus = go.Figure()
        fig_focus.add_trace(go.Scatter(
            x=days,
            y=sel_series,
            mode="lines",
            line=dict(color=selected_metric["color"], width=2.3),
            hovertemplate=f"{selected_metric['label']}: <b>%{{y:.4f}}</b><extra></extra>",
            showlegend=False,
        ))
        fig_focus.add_trace(go.Scatter(
            x=[selected_day],
            y=[sel_value],
            mode="markers",
            marker=dict(size=12, color="#f3f8ff", line=dict(color=selected_metric["color"], width=3)),
            hovertemplate="Day %{x}: <b>%{y:.4f}</b><extra></extra>",
            showlegend=False,
        ))
        _decorate(fig_focus, tq_start, tq_end, comm_days)
        fig_focus.update_layout(
            height=214,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(range=[0, 1.05]),
                margin=dict(l=40, r=10, t=8, b=30),
            ),
        )
        _safe_plotly_chart(fig_focus)

    # Physics 2×2
    fig_phys = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Crew Strain (S)", "Crew Cohesion (C)",
                        "Monotony (M)", "TQ Pressure (Q)"],
        shared_xaxes=True,
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    physics_traces = [
        (strains,       _PALETTE["strain"],   "Strain",      1, 1),
        (cohesions,     _PALETTE["cohesion"], "Cohesion",    1, 2),
        (monotonies,    _PALETTE["monotony"], "Monotony",    2, 1),
        (tq_pressures,  _PALETTE["tq"],       "TQ Pressure", 2, 2),
    ]
    for vals, color, name, row, col in physics_traces:
        fig_phys.add_trace(
            go.Scatter(x=days, y=vals, mode="lines", name=name,
                       line=dict(color=color, width=2.5), showlegend=False,
                       hovertemplate=f"{name}: <b>%{{y:.4f}}</b><extra></extra>"),
            row=row, col=col,
        )

    _decorate(fig_phys, tq_start, tq_end, comm_days,
              row_col_pairs=[(1, 1), (1, 2), (2, 1), (2, 2)])

    for r in [1, 2]:
        for c in [1, 2]:
            fig_phys.update_xaxes(title_text="Day" if r == 2 else "",
                                  row=r, col=c, **_axis())
            fig_phys.update_yaxes(row=r, col=c, **_axis())

    # Add TQ and MC annotations on main strain panel only
    if comm_days:
        fig_phys.add_annotation(
            xref="x", yref="paper",
            x=comm_days[0] + 2, y=0.97,
            text="MC →", showarrow=False,
            font=dict(size=10, color="rgba(74,144,217,0.7)"),
            xanchor="left", row=1, col=1,
        )

    fig_phys.update_layout(
        height=480,
        **_dl(margin=dict(l=52, r=24, t=45, b=20)),
    )
    st.plotly_chart(fig_phys, use_container_width=True)

    st.caption(
        "Yellow band = Third Quarter window (50–75% mission elapsed).  "
        "Blue dotted lines = scheduled MC communications.  "
        "Q = endogenous TQ pressure derived from M, S, C — not calendar-indexed."
    )

    # Physics inputs trace
    st.markdown('<div class="section-label">Physics Inputs — Resource & Action Aggregates</div>',
                unsafe_allow_html=True)

    fig_inputs = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Workload vs Recovery",
                        "Novelty & Success Events"],
        horizontal_spacing=0.12,
    )
    novelties  = [d.physics_novelty   for d in day_states]
    successes  = [d.physics_success   for d in day_states]

    # Left panel — area fill between recovery (floor) and workload (ceiling)
    # Red shaded gap = net stress burden
    fig_inputs.add_trace(
        go.Scatter(x=days, y=recoveries, mode="lines", name="Recovery",
                   line=dict(color=_PALETTE["success"], width=1.6),
                   fill="tozeroy", fillcolor="rgba(52,211,153,0.08)",
                   hovertemplate="Recovery: <b>%{y:.4f}</b><extra></extra>"),
        row=1, col=1,
    )
    fig_inputs.add_trace(
        go.Scatter(x=days, y=workloads, mode="lines", name="Workload",
                   line=dict(color=_PALETTE["error"], width=2.0),
                   fill="tonexty", fillcolor="rgba(248,113,113,0.18)",
                   hovertemplate="Workload: <b>%{y:.4f}</b><extra></extra>"),
        row=1, col=1,
    )

    # Right panel — binary signals as staggered impulse bars
    # Novelty: full-height accent bars; Success: shorter bars in front
    novelty_days = [d for d, v in zip(days, novelties) if v > 0]
    success_days = [d for d, v in zip(days, successes) if v > 0]
    fig_inputs.add_trace(
        go.Bar(x=novelty_days, y=[1.0] * len(novelty_days), name="Novelty",
               marker_color=_PALETTE["accent"], opacity=0.55, width=0.8,
               hovertemplate="Day %{x}: novel event<extra></extra>"),
        row=1, col=2,
    )
    fig_inputs.add_trace(
        go.Bar(x=success_days, y=[0.6] * len(success_days), name="Success",
               marker_color=_PALETTE["success"], opacity=0.85, width=0.8,
               hovertemplate="Day %{x}: task success<extra></extra>"),
        row=1, col=2,
    )

    _decorate(fig_inputs, tq_start, tq_end, comm_days, row_col_pairs=[(1, 1), (1, 2)])
    fig_inputs.update_layout(
        height=260,
        barmode="overlay",
        **_dl(margin=dict(l=52, r=24, t=40, b=36)),
    )
    fig_inputs.update_xaxes(**_axis(title_text="Day"))
    # Left: auto-scale so actual workload/recovery values fill the panel
    fig_inputs.update_yaxes(row=1, col=1, **_axis())
    # Right: fixed [0,1.1] is appropriate since signals are binary impulses
    fig_inputs.update_yaxes(row=1, col=2, **_axis(range=[0, 1.15], showticklabels=False))
    st.plotly_chart(fig_inputs, use_container_width=True)

    # KPI phase breakdown
    if pb:
        st.markdown('<div class="section-label">Critical Task Completion — Phase Breakdown</div>',
                    unsafe_allow_html=True)
        ph_early = pb.get("early_critical_completion", 0) * 100
        ph_tq    = pb.get("tq_critical_completion",    0) * 100
        ph_late  = pb.get("late_critical_completion",  0) * 100

        fig_phase = go.Figure()
        phases = ["Early (0–50%)", "TQ Window (50–75%)", "Late (75–100%)"]
        vals   = [ph_early, ph_tq, ph_late]
        colors = [
            "#5dbd5d" if v >= 85 else ("#e8924a" if v >= 70 else "#e05c5c")
            for v in vals
        ]
        fig_phase.add_trace(go.Bar(
            x=phases, y=vals,
            marker_color=colors,
            text=[f"{v:.1f}%" for v in vals],
            textposition="auto",
            textfont=dict(color="#e8edf8", size=13, family="sans-serif"),
            hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
        ))
        fig_phase.add_hrect(y0=85, y1=100,
                            fillcolor="rgba(93,189,93,0.05)", line_width=0)
        fig_phase.update_layout(
            height=220,
            **_dl(margin=dict(l=52, r=24, t=20, b=36), showlegend=False),
        )
        fig_phase.update_yaxes(**_axis(range=[0, 105], title_text="Completion %",
                                       ticksuffix="%"))
        fig_phase.update_xaxes(**_axis())
        st.plotly_chart(fig_phase, use_container_width=True)

        # TQP Emergence Score callout
        delta_tq = ph_tq - ph_early
        st.markdown(f"""
<div style="background:#0e1525;border:1px solid #1e2d4a;border-radius:8px;
     padding:16px 20px;margin:12px 0;">
  <div style="font-size:10px;font-weight:600;letter-spacing:0.10em;
       text-transform:uppercase;color:#5b7099;margin-bottom:8px;">
    TQP Emergence Analysis
  </div>
  <div style="font-size:13px;color:#9ab0d4;line-height:1.7;">
    TQ window critical task completion was
    <span style="color:{'#e05c5c' if delta_tq < -5 else '#e8924a' if delta_tq < 0 else '#5dbd5d'};
    font-weight:600;">{delta_tq:+.1f}%</span>
    vs early phase.
    TQP emergence score: <span style="color:#e8924a;font-weight:600;">{tqp_score:+.2f}</span>
    ({['mild', 'moderate', 'strong'][min(2, int(abs(tqp_score) / 0.2))]} TQP signature).
    <br>
    {f'Final cohesion recovered to <span style="color:#5dbd5d;font-weight:600;">{cohesions[-1]:.3f}</span>, suggesting late-mission stabilisation.' if cohesions[-1] > cohesions[tq_end] else f'Cohesion did not recover post-TQ window (<span style="color:#e05c5c;font-weight:600;">{cohesions[-1]:.3f}</span>).'}
  </div>
</div>
""", unsafe_allow_html=True)

    # Mission story
    story_path = Path("output") / run_cfg.get("mission_name", "") / "mission_story.json"
    if story_path.exists():
        with open(story_path, encoding="utf-8") as _f:
            story = json.load(_f)
        st.markdown('<div class="section-label">Mission Narrative</div>',
                    unsafe_allow_html=True)
        sentences = story.get("summary_sentences", [])
        if sentences:
            bullets = "".join(
                f'<div class="story-sentence">{s}</div>' for s in sentences
            )
            story_html = f'<div class="story-panel">{bullets}</div>'
            st.markdown(story_html, unsafe_allow_html=True)

        phase_stories = story.get("phase_stories", {})
        if phase_stories:
            st.markdown('<div class="section-label">Representative Failure by Phase</div>',
                        unsafe_allow_html=True)
            for phase_key, phase_info in phase_stories.items():
                if not phase_info:
                    continue
                phase_cls = f"phase-{phase_key}"
                phase_name = {"early": "Early", "tq": "TQ Window", "late": "Late"}[phase_key]
                sent = phase_info.get("sentence", "")
                day_n = phase_info.get("day", "?")
                task = phase_info.get("task_id", "?")
                st.markdown(
                    f'<div style="font-size:12px;color:#9ab0d4;padding:6px 0;">'
                    f'<span class="phase-tag {phase_cls}">{phase_name}</span>'
                    f'<span style="color:#5b7099;">Day {day_n} · {task}</span>'
                    f'<br><span style="padding-left:56px;">{sent}</span></div>',
                    unsafe_allow_html=True,
                )


###############################################################################
# TAB 2 — Agent Deep-Dive
###############################################################################

with tab_agent:
    agent_sel = st.selectbox(
        "Select crew member",
        agent_ids,
        key="agent_sel",
    )

    member = crew_members.get(agent_sel)
    col_radar, col_bio = st.columns([1, 2])

    # Big Five radar
    with col_radar:
        if member:
            p = member.personality
            big5_labels = ["Openness", "Conscientiousness", "Extraversion",
                           "Agreeableness", "Neuroticism"]
            big5_vals = [p.openness, p.conscientiousness, p.extraversion,
                         p.agreeableness, p.neuroticism]
            big5_vals_closed = big5_vals + [big5_vals[0]]  # close the polygon
            big5_labels_closed = big5_labels + [big5_labels[0]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=big5_vals_closed,
                theta=big5_labels_closed,
                fill="toself",
                fillcolor="rgba(74,144,217,0.15)",
                line=dict(color="#4a90d9", width=2),
                name="Big Five",
                hovertemplate="<b>%{theta}</b>: %{r:.2f}<extra></extra>",
            ))
            fig_radar.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True, range=[0, 1],
                        gridcolor="#1a2740", linecolor="#1a2740",
                        tickfont=dict(size=9, color="#5b7099"),
                    ),
                    angularaxis=dict(
                        gridcolor="#1a2740", linecolor="#1a2740",
                        tickfont=dict(size=10, color="#9ab0d4"),
                    ),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#7a95b8"),
                margin=dict(l=30, r=30, t=50, b=30),
                height=300,
                title=dict(text=f"Big Five — {agent_sel.split()[0]}",
                           font=dict(size=12, color="#9ab0d4"), x=0.5),
                showlegend=False,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    with col_bio:
        if member:
            p = member.personality
            st.markdown(f"""
<div style="background:#0e1525;border:1px solid #1e2d4a;border-radius:8px;
     padding:16px 20px;margin-top:8px;">
  <div style="font-size:14px;font-weight:600;color:#e8edf8;margin-bottom:8px;">{agent_sel}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;color:#9ab0d4;">
    <div><span style="color:#5b7099;">Openness</span> &nbsp; <b>{p.openness:.2f}</b></div>
    <div><span style="color:#5b7099;">Conscient.</span> &nbsp; <b>{p.conscientiousness:.2f}</b></div>
    <div><span style="color:#5b7099;">Extraversion</span> &nbsp; <b>{p.extraversion:.2f}</b></div>
    <div><span style="color:#5b7099;">Agreeableness</span> &nbsp; <b>{p.agreeableness:.2f}</b></div>
    <div><span style="color:#5b7099;">Neuroticism</span> &nbsp;
      <b style="color:{'#e05c5c' if p.neuroticism > 0.6 else '#e8924a' if p.neuroticism > 0.4 else '#5dbd5d'};">{p.neuroticism:.2f}</b>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # Internal state chart
    st.markdown('<div class="section-label">Internal State Trajectory</div>',
                unsafe_allow_html=True)

    state_metrics = {
        "morale":                ("Morale",               _PALETTE["success"]),
        "fatigue":               ("Fatigue",              _PALETTE["error"]),
        "stress":                ("Stress",               _PALETTE["warning"]),
        "boredom":               ("Boredom",              _PALETTE["muted"]),
        "trust_in_crew":         ("Trust in Crew",        _PALETTE["accent"]),
        "future_outlook":        ("Future Outlook",       "#a876d9"),
        "frustration_scarcity":  ("Frustration/Scarcity", "#e8924a"),
        "cooperation_threshold": ("Cooperation Threshold","#1abc9c"),
    }

    selected_metrics = st.multiselect(
        "Metrics to display",
        list(state_metrics.keys()),
        default=["morale", "fatigue", "stress", "trust_in_crew",
                 "boredom", "frustration_scarcity"],
        format_func=lambda k: state_metrics[k][0],
        key="state_metrics_sel",
    )

    if selected_metrics:
        fig_state = go.Figure()
        for mkey in selected_metrics:
            label, color = state_metrics[mkey]
            vals = [d.internal_states.get(agent_sel, {}).get(mkey, 0) for d in day_states]
            fig_state.add_trace(go.Scatter(
                x=days, y=vals, mode="lines", name=label,
                line=dict(color=color, width=2),
                hovertemplate=f"{label}: <b>%{{y:.4f}}</b><extra></extra>",
            ))
        _decorate(fig_state, tq_start, tq_end, comm_days)
        fig_state.update_layout(
            height=340,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(range=[0, 1.05], title_text="Value [0–1]"),
                margin=dict(l=52, r=24, t=20, b=36),
            ),
        )
        st.plotly_chart(fig_state, use_container_width=True)

    # Belief state
    st.markdown('<div class="section-label">Belief State Trajectory</div>',
                unsafe_allow_html=True)

    belief_metrics = {
        "belief_crew_cohesion":           ("Belief: Crew Cohesion",    _PALETTE["success"]),
        "belief_mission_control_support": ("Belief: MC Support",       _PALETTE["accent"]),
        "belief_mission_viability":       ("Belief: Mission Viability","#a876d9"),
        "belief_coffee_scarcity":         ("Belief: Coffee Scarcity",  _PALETTE["error"]),
    }

    fig_belief = go.Figure()
    for bkey, (blabel, bcolor) in belief_metrics.items():
        vals = [d.belief_states.get(agent_sel, {}).get(bkey, 0) for d in day_states]
        if any(v != 0 for v in vals):
            fig_belief.add_trace(go.Scatter(
                x=days, y=vals, mode="lines", name=blabel,
                line=dict(color=bcolor, width=1.8),
                hovertemplate=f"{blabel}: <b>%{{y:.4f}}</b><extra></extra>",
            ))
    _decorate(fig_belief, tq_start, tq_end, comm_days)
    fig_belief.update_layout(
        height=300,
        **_dl(
            xaxis=_axis(title_text="Day"),
            yaxis=_axis(range=[0, 1.05], title_text="Belief [0–1]"),
            margin=dict(l=52, r=24, t=20, b=36),
        ),
    )
    st.plotly_chart(fig_belief, use_container_width=True)

    # Perception layer — how does this agent read the environment?
    st.markdown('<div class="section-label">Perception Layer — Agent\'s Read of Environment</div>',
                unsafe_allow_html=True)
    st.caption(
        "Perceptions are the agent's sensory model of the environment each day — "
        "distinct from both objective resource state and subjective beliefs. "
        "Divergence between agents on the same day reveals contested threat models."
    )

    perception_metrics = {
        "perceived_sleep_quality":        ("Sleep Quality",        _PALETTE["accent"]),
        "perceived_coffee_scarcity":      ("Coffee Scarcity",      _PALETTE["monotony"]),
        "perceived_food_quality":         ("Food Quality",         _PALETTE["success"]),
        "perceived_distribution_fairness":("Distribution Fairness","#1abc9c"),
        "perceived_comms_reliability":    ("Comms Reliability",    "#a876d9"),
        "perceived_mission_support":      ("Mission Support",      _PALETTE["muted"]),
        "perceived_social_tension":       ("Social Tension",       _PALETTE["error"]),
    }

    sel_perc = st.multiselect(
        "Perceptions to display",
        list(perception_metrics.keys()),
        default=["perceived_sleep_quality", "perceived_coffee_scarcity",
                 "perceived_social_tension", "perceived_mission_support"],
        format_func=lambda k: perception_metrics[k][0],
        key="perc_metrics_sel",
    )

    if sel_perc:
        fig_perc = go.Figure()
        for pkey in sel_perc:
            plabel, pcolor = perception_metrics[pkey]
            vals = [d.perceived_states.get(agent_sel, {}).get(pkey, 0)
                    for d in day_states]
            if any(v != 0 for v in vals):
                fig_perc.add_trace(go.Scatter(
                    x=days, y=vals, mode="lines", name=plabel,
                    line=dict(color=pcolor, width=1.8),
                    hovertemplate=f"{plabel}: <b>%{{y:.4f}}</b><extra></extra>",
                ))
        _decorate(fig_perc, tq_start, tq_end, comm_days)
        fig_perc.update_layout(
            height=300,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(range=[0, 1.05], title_text="Perception [0–1]"),
                margin=dict(l=52, r=24, t=20, b=36),
            ),
        )
        st.plotly_chart(fig_perc, use_container_width=True)

    # Cross-agent perception divergence for one field
    st.markdown('<div class="section-label">Perception Divergence — All Agents on One Field</div>',
                unsafe_allow_html=True)
    div_field = st.selectbox(
        "Field to compare across crew",
        list(perception_metrics.keys()),
        format_func=lambda k: perception_metrics[k][0],
        index=0,
        key="div_field_sel",
    )
    fig_div = go.Figure()
    for i, aid in enumerate(agent_ids):
        dvals = [d.perceived_states.get(aid, {}).get(div_field, 0)
                 for d in day_states]
        if any(v != 0 for v in dvals):
            fig_div.add_trace(go.Scatter(
                x=days, y=dvals, mode="lines",
                name=aid.split()[0],
                line=dict(color=_AGENT_COLORS[i % len(_AGENT_COLORS)], width=1.8),
                hovertemplate=f"{aid.split()[0]}: <b>%{{y:.4f}}</b><extra></extra>",
            ))
    _decorate(fig_div, tq_start, tq_end, comm_days)
    fig_div.update_layout(
        height=250,
        **_dl(
            xaxis=_axis(title_text="Day"),
            yaxis=_axis(range=[0, 1.05],
                        title_text=perception_metrics[div_field][0]),
            margin=dict(l=52, r=24, t=20, b=36),
        ),
    )
    st.plotly_chart(fig_div, use_container_width=True)
    st.caption(
        "Spread between agents on the same day = contested threat model. "
        "Widest divergence during TQ window often precedes coordination failures."
    )

    # Action distribution
    st.markdown('<div class="section-label">Action Distribution</div>',
                unsafe_allow_html=True)

    action_counts: dict = {}
    action_by_day: list = []
    for _ds in day_states:
        act = _ds.crew_actions.get(agent_sel, {}).get("action_type", "maintain")
        action_counts[act] = action_counts.get(act, 0) + 1
        action_by_day.append(act)

    action_colors = {
        "maintain":  _PALETTE["accent"],
        "engage":    _PALETTE["success"],
        "support":   "#1abc9c",
        "escalate":  _PALETTE["warning"],
        "withdraw":  _PALETTE["error"],
    }

    col_pie, col_timeline = st.columns([1, 2])
    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=list(action_counts.keys()),
            values=list(action_counts.values()),
            marker_colors=[action_colors.get(k, "#5b7099") for k in action_counts],
            hole=0.5,
            textfont=dict(size=11, color="#e8edf8"),
            hovertemplate="%{label}: <b>%{value} days</b> (%{percent})<extra></extra>",
        ))
        fig_pie.update_layout(
            height=250,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#7a95b8"),
            legend=dict(font=dict(size=10, color="#9ab0d4"), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=10, r=10, t=20, b=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_timeline:
        action_vals = {"maintain": 0, "engage": 1, "support": 2, "escalate": 3, "withdraw": 4}
        action_num = [action_vals.get(a, 0) for a in action_by_day]
        fig_act = go.Figure(go.Scatter(
            x=days, y=action_num, mode="markers",
            marker=dict(
                color=[action_colors.get(a, "#5b7099") for a in action_by_day],
                size=5, symbol="circle",
            ),
            hovertemplate=[
                f"Day {d}: <b>{a}</b><extra></extra>"
                for d, a in zip(days, action_by_day)
            ],
        ))
        _decorate(fig_act, tq_start, tq_end, comm_days)
        fig_act.update_layout(
            height=250,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=dict(
                    tickmode="array",
                    tickvals=[0, 1, 2, 3, 4],
                    ticktext=["maintain", "engage", "support", "escalate", "withdraw"],
                    gridcolor="#1a2740", zerolinecolor="#1a2740",
                    tickcolor="#1a2740", linecolor="#1a2740",
                ),
                margin=dict(l=100, r=24, t=20, b=36),
                showlegend=False,
            ),
        )
        st.plotly_chart(fig_act, use_container_width=True)

    # Per-agent impairment vs crew average
    st.markdown('<div class="section-label">Impairment Index — Agent vs Crew Average</div>',
                unsafe_allow_html=True)

    FATIGUE_W = 0.6
    STRESS_W  = 0.4
    agent_imp = [
        d.internal_states.get(agent_sel, {}).get("fatigue", 0) * FATIGUE_W
        + d.internal_states.get(agent_sel, {}).get("stress",  0) * STRESS_W
        for d in day_states
    ]
    crew_imp = [
        sum(
            d.internal_states.get(aid, {}).get("fatigue", 0) * FATIGUE_W
            + d.internal_states.get(aid, {}).get("stress",  0) * STRESS_W
            for aid in agent_ids
        ) / max(1, len(agent_ids))
        for d in day_states
    ]

    fig_imp = go.Figure()
    fig_imp.add_trace(go.Scatter(
        x=days, y=crew_imp, mode="lines", name="Crew Avg",
        line=dict(color=_PALETTE["muted"], width=1.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(91,112,153,0.08)",
        hovertemplate="Crew avg: <b>%{y:.4f}</b><extra></extra>",
    ))
    fig_imp.add_trace(go.Scatter(
        x=days, y=agent_imp, mode="lines",
        name=agent_sel.split()[0],
        line=dict(color=_PALETTE["error"], width=2.5),
        hovertemplate=f"{agent_sel.split()[0]}: <b>%{{y:.4f}}</b><extra></extra>",
    ))
    _decorate(fig_imp, tq_start, tq_end, comm_days)
    fig_imp.update_layout(
        height=240,
        **_dl(
            xaxis=_axis(title_text="Day"),
            yaxis=_axis(range=[0, 1.05], title_text="Impairment [0–1]"),
            margin=dict(l=52, r=24, t=20, b=36),
        ),
    )
    st.plotly_chart(fig_imp, use_container_width=True)


###############################################################################
# TAB 3 — Causal Forensics
###############################################################################

with tab_forensics:
    if not all_traces:
        st.info("No causal traces recorded in this run.")
    else:
        # Sort by impact: high criticality + error outcome first
        crit_weight = {"high": 3.0, "medium": 2.0, "low": 1.0}
        outc_weight = {"error": 1.5, "skipped": 1.2, "delayed": 1.0}

        sorted_traces = sorted(
            all_traces,
            key=lambda x: (
                crit_weight.get(x[1].get("criticality", "low"), 1.0)
                * outc_weight.get(x[1].get("outcome", "delayed"), 1.0)
                * x[1].get("chain", {}).get("fail_prob", 0)
            ),
            reverse=True,
        )

        # Failure attribution chart — impairment channel by phase
        st.markdown('<div class="section-label">Failure Attribution by Channel</div>',
                    unsafe_allow_html=True)

        channel_colors = {
            "attention":     _PALETTE["warning"],
            "coordination":  _PALETTE["error"],
            "planning":      "#a876d9",
            "persistence":   _PALETTE["accent"],
        }
        channel_by_day: dict = {}
        for day_n, tr in all_traces:
            ch = tr.get("chain", {}).get("impairment_channel", "unknown")
            if day_n not in channel_by_day:
                channel_by_day[day_n] = {}
            channel_by_day[day_n][ch] = channel_by_day[day_n].get(ch, 0) + 1

        all_channels = sorted({
            tr.get("chain", {}).get("impairment_channel", "unknown")
            for _, tr in all_traces
        })

        fig_attr = go.Figure()
        for ch in all_channels:
            y_vals = [channel_by_day.get(d, {}).get(ch, 0) for d in days]
            fig_attr.add_trace(go.Bar(
                x=days, y=y_vals, name=ch,
                marker_color=channel_colors.get(ch, _PALETTE["muted"]),
                opacity=0.85,
                hovertemplate=f"{ch}: <b>%{{y}}</b> failures on day %{{x}}<extra></extra>",
            ))

        _decorate(fig_attr, tq_start, tq_end, comm_days)
        fig_attr.update_layout(
            barmode="stack",
            height=240,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(title_text="Failure count"),
                margin=dict(l=52, r=24, t=20, b=36),
                legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)",
                            font=dict(size=10, color="#9ab0d4")),
            ),
        )
        st.plotly_chart(fig_attr, use_container_width=True)
        st.caption(
            "Stacked bars show failure counts per impairment channel per day.  "
            "Coordination failures amplify in TQ window via weakest-link mechanism."
        )

        # Phase-level failure rate
        st.markdown('<div class="section-label">Failure Rate by Mission Phase</div>',
                    unsafe_allow_html=True)

        phase_labels = ["Early (0–50%)", "TQ Window (50–75%)", "Late (75–100%)"]
        phase_ranges = [(1, tq_start - 1), (tq_start, tq_end - 1), (tq_end, days[-1])]

        for ch in all_channels:
            ch_rates = []
            for d_start, d_end in phase_ranges:
                n = sum(channel_by_day.get(d, {}).get(ch, 0) for d in range(d_start, d_end + 1))
                n_days = max(1, d_end - d_start + 1)
                ch_rates.append(n / n_days)

        # Per-channel phase bars
        fig_phase_ch = go.Figure()
        for ch in all_channels:
            ch_rates = []
            for d_start, d_end in phase_ranges:
                n = sum(channel_by_day.get(d, {}).get(ch, 0) for d in range(d_start, d_end + 1))
                n_days = max(1, d_end - d_start + 1)
                ch_rates.append(n / n_days)
            fig_phase_ch.add_trace(go.Bar(
                x=phase_labels, y=ch_rates, name=ch,
                marker_color=channel_colors.get(ch, _PALETTE["muted"]),
                hovertemplate=f"{ch}: <b>%{{y:.2f}}</b> failures/day<extra></extra>",
            ))

        fig_phase_ch.update_layout(
            barmode="group",
            height=240,
            **_dl(
                xaxis=_axis(),
                yaxis=_axis(title_text="Failures per day"),
                margin=dict(l=52, r=24, t=20, b=36),
                legend=dict(orientation="h", y=1.15, bgcolor="rgba(0,0,0,0)",
                            font=dict(size=10, color="#9ab0d4")),
            ),
        )
        st.plotly_chart(fig_phase_ch, use_container_width=True)

        # Individual trace explorer
        st.markdown('<div class="section-label">Causal Trace Explorer — Click to drill down</div>',
                    unsafe_allow_html=True)

        max_traces = min(len(sorted_traces), 80)
        st.caption(f"Showing top {max_traces} failures by impact score (criticality × outcome weight × fail_prob)")

        for i, (day_n, tr) in enumerate(sorted_traces[:max_traces]):
            chain     = tr.get("chain", {})
            crit      = tr.get("criticality", "low")
            outcome   = tr.get("outcome", "?")
            task_id   = tr.get("task_id", "?")
            fail_prob = chain.get("fail_prob", 0)
            channel   = chain.get("impairment_channel", "?")
            wl_agent  = chain.get("weakest_link_agent", None)
            dep_pen   = chain.get("dependency_penalty", 0)
            upstream  = chain.get("upstream_failed", [])
            phase_tag = _phase_label(day_n, T)
            phase_cls = f"phase-{phase_tag}"
            phase_str = {"early": "Early", "tq": "TQ Window", "late": "Late"}[phase_tag]

            crit_cls = f"badge-{crit}"
            outcls = f"badge-error" if outcome == "error" else f"badge-skip" if outcome == "skipped" else "badge-delay"

            header_html = (
                f'<span class="phase-tag {phase_cls}">{phase_str}</span>'
                f'<span class="badge {crit_cls}">{crit.upper()}</span>'
                f'<span class="badge {outcls}">{outcome.upper()}</span>'
                f'<b style="color:#e8edf8;">{task_id}</b>'
                f'<span style="color:#5b7099;font-size:11px;margin-left:12px;">'
                f'Day {day_n} &nbsp;·&nbsp; fail_prob={fail_prob:.3f}'
                f'</span>'
            )

            with st.expander(f"Day {day_n:3d} | {crit.upper()} | {outcome.upper()} | {task_id}"):
                st.markdown(header_html, unsafe_allow_html=True)

                # Causal chain display
                sleep_q    = chain.get("sleep_quality", 0.0)
                circ_d     = chain.get("circadian_drift", 0.0)
                driver_v   = chain.get("driver_value", 0.0)
                max_imp    = chain.get("max_agent_impairment", None)

                chain_line = (
                    f'<span style="color:#5b7099;">sleep_quality</span>'
                    f'<span class="causal-value">&nbsp;{sleep_q:.3f}&nbsp;</span>'
                    f'<span class="causal-arrow">→</span>'
                    f'<span style="color:#5b7099;">circadian_drift</span>'
                    f'<span class="causal-value">&nbsp;{circ_d:.4f}&nbsp;</span>'
                    f'<span class="causal-arrow">→</span>'
                    f'<span style="color:#e8924a;font-weight:600;">{channel}</span>'
                    f'<span class="causal-arrow">→</span>'
                    f'<span style="color:#5b7099;">driver_value</span>'
                    f'<span class="causal-value">&nbsp;{driver_v:.4f}&nbsp;</span>'
                    f'<span class="causal-arrow">→</span>'
                    f'<span style="color:#e05c5c;font-weight:700;">fail_prob={fail_prob:.3f}</span>'
                )

                st.markdown(f'<div class="causal-chain">{chain_line}</div>',
                            unsafe_allow_html=True)

                if wl_agent:
                    wl_imp = max_imp if max_imp is not None else "?"
                    wl_imp_str = f"{wl_imp:.4f}" if isinstance(wl_imp, float) else str(wl_imp)
                    st.markdown(
                        f'<div style="font-size:11px;color:#9ab0d4;margin-top:6px;">'
                        f'Weakest link: <b style="color:#e05c5c;">{wl_agent}</b>'
                        f' (agent impairment={wl_imp_str})</div>',
                        unsafe_allow_html=True,
                    )

                if upstream:
                    st.markdown(
                        f'<div style="font-size:11px;color:#9ab0d4;margin-top:4px;">'
                        f'Dependency cascade: {" → ".join(upstream)} '
                        f'(<span style="color:#e8924a;">+{dep_pen:.3f} penalty</span>)</div>',
                        unsafe_allow_html=True,
                    )


###############################################################################
# TAB 4 — Social Network
###############################################################################

with tab_social:
    sn_data = [d.social_network for d in day_states if d.social_network is not None]

    if not sn_data:
        st.info("No social network data recorded in this run.")
    else:
        # Time-series of network metrics
        st.markdown('<div class="section-label">Social Network Metrics Over Time</div>',
                    unsafe_allow_html=True)

        sn_days     = [d.day for d in day_states if d.social_network is not None]
        cohesion_sn = [s.get("global_cohesion",      0) for s in sn_data]
        frag_idx    = [s.get("fragmentation_index",   0) for s in sn_data]
        clustering  = [s.get("clustering_coefficient",0) for s in sn_data]
        clique_cnt  = [s.get("clique_count",          0) for s in sn_data]

        fig_sn = make_subplots(
            rows=2, cols=2,
            subplot_titles=["Graph Cohesion", "Fragmentation Index",
                            "Clustering Coefficient", "Clique Count"],
            shared_xaxes=True,
            vertical_spacing=0.14,
            horizontal_spacing=0.10,
        )
        sn_traces = [
            (cohesion_sn, _PALETTE["success"],  "Graph Cohesion",       1, 1),
            (frag_idx,    _PALETTE["error"],     "Fragmentation",        1, 2),
            (clustering,  _PALETTE["accent"],    "Clustering Coeff",     2, 1),
            (clique_cnt,  _PALETTE["monotony"],  "Clique Count",         2, 2),
        ]
        for vals, color, name, row, col in sn_traces:
            fig_sn.add_trace(
                go.Scatter(x=sn_days, y=vals, mode="lines", name=name,
                           line=dict(color=color, width=2.5), showlegend=False,
                           hovertemplate=f"{name}: <b>%{{y:.4f}}</b><extra></extra>"),
                row=row, col=col,
            )
        _decorate(fig_sn, tq_start, tq_end, comm_days,
                  row_col_pairs=[(1, 1), (1, 2), (2, 1), (2, 2)])
        for r in [1, 2]:
            for c in [1, 2]:
                fig_sn.update_xaxes(title_text="Day" if r == 2 else "",
                                    row=r, col=c, **_axis())
                fig_sn.update_yaxes(row=r, col=c, **_axis())
        fig_sn.update_layout(
            height=460,
            **_dl(margin=dict(l=52, r=24, t=45, b=20)),
        )
        st.plotly_chart(fig_sn, use_container_width=True)

        # Network graph visualization
        st.markdown('<div class="section-label">Network Graph — Agent Trust & Morale</div>',
                    unsafe_allow_html=True)

        day_for_net = st.slider(
            "Mission Day",
            min_value=days[0], max_value=days[-1],
            value=min(tq_start + 10, days[-1]),
            key="net_day",
        )
        day_idx_net = min(range(len(days)), key=lambda i: abs(days[i] - day_for_net))
        ds_net = day_states[day_idx_net]

        # Node positions — equidistant circle
        n_agents = len(agent_ids)
        angles = [2 * math.pi * i / n_agents for i in range(n_agents)]
        nx_pos = {aid: (math.cos(a), math.sin(a)) for aid, a in zip(agent_ids, angles)}

        # Edge weights from trust between all pairs (use social_network edge_weights if available)
        sn_snap = ds_net.social_network or {}
        edge_weights_raw = sn_snap.get("edge_weights", {})

        fig_net = go.Figure()

        # Draw edges
        for i, a in enumerate(agent_ids):
            for b in agent_ids[i + 1:]:
                key1 = f"{a}|{b}"
                key2 = f"{b}|{a}"
                w = edge_weights_raw.get(key1, edge_weights_raw.get(key2, None))
                if w is None:
                    # Fall back to average trust of the two agents
                    ta = ds_net.internal_states.get(a, {}).get("trust_in_crew", 0.5)
                    tb = ds_net.internal_states.get(b, {}).get("trust_in_crew", 0.5)
                    w = (ta + tb) / 2

                x0, y0 = nx_pos[a]
                x1, y1 = nx_pos[b]
                edge_opacity = max(0.1, min(0.9, w))
                edge_width   = max(0.5, w * 5)
                edge_color = (
                    f"rgba(93,189,93,{edge_opacity:.2f})" if w > 0.6
                    else f"rgba(232,146,74,{edge_opacity:.2f})" if w > 0.35
                    else f"rgba(224,92,92,{edge_opacity:.2f})"
                )
                fig_net.add_trace(go.Scatter(
                    x=[x0, x1, None], y=[y0, y1, None],
                    mode="lines",
                    line=dict(color=edge_color, width=edge_width),
                    hoverinfo="skip",
                    showlegend=False,
                ))

        # Draw nodes
        node_x  = [nx_pos[a][0] for a in agent_ids]
        node_y  = [nx_pos[a][1] for a in agent_ids]
        morale_vals = [ds_net.internal_states.get(a, {}).get("morale", 0.5) for a in agent_ids]
        coop_vals   = [ds_net.internal_states.get(a, {}).get("cooperation_threshold", 0.5)
                       for a in agent_ids]

        fig_net.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            marker=dict(
                color=morale_vals,
                colorscale=[[0, "#e05c5c"], [0.5, "#e8924a"], [1, "#5dbd5d"]],
                cmin=0, cmax=1,
                size=[20 + c * 30 for c in coop_vals],
                line=dict(width=2, color="#1e2d4a"),
                colorbar=dict(
                    title=dict(text="Morale", font=dict(size=10, color="#5b7099")),
                    tickfont=dict(size=9, color="#5b7099"),
                    bgcolor="rgba(0,0,0,0)",
                    bordercolor="#1e2d4a",
                    len=0.5, x=1.02,
                ),
            ),
            text=[a.split()[0] for a in agent_ids],
            textposition="top center",
            textfont=dict(size=11, color="#e8edf8"),
            customdata=list(zip(agent_ids, morale_vals, coop_vals)),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Morale: %{customdata[1]:.3f}<br>"
                "Coop threshold: %{customdata[2]:.3f}<extra></extra>"
            ),
            showlegend=False,
        ))

        phase = _phase_label(day_for_net, T)
        phase_color = {"early": "#4a90d9", "tq": "#e8924a", "late": "#a876d9"}[phase]
        phase_name  = {"early": "Early Phase", "tq": "TQ Window", "late": "Late Phase"}[phase]

        fig_net.update_layout(
            title=dict(
                text=(f"Social Network — Day {day_for_net}"
                      f" <span style='color:{phase_color};font-size:12px;'>[{phase_name}]</span>"),
                font=dict(size=13, color="#9ab0d4"),
            ),
            height=460,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,21,37,1)",
            font=dict(color="#7a95b8"),
            xaxis=dict(visible=False, range=[-1.5, 1.6]),
            yaxis=dict(visible=False, range=[-1.4, 1.5], scaleanchor="x"),
            margin=dict(l=20, r=80, t=50, b=20),
            annotations=[
                dict(
                    x=0, y=-1.35,
                    text=(
                        f"Graph cohesion: <b>{sn_snap.get('global_cohesion', 0):.3f}</b> &nbsp;|&nbsp;"
                        f"Fragmentation: <b>{sn_snap.get('fragmentation_index', 0):.3f}</b> &nbsp;|&nbsp;"
                        f"Cliques: <b>{sn_snap.get('clique_count', 0)}</b>"
                    ),
                    showarrow=False,
                    font=dict(size=11, color="#5b7099"),
                    xanchor="center",
                )
            ],
        )
        st.plotly_chart(fig_net, use_container_width=True)
        st.caption(
            "Node color = morale (red→green).  Node size = cooperation threshold.  "
            "Edge color/width = trust weight (green=strong, red=weak).  "
            "Move the slider to watch the network evolve over the mission."
        )

        # All-agents trust divergence
        st.markdown('<div class="section-label">Per-Agent Trust Trajectory</div>',
                    unsafe_allow_html=True)
        fig_trust = go.Figure()
        for i, aid in enumerate(agent_ids):
            trust_vals = [d.internal_states.get(aid, {}).get("trust_in_crew", 0.5)
                          for d in day_states]
            fig_trust.add_trace(go.Scatter(
                x=days, y=trust_vals, mode="lines",
                name=aid.split()[0],
                line=dict(color=_AGENT_COLORS[i % len(_AGENT_COLORS)], width=2),
                hovertemplate=f"{aid.split()[0]}: <b>%{{y:.4f}}</b><extra></extra>",
            ))
        _decorate(fig_trust, tq_start, tq_end, comm_days)
        fig_trust.update_layout(
            height=260,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(range=[0, 1.05], title_text="Trust in Crew"),
                margin=dict(l=52, r=24, t=20, b=36),
            ),
        )
        st.plotly_chart(fig_trust, use_container_width=True)


###############################################################################
# TAB 5 — Tasks
###############################################################################

with tab_tasks:
    task_ids_ordered = []
    task_criticality = {}
    seen = set()
    for _ds in day_states:
        if _ds.task_outcomes:
            for _t in _ds.task_outcomes.get("task_results", []):
                tid = _t["task_id"]
                if tid not in seen:
                    task_ids_ordered.append(tid)
                    task_criticality[tid] = _t.get("criticality", "low")
                    seen.add(tid)

    if task_ids_ordered:
        outcome_num = {"completed": 0, "delayed": 1, "error": 2, "skipped": 3}
        colorscale = [
            [0.00, "#2ecc71"], [0.24, "#2ecc71"],
            [0.25, "#f39c12"], [0.49, "#f39c12"],
            [0.50, "#e74c3c"], [0.74, "#e74c3c"],
            [0.75, "#95a5a6"], [1.00, "#95a5a6"],
        ]

        outcome_lookup = {}
        for _ds in day_states:
            if _ds.task_outcomes:
                for _t in _ds.task_outcomes.get("task_results", []):
                    outcome_lookup[(_t["task_id"], _ds.day)] = outcome_num.get(_t["outcome"], -1)

        z = []
        for tid in task_ids_ordered:
            row = [outcome_lookup.get((tid, d), None) for d in days]
            z.append(row)

        # Criticality-prefixed y labels
        crit_prefix = {"high": "⬥ ", "medium": "◈ ", "low": "· "}
        y_labels = [
            crit_prefix.get(task_criticality.get(tid, "low"), "  ") + tid
            for tid in task_ids_ordered
        ]

        fig_heat = go.Figure(go.Heatmap(
            z=z, x=days, y=y_labels,
            colorscale=colorscale,
            zmin=0, zmax=3,
            showscale=False,
            hovertemplate="Day %{x}<br>%{y}<br>%{text}<extra></extra>",
            text=[[{0: "completed", 1: "delayed", 2: "error", 3: "skipped"}.get(v, "—")
                   for v in row] for row in z],
        ))

        _decorate(fig_heat, tq_start, tq_end, comm_days)
        fig_heat.update_layout(
            height=max(250, 38 * len(task_ids_ordered) + 80),
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(),
                margin=dict(t=20, b=20, l=220),
            ),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption(
            "⬥ = high criticality &nbsp; ◈ = medium &nbsp; · = low  |  "
            "Green = completed  Orange = delayed  Red = error  Gray = skipped"
        )

        # 7-day rolling failure rate
        st.markdown('<div class="section-label">Rolling Failure Rate (7-day window)</div>',
                    unsafe_allow_html=True)

        window = 7
        fail_rates = []
        fail_rates_crit = []
        for i, _ds in enumerate(day_states):
            ws = day_states[max(0, i - window + 1): i + 1]
            w_total = sum(len(s.task_outcomes.get("task_results", []))
                          for s in ws if s.task_outcomes)
            w_fail = sum(
                sum(1 for _t in s.task_outcomes.get("task_results", [])
                    if _t.get("outcome") != "completed")
                for s in ws if s.task_outcomes
            )
            w_crit_total = sum(
                sum(1 for _t in s.task_outcomes.get("task_results", [])
                    if _t.get("criticality") == "high")
                for s in ws if s.task_outcomes
            )
            w_crit_fail = sum(
                sum(1 for _t in s.task_outcomes.get("task_results", [])
                    if _t.get("criticality") == "high" and _t.get("outcome") != "completed")
                for s in ws if s.task_outcomes
            )
            fail_rates.append(w_fail / max(1, w_total))
            fail_rates_crit.append(w_crit_fail / max(1, w_crit_total) if w_crit_total > 0 else 0)

        fig_fail = go.Figure()
        fig_fail.add_trace(go.Scatter(
            x=days, y=fail_rates, mode="lines", name="All tasks",
            line=dict(color=_PALETTE["warning"], width=2),
            fill="tozeroy", fillcolor="rgba(232,146,74,0.10)",
            hovertemplate="All: <b>%{y:.3f}</b><extra></extra>",
        ))
        fig_fail.add_trace(go.Scatter(
            x=days, y=fail_rates_crit, mode="lines", name="High criticality",
            line=dict(color=_PALETTE["error"], width=2.5),
            hovertemplate="Critical: <b>%{y:.3f}</b><extra></extra>",
        ))
        _decorate(fig_fail, tq_start, tq_end, comm_days)
        fig_fail.update_layout(
            height=220,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(range=[0, 1.0], title_text="7-day failure rate"),
                margin=dict(l=52, r=24, t=20, b=36),
            ),
        )
        st.plotly_chart(fig_fail, use_container_width=True)

    else:
        st.info("No task outcome data found in this run.")


###############################################################################
# TAB 6 — Resources
###############################################################################

with tab_res:
    resource_metrics = {
        "sleep_quality":    ("Sleep Quality",    _PALETTE["accent"]),
        "task_load":        ("Task Load",        _PALETTE["error"]),
        "coffee":           ("Coffee Stock",     _PALETTE["monotony"]),
        "food_variety":     ("Food Variety",     _PALETTE["success"]),
        "comms_delay":      ("Comms Delay",      "#a876d9"),
        "hygiene_supplies": ("Hygiene Supplies", "#1abc9c"),
    }

    fig_res = make_subplots(
        rows=3, cols=2,
        subplot_titles=[v[0] for v in resource_metrics.values()],
        shared_xaxes=True,
        vertical_spacing=0.10,
        horizontal_spacing=0.10,
    )

    thresholds = {
        "sleep_quality":    (0.6,  "rgba(224,92,92,0.12)", "below"),
        "task_load":        (0.8,  "rgba(224,92,92,0.12)", "above"),
        "coffee":           (0.1,  "rgba(224,92,92,0.12)", "below"),
        "hygiene_supplies": (0.25, "rgba(224,92,92,0.12)", "below"),
        "comms_delay":      (0.7,  "rgba(224,92,92,0.12)", "above"),
    }

    for idx, (key, (label, color)) in enumerate(resource_metrics.items()):
        r, c = divmod(idx, 2)
        vals = [d.resource_state_dict.get(key, 0) for d in day_states]
        fig_res.add_trace(
            go.Scatter(x=days, y=vals, mode="lines", name=label,
                       line=dict(color=color, width=2.5), showlegend=False,
                       hovertemplate=f"{label}: <b>%{{y:.4f}}</b><extra></extra>"),
            row=r + 1, col=c + 1,
        )
        if key in thresholds:
            thresh_val, thresh_color, direction = thresholds[key]
            # shade the danger zone
            y0, y1 = (0, thresh_val) if direction == "below" else (thresh_val, 1.0)
            fig_res.add_hrect(
                y0=y0, y1=y1,
                fillcolor=thresh_color, line_width=0,
                row=r + 1, col=c + 1,
            )
            fig_res.add_hline(
                y=thresh_val, line_dash="dot",
                line_color="rgba(224,92,92,0.4)",
                row=r + 1, col=c + 1,
            )

    _decorate(fig_res, tq_start, tq_end, comm_days,
              row_col_pairs=[(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)])
    for r in [1, 2, 3]:
        for c in [1, 2]:
            fig_res.update_xaxes(title_text="Day" if r == 3 else "",
                                  row=r, col=c, **_axis())
            fig_res.update_yaxes(row=r, col=c, **_axis(range=[0, 1.1]))

    fig_res.update_layout(
        height=680,
        **_dl(margin=dict(l=52, r=24, t=45, b=20)),
    )
    st.plotly_chart(fig_res, use_container_width=True)
    st.caption(
        "Red zones = degraded operating range.  "
        "Dotted red lines = operational floor / ceiling thresholds.  "
        "Resource states feed into perception → belief → internal state each day."
    )

    # Per-agent fatigue accumulation
    st.markdown('<div class="section-label">Per-Agent Fatigue Accumulation</div>',
                unsafe_allow_html=True)
    fig_fatigue = go.Figure()
    # Crew mean as reference
    crew_fat = [
        sum(d.internal_states.get(aid, {}).get("fatigue", 0) for aid in agent_ids)
        / max(1, len(agent_ids))
        for d in day_states
    ]
    fig_fatigue.add_trace(go.Scatter(
        x=days, y=crew_fat, mode="lines", name="Crew mean",
        line=dict(color="#5b7099", width=1.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(91,112,153,0.06)",
        hovertemplate="Crew mean: <b>%{y:.4f}</b><extra></extra>",
    ))
    for i, aid in enumerate(agent_ids):
        fat_vals = [d.internal_states.get(aid, {}).get("fatigue", 0)
                    for d in day_states]
        if any(v != 0 for v in fat_vals):
            fig_fatigue.add_trace(go.Scatter(
                x=days, y=fat_vals, mode="lines",
                name=aid.split()[0],
                line=dict(color=_AGENT_COLORS[i % len(_AGENT_COLORS)], width=1.8),
                hovertemplate=f"{aid.split()[0]}: <b>%{{y:.4f}}</b><extra></extra>",
            ))
    _decorate(fig_fatigue, tq_start, tq_end, comm_days)
    fig_fatigue.add_hline(y=0.7, line_dash="dot", line_color="rgba(224,92,92,0.4)")
    fig_fatigue.update_layout(
        height=260,
        **_dl(
            xaxis=_axis(title_text="Day"),
            yaxis=_axis(range=[0, 1.05], title_text="Fatigue [0–1]"),
            margin=dict(l=52, r=24, t=20, b=36),
        ),
    )
    st.plotly_chart(fig_fatigue, use_container_width=True)
    st.caption(
        "Fatigue is the integrated output of sleep quality, circadian drift, and workload — "
        "the direct driver of attention and planning impairment in the task layer.  "
        "Dotted red line = 0.70 impairment onset threshold."
    )

    # Per-agent perceived sleep quality divergence
    st.markdown('<div class="section-label">Per-Agent Perceived Sleep Quality</div>',
                unsafe_allow_html=True)
    fig_psleep = go.Figure()
    for i, aid in enumerate(agent_ids):
        ps_vals = [d.perceived_states.get(aid, {}).get("perceived_sleep_quality", 0)
                   for d in day_states]
        if any(v != 0 for v in ps_vals):
            fig_psleep.add_trace(go.Scatter(
                x=days, y=ps_vals, mode="lines",
                name=aid.split()[0],
                line=dict(color=_AGENT_COLORS[i % len(_AGENT_COLORS)], width=1.8),
                hovertemplate=f"{aid.split()[0]}: <b>%{{y:.4f}}</b><extra></extra>",
            ))
    _decorate(fig_psleep, tq_start, tq_end, comm_days)
    fig_psleep.update_layout(
        height=240,
        **_dl(
            xaxis=_axis(title_text="Day"),
            yaxis=_axis(range=[0, 1.05], title_text="Perceived Sleep Quality"),
            margin=dict(l=52, r=24, t=20, b=36),
        ),
    )
    st.plotly_chart(fig_psleep, use_container_width=True)

    # Micro-event timeline
    micro_events = [(d.day if hasattr(d, "day") else days[i], d.micro_event)
                    for i, d in enumerate(day_states)
                    if d.micro_event]
    if micro_events:
        st.markdown('<div class="section-label">Micro-Event Timeline</div>',
                    unsafe_allow_html=True)
        event_days  = [me[0] for me in micro_events]
        event_names = [str(me[1]) for me in micro_events]
        # Alternate y-levels so overlapping labels don't stack
        event_y = [0.6 + 0.3 * (i % 2) for i in range(len(micro_events))]
        fig_micro = go.Figure()
        fig_micro.add_trace(go.Scatter(
            x=event_days, y=event_y,
            mode="markers+text",
            marker=dict(color=_PALETTE["accent"], size=9, symbol="diamond"),
            text=event_names,
            textposition="top center",
            textfont=dict(size=9, color="#9ab0d4"),
            hovertemplate="Day %{x}: <b>%{text}</b><extra></extra>",
            name="Event",
        ))
        # Stem lines from x-axis to marker
        for xd, yd in zip(event_days, event_y):
            fig_micro.add_shape(
                type="line", x0=xd, x1=xd, y0=0, y1=yd,
                line=dict(color="rgba(74,144,217,0.3)", width=1, dash="dot"),
            )
        _decorate(fig_micro, tq_start, tq_end, comm_days)
        fig_micro.update_layout(
            height=200,
            **_dl(
                xaxis=_axis(title_text="Day", range=[days[0] - 1, days[-1] + 1]),
                yaxis=dict(visible=False, range=[0, 1.3],
                           gridcolor="#1a2740", zerolinecolor="#1a2740"),
                margin=dict(l=24, r=24, t=20, b=36),
                showlegend=False,
            ),
        )
        st.plotly_chart(fig_micro, use_container_width=True)
        st.caption(f"{len(micro_events)} forcing events over {len(days)}-day mission.")


###############################################################################
# TAB 7 — Comparison Mode
###############################################################################

with tab_compare:
    if result_bl is None:
        st.markdown("""
<div style="background:#0e1525;border:1px solid #1e2d4a;border-radius:10px;
     padding:28px 32px;margin:20px 0;text-align:center;">
  <div style="font-size:14px;color:#5b7099;margin-bottom:12px;">
    Comparison mode requires at least one MC intervention
  </div>
  <div style="font-size:12px;color:#3d5070;">
    Add an intervention in the sidebar (e.g., <b style="color:#4a90d9;">rest_authorization</b>
    or <b style="color:#4a90d9;">celebration</b>) and re-run the simulation.
    The dashboard will automatically run a matched baseline (same seed, no comms)
    and show the counterfactual delta here.
  </div>
</div>
""", unsafe_allow_html=True)
    else:
        bl = result_bl
        bl_ds = bl.day_states
        bl_strains      = [d.core_strain      for d in bl_ds]
        bl_cohesions    = [d.core_cohesion    for d in bl_ds]
        bl_tq_pressures = [d.core_tq_pressure for d in bl_ds]

        # Delta KPIs
        delta_peak_strain  = max(strains) - max(bl_strains)
        delta_min_coh      = min(cohesions) - min(bl_cohesions)
        delta_final_coh    = cohesions[-1] - bl_cohesions[-1]

        # Task completion delta
        def _crit_pct(ds_list):
            tot = fail = 0
            for _ds in ds_list:
                if _ds.task_outcomes:
                    for _t in _ds.task_outcomes.get("task_results", []):
                        if _t.get("criticality") == "high":
                            tot += 1
                            if _t.get("outcome") != "completed":
                                fail += 1
            return (tot - fail) / max(1, tot) * 100

        with_crit_pct = _crit_pct(day_states)
        bl_crit_pct   = _crit_pct(bl_ds)
        delta_crit    = with_crit_pct - bl_crit_pct

        st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Peak Strain Δ</div>
    <div class="kpi-value {'green' if delta_peak_strain < 0 else 'red'}">{delta_peak_strain:+.3f}</div>
    <div class="kpi-sub">vs baseline {max(bl_strains):.3f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Min Cohesion Δ</div>
    <div class="kpi-value {'green' if delta_min_coh > 0 else 'red'}">{delta_min_coh:+.3f}</div>
    <div class="kpi-sub">baseline trough: {min(bl_cohesions):.3f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Final Cohesion Δ</div>
    <div class="kpi-value {'green' if delta_final_coh > 0 else 'red'}">{delta_final_coh:+.3f}</div>
    <div class="kpi-sub">baseline final: {bl_cohesions[-1]:.3f}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Critical Completion Δ</div>
    <div class="kpi-value {'green' if delta_crit > 0 else 'red'}">{delta_crit:+.1f}%</div>
    <div class="kpi-sub">baseline: {bl_crit_pct:.0f}%  |  with MC: {with_crit_pct:.0f}%</div>
  </div>
</div>
""", unsafe_allow_html=True)

        # Side-by-side physics overlay
        st.markdown('<div class="section-label">Physics Overlay — Baseline vs With Interventions</div>',
                    unsafe_allow_html=True)

        fig_cmp = make_subplots(
            rows=1, cols=2,
            subplot_titles=["Crew Strain", "Crew Cohesion"],
            horizontal_spacing=0.10,
        )
        for vals, bl_vals, name, row, col in [
            (strains,   bl_strains,   "Strain",   1, 1),
            (cohesions, bl_cohesions, "Cohesion", 1, 2),
        ]:
            fig_cmp.add_trace(
                go.Scatter(x=days, y=bl_vals, mode="lines",
                           name="Baseline",
                           line=dict(color=_PALETTE["error"], width=2, dash="dot"),
                           hovertemplate=f"Baseline {name}: <b>%{{y:.4f}}</b><extra></extra>"),
                row=1, col=col,
            )
            fig_cmp.add_trace(
                go.Scatter(x=days, y=vals, mode="lines",
                           name="With MC",
                           line=dict(color=_PALETTE["accent"], width=2.5),
                           hovertemplate=f"With MC {name}: <b>%{{y:.4f}}</b><extra></extra>"),
                row=1, col=col,
            )
            # Delta fill
            fig_cmp.add_trace(
                go.Scatter(
                    x=days + days[::-1],
                    y=vals + bl_vals[::-1],
                    fill="toself",
                    fillcolor="rgba(74,144,217,0.08)",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=1, col=col,
            )

        _decorate(fig_cmp, tq_start, tq_end, comm_days, row_col_pairs=[(1, 1), (1, 2)])
        fig_cmp.update_layout(
            height=340,
            **_dl(
                margin=dict(l=52, r=24, t=45, b=36),
                legend=dict(
                    orientation="h", x=0.5, xanchor="center", y=1.08,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#9ab0d4"),
                ),
            ),
        )
        fig_cmp.update_xaxes(**_axis(title_text="Day"))
        fig_cmp.update_yaxes(**_axis())
        st.plotly_chart(fig_cmp, use_container_width=True)
        st.caption(
            "Blue shading = region where interventions improved outcomes.  "
            "Both runs used the same daily micro-events (identical seed) "
            "— the only variable is the MC communication schedule."
        )

        # TQ window detail
        st.markdown('<div class="section-label">TQ Window Detail — Day-by-Day Delta</div>',
                    unsafe_allow_html=True)

        tq_days   = [d for d in days if tq_start <= d <= tq_end]
        tq_strain_with = [strains[days.index(d)]  for d in tq_days]
        tq_strain_bl   = [bl_strains[days.index(d)] for d in tq_days]
        tq_delta       = [w - b for w, b in zip(tq_strain_with, tq_strain_bl)]

        fig_tq_delta = go.Figure()
        fig_tq_delta.add_trace(go.Bar(
            x=tq_days, y=tq_delta,
            marker_color=[
                _PALETTE["success"] if v < 0 else _PALETTE["error"]
                for v in tq_delta
            ],
            opacity=0.8,
            hovertemplate="Day %{x}: strain delta <b>%{y:+.4f}</b><extra></extra>",
            name="Strain Δ (with MC − baseline)",
        ))
        fig_tq_delta.add_hline(y=0, line_color="#5b7099", line_width=1)
        for cd in comm_days:
            if tq_start <= cd <= tq_end:
                fig_tq_delta.add_vline(x=cd, line_dash="dot",
                                       line_color="rgba(74,144,217,0.6)")
        fig_tq_delta.update_layout(
            height=220,
            **_dl(
                xaxis=_axis(title_text="Day"),
                yaxis=_axis(title_text="Strain Δ (with MC − baseline)"),
                margin=dict(l=52, r=24, t=20, b=36),
                showlegend=False,
            ),
        )
        st.plotly_chart(fig_tq_delta, use_container_width=True)
        st.caption("Green bars = MC reduced strain vs baseline. Red = worse than baseline on that day.")

        # Intervention schedule summary
        if run_cfg.get("interventions"):
            st.markdown('<div class="section-label">Intervention Catalogue</div>',
                        unsafe_allow_html=True)
            for _itype, _iday in sorted(run_cfg["interventions"], key=lambda x: x[1]):
                s = INTERVENTION_CATALOGUE.get(_itype, {})
                desc = s.get("description", "").split(";")[0]
                mc_delta  = s.get("belief_mc_support_delta", 0)
                coh_delta = s.get("belief_crew_cohesion_delta", 0)
                relief    = s.get("workload_relief_factor", 0)
                effects = []
                if mc_delta:   effects.append(f"MC support {mc_delta:+.2f}")
                if coh_delta:  effects.append(f"cohesion {coh_delta:+.2f}")
                if relief:     effects.append(f"workload -{relief*100:.0f}%")
                effects_str = "  |  " + " · ".join(effects) if effects else ""
                st.markdown(
                    f'<div style="font-size:12px;color:#9ab0d4;padding:4px 0;">'
                    f'<span style="color:#4a90d9;font-weight:600;">Day {_iday}</span>'
                    f'&nbsp;&nbsp;<code style="background:#131929;padding:2px 6px;'
                    f'border-radius:3px;font-size:11px;">{_itype}</code>'
                    f'&nbsp;&nbsp;{desc}{effects_str}</div>',
                    unsafe_allow_html=True,
                )

        # Per-agent intervention penetration
        st.markdown('<div class="section-label">Intervention Penetration — Per-Agent Belief & Morale Response</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Did the MC message reach everyone equally? "
            "High-strain agents discount communications — their belief_mc_support "
            "and morale curves diverge from the crew average. "
            "Dotted = baseline (no intervention). Solid = with MC."
        )

        fig_pen = make_subplots(
            rows=1, cols=2,
            subplot_titles=["MC Support Belief — per agent",
                            "Morale — per agent"],
            horizontal_spacing=0.12,
        )
        for i, aid in enumerate(agent_ids):
            color = _AGENT_COLORS[i % len(_AGENT_COLORS)]
            short = aid.split()[0]

            # MC support belief
            mc_bl  = [d.belief_states.get(aid, {}).get("belief_mission_control_support", 0)
                      for d in bl_ds]
            mc_int = [d.belief_states.get(aid, {}).get("belief_mission_control_support", 0)
                      for d in day_states]
            fig_pen.add_trace(go.Scatter(
                x=days, y=mc_bl, mode="lines", name=f"{short} base",
                line=dict(color=color, width=1.2, dash="dot"),
                showlegend=False,
                hovertemplate=f"{short} baseline MC: <b>%{{y:.4f}}</b><extra></extra>",
            ), row=1, col=1)
            fig_pen.add_trace(go.Scatter(
                x=days, y=mc_int, mode="lines", name=short,
                line=dict(color=color, width=2.0),
                hovertemplate=f"{short} MC support: <b>%{{y:.4f}}</b><extra></extra>",
            ), row=1, col=1)

            # Morale
            mor_bl  = [d.internal_states.get(aid, {}).get("morale", 0) for d in bl_ds]
            mor_int = [d.internal_states.get(aid, {}).get("morale", 0) for d in day_states]
            fig_pen.add_trace(go.Scatter(
                x=days, y=mor_bl, mode="lines", name=f"{short} base",
                line=dict(color=color, width=1.2, dash="dot"),
                showlegend=False,
                hovertemplate=f"{short} baseline morale: <b>%{{y:.4f}}</b><extra></extra>",
            ), row=1, col=2)
            fig_pen.add_trace(go.Scatter(
                x=days, y=mor_int, mode="lines", name=short,
                line=dict(color=color, width=2.0),
                showlegend=i == 0,
                hovertemplate=f"{short} morale: <b>%{{y:.4f}}</b><extra></extra>",
            ), row=1, col=2)

        _decorate(fig_pen, tq_start, tq_end, comm_days, row_col_pairs=[(1, 1), (1, 2)])
        fig_pen.update_layout(
            height=320,
            **_dl(
                xaxis=_axis(title_text="Day"),
                margin=dict(l=52, r=24, t=45, b=36),
                legend=dict(
                    orientation="h", x=0.5, xanchor="center", y=1.08,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="#9ab0d4"),
                ),
            ),
        )
        fig_pen.update_xaxes(**_axis(title_text="Day"))
        fig_pen.update_yaxes(**_axis(range=[0, 1.05]))
        st.plotly_chart(fig_pen, use_container_width=True)
        st.caption(
            "Solid lines = with MC intervention. Dotted = matched baseline (same seed, no comms).  "
            "Narrow gap = intervention penetrated. Wide gap = significant effect.  "
            "Agents whose solid line barely separates from dotted are discounting the message."
        )
