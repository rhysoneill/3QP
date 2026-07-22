"""
3QP HTML Demo Report Generator
================================

Runs the same three scenarios as demo.py and produces a standalone
interactive HTML report using Plotly.js (CDN).

Usage:
    cd integration/runtime
    python -X utf8 demo_report.py

Output:
    output/demo_report.html   (open in any browser)

No additional dependencies beyond the simulation itself.
Plotly.js is loaded from CDN — requires internet on first open.
"""

import importlib.util
import json
import sys
from pathlib import Path

# --- path setup (mirrors demo.py) ---
_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent
_PHASE4 = _ROOT / "phase4" / "06_Ruthless_Core_Model"
_SOCIAL_NET = _ROOT / "modules" / "05_Social_Network"
for p in [str(_ROOT), str(_PHASE4), str(_SOCIAL_NET)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load local demo.py explicitly to avoid the demo.py inside modules/05_Social_Network
_demo_spec = importlib.util.spec_from_file_location("_local_demo", _HERE / "demo.py")
_demo = importlib.util.module_from_spec(_demo_spec)
_demo_spec.loader.exec_module(_demo)
run_scenario      = _demo.run_scenario
MISSION_DAYS      = _demo.MISSION_DAYS
MC_COMMS_START_DAY = _demo.MC_COMMS_START_DAY
MC_COMMS_FREQ     = _demo.MC_COMMS_FREQ
DEMO_SEED         = _demo.DEMO_SEED

OUTPUT_DIR = str(_HERE / "output")
REPORT_PATH = str(_HERE / "output" / "demo_report.html")

SCENARIO_DEFS = [
    ("Fragile — no MC support",      "fragile_team",        False, "#E05C5C", "solid"),
    ("Fragile — MC from day 100",    "fragile_team",        True,  "#4A90D9", "solid"),
    ("High-cohesion — no MC",        "high_cohesion_team",  False, "#5DBD5D", "dot"),
]


# ---------------------------------------------------------------------------
# Run simulations
# ---------------------------------------------------------------------------

def collect_data() -> dict:
    results = {}
    for label, preset, inject_comms, color, dash in SCENARIO_DEFS:
        rows = run_scenario(label, preset, inject_comms)
        results[label] = {
            "rows": rows,
            "color": color,
            "dash": dash,
        }
    return results


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def _peak(rows, key):
    return max(r[key] for r in rows)

def _min(rows, key):
    return min(r[key] for r in rows)

def _final(rows, key):
    return rows[-1][key]

def _pct_reduction(base, new):
    if base == 0:
        return 0.0
    return (base - new) / base * 100

def _phase_avg(rows, key, start_day, end_day):
    subset = [r[key] for r in rows if start_day <= r["day"] <= end_day]
    return sum(subset) / len(subset) if subset else 0.0


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3QP — Lunar Crew Behavioral Twin</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Oxanium:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:        #0b3d91;
    --surface:   #0d4aab;
    --surface-2: #114fba;
    --surface-3: #0a3476;
    --border:    #2f6ece;
    --text:      #e9f2ff;
    --muted:     #b8d4ff;
    --accent:    #58d9ff;
    --viz-bg:    #02050d;
    --viz-bg-2:  #040a15;
    --viz-border:#1b6dbb;
    --red:       #e05c5c;
    --green:     #5dbd5d;
    --orange:    #e8924a;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background:
      radial-gradient(circle at 12% 10%, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0) 38%),
      radial-gradient(circle at 88% 0%, rgba(88,217,255,0.25) 0%, rgba(88,217,255,0) 28%),
      linear-gradient(165deg, #0b3d91 0%, #0d4fb4 46%, #083782 100%);
    color: var(--text);
    font-family: "Manrope", "Segoe UI", system-ui, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    padding: 0 0 48px 0;
    min-height: 100vh;
  }}

  /* ---- Header ---- */
  .header {{
    background: linear-gradient(120deg, rgba(4,22,58,0.55) 0%, rgba(8,35,82,0.32) 62%, rgba(88,217,255,0.10) 100%);
    border-bottom: 1px solid rgba(233,242,255,0.18);
    padding: 36px 48px 28px;
    backdrop-filter: blur(2px);
  }}
  .header-eyebrow {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #95e7ff;
    margin-bottom: 8px;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}
  .header h1 {{
    font-size: 30px;
    font-weight: 700;
    color: #f2f7ff;
    margin-bottom: 6px;
    letter-spacing: 0.03em;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}
  .header-sub {{
    font-size: 13px;
    color: #d2e3ff;
  }}

  /* ---- KPI strip ---- */
  .kpi-strip {{
    display: flex;
    gap: 16px;
    padding: 24px 48px;
    border-bottom: 1px solid rgba(233,242,255,0.20);
    flex-wrap: wrap;
  }}
  .kpi-card {{
    flex: 1;
    min-width: 160px;
    background: linear-gradient(160deg, rgba(2,14,40,0.42) 0%, rgba(17,79,186,0.40) 100%);
    border: 1px solid rgba(233,242,255,0.22);
    border-radius: 10px;
    padding: 18px 22px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.10);
  }}
  .kpi-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #c9deff;
    margin-bottom: 6px;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}
  .kpi-value {{
    font-size: 30px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
    font-family: "Oxanium", "Manrope", sans-serif;
    letter-spacing: 0.02em;
  }}
  .kpi-sub {{
    font-size: 11px;
    color: #d8e8ff;
  }}
  .kpi-value.red   {{ color: var(--red); }}
  .kpi-value.blue  {{ color: var(--accent); }}
  .kpi-value.green {{ color: var(--green); }}
  .kpi-value.orange{{ color: var(--orange); }}

  /* ---- Legend pill strips ---- */
  .legend-strip {{
    display: flex;
    gap: 24px;
    padding: 16px 48px 0;
    flex-wrap: wrap;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #edf5ff;
    background: rgba(4,28,74,0.35);
    border: 1px solid rgba(233,242,255,0.18);
    border-radius: 999px;
    padding: 8px 12px;
  }}
  .legend-swatch {{
    width: 28px;
    height: 3px;
    border-radius: 2px;
  }}
  .legend-swatch.dashed {{
    background: repeating-linear-gradient(90deg, var(--color) 0, var(--color) 6px, transparent 6px, transparent 10px);
  }}

  /* ---- Section labels ---- */
  .section-label {{
    padding: 28px 48px 8px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #d7e7ff;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}
  .section-header {{
    padding: 28px 48px 8px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #d7e7ff;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}

  /* ---- Chart containers ---- */
  .chart-card {{
    margin: 0 48px 20px;
    background: linear-gradient(145deg, rgba(3,24,64,0.45) 0%, rgba(14,71,165,0.32) 100%);
    border: 1px solid rgba(233,242,255,0.22);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 14px 30px rgba(2,10,30,0.25);
  }}
  .chart-card.viz-shell {{
    background:
      radial-gradient(circle at 85% 15%, rgba(88,217,255,0.10) 0%, rgba(88,217,255,0) 30%),
      linear-gradient(170deg, var(--viz-bg) 0%, var(--viz-bg-2) 100%);
    border: 1px solid var(--viz-border);
    box-shadow:
      0 0 0 1px rgba(88,217,255,0.10) inset,
      0 18px 32px rgba(0,0,0,0.42);
  }}
  .chart-title {{
    padding: 16px 20px 6px;
    font-size: 13px;
    font-weight: 700;
    color: #9ad9ff;
    font-family: "Oxanium", "Manrope", sans-serif;
    letter-spacing: 0.03em;
  }}
  .chart-inner {{
    width: 100%;
    height: 260px;
  }}
  .chart-inner-xl {{
    width: 100%;
    height: 540px;
  }}

  .explorer-grid {{
    display: grid;
    grid-template-columns: minmax(580px, 1fr) 320px;
    gap: 16px;
    margin: 0 48px 20px;
    align-items: start;
  }}
  .explorer-grid .chart-card {{
    margin: 0;
  }}
  .explorer-meta {{
    padding: 0 20px 12px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    align-items: center;
  }}
  .slider-wrap {{
    display: grid;
    gap: 6px;
  }}
  .slider-label {{
    font-size: 11px;
    color: #8eb8e8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}
  .day-pill {{
    border: 1px solid rgba(88,217,255,0.5);
    color: #9fe8ff;
    background: rgba(2,12,32,0.85);
    border-radius: 8px;
    padding: 8px 12px;
    font-family: "Oxanium", "Manrope", sans-serif;
    font-size: 13px;
    min-width: 96px;
    text-align: center;
  }}
  .slider-row input[type="range"] {{
    width: 100%;
    accent-color: #58d9ff;
  }}
  .quick-jump {{
    display: flex;
    gap: 8px;
    padding: 0 20px 10px;
    flex-wrap: wrap;
  }}
  .quick-jump button {{
    border: 1px solid rgba(88,217,255,0.4);
    background: rgba(5,20,47,0.86);
    color: #cfeeff;
    border-radius: 999px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-family: "Oxanium", "Manrope", sans-serif;
    cursor: pointer;
  }}
  .quick-jump button:hover {{
    border-color: #58d9ff;
    color: #ffffff;
  }}

  .detail-card {{
    background: linear-gradient(165deg, rgba(5,30,74,0.42) 0%, rgba(17,79,186,0.36) 100%);
    border: 1px solid rgba(233,242,255,0.25);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 14px 30px rgba(2,10,30,0.25);
  }}
  .detail-kicker {{
    font-size: 11px;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: #b8d7ff;
    margin-bottom: 6px;
    font-family: "Oxanium", "Manrope", sans-serif;
    font-weight: 700;
  }}
  .detail-title {{
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 14px;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}
  .detail-metric {{
    display: flex;
    justify-content: space-between;
    gap: 8px;
    border-top: 1px solid rgba(233,242,255,0.16);
    padding: 8px 0;
    font-size: 12px;
  }}
  .detail-metric span:first-child {{
    color: #c8e0ff;
  }}
  .detail-metric span:last-child {{
    color: #ffffff;
    font-weight: 700;
    font-family: "Oxanium", "Manrope", sans-serif;
  }}
  .detail-insight {{
    margin-top: 12px;
    font-size: 12px;
    color: #d7e7ff;
    line-height: 1.6;
  }}

  /* ---- Footer ---- */
  .footer {{
    margin: 24px 48px 0;
    padding-top: 16px;
    border-top: 1px solid rgba(233,242,255,0.20);
    font-size: 11px;
    color: #d3e4ff;
    display: flex;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .footer-note {{
    max-width: 680px;
    line-height: 1.7;
  }}
  .footer-badge {{
    background: rgba(4,25,66,0.50);
    border: 1px solid rgba(233,242,255,0.25);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 10px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #d4e7ff;
    white-space: nowrap;
    align-self: start;
  }}

  @media (max-width: 1200px) {{
    .explorer-grid {{
      grid-template-columns: 1fr;
    }}
  }}

  @media (max-width: 900px) {{
    .header, .kpi-strip, .legend-strip, .section-label, .section-header,
    .chart-card, .explorer-grid, .footer {{
      margin-left: 16px;
      margin-right: 16px;
      padding-left: 0;
      padding-right: 0;
    }}
    .header {{
      padding: 26px 16px 20px;
    }}
    .kpi-strip {{
      padding-top: 18px;
      padding-bottom: 18px;
    }}
    .chart-card {{
      margin: 0 16px 16px;
    }}
    .section-label, .section-header {{
      padding: 20px 16px 8px;
    }}
    .legend-strip {{
      padding: 14px 16px 0;
    }}
    .footer {{
      margin: 20px 16px 0;
    }}
    .chart-inner-xl {{
      height: 420px;
    }}
  }}
</style>
</head>
<body>

<!-- ===== Header ===== -->
<div class="header">
  <div class="header-eyebrow">MITRE &middot; Behavioral Health Modeling</div>
  <h1>3QP &mdash; Lunar Crew Behavioral Twin</h1>
  <div class="header-sub">
    200-Day Mission Counterfactual Analysis &nbsp;&middot;&nbsp;
    {crew_size}-Astronaut Crew &nbsp;&middot;&nbsp;
    Third-Quarter Phenomenon Study
  </div>
</div>

<!-- ===== KPI Strip ===== -->
<div class="kpi-strip">
  <div class="kpi-card">
    <div class="kpi-label">Peak Strain &mdash; Fragile</div>
    <div class="kpi-value red">{peak_strain_fragile:.3f}</div>
    <div class="kpi-sub">without MC support</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">MC Intervention Effect</div>
    <div class="kpi-value blue">&minus;{mc_reduction:.0f}%</div>
    <div class="kpi-sub">peak strain reduction</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Personality Advantage</div>
    <div class="kpi-value green">&minus;{hc_reduction:.0f}%</div>
    <div class="kpi-sub">high-cohesion vs fragile, no MC</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">MC Comms Schedule</div>
    <div class="kpi-value orange">q{mc_freq}d</div>
    <div class="kpi-sub">reassurance from day {mc_start}</div>
  </div>
</div>

<!-- ===== Legend ===== -->
<div class="legend-strip">
  <div class="legend-item">
    <div class="legend-swatch" style="background:#E05C5C;"></div>
    Fragile crew &mdash; no MC support
  </div>
  <div class="legend-item">
    <div class="legend-swatch" style="background:#4A90D9;"></div>
    Fragile crew &mdash; MC support from day {mc_start}
  </div>
  <div class="legend-item">
    <div class="legend-swatch dashed" style="--color:#5DBD5D; background:none; border-top: 2px dashed #5DBD5D; height:0; margin-top:2px;"></div>
    High-cohesion crew &mdash; no MC support
  </div>
</div>

<!-- ===== Charts ===== -->
<div class="section-label">Orbital Behavioral Explorer</div>

<div class="explorer-grid">
  <div class="chart-card viz-shell">
    <div class="chart-title">3D Scenario Orbit Map &mdash; rotate, zoom, and select a mission body</div>
    <div class="explorer-meta">
      <div class="slider-wrap">
        <div class="slider-label">Mission day timeline</div>
        <div class="slider-row"><input id="explorer-day-slider" type="range" min="1" max="{mission_days}" value="{mission_days}" step="1" /></div>
      </div>
      <div class="day-pill" id="explorer-day-pill">Day {mission_days}</div>
    </div>
    <div class="quick-jump">
      <button type="button" data-jump-day="1">Day 1</button>
      <button type="button" data-jump-day="{mc_start}">MC Start</button>
      <button type="button" data-jump-day="{tq_start}">TQ Start</button>
      <button type="button" data-jump-day="{tq_end}">TQ End</button>
      <button type="button" data-jump-day="{mission_days}">Final</button>
    </div>
    <div class="chart-inner-xl" id="orbital-explorer"></div>
  </div>

  <aside class="detail-card">
    <div class="detail-kicker">Selected Scenario</div>
    <div class="detail-title" id="detail-scenario">Fragile &mdash; no MC support</div>
    <div class="detail-metric"><span>Mission Day</span><span id="detail-day">{mission_days}</span></div>
    <div class="detail-metric"><span>Strain (S)</span><span id="detail-strain">0.000</span></div>
    <div class="detail-metric"><span>Cohesion (C)</span><span id="detail-cohesion">0.000</span></div>
    <div class="detail-metric"><span>Monotony (M)</span><span id="detail-monotony">0.000</span></div>
    <div class="detail-metric"><span>TQ Pressure (Q)</span><span id="detail-tq">0.000</span></div>
    <div class="detail-metric"><span>Social Cohesion</span><span id="detail-social">0.000</span></div>
    <div class="detail-insight" id="detail-insight">
      Live mission-state narrative will appear here after selecting a scenario body in the 3D explorer.
    </div>
  </aside>
</div>

<div class="section-label">Psychological State Dynamics</div>

<div class="chart-card viz-shell">
  <div class="chart-title">Accumulated Strain &mdash; psychological load over mission</div>
  <div class="chart-inner" id="strain-chart"></div>
</div>

<div class="chart-card viz-shell">
  <div class="chart-title">Crew Cohesion &mdash; social bond quality (TQP indicator)</div>
  <div class="chart-inner" id="cohesion-chart"></div>
</div>

<div class="chart-card viz-shell">
  <div class="chart-title">Social Network Cohesion &mdash; Module 05 full graph dynamics</div>
  <div class="chart-inner" id="social-chart"></div>
</div>

<div class="section-header">Task Performance &mdash; Operational Risk by Mission Phase</div>

<div class="chart-card viz-shell">
  <div class="chart-title">Coordination Failures &amp; Maintenance Skips &mdash; Phase Comparison (Fragile Crew)</div>
  <div class="chart-inner" id="task-coord-chart"></div>
</div>

<div class="chart-card viz-shell">
  <div class="chart-title">Intervention Effect on Task Compliance &mdash; Fragile No-MC vs With-MC</div>
  <div class="chart-inner" id="task-mc-chart"></div>
</div>

<div class="chart-card viz-shell">
  <div class="chart-title">Critical Task Completion Rate by Phase &mdash; All Scenarios</div>
  <div class="chart-inner" id="task-critical-chart"></div>
</div>

<!-- ===== Footer ===== -->
<div class="footer">
  <div class="footer-note">
    <strong style="color:var(--text)">Methodology:</strong>
    All three scenarios run with identical daily micro-events (seed {seed}) &mdash;
    the only variables are crew personality profile and Mission Control communication schedule.
    Physics layer: RuthlessCoreModel (M/S/C/Q coupled ODEs).
    Per-agent pipeline: Resource &rarr; Perception &rarr; Belief &rarr; Internal State &rarr; Action Selection.
    Social layer: Module 05 full graph dynamics (tie-strength drift, clique detection).
  </div>
  <div class="footer-badge">3QP v0.1 &middot; MITRE Internal</div>
</div>

<script>
// ---- injected simulation data ----
var DAYS    = {days_json};
var LABELS  = {labels_json};
var COLORS  = {colors_json};
var DASHES  = {dashes_json};
var STRAIN  = {strain_json};
var COHESION = {cohesion_json};
var MONOTONY = {monotony_json};
var TQ_PRESSURE = {tq_json};
var SOCIAL  = {social_json};
var SOCIAL_DAYS = {social_days_json};
var MC_START = {mc_start};
var TQ_START = {tq_start};
var TQ_END   = {tq_end};
var TASK_PERF = {task_perf_json};
var FONT_FAMILY = '"Manrope", "Segoe UI", system-ui, sans-serif';
var FONT_FAMILY_DISPLAY = '"Oxanium", "Manrope", "Segoe UI", system-ui, sans-serif';

// ---- common layout base ----
var LAYOUT_BASE = {{
  paper_bgcolor: '#04070f',
  plot_bgcolor:  '#04070f',
  font: {{ family: FONT_FAMILY, size: 11, color: '#8eb8e8' }},
  margin: {{ l: 52, r: 24, t: 16, b: 36 }},
  showlegend: false,
  hovermode: 'x unified',
  hoverlabel: {{
    bgcolor: '#06162c',
    bordercolor: '#1f6ab3',
    font: {{ size: 12, color: '#e7f3ff', family: FONT_FAMILY }},
  }},
  xaxis: {{
    gridcolor:  '#10213d',
    zerolinecolor: '#10213d',
    tickcolor: '#153160',
    linecolor: '#153160',
    title: {{ text: 'Mission Day', font: {{ size: 11, family: FONT_FAMILY_DISPLAY }} }},
  }},
  yaxis: {{
    gridcolor: '#10213d',
    zerolinecolor: '#10213d',
    tickcolor: '#153160',
    linecolor: '#153160',
  }},
  shapes: [
    // TQ window shading
    {{
      type: 'rect', xref: 'x', yref: 'paper',
      x0: TQ_START, x1: TQ_END, y0: 0, y1: 1,
      fillcolor: 'rgba(232,146,74,0.08)',
      line: {{ width: 0 }},
      layer: 'below',
    }},
    // MC comms start line
    {{
      type: 'line', xref: 'x', yref: 'paper',
      x0: MC_START, x1: MC_START, y0: 0, y1: 1,
      line: {{ color: 'rgba(88,217,255,0.58)', width: 1.5, dash: 'dot' }},
    }},
  ],
  annotations: [
    {{
      xref: 'x', yref: 'paper',
      x: MC_START + 2, y: 0.96,
      text: 'MC support begins',
      showarrow: false,
      font: {{ size: 10, color: 'rgba(88,217,255,0.78)', family: FONT_FAMILY_DISPLAY }},
      xanchor: 'left',
    }},
    {{
      xref: 'x', yref: 'paper',
      x: (TQ_START + TQ_END) / 2, y: 0.04,
      text: '3rd quarter',
      showarrow: false,
      font: {{ size: 10, color: 'rgba(232,146,74,0.72)', family: FONT_FAMILY_DISPLAY }},
      xanchor: 'center',
    }},
  ],
}};

var CONFIG = {{
  displayModeBar: true,
  displaylogo: false,
  responsive: true,
  scrollZoom: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
}};

function buildTraces(seriesData, seriesDays) {{
  var traces = [];
  for (var i = 0; i < LABELS.length; i++) {{
    var days = seriesDays ? seriesDays[i] : DAYS;
    traces.push({{
      x: days,
      y: seriesData[i],
      name: LABELS[i],
      type: 'scatter',
      mode: 'lines',
      line: {{
        color: COLORS[i],
        width: 2.5,
        dash: DASHES[i],
      }},
      hovertemplate: '<b>' + LABELS[i] + '</b><br>Day %{{x}}<br>Value: %{{y:.4f}}<extra></extra>',
    }});
  }}
  return traces;
}}

function valueAtDay(series, dayIdx) {{
  if (!series || !series.length) return 0;
  var safe = Math.max(0, Math.min(series.length - 1, dayIdx));
  return series[safe];
}}

function socialAtDay(scenarioIdx, dayNumber) {{
  var days = SOCIAL_DAYS[scenarioIdx] || [];
  var vals = SOCIAL[scenarioIdx] || [];
  if (!days.length || !vals.length) return valueAtDay(COHESION[scenarioIdx], dayNumber - 1);
  var best = vals[0];
  for (var i = 0; i < days.length; i++) {{
    if (days[i] <= dayNumber) best = vals[i];
    if (days[i] > dayNumber) break;
  }}
  return best;
}}

function stateInsight(strain, cohesion, tqPressure) {{
  if (tqPressure > 1.1 || strain > 1.25) {{
    return 'Elevated collapse pressure signature. Crew state suggests high operational fragility and reduced tolerance for additional stressors.';
  }}
  if (cohesion > 0.66 && strain < 0.92) {{
    return 'Crew is operating in a resilient envelope. Social capital and psychological load are still balanced.';
  }}
  if (cohesion < 0.46) {{
    return 'Cohesion erosion is now the dominant risk channel. Expect interpersonal friction and coordination inefficiency.';
  }}
  return 'Mixed regime: manageable but unstable. Small shocks can amplify quickly inside the third-quarter window.';
}}

function scenarioState(scenarioIdx, dayIdx) {{
  var dayNumber = dayIdx + 1;
  var strain = valueAtDay(STRAIN[scenarioIdx], dayIdx);
  var cohesion = valueAtDay(COHESION[scenarioIdx], dayIdx);
  var monotony = valueAtDay(MONOTONY[scenarioIdx], dayIdx);
  var tq = valueAtDay(TQ_PRESSURE[scenarioIdx], dayIdx);
  var social = socialAtDay(scenarioIdx, dayNumber);

  var missionPhase = dayIdx / Math.max(1, DAYS.length - 1);
  var omega = (0.58 + scenarioIdx * 0.22) * Math.PI * 2;
  var angle = (missionPhase * omega * 6.2) + (scenarioIdx * 2.2);
  var radius = 2.7 + (scenarioIdx * 1.45) + (strain * 0.42);

  return {{
    idx: scenarioIdx,
    label: LABELS[scenarioIdx],
    color: COLORS[scenarioIdx],
    day: dayNumber,
    strain: strain,
    cohesion: cohesion,
    monotony: monotony,
    tq: tq,
    social: social,
    x: radius * Math.cos(angle),
    y: radius * Math.sin(angle),
    z: ((cohesion - 0.5) * 5.1) + ((social - 0.5) * 2.9) + (Math.sin(angle * 0.7) * 0.5),
    size: 14 + (strain * 16) + ((1 - cohesion) * 4),
  }};
}}

function buildStarTrace() {{
  function frac(v) {{ return v - Math.floor(v); }}
  var xs = [];
  var ys = [];
  var zs = [];
  var sizes = [];
  for (var i = 0; i < 300; i++) {{
    var x = (frac(Math.sin((i + 1) * 12.9898) * 43758.5453) * 36) - 18;
    var y = (frac(Math.sin((i + 11) * 7.233) * 12839.221) * 36) - 18;
    var z = (frac(Math.sin((i + 31) * 3.731) * 98347.113) * 20) - 10;
    if (Math.sqrt((x * x) + (y * y) + (z * z)) < 5.6) {{
      continue;
    }}
    xs.push(x);
    ys.push(y);
    zs.push(z);
    sizes.push(0.8 + (frac(i * 9.13) * 1.3));
  }}
  return {{
    type: 'scatter3d',
    mode: 'markers',
    x: xs,
    y: ys,
    z: zs,
    marker: {{ size: sizes, color: 'rgba(220,236,255,0.82)' }},
    hoverinfo: 'skip',
    showlegend: false,
  }};
}}

function buildOrbitTrace(state) {{
  var xs = [];
  var ys = [];
  var zs = [];
  var radius = Math.sqrt((state.x * state.x) + (state.y * state.y));
  var tilt = ((state.cohesion - 0.5) * 1.2) + ((state.idx - 1) * 0.18);
  for (var k = 0; k <= 130; k++) {{
    var t = (k / 130) * Math.PI * 2;
    xs.push(radius * Math.cos(t));
    ys.push(radius * Math.sin(t));
    zs.push(Math.sin((t * 1.4) + state.idx) * tilt);
  }}
  return {{
    type: 'scatter3d',
    mode: 'lines',
    x: xs,
    y: ys,
    z: zs,
    line: {{ color: state.color, width: 2 }},
    opacity: 0.55,
    hoverinfo: 'skip',
    showlegend: false,
  }};
}}

function renderExplorer(dayValue, selectedScenarioIdx) {{
  var dayIdx = Math.max(0, Math.min(DAYS.length - 1, dayValue - 1));
  var states = [];
  for (var i = 0; i < LABELS.length; i++) {{
    states.push(scenarioState(i, dayIdx));
  }}

  var selected = states[Math.max(0, Math.min(states.length - 1, selectedScenarioIdx || 0))];
  document.getElementById('explorer-day-pill').textContent = 'Day ' + dayValue;
  document.getElementById('detail-scenario').textContent = selected.label;
  document.getElementById('detail-day').textContent = String(dayValue);
  document.getElementById('detail-strain').textContent = selected.strain.toFixed(3);
  document.getElementById('detail-cohesion').textContent = selected.cohesion.toFixed(3);
  document.getElementById('detail-monotony').textContent = selected.monotony.toFixed(3);
  document.getElementById('detail-tq').textContent = selected.tq.toFixed(3);
  document.getElementById('detail-social').textContent = selected.social.toFixed(3);
  document.getElementById('detail-insight').textContent = stateInsight(selected.strain, selected.cohesion, selected.tq);

  var orbitTraces = states.map(buildOrbitTrace);

  var markerSizes = [];
  var markerLines = [];
  var symbols = [];
  var xs = [];
  var ys = [];
  var zs = [];
  var texts = [];
  var custom = [];
  for (var j = 0; j < states.length; j++) {{
    var st = states[j];
    var isSelected = st.idx === selected.idx;
    xs.push(st.x);
    ys.push(st.y);
    zs.push(st.z);
    texts.push(st.label);
    custom.push([st.idx, st.day, st.strain, st.cohesion, st.social, st.monotony, st.tq]);
    markerSizes.push(isSelected ? st.size + 6 : st.size);
    markerLines.push({{ color: isSelected ? '#c6f4ff' : '#0b1f41', width: isSelected ? 3 : 1.2 }});
    symbols.push(isSelected ? 'diamond' : 'circle');
  }}

  var planetTrace = {{
    type: 'scatter3d',
    mode: 'markers+text',
    name: 'scenario-planets',
    x: xs,
    y: ys,
    z: zs,
    text: texts,
    textposition: 'top center',
    textfont: {{ family: FONT_FAMILY_DISPLAY, size: 11, color: '#ccecff' }},
    marker: {{
      size: markerSizes,
      color: COLORS,
      opacity: 0.98,
      line: markerLines,
      symbol: symbols,
    }},
    customdata: custom,
    hovertemplate:
      '<b>%{{text}}</b><br>' +
      'Day %{{customdata[1]}}<br>' +
      'Strain: %{{customdata[2]:.3f}}<br>' +
      'Cohesion: %{{customdata[3]:.3f}}<br>' +
      'Social: %{{customdata[4]:.3f}}<br>' +
      'Monotony: %{{customdata[5]:.3f}}<br>' +
      'TQ Pressure: %{{customdata[6]:.3f}}<extra></extra>',
    showlegend: false,
  }};

  var traces = [
    buildStarTrace(),
    {{
      type: 'scatter3d',
      mode: 'markers',
      x: [0], y: [0], z: [0],
      marker: {{ size: 52, color: 'rgba(46,144,255,0.22)' }},
      hoverinfo: 'skip',
      showlegend: false,
    }},
    {{
      type: 'scatter3d',
      mode: 'markers+text',
      x: [0], y: [0], z: [0],
      marker: {{ size: 28, color: '#2f7fe9', line: {{ color: '#a7d4ff', width: 1.8 }} }},
      text: ['Earth Baseline'],
      textposition: 'bottom center',
      textfont: {{ family: FONT_FAMILY_DISPLAY, size: 11, color: '#a5d7ff' }},
      hovertemplate: 'Earth baseline node<extra></extra>',
      showlegend: false,
    }},
  ].concat(orbitTraces).concat([planetTrace]);

  var layout = {{
    paper_bgcolor: '#04070f',
    plot_bgcolor: '#04070f',
    margin: {{ l: 0, r: 0, t: 0, b: 0 }},
    scene: {{
      bgcolor: '#04070f',
      xaxis: {{ showgrid: false, zeroline: false, showline: false, showticklabels: false, visible: false }},
      yaxis: {{ showgrid: false, zeroline: false, showline: false, showticklabels: false, visible: false }},
      zaxis: {{ showgrid: false, zeroline: false, showline: false, showticklabels: false, visible: false }},
      aspectmode: 'cube',
      camera: {{ eye: {{ x: 1.55, y: 1.55, z: 1.1 }} }},
    }},
    showlegend: false,
    hoverlabel: {{
      bgcolor: '#06162c',
      bordercolor: '#1f6ab3',
      font: {{ size: 12, family: FONT_FAMILY, color: '#e7f3ff' }},
    }},
  }};

  Plotly.react('orbital-explorer', traces, layout, CONFIG);
}}

(function setupExplorer() {{
  var slider = document.getElementById('explorer-day-slider');
  var jumpButtons = Array.prototype.slice.call(document.querySelectorAll('[data-jump-day]'));
  var selectedScenario = 0;

  function rerender(dayVal) {{
    renderExplorer(dayVal, selectedScenario);
  }}

  slider.addEventListener('input', function() {{
    rerender(parseInt(slider.value, 10));
  }});

  jumpButtons.forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var jumpDay = parseInt(btn.getAttribute('data-jump-day'), 10);
      if (!Number.isFinite(jumpDay)) return;
      var clamped = Math.max(1, Math.min(DAYS.length, jumpDay));
      slider.value = String(clamped);
      rerender(clamped);
    }});
  }});

  var explorerEl = document.getElementById('orbital-explorer');
  explorerEl.on('plotly_click', function(evt) {{
    if (!evt || !evt.points || !evt.points.length) return;
    var point = evt.points[0];
    if (!point || !point.data || point.data.name !== 'scenario-planets') return;
    selectedScenario = point.pointNumber || 0;
    rerender(parseInt(slider.value, 10));
  }});

  rerender(parseInt(slider.value, 10));
}})();

// ---- Strain chart ----
(function() {{
  var layout = JSON.parse(JSON.stringify(LAYOUT_BASE));
  layout.yaxis.title = {{ text: 'Strain (S)', font: {{ size: 11 }} }};
  layout.yaxis.rangemode = 'tozero';
  Plotly.newPlot('strain-chart', buildTraces(STRAIN, null), layout, CONFIG);
}})();

// ---- Cohesion chart ----
(function() {{
  var layout = JSON.parse(JSON.stringify(LAYOUT_BASE));
  layout.yaxis.title = {{ text: 'Cohesion (C)', font: {{ size: 11 }} }};
  Plotly.newPlot('cohesion-chart', buildTraces(COHESION, null), layout, CONFIG);
}})();

// ---- Social network chart ----
(function() {{
  var layout = JSON.parse(JSON.stringify(LAYOUT_BASE));
  layout.yaxis.title = {{ text: 'Graph edge weight', font: {{ size: 11 }} }};
  layout.yaxis.range = [0, 1];
  var traces = buildTraces(SOCIAL, SOCIAL_DAYS);
  // Only show traces that have data
  traces = traces.filter(function(t) {{ return t.y.length > 0; }});
  Plotly.newPlot('social-chart', traces, layout, CONFIG);
}})();

// ---- Task performance: phase degradation (fragile no-MC) ----
(function() {{
  var phases = ['Early (d1–100)', 'TQ Window (d101–150)', 'Late (d151–200)'];
  var nomc = TASK_PERF['fragile_no_mc'];
  var traces = [
    {{
      name: 'Coordination failures',
      x: phases,
      y: [nomc.early.coord, nomc.tq.coord, nomc.late.coord].map(function(v) {{ return v * 100; }}),
      type: 'bar',
      marker: {{ color: '#E05C5C', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Coordination failure</extra>',
    }},
    {{
      name: 'Maintenance skips',
      x: phases,
      y: [nomc.early.maint, nomc.tq.maint, nomc.late.maint].map(function(v) {{ return v * 100; }}),
      type: 'bar',
      marker: {{ color: '#E8924A', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Maintenance skip</extra>',
    }},
    {{
      name: 'Planning errors',
      x: phases,
      y: [nomc.early.planning, nomc.tq.planning, nomc.late.planning].map(function(v) {{ return v * 100; }}),
      type: 'bar',
      marker: {{ color: '#A876D9', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Planning error</extra>',
    }},
    {{
      name: 'Checklist misses',
      x: phases,
      y: [nomc.early.checklist, nomc.tq.checklist, nomc.late.checklist].map(function(v) {{ return v * 100; }}),
      type: 'bar',
      marker: {{ color: '#5B9BD5', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Checklist miss</extra>',
    }},
  ];
  var layout = {{
    paper_bgcolor: '#04070f',
    plot_bgcolor:  '#04070f',
    barmode: 'group',
    bargap: 0.20,
    bargroupgap: 0.06,
    font: {{ family: FONT_FAMILY, size: 11, color: '#8eb8e8' }},
    margin: {{ l: 52, r: 24, t: 16, b: 48 }},
    showlegend: true,
    legend: {{ orientation: 'h', x: 0, y: 1.12,
               font: {{ size: 10, family: FONT_FAMILY, color: '#9fd4ff' }},
               bgcolor: 'rgba(0,0,0,0)', bordercolor: 'rgba(0,0,0,0)' }},
    hovermode: 'x unified',
    hoverlabel: {{ bgcolor: '#06162c', bordercolor: '#1f6ab3',
                   font: {{ size: 12, color: '#e7f3ff', family: FONT_FAMILY }} }},
    xaxis: {{ gridcolor: '#10213d', tickcolor: '#153160', linecolor: '#153160' }},
    yaxis: {{
      gridcolor: '#10213d', zerolinecolor: '#10213d', tickcolor: '#153160', linecolor: '#153160',
      title: {{ text: 'Failure rate (%)', font: {{ size: 11, family: FONT_FAMILY_DISPLAY }} }},
      rangemode: 'tozero',
      tickformat: '.0f',
      ticksuffix: '%',
    }},
    shapes: [{{
      type: 'rect', xref: 'paper', yref: 'paper',
      x0: 0.36, x1: 0.70, y0: 0, y1: 1,
      fillcolor: 'rgba(232,146,74,0.07)', line: {{ width: 0 }}, layer: 'below',
    }}],
    annotations: [{{
      xref: 'paper', yref: 'paper', x: 0.53, y: 0.97,
      text: '3rd quarter', showarrow: false,
      font: {{ size: 10, color: 'rgba(232,146,74,0.72)', family: FONT_FAMILY_DISPLAY }}, xanchor: 'center',
    }}],
  }};
  Plotly.newPlot('task-coord-chart', traces, layout, CONFIG);
}})();

// ---- Task performance: intervention effect (coordination failures) ----
(function() {{
  var phases = ['Early (d1–100)', 'TQ Window (d101–150)', 'Late (d151–200)'];
  var nomc = TASK_PERF['fragile_no_mc'];
  var mc   = TASK_PERF['fragile_mc'];
  var hc   = TASK_PERF['high_cohesion'];
  var metric = 'coord';
  var traces = [
    {{
      name: 'Fragile — no MC',
      x: phases,
      y: [nomc.early[metric], nomc.tq[metric], nomc.late[metric]].map(function(v){{ return v*100; }}),
      type: 'bar', marker: {{ color: '#E05C5C', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Fragile, no MC</extra>',
    }},
    {{
      name: 'Fragile — MC from day 100',
      x: phases,
      y: [mc.early[metric], mc.tq[metric], mc.late[metric]].map(function(v){{ return v*100; }}),
      type: 'bar', marker: {{ color: '#4A90D9', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Fragile, with MC</extra>',
    }},
    {{
      name: 'High-cohesion — no MC',
      x: phases,
      y: [hc.early[metric], hc.tq[metric], hc.late[metric]].map(function(v){{ return v*100; }}),
      type: 'bar', marker: {{ color: '#5DBD5D', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>High-cohesion</extra>',
    }},
  ];
  var layout = {{
    paper_bgcolor: '#04070f',
    plot_bgcolor:  '#04070f',
    barmode: 'group',
    bargap: 0.20,
    bargroupgap: 0.06,
    font: {{ family: FONT_FAMILY, size: 11, color: '#8eb8e8' }},
    margin: {{ l: 52, r: 24, t: 16, b: 48 }},
    showlegend: true,
    legend: {{ orientation: 'h', x: 0, y: 1.12,
               font: {{ size: 10, family: FONT_FAMILY, color: '#9fd4ff' }},
               bgcolor: 'rgba(0,0,0,0)', bordercolor: 'rgba(0,0,0,0)' }},
    hovermode: 'x unified',
    hoverlabel: {{ bgcolor: '#06162c', bordercolor: '#1f6ab3',
                   font: {{ size: 12, color: '#e7f3ff', family: FONT_FAMILY }} }},
    xaxis: {{ gridcolor: '#10213d', tickcolor: '#153160', linecolor: '#153160' }},
    yaxis: {{
      gridcolor: '#10213d', zerolinecolor: '#10213d', tickcolor: '#153160', linecolor: '#153160',
      title: {{ text: 'Coordination failure rate (%)', font: {{ size: 11, family: FONT_FAMILY_DISPLAY }} }},
      rangemode: 'tozero',
      tickformat: '.0f',
      ticksuffix: '%',
    }},
    shapes: [{{
      type: 'rect', xref: 'paper', yref: 'paper',
      x0: 0.36, x1: 0.70, y0: 0, y1: 1,
      fillcolor: 'rgba(232,146,74,0.07)', line: {{ width: 0 }}, layer: 'below',
    }}, {{
      type: 'line', xref: 'paper', yref: 'paper',
      x0: 0.36, x1: 0.36, y0: 0, y1: 1,
      line: {{ color: 'rgba(74,144,217,0.35)', width: 1.2, dash: 'dot' }},
    }}],
    annotations: [{{
      xref: 'paper', yref: 'paper', x: 0.53, y: 0.97,
      text: 'TQ window — MC starts day 100', showarrow: false,
      font: {{ size: 10, color: 'rgba(88,217,255,0.72)', family: FONT_FAMILY_DISPLAY }}, xanchor: 'center',
    }}],
  }};
  Plotly.newPlot('task-mc-chart', traces, layout, CONFIG);
}})();

// ---- Critical task completion rate by phase ----
(function() {{
  var phases = ['Early (d1–100)', 'TQ Window (d101–150)', 'Late (d151–200)'];
  var nomc = TASK_PERF['fragile_no_mc'];
  var mc   = TASK_PERF['fragile_mc'];
  var hc   = TASK_PERF['high_cohesion'];
  var traces = [
    {{
      name: 'Fragile — no MC',
      x: phases,
      y: [nomc.early.critical_completion, nomc.tq.critical_completion, nomc.late.critical_completion].map(function(v){{ return v*100; }}),
      type: 'bar', marker: {{ color: '#E05C5C', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Fragile, no MC</extra>',
    }},
    {{
      name: 'Fragile — MC from day 100',
      x: phases,
      y: [mc.early.critical_completion, mc.tq.critical_completion, mc.late.critical_completion].map(function(v){{ return v*100; }}),
      type: 'bar', marker: {{ color: '#4A90D9', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>Fragile, with MC</extra>',
    }},
    {{
      name: 'High-cohesion — no MC',
      x: phases,
      y: [hc.early.critical_completion, hc.tq.critical_completion, hc.late.critical_completion].map(function(v){{ return v*100; }}),
      type: 'bar', marker: {{ color: '#5DBD5D', opacity: 0.85 }},
      hovertemplate: '%{{x}}: <b>%{{y:.1f}}%</b><extra>High-cohesion</extra>',
    }},
  ];
  var layout = {{
    paper_bgcolor: '#04070f',
    plot_bgcolor:  '#04070f',
    barmode: 'group',
    bargap: 0.20,
    bargroupgap: 0.06,
    font: {{ family: FONT_FAMILY, size: 11, color: '#8eb8e8' }},
    margin: {{ l: 52, r: 24, t: 16, b: 48 }},
    showlegend: true,
    legend: {{ orientation: 'h', x: 0, y: 1.12,
               font: {{ size: 10, family: FONT_FAMILY, color: '#9fd4ff' }},
               bgcolor: 'rgba(0,0,0,0)', bordercolor: 'rgba(0,0,0,0)' }},
    hovermode: 'x unified',
    hoverlabel: {{ bgcolor: '#06162c', bordercolor: '#1f6ab3',
                   font: {{ size: 12, color: '#e7f3ff', family: FONT_FAMILY }} }},
    xaxis: {{ gridcolor: '#10213d', tickcolor: '#153160', linecolor: '#153160' }},
    yaxis: {{
      gridcolor: '#10213d', zerolinecolor: '#10213d', tickcolor: '#153160', linecolor: '#153160',
      title: {{ text: 'Critical task completion (%)', font: {{ size: 11, family: FONT_FAMILY_DISPLAY }} }},
      range: [0, 105],
      tickformat: '.0f',
      ticksuffix: '%',
    }},
    shapes: [{{
      type: 'rect', xref: 'paper', yref: 'paper',
      x0: 0.36, x1: 0.70, y0: 0, y1: 1,
      fillcolor: 'rgba(232,146,74,0.07)', line: {{ width: 0 }}, layer: 'below',
    }}],
    annotations: [{{
      xref: 'paper', yref: 'paper', x: 0.53, y: 0.97,
      text: '3rd quarter', showarrow: false,
      font: {{ size: 10, color: 'rgba(232,146,74,0.72)', family: FONT_FAMILY_DISPLAY }}, xanchor: 'center',
    }}],
  }};
  Plotly.newPlot('task-critical-chart', traces, layout, CONFIG);
}})();
</script>
</body>
</html>
"""


def generate_html(data: dict) -> str:
    days = list(range(1, MISSION_DAYS + 1))
    labels = [label for label, _, _ in [(k, v["color"], v["dash"]) for k, v in data.items()]]
    colors = [v["color"] for v in data.values()]
    dashes = [v["dash"] for v in data.values()]

    strain_series   = [[r["strain"]   for r in v["rows"]] for v in data.values()]
    cohesion_series = [[r["cohesion"] for r in v["rows"]] for v in data.values()]
    monotony_series = [[r["monotony"] for r in v["rows"]] for v in data.values()]
    tq_series       = [[r["tq_pressure"] for r in v["rows"]] for v in data.values()]
    social_series   = [[r["social_cohesion"] for r in v["rows"] if r["social_cohesion"] is not None] for v in data.values()]
    social_days     = [[r["day"]              for r in v["rows"] if r["social_cohesion"] is not None] for v in data.values()]

    # Task performance: phase-bucketed averages for each scenario
    tq_start_day = int(0.5 * MISSION_DAYS) + 1
    tq_end_day   = int(0.75 * MISSION_DAYS)
    late_start   = tq_end_day + 1

    def _tp(rows, early_e=int(0.5*MISSION_DAYS), tq_s=tq_start_day, tq_e=tq_end_day, late_s=late_start):
        def _crit_avg(start, end):
            vals = [r["critical_completion_rate"] for r in rows
                    if start <= r["day"] <= end and r["critical_completion_rate"] is not None]
            return sum(vals) / len(vals) if vals else 0.0
        return {
            "early":   {
                "coord":     _phase_avg(rows, "coord_failure_rate",    1,      early_e),
                "checklist": _phase_avg(rows, "checklist_miss_rate",   1,      early_e),
                "planning":  _phase_avg(rows, "planning_error_rate",   1,      early_e),
                "maint":     _phase_avg(rows, "maintenance_skip_rate", 1,      early_e),
                "critical_completion": _crit_avg(1, early_e),
            },
            "tq":      {
                "coord":     _phase_avg(rows, "coord_failure_rate",    tq_s,   tq_e),
                "checklist": _phase_avg(rows, "checklist_miss_rate",   tq_s,   tq_e),
                "planning":  _phase_avg(rows, "planning_error_rate",   tq_s,   tq_e),
                "maint":     _phase_avg(rows, "maintenance_skip_rate", tq_s,   tq_e),
                "critical_completion": _crit_avg(tq_s, tq_e),
            },
            "late":    {
                "coord":     _phase_avg(rows, "coord_failure_rate",    late_s, MISSION_DAYS),
                "checklist": _phase_avg(rows, "checklist_miss_rate",   late_s, MISSION_DAYS),
                "planning":  _phase_avg(rows, "planning_error_rate",   late_s, MISSION_DAYS),
                "maint":     _phase_avg(rows, "maintenance_skip_rate", late_s, MISSION_DAYS),
                "critical_completion": _crit_avg(late_s, MISSION_DAYS),
            },
        }

    all_rows = list(data.values())
    task_perf = {
        "fragile_no_mc": _tp(all_rows[0]["rows"]),
        "fragile_mc":    _tp(all_rows[1]["rows"]),
        "high_cohesion": _tp(all_rows[2]["rows"]),
    }

    # KPI stats
    fragile_no_mc_rows = all_rows[0]["rows"]
    fragile_mc_rows    = all_rows[1]["rows"]
    hc_rows            = all_rows[2]["rows"]

    peak_no_mc  = _peak(fragile_no_mc_rows, "strain")
    peak_mc     = _peak(fragile_mc_rows,    "strain")
    peak_hc     = _peak(hc_rows,            "strain")
    mc_red      = _pct_reduction(peak_no_mc, peak_mc)
    hc_red      = _pct_reduction(peak_no_mc, peak_hc)

    return _HTML_TEMPLATE.format(
        crew_size=4,
      mission_days=MISSION_DAYS,
        peak_strain_fragile=peak_no_mc,
        mc_reduction=mc_red,
        hc_reduction=hc_red,
        mc_freq=MC_COMMS_FREQ,
        mc_start=MC_COMMS_START_DAY,
        seed=DEMO_SEED,
        days_json=json.dumps(days),
        labels_json=json.dumps(labels),
        colors_json=json.dumps(colors),
        dashes_json=json.dumps(dashes),
        strain_json=json.dumps(strain_series),
        cohesion_json=json.dumps(cohesion_series),
        monotony_json=json.dumps(monotony_series),
        tq_json=json.dumps(tq_series),
        social_json=json.dumps(social_series),
        social_days_json=json.dumps(social_days),
        task_perf_json=json.dumps(task_perf),
        tq_start=int(0.5 * MISSION_DAYS),
        tq_end=int(0.75 * MISSION_DAYS),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("3QP — HTML Demo Report Generator")
    print("=" * 60)
    print(f"\nMission: {MISSION_DAYS} days | Crew: 4 astronauts")
    print(f"MC support: reassurance every {MC_COMMS_FREQ} days from day {MC_COMMS_START_DAY}")
    print()

    data = collect_data()

    print("\nGenerating HTML report...")
    html = generate_html(data)

    Path(REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Report saved: {REPORT_PATH}")
    print("\nDone. Open demo_report.html in any browser.")


if __name__ == "__main__":
    main()
