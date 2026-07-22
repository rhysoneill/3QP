"""
Fingerprint Operations Demo

Demonstrates usage of FingerprintSchema, FingerprintComparator, and FingerprintGrouper
for analyzing and comparing mission collapse signatures.

This script shows:
1. Creating FingerprintSchema objects from simulation runs
2. Computing distance and similarity between fingerprints
3. Finding nearest neighbors
4. Grouping fingerprints by various criteria
5. Saving and loading fingerprints
"""

import sys
from pathlib import Path
from datetime import datetime

# Add fingerprinting module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fingerprinting import (
    FingerprintSchema,
    FingerprintComparator,
    FingerprintGrouper,
    CollapseFingerprint,
    load_fingerprints_from_directory,
    save_fingerprint_collection,
)


def create_example_fingerprints() -> list:
    """Create example fingerprints for demonstration."""
    
    # Example 1: Early collapse, deep failure
    fp1 = CollapseFingerprint(
        collapse_timing=0.23,
        collapse_depth=0.15,
        collapse_day=41,
        fractiousness_index=0.42,
        weakest_pairs=[
            {"member_i": 0, "member_j": 3, "min_cohesion": 0.12, "min_cohesion_day": 40, "min_cohesion_progress": 0.22, "compatibility_score": 0.35, "final_cohesion": 0.18}
        ],
        risk_score=0.82,
        risk_category="high risk",
        metadata={"mission_length_days": 180}
    )
    
    schema1 = FingerprintSchema(
        fingerprint=fp1,
        mission_name="mars_mission_alpha",
        crew_id="crew_001",
        timestamp=datetime.now().isoformat(),
        run_metadata={"scenario": "baseline", "crew_size": 6}
    )
    
    # Example 2: Late collapse, moderate failure
    fp2 = CollapseFingerprint(
        collapse_timing=0.72,
        collapse_depth=0.45,
        collapse_day=129,
        fractiousness_index=0.28,
        weakest_pairs=[
            {"member_i": 1, "member_j": 4, "min_cohesion": 0.38, "min_cohesion_day": 128, "min_cohesion_progress": 0.71, "compatibility_score": 0.52, "final_cohesion": 0.41}
        ],
        risk_score=0.38,
        risk_category="moderate risk",
        metadata={"mission_length_days": 180}
    )
    
    schema2 = FingerprintSchema(
        fingerprint=fp2,
        mission_name="mars_mission_beta",
        crew_id="crew_002",
        timestamp=datetime.now().isoformat(),
        run_metadata={"scenario": "baseline", "crew_size": 6}
    )
    
    # Example 3: Mid-mission collapse, shallow failure
    fp3 = CollapseFingerprint(
        collapse_timing=0.48,
        collapse_depth=0.62,
        collapse_day=86,
        fractiousness_index=0.15,
        weakest_pairs=[
            {"member_i": 2, "member_j": 5, "min_cohesion": 0.58, "min_cohesion_day": 85, "min_cohesion_progress": 0.47, "compatibility_score": 0.68, "final_cohesion": 0.65}
        ],
        risk_score=0.25,
        risk_category="low risk",
        metadata={"mission_length_days": 180}
    )
    
    schema3 = FingerprintSchema(
        fingerprint=fp3,
        mission_name="mars_mission_gamma",
        crew_id="crew_003",
        timestamp=datetime.now().isoformat(),
        run_metadata={"scenario": "baseline", "crew_size": 6}
    )
    
    # Example 4: Similar to Example 1 (early, deep)
    fp4 = CollapseFingerprint(
        collapse_timing=0.28,
        collapse_depth=0.18,
        collapse_day=50,
        fractiousness_index=0.38,
        weakest_pairs=[
            {"member_i": 0, "member_j": 2, "min_cohesion": 0.15, "min_cohesion_day": 49, "min_cohesion_progress": 0.27, "compatibility_score": 0.42, "final_cohesion": 0.22}
        ],
        risk_score=0.78,
        risk_category="high risk",
        metadata={"mission_length_days": 180}
    )
    
    schema4 = FingerprintSchema(
        fingerprint=fp4,
        mission_name="mars_mission_delta",
        crew_id="crew_004",
        timestamp=datetime.now().isoformat(),
        run_metadata={"scenario": "high_stress", "crew_size": 6}
    )
    
    return [schema1, schema2, schema3, schema4]


def demo_comparison():
    """Demonstrate fingerprint comparison operations."""
    print("=" * 70)
    print("FINGERPRINT COMPARISON DEMO")
    print("=" * 70)
    
    fingerprints = create_example_fingerprints()
    comparator = FingerprintComparator()
    
    print("\n1. COMPUTING PAIRWISE DISTANCES\n")
    
    for i in range(len(fingerprints)):
        for j in range(i + 1, len(fingerprints)):
            fp1 = fingerprints[i]
            fp2 = fingerprints[j]
            
            distance = comparator.compute_distance(fp1, fp2)
            similarity = comparator.compute_similarity(fp1, fp2)
            
            print(f"{fp1.mission_name} <-> {fp2.mission_name}")
            print(f"  Distance:   {distance:.4f}")
            print(f"  Similarity: {similarity:.4f}")
            print()
    
    print("\n2. FINDING NEAREST NEIGHBORS\n")
    
    target = fingerprints[0]
    neighbors = comparator.find_nearest_neighbors(target, fingerprints, k=3)
    
    print(f"Target: {target.mission_name}")
    print(f"  Timing: {target.fingerprint.collapse_timing:.2f}")
    print(f"  Depth:  {target.fingerprint.collapse_depth:.2f}")
    print(f"  Risk:   {target.fingerprint.risk_category}")
    print()
    print("Nearest neighbors:")
    for neighbor, dist in neighbors:
        print(f"  {neighbor.mission_name} (distance: {dist:.4f})")
        print(f"    Timing: {neighbor.fingerprint.collapse_timing:.2f}")
        print(f"    Depth:  {neighbor.fingerprint.collapse_depth:.2f}")
        print(f"    Risk:   {neighbor.fingerprint.risk_category}")
    print()


def demo_grouping():
    """Demonstrate fingerprint grouping operations."""
    print("=" * 70)
    print("FINGERPRINT GROUPING DEMO")
    print("=" * 70)
    
    fingerprints = create_example_fingerprints()
    grouper = FingerprintGrouper()
    
    print("\n1. GROUP BY RISK CATEGORY\n")
    risk_groups = grouper.group_by_risk_category(fingerprints)
    for category, group in risk_groups.items():
        print(f"{category.upper()}: {len(group)} mission(s)")
        for fp in group:
            print(f"  - {fp.mission_name} (risk_score: {fp.fingerprint.risk_score:.2f})")
    print()
    
    print("\n2. GROUP BY TIMING WINDOW\n")
    timing_groups = grouper.group_by_timing_window(fingerprints)
    for window, group in sorted(timing_groups.items()):
        print(f"{window.upper()}: {len(group)} mission(s)")
        for fp in group:
            print(f"  - {fp.mission_name} (timing: {fp.fingerprint.collapse_timing:.2f})")
    print()
    
    print("\n3. GROUP BY DEPTH RANGE\n")
    depth_groups = grouper.group_by_depth_range(fingerprints, num_bins=3)
    for depth_range, group in sorted(depth_groups.items()):
        print(f"{depth_range}: {len(group)} mission(s)")
        for fp in group:
            print(f"  - {fp.mission_name} (depth: {fp.fingerprint.collapse_depth:.2f})")
    print()
    
    print("\n4. GROUP BY SIMILARITY (threshold=0.8)\n")
    similarity_groups = grouper.group_by_similarity(fingerprints, similarity_threshold=0.8)
    for i, group in enumerate(similarity_groups, 1):
        print(f"Group {i}: {len(group)} mission(s)")
        for fp in group:
            print(f"  - {fp.mission_name}")
    print()


def demo_serialization():
    """Demonstrate saving and loading fingerprints."""
    print("=" * 70)
    print("FINGERPRINT SERIALIZATION DEMO")
    print("=" * 70)
    
    fingerprints = create_example_fingerprints()
    output_dir = Path(__file__).parent / "demo_output"
    
    print("\n1. SAVING FINGERPRINTS\n")
    saved_paths = save_fingerprint_collection(fingerprints, output_dir)
    print(f"Saved {len(saved_paths)} fingerprints to {output_dir}")
    for path in saved_paths:
        print(f"  - {path.name}")
    print()
    
    print("\n2. LOADING FINGERPRINTS\n")
    loaded = load_fingerprints_from_directory(output_dir)
    print(f"Loaded {len(loaded)} fingerprints from {output_dir}")
    for fp in loaded:
        print(f"  - {fp.mission_name} (risk: {fp.fingerprint.risk_category})")
    print()
    
    print("\n3. VERIFYING ROUND-TRIP\n")
    for original, reloaded in zip(fingerprints, loaded):
        match = (
            original.mission_name == reloaded.mission_name and
            original.fingerprint.collapse_timing == reloaded.fingerprint.collapse_timing and
            original.fingerprint.collapse_depth == reloaded.fingerprint.collapse_depth and
            original.fingerprint.risk_score == reloaded.fingerprint.risk_score
        )
        status = "✓" if match else "✗"
        print(f"  {status} {original.mission_name}")
    print()


def main():
    """Run all demonstrations."""
    demo_comparison()
    print("\n" * 2)
    demo_grouping()
    print("\n" * 2)
    demo_serialization()
    
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nFingerprintSchema provides:")
    print("  ✓ First-class fingerprint objects with provenance")
    print("  ✓ Distance/similarity metrics for comparison")
    print("  ✓ Nearest neighbor search")
    print("  ✓ Grouping by risk, timing, depth, and similarity")
    print("  ✓ JSON serialization for persistence")
    print("\nReady for Phase B: Action/Intent Hooks")
    print()


if __name__ == "__main__":
    main()
