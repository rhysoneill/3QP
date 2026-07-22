"""
Fingerprint Analysis Utility

Analyzes fingerprint schemas from simulation runs.

This utility:
1. Loads all fingerprints from output directory
2. Groups them by various criteria
3. Finds similar runs
4. Generates comparison reports

Usage:
    python analyze_fingerprints.py [--output-dir OUTPUT_DIR]
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add fingerprinting module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fingerprinting import (
    FingerprintSchema,
    FingerprintComparator,
    FingerprintGrouper,
    load_fingerprints_from_directory,
)


def analyze_fingerprints(output_dir: Path, verbose: bool = True):
    """
    Analyze all fingerprints in output directory.
    
    Args:
        output_dir: Directory containing fingerprint_schema_*.json files
        verbose: Whether to print detailed output
    """
    # Load all fingerprints
    fingerprints = load_fingerprints_from_directory(output_dir)
    
    if not fingerprints:
        print(f"No fingerprints found in {output_dir}")
        print(f"Looking for files matching pattern: fingerprint_schema_*.json")
        return
    
    print("=" * 80)
    print(f"FINGERPRINT ANALYSIS - {len(fingerprints)} runs loaded")
    print("=" * 80)
    print()
    
    # Section 1: Overview
    print("OVERVIEW")
    print("-" * 80)
    for fp in fingerprints:
        print(f"  {fp.mission_name}")
        print(f"    Risk:   {fp.fingerprint.risk_category} (score: {fp.fingerprint.risk_score:.3f})")
        print(f"    Timing: {fp.fingerprint.collapse_timing:.2f} (day {fp.fingerprint.collapse_day})")
        print(f"    Depth:  {fp.fingerprint.collapse_depth:.3f}")
        if fp.fingerprint.fractiousness_index is not None:
            print(f"    Fract:  {fp.fingerprint.fractiousness_index:.3f}")
        if fp.timestamp:
            print(f"    Time:   {fp.timestamp}")
        print()
    
    # Section 2: Risk Category Groups
    print("\nRISK CATEGORY DISTRIBUTION")
    print("-" * 80)
    grouper = FingerprintGrouper()
    risk_groups = grouper.group_by_risk_category(fingerprints)
    
    for category in ["high risk", "moderate risk", "low risk"]:
        group = risk_groups.get(category, [])
        print(f"{category.upper()}: {len(group)} run(s)")
        for fp in group:
            print(f"  - {fp.mission_name} (risk_score: {fp.fingerprint.risk_score:.3f})")
    print()
    
    # Section 3: Timing Windows
    print("\nTIMING WINDOW DISTRIBUTION")
    print("-" * 80)
    timing_groups = grouper.group_by_timing_window(fingerprints)
    
    for window in ["early", "mid-early", "mid-late", "late"]:
        group = timing_groups.get(window, [])
        print(f"{window.upper()}: {len(group)} run(s)")
        for fp in group:
            print(f"  - {fp.mission_name} (timing: {fp.fingerprint.collapse_timing:.2f})")
    print()
    
    # Section 4: Similarity Clusters
    if len(fingerprints) >= 2:
        print("\nSIMILARITY CLUSTERS (threshold=0.85)")
        print("-" * 80)
        similarity_groups = grouper.group_by_similarity(fingerprints, similarity_threshold=0.85)
        
        for i, group in enumerate(similarity_groups, 1):
            print(f"Cluster {i}: {len(group)} run(s)")
            for fp in group:
                print(f"  - {fp.mission_name}")
                print(f"      Timing: {fp.fingerprint.collapse_timing:.2f}, "
                      f"Depth: {fp.fingerprint.collapse_depth:.3f}, "
                      f"Risk: {fp.fingerprint.risk_category}")
        print()
    
    # Section 5: Pairwise Comparisons
    if len(fingerprints) >= 2:
        print("\nPAIRWISE DISTANCES (top 10 most similar)")
        print("-" * 80)
        comparator = FingerprintComparator()
        
        distances = []
        for i in range(len(fingerprints)):
            for j in range(i + 1, len(fingerprints)):
                fp1 = fingerprints[i]
                fp2 = fingerprints[j]
                dist = comparator.compute_distance(fp1, fp2)
                sim = comparator.compute_similarity(fp1, fp2)
                distances.append((fp1.mission_name, fp2.mission_name, dist, sim))
        
        distances.sort(key=lambda x: x[2])  # Sort by distance (ascending)
        
        for name1, name2, dist, sim in distances[:10]:
            print(f"{name1} <-> {name2}")
            print(f"  Distance: {dist:.4f}, Similarity: {sim:.4f}")
        print()
    
    # Section 6: Outlier Detection
    if len(fingerprints) >= 3:
        print("\nOUTLIER DETECTION (highest avg distance to others)")
        print("-" * 80)
        comparator = FingerprintComparator()
        
        avg_distances = []
        for fp in fingerprints:
            distances = [
                comparator.compute_distance(fp, other)
                for other in fingerprints
                if other.mission_name != fp.mission_name
            ]
            avg_dist = sum(distances) / len(distances) if distances else 0.0
            avg_distances.append((fp, avg_dist))
        
        avg_distances.sort(key=lambda x: x[1], reverse=True)
        
        for fp, avg_dist in avg_distances[:5]:
            print(f"{fp.mission_name}: avg_distance={avg_dist:.4f}")
            print(f"  Timing: {fp.fingerprint.collapse_timing:.2f}, "
                  f"Depth: {fp.fingerprint.collapse_depth:.3f}, "
                  f"Risk: {fp.fingerprint.risk_category}")
        print()
    
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze fingerprint schemas from simulation runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory containing fingerprint schemas (default: output)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        sys.exit(1)
    
    analyze_fingerprints(output_dir, verbose=not args.quiet)


if __name__ == "__main__":
    main()
