"""
Tests for the EventBus component.
"""

import pytest
from architecture import EventBus, Event


def test_event_bus_subscribe_and_publish():
    """Test basic subscribe and publish functionality."""
    bus = EventBus()
    events_received = []
    
    def handler(event: Event):
        events_received.append(event)
    
    bus.subscribe("test_event", handler)
    
    event = Event(
        event_type="test_event",
        source_module="test",
        payload={"data": "value"}
    )
    
    bus.publish(event)
    
    assert len(events_received) == 1
    assert events_received[0].event_type == "test_event"
    assert events_received[0].payload["data"] == "value"


def test_event_bus_multiple_subscribers():
    """Test that multiple subscribers receive the same event."""
    bus = EventBus()
    events1 = []
    events2 = []
    
    bus.subscribe("test_event", lambda e: events1.append(e))
    bus.subscribe("test_event", lambda e: events2.append(e))
    
    event = Event(
        event_type="test_event",
        source_module="test",
        payload={}
    )
    
    bus.publish(event)
    
    assert len(events1) == 1
    assert len(events2) == 1
    assert events1[0] == events2[0]


def test_event_bus_unsubscribe():
    """Test unsubscribing from events."""
    bus = EventBus()
    events = []
    
    def handler(event):
        events.append(event)
    
    bus.subscribe("test_event", handler)
    
    event1 = Event(event_type="test_event", source_module="test", payload={})
    bus.publish(event1)
    
    bus.unsubscribe("test_event", handler)
    
    event2 = Event(event_type="test_event", source_module="test", payload={})
    bus.publish(event2)
    
    assert len(events) == 1  # Only first event received


def test_event_bus_history():
    """Test event history tracking."""
    bus = EventBus()
    
    event1 = Event(event_type="type1", source_module="mod1", payload={})
    event2 = Event(event_type="type2", source_module="mod1", payload={})
    event3 = Event(event_type="type1", source_module="mod2", payload={})
    
    bus.publish(event1)
    bus.publish(event2)
    bus.publish(event3)
    
    # Get all history
    all_history = bus.get_history()
    assert len(all_history) == 3
    
    # Filter by event type
    type1_history = bus.get_history(event_type="type1")
    assert len(type1_history) == 2
    
    # Filter by source module
    mod1_history = bus.get_history(source_module="mod1")
    assert len(mod1_history) == 2
    
    # Filter with limit
    limited_history = bus.get_history(limit=2)
    assert len(limited_history) == 2


def test_event_bus_disable_enable():
    """Test disabling and enabling the event bus."""
    bus = EventBus()
    events = []
    
    bus.subscribe("test_event", lambda e: events.append(e))
    
    bus.disable()
    
    event1 = Event(event_type="test_event", source_module="test", payload={})
    bus.publish(event1)
    
    assert len(events) == 0  # No events while disabled
    
    bus.enable()
    
    event2 = Event(event_type="test_event", source_module="test", payload={})
    bus.publish(event2)
    
    assert len(events) == 1  # Event received after re-enabling


def test_event_bus_error_handling():
    """Test that errors in handlers don't crash the bus."""
    bus = EventBus()
    events_received = []
    
    def failing_handler(event):
        raise ValueError("Handler error")
    
    def working_handler(event):
        events_received.append(event)
    
    bus.subscribe("test_event", failing_handler)
    bus.subscribe("test_event", working_handler)
    
    event = Event(event_type="test_event", source_module="test", payload={})
    bus.publish(event)
    
    # Working handler should still receive the event
    assert len(events_received) == 1


def test_event_bus_subscriber_count():
    """Test getting subscriber count."""
    bus = EventBus()
    
    assert bus.get_subscriber_count("test_event") == 0
    
    bus.subscribe("test_event", lambda e: None)
    assert bus.get_subscriber_count("test_event") == 1
    
    bus.subscribe("test_event", lambda e: None)
    assert bus.get_subscriber_count("test_event") == 2


def test_event_bus_get_all_event_types():
    """Test getting all event types with subscribers."""
    bus = EventBus()
    
    bus.subscribe("event1", lambda e: None)
    bus.subscribe("event2", lambda e: None)
    bus.subscribe("event3", lambda e: None)
    
    event_types = bus.get_all_event_types()
    assert set(event_types) == {"event1", "event2", "event3"}
