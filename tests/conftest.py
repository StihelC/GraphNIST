"""
Test configuration and fixtures for pytest.

This file contains common fixtures and mock objects that can be used across all tests.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPointF

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Global Qt application for all tests
@pytest.fixture(scope="session")
def app():
    """Return a QtApplication instance that will be used for all tests."""
    app = QApplication([])
    yield app
    app.quit()

# Mock Canvas
@pytest.fixture
def mock_canvas():
    """Create a mock canvas for testing."""
    canvas = MagicMock()
    canvas.devices = []
    canvas.connections = []
    canvas.scene.return_value.selectedItems.return_value = []
    return canvas

# Mock Event Bus
@pytest.fixture
def mock_event_bus():
    """Create a mock event bus for testing."""
    event_bus = MagicMock()
    return event_bus

# Mock Undo/Redo Manager
@pytest.fixture
def mock_undo_redo_manager():
    """Create a mock undo/redo manager for testing."""
    manager = MagicMock()
    manager.is_in_command_execution.return_value = False
    return manager

# Mock Device
@pytest.fixture
def mock_device():
    """Create a mock device for testing."""
    device = MagicMock()
    device.name = "MockDevice"
    device.device_type = "router"
    device.connections = []
    device.scenePos.return_value = QPointF(100, 100)
    device.boundingRect.return_value.width.return_value = 50
    device.boundingRect.return_value.height.return_value = 50
    
    # Mock getting nearest port
    device.get_nearest_port = lambda pos: QPointF(120, 120)
    
    # Mock getting center position
    device.get_center_position = lambda: QPointF(125, 125)
    
    return device

# Mock Connection
@pytest.fixture
def mock_connection():
    """Create a mock connection for testing."""
    connection = MagicMock()
    connection.id = "mock-connection-1"
    connection.source_device = MagicMock()
    connection.target_device = MagicMock()
    connection.connection_type = "ethernet"
    return connection 