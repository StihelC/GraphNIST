from PyQt5.QtWidgets import (
    QFormLayout, QLineEdit, QHBoxLayout, QPushButton, 
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QColorDialog
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor

from .base_section import BaseSection

class BoundarySection(BaseSection):
    """Section for displaying boundary-specific properties."""
    
    # Signals
    property_changed = pyqtSignal(str, object)
    device_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        # Initialize attributes before calling super().__init__
        # Boundary references
        self.current_boundary = None
        self.multiple_boundaries = []
        self.contained_devices = []
        
        # Boundary UI elements
        self.boundary_name_edit = None
        self.color_button = None
        self.boundary_font_size_spin = None
        self.boundary_devices_table = None
        
        # Call parent constructor
        super().__init__("Boundary Properties", parent)
        
    def _init_ui(self):
        """Initialize the UI elements."""
        try:
            # If UI elements already exist, return to avoid duplication
            if self.boundary_name_edit is not None and self.color_button is not None:
                return
                
            form_layout = QFormLayout()
            form_layout.setVerticalSpacing(8)
            
            # Boundary name
            self.boundary_name_edit = QLineEdit()
            self.boundary_name_edit.editingFinished.connect(
                lambda: self.property_changed.emit('name', self.boundary_name_edit.text())
            )
            form_layout.addRow("Name:", self.boundary_name_edit)
            
            # Color selection
            color_layout = QHBoxLayout()
            self.color_button = QPushButton("Change Color")
            self.color_button.clicked.connect(self._on_boundary_color_change)
            color_layout.addWidget(self.color_button)
            color_layout.addStretch()
            form_layout.addRow("Color:", color_layout)
            
            # Font size
            self.boundary_font_size_spin = QSpinBox()
            self.boundary_font_size_spin.setRange(8, 50)
            self.boundary_font_size_spin.setSuffix(" pt")
            self.boundary_font_size_spin.valueChanged.connect(
                lambda value: self.property_changed.emit('font_size', value)
            )
            form_layout.addRow("Text Size:", self.boundary_font_size_spin)
            
            # Contained devices table
            self.boundary_devices_table = QTableWidget(0, 2)
            self.boundary_devices_table.setHorizontalHeaderLabels(["Device Name", "Type"])
            self.boundary_devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.boundary_devices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.boundary_devices_table.setMinimumHeight(150)
            self.boundary_devices_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.boundary_devices_table.setSelectionMode(QTableWidget.SingleSelection)
            self.boundary_devices_table.itemClicked.connect(self._on_boundary_device_clicked)
            form_layout.addRow("Contained Devices:", self.boundary_devices_table)
            
            # Add form layout to main layout
            self.main_layout.addLayout(form_layout)
            
        except Exception as e:
            self._handle_error("_init_ui", e)
    
    def reset(self):
        """Reset all fields to their default state."""
        try:
            # Reset boundary references
            self.current_boundary = None
            self.multiple_boundaries = []
            self.contained_devices = []
            
            # Reset boundary UI elements
            if self.boundary_name_edit:
                self.boundary_name_edit.clear()
            
            if self.boundary_font_size_spin:
                self.boundary_font_size_spin.setValue(12)  # Default font size
            
            # Reset the color button
            self._update_color_button(QColor(0, 114, 178))  # Default color
            
            # Clear the devices table
            if self.boundary_devices_table:
                self.boundary_devices_table.setRowCount(0)
                
        except Exception as e:
            self._handle_error("reset", e)
    
    def set_boundary(self, boundary):
        """Set the boundary to display properties for."""
        try:
            # Store reference to boundary
            self.current_boundary = boundary
            self.multiple_boundaries = []
            
            # Ensure UI components are initialized
            if self.boundary_name_edit is None or self.color_button is None or self.boundary_font_size_spin is None:
                self._init_ui()  # Re-initialize UI if components are missing
                
            # Check if UI components still haven't been initialized
            if self.color_button is None:
                self.logger.error("UI components not properly initialized in BoundarySection")
                return
            
            # Update color button appearance based on boundary color
            if hasattr(boundary, 'color'):
                self._update_color_button(boundary.color)
            
            # Update font size spinner value based on boundary's label font size
            if hasattr(boundary, 'get_font_size') and self.boundary_font_size_spin:
                font_size = boundary.get_font_size()
                self.boundary_font_size_spin.setValue(font_size)
            
            # Update boundary name
            if hasattr(boundary, 'name') and self.boundary_name_edit:
                self.boundary_name_edit.setText(boundary.name)
            
            # Update contained devices table (uses devices previously set by set_contained_devices)
            self._update_devices_table()
            
        except Exception as e:
            self._handle_error("set_boundary", e)
    
    def set_contained_devices(self, devices):
        """Set the list of devices contained within the selected boundary."""
        try:
            self.contained_devices = devices
            self._update_devices_table()
            
        except Exception as e:
            self._handle_error("set_contained_devices", e)
    
    def _update_devices_table(self):
        """Update the devices table with the current contained devices."""
        try:
            # Ensure UI components are initialized
            if self.boundary_devices_table is None:
                self._init_ui()  # Re-initialize UI if components are missing
                
            # Check if UI components still haven't been initialized
            if self.boundary_devices_table is None:
                self.logger.error("UI components not properly initialized in BoundarySection")
                return
                
            # Clear and update the devices table
            self.boundary_devices_table.setRowCount(0)
            
            # Add devices to the table
            for row, device in enumerate(self.contained_devices):
                self.boundary_devices_table.insertRow(row)
                
                # Device name column
                name_item = QTableWidgetItem(device.name if hasattr(device, 'name') else "Unnamed")
                name_item.setData(Qt.UserRole, device)  # Store device reference
                self.boundary_devices_table.setItem(row, 0, name_item)
                
                # Device type column
                device_type = "Unknown"
                if hasattr(device, 'device_type'):
                    device_type = device.device_type.capitalize()
                type_item = QTableWidgetItem(device_type)
                self.boundary_devices_table.setItem(row, 1, type_item)
                
        except Exception as e:
            self._handle_error("_update_devices_table", e)
    
    def set_multiple_boundaries(self, boundaries):
        """Set multiple boundaries for batch editing."""
        try:
            # Store references
            self.current_boundary = None
            self.multiple_boundaries = boundaries
            
            # Ensure UI components are initialized
            if self.boundary_name_edit is None or self.color_button is None or self.boundary_font_size_spin is None:
                self._init_ui()  # Re-initialize UI if components are missing
                
            # Check if UI components still haven't been initialized
            if self.color_button is None or self.boundary_font_size_spin is None:
                self.logger.error("UI components not properly initialized in BoundarySection")
                return
            
            # Get the most common color
            colors = {}
            for boundary in boundaries:
                if hasattr(boundary, 'color'):
                    color = boundary.color
                    color_key = f"{color.red()},{color.green()},{color.blue()}"
                    if color_key in colors:
                        colors[color_key] += 1
                    else:
                        colors[color_key] = 1
            
            # Display the most common color
            if colors:
                most_common_color = max(colors.items(), key=lambda x: x[1])[0]
                r, g, b = map(int, most_common_color.split(','))
                self._update_color_button(QColor(r, g, b))
            
            # Get the most common font size
            font_sizes = {}
            for boundary in boundaries:
                if hasattr(boundary, 'get_font_size'):
                    size = boundary.get_font_size()
                    if size in font_sizes:
                        font_sizes[size] += 1
                    else:
                        font_sizes[size] = 1
            
            # Display the most common font size
            if font_sizes and self.boundary_font_size_spin:
                most_common_size = max(font_sizes.items(), key=lambda x: x[1])[0]
                self.boundary_font_size_spin.setValue(most_common_size)
            
            # Clear the devices table since it doesn't apply to multiple boundaries
            if self.boundary_devices_table:
                self.boundary_devices_table.setRowCount(0)
            self.contained_devices = []
            
        except Exception as e:
            self._handle_error("set_multiple_boundaries", e)
    
    def _update_color_button(self, color):
        """Update the color button to show the current boundary color."""
        try:
            if not self.color_button:
                return
                
            # Create style with the current color as background
            rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255.0})"
            text_color = "white" if color.lightness() < 128 else "black"
            
            style = f"""
                QPushButton {{
                    background-color: {rgba};
                    color: {text_color};
                    padding: 4px 8px;
                    border: 1px solid #888;
                }}
                QPushButton:hover {{
                    border: 1px solid #333;
                }}
            """
            self.color_button.setStyleSheet(style)
            
        except Exception as e:
            self._handle_error("_update_color_button", e)
    
    def _on_boundary_color_change(self):
        """Handle boundary color change request."""
        try:
            if not self.current_boundary and not self.multiple_boundaries:
                return
                
            current_color = None
            if self.current_boundary and hasattr(self.current_boundary, 'color'):
                current_color = self.current_boundary.color
            
            # Open color dialog with current color preselected
            color_dialog = QColorDialog(self)
            if current_color:
                color_dialog.setCurrentColor(current_color)
            
            if color_dialog.exec_():
                selected_color = color_dialog.selectedColor()
                # Update the button appearance
                self._update_color_button(selected_color)
                # Pass the color to the controller
                self.property_changed.emit("color", selected_color)
                
        except Exception as e:
            self._handle_error("_on_boundary_color_change", e)
    
    def _on_boundary_device_clicked(self, item):
        """Handle clicking on a device in the boundary's contained devices table."""
        try:
            if item is None:
                return
                
            # Get the device reference from the first column
            device = self.boundary_devices_table.item(item.row(), 0).data(Qt.UserRole)
            if device:
                # Emit signal to select the clicked device
                self.device_selected.emit(device)
                
        except Exception as e:
            self._handle_error("_on_boundary_device_clicked", e) 