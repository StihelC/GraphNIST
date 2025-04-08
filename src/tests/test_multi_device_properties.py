import unittest
from unittest.mock import MagicMock, patch, call
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QGroupBox, QLabel

from controllers.properties_controller import PropertiesController
from views.properties_panel import PropertiesPanel
from models.device import Device

class TestMultiDeviceProperties(unittest.TestCase):
    """Test case for properties panel handling multiple device selection."""
    
    def setUp(self):
        """Set up the test environment."""
        # Ensure QApplication exists
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
            
        # Create real properties panel
        self.properties_panel = PropertiesPanel()
        
        # Create mock objects
        self.canvas = MagicMock()
        self.canvas.scene.return_value = MagicMock()
        self.canvas.devices = []
        
        self.event_bus = MagicMock()
        self.undo_redo_manager = MagicMock()
        
        # Create the controller
        self.controller = PropertiesController(
            self.canvas, 
            self.properties_panel, 
            self.event_bus, 
            self.undo_redo_manager
        )
        
        # Create mock devices with different properties
        self.device1 = MagicMock(spec=Device)
        self.device1.name = "Device 1"
        self.device1.device_type = "router"
        self.device1.properties = {
            "ip_address": "192.168.1.1",
            "hostname": "router1",
            "model": "Cisco 3000",
            "os": "IOS"
        }
        self.device1.get_property_display_state = MagicMock(return_value=True)
        self.device1.isSelected.return_value = True
        
        self.device2 = MagicMock(spec=Device)
        self.device2.name = "Device 2"
        self.device2.device_type = "switch"
        self.device2.properties = {
            "ip_address": "192.168.1.2",
            "hostname": "switch1",
            "ports": "48",
            "location": "Rack 2"
        }
        self.device2.get_property_display_state = MagicMock(return_value=True)
        self.device2.isSelected.return_value = True
        
        self.device3 = MagicMock(spec=Device)
        self.device3.name = "Device 3"
        self.device3.device_type = "firewall"
        self.device3.properties = {
            "ip_address": "192.168.1.3",
            "manufacturer": "Palo Alto",
            "firewall_type": "NGFW"
        }
        self.device3.get_property_display_state = MagicMock(return_value=True)
        self.device3.isSelected.return_value = True
        
        # Add devices to canvas
        self.canvas.devices = [self.device1, self.device2, self.device3]
    
    def test_show_all_properties_for_multiple_devices(self):
        """Test that selecting multiple devices shows all properties, not just common ones."""
        # Mock the show_multiple_devices method to track how it's called
        original_method = self.properties_panel.show_multiple_devices
        
        try:
            # Create a mock to replace the original method
            self.properties_panel.show_multiple_devices = MagicMock()
            
            # Perform multi-selection
            selected_items = [self.device1, self.device2, self.device3]
            self.controller.update_properties_panel(selected_items)
            
            # Verify the controller has set the selected_items correctly
            self.assertEqual(self.controller.selected_items, selected_items)
            
            # Verify show_multiple_devices was called with all devices
            self.properties_panel.show_multiple_devices.assert_called_once_with(selected_items)
        finally:
            # Restore the original method
            self.properties_panel.show_multiple_devices = original_method
    
    def test_show_all_unique_properties(self):
        """Test that all unique properties from all devices are shown, not just common ones."""
        # For this test, actually call the real show_multiple_devices method
        # and check that it collects all unique properties
        
        # Set up proper methods to avoid AttributeError for device mocks
        for device in [self.device1, self.device2, self.device3]:
            device.toggle_property_display = MagicMock()
        
        # Select multiple devices with different properties
        selected_devices = [self.device1, self.device2, self.device3]
        
        # Call the real method (not mocked)
        self.properties_panel.show_multiple_devices(selected_devices)
        
        # Get all the unique properties from all devices
        all_properties = set()
        for device in selected_devices:
            for prop in device.properties:
                if prop not in ["name", "device_type", "width", "height", "color", "icon", "position", "port_positions", "selected"]:
                    all_properties.add(prop)
        
        # Parse the display checkboxes to see what properties are shown
        displayed_properties = set()
        if hasattr(self.properties_panel, 'display_checkboxes'):
            for prop in self.properties_panel.display_checkboxes.keys():
                displayed_properties.add(prop)
                
        # All unique properties should be in the displayed properties
        for prop in all_properties:
            self.assertIn(prop, displayed_properties, f"Property {prop} is missing from the display checkboxes")
            
        # The count should match
        self.assertEqual(len(all_properties), len(displayed_properties))
    
    def test_property_edit_handling(self):
        """Test that property changes are applied to all selected devices."""
        # Setup multiple device selection
        selected_devices = [self.device1, self.device2, self.device3]
        self.controller.selected_items = selected_devices
        
        # Simulate changing a property from the properties panel
        property_name = "new_property"
        property_value = "test_value"
        
        # Call the property change handler
        self.controller._handle_multiple_property_change(property_name, property_value)
        
        # Verify undo/redo command was created
        self.undo_redo_manager.push_command.assert_called_once()
        
        # Get the command that was pushed
        command = self.undo_redo_manager.push_command.call_args[0][0]
        
        # Manually execute the command to verify it works
        command.execute()
        
        # Verify the event bus was called with bulk_properties_changed
        self.event_bus.emit.assert_called_with("bulk_properties_changed", selected_devices)
                
    def test_display_toggle_handling(self):
        """Test that display toggles are applied to all selected devices."""
        # Setup multiple device selection
        selected_devices = [self.device1, self.device2, self.device3]
        self.controller.selected_items = selected_devices
        
        # Simulate toggling a property display setting
        property_name = "ip_address"
        is_enabled = True
        
        # Call the display toggle handler
        self.controller._on_property_display_toggled(property_name, is_enabled)
        
        # Verify the toggle method was called for each device
        for device in selected_devices:
            device.toggle_property_display.assert_called_with(property_name, is_enabled)

if __name__ == '__main__':
    unittest.main() 