import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from views.properties.device_section import DeviceSection
from models.device import Device
from models.device.device_properties import DeviceProperties
from models.device.device_signals import DeviceSignals

class TestDeviceSection(unittest.TestCase):
    def setUp(self):
        # Create QApplication instance if it doesn't exist
        self.app = QApplication.instance() or QApplication([])
        
        # Create test devices
        self.device1 = Device("Device1", "router")
        self.device2 = Device("Device2", "switch")
        self.device3 = Device("Device3", "firewall")
        
        # Initialize properties for test devices
        self.device1.properties = {
            "ip": {"value": "192.168.1.1", "display": True},
            "os": {"value": "Cisco", "display": False}
        }
        self.device2.properties = {
            "ip": {"value": "192.168.1.2", "display": True},
            "os": {"value": "Juniper", "display": True}
        }
        self.device3.properties = {
            "ip": {"value": "192.168.1.3", "display": False},
            "os": {"value": "Palo Alto", "display": True}
        }
        
        # Create DeviceSection instance
        self.section = DeviceSection()
        self.section._init_ui()

    def test_1_set_multiple_devices_common_properties(self):
        """Test that common properties are correctly identified and displayed."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Check that only common properties are shown
        self.assertEqual(self.section.property_table.rowCount(), 2)  # ip and os
        self.assertEqual(self.section.property_table.item(0, 0).text(), "ip")
        self.assertEqual(self.section.property_table.item(1, 0).text(), "os")

    def test_2_property_value_edit_multiple_devices(self):
        """Test editing property values for multiple devices."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Edit the IP property
        ip_row = 0
        new_value = "10.0.0.1"
        self.section.property_table.item(ip_row, 1).setText(new_value)
        
        # Check that all devices were updated
        self.assertEqual(self.device1.properties["ip"]["value"], new_value)
        self.assertEqual(self.device2.properties["ip"]["value"], new_value)
        self.assertEqual(self.device3.properties["ip"]["value"], new_value)

    def test_3_property_display_state_mixed_selection(self):
        """Test handling of mixed display states in multiple device selection."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Check that the display checkbox shows mixed state for 'ip'
        display_widget = self.section.property_table.cellWidget(0, 2)
        display_checkbox = display_widget.layout().itemAt(0).widget()
        self.assertEqual(display_checkbox.checkState(), Qt.PartiallyChecked)

    def test_4_property_display_toggle_multiple_devices(self):
        """Test toggling display state for multiple devices."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Toggle display state for 'os' property
        display_widget = self.section.property_table.cellWidget(1, 2)
        display_checkbox = display_widget.layout().itemAt(0).widget()
        display_checkbox.setChecked(True)
        
        # Check that all devices have the property displayed
        self.assertTrue(self.device1.get_property_display_state("os"))
        self.assertTrue(self.device2.get_property_display_state("os"))
        self.assertTrue(self.device3.get_property_display_state("os"))

    def test_5_property_rename_multiple_devices(self):
        """Test renaming properties for multiple devices."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Rename 'ip' to 'ip_address'
        ip_row = 0
        new_key = "ip_address"
        self.section.property_table.item(ip_row, 0).setText(new_key)
        
        # Check that the property was renamed in all devices
        self.assertIn(new_key, self.device1.properties)
        self.assertIn(new_key, self.device2.properties)
        self.assertIn(new_key, self.device3.properties)
        self.assertNotIn("ip", self.device1.properties)
        self.assertNotIn("ip", self.device2.properties)
        self.assertNotIn("ip", self.device3.properties)

    def test_6_property_value_preservation(self):
        """Test that property values are preserved when toggling display state."""
        original_values = {
            "device1": self.device1.properties["ip"]["value"],
            "device2": self.device2.properties["ip"]["value"],
            "device3": self.device3.properties["ip"]["value"]
        }
        
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Toggle display state
        display_widget = self.section.property_table.cellWidget(0, 2)
        display_checkbox = display_widget.layout().itemAt(0).widget()
        display_checkbox.setChecked(True)
        
        # Check that values were preserved
        self.assertEqual(self.device1.properties["ip"]["value"], original_values["device1"])
        self.assertEqual(self.device2.properties["ip"]["value"], original_values["device2"])
        self.assertEqual(self.device3.properties["ip"]["value"], original_values["device3"])

    def test_7_error_handling_invalid_property(self):
        """Test error handling when editing non-existent properties."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Try to edit a non-existent property
        with patch('logging.Logger.error') as mock_logger:
            self.section._property_changed(Mock(row=999, column=1))
            mock_logger.assert_called()

    def test_8_property_signal_emission(self):
        """Test that property change signals are emitted correctly."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Set up signal spies
        signal_spies = [Mock() for _ in range(3)]
        for device, spy in zip([self.device1, self.device2, self.device3], signal_spies):
            device.signals.property_changed.connect(spy)
        
        # Edit a property
        self.section.property_table.item(0, 1).setText("10.0.0.1")
        
        # Check that signals were emitted
        for spy in signal_spies:
            spy.assert_called()

    def test_9_property_label_updates(self):
        """Test that property labels are updated after property changes."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Mock the update_property_labels method
        for device in [self.device1, self.device2, self.device3]:
            device.update_property_labels = Mock()
        
        # Edit a property
        self.section.property_table.item(0, 1).setText("10.0.0.1")
        
        # Check that update_property_labels was called
        for device in [self.device1, self.device2, self.device3]:
            device.update_property_labels.assert_called()

    def test_10_property_display_state_consistency(self):
        """Test that display states remain consistent after multiple operations."""
        self.section.set_multiple_devices([self.device1, self.device2, self.device3])
        
        # Perform multiple operations
        self.section.property_table.item(0, 1).setText("10.0.0.1")  # Edit value
        display_widget = self.section.property_table.cellWidget(0, 2)
        display_checkbox = display_widget.layout().itemAt(0).widget()
        display_checkbox.setChecked(True)  # Toggle display
        self.section.property_table.item(0, 0).setText("ip_address")  # Rename
        
        # Check that display states are consistent
        self.assertTrue(self.device1.get_property_display_state("ip_address"))
        self.assertTrue(self.device2.get_property_display_state("ip_address"))
        self.assertTrue(self.device3.get_property_display_state("ip_address"))

if __name__ == '__main__':
    unittest.main() 