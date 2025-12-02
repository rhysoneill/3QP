"""
Index manifest management.

Maintains a catalog of all log batch files with metadata for efficient querying.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .types import BatchMetadata


class IndexManifest:
    """
    Catalog of log batch files with metadata.
    
    Provides efficient lookup of batch files by time-step range,
    module ID, and log type.
    """
    
    def __init__(self, manifest_path: Path):
        """
        Initialize index manifest.
        
        Args:
            manifest_path: Path to manifest JSON file
        """
        self.manifest_path = manifest_path
        self.simulation_id = ""
        self.batches: List[BatchMetadata] = []
        
        # Load existing manifest if it exists
        if manifest_path.exists():
            self._load()
    
    def initialize(self, simulation_id: str) -> None:
        """
        Initialize a new manifest for a simulation run.
        
        Args:
            simulation_id: Unique identifier for simulation
        """
        self.simulation_id = simulation_id
        self.batches = []
        self._save()
    
    def add_batch(self, metadata: BatchMetadata) -> None:
        """
        Add a batch to the manifest.
        
        Args:
            metadata: Batch metadata to add
        """
        self.batches.append(metadata)
        self._save()
    
    def add_batches(self, batch_list: List[BatchMetadata]) -> None:
        """
        Add multiple batches to the manifest.
        
        Args:
            batch_list: List of batch metadata to add
        """
        self.batches.extend(batch_list)
        self._save()
    
    def query_batches(
        self,
        module_id: Optional[str] = None,
        log_type: Optional[str] = None,
        timestamp_start: Optional[int] = None,
        timestamp_end: Optional[int] = None
    ) -> List[BatchMetadata]:
        """
        Query batches by filters.
        
        Args:
            module_id: Filter by module (optional)
            log_type: Filter by log type (optional)
            timestamp_start: Filter by start timestamp (optional)
            timestamp_end: Filter by end timestamp (optional)
            
        Returns:
            List of matching batch metadata
        """
        results = self.batches
        
        if module_id is not None:
            results = [b for b in results if b.module_id == module_id]
        
        if log_type is not None:
            results = [b for b in results if b.log_type == log_type]
        
        if timestamp_start is not None:
            # Include batches that overlap with requested range
            results = [b for b in results if b.timestamp_end >= timestamp_start]
        
        if timestamp_end is not None:
            results = [b for b in results if b.timestamp_start <= timestamp_end]
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics about logged data.
        
        Returns:
            Dictionary with statistics
        """
        if not self.batches:
            return {
                "total_batches": 0,
                "total_records": 0,
                "total_size_bytes": 0,
                "modules": [],
                "log_types": [],
                "timestamp_range": None
            }
        
        total_records = sum(b.record_count for b in self.batches)
        total_size = sum(b.file_size_bytes for b in self.batches)
        modules = sorted(set(b.module_id for b in self.batches))
        log_types = sorted(set(b.log_type for b in self.batches))
        
        min_timestamp = min(b.timestamp_start for b in self.batches)
        max_timestamp = max(b.timestamp_end for b in self.batches)
        
        return {
            "total_batches": len(self.batches),
            "total_records": total_records,
            "total_size_bytes": total_size,
            "modules": modules,
            "log_types": log_types,
            "timestamp_range": (min_timestamp, max_timestamp)
        }
    
    def _load(self) -> None:
        """Load manifest from file."""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.simulation_id = data.get("simulation_id", "")
        
        # Reconstruct BatchMetadata objects
        self.batches = []
        for batch_dict in data.get("batches", []):
            metadata = BatchMetadata(
                file_path=batch_dict["file_path"],
                module_id=batch_dict["module_id"],
                log_type=batch_dict["log_type"],
                timestamp_start=batch_dict["timestamp_start"],
                timestamp_end=batch_dict["timestamp_end"],
                record_count=batch_dict["record_count"],
                file_size_bytes=batch_dict["file_size_bytes"],
                checksum=batch_dict["checksum"],
                compression=batch_dict["compression"],
                status=batch_dict["status"]
            )
            self.batches.append(metadata)
    
    def _save(self) -> None:
        """Save manifest to file."""
        # Ensure directory exists
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary
        manifest_dict = {
            "manifest_version": "1.0.0",
            "simulation_id": self.simulation_id,
            "creation_time": datetime.utcnow().isoformat() + "Z",
            "batches": []
        }
        
        for batch in self.batches:
            batch_dict = {
                "file_path": batch.file_path,
                "module_id": batch.module_id,
                "log_type": batch.log_type,
                "timestamp_start": batch.timestamp_start,
                "timestamp_end": batch.timestamp_end,
                "record_count": batch.record_count,
                "file_size_bytes": batch.file_size_bytes,
                "checksum": batch.checksum,
                "compression": batch.compression,
                "status": batch.status
            }
            manifest_dict["batches"].append(batch_dict)
        
        # Write with pretty formatting
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_dict, f, indent=2, sort_keys=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert manifest to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "manifest_version": "1.0.0",
            "simulation_id": self.simulation_id,
            "batches": [
                {
                    "file_path": b.file_path,
                    "module_id": b.module_id,
                    "log_type": b.log_type,
                    "timestamp_start": b.timestamp_start,
                    "timestamp_end": b.timestamp_end,
                    "record_count": b.record_count,
                    "file_size_bytes": b.file_size_bytes,
                    "checksum": b.checksum,
                    "compression": b.compression,
                    "status": b.status
                }
                for b in self.batches
            ]
        }
