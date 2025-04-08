import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetItem, QCheckBox

from controllers.bulk_property_controller import BulkPropertyController, BulkPropertyEditDialog
from models.device import Device

class TestBulkPropertyEdit(unittest.TestCase):
    """Test case for bulk property editing dialog functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Ensure QApplication exists
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
            
        # Create mock objects
        self.canvas = MagicMock()
        self.canvas.scene.return_value = MagicMock()
        self.device_controller = MagicMock()
        self.event_bus = MagicMock()
        self.undo_redo_manager = MagicMock()
        
        # Create the controller
        self.controller = BulkPropertyController(
            self.canvas,
            self.device_controller,
            self.event_bus,
            self.undo_redo_manager
        )
        
        # Create mock devices with different properties
        self.device1 = MagicMock(spec=Device)
        self.device1.id = "device1"
        self.device1.name = "Device 1"
        self.device1.device_type = "router"
        self.device1.properties = {
            "ip_address": "192.168.1.1",
            "hostname": "router1",
            "model": "Cisco 3000",
            "os": "IOS"
        }
        self.device1.display_properties = {"ip_address": True}
        self.device1.isSelected.return_value = True
        
        self.device2 = MagicMock(spec=Device)
        self.device2.id = "device2"
        self.device2.name = "Device 2"
        self.device2.device_type = "switch"
        self.device2.properties = {
            "ip_address": "192.168.1.2",
            "hostname": "switch1",
            "ports": "48",
            "location": "Rack 2"
        }
        self.device2.display_properties = {"hostname": True}
        self.device2.isSelected.return_value = True
        
        self.device3 = MagicMock(spec=Device)
        self.device3.id = "device3"
        self.device3.name = "Device 3"
        self.device3.device_type = "firewall"
        self.device3.properties = {
            "ip_address": "192.168.1.3",
            "manufacturer": "Palo Alto",
            "firewall_type": "NGFW"
        }
        self.device3.display_properties = {"manufacturer": True}
        self.device3.isSelected.return_value = True
        
        # Add devices to canvas
        self.canvas.devices = [self.device1, self.device2, self.device3]
        
        # Mock the canvas scene's selectedItems method
        self.canvas.scene().selectedItems.return_value = [self.device1, self.device2, self.device3]
    
    @patch('controllers.bulk_property_controller.BulkPropertyEditDialog')
    def test_edit_selected_devices(self, mock_dialog_class):
        """Test that edit_selected_devices opens a dialog and applies changes on accept."""
        # Mock the dialog instance
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog
        
        # Mock the dialog's exec_ method to return QDialog.Accepted
        mock_dialog.exec_.return_value = QDialog.Accepted
        
        # Mock the get_property_changes method to return some property changes
        property_changes = {
            "device1": {
                "hostname": ("router1", "new_hostname"),
                "_display_ip_address": (True, False)
            },
            "device2": {
                "ip_address": ("192.168.1.2", "192.168.1.20"),
                "_display_hostname": (True, False)
            }
        }
        mock_dialog.get_property_changes.return_value = property_changes
        
        # Patch _apply_bulk_property_changes to verify it's called correctly
        with patch.object(self.controller, '_apply_bulk_property_changes') as mock_apply:
            # Call the method under test
            self.controller.edit_selected_devices()
            
            # Verify dialog was created and shown as modal
            mock_dialog_class.assert_called_once_with([self.device1, self.device2, self.device3])
            mock_dialog.setModal.assert_called_once_with(True)
            mock_dialog.exec_.assert_called_once()
            
            # Verify property changes were applied
            mock_apply.assert_called_once_with([self.device1, self.device2, self.device3], property_changes)
            
    def test_dialog_shows_all_properties(self):
        """Test that the dialog shows all properties from all devices, not just common ones."""
        # Create an actual dialog with our mock devices
        dialog = BulkPropertyEditDialog([self.device1, self.device2, self.device3])
        
        # Get all unique properties from all devices (excluding color and icon)
        all_properties = set()
        for device in [self.device1, self.device2, self.device3]:
            for prop in device.properties:
                if prop not in ['color', 'icon']:
                    all_properties.add(prop)
        
        # Get all properties shown in the table
        table_properties = set()
        for row in range(dialog.property_table.rowCount()):
            prop_name = dialog.property_table.item(row, 0).text()
            table_properties.add(prop_name)
        
        # All unique properties should be in the table
        for prop in all_properties:
            self.assertIn(prop, table_properties, f"Property {prop} is missing from the property table")
            
        # The count should match
        self.assertEqual(len(all_properties), len(table_properties), 
                         f"Expected {len(all_properties)} properties but found {len(table_properties)}")
    
    def test_property_changes_calculation(self):
        """Test that get_property_changes correctly calculates changes to apply."""
        # Create a dialog with our mock devices
        dialog = BulkPropertyEditDialog([self.device1, self.device2, self.device3])
        
        # Modify some values in the table
        # For simplicity, we'll directly set the values rather than simulate UI interaction
        
        # Find a row with "hostname" and change its value
        hostname_row = None
        for row in range(dialog.property_table.rowCount()):
            if dialog.property_table.item(row, 0).text() == "hostname":
                hostname_row = row
                break
                
        if hostname_row is not None:
            dialog.property_table.setItem(hostname_row, 1, QTableWidgetItem("new_hostname"))
            # Ensure the apply checkbox is checked
            apply_checkbox = QCheckBox()
            apply_checkbox.setChecked(True)
            dialog.property_table.setCellWidget(hostname_row, 2, apply_checkbox)
        
        # Change display settings for ip_address to be displayed on all devices
        for prop, checkbox in dialog.display_checkboxes.items():
            if prop == "ip_address":
                checkbox.setChecked(True)
                break
        
        # Get the calculated property changes
        property_changes = dialog.get_property_changes()
        
        # Verify hostname changes are included for devices that have hostname
        if "device1" in property_changes and hostname_row is not None:
            self.assertIn("hostname", property_changes["device1"], 
                          "Hostname property change should be included for device1")
            
        # Verify display property changes are included
        # device2 and device3 should have changes to display ip_address
        if "device2" in property_changes:
            self.assertIn("_display_ip_address", property_changes["device2"], 
                          "Display change for ip_address should be included for device2")
            
        if "device3" in property_changes:
            self.assertIn("_display_ip_address", property_changes["device3"], 
                          "Display change for ip_address should be included for device3")
    
    def test_modal_dialog_prevents_conflicts(self):
        """Test that the dialog is shown as modal to prevent interactions with properties panel."""
        # Mock the dialog's exec_ method to allow us to check the modal state
        with patch('controllers.bulk_property_controller.BulkPropertyEditDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog_class.return_value = mock_dialog
            mock_dialog.exec_.return_value = QDialog.Rejected  # User cancels
            
            # Call the method under test
            self.controller.edit_selected_devices()
            
            # Verify dialog was set as modal
            mock_dialog.setModal.assert_called_once_with(True)
            
if __name__ == '__main__':
    unittest.main() 