"""
Event bus for inter-module communication.

Provides publish/subscribe mechanism for modules to communicate
without direct dependencies.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """
    Represents a system event.
    
    Attributes:
        event_type: Type identifier for the event
        source_module: ID of the module that emitted the event
        payload: Event data
        timestamp: When the event was created
        simulation_time: Current simulation time step
    """
    event_type: str
    source_module: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    simulation_time: int = 0


EventHandler = Callable[[Event], None]


class EventBus:
    """
    Event bus for loosely-coupled inter-module communication.
    
    Modules can subscribe to event types and publish events without
    knowing which modules will receive them. This prevents tight coupling
    while enabling necessary coordination.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._enabled = True
        
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to (e.g., "breakthrough_occurred")
            handler: Callback function to invoke when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed handler from event type: {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        if not self._enabled:
            logger.warning("Event bus is disabled, event not published")
            return
        
        # Store in history
        self._event_history.append(event)
        
        # Notify subscribers
        handlers = self._subscribers.get(event.event_type, [])
        logger.debug(
            f"Publishing event '{event.event_type}' from '{event.source_module}' "
            f"to {len(handlers)} subscribers"
        )
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for '{event.event_type}': {e}",
                    exc_info=True
                )
    
    def get_history(
        self,
        event_type: Optional[str] = None,
        source_module: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Retrieve event history.
        
        Args:
            event_type: Filter by event type (optional)
            source_module: Filter by source module (optional)
            limit: Maximum number of events to return (optional)
            
        Returns:
            List of events matching filters
        """
        events = self._event_history
        
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        
        if source_module is not None:
            events = [e for e in events if e.source_module == source_module]
        
        if limit is not None:
            events = events[-limit:]
        
        return events
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()
        logger.debug("Event history cleared")
    
    def disable(self) -> None:
        """Disable the event bus (events will not be published)."""
        self._enabled = False
        logger.info("Event bus disabled")
    
    def enable(self) -> None:
        """Enable the event bus."""
        self._enabled = True
        logger.info("Event bus enabled")
    
    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get the number of subscribers for an event type.
        
        Args:
            event_type: Event type to query
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))
    
    def get_all_event_types(self) -> List[str]:
        """
        Get all event types that have subscribers.
        
        Returns:
            List of event type identifiers
        """
        return list(self._subscribers.keys())
