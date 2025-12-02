"""
Serialization backend for log records.

Handles conversion of log entries to JSON Lines format with optional compression.
"""

import json
import gzip
from typing import Dict, Any, List, BinaryIO, TextIO
from pathlib import Path
from .types import LogEntry


class Serializer:
    """
    Serializer for log records to JSON Lines format.
    
    Supports deterministic serialization with consistent field ordering
    and optional gzip compression.
    """
    
    def __init__(self, compression: str = "none"):
        """
        Initialize serializer.
        
        Args:
            compression: Compression method ("gzip" or "none")
        """
        if compression not in ["gzip", "none"]:
            raise ValueError(f"Unsupported compression: {compression}")
        self.compression = compression
    
    def serialize_entry(self, entry: LogEntry) -> str:
        """
        Serialize a single log entry to JSON string.
        
        Args:
            entry: Log entry to serialize
            
        Returns:
            JSON string (single line, no newline)
        """
        entry_dict = entry.to_dict()
        
        # Use sort_keys=True for deterministic serialization
        # Use separators for compact output
        json_str = json.dumps(
            entry_dict,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False
        )
        
        return json_str
    
    def deserialize_entry(self, json_str: str) -> Dict[str, Any]:
        """
        Deserialize a JSON string to a dictionary.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            Dictionary representation of log entry
        """
        return json.loads(json_str)
    
    def write_to_file(self, entries: List[LogEntry], file_path: Path) -> None:
        """
        Write log entries to a JSON Lines file.
        
        Args:
            entries: List of log entries to write
            file_path: Path to output file
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.compression == "gzip":
            self._write_compressed(entries, file_path)
        else:
            self._write_uncompressed(entries, file_path)
    
    def _write_uncompressed(self, entries: List[LogEntry], file_path: Path) -> None:
        """Write uncompressed JSON Lines."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                json_str = self.serialize_entry(entry)
                f.write(json_str + '\n')
    
    def _write_compressed(self, entries: List[LogEntry], file_path: Path) -> None:
        """Write gzip-compressed JSON Lines."""
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            for entry in entries:
                json_str = self.serialize_entry(entry)
                f.write(json_str + '\n')
    
    def append_to_file(self, entry: LogEntry, file_handle: TextIO) -> None:
        """
        Append a single log entry to an open file handle.
        
        Args:
            entry: Log entry to append
            file_handle: Open file handle (must be in text mode)
        """
        json_str = self.serialize_entry(entry)
        file_handle.write(json_str + '\n')
        file_handle.flush()
    
    def read_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Read log entries from a JSON Lines file.
        
        Args:
            file_path: Path to input file
            
        Returns:
            List of log entry dictionaries
        """
        entries = []
        
        if file_path.suffix == '.gz':
            opener = gzip.open
            mode = 'rt'
        else:
            opener = open
            mode = 'r'
        
        with opener(file_path, mode, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    entry_dict = self.deserialize_entry(line)
                    entries.append(entry_dict)
        
        return entries
    
    def get_file_extension(self) -> str:
        """Get the appropriate file extension for this serializer."""
        if self.compression == "gzip":
            return ".jsonl.gz"
        else:
            return ".jsonl"
