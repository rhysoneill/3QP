# Fingerprint Operations - Quick Reference

## Loading Fingerprints

```python
from fingerprinting import load_fingerprints_from_directory

# Load all fingerprints from output directory
fingerprints = load_fingerprints_from_directory("output")

# Load from custom directory with pattern
fingerprints = load_fingerprints_from_directory(
    "my_runs", 
    pattern="fingerprint_schema_*.json"
)
```

## Comparing Fingerprints

```python
from fingerprinting import FingerprintComparator

comparator = FingerprintComparator()

# Compute distance between two fingerprints
distance = comparator.compute_distance(fp1, fp2)

# Compute similarity (1.0 = identical, 0.0 = maximally different)
similarity = comparator.compute_similarity(fp1, fp2)

# Find k nearest neighbors
neighbors = comparator.find_nearest_neighbors(
    target=my_fingerprint,
    candidates=all_fingerprints,
    k=5
)
for neighbor, dist in neighbors:
    print(f"{neighbor.mission_name}: {dist:.4f}")
```

## Grouping Fingerprints

```python
from fingerprinting import FingerprintGrouper

grouper = FingerprintGrouper()

# Group by risk category
risk_groups = grouper.group_by_risk_category(fingerprints)
# Returns: {"high risk": [...], "moderate risk": [...], "low risk": [...]}

# Group by timing window
timing_groups = grouper.group_by_timing_window(fingerprints)
# Returns: {"early": [...], "mid-early": [...], "mid-late": [...], "late": [...]}

# Group by depth range
depth_groups = grouper.group_by_depth_range(fingerprints, num_bins=4)
# Returns: {"0.15-0.30": [...], "0.30-0.45": [...], ...}

# Group by similarity
clusters = grouper.group_by_similarity(fingerprints, similarity_threshold=0.85)
# Returns: [[fp1, fp2], [fp3, fp4, fp5], ...]
```

## Creating Fingerprint Schemas

```python
from fingerprints import FingerprintSchema, CollapseFingerprint
from datetime import datetime

# Create from existing CollapseFingerprint
schema = FingerprintSchema(
    fingerprint=my_collapse_fingerprint,
    mission_name="mars_mission_001",
    crew_id="crew_alpha",
    timestamp=datetime.now().isoformat(),
    run_metadata={
        "scenario": "baseline",
        "crew_size": 6,
        "mission_length_days": 180
    }
)

# Save to file
schema.save("output/fingerprint_schema_mars_mission_001.json")

# Load from file
loaded = FingerprintSchema.load("output/fingerprint_schema_mars_mission_001.json")
```

## Analyzing Existing Runs

```bash
# From command line
cd integration/runtime
python analyze_fingerprints.py --output-dir output

# Options
python analyze_fingerprints.py --output-dir my_runs --quiet
```

## Accessing Fingerprint Data

```python
fp = fingerprints[0]

# Mission metadata
print(fp.mission_name)      # "mars_mission_001"
print(fp.crew_id)            # "crew_alpha"
print(fp.timestamp)          # "2025-12-16T10:30:00"
print(fp.run_metadata)       # {...}

# Collapse metrics
print(fp.fingerprint.collapse_timing)    # 0.62 (mission fraction)
print(fp.fingerprint.collapse_depth)     # 0.45 (cohesion value)
print(fp.fingerprint.collapse_day)       # 112 (day index)
print(fp.fingerprint.risk_score)         # 0.72
print(fp.fingerprint.risk_category)      # "high risk"

# Dyadic metrics (if crew-based)
print(fp.fingerprint.fractiousness_index)  # 0.38
print(fp.fingerprint.weakest_pairs)        # [{...}, {...}]
```

## Common Patterns

### Find Most Risky Runs
```python
high_risk = [fp for fp in fingerprints 
             if fp.fingerprint.risk_category == "high risk"]
high_risk.sort(key=lambda x: x.fingerprint.risk_score, reverse=True)
```

### Find Early Collapse Runs
```python
early_collapse = [fp for fp in fingerprints 
                  if fp.fingerprint.collapse_timing < 0.3]
```

### Find Runs Similar to Target
```python
comparator = FingerprintComparator()
similar = [fp for fp in fingerprints 
           if comparator.compute_similarity(target, fp) > 0.85]
```

### Compare Two Specific Missions
```python
fp1 = next(fp for fp in fingerprints if fp.mission_name == "mission_a")
fp2 = next(fp for fp in fingerprints if fp.mission_name == "mission_b")

dist = comparator.compute_distance(fp1, fp2)
print(f"Distance: {dist:.4f}")
print(f"Timing diff: {abs(fp1.fingerprint.collapse_timing - fp2.fingerprint.collapse_timing):.2f}")
print(f"Depth diff: {abs(fp1.fingerprint.collapse_depth - fp2.fingerprint.collapse_depth):.2f}")
```

## Integration with Simulations

Fingerprint schemas are automatically generated and saved when running simulations:

```bash
cd integration/runtime
python run_simulation.py --mission-name my_mission --days 180
```

This creates:
- `output/my_mission_collapse_fingerprint.json` (legacy format)
- `output/fingerprint_schema_my_mission.json` (Phase A format)

The schema file includes:
- Full collapse metrics
- Run timestamp
- Mission parameters (from RuthlessCoreConfig)
- Trajectory classification
- Crew ID (if crew-based mission)
