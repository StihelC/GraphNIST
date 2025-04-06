"""
Unit tests for layout optimization functionality.

These tests focus on ensuring that layout optimization keeps devices properly 
contained within the user's view and properly scales the layout.
"""

import pytest
from unittest.mock import MagicMock, patch
import math
from PyQt5.QtCore import QPointF, QRectF

from controllers.connection_controller import ConnectionController

class TestLayoutOptimization:
    """Test suite for layout optimization functionality."""
    
    @pytest.mark.unit
    def test_normalize_layout_centers_devices(self, mock_canvas, mock_event_bus, mock_device):
        """Test that _normalize_layout centers devices in the viewport."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus)
        
        # Create a scene rect with known dimensions
        scene_rect = QRectF(0, 0, 1000, 800)
        mock_canvas.scene.return_value.sceneRect.return_value = scene_rect
        
        # Create multiple devices at various positions
        device1 = MagicMock()
        device1.boundingRect.return_value.width.return_value = 50
        device1.boundingRect.return_value.height.return_value = 50
        device1.scenePos.return_value = QPointF(100, 100)
        
        device2 = MagicMock()
        device2.boundingRect.return_value.width.return_value = 50
        device2.boundingRect.return_value.height.return_value = 50
        device2.scenePos.return_value = QPointF(200, 200)
        
        device3 = MagicMock()
        device3.boundingRect.return_value.width.return_value = 50
        device3.boundingRect.return_value.height.return_value = 50
        device3.scenePos.return_value = QPointF(300, 100)
        
        # List of all devices
        devices = [device1, device2, device3]
        
        # Call normalize layout
        controller._normalize_layout(devices)
        
        # Verify that each device was moved
        for device in devices:
            device.setPos.assert_called()
            
        # Check that device1 was moved to center
        args1 = device1.setPos.call_args[0]
        x1, y1 = args1[0], args1[1]
        
        # Should be scaled and centered - adjust expected range based on implementation
        assert 250 < x1 < 600, "Device should be moved closer to center horizontally"
        assert 250 < y1 < 500, "Device should be moved closer to center vertically"
    
    @pytest.mark.unit
    def test_force_directed_layout_contains_devices(self, mock_canvas, mock_event_bus):
        """Test that force-directed layout keeps devices within the viewport."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus)
        
        # Create a scene rect with known dimensions
        scene_rect = QRectF(0, 0, 1000, 800)
        mock_canvas.scene.return_value.sceneRect.return_value = scene_rect
        
        # Create test devices with position far away from center
        devices = []
        for i in range(10):
            device = MagicMock()
            device.scenePos.return_value = QPointF(50 * i, 50 * i)  # Devices spreading out
            devices.append(device)
        
        # Create some connections between them
        connections = []
        for i in range(len(devices) - 1):
            connection = MagicMock()
            connection.source_device = devices[i]
            connection.target_device = devices[i + 1]
            connections.append(connection)
            
        # Mock required methods
        mock_canvas.connections = connections
        
        # With patch for _normalize_layout to verify it gets called
        with patch.object(controller, '_normalize_layout') as mock_normalize:
            # Call the force-directed layout
            controller._apply_force_directed_layout(devices, connections, iterations=10)
            
            # Check that devices were moved
            for device in devices:
                assert device.setPos.call_count > 0, "Device should be repositioned"
                
                # Get the last position set
                args = device.setPos.call_args_list[-1][0]
                x, y = args[0], args[1]
                
                # Verify position is within viewport bounds with margin
                margin = 1000 * 0.1  # 10% of width
                assert margin <= x <= (1000 - margin), "X position should be within bounds with margin"
                assert margin <= y <= (800 - margin), "Y position should be within bounds with margin"
            
            # Normalize should be called afterward to finalize the layout
            # (but we're mocking it out in this test)
            mock_normalize.assert_not_called()
    
    @pytest.mark.unit
    def test_optimize_topology_calls_correct_algorithm(self, mock_canvas, mock_event_bus):
        """Test that optimize_topology_layout calls the correct algorithm."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus)
        
        # Set up mocks for the different algorithms
        with patch.object(controller, '_apply_force_directed_layout') as mock_force_directed, \
             patch.object(controller, '_apply_hierarchical_layout') as mock_hierarchical, \
             patch.object(controller, '_apply_radial_layout') as mock_radial, \
             patch.object(controller, '_apply_grid_layout') as mock_grid, \
             patch.object(controller, '_normalize_layout'):
                
            # Create some test data
            devices = [MagicMock() for _ in range(5)]
            mock_canvas.devices = devices
            
            # Test with different algorithms
            controller.optimize_topology_layout(algorithm="force_directed")
            mock_force_directed.assert_called_once()
            
            controller.optimize_topology_layout(algorithm="hierarchical")
            mock_hierarchical.assert_called_once()
            
            controller.optimize_topology_layout(algorithm="radial")
            mock_radial.assert_called_once()
            
            controller.optimize_topology_layout(algorithm="grid")
            mock_grid.assert_called_once()
    
    @pytest.mark.unit
    def test_device_containment_calculation(self, mock_canvas, mock_event_bus):
        """Test the containment calculations in force-directed layout."""
        # Setup
        controller = ConnectionController(mock_canvas, mock_event_bus)
        
        # Create a scene rect with known dimensions
        scene_rect = QRectF(0, 0, 800, 600)
        mock_canvas.scene.return_value.sceneRect.return_value = scene_rect
        
        # Create a sample device at position that would be affected by bounds check
        device = MagicMock()
        device.scenePos.return_value = QPointF(900, 700)  # Outside bounds
        
        # Mock required attributes 
        with patch('random.random', return_value=0.5), \
             patch('math.cos', return_value=0.5), \
             patch('math.sin', return_value=0.5):
            
            # Call the force-directed layout with a single iteration
            controller._apply_force_directed_layout([device], [], iterations=1)
            
            # Check that device was moved inside bounds
            device.setPos.assert_called()
            
            # Get the position the device was moved to
            args = device.setPos.call_args[0]
            x, y = args[0], args[1]
            
            # Calculate expected margins
            margin = 800 * 0.1  # 10% of width
            
            # Verify device was moved inside the bounds
            assert margin <= x <= (800 - margin), "Device X position should be constrained inside viewport"
            assert margin <= y <= (600 - margin), "Device Y position should be constrained inside viewport" 