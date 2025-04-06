"""
Unit tests for the ConnectionController class.

These tests focus on ensuring that the connection controller properly prevents duplicate
connections between devices, which was a bug we recently fixed.
"""

import pytest
from unittest.mock import MagicMock, patch

from controllers.connection_controller import ConnectionController
from models.connection import Connection
from constants import ConnectionTypes, RoutingStyle

class TestConnectionController:
    """Test suite for ConnectionController."""
    
    @pytest.mark.unit
    def test_connection_exists_both_directions(self, mock_canvas, mock_event_bus, mock_device):
        """Test that _connection_exists checks connections in both directions."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus)
        
        # Create two mock devices
        device1 = mock_device
        device2 = MagicMock()
        device2.name = "Device2"
        device2.get_center_position = lambda: None
        device2.get_nearest_port = lambda pos: None
        
        # Create a mock connection from device1 to device2
        connection = MagicMock()
        connection.source_device = device1
        connection.target_device = device2
        
        # Add the connection to the mock canvas
        mock_canvas.connections = [connection]
        
        # Test that connection exists from device1 to device2
        assert controller._connection_exists(device1, device2) == True
        
        # Test that connection is detected in reverse direction too (device2 to device1)
        assert controller._connection_exists(device2, device1) == True
    
    @pytest.mark.unit
    def test_add_connection_prevents_duplicates(self, mock_canvas, mock_event_bus, mock_undo_redo_manager):
        """Test that on_add_connection_requested prevents duplicate connections."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus, mock_undo_redo_manager)
        
        # Create two mock devices
        device1 = MagicMock()
        device1.name = "Device1"
        device1.get_center_position = lambda: None
        device1.get_nearest_port = lambda pos: None
        
        device2 = MagicMock()
        device2.name = "Device2"
        device2.get_center_position = lambda: None
        device2.get_nearest_port = lambda pos: None
        
        # Create a mock connection that will be returned by our patched _connection_exists
        connection = MagicMock()
        connection.source_device = device1
        connection.target_device = device2
        
        # Add the connection to the mock canvas
        mock_canvas.connections = [connection]
        
        # Now try to add a connection between the same devices
        result = controller.on_add_connection_requested(device1, device2)
        
        # The connection should be rejected because it already exists
        assert result == False
        
        # Also check the reverse direction
        result = controller.on_add_connection_requested(device2, device1)
        
        # Should also be rejected
        assert result == False
        
        # Make sure the undo_redo_manager's push_command was never called (no connection was created)
        mock_undo_redo_manager.push_command.assert_not_called()
    
    @pytest.mark.unit
    def test_multi_connection_prevents_duplicates(self, mock_canvas, mock_event_bus, mock_undo_redo_manager):
        """Test that on_connect_multiple_devices_requested prevents duplicate connections."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus, mock_undo_redo_manager)
        
        # Create mock devices
        device1 = MagicMock()
        device1.name = "Device1"
        device1.scenePos = lambda: MagicMock(x=lambda: 0, y=lambda: 0)
        
        device2 = MagicMock()
        device2.name = "Device2"
        device2.scenePos = lambda: MagicMock(x=lambda: 100, y=lambda: 0)
        
        # Create a mock connection
        connection = MagicMock()
        connection.source_device = device1
        connection.target_device = device2
        
        # Add the connection to the mock canvas
        mock_canvas.connections = [connection]
        
        # Mock the MultiConnectionDialog and its get_connection_data method
        with patch('controllers.connection_controller.MultiConnectionDialog') as MockDialog:
            # Configure the mock dialog
            mock_dialog_instance = MagicMock()
            MockDialog.return_value = mock_dialog_instance
            mock_dialog_instance.exec_.return_value = 1  # QDialog.Accepted
            mock_dialog_instance.get_connection_data.return_value = {
                'strategy': 'chain',
                'type': ConnectionTypes.ETHERNET,
                'label': 'Link',
                'bandwidth': '1Gbps',
                'latency': '1ms',
                'bidirectional': False
            }
            
            # With patch for AddConnectionCommand
            with patch('controllers.commands.AddConnectionCommand') as MockCommand:
                # Mock command instance
                mock_command_instance = MagicMock()
                MockCommand.return_value = mock_command_instance
                
                # Mock CompositeCommand
                with patch('controllers.commands.CompositeCommand') as MockCompositeCommand:
                    # Mock CompositeCommand instance
                    mock_composite_instance = MagicMock()
                    MockCompositeCommand.return_value = mock_composite_instance
                    
                    # Now try to connect the devices using chain strategy
                    controller.on_connect_multiple_devices_requested([device1, device2])
                    
                    # The AddConnectionCommand should not have been called because the connection already exists
                    assert MockCommand.call_count == 0, "Should not create a connection that already exists"
    
    @pytest.mark.unit
    def test_successful_connection_creation(self, mock_canvas, mock_event_bus, mock_undo_redo_manager):
        """Test that connections can be successfully created when they don't already exist."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus, mock_undo_redo_manager)
        
        # Create two mock devices
        device1 = MagicMock()
        device1.name = "Device1"
        device1.get_center_position = lambda: None
        device1.get_nearest_port = lambda pos: None
        
        device2 = MagicMock()
        device2.name = "Device2"
        device2.get_center_position = lambda: None
        device2.get_nearest_port = lambda pos: None
        
        # No existing connections
        mock_canvas.connections = []
        
        # Mock the on_connection_requested method
        with patch.object(controller, 'on_connection_requested') as mock_on_connection_requested:
            mock_on_connection_requested.return_value = True
            
            # Try to add a connection
            result = controller.on_add_connection_requested(device1, device2)
            
            # The connection should be accepted
            assert result == True
            
            # Verify on_connection_requested was called
            mock_on_connection_requested.assert_called_once() 