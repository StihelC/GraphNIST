"""
Tests for the layout optimization dialog.

This tests the UI aspects of layout optimization, particularly the presence
of the experimental tag we added.
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QLabel, QDialog, QApplication

from views.layout_optimization_dialog import LayoutOptimizationDialog

class TestLayoutOptimizationDialog:
    """Test suite for LayoutOptimizationDialog."""
    
    @pytest.mark.unit
    def test_experimental_tag_exists(self, app):
        """Test that the experimental tag is displayed in the dialog."""
        # Create the dialog
        dialog = LayoutOptimizationDialog()
        
        # Find all QLabels in the dialog
        labels = dialog.findChildren(QLabel)
        
        # Check if any label contains the experimental tag text
        experimental_text = "EXPERIMENTAL: Topology optimization is still under development"
        found_experimental_tag = False
        
        for label in labels:
            if experimental_text in label.text():
                found_experimental_tag = True
                
                # Also check if the label has appropriate styling
                assert "color: #FF6700" in label.styleSheet(), "Experimental tag should have warning color"
                assert "border: 1px solid" in label.styleSheet(), "Experimental tag should have a border"
                break
        
        assert found_experimental_tag, "Dialog should display an experimental warning tag"
    
    @pytest.mark.unit
    def test_algorithm_selection(self, app):
        """Test that algorithm selection works correctly."""
        # Create the dialog
        dialog = LayoutOptimizationDialog()
        
        # Check default selection is force-directed
        assert dialog.get_selected_algorithm() == "force_directed"
        
        # Select different algorithms and verify
        dialog.hierarchical_radio.setChecked(True)
        assert dialog.get_selected_algorithm() == "hierarchical"
        
        dialog.radial_radio.setChecked(True)
        assert dialog.get_selected_algorithm() == "radial"
        
        dialog.grid_radio.setChecked(True)
        assert dialog.get_selected_algorithm() == "grid"
    
    @pytest.mark.unit
    def test_parameters_return_value(self, app):
        """Test that get_parameters returns the correct values."""
        # Create the dialog
        dialog = LayoutOptimizationDialog()
        
        # Get parameters with default values
        params = dialog.get_parameters()
        
        # Check default values
        assert params['algorithm'] == "force_directed"
        assert params['selected_only'] == True
        assert params['iterations'] == 50
        
        # Change values
        dialog.force_iterations.setValue(100)
        dialog.all_devices_radio.setChecked(True)
        dialog.radial_radio.setChecked(True)
        
        # Get updated parameters
        params = dialog.get_parameters()
        
        # Check updated values
        assert params['algorithm'] == "radial"
        assert params['selected_only'] == False
        assert params['iterations'] == 50  # Should still be 50 since radial layout doesn't use iterations 