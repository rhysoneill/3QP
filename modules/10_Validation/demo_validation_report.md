# Validation Report

**Report ID:** `validation_0ca5c79b3489`
**System Version:** 3QP-demo-v0.1.0
**Validation Framework Version:** 0.1.0
**Execution Timestamp:** 2025-12-02T08:59:01.785134
**Random Seed:** 12345

## Overall Result

**⚠️ WARNING**

## Executive Summary

- **Critical Failures:** 0
- **Warnings:** 0
- **Modules Validated:** 3
- **Time Steps:** 10
- **Snapshots Analyzed:** 30
- **Validation Duration:** 0.00 ms

## Validation by Category

### ⚠️ STRUCTURAL

- **Result:** WARNING
- **Tests Run:** 3
- **Tests Passed:** 2
- **Tests Failed:** 0
- **Tests Warned:** 1

**Test Details:**

- ✅ `module_initialization`: All 3 modules initialized successfully
- ⚠️ `configuration_validation`: No system configuration provided for validation
- ✅ `schema_compliance`: All 30 snapshots conform to schemas

### ✅ DATA_INTEGRITY

- **Result:** PASS
- **Tests Run:** 3
- **Tests Passed:** 3
- **Tests Failed:** 0
- **Tests Warned:** 0

**Test Details:**

- ✅ `constraint_validation`: No constraint violations in 30 snapshots
- ✅ `data_completeness`: Data completeness: 100.00%
- ✅ `corruption_detection`: No corruption detected in 30 snapshots

### ⚠️ DETERMINISM

- **Result:** WARNING
- **Tests Run:** 1
- **Tests Passed:** 0
- **Tests Failed:** 0
- **Tests Warned:** 1

**Test Details:**

- ⚠️ `reproducibility_check`: Reproducibility validation not performed

### ⚠️ INTEGRATION

- **Result:** WARNING
- **Tests Run:** 2
- **Tests Passed:** 1
- **Tests Failed:** 0
- **Tests Warned:** 1

**Test Details:**

- ⚠️ `message_contracts`: No inter-module messages to validate
- ✅ `data_flow_validation`: Validated data flow for 0 messages

### ⚠️ TEMPORAL

- **Result:** WARNING
- **Tests Run:** 2
- **Tests Passed:** 1
- **Tests Failed:** 0
- **Tests Warned:** 1

**Test Details:**

- ⚠️ `time_step_sequencing`: No time-step metadata available
- ✅ `clock_synchronization`: All modules synchronized across time steps

### ✅ METRIC

- **Result:** PASS
- **Tests Run:** 2
- **Tests Passed:** 2
- **Tests Failed:** 0
- **Tests Warned:** 0

**Test Details:**

- ✅ `metric_ranges`: Validated ranges for 0 metric sets
- ✅ `statistical_properties`: Statistical properties validated

## Module Results

- ✅ **module_01** (`module_01`): PASS
- ✅ **module_02** (`module_02`): PASS
- ✅ **module_03** (`module_03`): PASS

---
*Report generated at 2025-12-02T08:59:01.785574*