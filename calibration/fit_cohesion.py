"""
fit_cohesion.py — Calibrate RuthlessCoreModel parameters to real cohesion data.

Usage (CLI):
    python fit_cohesion.py --data ../data/example_real_cohesion.csv --days 200
    python fit_cohesion.py --data path/to/real_data.csv --days 520 --output fitted.json
    python fit_cohesion.py --data ../data/example_real_cohesion.csv --days 200 --no-scipy

Input CSV format (two columns, day and cohesion, 0–1 normalized):
    day,real_cohesion
    0,1.000
    5,0.980
    ...

Output JSON:
    {
      "fit_metadata": { "rmse": ..., "mse": ..., ... },
      "optimized_params": { "q_center": ..., ... },
      "full_config": { ... all RuthlessCoreConfig params ... }
    }

Optimizer priority:
    1. scipy.optimize.minimize (Nelder-Mead) if scipy is installed
    2. Pure-Python Nelder-Mead simplex (no dependencies)

The 5 parameters being fitted are the ones with the most leverage on
cohesion trajectory shape:
    q_center  — where TQP peak lands (mission fraction)
    q_peak    — amplitude of TQP pressure
    q_width   — width of the Gaussian TQP hump
    c_strain  — cohesion erosion rate from strain
    c_q       — cohesion erosion rate from TQP pressure

All other RuthlessCoreConfig params are held at calibrated defaults.
"""

import sys
import csv
import json
import math
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional

# ---------------------------------------------------------------------------
# Path setup — find ruthless_core relative to this file regardless of cwd
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_CORE = _HERE.parent / "phase4" / "06_Ruthless_Core_Model"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from ruthless_core import RuthlessCoreConfig, RuthlessCoreModel  # noqa: E402

# ---------------------------------------------------------------------------
# Parameter search space
# ---------------------------------------------------------------------------

PARAM_BOUNDS: Dict[str, Tuple[float, float]] = {
    "q_center": (0.50, 0.85),
    "q_peak":   (0.15, 1.20),
    "q_width":  (0.05, 0.30),
    "c_strain": (0.002, 0.060),
    "c_q":      (0.005, 0.100),
}

# Starting point = current RuthlessCoreConfig defaults
PARAM_DEFAULTS: Dict[str, float] = {
    "q_center": 0.62,
    "q_peak":   0.55,
    "q_width":  0.08,
    "c_strain": 0.008,
    "c_q":      0.033,
}

# Secondary params held fixed during fitting (not enough leverage to fit blindly)
_SECONDARY_DEFAULTS: Dict[str, float] = {
    "m_base":          0.008,
    "m_novelty":       0.200,
    "s_workload":      0.030,
    "s_mono":          0.004,
    "s_recovery":      0.040,
    "s_leak":          0.030,
    "c_shared_success": 0.060,
    "c_rebound":       0.010,
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_cohesion_csv(path: str) -> Tuple[List[float], List[float]]:
    """Load day/cohesion pairs from CSV. Returns (days, cohesion_values)."""
    days, cohesion = [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            days.append(float(row["day"]))
            cohesion.append(float(row["real_cohesion"]))
    if not days:
        raise ValueError(f"No data loaded from {path}")
    return days, cohesion


# ---------------------------------------------------------------------------
# Model runner
# ---------------------------------------------------------------------------

def run_model(params: Dict[str, float], mission_length: int) -> Tuple[List[int], List[float]]:
    """Run RuthlessCoreModel with given params. Returns (days, cohesion)."""
    config = RuthlessCoreConfig(
        mission_length_days=mission_length,
        q_center=params["q_center"],
        q_peak=params["q_peak"],
        q_width=params["q_width"],
        c_strain=params["c_strain"],
        c_q=params["c_q"],
    )
    output = RuthlessCoreModel(config).run()
    return output.days, output.cohesion


# ---------------------------------------------------------------------------
# Pure-Python linear interpolation (no numpy)
# ---------------------------------------------------------------------------

def _interp(x: float, xs: List[int], ys: List[float]) -> float:
    """Linear interpolation of ys at x, given sorted xs."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


# ---------------------------------------------------------------------------
# Loss function
# ---------------------------------------------------------------------------

def compute_loss(
    params: Dict[str, float],
    real_days: List[float],
    real_cohesion: List[float],
    mission_length: int,
) -> float:
    """
    MSE of simulated cohesion vs real cohesion at observed days.
    Includes a soft boundary penalty to keep params inside valid ranges.
    """
    # Clamp params before running (prevents model instability at edges)
    clamped = {k: max(lo, min(hi, params[k])) for k, (lo, hi) in PARAM_BOUNDS.items()}

    sim_days, sim_cohesion = run_model(clamped, mission_length)

    sq_errors = []
    for d, rc in zip(real_days, real_cohesion):
        sc = _interp(d, sim_days, sim_cohesion)
        sq_errors.append((rc - sc) ** 2)
    mse = sum(sq_errors) / len(sq_errors)

    # Soft penalty: pushes away from hard boundary edges (within inner 5%)
    penalty = 0.0
    for k, (lo, hi) in PARAM_BOUNDS.items():
        span = hi - lo
        if span > 0:
            norm = (params[k] - lo) / span  # 0..1
            near_lo = max(0.0, 0.05 - norm)
            near_hi = max(0.0, norm - 0.95)
            penalty += 0.001 * (near_lo ** 2 + near_hi ** 2)

    return mse + penalty


def compute_metrics(
    params: Dict[str, float],
    real_days: List[float],
    real_cohesion: List[float],
    mission_length: int,
) -> Dict[str, float]:
    """Compute RMSE, MAE, max_error for a fitted parameter set."""
    sim_days, sim_cohesion = run_model(params, mission_length)
    errors = []
    for d, rc in zip(real_days, real_cohesion):
        sc = _interp(d, sim_days, sim_cohesion)
        errors.append(rc - sc)
    n = len(errors)
    mse = sum(e ** 2 for e in errors) / n
    return {
        "mse":       mse,
        "rmse":      math.sqrt(mse),
        "mae":       sum(abs(e) for e in errors) / n,
        "max_error": max(abs(e) for e in errors),
    }


# ---------------------------------------------------------------------------
# Pure-Python Nelder-Mead simplex optimizer
# ---------------------------------------------------------------------------

def _nelder_mead(
    loss_fn,
    x0: List[float],
    param_names: List[str],
    max_iter: int = 2000,
    tol: float = 1e-7,
    verbose: bool = False,
) -> Tuple[List[float], float]:
    """
    Nelder-Mead simplex optimizer with no external dependencies.
    Returns (best_x_list, best_loss).
    """
    n = len(x0)

    # Build initial simplex: x0 + n perturbed vertices
    simplex = [list(x0)]
    for i in range(n):
        vertex = list(x0)
        lo, hi = PARAM_BOUNDS[param_names[i]]
        step = (hi - lo) * 0.10
        vertex[i] = min(hi, x0[i] + step)
        simplex.append(vertex)

    def f(x):
        params = dict(zip(param_names, x))
        return loss_fn(params)

    scores = [f(v) for v in simplex]

    alpha = 1.0  # reflection coefficient
    gamma = 2.0  # expansion coefficient
    rho   = 0.5  # contraction coefficient
    sigma = 0.5  # shrink coefficient

    for iteration in range(max_iter):
        # Sort simplex by loss (ascending)
        order = sorted(range(n + 1), key=lambda i: scores[i])
        simplex = [simplex[i] for i in order]
        scores  = [scores[i]  for i in order]

        if verbose and iteration % 200 == 0:
            print(f"  iter {iteration:4d}  best_rmse={math.sqrt(scores[0]):.6f}")

        # Convergence: loss spread small enough
        if (scores[-1] - scores[0]) < tol:
            break

        # Centroid of all vertices except the worst
        centroid = [sum(simplex[i][j] for i in range(n)) / n for j in range(n)]

        worst = simplex[-1]

        # Reflection
        reflected = [centroid[j] + alpha * (centroid[j] - worst[j]) for j in range(n)]
        r_score = f(reflected)

        if scores[0] <= r_score < scores[-2]:
            simplex[-1] = reflected
            scores[-1]  = r_score
            continue

        if r_score < scores[0]:
            # Expansion
            expanded = [centroid[j] + gamma * (reflected[j] - centroid[j]) for j in range(n)]
            e_score = f(expanded)
            if e_score < r_score:
                simplex[-1] = expanded
                scores[-1]  = e_score
            else:
                simplex[-1] = reflected
                scores[-1]  = r_score
            continue

        # Contraction
        contracted = [centroid[j] + rho * (worst[j] - centroid[j]) for j in range(n)]
        c_score = f(contracted)
        if c_score < scores[-1]:
            simplex[-1] = contracted
            scores[-1]  = c_score
            continue

        # Shrink: pull all vertices toward the best
        best = simplex[0]
        new_simplex = [best]
        new_scores  = [scores[0]]
        for i in range(1, n + 1):
            shrunk = [best[j] + sigma * (simplex[i][j] - best[j]) for j in range(n)]
            new_simplex.append(shrunk)
            new_scores.append(f(shrunk))
        simplex = new_simplex
        scores  = new_scores

    return simplex[0], scores[0]


# ---------------------------------------------------------------------------
# Main calibration function (importable)
# ---------------------------------------------------------------------------

def calibrate(
    data_path: str,
    mission_length: int,
    output_path: Optional[str] = None,
    use_scipy: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Fit RuthlessCoreConfig parameters to a real cohesion timeseries.

    Args:
        data_path:      Path to CSV with columns 'day' and 'real_cohesion'.
        mission_length: Total mission duration in days.
        output_path:    If set, write result JSON to this path.
        use_scipy:      Try scipy.optimize.minimize first; fall back if unavailable.
        verbose:        Print progress to stdout.

    Returns:
        dict with keys:
            fit_metadata     — data info + error metrics + optimizer used
            optimized_params — the 5 fitted parameter values
            full_config      — complete RuthlessCoreConfig dict ready to use
    """
    if verbose:
        print(f"Loading cohesion data from: {data_path}")

    real_days, real_cohesion = load_cohesion_csv(data_path)

    if verbose:
        print(f"  {len(real_days)} observations  |  "
              f"days {int(real_days[0])}–{int(real_days[-1])}  |  "
              f"cohesion {min(real_cohesion):.3f}–{max(real_cohesion):.3f}")

    param_names = list(PARAM_BOUNDS.keys())
    x0 = [PARAM_DEFAULTS[k] for k in param_names]

    def loss_fn(params):
        return compute_loss(params, real_days, real_cohesion, mission_length)

    optimizer_used = None
    best_params: Dict[str, float] = {}

    # --- Try scipy first ---
    if use_scipy:
        try:
            from scipy.optimize import minimize as _sp_minimize

            if verbose:
                print("Optimizing with scipy Nelder-Mead...")

            def vec_loss(x):
                return loss_fn(dict(zip(param_names, x)))

            result = _sp_minimize(
                vec_loss, x0,
                method="Nelder-Mead",
                options={"maxiter": 3000, "xatol": 1e-7, "fatol": 1e-9, "disp": False},
            )
            raw = list(result.x)
            best_params = {
                k: max(lo, min(hi, raw[i]))
                for i, (k, (lo, hi)) in enumerate(zip(param_names, [PARAM_BOUNDS[p] for p in param_names]))
            }
            optimizer_used = "scipy-nelder-mead"

        except ImportError:
            if verbose:
                print("scipy not available — using pure-Python Nelder-Mead")
            use_scipy = False

    # --- Fall back to pure-Python Nelder-Mead ---
    if not use_scipy:
        if verbose:
            print("Optimizing with pure-Python Nelder-Mead...")

        best_x, _ = _nelder_mead(loss_fn, x0, param_names, max_iter=2000, verbose=verbose)
        best_params = {
            k: max(lo, min(hi, best_x[i]))
            for i, (k, (lo, hi)) in enumerate(zip(param_names, [PARAM_BOUNDS[p] for p in param_names]))
        }
        optimizer_used = "pure-python-nelder-mead"

    # --- Metrics ---
    metrics = compute_metrics(best_params, real_days, real_cohesion, mission_length)

    if verbose:
        print(f"\nFit complete ({optimizer_used}):")
        print(f"  RMSE={metrics['rmse']:.6f}  MAE={metrics['mae']:.6f}  "
              f"max_error={metrics['max_error']:.6f}")
        print(f"  q_center={best_params['q_center']:.4f}  "
              f"q_peak={best_params['q_peak']:.4f}  "
              f"q_width={best_params['q_width']:.4f}")
        print(f"  c_strain={best_params['c_strain']:.5f}  "
              f"c_q={best_params['c_q']:.5f}")

    # --- Build full config dict ---
    full_config = {
        "mission_length_days": mission_length,
        **best_params,
        **_SECONDARY_DEFAULTS,
    }

    result = {
        "fit_metadata": {
            "data_file":          str(data_path),
            "mission_length_days": mission_length,
            "n_observations":     len(real_days),
            "optimizer":          optimizer_used,
            "rmse":               metrics["rmse"],
            "mse":                metrics["mse"],
            "mae":                metrics["mae"],
            "max_error":          metrics["max_error"],
            "fit_timestamp":      datetime.now(timezone.utc).isoformat(),
        },
        "optimized_params": best_params,
        "full_config":      full_config,
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        if verbose:
            print(f"\nSaved to: {out}")

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Calibrate RuthlessCoreModel to real cohesion data."
    )
    parser.add_argument(
        "--data", required=True,
        help="Path to CSV file with columns: day, real_cohesion"
    )
    parser.add_argument(
        "--days", type=int, default=200,
        help="Mission length in days (default: 200)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Path to write fitted config JSON (optional)"
    )
    parser.add_argument(
        "--no-scipy", dest="use_scipy", action="store_false",
        help="Force pure-Python Nelder-Mead even if scipy is available"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress progress output"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    calibrate(
        data_path=args.data,
        mission_length=args.days,
        output_path=args.output,
        use_scipy=args.use_scipy,
        verbose=not args.quiet,
    )
