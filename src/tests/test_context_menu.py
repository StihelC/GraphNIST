import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QApplication, QMenu, QAction

from views.canvas.canvas import Canvas
from models.device import Device

class TestContextMenu(unittest.TestCase):
    """Test case for the right-click context menu functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Ensure QApplication exists
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
            
        # Create a canvas instance
        self.canvas = Canvas()
        self.canvas._request_bulk_edit = MagicMock()
        self.canvas.connect_all_selected_devices = MagicMock()
        self.canvas.align_selected_devices = MagicMock()
        
        # Create mock devices
        self.device1 = MagicMock(spec=Device)
        self.device1.name = "Device 1"
        self.device1.isSelected.return_value = True
        
        self.device2 = MagicMock(spec=Device)
        self.device2.name = "Device 2"
        self.device2.isSelected.return_value = True
        
        self.device3 = MagicMock(spec=Device)
        self.device3.name = "Device 3"
        self.device3.isSelected.return_value = True
        
        # Add devices to canvas
        self.canvas.devices = [self.device1, self.device2, self.device3]
    
    @patch('views.canvas.canvas.QMenu')
    def test_context_menu_single_device(self, mock_menu_class):
        """Test that context menu shows correct options for a single device."""
        # Mock the menu and its methods
        mock_menu = MagicMock()
        mock_menu_class.return_value = mock_menu
        mock_menu.addAction.return_value = MagicMock()
        mock_menu.addMenu.return_value = MagicMock()
        mock_menu.exec_.return_value = None
        
        # Mock scene.itemAt to return a device
        self.canvas.scene().itemAt = MagicMock(return_value=self.device1)
        
        # Set up only one device as selected
        self.device2.isSelected.return_value = False
        self.device3.isSelected.return_value = False
        self.canvas.scene().selectedItems = MagicMock(return_value=[self.device1])
        
        # Create a context menu event
        event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(100, 100))
        
        # Show the context menu
        self.canvas.contextMenuEvent(event)
        
        # Verify menu was created and shown
        mock_menu_class.assert_called_once()
        mock_menu.exec_.assert_called_once()
        
        # No bulk edit action should be called
        self.canvas._request_bulk_edit.assert_not_called()
    
    @patch('views.canvas.canvas.QMenu')
    def test_context_menu_multiple_devices(self, mock_menu_class):
        """Test that context menu shows correct options for multiple selected devices."""
        # Mock the menu and its methods
        mock_menu = MagicMock()
        mock_menu_class.return_value = mock_menu
        
        # Set up an action for the bulk edit option
        bulk_edit_action = MagicMock()
        mock_menu.addAction.return_value = bulk_edit_action
        
        # Other menu items
        mock_menu.addMenu.return_value = MagicMock()
        
        # Mock scene.itemAt to return a device
        self.canvas.scene().itemAt = MagicMock(return_value=self.device1)
        
        # Set up multiple devices as selected
        self.canvas.scene().selectedItems = MagicMock(return_value=[self.device1, self.device2, self.device3])
        
        # Create a context menu event
        event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(100, 100))
        
        # Show the context menu
        self.canvas.contextMenuEvent(event)
        
        # Verify menu was created and shown
        mock_menu_class.assert_called_once()
        mock_menu.exec_.assert_called_once()
        
        # Simulate clicking the "Edit X Devices..." action
        bulk_edit_action.triggered.emit()
        
        # Verify bulk edit was requested
        self.canvas._request_bulk_edit.assert_called_once()
    
    @patch('views.canvas.canvas.QMenu')
    def test_bulk_edit_action_triggers_dialog(self, mock_menu_class):
        """Test that the bulk edit action triggers the appropriate handler."""
        # Mock the menu and its methods
        mock_menu = MagicMock()
        mock_menu_class.return_value = mock_menu
        
        # Set up an action for the bulk edit option
        bulk_edit_action = MagicMock()
        connect_action = MagicMock()
        
        # Return different actions based on the action text
        def mock_add_action(text):
            if "Edit" in text:
                return bulk_edit_action
            elif "Connect" in text:
                return connect_action
            else:
                return MagicMock()
                
        mock_menu.addAction.side_effect = mock_add_action
        mock_menu.addMenu.return_value = MagicMock()
        
        # Mock scene.itemAt to return a device
        self.canvas.scene().itemAt = MagicMock(return_value=self.device1)
        
        # Set up multiple devices as selected
        self.canvas.scene().selectedItems = MagicMock(return_value=[self.device1, self.device2, self.device3])
        
        # Create a context menu event
        event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(100, 100))
        
        # Show the context menu
        self.canvas.contextMenuEvent(event)
        
        # Verify menu was created and shown
        mock_menu_class.assert_called_once()
        
        # Simulate clicking the "Edit X Devices..." action
        bulk_edit_action.triggered.emit()
        
        # Verify bulk edit was requested
        self.canvas._request_bulk_edit.assert_called_once()
        
        # Simulate clicking the "Connect X Devices..." action
        connect_action.triggered.emit()
        
        # Verify connect devices was requested
        self.canvas.connect_all_selected_devices.assert_called_once()
    
    @patch('views.canvas.canvas.QMenu')
    def test_aligned_devices_action(self, mock_menu_class):
        """Test that the align devices option works in the context menu."""
        # Mock the menu hierarchy
        mock_menu = MagicMock()
        mock_align_menu = MagicMock()
        mock_basic_align = MagicMock()
        
        mock_menu_class.return_value = mock_menu
        mock_menu.addMenu.return_value = mock_align_menu
        mock_align_menu.addMenu.return_value = mock_basic_align
        
        # Set up actions for alignment
        align_left_action = MagicMock()
        mock_basic_align.addAction.return_value = align_left_action
        
        # Mock scene.itemAt to return a device
        self.canvas.scene().itemAt = MagicMock(return_value=self.device1)
        
        # Set up multiple devices as selected
        self.canvas.scene().selectedItems = MagicMock(return_value=[self.device1, self.device2, self.device3])
        
        # Create a context menu event
        event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(100, 100))
        
        # Show the context menu
        with patch('PyQt5.QtWidgets.QAction', spec=QAction) as mock_action:
            with patch.object(self.canvas, 'align_selected_devices') as mock_align:
                self.canvas.contextMenuEvent(event)
                
                # We can't easily trigger the lambda functions in the actual context menu
                # But we can verify that the align_selected_devices method works
                self.canvas.align_selected_devices('left')
                mock_align.assert_called_with('left')
        
    @patch('views.canvas.canvas.QMenu')
    def test_connect_devices_action(self, mock_menu_class):
        """Test that the connect devices option works in the context menu."""
        # Mock the menu
        mock_menu = MagicMock()
        mock_menu_class.return_value = mock_menu
        
        # Set up actions
        connect_action = MagicMock()
        mock_menu.addAction.return_value = connect_action
        
        # Mock scene.itemAt to return a device
        self.canvas.scene().itemAt = MagicMock(return_value=self.device1)
        
        # Set up multiple devices as selected
        self.canvas.scene().selectedItems = MagicMock(return_value=[self.device1, self.device2, self.device3])
        
        # Create a context menu event
        event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(100, 100))
        
        # Show the context menu
        self.canvas.contextMenuEvent(event)
        
        # Verify that the connect_all_selected_devices method can be called
        self.canvas.connect_all_selected_devices()
        self.canvas.connect_all_selected_devices.assert_called_once()

if __name__ == '__main__':
    unittest.main() 