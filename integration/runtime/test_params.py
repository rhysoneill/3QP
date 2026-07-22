"""
Tests for the 3QP Parameter Registry (params.py).

Covers:
  - All constants are defined and have correct types
  - REGISTRY contains entries for all known constant groups
  - REGISTRY values match the actual constants
  - SCHEMA_VERSION is a valid semver-style string
  - Phase window fractions are logically ordered
  - Coefficient values are within physically plausible ranges
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import params


class TestSchemaVersion(unittest.TestCase):

    def test_schema_version_is_string(self):
        self.assertIsInstance(params.SCHEMA_VERSION, str)

    def test_schema_version_format(self):
        """Should be major.minor (e.g. '1.2')."""
        parts = params.SCHEMA_VERSION.split(".")
        self.assertEqual(len(parts), 2, f"Unexpected version format: {params.SCHEMA_VERSION}")
        self.assertTrue(all(p.isdigit() for p in parts),
                        f"Non-numeric version parts: {params.SCHEMA_VERSION}")


class TestPhaseWindows(unittest.TestCase):

    def test_tq_window_order(self):
        self.assertLess(params.TQ_PHASE_START, params.TQ_PHASE_END)

    def test_late_phase_starts_at_tq_end(self):
        self.assertEqual(params.TQ_PHASE_END, params.LATE_PHASE_START)

    def test_phase_fractions_in_range(self):
        for name in ("TQ_PHASE_START", "TQ_PHASE_END", "LATE_PHASE_START"):
            val = getattr(params, name)
            self.assertGreater(val, 0.0, f"{name} should be > 0")
            self.assertLess(val, 1.0, f"{name} should be < 1")


class TestTaskCoefficients(unittest.TestCase):

    def test_attention_weights_positive(self):
        self.assertGreater(params.ATTN_MONOTONY_WEIGHT, 0.0)
        self.assertGreater(params.ATTN_SLEEP_DEFICIT_WEIGHT, 0.0)

    def test_coordination_weight_greater_than_planning(self):
        """Coordination tasks are more sensitive to strain than planning."""
        self.assertGreater(params.COORD_STRAIN_WEIGHT, params.PLAN_STRAIN_WEIGHT)

    def test_weakest_link_amp_positive(self):
        self.assertGreater(params.COORD_WEAKEST_LINK_AMP, 0.0)

    def test_delay_probs_in_range(self):
        for name in ("ATTN_DELAY_PROB", "PLAN_DELAY_PROB"):
            val = getattr(params, name)
            self.assertGreaterEqual(val, 0.0, name)
            self.assertLessEqual(val, 1.0, name)

    def test_dependency_penalties_ordered(self):
        """Hard penalty (error) must exceed soft penalty (delayed/skipped)."""
        self.assertGreater(params.DEPENDENCY_FAIL_PENALTY_HARD,
                           params.DEPENDENCY_FAIL_PENALTY_SOFT)

    def test_dependency_penalties_positive(self):
        self.assertGreater(params.DEPENDENCY_FAIL_PENALTY_SOFT, 0.0)
        self.assertGreater(params.DEPENDENCY_FAIL_PENALTY_HARD, 0.0)

    def test_dependency_penalties_dont_exceed_half(self):
        """Penalties shouldn't be unrealistically large."""
        self.assertLess(params.DEPENDENCY_FAIL_PENALTY_HARD, 0.50)


class TestSleepAndCircadian(unittest.TestCase):

    def test_sleep_baseline_in_range(self):
        self.assertGreater(params.ATTN_SLEEP_BASELINE, 0.0)
        self.assertLess(params.ATTN_SLEEP_BASELINE, 1.0)

    def test_sleep_debt_decay_in_range(self):
        self.assertGreater(params.SLEEP_DEBT_DECAY_FACTOR, 0.0)
        self.assertLess(params.SLEEP_DEBT_DECAY_FACTOR, 1.0)

    def test_circadian_rates_positive(self):
        self.assertGreater(params.CIRCADIAN_ACCUM_RATE, 0.0)
        self.assertGreater(params.CIRCADIAN_RECOVERY_RATE, 0.0)

    def test_circadian_accumulates_faster_than_recovers(self):
        """Circadian drift is easier to acquire than to reverse."""
        self.assertGreater(params.CIRCADIAN_ACCUM_RATE, params.CIRCADIAN_RECOVERY_RATE)


class TestDyadAndBacklog(unittest.TestCase):

    def test_dyad_decay_in_range(self):
        self.assertGreater(params.DYAD_CONFLICT_DECAY, 0.0)
        self.assertLess(params.DYAD_CONFLICT_DECAY, 1.0)

    def test_dyad_increment_positive(self):
        self.assertGreater(params.DYAD_CONFLICT_INCREMENT, 0.0)

    def test_trust_suppressor_in_range(self):
        self.assertGreater(params.DYAD_TRUST_SUPPRESSOR, 0.0)
        self.assertLessEqual(params.DYAD_TRUST_SUPPRESSOR, 1.0)

    def test_backlog_decay_in_range(self):
        self.assertGreater(params.BACKLOG_NATURAL_DECAY, 0.0)
        self.assertLess(params.BACKLOG_NATURAL_DECAY, 1.0)

    def test_backlog_max_load_positive(self):
        self.assertGreater(params.BACKLOG_MAX_LOAD, 0.0)
        self.assertLessEqual(params.BACKLOG_MAX_LOAD, 0.5)


class TestRegistryCompleteness(unittest.TestCase):

    def test_registry_has_required_groups(self):
        required_groups = {
            "task_failure", "micro_events", "circadian_drift",
            "sleep_debt", "exec_impairment", "effort_quality",
            "compliance_scaling", "per_agent_impairment",
            "backlog_dynamics", "reputation_memory",
        }
        for group in required_groups:
            self.assertIn(group, params.REGISTRY,
                          f"Missing group '{group}' in REGISTRY")

    def test_registry_task_failure_values_match_constants(self):
        tf = params.REGISTRY["task_failure"]
        pairs = [
            ("ATTN_MONOTONY_WEIGHT",    params.ATTN_MONOTONY_WEIGHT),
            ("COORD_STRAIN_WEIGHT",     params.COORD_STRAIN_WEIGHT),
            ("PLAN_STRAIN_WEIGHT",      params.PLAN_STRAIN_WEIGHT),
            ("PERSIST_MONOTONY_WEIGHT", params.PERSIST_MONOTONY_WEIGHT),
            ("DEPENDENCY_FAIL_PENALTY_SOFT", params.DEPENDENCY_FAIL_PENALTY_SOFT),
            ("DEPENDENCY_FAIL_PENALTY_HARD", params.DEPENDENCY_FAIL_PENALTY_HARD),
        ]
        for key, expected in pairs:
            self.assertIn(key, tf, f"'{key}' not in REGISTRY task_failure group")
            self.assertAlmostEqual(
                tf[key]["value"], expected, places=7,
                msg=f"Registry value mismatch for '{key}'",
            )

    def test_registry_entries_have_value_and_desc(self):
        """Every leaf entry with a 'value' key must also have 'desc' and 'units'."""
        def check_node(node, path=""):
            if isinstance(node, dict):
                if "value" in node:
                    self.assertIn("units", node, f"Missing 'units' at {path}")
                    self.assertIn("desc",  node, f"Missing 'desc' at {path}")
                else:
                    for k, v in node.items():
                        if k not in ("schema_version",) and isinstance(v, dict):
                            check_node(v, path=f"{path}.{k}")
        check_node(params.REGISTRY)


if __name__ == "__main__":
    unittest.main(verbosity=2)
