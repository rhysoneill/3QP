"""
Analysis and Validation Routines (D.3)

Demonstrates:
1. Fingerprint stability under narrative variability
2. Predictable fingerprint shifts under counterfactual changes
3. Correlation between action patterns and collapse archetypes

Enables answering: "This outcome changed because X crossed Y."
"""

import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import statistics

from ..data_collector import RunData


class CounterfactualAnalyzer:
    """
    Analyzer for counterfactual experiment results.
    
    Provides methods to demonstrate causal stability, fingerprint shifts,
    and action-collapse correlations.
    """
    
    def __init__(self):
        """Initialize analyzer."""
        self.runs: List[RunData] = []
    
    def load_runs(self, runs: List[RunData]):
        """
        Load run data for analysis.
        
        Args:
            runs: List of RunData objects to analyze
        """
        self.runs = runs
    
    def analyze_narrative_stability(
        self,
        run_ids_with_narrative: List[str],
        run_ids_without_narrative: List[str]
    ) -> Dict[str, Any]:
        """
        Demonstrate fingerprint stability when narrative layer varies.
        
        Compares runs with same configuration but different narrative settings
        to show that narratives do not affect causal outcomes.
        
        Args:
            run_ids_with_narrative: Run IDs with narrative enabled
            run_ids_without_narrative: Run IDs with narrative disabled
            
        Returns:
            Analysis showing fingerprint stability
        """
        # Get runs
        with_narrative = [r for r in self.runs if r.run_id in run_ids_with_narrative]
        without_narrative = [r for r in self.runs if r.run_id in run_ids_without_narrative]
        
        results = {
            "test": "narrative_stability",
            "description": "Fingerprint stability under narrative variability",
            "with_narrative": [],
            "without_narrative": [],
            "differences": [],
        }
        
        # Compare fingerprints
        for run in with_narrative:
            results["with_narrative"].append({
                "run_id": run.run_id,
                "collapse_day": run.get_collapse_day(),
                "collapse_depth": run.get_collapse_depth(),
                "collapse_timing": run.get_collapse_timing(),
            })
        
        for run in without_narrative:
            results["without_narrative"].append({
                "run_id": run.run_id,
                "collapse_day": run.get_collapse_day(),
                "collapse_depth": run.get_collapse_depth(),
                "collapse_timing": run.get_collapse_timing(),
            })
        
        # Calculate differences (should be minimal/zero for same config)
        if with_narrative and without_narrative:
            for wn, won in zip(with_narrative, without_narrative):
                diff = {
                    "pair": f"{wn.run_id} vs {won.run_id}",
                    "collapse_day_diff": abs(wn.get_collapse_day() - won.get_collapse_day()),
                    "collapse_depth_diff": abs(wn.get_collapse_depth() - won.get_collapse_depth()),
                    "timing_matches": wn.get_collapse_timing() == won.get_collapse_timing(),
                }
                results["differences"].append(diff)
        
        return results
    
    def analyze_duration_effects(self, family: str = "mission_duration") -> Dict[str, Any]:
        """
        Analyze how mission duration affects collapse fingerprints.
        
        Shows predictable shifts in collapse timing and depth as duration changes.
        
        Args:
            family: Experiment family to analyze (default: mission_duration)
            
        Returns:
            Analysis of duration effects on fingerprints
        """
        # Filter runs from duration family
        duration_runs = [r for r in self.runs if r.experiment_family == family]
        duration_runs.sort(key=lambda r: r.mission_duration)
        
        results = {
            "test": "duration_effects",
            "description": "Fingerprint shifts under duration changes",
            "runs": [],
            "correlations": {},
        }
        
        # Collect data
        durations = []
        collapse_days = []
        collapse_depths = []
        
        for run in duration_runs:
            durations.append(run.mission_duration)
            collapse_days.append(run.get_collapse_day())
            collapse_depths.append(run.get_collapse_depth())
            
            results["runs"].append({
                "run_id": run.run_id,
                "duration": run.mission_duration,
                "collapse_day": run.get_collapse_day(),
                "collapse_depth": run.get_collapse_depth(),
                "collapse_timing": run.get_collapse_timing(),
                "risk_category": run.get_risk_category(),
            })
        
        # Calculate correlations
        if len(durations) > 1:
            results["correlations"]["duration_vs_collapse_day"] = self._pearson_correlation(
                durations, collapse_days
            )
            results["correlations"]["duration_vs_collapse_depth"] = self._pearson_correlation(
                durations, collapse_depths
            )
        
        # Identify threshold crossings
        results["threshold_crossings"] = self._identify_threshold_crossings(duration_runs)
        
        return results
    
    def analyze_action_collapse_correlation(self) -> Dict[str, Any]:
        """
        Correlate action patterns with collapse archetypes.
        
        Shows which action patterns predict which collapse outcomes.
        
        Returns:
            Analysis of action-collapse correlations
        """
        results = {
            "test": "action_collapse_correlation",
            "description": "Correlation between action patterns and collapse types",
            "by_collapse_timing": defaultdict(lambda: {"runs": [], "action_stats": {}}),
            "by_risk_category": defaultdict(lambda: {"runs": [], "action_stats": {}}),
        }
        
        # Group runs by collapse characteristics
        for run in self.runs:
            timing = run.get_collapse_timing()
            risk = run.get_risk_category()
            
            # Add to timing groups
            results["by_collapse_timing"][timing]["runs"].append(run.run_id)
            
            # Add to risk groups
            results["by_risk_category"][risk]["runs"].append(run.run_id)
            
            # Accumulate action frequencies
            for action_type, count in run.action_frequencies.items():
                if action_type not in results["by_collapse_timing"][timing]["action_stats"]:
                    results["by_collapse_timing"][timing]["action_stats"][action_type] = []
                results["by_collapse_timing"][timing]["action_stats"][action_type].append(count)
                
                if action_type not in results["by_risk_category"][risk]["action_stats"]:
                    results["by_risk_category"][risk]["action_stats"][action_type] = []
                results["by_risk_category"][risk]["action_stats"][action_type].append(count)
        
        # Calculate statistics for each group
        for timing, data in results["by_collapse_timing"].items():
            for action_type, counts in data["action_stats"].items():
                data["action_stats"][action_type] = {
                    "mean": statistics.mean(counts),
                    "median": statistics.median(counts),
                    "stdev": statistics.stdev(counts) if len(counts) > 1 else 0.0,
                }
        
        for risk, data in results["by_risk_category"].items():
            for action_type, counts in data["action_stats"].items():
                data["action_stats"][action_type] = {
                    "mean": statistics.mean(counts),
                    "median": statistics.median(counts),
                    "stdev": statistics.stdev(counts) if len(counts) > 1 else 0.0,
                }
        
        # Convert defaultdicts to regular dicts for JSON serialization
        results["by_collapse_timing"] = dict(results["by_collapse_timing"])
        results["by_risk_category"] = dict(results["by_risk_category"])
        
        return results
    
    def analyze_pre_collapse_sequences(self, window_days: int = 20) -> Dict[str, Any]:
        """
        Analyze action sequences in pre-collapse windows.
        
        Identifies characteristic patterns that precede different collapse types.
        
        Args:
            window_days: Number of days before collapse to analyze
            
        Returns:
            Analysis of pre-collapse action sequences
        """
        results = {
            "test": "pre_collapse_sequences",
            "description": f"Action patterns in {window_days}-day pre-collapse window",
            "by_collapse_timing": defaultdict(lambda: {"sequences": [], "common_patterns": []}),
        }
        
        # Group sequences by collapse timing
        for run in self.runs:
            timing = run.get_collapse_timing()
            
            # Extract action sequence from pre-collapse window
            sequence = [a["action_type"] for a in run.pre_collapse_actions]
            results["by_collapse_timing"][timing]["sequences"].append({
                "run_id": run.run_id,
                "sequence": sequence,
                "length": len(sequence),
            })
        
        # Find common patterns (n-grams)
        for timing, data in results["by_collapse_timing"].items():
            patterns = self._find_common_ngrams(
                [s["sequence"] for s in data["sequences"]],
                n=3
            )
            data["common_patterns"] = patterns[:5]  # Top 5 patterns
        
        results["by_collapse_timing"] = dict(results["by_collapse_timing"])
        
        return results
    
    def generate_causal_explanation(
        self,
        run_id_baseline: str,
        run_id_variant: str
    ) -> Dict[str, Any]:
        """
        Generate causal explanation for why outcomes differ between two runs.
        
        Answers: "This outcome changed because X crossed Y."
        
        Args:
            run_id_baseline: Baseline run ID
            run_id_variant: Variant run ID
            
        Returns:
            Causal explanation with specific threshold crossings
        """
        baseline = next((r for r in self.runs if r.run_id == run_id_baseline), None)
        variant = next((r for r in self.runs if r.run_id == run_id_variant), None)
        
        if not baseline or not variant:
            return {"error": "One or both runs not found"}
        
        explanation = {
            "baseline_run": run_id_baseline,
            "variant_run": run_id_variant,
            "configuration_changes": {},
            "outcome_changes": {},
            "causal_factors": [],
        }
        
        # Identify configuration changes
        if baseline.mission_duration != variant.mission_duration:
            explanation["configuration_changes"]["mission_duration"] = {
                "baseline": baseline.mission_duration,
                "variant": variant.mission_duration,
                "change_pct": (variant.mission_duration - baseline.mission_duration) / baseline.mission_duration * 100,
            }
        
        # Identify outcome changes
        explanation["outcome_changes"]["collapse_day"] = {
            "baseline": baseline.get_collapse_day(),
            "variant": variant.get_collapse_day(),
            "delta": variant.get_collapse_day() - baseline.get_collapse_day(),
        }
        
        explanation["outcome_changes"]["collapse_depth"] = {
            "baseline": baseline.get_collapse_depth(),
            "variant": variant.get_collapse_depth(),
            "delta": variant.get_collapse_depth() - baseline.get_collapse_depth(),
        }
        
        explanation["outcome_changes"]["collapse_timing_changed"] = (
            baseline.get_collapse_timing() != variant.get_collapse_timing()
        )
        
        explanation["outcome_changes"]["risk_category_changed"] = (
            baseline.get_risk_category() != variant.get_risk_category()
        )
        
        # Identify causal factors (based on known thresholds)
        causal_factors = []
        
        # Check if duration change led to timing category change
        if explanation["outcome_changes"]["collapse_timing_changed"]:
            causal_factors.append(
                f"Mission duration change ({baseline.mission_duration} → {variant.mission_duration} days) "
                f"shifted collapse timing from {baseline.get_collapse_timing()} to {variant.get_collapse_timing()}"
            )
        
        # Check if collapse moved across TQ boundary (day 140-160 in 200-day mission)
        baseline_tq_zone = 140 <= baseline.get_collapse_day() <= 160
        variant_tq_zone = 140 <= variant.get_collapse_day() <= 160
        if baseline_tq_zone != variant_tq_zone:
            causal_factors.append(
                f"Collapse {'entered' if variant_tq_zone else 'exited'} Third-Quarter zone "
                f"(day {baseline.get_collapse_day()} → {variant.get_collapse_day()})"
            )
        
        # Check action pattern changes
        baseline_dominant = baseline.get_dominant_action()
        variant_dominant = variant.get_dominant_action()
        if baseline_dominant != variant_dominant:
            causal_factors.append(
                f"Dominant action pattern shifted from {baseline_dominant} to {variant_dominant}"
            )
        
        explanation["causal_factors"] = causal_factors
        
        return explanation
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        
        return numerator / (denominator_x * denominator_y) ** 0.5
    
    def _identify_threshold_crossings(self, runs: List[RunData]) -> List[Dict[str, Any]]:
        """Identify when changing parameters caused threshold crossings."""
        crossings = []
        
        for i in range(len(runs) - 1):
            run_a = runs[i]
            run_b = runs[i + 1]
            
            # Check for timing category changes
            if run_a.get_collapse_timing() != run_b.get_collapse_timing():
                crossings.append({
                    "type": "collapse_timing",
                    "from_run": run_a.run_id,
                    "to_run": run_b.run_id,
                    "from_value": run_a.get_collapse_timing(),
                    "to_value": run_b.get_collapse_timing(),
                    "duration_change": run_b.mission_duration - run_a.mission_duration,
                })
            
            # Check for risk category changes
            if run_a.get_risk_category() != run_b.get_risk_category():
                crossings.append({
                    "type": "risk_category",
                    "from_run": run_a.run_id,
                    "to_run": run_b.run_id,
                    "from_value": run_a.get_risk_category(),
                    "to_value": run_b.get_risk_category(),
                    "duration_change": run_b.mission_duration - run_a.mission_duration,
                })
        
        return crossings
    
    def _find_common_ngrams(
        self,
        sequences: List[List[str]],
        n: int = 3
    ) -> List[Dict[str, Any]]:
        """Find most common n-grams in action sequences."""
        from collections import Counter
        
        ngrams = []
        for sequence in sequences:
            for i in range(len(sequence) - n + 1):
                ngram = tuple(sequence[i:i+n])
                ngrams.append(ngram)
        
        counter = Counter(ngrams)
        most_common = counter.most_common(10)
        
        return [
            {"pattern": list(pattern), "count": count}
            for pattern, count in most_common
        ]
    
    def save_analysis(self, analysis: Dict[str, Any], output_file: Path):
        """
        Save analysis results to JSON file.
        
        Args:
            analysis: Analysis results dictionary
            output_file: Path to output file
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
