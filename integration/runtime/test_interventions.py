"""
Tests for the 3QP Intervention Library (interventions.py).

Covers:
  - Catalogue completeness and schema
  - make_comm() factory function
  - make_comm_schedule() recurring factory
  - Workload relief factor bounds
  - Cohesion delta present on celebration/peer_check
  - Legacy comm types still resolve
  - Invalid type raises ValueError
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interventions import (
    INTERVENTION_CATALOGUE,
    make_comm,
    make_comm_schedule,
)


REQUIRED_FIELDS = {
    "description",
    "belief_mc_support_delta",
    "belief_resupply_reliability_delta",
    "belief_crew_cohesion_delta",
    "workload_relief_factor",
    "content_template",
}

LEGACY_TYPES = {
    "reassurance", "direction", "support", "acknowledgment", "resupply_announcement"
}

NEW_TYPES = {
    "celebration", "peer_check", "rest_authorization", "schedule_relief"
}


class TestCatalogueSchema(unittest.TestCase):

    def test_all_types_have_required_fields(self):
        for name, spec in INTERVENTION_CATALOGUE.items():
            for field in REQUIRED_FIELDS:
                self.assertIn(field, spec, f"Missing field '{field}' in type '{name}'")

    def test_numeric_fields_in_range(self):
        for name, spec in INTERVENTION_CATALOGUE.items():
            self.assertGreaterEqual(spec["belief_mc_support_delta"], 0.0, name)
            self.assertLessEqual(spec["belief_mc_support_delta"], 0.20, name)
            self.assertGreaterEqual(spec["belief_crew_cohesion_delta"], 0.0, name)
            self.assertLessEqual(spec["belief_crew_cohesion_delta"], 0.20, name)
            self.assertGreaterEqual(spec["workload_relief_factor"], 0.0, name)
            self.assertLessEqual(spec["workload_relief_factor"], 0.30, name)

    def test_legacy_types_present(self):
        for t in LEGACY_TYPES:
            self.assertIn(t, INTERVENTION_CATALOGUE, f"Legacy type '{t}' missing")

    def test_new_types_present(self):
        for t in NEW_TYPES:
            self.assertIn(t, INTERVENTION_CATALOGUE, f"New type '{t}' missing")


class TestMakeComm(unittest.TestCase):

    def test_basic_construction(self):
        comm = make_comm("reassurance", day=50)
        self.assertEqual(comm.day, 50)
        self.assertEqual(comm.message_type, "reassurance")
        self.assertEqual(comm.sender, "mission_control")
        self.assertIsInstance(comm.content, str)
        self.assertGreater(len(comm.content), 10)

    def test_deltas_match_catalogue(self):
        for name in INTERVENTION_CATALOGUE:
            spec = INTERVENTION_CATALOGUE[name]
            comm = make_comm(name, day=1)
            self.assertAlmostEqual(
                comm.belief_mc_support_delta,
                spec["belief_mc_support_delta"], places=6,
                msg=f"mc_support_delta mismatch for '{name}'",
            )
            self.assertAlmostEqual(
                comm.belief_crew_cohesion_delta,
                spec["belief_crew_cohesion_delta"], places=6,
                msg=f"crew_cohesion_delta mismatch for '{name}'",
            )
            self.assertAlmostEqual(
                comm.workload_relief_factor,
                spec["workload_relief_factor"], places=6,
                msg=f"workload_relief_factor mismatch for '{name}'",
            )

    def test_content_override(self):
        custom = "Custom MC message for testing."
        comm = make_comm("direction", day=10, content_override=custom)
        self.assertEqual(comm.content, custom)

    def test_invalid_type_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            make_comm("nonexistent_type", day=1)
        self.assertIn("nonexistent_type", str(ctx.exception))

    def test_celebration_has_cohesion_delta(self):
        comm = make_comm("celebration", day=120)
        self.assertGreater(comm.belief_crew_cohesion_delta, 0.0)

    def test_peer_check_has_cohesion_delta(self):
        comm = make_comm("peer_check", day=80)
        self.assertGreater(comm.belief_crew_cohesion_delta, 0.0)

    def test_rest_authorization_has_workload_relief(self):
        comm = make_comm("rest_authorization", day=100)
        self.assertGreater(comm.workload_relief_factor, 0.0)
        self.assertLessEqual(comm.workload_relief_factor, 0.30)

    def test_schedule_relief_has_workload_relief(self):
        comm = make_comm("schedule_relief", day=100)
        self.assertGreater(comm.workload_relief_factor, 0.0)
        # schedule_relief should be weaker than rest_authorization
        rest = make_comm("rest_authorization", day=100)
        self.assertLess(comm.workload_relief_factor, rest.workload_relief_factor)

    def test_reassurance_no_workload_relief(self):
        comm = make_comm("reassurance", day=50)
        self.assertEqual(comm.workload_relief_factor, 0.0)

    def test_resupply_announcement_has_reliability_delta(self):
        comm = make_comm("resupply_announcement", day=60)
        self.assertGreater(comm.belief_resupply_reliability_delta, 0.0)


class TestMakeCommSchedule(unittest.TestCase):

    def test_returns_correct_count(self):
        schedule = make_comm_schedule("reassurance", start_day=50, interval=10, count=5)
        self.assertEqual(len(schedule), 5)

    def test_days_are_correct(self):
        schedule = make_comm_schedule("reassurance", start_day=100, interval=7, count=4)
        expected_days = [100, 107, 114, 121]
        actual_days = [day for day, _ in schedule]
        self.assertEqual(actual_days, expected_days)

    def test_comms_are_correct_type(self):
        schedule = make_comm_schedule("celebration", start_day=120, interval=30, count=3)
        for day, comm in schedule:
            self.assertEqual(comm.message_type, "celebration")
            self.assertEqual(comm.day, day)

    def test_count_zero_returns_empty(self):
        schedule = make_comm_schedule("support", start_day=50, interval=7, count=0)
        self.assertEqual(schedule, [])

    def test_single_comm_schedule(self):
        schedule = make_comm_schedule("direction", start_day=75, interval=1, count=1)
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0][0], 75)


if __name__ == "__main__":
    unittest.main(verbosity=2)
