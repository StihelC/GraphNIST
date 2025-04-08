import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QEvent, QPointF
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QGraphicsItem

# Import the module under test
from views.canvas.modes.select_mode import SelectMode
from models.device import Device

class TestSelectMode(unittest.TestCase):
    """Test case for the select mode functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mock canvas
        self.canvas = MagicMock()
        self.canvas.scene.return_value = MagicMock()
        self.canvas.scene().clearSelection = MagicMock()
        self.canvas.selection_changed = MagicMock()
        
        # Create select mode
        self.select_mode = SelectMode(self.canvas)
        
        # Create mock devices
        self.device1 = MagicMock(spec=Device)
        self.device1.name = "Device 1"
        self.device1.isSelected.return_value = False
        
        self.device2 = MagicMock(spec=Device)
        self.device2.name = "Device 2"
        self.device2.isSelected.return_value = False
        
        self.device3 = MagicMock(spec=Device)
        self.device3.name = "Device 3"
        self.device3.isSelected.return_value = False
    
    def create_mouse_event(self, button=Qt.LeftButton, modifiers=Qt.NoModifier):
        """Create a mouse event for testing."""
        event = MagicMock()
        event.button.return_value = button
        event.modifiers.return_value = modifiers
        event.type.return_value = QEvent.MouseButtonPress
        return event
    
    def test_regular_click_clears_selection(self):
        """Test that a regular click clears existing selection."""
        # Setup
        event = self.create_mouse_event(Qt.LeftButton)
        scene_pos = QPointF(100, 100)
        
        # Execute
        self.select_mode.handle_mouse_press(event, scene_pos, self.device1)
        
        # Verify
        self.canvas.scene().clearSelection.assert_called_once()
        self.device1.setSelected.assert_called_with(True)
    
    def test_ctrl_click_preserves_selection(self):
        """Test that Ctrl+click preserves existing selection."""
        # Setup
        event = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        scene_pos = QPointF(100, 100)
        
        # Execute
        self.select_mode.handle_mouse_press(event, scene_pos, self.device1)
        
        # Verify
        self.canvas.scene().clearSelection.assert_not_called()
        self.device1.setSelected.assert_called_once()
    
    def test_ctrl_click_toggles_item_selection(self):
        """Test that Ctrl+click toggles the selection of an item."""
        # Setup - item is already selected
        self.device1.isSelected.return_value = True
        event = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        scene_pos = QPointF(100, 100)
        
        # Execute
        self.select_mode.handle_mouse_press(event, scene_pos, self.device1)
        
        # Verify - should deselect the item
        self.device1.setSelected.assert_called_with(False)
        
        # Setup again - now item is deselected
        self.device1.isSelected.return_value = False
        
        # Execute again
        self.select_mode.handle_mouse_press(event, scene_pos, self.device1)
        
        # Verify - should select the item without clearing selection
        self.canvas.scene().clearSelection.assert_not_called()
        self.device1.setSelected.assert_called_with(True)
    
    def test_multiple_ctrl_clicks_build_selection(self):
        """Test that multiple Ctrl+clicks build up the selection."""
        # Mock the scene.selectedItems to return our selected devices
        self.canvas.scene().selectedItems.return_value = []
        
        # First click on device1 with Ctrl
        event1 = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        self.select_mode.handle_mouse_press(event1, QPointF(100, 100), self.device1)
        
        # Now device1 is selected
        self.device1.isSelected.return_value = True
        self.canvas.scene().selectedItems.return_value = [self.device1]
        
        # Second click on device2 with Ctrl
        event2 = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        self.select_mode.handle_mouse_press(event2, QPointF(200, 200), self.device2)
        
        # Now both device1 and device2 are selected
        self.device2.isSelected.return_value = True
        self.canvas.scene().selectedItems.return_value = [self.device1, self.device2]
        
        # Verify device2 was selected without clearing selection
        self.canvas.scene().clearSelection.assert_not_called()
        self.device2.setSelected.assert_called_with(True)
    
    def test_click_empty_space_clears_selection(self):
        """Test that clicking in empty space clears selection."""
        # Setup
        event = self.create_mouse_event(Qt.LeftButton)
        scene_pos = QPointF(100, 100)
        
        # Execute - pass None as the item to simulate click in empty space
        self.select_mode.handle_mouse_press(event, scene_pos, None)
        
        # Verify
        self.canvas.scene().clearSelection.assert_called_once()
    
    def test_ctrl_click_empty_space_preserves_selection(self):
        """Test that Ctrl+click in empty space preserves selection."""
        # Setup
        event = self.create_mouse_event(Qt.LeftButton, Qt.ControlModifier)
        scene_pos = QPointF(100, 100)
        
        # Execute - pass None as the item to simulate click in empty space
        self.select_mode.handle_mouse_press(event, scene_pos, None)
        
        # Verify
        self.canvas.scene().clearSelection.assert_not_called()

if __name__ == '__main__':
    unittest.main() 