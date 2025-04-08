import unittest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QDialog

# Import the required modules
from controllers.connection_controller import ConnectionController
from models.device import Device

class TestConnectionController(unittest.TestCase):
    """Test case for the ConnectionController class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create mock objects
        self.canvas = MagicMock()
        self.canvas.connections = []
        self.canvas.devices = []
        self.event_bus = MagicMock()
        
        # Create the controller
        self.controller = ConnectionController(self.canvas, self.event_bus)
        
        # Create test devices
        self.device1 = MagicMock(spec=Device)
        self.device1.name = "Device 1"
        self.device1.connections = []
        
        self.device2 = MagicMock(spec=Device)
        self.device2.name = "Device 2"
        self.device2.connections = []
        
        self.device3 = MagicMock(spec=Device)
        self.device3.name = "Device 3"
        self.device3.connections = []
    
    def test_connection_operation_flag_reset(self):
        """Test that the connection_operation_in_progress flag is properly reset."""
        # Mock the MultiConnectionDialog
        with patch('controllers.connection_controller.MultiConnectionDialog') as mock_dialog:
            # Configure the mock to return a dialog instance
            dialog_instance = MagicMock()
            mock_dialog.return_value = dialog_instance
            
            # Make the dialog return QDialog.Rejected when executed
            dialog_instance.exec_.return_value = QDialog.Rejected
            
            # Call the method
            self.controller.on_connect_multiple_devices_requested([self.device1, self.device2, self.device3])
            
            # Check that the flag is reset after the dialog is closed
            self.assertFalse(self.controller.connection_operation_in_progress, 
                            "connection_operation_in_progress flag should be reset even when dialog is canceled")
            
            # Verify dialog was created and shown exactly once
            mock_dialog.assert_called_once()
            dialog_instance.exec_.assert_called_once()
    
    def test_connection_operation_in_progress_prevents_duplicate_dialogs(self):
        """Test that the connection_operation_in_progress flag prevents duplicate dialogs."""
        # Set the flag to simulate an in-progress operation
        self.controller.connection_operation_in_progress = True
        
        # Mock the MultiConnectionDialog
        with patch('controllers.connection_controller.MultiConnectionDialog') as mock_dialog:
            # Call the method
            result = self.controller.on_connect_multiple_devices_requested([self.device1, self.device2])
            
            # Check that the method returns False
            self.assertFalse(result, "Method should return False when operation is already in progress")
            
            # Verify dialog was not created
            mock_dialog.assert_not_called()
    
    def test_connection_operation_exception_handling(self):
        """Test that the connection_operation_in_progress flag is reset even when exceptions occur."""
        # Mock the MultiConnectionDialog to raise an exception
        with patch('controllers.connection_controller.MultiConnectionDialog', side_effect=Exception("Test exception")):
            # Call the method
            result = self.controller.on_connect_multiple_devices_requested([self.device1, self.device2])
            
            # Check that the method returns False
            self.assertFalse(result, "Method should return False when an exception occurs")
            
            # Check that the flag is reset
            self.assertFalse(self.controller.connection_operation_in_progress, 
                            "connection_operation_in_progress flag should be reset even when exceptions occur")

    def test_connection_creates_mesh_network(self):
        """Test that mesh strategy correctly creates all connections between devices."""
        # Mock the MultiConnectionDialog
        with patch('controllers.connection_controller.MultiConnectionDialog') as mock_dialog:
            # Configure the dialog instance
            dialog_instance = MagicMock()
            mock_dialog.return_value = dialog_instance
            
            # Configure dialog to return Accepted and mesh network data
            dialog_instance.exec_.return_value = QDialog.Accepted
            dialog_instance.get_connection_data.return_value = {
                'strategy': 'mesh',
                'type': 'ethernet',
                'label': 'Test Connection',
                'bandwidth': '100',
                'latency': '10',
                'bidirectional': True
            }
            
            # Mock undo_redo_manager and commands
            self.controller.undo_redo_manager = MagicMock()
            self.controller.undo_redo_manager.is_in_command_execution.return_value = False
            
            # Mock _connection_exists to always return False (no existing connections)
            self.controller._connection_exists = MagicMock(return_value=False)
            
            # Mock the commands - fix by patching the controllers.commands module instead
            with patch('controllers.commands.CompositeCommand') as mock_composite_cmd, \
                 patch('controllers.commands.AddConnectionCommand') as mock_add_cmd:
                
                # Configure mock composite command
                composite_instance = MagicMock()
                mock_composite_cmd.return_value = composite_instance
                
                # Call the method with three devices
                result = self.controller.on_connect_multiple_devices_requested(
                    [self.device1, self.device2, self.device3]
                )
                
                # Check success
                self.assertTrue(result, "Method should return True on successful connections")
                
                # Verify dialog was shown exactly once
                mock_dialog.assert_called_once()
                dialog_instance.exec_.assert_called_once()
                
                # For 3 devices, we expect 6 connections (bidirectional mesh)
                # Each device connects to all other devices: 3*(3-1) = 6
                # 1→2, 1→3, 2→1, 2→3, 3→1, 3→2
                self.assertEqual(mock_add_cmd.call_count, 6,
                               "Should create 6 connections for mesh network with 3 devices")
                
                # Verify the composite command was pushed
                self.controller.undo_redo_manager.push_command.assert_called_once()
                
                # Verify flag was reset
                self.assertFalse(self.controller.connection_operation_in_progress)

    def test_connection_creates_chain_network(self):
        """Test that chain strategy correctly creates connections between devices in sequence."""
        
        # Mock the MultiConnectionDialog
        with patch('controllers.connection_controller.MultiConnectionDialog') as mock_dialog:
            # Configure the dialog instance
            dialog_instance = MagicMock()
            mock_dialog.return_value = dialog_instance
            
            # Configure dialog to return Accepted and chain network data
            dialog_instance.exec_.return_value = QDialog.Accepted
            dialog_instance.get_connection_data.return_value = {
                'strategy': 'chain',
                'type': 'ethernet',
                'label': 'Test Connection',
                'bandwidth': '100',
                'latency': '10',
                'bidirectional': True
            }
            
            # Mock sorting devices by position
            sorted_devices = [self.device1, self.device2, self.device3]
            
            # Mock the sorting function to return devices in order
            with patch('controllers.connection_controller.sorted', return_value=sorted_devices):
                # Mock undo_redo_manager and commands
                self.controller.undo_redo_manager = MagicMock()
                self.controller.undo_redo_manager.is_in_command_execution.return_value = False
                
                # Mock _connection_exists to always return False (no existing connections)
                self.controller._connection_exists = MagicMock(return_value=False)
                
                # Mock the commands - fix by patching the controllers.commands module instead
                with patch('controllers.commands.CompositeCommand') as mock_composite_cmd, \
                     patch('controllers.commands.AddConnectionCommand') as mock_add_cmd:
                    
                    # Configure mock composite command
                    composite_instance = MagicMock()
                    mock_composite_cmd.return_value = composite_instance
                    
                    # Call the method with three devices
                    result = self.controller.on_connect_multiple_devices_requested(
                        [self.device1, self.device2, self.device3]
                    )
                    
                    # Check success
                    self.assertTrue(result, "Method should return True on successful connections")
                    
                    # Verify dialog was shown exactly once
                    mock_dialog.assert_called_once()
                    dialog_instance.exec_.assert_called_once()
                    
                    # For 3 devices with bidirectional connections in a chain, we should have 4 connections
                    # 1->2, 2->1, 2->3, 3->2
                    self.assertEqual(mock_add_cmd.call_count, 4,
                                  "Should create 4 connections for chain network with 3 devices")
                    
                    # Verify the composite command was pushed
                    self.controller.undo_redo_manager.push_command.assert_called_once()
                    
                    # Verify flag was reset
                    self.assertFalse(self.controller.connection_operation_in_progress)

    def test_connection_operation_dialog_cleanup(self):
        """Test that the dialog is properly closed and cleaned up."""
        # Mock the MultiConnectionDialog
        with patch('controllers.connection_controller.MultiConnectionDialog') as mock_dialog:
            # Configure the dialog instance
            dialog_instance = MagicMock()
            mock_dialog.return_value = dialog_instance
            
            # Make dialog return Rejected
            dialog_instance.exec_.return_value = QDialog.Rejected
            
            # Call the method
            self.controller.on_connect_multiple_devices_requested([self.device1, self.device2])
            
            # Verify dialog was closed and destroyed
            dialog_instance.close.assert_called_once()
            dialog_instance.deleteLater.assert_called_once()

if __name__ == '__main__':
    unittest.main() 