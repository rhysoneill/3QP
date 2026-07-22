"""
Tests for TaskPerformanceEngine (task_performance.py).

Covers:
  - Failure probability equations: each vulnerability channel
  - Boundary conditions: zero inputs, saturated inputs
  - Dependency graph: soft penalty, hard penalty, no penalty when dep succeeded
  - Weakest-link coordination amplification
  - Determinism: same seed → same outcomes
  - Aggregate failure-rate computation
  - daily_task_queue rotation
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_performance import (
    TaskPerformanceEngine,
    MissionTask,
    DayTaskOutcomes,
    TaskOutcome,
    daily_task_queue,
    MISSION_TASK_CATALOGUE,
    OUTCOME_COMPLETED,
    OUTCOME_ERROR,
    OUTCOME_DELAYED,
    OUTCOME_SKIPPED,
)
from params import (
    COORD_STRAIN_WEIGHT,
    COORD_WEAKEST_LINK_AMP,
    PLAN_STRAIN_WEIGHT,
    ATTN_SLEEP_BASELINE,
    PERSIST_MONOTONY_WEIGHT,
    DEPENDENCY_FAIL_PENALTY_SOFT,
    DEPENDENCY_FAIL_PENALTY_HARD,
)


class TestDailyTaskQueue(unittest.TestCase):

    def test_returns_three_tasks(self):
        for day in range(1, 22):
            tasks = daily_task_queue(day)
            self.assertEqual(len(tasks), 3, f"Expected 3 tasks on day {day}")

    def test_rotation_repeats_weekly(self):
        for day in range(1, 8):
            t1 = [t.task_id for t in daily_task_queue(day)]
            t2 = [t.task_id for t in daily_task_queue(day + 7)]
            self.assertEqual(t1, t2, f"Rotation mismatch at day {day}")

    def test_all_tasks_in_catalogue(self):
        catalogue_ids = {t.task_id for t in MISSION_TASK_CATALOGUE}
        for day in range(1, 8):
            for task in daily_task_queue(day):
                self.assertIn(task.task_id, catalogue_ids)


class TestDependencyGraph(unittest.TestCase):
    """Dependency graph: prior-day failures elevate fail_prob for dependent tasks."""

    def _force_outcome(self, task_id: str, outcome: str) -> DayTaskOutcomes:
        """Construct a synthetic DayTaskOutcomes with one failed task."""
        return DayTaskOutcomes(
            day=1,
            task_results=[TaskOutcome(
                task_id=task_id,
                criticality="low",
                vulnerability="persistence",
                outcome=outcome,
                failure_prob=0.5,
            )],
            checklist_miss_rate=0.0,
            coordination_failure_rate=0.0,
            planning_error_rate=0.0,
            maintenance_skip_rate=0.0,
            core_strain=0.0,
            core_monotony=0.0,
            sleep_quality=1.0,
            circadian_drift=0.0,
        )

    def test_no_penalty_when_dependency_succeeded(self):
        """If the upstream task completed, no penalty applied."""
        engine = TaskPerformanceEngine(seed=99)
        # hab_repair_plan depends on equipment_inspection
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "habitat_repair_plan")
        prior = self._force_outcome("equipment_inspection", OUTCOME_COMPLETED)

        # Base fail_prob at strain=0.1
        base_fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.1, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={},  # nothing failed
        )
        with_prior_fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.1, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={},
        )
        self.assertAlmostEqual(base_fp, with_prior_fp, places=6)

    def test_soft_penalty_for_delayed_dependency(self):
        """DELAYED upstream task adds DEPENDENCY_FAIL_PENALTY_SOFT to fail_prob."""
        engine = TaskPerformanceEngine(seed=99)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "habitat_repair_plan")

        base_fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.05, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={},
        )
        dep_fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.05, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={"equipment_inspection": OUTCOME_DELAYED},
        )
        self.assertAlmostEqual(dep_fp, min(1.0, base_fp + DEPENDENCY_FAIL_PENALTY_SOFT), places=5)

    def test_hard_penalty_for_error_dependency(self):
        """ERROR upstream task adds DEPENDENCY_FAIL_PENALTY_HARD to fail_prob."""
        engine = TaskPerformanceEngine(seed=99)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "habitat_repair_plan")

        base_fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.05, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={},
        )
        dep_fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.05, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={"equipment_inspection": OUTCOME_ERROR},
        )
        self.assertAlmostEqual(dep_fp, min(1.0, base_fp + DEPENDENCY_FAIL_PENALTY_HARD), places=5)

    def test_dependency_penalty_appears_in_trace_on_failure(self):
        """When a task fails due to dependency, the trace records upstream_failed and penalty."""
        engine = TaskPerformanceEngine(seed=99)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "habitat_repair_plan")
        # Saturate strain → fail_prob = 1.0 → guaranteed failure → extra_trace always returned
        _, outcome, _, extra = engine._evaluate_task(
            task, core_strain=10.0, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={"equipment_inspection": OUTCOME_ERROR},
        )
        self.assertNotEqual(outcome, OUTCOME_COMPLETED)
        self.assertIsNotNone(extra)
        self.assertIn("dependency_penalty", extra)
        self.assertAlmostEqual(extra["dependency_penalty"], DEPENDENCY_FAIL_PENALTY_HARD, places=5)
        self.assertEqual(extra["upstream_failed"], ["equipment_inspection"])

    def test_skipped_dependency_applies_soft_penalty(self):
        """SKIPPED upstream task is treated as a soft failure."""
        engine = TaskPerformanceEngine(seed=99)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "habitat_repair_plan")
        dep_fp, _, _, extra = engine._evaluate_task(
            task, core_strain=0.05, core_monotony=0.0, sleep_quality=1.0,
            failed_yesterday={"equipment_inspection": OUTCOME_SKIPPED},
        )
        self.assertAlmostEqual(extra["dependency_penalty"], DEPENDENCY_FAIL_PENALTY_SOFT, places=5)

    def test_task_with_no_depends_unaffected(self):
        """A task with no depends_on receives no penalty regardless of prior day."""
        engine = TaskPerformanceEngine(seed=99)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "eva_prep_checklist")
        self.assertEqual(task.depends_on, [])

        fp_clean, _, _, _ = engine._evaluate_task(
            task, core_strain=0.1, core_monotony=0.3, sleep_quality=0.8,
            failed_yesterday={},
        )
        fp_noisy, _, _, extra_noisy = engine._evaluate_task(
            task, core_strain=0.1, core_monotony=0.3, sleep_quality=0.8,
            failed_yesterday={"equipment_inspection": OUTCOME_ERROR,
                              "maintenance_log_review": OUTCOME_SKIPPED},
        )
        self.assertAlmostEqual(fp_clean, fp_noisy, places=5)
        self.assertIsNone(extra_noisy)  # no penalty, no extra trace for deps


class TestWeakestLinkCoordination(unittest.TestCase):

    def test_impairment_amplifies_coordination_fail_prob(self):
        """Higher max_agent_impairment → higher coordination fail_prob."""
        engine = TaskPerformanceEngine(seed=42)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "science_sequence_handoff")

        fp_zero, _, _, _ = engine._evaluate_task(
            task, core_strain=0.10, core_monotony=0.0, sleep_quality=1.0,
            max_agent_impairment=0.0,
        )
        fp_half, _, _, _ = engine._evaluate_task(
            task, core_strain=0.10, core_monotony=0.0, sleep_quality=1.0,
            max_agent_impairment=0.5,
        )
        fp_full, _, _, _ = engine._evaluate_task(
            task, core_strain=0.10, core_monotony=0.0, sleep_quality=1.0,
            max_agent_impairment=1.0,
        )
        self.assertLess(fp_zero, fp_half)
        self.assertLess(fp_half, fp_full)

    def test_coordination_formula(self):
        """Verify: base = strain × COORD_STRAIN_WEIGHT × (1 + impairment × AMP)."""
        engine = TaskPerformanceEngine(seed=42)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "science_sequence_handoff")
        strain = 0.12
        impairment = 0.6
        expected = min(1.0, strain * COORD_STRAIN_WEIGHT * (1.0 + impairment * COORD_WEAKEST_LINK_AMP))
        actual, _, _, _ = engine._evaluate_task(
            task, core_strain=strain, core_monotony=0.0, sleep_quality=1.0,
            max_agent_impairment=impairment,
        )
        self.assertAlmostEqual(actual, expected, places=6)

    def test_weakest_link_agent_recorded_in_trace(self):
        """For a coordination task, extra_trace contains weakest_link_agent when task fails."""
        engine = TaskPerformanceEngine(seed=42)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "science_sequence_handoff")
        # Saturate strain → fail_prob = 1.0 → guaranteed failure → extra_trace returned
        _, outcome, _, extra = engine._evaluate_task(
            task, core_strain=10.0, core_monotony=0.0, sleep_quality=1.0,
            max_agent_impairment=0.7, weakest_link_agent="agent_B",
        )
        self.assertNotEqual(outcome, OUTCOME_COMPLETED)
        self.assertIsNotNone(extra)
        self.assertEqual(extra["weakest_link_agent"], "agent_B")
        self.assertAlmostEqual(extra["max_agent_impairment"], 0.7, places=3)


class TestFailureProbabilityEquations(unittest.TestCase):

    def _make_engine(self):
        return TaskPerformanceEngine(seed=0)

    def test_attention_zero_impairment_gives_zero_prob(self):
        """Perfect sleep and zero monotony → zero attention fail prob."""
        engine = self._make_engine()
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "eva_prep_checklist")
        fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.0, core_monotony=0.0,
            sleep_quality=ATTN_SLEEP_BASELINE,  # exact baseline → zero deficit
        )
        self.assertAlmostEqual(fp, 0.0, places=5)

    def test_persistence_zero_monotony_gives_zero_prob(self):
        engine = self._make_engine()
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "equipment_inspection")
        fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.0, core_monotony=0.0, sleep_quality=1.0,
        )
        self.assertAlmostEqual(fp, 0.0, places=5)

    def test_planning_zero_strain_gives_zero_prob(self):
        engine = self._make_engine()
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "habitat_repair_plan")
        fp, _, _, _ = engine._evaluate_task(
            task, core_strain=0.0, core_monotony=0.0, sleep_quality=1.0,
        )
        self.assertAlmostEqual(fp, 0.0, places=5)

    def test_planning_formula(self):
        engine = self._make_engine()
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "habitat_repair_plan")
        strain = 0.15
        expected = min(1.0, strain * PLAN_STRAIN_WEIGHT)
        actual, _, _, _ = engine._evaluate_task(
            task, core_strain=strain, core_monotony=0.0, sleep_quality=1.0,
        )
        self.assertAlmostEqual(actual, expected, places=6)

    def test_persistence_formula(self):
        engine = self._make_engine()
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "equipment_inspection")
        monotony = 0.4
        expected = min(1.0, monotony * PERSIST_MONOTONY_WEIGHT)
        actual, _, _, _ = engine._evaluate_task(
            task, core_strain=0.0, core_monotony=monotony, sleep_quality=1.0,
        )
        self.assertAlmostEqual(actual, expected, places=6)

    def test_fail_prob_capped_at_one(self):
        """Saturated inputs must not produce fail_prob > 1.0."""
        engine = self._make_engine()
        for task in MISSION_TASK_CATALOGUE:
            fp, _, _, _ = engine._evaluate_task(
                task, core_strain=10.0, core_monotony=10.0, sleep_quality=0.0,
                max_agent_impairment=1.0,
            )
            self.assertLessEqual(fp, 1.0, f"Overflow on task {task.task_id}")
            self.assertGreaterEqual(fp, 0.0, f"Negative fp on task {task.task_id}")

    def test_persistence_fail_mode_is_always_skipped(self):
        engine = TaskPerformanceEngine(seed=77)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "equipment_inspection")
        outcomes = set()
        for _ in range(50):
            _, outcome, _, _ = engine._evaluate_task(
                task, core_strain=0.0, core_monotony=0.9, sleep_quality=1.0,
            )
            outcomes.add(outcome)
        self.assertIn(OUTCOME_SKIPPED, outcomes)
        # Persistence should never produce ERROR or DELAYED
        self.assertNotIn(OUTCOME_ERROR, outcomes)
        self.assertNotIn(OUTCOME_DELAYED, outcomes)

    def test_coordination_fail_mode_is_always_error(self):
        engine = TaskPerformanceEngine(seed=77)
        task = next(t for t in MISSION_TASK_CATALOGUE if t.task_id == "science_sequence_handoff")
        outcomes = set()
        for _ in range(50):
            _, outcome, _, _ = engine._evaluate_task(
                task, core_strain=0.5, core_monotony=0.0, sleep_quality=1.0,
            )
            outcomes.add(outcome)
        failure_outcomes = {o for o in outcomes if o != OUTCOME_COMPLETED}
        # All failures must be ERROR
        self.assertTrue(failure_outcomes.issubset({OUTCOME_ERROR}))


class TestDeterminism(unittest.TestCase):

    def test_same_seed_same_outcomes(self):
        """Two engines with the same seed must produce identical outputs."""
        for trial in range(3):
            e1 = TaskPerformanceEngine(seed=trial)
            e2 = TaskPerformanceEngine(seed=trial)
            for day in range(1, 15):
                r1 = e1.evaluate(day, 0.1, 0.4, 0.8)
                r2 = e2.evaluate(day, 0.1, 0.4, 0.8)
                self.assertEqual(
                    [t.outcome for t in r1.task_results],
                    [t.outcome for t in r2.task_results],
                    f"Outcome mismatch on day {day} with seed {trial}",
                )

    def test_different_seed_different_outcomes(self):
        """Two engines with different seeds should (very likely) differ at some day."""
        e1 = TaskPerformanceEngine(seed=1)
        e2 = TaskPerformanceEngine(seed=2)
        all_same = True
        for day in range(1, 15):
            r1 = e1.evaluate(day, 0.15, 0.5, 0.75)
            r2 = e2.evaluate(day, 0.15, 0.5, 0.75)
            if [t.outcome for t in r1.task_results] != [t.outcome for t in r2.task_results]:
                all_same = False
                break
        self.assertFalse(all_same, "Different seeds produced identical outcomes across 14 days")


class TestAggregateMetrics(unittest.TestCase):

    def test_zero_impairment_all_completed(self):
        """At near-zero impairment, all tasks should complete (over many seeds)."""
        # With zero strain/monotony and perfect sleep, fail_prob is 0 for all tasks
        for seed in range(5):
            engine = TaskPerformanceEngine(seed=seed)
            for day in range(1, 8):
                r = engine.evaluate(day, 0.0, 0.0, ATTN_SLEEP_BASELINE)
                for t in r.task_results:
                    self.assertEqual(
                        t.outcome, OUTCOME_COMPLETED,
                        f"Expected completed at zero impairment; day={day} task={t.task_id}",
                    )

    def test_failure_rates_between_zero_and_one(self):
        engine = TaskPerformanceEngine(seed=42)
        for day in range(1, 8):
            r = engine.evaluate(day, 0.15, 0.5, 0.75)
            self.assertGreaterEqual(r.checklist_miss_rate, 0.0)
            self.assertLessEqual(r.checklist_miss_rate, 1.0)
            self.assertGreaterEqual(r.coordination_failure_rate, 0.0)
            self.assertLessEqual(r.coordination_failure_rate, 1.0)

    def test_causal_traces_only_for_failures(self):
        """causal_traces must contain exactly the non-completed tasks."""
        engine = TaskPerformanceEngine(seed=7)
        for day in range(1, 8):
            r = engine.evaluate(day, 0.20, 0.7, 0.65)
            expected_trace_count = sum(
                1 for t in r.task_results if t.outcome != OUTCOME_COMPLETED
            )
            self.assertEqual(len(r.causal_traces), expected_trace_count)

    def test_to_dict_structure(self):
        """to_dict() output must contain expected top-level keys."""
        engine = TaskPerformanceEngine(seed=0)
        r = engine.evaluate(1, 0.1, 0.3, 0.8)
        d = r.to_dict()
        for key in ("day", "task_results", "metrics", "impairment", "causal_traces"):
            self.assertIn(key, d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
