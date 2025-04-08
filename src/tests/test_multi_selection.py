import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication

# Import the canvas for testing
from views.canvas.canvas import Canvas
from views.canvas.modes.select_mode import SelectMode
from constants import Modes

class TestMultiSelection(unittest.TestCase):
    """Test case for multi-selection functionality in the canvas."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a canvas instance
        self.canvas = Canvas()
        
        # Mock the _emit_selection_changed method
        self.canvas._emit_selection_changed = MagicMock()
        
        # Create mock devices
        self.device1 = MagicMock()
        self.device1.isSelected.return_value = False
        self.device1.sceneBoundingRect.return_value.contains.return_value = True
        
        self.device2 = MagicMock()
        self.device2.isSelected.return_value = False
        self.device2.sceneBoundingRect.return_value.contains.return_value = True
        
        self.device3 = MagicMock()
        self.device3.isSelected.return_value = False
        self.device3.sceneBoundingRect.return_value.contains.return_value = True
        
        # Add devices to canvas
        self.canvas.devices = [self.device1, self.device2, self.device3]
        
        # Ensure we're in select mode
        self.canvas.set_mode(Modes.SELECT)
        
        # Mock the scene and selection methods
        self.canvas.scene().selectedItems = MagicMock(return_value=[])
        self.canvas.scene().clearSelection = MagicMock()
        
        # Set up signal spy
        self.selection_changed_spy = MagicMock()
        self.canvas.selection_changed.connect(self.selection_changed_spy)
        
        # Mock the get_item_at method to return our test devices
        self.canvas.get_item_at = MagicMock()
    
    def create_mouse_event(self, button, modifiers=Qt.NoModifier, position=QPoint(100, 100)):
        """Helper method to create mouse events."""
        return QMouseEvent(
            QEvent.MouseButtonPress,
            position,
            button,
            button,
            modifiers
        )
    
    def test_ctrl_click_selects_without_clearing(self):
        """Test that Ctrl+click allows selecting multiple devices without clearing previous selection."""
        # Mock the get_item_at to return device1
        self.canvas.get_item_at.return_value = self.device1
        
        # First select device1 with a normal click
        event = self.create_mouse_event(Qt.LeftButton)
        self.canvas.mousePressEvent(event)
        
        # Simulate device1 being selected
        self.device1.isSelected.return_value = True
        self.canvas.scene().selectedItems.return_value = [self.device1]
        
        # Now select device2 with Ctrl+click
        self.canvas.get_item_at.return_value = self.device2
        event = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        self.canvas.mousePressEvent(event)
        
        # Simulate both devices being selected
        self.device2.isSelected.return_value = True
        self.canvas.scene().selectedItems.return_value = [self.device1, self.device2]
        
        # Now select device3 with Ctrl+click
        self.canvas.get_item_at.return_value = self.device3
        event = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        self.canvas.mousePressEvent(event)
        
        # Simulate all three devices being selected
        self.device3.isSelected.return_value = True
        self.canvas.scene().selectedItems.return_value = [self.device1, self.device2, self.device3]
        
        # Trigger selection changed signal
        self.canvas._emit_selection_changed([self.device1, self.device2, self.device3])
        
        # Verify selection changed was emitted with all three devices
        self.selection_changed_spy.assert_called_with([self.device1, self.device2, self.device3])
    
    def test_normal_click_clears_selection(self):
        """Test that a normal click clears previous selection."""
        # Set up initial selection of device1 and device2
        self.device1.isSelected.return_value = True
        self.device2.isSelected.return_value = True
        self.canvas.scene().selectedItems.return_value = [self.device1, self.device2]
        
        # Now click device3 without Ctrl
        self.canvas.get_item_at.return_value = self.device3
        event = self.create_mouse_event(Qt.LeftButton)
        self.canvas.mousePressEvent(event)
        
        # The scene should clear the selection first
        self.canvas.scene().clearSelection.assert_called_once()
    
    def test_ctrl_click_toggles_selection(self):
        """Test that Ctrl+click toggles selection state of the clicked device."""
        # Initially select device1
        self.device1.isSelected.return_value = True
        self.canvas.scene().selectedItems.return_value = [self.device1]
        
        # Ctrl+click on device1 again to deselect it
        self.canvas.get_item_at.return_value = self.device1
        event = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        self.canvas.mousePressEvent(event)
        
        # Device1 should be deselected
        self.device1.setSelected.assert_called_with(False)
    
    def test_properties_panel_shows_with_multiple_selection(self):
        """Test that properties panel is shown with multiple devices selected."""
        # Mock the main window and properties controller
        main_window = MagicMock()
        self.canvas.parent.return_value = main_window
        main_window.properties_controller = MagicMock()
        
        # Select multiple devices
        selected_devices = [self.device1, self.device2, self.device3]
        self.canvas.scene().selectedItems.return_value = selected_devices
        
        # Trigger selection change
        self.canvas._emit_selection_changed(selected_devices)
        
        # Verify selection changed signal was emitted
        self.selection_changed_spy.assert_called_with(selected_devices)

if __name__ == '__main__':
    unittest.main() 