"""
Batch file management for log storage.

Handles creation, rotation, and management of log batch files organized
by module, log type, and time-step range.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, TextIO
from datetime import datetime
from .types import LogEntry, LogType, BatchMetadata
from .serializer import Serializer
from .config import LoggingConfig


class BatchFile:
    """
    Represents an active log batch file.
    
    Manages writing to a single batch file until it reaches capacity,
    then closes and optionally compresses.
    """
    
    def __init__(
        self,
        module_id: str,
        log_type: str,
        timestamp_start: int,
        batch_size: int,
        output_dir: Path,
        serializer: Serializer
    ):
        """
        Initialize batch file.
        
        Args:
            module_id: Module producing these logs
            log_type: Type of logs in this batch
            timestamp_start: Starting time-step for this batch
            batch_size: Number of time-steps per batch
            output_dir: Base directory for log files
            serializer: Serializer instance for writing
        """
        self.module_id = module_id
        self.log_type = log_type
        self.timestamp_start = timestamp_start
        self.timestamp_end = timestamp_start + batch_size - 1
        self.batch_size = batch_size
        self.output_dir = output_dir
        self.serializer = serializer
        
        self.record_count = 0
        self.file_handle: Optional[TextIO] = None
        self.file_path: Optional[Path] = None
        self.is_closed = False
        
        self._open_file()
    
    def _open_file(self) -> None:
        """Open the batch file for writing."""
        # Create directory structure: output_dir/log_type/
        log_dir = self.output_dir / self.log_type
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename: {module_id}_{log_type}_{start:08d}_{end:08d}.jsonl
        filename = (
            f"{self.module_id}_{self.log_type}_"
            f"{self.timestamp_start:08d}_{self.timestamp_end:08d}.jsonl"
        )
        
        self.file_path = log_dir / filename
        self.file_handle = open(self.file_path, 'w', encoding='utf-8')
    
    def write_entry(self, entry: LogEntry) -> bool:
        """
        Write a log entry to the batch file.
        
        Args:
            entry: Log entry to write
            
        Returns:
            True if entry was written, False if batch is full/closed
        """
        if self.is_closed or self.file_handle is None:
            return False
        
        self.serializer.append_to_file(entry, self.file_handle)
        self.record_count += 1
        
        return True
    
    def should_rotate(self, current_timestamp: int) -> bool:
        """
        Check if batch should rotate based on time-step.
        
        Args:
            current_timestamp: Current simulation time-step
            
        Returns:
            True if rotation needed
        """
        return current_timestamp > self.timestamp_end
    
    def close(self) -> BatchMetadata:
        """
        Close the batch file and generate metadata.
        
        Returns:
            BatchMetadata for this batch
        """
        if self.file_handle is not None:
            self.file_handle.close()
            self.file_handle = None
        
        self.is_closed = True
        
        # Calculate file size and checksum
        file_size = 0
        checksum = ""
        
        if self.file_path and self.file_path.exists():
            file_size = self.file_path.stat().st_size
            checksum = self._calculate_checksum()
        
        metadata = BatchMetadata(
            file_path=str(self.file_path.relative_to(self.output_dir)),
            module_id=self.module_id,
            log_type=self.log_type,
            timestamp_start=self.timestamp_start,
            timestamp_end=self.timestamp_end,
            record_count=self.record_count,
            file_size_bytes=file_size,
            checksum=checksum,
            compression="none",
            status="closed"
        )
        
        return metadata
    
    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of file contents."""
        if not self.file_path or not self.file_path.exists():
            return ""
        
        sha256 = hashlib.sha256()
        
        with open(self.file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def compress(self, compression_format: str = "gzip") -> None:
        """
        Compress the closed batch file.
        
        Args:
            compression_format: Compression method
        """
        if not self.is_closed or not self.file_path:
            return
        
        if compression_format != "gzip":
            return  # Only gzip supported currently
        
        import gzip
        import shutil
        
        compressed_path = self.file_path.with_suffix('.jsonl.gz')
        
        with open(self.file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        self.file_path.unlink()
        self.file_path = compressed_path


class BatchManager:
    """
    Manages multiple batch files organized by module and log type.
    
    Handles creation, rotation, and tracking of batch files.
    """
    
    def __init__(self, config: LoggingConfig, serializer: Serializer):
        """
        Initialize batch manager.
        
        Args:
            config: Logging configuration
            serializer: Serializer for writing logs
        """
        self.config = config
        self.serializer = serializer
        
        # Track active batch files: (module_id, log_type) -> BatchFile
        self.active_batches: Dict[tuple, BatchFile] = {}
        
        # Track completed batches
        self.completed_batches: List[BatchMetadata] = []
    
    def get_batch(
        self,
        module_id: str,
        log_type: str,
        timestamp: int
    ) -> BatchFile:
        """
        Get or create a batch file for the given module, log type, and timestamp.
        
        Args:
            module_id: Module identifier
            log_type: Log type
            timestamp: Current time-step
            
        Returns:
            Active BatchFile instance
        """
        key = (module_id, log_type)
        
        # Check if we have an active batch
        if key in self.active_batches:
            batch = self.active_batches[key]
            
            # Check if rotation needed
            if batch.should_rotate(timestamp):
                self._rotate_batch(key, timestamp)
                batch = self.active_batches[key]
        else:
            # Create new batch
            batch = self._create_batch(module_id, log_type, timestamp)
            self.active_batches[key] = batch
        
        return batch
    
    def _create_batch(
        self,
        module_id: str,
        log_type: str,
        timestamp: int
    ) -> BatchFile:
        """Create a new batch file."""
        # Calculate batch start (align to batch_size boundary)
        batch_start = (timestamp // self.config.batch_size) * self.config.batch_size
        
        batch = BatchFile(
            module_id=module_id,
            log_type=log_type,
            timestamp_start=batch_start,
            batch_size=self.config.batch_size,
            output_dir=self.config.output_directory,
            serializer=self.serializer
        )
        
        return batch
    
    def _rotate_batch(self, key: tuple, new_timestamp: int) -> None:
        """Close current batch and create new one."""
        module_id, log_type = key
        
        # Close existing batch
        old_batch = self.active_batches[key]
        metadata = old_batch.close()
        
        # Compress if enabled
        if self.config.enable_compression:
            old_batch.compress(self.config.compression_format)
            metadata.compression = self.config.compression_format
            # Update file path in metadata
            metadata.file_path = str(old_batch.file_path.relative_to(self.config.output_directory))
            metadata.file_size_bytes = old_batch.file_path.stat().st_size
            metadata.checksum = old_batch._calculate_checksum()
        
        self.completed_batches.append(metadata)
        
        # Create new batch
        new_batch = self._create_batch(module_id, log_type, new_timestamp)
        self.active_batches[key] = new_batch
    
    def close_all(self) -> None:
        """Close all active batches."""
        for key, batch in list(self.active_batches.items()):
            metadata = batch.close()
            
            if self.config.enable_compression:
                batch.compress(self.config.compression_format)
                metadata.compression = self.config.compression_format
                metadata.file_path = str(batch.file_path.relative_to(self.config.output_directory))
                metadata.file_size_bytes = batch.file_path.stat().st_size
                metadata.checksum = batch._calculate_checksum()
            
            self.completed_batches.append(metadata)
        
        self.active_batches.clear()
    
    def get_completed_batches(self) -> List[BatchMetadata]:
        """Get list of completed batch metadata."""
        return self.completed_batches.copy()
