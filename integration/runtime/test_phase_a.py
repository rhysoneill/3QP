"""
Comprehensive test of Phase A Fingerprint Operations.

Verifies:
1. Fingerprint schema creation and serialization
2. Distance/similarity computation
3. Grouping operations
4. Loading from runtime output
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fingerprinting import (
    FingerprintSchema,
    FingerprintComparator,
    FingerprintGrouper,
    load_fingerprints_from_directory,
)


def test_loading():
    """Test loading fingerprints from output directory."""
    print("TEST 1: Loading fingerprints from output")
    print("-" * 60)
    
    fingerprints = load_fingerprints_from_directory("output")
    print(f"✓ Loaded {len(fingerprints)} fingerprints")
    
    for fp in fingerprints:
        print(f"  - {fp.mission_name}: risk={fp.fingerprint.risk_category}, "
              f"timing={fp.fingerprint.collapse_timing:.2f}")
    
    assert len(fingerprints) > 0, "Should load at least one fingerprint"
    print()
    return fingerprints


def test_comparison(fingerprints):
    """Test distance and similarity computation."""
    print("TEST 2: Distance and similarity computation")
    print("-" * 60)
    
    if len(fingerprints) < 2:
        print("⊘ Skipping (need at least 2 fingerprints)")
        print()
        return
    
    comparator = FingerprintComparator()
    
    fp1, fp2 = fingerprints[0], fingerprints[1]
    distance = comparator.compute_distance(fp1, fp2)
    similarity = comparator.compute_similarity(fp1, fp2)
    
    print(f"✓ {fp1.mission_name} <-> {fp2.mission_name}")
    print(f"  Distance: {distance:.4f}")
    print(f"  Similarity: {similarity:.4f}")
    
    assert 0.0 <= distance, "Distance should be >= 0"
    assert 0.0 <= similarity <= 1.0, "Similarity should be in [0, 1]"
    assert abs(similarity - (1.0 - distance)) < 0.01, "Similarity ≈ 1 - distance"
    
    print()


def test_nearest_neighbors(fingerprints):
    """Test nearest neighbor search."""
    print("TEST 3: Nearest neighbor search")
    print("-" * 60)
    
    if len(fingerprints) < 2:
        print("⊘ Skipping (need at least 2 fingerprints)")
        print()
        return
    
    comparator = FingerprintComparator()
    target = fingerprints[0]
    
    neighbors = comparator.find_nearest_neighbors(target, fingerprints, k=min(3, len(fingerprints) - 1))
    
    print(f"✓ Found {len(neighbors)} nearest neighbors to {target.mission_name}")
    for neighbor, dist in neighbors:
        print(f"  - {neighbor.mission_name}: distance={dist:.4f}")
    
    # Verify distances are sorted
    for i in range(len(neighbors) - 1):
        assert neighbors[i][1] <= neighbors[i+1][1], "Neighbors should be sorted by distance"
    
    print()


def test_grouping_risk(fingerprints):
    """Test grouping by risk category."""
    print("TEST 4: Grouping by risk category")
    print("-" * 60)
    
    grouper = FingerprintGrouper()
    groups = grouper.group_by_risk_category(fingerprints)
    
    total = sum(len(group) for group in groups.values())
    print(f"✓ Grouped {total} fingerprints into {len(groups)} categories")
    
    for category, group in groups.items():
        print(f"  {category}: {len(group)} runs")
    
    assert total == len(fingerprints), "All fingerprints should be grouped"
    print()


def test_grouping_timing(fingerprints):
    """Test grouping by timing window."""
    print("TEST 5: Grouping by timing window")
    print("-" * 60)
    
    grouper = FingerprintGrouper()
    groups = grouper.group_by_timing_window(fingerprints)
    
    total = sum(len(group) for group in groups.values())
    print(f"✓ Grouped {total} fingerprints into {len(groups)} timing windows")
    
    for window, group in sorted(groups.items()):
        print(f"  {window}: {len(group)} runs")
    
    assert total == len(fingerprints), "All fingerprints should be grouped"
    print()


def test_grouping_similarity(fingerprints):
    """Test grouping by similarity."""
    print("TEST 6: Grouping by similarity")
    print("-" * 60)
    
    if len(fingerprints) < 2:
        print("⊘ Skipping (need at least 2 fingerprints)")
        print()
        return
    
    grouper = FingerprintGrouper()
    groups = grouper.group_by_similarity(fingerprints, similarity_threshold=0.85)
    
    total = sum(len(group) for group in groups)
    print(f"✓ Grouped {total} fingerprints into {len(groups)} similarity clusters")
    
    for i, group in enumerate(groups, 1):
        print(f"  Cluster {i}: {len(group)} runs")
    
    assert total == len(fingerprints), "All fingerprints should be grouped"
    print()


def test_serialization(fingerprints):
    """Test round-trip serialization."""
    print("TEST 7: Round-trip serialization")
    print("-" * 60)
    
    if not fingerprints:
        print("⊘ Skipping (no fingerprints available)")
        print()
        return
    
    # Pick first fingerprint
    original = fingerprints[0]
    
    # Save to temp file
    temp_path = Path("output/test_roundtrip.json")
    original.save(temp_path)
    print(f"✓ Saved to {temp_path}")
    
    # Load back
    loaded = FingerprintSchema.load(temp_path)
    print(f"✓ Loaded from {temp_path}")
    
    # Verify key fields match
    assert loaded.mission_name == original.mission_name, "Mission name should match"
    assert loaded.fingerprint.collapse_timing == original.fingerprint.collapse_timing, "Timing should match"
    assert loaded.fingerprint.collapse_depth == original.fingerprint.collapse_depth, "Depth should match"
    assert loaded.fingerprint.risk_score == original.fingerprint.risk_score, "Risk score should match"
    
    print(f"✓ Round-trip verification successful")
    print(f"  Mission: {loaded.mission_name}")
    print(f"  Timing: {loaded.fingerprint.collapse_timing:.4f}")
    print(f"  Depth: {loaded.fingerprint.collapse_depth:.4f}")
    print(f"  Risk: {loaded.fingerprint.risk_score:.4f}")
    
    # Clean up
    temp_path.unlink()
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("PHASE A FINGERPRINT OPERATIONS - COMPREHENSIVE TEST")
    print("=" * 60)
    print()
    
    try:
        fingerprints = test_loading()
        test_comparison(fingerprints)
        test_nearest_neighbors(fingerprints)
        test_grouping_risk(fingerprints)
        test_grouping_timing(fingerprints)
        test_grouping_similarity(fingerprints)
        test_serialization(fingerprints)
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print()
        print("Phase A Fingerprint Operations verified:")
        print("  ✓ FingerprintSchema loading and saving")
        print("  ✓ FingerprintComparator distance/similarity")
        print("  ✓ FingerprintComparator nearest neighbors")
        print("  ✓ FingerprintGrouper risk categorization")
        print("  ✓ FingerprintGrouper timing windows")
        print("  ✓ FingerprintGrouper similarity clustering")
        print("  ✓ JSON serialization round-trip")
        print()
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
