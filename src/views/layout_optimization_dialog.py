from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialogButtonBox, 
    QGroupBox, QRadioButton, QSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt

class LayoutOptimizationDialog(QDialog):
    """Dialog for selecting layout optimization algorithm and parameters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optimize Network Layout")
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Experimental tag
        experimental_label = QLabel("⚠️ EXPERIMENTAL: Topology optimization is still under development")
        experimental_label.setStyleSheet("color: #FF6700; font-weight: bold; padding: 5px; border: 1px solid #FF6700; border-radius: 4px;")
        experimental_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(experimental_label)
        
        # Header
        header_label = QLabel("Select layout algorithm to organize the network topology:")
        header_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(header_label)
        
        # Description
        description = QLabel(
            "Layout optimization will rearrange devices to minimize connection crossings "
            "and create a more aesthetically pleasing topology."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Algorithm selection group
        algorithm_group = QGroupBox("Layout Algorithm")
        algorithm_layout = QVBoxLayout()
        
        # Force-directed option
        self.force_directed_radio = QRadioButton("Force-Directed Layout")
        self.force_directed_radio.setToolTip(
            "Simulates physical forces between nodes for an organic-looking layout. "
            "Best for complex networks with many connections."
        )
        algorithm_layout.addWidget(self.force_directed_radio)
        
        # Force-directed parameters
        force_params = QFormLayout()
        self.force_iterations = QSpinBox()
        self.force_iterations.setRange(20, 200)
        self.force_iterations.setValue(50)
        self.force_iterations.setToolTip("More iterations can produce better results but take longer")
        force_params.addRow("Iterations:", self.force_iterations)
        algorithm_layout.addLayout(force_params)
        
        # Hierarchical option
        self.hierarchical_radio = QRadioButton("Hierarchical Layout")
        self.hierarchical_radio.setToolTip(
            "Organizes devices in levels/layers based on their connectivity. "
            "Good for showing network hierarchy and dependencies."
        )
        algorithm_layout.addWidget(self.hierarchical_radio)
        
        # Radial option
        self.radial_radio = QRadioButton("Radial Layout")
        self.radial_radio.setToolTip(
            "Arranges devices in concentric circles around a central node. "
            "Best for networks with a central device connecting to others."
        )
        algorithm_layout.addWidget(self.radial_radio)
        
        # Grid option
        self.grid_radio = QRadioButton("Grid Layout")
        self.grid_radio.setToolTip(
            "Arranges devices in a uniform grid pattern. "
            "Provides a clean, structured layout regardless of connections."
        )
        algorithm_layout.addWidget(self.grid_radio)
        
        # Set force-directed as default
        self.force_directed_radio.setChecked(True)
        
        # Enable/disable parameters based on selection
        self.force_directed_radio.toggled.connect(
            lambda checked: self.force_iterations.setEnabled(checked))
        
        algorithm_group.setLayout(algorithm_layout)
        layout.addWidget(algorithm_group)
        
        # Options for selected devices only
        options_group = QGroupBox("Scope")
        options_layout = QVBoxLayout()
        
        self.selected_only_radio = QRadioButton("Optimize selected devices only")
        self.all_devices_radio = QRadioButton("Optimize all devices")
        
        options_layout.addWidget(self.selected_only_radio)
        options_layout.addWidget(self.all_devices_radio)
        
        # Set default based on current selection
        self.selected_only_radio.setChecked(True)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_selected_algorithm(self):
        """Get the selected layout algorithm."""
        if self.force_directed_radio.isChecked():
            return "force_directed"
        elif self.hierarchical_radio.isChecked():
            return "hierarchical"
        elif self.radial_radio.isChecked():
            return "radial"
        elif self.grid_radio.isChecked():
            return "grid"
        return "force_directed"  # Default
    
    def get_parameters(self):
        """Get the selected parameters as a dictionary."""
        params = {
            'algorithm': self.get_selected_algorithm(),
            'selected_only': self.selected_only_radio.isChecked(),
            'iterations': self.force_iterations.value() if self.force_directed_radio.isChecked() else 50
        }
        return params 