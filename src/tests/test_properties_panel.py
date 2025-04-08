import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QApplication

# Import the module under test
from controllers.properties_controller import PropertiesController

class TestPropertiesPanel(unittest.TestCase):
    """Test case for the properties panel functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mock objects
        self.canvas = MagicMock()
        self.canvas.scene.return_value = MagicMock()
        self.canvas.devices = []
        
        self.properties_panel = MagicMock()
        self.event_bus = MagicMock()
        self.undo_redo_manager = MagicMock()
        
        # Create the controller
        self.controller = PropertiesController(
            self.canvas, 
            self.properties_panel, 
            self.event_bus, 
            self.undo_redo_manager
        )
        
        # Create mock devices
        self.device1 = MagicMock()
        self.device1.name = "Device 1"
        self.device1.isSelected.return_value = True
        
        self.device2 = MagicMock()
        self.device2.name = "Device 2"
        self.device2.isSelected.return_value = True
        
        self.device3 = MagicMock()
        self.device3.name = "Device 3"
        self.device3.isSelected.return_value = True
        
        # Add devices to canvas
        self.canvas.devices = [self.device1, self.device2, self.device3]
    
    def test_single_device_selection(self):
        """Test that selecting a single device shows its properties."""
        # Setup
        selected_items = [self.device1]
        
        # Execute
        self.controller.update_properties_panel(selected_items)
        
        # Verify
        self.assertEqual(self.controller.selected_item, self.device1)
        self.assertEqual(len(self.controller.selected_items), 0)
        self.properties_panel.display_item_properties.assert_called_once_with(self.device1)
        self.properties_panel.show_multiple_devices.assert_not_called()
    
    def test_multiple_device_selection(self):
        """Test that selecting multiple devices shows the multi-device panel."""
        # Setup
        selected_items = [self.device1, self.device2, self.device3]
        
        # Execute
        self.controller.update_properties_panel(selected_items)
        
        # Verify
        self.assertIsNone(self.controller.selected_item)
        self.assertEqual(len(self.controller.selected_items), 3)
        self.assertEqual(self.controller.selected_items, [self.device1, self.device2, self.device3])
        self.properties_panel.show_multiple_devices.assert_called_once_with([self.device1, self.device2, self.device3])
        self.properties_panel.display_item_properties.assert_not_called()
    
    def test_no_selection(self):
        """Test that having no selection clears the panel."""
        # Setup
        selected_items = []
        
        # Execute
        self.controller.update_properties_panel(selected_items)
        
        # Verify
        self.assertIsNone(self.controller.selected_item)
        self.assertEqual(len(self.controller.selected_items), 0)
        self.properties_panel.clear.assert_called_once()
        self.properties_panel.display_item_properties.assert_not_called()
        self.properties_panel.show_multiple_devices.assert_not_called()
    
    def test_selection_changed_signal(self):
        """Test that the selection_changed signal updates the panel."""
        # Setup
        selected_items = [self.device1, self.device2]
        
        # Execute
        self.controller.on_selection_changed(selected_items)
        
        # Verify
        self.assertEqual(len(self.controller.selected_items), 2)
        self.properties_panel.show_multiple_devices.assert_called_once()
    
    @patch('controllers.properties_controller.QTimer')
    def test_properties_panel_visibility(self, mock_qtimer):
        """Test that the properties panel is made visible when selection changes."""
        # Setup
        main_window = MagicMock()
        main_window.properties_dock = MagicMock()
        
        # Make the panel's parent be the main window
        self.properties_panel.parent.return_value = main_window
        
        # Execute with a selection
        self.controller.on_selection_changed([self.device1])
        
        # Verify
        main_window.properties_dock.setVisible.assert_called_with(True)
        main_window.properties_dock.raise_.assert_called_once()

if __name__ == '__main__':
    unittest.main() 