from PyQt5.QtWidgets import QFormLayout, QLineEdit, QSpinBox
from PyQt5.QtCore import pyqtSignal

from .base_section import BaseSection

class GeneralSection(BaseSection):
    """Section for displaying general properties (common to all items)."""
    
    # Signals
    name_changed = pyqtSignal(str)
    z_value_changed = pyqtSignal(float)
    
    def __init__(self, parent=None):
        # Initialize fields as None before calling super().__init__
        self.name_edit = None
        self.z_index_spin = None
        
        # Call parent constructor
        super().__init__("General Properties", parent)
    
    def _init_ui(self):
        """Initialize the UI elements."""
        # If UI elements already exist, return to avoid duplication
        if self.name_edit is not None and self.z_index_spin is not None:
            return
            
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(8)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        self.name_edit.editingFinished.connect(
            lambda: self.name_changed.emit(self.name_edit.text())
        )
        form_layout.addRow("Name:", self.name_edit)
        
        # Z-Index (layer) control
        self.z_index_spin = QSpinBox()
        self.z_index_spin.setRange(-100, 100)
        self.z_index_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QSpinBox:focus {
                border: 1px solid #3498db;
            }
        """)
        self.z_index_spin.valueChanged.connect(
            lambda value: self.z_value_changed.emit(float(value))
        )
        form_layout.addRow("Layer (Z-Index):", self.z_index_spin)
        
        # Add form layout to main layout
        self.main_layout.addLayout(form_layout)
    
    def reset(self):
        """Reset all fields to their default state."""
        try:
            if self.name_edit:
                self.name_edit.clear()
            if self.z_index_spin:
                self.z_index_spin.setValue(0)
        except Exception as e:
            self._handle_error("reset", e)
    
    def set_name(self, name):
        """Set the name field."""
        try:
            if self.name_edit:
                self.name_edit.setText(name)
        except Exception as e:
            self._handle_error("set_name", e)
    
    def set_z_value(self, z_value):
        """Set the Z-value (layer) field."""
        try:
            if self.z_index_spin:
                self.z_index_spin.setValue(z_value)
        except Exception as e:
            self._handle_error("set_z_value", e) 