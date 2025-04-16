from PyQt5.QtWidgets import (
    QFormLayout, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout,
    QHBoxLayout, QCheckBox, QLabel, QWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
import logging

from .base_section import BaseSection

class DeviceSection(BaseSection):
    """Section for displaying and editing device-specific properties."""
    
    # Signals
    property_changed = pyqtSignal(str, object)
    display_toggled = pyqtSignal(str, bool)
    property_deleted = pyqtSignal(str)
    change_icon_requested = pyqtSignal(object)
    
    def __init__(self, parent=None):
        # Initialize components before calling super().__init__
        self.device = None
        self.property_table = None
        self.add_property_button = None
        self.change_icon_button = None
        
        # Call parent constructor
        super().__init__("Device Properties", parent)
    
    def _init_ui(self):
        """Initialize the UI elements."""
        # If UI elements already exist, return to avoid duplication
        if self.property_table is not None:
            return
            
        # Create property table
        self.property_table = QTableWidget(0, 3)  # 0 rows initially, 3 columns (Key, Value, Display)
        self.property_table.setHorizontalHeaderLabels(["Property", "Value", "Display"])
        self.property_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.property_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.property_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.property_table.setAlternatingRowColors(True)
        self.property_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                alternate-background-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 5px;
                border: 1px solid #2980b9;
            }
        """)
        
        # Add property button
        self.add_property_button = QPushButton("Add Property")
        self.add_property_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.add_property_button.clicked.connect(self._add_property)
        
        # Change icon button
        self.change_icon_button = QPushButton("Change Icon")
        self.change_icon_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.change_icon_button.clicked.connect(self._request_icon_change)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_property_button)
        button_layout.addWidget(self.change_icon_button)
        
        # Add widgets to main layout
        self.main_layout.addWidget(self.property_table)
        self.main_layout.addLayout(button_layout)
    
    def reset(self):
        """Reset all fields to their default state."""
        try:
            if self.property_table:
                self.property_table.setRowCount(0)
            self.device = None
        except Exception as e:
            self._handle_error("reset", e)
    
    def set_device(self, device):
        """Set the device and update the display."""
        try:
            self.device = device
            self._update_properties()
        except Exception as e:
            self._handle_error("set_device", e)
    
    def set_multiple_devices(self, devices):
        """Handle display for multiple device selection."""
        try:
            # Reset current display
            self.reset()
            
            if not self.property_table:
                return
                
            # Store devices for property updates
            self.devices = devices
            
            # Find common properties across all devices
            common_properties = {}
            if devices:
                # Get properties from first device as baseline
                first_device = devices[0]
                if hasattr(first_device, 'properties'):
                    for key, value in first_device.properties.items():
                        # Check if this property exists in all devices with the same value
                        is_common = True
                        common_value = value
                        for device in devices[1:]:
                            if not hasattr(device, 'properties') or key not in device.properties:
                                is_common = False
                                break
                            if device.properties[key] != value:
                                is_common = False
                                break
                        if is_common:
                            common_properties[key] = common_value
            
            # Show header with device count
            self.property_table.setRowCount(0)
            self.property_table.setHorizontalHeaderLabels(["Property", "Value", "Display"])
            self.property_table.horizontalHeader().show()
            
            # Add common properties to table
            for key, value in common_properties.items():
                self._add_property_to_table(key, value)
            
            # Enable add property button but with modified tooltip
            if self.add_property_button:
                self.add_property_button.setEnabled(True)
                self.add_property_button.setToolTip("Add property to all selected devices")
            
            # Enable change icon button for bulk icon change
            if self.change_icon_button:
                self.change_icon_button.setEnabled(True)
                self.change_icon_button.setToolTip("Change icon for all selected devices")
                
        except Exception as e:
            self._handle_error("set_multiple_devices", e)
    
    def _update_properties(self):
        """Update the property table with device properties."""
        if not self.device or not self.property_table:
            return
            
        # Clear existing properties
        self.property_table.setRowCount(0)
        
        # Add device properties to table
        if hasattr(self.device, 'properties') and self.device.properties:
            for key, value in self.device.properties.items():
                self._add_property_to_table(key, value)
                
        # Enable buttons for single device
        if self.add_property_button:
            self.add_property_button.setEnabled(True)
        if self.change_icon_button:
            self.change_icon_button.setEnabled(True)
    
    def _add_property_to_table(self, key, value):
        """Add a property to the table."""
        if not self.property_table:
            return
            
        # Get current row count
        row = self.property_table.rowCount()
        self.property_table.insertRow(row)
        
        # Create key item
        key_item = QTableWidgetItem(key)
        key_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        
        # Create value item
        # Handle different value formats (dict, string, or other)
        if isinstance(value, dict) and 'value' in value:
            value_text = str(value.get('value', ''))
            is_displayed = value.get('display', False)
        elif isinstance(value, str):
            value_text = value
            is_displayed = False
        else:
            value_text = str(value) if value is not None else ''
            is_displayed = False

        # Check display state if we have a single device
        if hasattr(self, 'device') and self.device and hasattr(self.device, 'get_property_display_state'):
            is_displayed = self.device.get_property_display_state(key)
            
        value_item = QTableWidgetItem(value_text)
        value_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        
        # Set items in table
        self.property_table.setItem(row, 0, key_item)
        self.property_table.setItem(row, 1, value_item)
        
        # Create display checkbox
        display_widget = QWidget()
        display_layout = QHBoxLayout(display_widget)
        display_layout.setContentsMargins(5, 0, 5, 0)
        display_layout.setAlignment(Qt.AlignCenter)
        
        display_checkbox = QCheckBox()
        display_checkbox.setChecked(is_displayed)
        
        # For multiple devices, check if display state is consistent
        if hasattr(self, 'devices') and self.devices:
            # Disable checkbox when multiple devices are selected with different display states
            all_displayed = True
            none_displayed = True
            
            for device in self.devices:
                if hasattr(device, 'get_property_display_state'):
                    display_state = device.get_property_display_state(key)
                    if display_state:
                        none_displayed = False
                    else:
                        all_displayed = False
            
            # Set checkbox state based on consensus
            if all_displayed:
                display_checkbox.setChecked(True)
            elif none_displayed:
                display_checkbox.setChecked(False)
            else:
                # Mixed state - partially checked
                display_checkbox.setTristate(True)
                display_checkbox.setCheckState(Qt.PartiallyChecked)
                
            # Connect state changed signal with proper handling for multiple devices
            display_checkbox.stateChanged.connect(
                lambda state, k=key: self._handle_display_state_change(k, state)
            )
        else:
            # Single device case
            display_checkbox.stateChanged.connect(
                lambda state, k=key: self.display_toggled.emit(k, state == Qt.Checked)
            )
        
        delete_button = QPushButton("×")  # Using × character as delete icon
        delete_button.setMaximumWidth(25)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_button.clicked.connect(lambda _, k=key: self._delete_property(k))
        
        display_layout.addWidget(display_checkbox)
        display_layout.addWidget(delete_button)
        
        self.property_table.setCellWidget(row, 2, display_widget)
        
        # Connect item changed signals
        self.property_table.itemChanged.connect(self._property_changed)
    
    def _property_changed(self, item):
        """Handle property changes in the table."""
        # Get row and column of changed item
        row = item.row()
        col = item.column()
        
        # Only process if key or value columns were changed
        if col not in [0, 1]:
            return
            
        try:
            # Get the key and value
            key_item = self.property_table.item(row, 0)
            value_item = self.property_table.item(row, 1)
            
            # Check if both exist
            if key_item and value_item:
                new_key = key_item.text()
                value = value_item.text()
                
                # Temporarily disconnect to avoid recursion
                self.property_table.itemChanged.disconnect(self._property_changed)
                
                if hasattr(self, 'devices') and self.devices:
                    # Bulk edit mode - apply to all selected devices
                    for device in self.devices:
                        try:
                            if col == 0:
                                # Key changed - handle renaming for all devices
                                old_key = list(device.properties.keys())[row] if row < len(device.properties) else ""
                                if old_key != new_key:
                                    # Get display state
                                    display_widget = self.property_table.cellWidget(row, 2)
                                    display_checkbox = display_widget.layout().itemAt(0).widget()
                                    display_value = display_checkbox.isChecked()
                                    
                                    # Update property for each device
                                    if old_key in device.properties:
                                        # Preserve the existing value and display state
                                        old_value = device.properties[old_key]
                                        if isinstance(old_value, dict):
                                            old_display = old_value.get('display', False)
                                        else:
                                            old_display = False
                                        
                                        # Delete old key
                                        del device.properties[old_key]
                                        
                                        # Set new key with preserved values
                                        device.properties[new_key] = {
                                            'value': value,
                                            'display': old_display
                                        }
                                        
                                        # Update property display if needed
                                        if hasattr(device, 'toggle_property_display'):
                                            device.toggle_property_display(new_key, old_display)
                                        
                                        # Emit property changed signal
                                        if hasattr(device.signals, 'property_changed'):
                                            device.signals.property_changed.emit(device, new_key, {
                                                'value': value,
                                                'display': old_display
                                            })
                            else:
                                # Value changed - update value for all devices
                                if new_key in device.properties:
                                    # Preserve display state
                                    old_value = device.properties[new_key]
                                    if isinstance(old_value, dict):
                                        old_display = old_value.get('display', False)
                                    else:
                                        old_display = False
                                    
                                    # Update value while preserving display state
                                    device.properties[new_key] = {
                                        'value': value,
                                        'display': old_display
                                    }
                                    
                                    # Emit property changed signal
                                    if hasattr(device.signals, 'property_changed'):
                                        device.signals.property_changed.emit(device, new_key, {
                                            'value': value,
                                            'display': old_display
                                        })
                            
                            # Force update of property labels for this device
                            if hasattr(device, 'update_property_labels'):
                                device.update_property_labels()
                                
                        except Exception as e:
                            self.logger.error(f"Error updating property for device {device.name}: {str(e)}")
                            continue
                            
                elif self.device:
                    # Single device mode - original behavior
                    old_key = list(self.device.properties.keys())[row] if row < len(self.device.properties) else ""
                    if col == 0 and old_key != new_key:
                        # Handle key change
                        display_widget = self.property_table.cellWidget(row, 2)
                        display_checkbox = display_widget.layout().itemAt(0).widget()
                        display_value = display_checkbox.isChecked()
                        
                        if old_key in self.device.properties:
                            # Preserve the existing value and display state
                            old_value = self.device.properties[old_key]
                            if isinstance(old_value, dict):
                                old_display = old_value.get('display', False)
                            else:
                                old_display = False
                            
                            # Delete old key
                            del self.device.properties[old_key]
                            
                            # Set new key with preserved values
                            self.device.properties[new_key] = {
                                'value': value,
                                'display': old_display
                            }
                            
                            # Update property display if needed
                            if hasattr(self.device, 'toggle_property_display'):
                                self.device.toggle_property_display(new_key, old_display)
                                
                            # Emit property changed signal
                            if hasattr(self.device.signals, 'property_changed'):
                                self.device.signals.property_changed.emit(self.device, new_key, {
                                    'value': value,
                                    'display': old_display
                                })
                    else:
                        # Handle value change
                        if new_key in self.device.properties:
                            # Preserve display state
                            old_value = self.device.properties[new_key]
                            if isinstance(old_value, dict):
                                old_display = old_value.get('display', False)
                            else:
                                old_display = False
                            
                            # Update value while preserving display state
                            self.device.properties[new_key] = {
                                'value': value,
                                'display': old_display
                            }
                            
                            # Emit property changed signal
                            if hasattr(self.device.signals, 'property_changed'):
                                self.device.signals.property_changed.emit(self.device, new_key, {
                                    'value': value,
                                    'display': old_display
                                })
                
                # Reconnect signal
                self.property_table.itemChanged.connect(self._property_changed)
                
                # Force update of all property labels
                if hasattr(self, 'devices') and self.devices:
                    for device in self.devices:
                        if hasattr(device, 'update_property_labels'):
                            device.update_property_labels()
                elif self.device and hasattr(self.device, 'update_property_labels'):
                    self.device.update_property_labels()
                    
        except Exception as e:
            self._handle_error("_property_changed", e)
    
    def _add_property(self):
        """Add a new property."""
        if not self.device:
            return
            
        # Create a new property with default values
        default_key = f"property{len(self.device.properties) + 1}"
        default_value = {'value': '', 'display': False}
        
        # Add to table
        self._add_property_to_table(default_key, default_value)
        
        # Signal the property change
        self.property_changed.emit(default_key, default_value)
    
    def _delete_property(self, key):
        """Delete a property."""
        if not self.device or not self.property_table:
            return
            
        try:
            # Find the row with this key
            for row in range(self.property_table.rowCount()):
                key_item = self.property_table.item(row, 0)
                if key_item and key_item.text() == key:
                    # Remove from table
                    self.property_table.removeRow(row)
                    # Signal deletion
                    self.property_deleted.emit(key)
                    break
        except Exception as e:
            self._handle_error("_delete_property", e)
    
    def _request_icon_change(self):
        """Request a change of icon for the device."""
        if self.device:
            self.change_icon_requested.emit(self.device)
    
    def _handle_display_state_change(self, key, state):
        """Handle display state changes for multiple devices."""
        if not hasattr(self, 'devices') or not self.devices:
            return
            
        # If in mixed state (PartiallyChecked), set all to checked
        if state == Qt.PartiallyChecked:
            state = Qt.Checked
            
        # Apply the new state to all devices
        for device in self.devices:
            if hasattr(device, 'toggle_property_display'):
                device.toggle_property_display(key, state == Qt.Checked)
                
        # Emit signal for the change
        self.display_toggled.emit(key, state == Qt.Checked) 