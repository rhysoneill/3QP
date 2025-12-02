"""
Supporting system components: memory buffer, event scheduler, message bus, RNG manager.
"""

import heapq
import random
from collections import deque
from typing import Dict, List, Any, Optional
from .types import (
    MemoryRecord, ScheduledEvent, ScheduledEventRequest,
    Message, MessageRequest
)


class MemoryBuffer:
    """
    Time-ordered FIFO buffer for agent memory records.
    
    Automatically evicts oldest records when capacity is reached.
    """
    
    def __init__(self, max_size: int):
        """
        Initialize memory buffer.
        
        Args:
            max_size: Maximum number of records to retain
        """
        self.buffer: deque = deque(maxlen=max_size)
        self.max_size = max_size
    
    def add(self, record: MemoryRecord) -> None:
        """
        Add a memory record to the buffer.
        
        Args:
            record: Memory record to add
        """
        self.buffer.append(record)
    
    def add_multiple(self, records: List[MemoryRecord]) -> None:
        """Add multiple memory records."""
        for record in records:
            self.add(record)
    
    def query(self, filters: Optional[Dict[str, Any]] = None) -> List[MemoryRecord]:
        """
        Query memory buffer with optional filters.
        
        Args:
            filters: Dictionary of field-value pairs to match
            
        Returns:
            List of matching memory records
        """
        if filters is None:
            return list(self.buffer)
        
        results = []
        for record in self.buffer:
            match = True
            for key, value in filters.items():
                if key == "event_type" and record.event_type != value:
                    match = False
                    break
                elif key == "source_module" and record.source_module != value:
                    match = False
                    break
                elif key == "min_salience" and record.salience < value:
                    match = False
                    break
                elif key == "max_salience" and record.salience > value:
                    match = False
                    break
                elif key == "min_timestamp" and record.timestamp < value:
                    match = False
                    break
                elif key == "max_timestamp" and record.timestamp > value:
                    match = False
                    break
            
            if match:
                results.append(record)
        
        return results
    
    def get_all(self) -> List[MemoryRecord]:
        """Get all memory records."""
        return list(self.buffer)
    
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)


class EventScheduler:
    """
    Priority queue for scheduled events.
    
    Events are delivered to modules at their designated trigger time.
    """
    
    def __init__(self):
        self.queue: List[tuple] = []  # heap of (trigger_time, event_id, event)
        self._event_counter = 0  # for unique event IDs
    
    def schedule(self, request: ScheduledEventRequest) -> str:
        """
        Schedule a future event.
        
        Args:
            request: Event scheduling request
            
        Returns:
            event_id: Unique identifier for the scheduled event
        """
        event_id = f"evt_{self._event_counter}"
        self._event_counter += 1
        
        event = ScheduledEvent(
            event_id=event_id,
            trigger_time=request.trigger_time,
            event_type=request.event_type,
            event_payload=request.event_payload,
            source_module=request.target_module  # TODO: This should be source, not target
        )
        
        # Use event_id as tiebreaker for stable ordering
        heapq.heappush(self.queue, (event.trigger_time, event_id, event))
        return event_id
    
    def get_events_for_time(self, current_time: int, target_module: Optional[str] = None) -> List[ScheduledEvent]:
        """
        Retrieve all events scheduled for the current time.
        
        Args:
            current_time: Current simulation time
            target_module: Optional filter for specific module
            
        Returns:
            List of scheduled events for this time
        """
        events = []
        
        while self.queue and self.queue[0][0] == current_time:
            _, _, event = heapq.heappop(self.queue)
            
            if target_module is None or event.source_module == target_module or event.source_module == "broadcast":
                events.append(event)
        
        return events
    
    def peek_next_event_time(self) -> Optional[int]:
        """Get the time of the next scheduled event, if any."""
        if self.queue:
            return self.queue[0][0]
        return None


class MessageBus:
    """
    Inter-module message passing system.
    
    Messages are delivered within the same time-step they are sent.
    """
    
    def __init__(self):
        self.pending_messages: List[Message] = []
    
    def send(self, from_module: str, request: MessageRequest) -> None:
        """
        Send a message to another module.
        
        Args:
            from_module: Sender module ID
            request: Message request
        """
        message = Message(
            from_module=from_module,
            to_module=request.to_module,
            message_type=request.message_type,
            message_payload=request.message_payload
        )
        self.pending_messages.append(message)
    
    def get_messages_for_module(self, module_id: str) -> List[Message]:
        """
        Get all messages for a specific module.
        
        Args:
            module_id: Target module ID
            
        Returns:
            List of messages addressed to this module or broadcast
        """
        messages = []
        for msg in self.pending_messages:
            if msg.to_module == module_id or msg.to_module == "broadcast":
                messages.append(msg)
        return messages
    
    def clear(self) -> None:
        """Clear all pending messages (called after time-step completion)."""
        self.pending_messages.clear()


class RNGManager:
    """
    Managed random number generator for deterministic simulation.
    
    Provides a single RNG instance that can be seeded and checkpointed.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize RNG manager.
        
        Args:
            seed: Random seed (None for non-deterministic)
        """
        self.rng = random.Random(seed)
        self._seed = seed
    
    def get_rng(self) -> random.Random:
        """Get the managed RNG instance."""
        return self.rng
    
    def get_state(self) -> tuple:
        """Get current RNG state for checkpointing."""
        return self.rng.getstate()
    
    def set_state(self, state: tuple) -> None:
        """Restore RNG state from checkpoint."""
        self.rng.setstate(state)
    
    def reseed(self, seed: int) -> None:
        """Reset RNG with new seed."""
        self.rng.seed(seed)
        self._seed = seed
