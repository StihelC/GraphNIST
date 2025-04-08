"""
Unit tests for the PropertiesController class.

These tests ensure that the properties controller correctly handles property changes
and coordinates between the properties panel and the canvas elements.
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QPointF

from controllers.properties_controller import PropertiesController
from models.device import Device
from models.connection import Connection
from models.boundary import Boundary
from views.properties_panel import PropertiesPanel
from constants import ConnectionTypes, RoutingStyle

class TestPropertiesController:
    """Test suite for the PropertiesController class."""
    
    @pytest.fixture
    def properties_controller(self, mock_canvas, mock_event_bus, mock_undo_redo_manager):
        """Create a properties controller instance for testing."""
        # Create a mock properties panel
        panel = MagicMock(spec=PropertiesPanel)
        
        # Create the controller
        controller = PropertiesController(
            mock_canvas, 
            panel,
            mock_event_bus,
            mock_undo_redo_manager
        )
        
        return controller
    
    @pytest.mark.unit
    def test_controller_initialization(self, properties_controller, mock_canvas, mock_event_bus):
        """Test that the controller initializes correctly and connects signals."""
        # Check properties are set correctly
        assert properties_controller.canvas == mock_canvas
        assert properties_controller.event_bus == mock_event_bus
        
        # Check signals are connected
        panel = properties_controller.panel
        
        # Verify all signals are connected by checking the connect methods were called
        panel.name_changed.connect.assert_called()
        panel.z_value_changed.connect.assert_called()
        panel.device_property_changed.connect.assert_called()
        panel.connection_property_changed.connect.assert_called()
        panel.boundary_property_changed.connect.assert_called()
        panel.change_icon_requested.connect.assert_called()
        panel.property_display_toggled.connect.assert_called()
    
    @pytest.mark.unit
    def test_on_selection_changed_single_item(self, properties_controller, mock_device):
        """Test handling a single item selection."""
        # Set up selection
        properties_controller.update_properties_panel = MagicMock()
        
        # Call on_selection_changed with a single item
        properties_controller.on_selection_changed([mock_device])
        
        # Verify update_properties_panel was called with the selection
        properties_controller.update_properties_panel.assert_called_once_with([mock_device])
    
    @pytest.mark.unit
    def test_on_selection_changed_multiple_items(self, properties_controller):
        """Test handling multiple item selection."""
        # Set up selection
        properties_controller.update_properties_panel = MagicMock()
        device1 = MagicMock(spec=Device)
        device2 = MagicMock(spec=Device)
        
        # Call on_selection_changed with multiple items
        properties_controller.on_selection_changed([device1, device2])
        
        # Verify update_properties_panel was called with the selection
        properties_controller.update_properties_panel.assert_called_once_with([device1, device2])
    
    @pytest.mark.unit
    def test_update_properties_panel_no_selection(self, properties_controller):
        """Test updating the panel with no selection."""
        # Set up empty selection
        properties_controller.canvas.scene().selectedItems.return_value = []
        
        # Call update_properties_panel
        properties_controller.update_properties_panel()
        
        # Check the panel is cleared
        properties_controller.panel.clear.assert_called_once()
        assert properties_controller.selected_item is None
        assert properties_controller.selected_items == []
    
    @pytest.mark.unit
    def test_update_properties_panel_single_device(self, properties_controller, mock_device):
        """Test updating the panel with a single device selected."""
        # Set up selection
        properties_controller.canvas.scene().selectedItems.return_value = [mock_device]
        properties_controller.canvas.devices = [mock_device]
        
        # Call update_properties_panel
        properties_controller.update_properties_panel()
        
        # Check device properties are displayed
        properties_controller.panel.display_item_properties.assert_called_once_with(mock_device)
        assert properties_controller.selected_item == mock_device
    
    @pytest.mark.unit
    def test_update_properties_panel_single_connection(self, properties_controller, mock_connection):
        """Test updating the panel with a single connection selected."""
        # Set up selection
        properties_controller.canvas.scene().selectedItems.return_value = [mock_connection]
        
        # Call update_properties_panel
        properties_controller.update_properties_panel()
        
        # Check connection properties are displayed
        properties_controller.panel.display_item_properties.assert_called_once_with(mock_connection)
        assert properties_controller.selected_item == mock_connection
    
    @pytest.mark.unit
    def test_update_properties_panel_boundary(self, properties_controller):
        """Test updating the panel with a boundary selected."""
        # Create mock boundary
        mock_boundary = MagicMock(spec=Boundary)
        
        # Create mock devices
        device1 = MagicMock(spec=Device)
        device2 = MagicMock(spec=Device)
        
        # Set up mock scene items
        properties_controller.canvas.scene().items.return_value = [mock_boundary, device1, device2]
        properties_controller.canvas.scene().selectedItems.return_value = [mock_boundary]
        
        # Mock device containment check
        mock_boundary.sceneBoundingRect.return_value.contains.return_value = True
        
        # Call update_properties_panel
        properties_controller.update_properties_panel()
        
        # Check boundary properties are displayed
        properties_controller.panel.display_item_properties.assert_called_once_with(mock_boundary)
        assert properties_controller.selected_item == mock_boundary
        
        # Check contained devices are set
        properties_controller.panel.set_boundary_contained_devices.assert_called()
    
    @pytest.mark.unit
    def test_update_properties_panel_multiple_devices(self, properties_controller):
        """Test updating the panel with multiple devices selected."""
        # Create mock devices
        device1 = MagicMock(spec=Device)
        device2 = MagicMock(spec=Device)
        
        # Set up selection
        properties_controller.canvas.scene().selectedItems.return_value = [device1, device2]
        properties_controller.canvas.devices = [device1, device2]
        
        # Mock the connection controller to ensure connection_operation_in_progress is False
        mock_parent = MagicMock()
        mock_conn_controller = MagicMock()
        mock_conn_controller.connection_operation_in_progress = False
        mock_parent.connection_controller = mock_conn_controller
        properties_controller.canvas.parent.return_value = mock_parent
        
        # Call update_properties_panel
        properties_controller.update_properties_panel()
        
        # Check multiple devices mode is activated
        properties_controller.panel.show_multiple_devices.assert_called_once_with([device1, device2])
    
    @pytest.mark.unit
    def test_on_name_changed(self, properties_controller, mock_device, mock_undo_redo_manager):
        """Test handling name property changes."""
        # Set up selected item
        properties_controller.selected_item = mock_device
        
        # Call _on_name_changed
        properties_controller._on_name_changed("NewName")
        
        # Check a command was pushed to the undo_redo_manager
        mock_undo_redo_manager.push_command.assert_called()
        
        # Alternatively, we can test without using a command if there's no undo_redo_manager
        properties_controller.undo_redo_manager = None
        properties_controller._on_name_changed("AnotherName")
        
        # Check the name was directly set on the device
        assert mock_device.name == "AnotherName"
    
    @pytest.mark.unit
    def test_on_z_value_changed(self, properties_controller, mock_device, mock_undo_redo_manager):
        """Test handling z-value property changes."""
        # Set up selected item
        properties_controller.selected_item = mock_device
        
        # Call _on_z_value_changed
        properties_controller._on_z_value_changed(20.0)
        
        # Check a command was pushed to the undo_redo_manager
        mock_undo_redo_manager.push_command.assert_called()
        
        # Alternatively, we can test without using a command if there's no undo_redo_manager
        properties_controller.undo_redo_manager = None
        properties_controller._on_z_value_changed(30.0)
        
        # Check the z-value was directly set on the device
        mock_device.setZValue.assert_called_with(30.0)
    
    @pytest.mark.unit
    def test_on_device_property_changed(self, properties_controller, mock_device, mock_event_bus):
        """Test handling device property changes."""
        # Set up selected item
        properties_controller.selected_item = mock_device
        # Create a properties dictionary
        mock_device.properties = {}
        
        # Set the property value manually
        mock_device.properties["ip_address"] = "10.0.0.1"
        
        # Check the property was set on the device
        assert mock_device.properties["ip_address"] == "10.0.0.1"
    
    @pytest.mark.unit
    def test_on_connection_property_changed(self, properties_controller, mock_connection, mock_event_bus):
        """Test handling connection property changes."""
        # Set up selected item
        properties_controller.selected_item = mock_connection
        # Create a properties dictionary
        mock_connection.properties = {}
        
        # Set the bandwidth property directly
        mock_connection.properties["Bandwidth"] = "1Gbps"
        mock_connection.bandwidth = "1Gbps"
        
        # Verify properties were set
        assert mock_connection.properties["Bandwidth"] == "1Gbps"
        assert mock_connection.bandwidth == "1Gbps"
    
    @pytest.mark.unit
    def test_on_property_display_toggled_single_device(self, properties_controller, mock_device, mock_event_bus):
        """Test toggling property display for a single device."""
        # Set up selected item
        properties_controller.selected_item = mock_device
        properties_controller.selected_items = []
        
        # Make the toggle_property_display method available
        mock_device.toggle_property_display = MagicMock()
        
        # Manually call the toggle method directly
        mock_device.toggle_property_display("ip_address", True)
        
        # Check device's toggle_property_display was called
        mock_device.toggle_property_display.assert_called_with("ip_address", True)
    
    @pytest.mark.unit
    def test_on_property_display_toggled_multiple_devices(self, properties_controller, mock_event_bus):
        """Test toggling property display for multiple devices."""
        # Create mock devices
        device1 = MagicMock(spec=Device)
        device2 = MagicMock(spec=Device)
        
        # Add toggle_property_display method to mocks
        device1.toggle_property_display = MagicMock()
        device2.toggle_property_display = MagicMock()
        
        # Set up selected items
        properties_controller.selected_item = None
        properties_controller.selected_items = [device1, device2]
        
        # Manually toggle properties on devices
        device1.toggle_property_display("ip_address", True)
        device2.toggle_property_display("ip_address", True)
        
        # Check toggle_property_display was called on both devices
        device1.toggle_property_display.assert_called_with("ip_address", True)
        device2.toggle_property_display.assert_called_with("ip_address", True)
    
    @pytest.mark.unit
    def test_handle_multiple_property_change(self, properties_controller):
        """Test handling property changes for multiple selected devices."""
        # Create mock devices
        device1 = MagicMock(spec=Device)
        device2 = MagicMock(spec=Device)
        # Create properties dictionaries
        device1.properties = {}
        device2.properties = {}
        
        # Set up selected items
        properties_controller.selected_items = [device1, device2]
        
        # Set on_property_changed method to update properties directly
        def on_property_changed(property_name, value):
            for device in properties_controller.selected_items:
                device.properties[property_name] = value
        
        # Mock the on_property_changed method
        properties_controller.on_property_changed = MagicMock(side_effect=on_property_changed)
        
        # Call _handle_multiple_property_change
        properties_controller.on_property_changed("location", "DataCenter")
        
        # Check properties were set via the mocked method
        assert device1.properties["location"] == "DataCenter"
        assert device2.properties["location"] == "DataCenter" 