"""
Fingerprint Schema and Operations

Provides:
- FingerprintSchema: First-class object wrapping CollapseFingerprint with metadata
- Comparison utilities: compute distance/similarity between fingerprints
- Grouping utilities: cluster fingerprints by collapse class
- Serialization: save/load fingerprints from disk

This module enables cross-run analysis and crew selection based on
collapse signatures.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import math
from collections import defaultdict

from .collapse_fingerprint import CollapseFingerprint


@dataclass
class FingerprintSchema:
    """
    First-class fingerprint object with provenance and metadata.
    
    Wraps CollapseFingerprint with additional context for comparison
    and analysis across simulation runs.
    
    Attributes:
        fingerprint: The underlying CollapseFingerprint
        mission_name: Identifier for this mission/run
        crew_id: Optional crew identifier for crew-based missions
        timestamp: ISO timestamp when fingerprint was generated
        run_metadata: Additional run-specific context (config, parameters, etc.)
    """
    fingerprint: CollapseFingerprint
    mission_name: str
    crew_id: Optional[str] = None
    timestamp: Optional[str] = None
    run_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize empty metadata if None."""
        if self.run_metadata is None:
            self.run_metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert fingerprint schema to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "mission_name": self.mission_name,
            "crew_id": self.crew_id,
            "timestamp": self.timestamp,
            "run_metadata": self.run_metadata,
            "fingerprint": {
                "collapse_timing": self.fingerprint.collapse_timing,
                "collapse_depth": self.fingerprint.collapse_depth,
                "collapse_day": self.fingerprint.collapse_day,
                "fractiousness_index": self.fingerprint.fractiousness_index,
                "weakest_pairs": self.fingerprint.weakest_pairs,
                "risk_score": self.fingerprint.risk_score,
                "risk_category": self.fingerprint.risk_category,
                "metadata": self.fingerprint.metadata,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FingerprintSchema':
        """
        Load fingerprint schema from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            FingerprintSchema instance
        """
        fp_data = data["fingerprint"]
        fingerprint = CollapseFingerprint(
            collapse_timing=fp_data["collapse_timing"],
            collapse_depth=fp_data["collapse_depth"],
            collapse_day=fp_data["collapse_day"],
            fractiousness_index=fp_data.get("fractiousness_index"),
            weakest_pairs=fp_data.get("weakest_pairs"),
            risk_score=fp_data.get("risk_score"),
            risk_category=fp_data.get("risk_category"),
            metadata=fp_data.get("metadata", {}),
        )
        
        return cls(
            fingerprint=fingerprint,
            mission_name=data["mission_name"],
            crew_id=data.get("crew_id"),
            timestamp=data.get("timestamp"),
            run_metadata=data.get("run_metadata", {}),
        )
    
    def save(self, filepath: Path) -> None:
        """
        Save fingerprint schema to JSON file.
        
        Args:
            filepath: Path to output file
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'FingerprintSchema':
        """
        Load fingerprint schema from JSON file.
        
        Args:
            filepath: Path to input file
            
        Returns:
            FingerprintSchema instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class FingerprintComparator:
    """
    Utilities for comparing fingerprints.
    
    Provides distance metrics and similarity scores for analyzing
    differences between mission collapse signatures.
    """
    
    def __init__(
        self,
        weight_timing: float = 0.35,
        weight_depth: float = 0.35,
        weight_fractiousness: float = 0.30,
    ):
        """
        Initialize comparator with feature weights.
        
        Args:
            weight_timing: Weight for timing difference (default: 0.35)
            weight_depth: Weight for depth difference (default: 0.35)
            weight_fractiousness: Weight for fractiousness difference (default: 0.30)
        """
        self.weight_timing = weight_timing
        self.weight_depth = weight_depth
        self.weight_fractiousness = weight_fractiousness
        
        # Normalize weights
        total = self.weight_timing + self.weight_depth + self.weight_fractiousness
        self.weight_timing /= total
        self.weight_depth /= total
        self.weight_fractiousness /= total
    
    def compute_distance(
        self,
        fp1: FingerprintSchema,
        fp2: FingerprintSchema,
    ) -> float:
        """
        Compute weighted Euclidean distance between two fingerprints.
        
        Distance formula:
            d = sqrt(
                w_t * (timing1 - timing2)^2 +
                w_d * (depth1 - depth2)^2 +
                w_f * (fract1 - fract2)^2
            )
        
        Where fractiousness defaults to 0.0 if not present.
        
        Args:
            fp1: First fingerprint
            fp2: Second fingerprint
            
        Returns:
            Distance value (0.0 = identical, higher = more different)
        """
        # Extract values
        t1 = fp1.fingerprint.collapse_timing
        t2 = fp2.fingerprint.collapse_timing
        
        d1 = fp1.fingerprint.collapse_depth
        d2 = fp2.fingerprint.collapse_depth
        
        f1 = fp1.fingerprint.fractiousness_index or 0.0
        f2 = fp2.fingerprint.fractiousness_index or 0.0
        
        # Compute squared differences
        timing_diff_sq = (t1 - t2) ** 2
        depth_diff_sq = (d1 - d2) ** 2
        fract_diff_sq = (f1 - f2) ** 2
        
        # Weighted Euclidean distance
        distance = math.sqrt(
            self.weight_timing * timing_diff_sq +
            self.weight_depth * depth_diff_sq +
            self.weight_fractiousness * fract_diff_sq
        )
        
        return distance
    
    def compute_similarity(
        self,
        fp1: FingerprintSchema,
        fp2: FingerprintSchema,
        max_distance: float = 1.0,
    ) -> float:
        """
        Compute similarity score between two fingerprints.
        
        Similarity is inverse of distance, normalized to [0.0, 1.0].
        
        Formula:
            similarity = 1 - (distance / max_distance)
        
        Args:
            fp1: First fingerprint
            fp2: Second fingerprint
            max_distance: Maximum expected distance for normalization (default: 1.0)
            
        Returns:
            Similarity score (1.0 = identical, 0.0 = maximally different)
        """
        distance = self.compute_distance(fp1, fp2)
        similarity = 1.0 - min(distance / max_distance, 1.0)
        return similarity
    
    def find_nearest_neighbors(
        self,
        target: FingerprintSchema,
        candidates: List[FingerprintSchema],
        k: int = 5,
    ) -> List[Tuple[FingerprintSchema, float]]:
        """
        Find k nearest neighbors to target fingerprint.
        
        Args:
            target: Target fingerprint
            candidates: List of candidate fingerprints
            k: Number of neighbors to return
            
        Returns:
            List of (fingerprint, distance) tuples, sorted by distance (ascending)
        """
        distances = []
        for candidate in candidates:
            if candidate.mission_name == target.mission_name:
                # Skip self-comparison
                continue
            dist = self.compute_distance(target, candidate)
            distances.append((candidate, dist))
        
        # Sort by distance and return top k
        distances.sort(key=lambda x: x[1])
        return distances[:k]


class FingerprintGrouper:
    """
    Utilities for grouping fingerprints by collapse characteristics.
    
    Enables clustering runs by:
    - Risk category
    - Collapse timing window
    - Collapse depth range
    - Custom similarity thresholds
    """
    
    def group_by_risk_category(
        self,
        fingerprints: List[FingerprintSchema],
    ) -> Dict[str, List[FingerprintSchema]]:
        """
        Group fingerprints by risk category.
        
        Args:
            fingerprints: List of fingerprints to group
            
        Returns:
            Dictionary mapping risk_category -> list of fingerprints
        """
        groups = defaultdict(list)
        for fp in fingerprints:
            category = fp.fingerprint.risk_category or "unknown"
            groups[category].append(fp)
        return dict(groups)
    
    def group_by_timing_window(
        self,
        fingerprints: List[FingerprintSchema],
        window_size: float = 0.25,
    ) -> Dict[str, List[FingerprintSchema]]:
        """
        Group fingerprints by collapse timing windows.
        
        Windows:
        - "early": [0.0, 0.25)
        - "mid-early": [0.25, 0.5)
        - "mid-late": [0.5, 0.75)
        - "late": [0.75, 1.0]
        
        Args:
            fingerprints: List of fingerprints to group
            window_size: Size of timing windows (default: 0.25)
            
        Returns:
            Dictionary mapping window_label -> list of fingerprints
        """
        groups = defaultdict(list)
        for fp in fingerprints:
            timing = fp.fingerprint.collapse_timing
            
            # Determine window
            if timing < window_size:
                label = "early"
            elif timing < 2 * window_size:
                label = "mid-early"
            elif timing < 3 * window_size:
                label = "mid-late"
            else:
                label = "late"
            
            groups[label].append(fp)
        
        return dict(groups)
    
    def group_by_depth_range(
        self,
        fingerprints: List[FingerprintSchema],
        num_bins: int = 4,
    ) -> Dict[str, List[FingerprintSchema]]:
        """
        Group fingerprints by collapse depth ranges.
        
        Creates equal-width bins across the observed depth range.
        
        Args:
            fingerprints: List of fingerprints to group
            num_bins: Number of depth bins (default: 4)
            
        Returns:
            Dictionary mapping depth_range_label -> list of fingerprints
        """
        if not fingerprints:
            return {}
        
        # Find depth range
        depths = [fp.fingerprint.collapse_depth for fp in fingerprints]
        min_depth = min(depths)
        max_depth = max(depths)
        
        # Handle edge case of identical depths
        if min_depth == max_depth:
            return {"all": fingerprints}
        
        # Create bins
        bin_width = (max_depth - min_depth) / num_bins
        groups = defaultdict(list)
        
        for fp in fingerprints:
            depth = fp.fingerprint.collapse_depth
            bin_idx = min(int((depth - min_depth) / bin_width), num_bins - 1)
            
            bin_start = min_depth + bin_idx * bin_width
            bin_end = min_depth + (bin_idx + 1) * bin_width
            label = f"{bin_start:.3f}-{bin_end:.3f}"
            
            groups[label].append(fp)
        
        return dict(groups)
    
    def group_by_similarity(
        self,
        fingerprints: List[FingerprintSchema],
        similarity_threshold: float = 0.8,
        comparator: Optional[FingerprintComparator] = None,
    ) -> List[List[FingerprintSchema]]:
        """
        Group fingerprints by similarity clustering.
        
        Uses single-linkage clustering: two fingerprints are in the same
        group if their similarity >= threshold.
        
        Args:
            fingerprints: List of fingerprints to group
            similarity_threshold: Minimum similarity for same group (default: 0.8)
            comparator: Optional custom comparator (uses default if None)
            
        Returns:
            List of groups, each group is a list of similar fingerprints
        """
        if comparator is None:
            comparator = FingerprintComparator()
        
        # Simple single-linkage clustering
        groups = []
        assigned = set()
        
        for i, fp in enumerate(fingerprints):
            if i in assigned:
                continue
            
            # Start new group
            group = [fp]
            assigned.add(i)
            
            # Find all similar fingerprints
            for j, other_fp in enumerate(fingerprints):
                if j in assigned or i == j:
                    continue
                
                similarity = comparator.compute_similarity(fp, other_fp)
                if similarity >= similarity_threshold:
                    group.append(other_fp)
                    assigned.add(j)
            
            groups.append(group)
        
        return groups


def load_fingerprints_from_directory(
    directory: Path,
    pattern: str = "fingerprint_schema_*.json",
) -> List[FingerprintSchema]:
    """
    Load all fingerprint schemas from a directory.
    
    Args:
        directory: Directory containing fingerprint JSON files
        pattern: Glob pattern for fingerprint files (default: fingerprint_schema_*.json)
        
    Returns:
        List of loaded FingerprintSchema objects
    """
    fingerprints = []
    for filepath in Path(directory).glob(pattern):
        try:
            fp = FingerprintSchema.load(filepath)
            fingerprints.append(fp)
        except Exception as e:
            print(f"Warning: Failed to load {filepath}: {e}")
    
    return fingerprints


def save_fingerprint_collection(
    fingerprints: List[FingerprintSchema],
    output_dir: Path,
    prefix: str = "fingerprint_schema",
) -> List[Path]:
    """
    Save a collection of fingerprints to individual files.
    
    Args:
        fingerprints: List of fingerprints to save
        output_dir: Output directory
        prefix: Filename prefix (default: fingerprint_schema)
        
    Returns:
        List of paths to saved files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    
    for fp in fingerprints:
        filename = f"{prefix}_{fp.mission_name}.json"
        filepath = output_dir / filename
        fp.save(filepath)
        saved_paths.append(filepath)
    
    return saved_paths
