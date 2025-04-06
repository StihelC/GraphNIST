"""
Unit tests for the PropertiesPanel class.

These tests ensure that the properties panel correctly displays and allows editing of
properties for different types of items (devices, connections, boundaries).
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import QTableWidgetItem

from views.properties_panel import PropertiesPanel
from models.device import Device
from models.connection import Connection
from models.boundary import Boundary
from constants import ConnectionTypes, RoutingStyle

class TestPropertiesPanel:
    """Test suite for the PropertiesPanel class."""
    
    @pytest.fixture
    def properties_panel(self, app):
        """Create a properties panel instance for testing."""
        panel = PropertiesPanel()
        # We need to patch display_item_properties to avoid UI issues in testing
        panel.display_item_properties = MagicMock()
        return panel
    
    @pytest.mark.unit
    def test_properties_panel_initialization(self, properties_panel):
        """Test that the properties panel initializes correctly."""
        # Panel should start with no current item
        assert properties_panel.current_item is None
        assert len(properties_panel.boundary_devices) == 0
        
        # All sections should initially be defined
        assert hasattr(properties_panel, 'general_group')
        assert hasattr(properties_panel, 'device_group')
        assert hasattr(properties_panel, 'connection_group')
        assert hasattr(properties_panel, 'boundary_group')
    
    @pytest.mark.unit
    def test_clear_panel(self, properties_panel):
        """Test that the clear method resets the panel correctly."""
        # Mock a current item
        properties_panel.current_item = MagicMock()
        properties_panel.boundary_devices = [MagicMock()]
        
        # Call clear
        properties_panel.clear()
        
        # Panel should be reset
        assert properties_panel.current_item is None
        assert len(properties_panel.boundary_devices) == 0
    
    @pytest.mark.unit
    def test_name_change_signal(self, properties_panel):
        """Test that name_changed signal is emitted when editing a name."""
        # Set up name changed signal spy
        signal_spy = MagicMock()
        properties_panel.name_changed.connect(signal_spy)
        
        # Simulate name edit and editingFinished signal
        properties_panel.name_edit.setText("NewName")
        properties_panel.name_edit.editingFinished.emit()
        
        # Check signal was emitted with correct value
        signal_spy.assert_called_once_with("NewName")
    
    @pytest.mark.unit
    def test_z_value_change_signal(self, properties_panel):
        """Test that z_value_changed signal is emitted when changing z-value."""
        # Set up z-value changed signal spy
        signal_spy = MagicMock()
        properties_panel.z_value_changed.connect(signal_spy)
        
        # Simulate z-value change
        properties_panel.z_index_spin.setValue(20)
        
        # Check signal was emitted with correct value
        signal_spy.assert_called_with(20.0)
    
    @pytest.mark.unit
    def test_show_multiple_devices(self, properties_panel):
        """Test displaying properties for multiple selected devices."""
        # Create mock devices
        device1 = MagicMock(spec=Device)
        device1.name = "Device1"
        device1.device_type = "router"
        device1.properties = {"ip_address": "192.168.1.1", "os": "RouterOS"}
        
        device2 = MagicMock(spec=Device)
        device2.name = "Device2"
        device2.device_type = "switch"
        device2.properties = {"ip_address": "192.168.1.2", "os": "SwitchOS"}
        
        # Patch _reset_layout to avoid UI errors
        with patch.object(properties_panel, '_reset_layout'):
            # Patch content_layout.addWidget to avoid UI errors
            with patch.object(properties_panel.content_layout, 'addWidget'):
                # Call method
                properties_panel.show_multiple_devices([device1, device2])
                
                # Check current item is None (multiple selection mode)
                assert properties_panel.current_item is None
    
    @pytest.mark.unit
    def test_device_property_change_signal(self, properties_panel):
        """Test device_property_changed signal is emitted."""
        # Set up signal spy
        signal_spy = MagicMock()
        properties_panel.device_property_changed.connect(signal_spy)
        
        # Create mock table item
        key_item = MagicMock()
        key_item.text.return_value = "ip_address"
        
        value_item = MagicMock()
        value_item.text.return_value = "10.0.0.1"
        
        # Mock the table item retrieval
        properties_panel.device_props_table.item = MagicMock()
        properties_panel.device_props_table.item.side_effect = lambda row, col: key_item if col == 0 else value_item
        
        # Call the handler
        properties_panel._on_device_property_changed(0, 1)
        
        # Check signal was emitted
        signal_spy.assert_called_once_with("ip_address", "10.0.0.1")
    
    @pytest.mark.unit
    def test_connection_property_change_signal(self, properties_panel):
        """Test connection_property_changed signal is emitted."""
        # Set up signal spy
        signal_spy = MagicMock()
        properties_panel.connection_property_changed.connect(signal_spy)
        
        # Create mock table item
        key_item = MagicMock()
        key_item.text.return_value = "bandwidth"
        
        value_item = MagicMock()
        value_item.text.return_value = "1Gbps"
        
        # Mock the table item retrieval
        properties_panel.connection_props_table.item = MagicMock()
        properties_panel.connection_props_table.item.side_effect = lambda row, col: key_item if col == 0 else value_item
        
        # Call the handler
        properties_panel._on_connection_property_changed(0, 1)
        
        # Check signal was emitted
        signal_spy.assert_called_once_with("bandwidth", "1Gbps")
    
    @pytest.mark.unit
    def test_property_display_toggle_signal(self, properties_panel):
        """Test property_display_toggled signal is emitted."""
        # Set up signal spy
        signal_spy = MagicMock()
        properties_panel.property_display_toggled.connect(signal_spy)
        
        # Create a checkbox mock
        checkbox = MagicMock()
        checkbox.property.return_value = "ip_address"
        checkbox.isChecked.return_value = True
        
        # Set sender method to return our checkbox
        properties_panel.sender = MagicMock(return_value=checkbox)
        
        # Call the handler
        properties_panel._handle_checkbox_state_changed(Qt.Checked)
        
        # Check signal was emitted
        signal_spy.assert_called_once_with("ip_address", True)
    
    @pytest.mark.unit
    def test_change_icon_signal(self, properties_panel):
        """Test change_icon_requested signal is emitted."""
        # Set up signal spy
        signal_spy = MagicMock()
        properties_panel.change_icon_requested.connect(signal_spy)
        
        # Create a mock device
        mock_device = MagicMock()
        properties_panel.current_item = mock_device
        
        # Call the change icon method if it exists
        if hasattr(properties_panel, '_on_change_icon_clicked'):
            properties_panel._on_change_icon_clicked()
            
            # Check signal was emitted
            signal_spy.assert_called_once_with(mock_device)
    
    @pytest.mark.unit
    def test_set_boundary_contained_devices(self, properties_panel):
        """Test that boundary devices can be set."""
        # Create mock devices
        device1 = MagicMock()
        device1.name = "Device1"
        device2 = MagicMock()
        device2.name = "Device2"
        
        # Set devices
        properties_panel.set_boundary_contained_devices([device1, device2])
        
        # Check devices were set
        assert len(properties_panel.boundary_devices) == 2
        assert properties_panel.boundary_devices[0] == device1
        assert properties_panel.boundary_devices[1] == device2 