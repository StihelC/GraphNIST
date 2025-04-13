from PyQt5.QtWidgets import (
    QFormLayout, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton
)
from PyQt5.QtCore import pyqtSignal, Qt
import logging

from models.connection.connection import Connection, ConnectionTypes, RoutingStyle
from .base_section import BaseSection

class ConnectionSection(BaseSection):
    """Section for displaying connection-specific properties."""
    
    # Signals
    property_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        # Initialize attributes before calling super().__init__
        # Connection references
        self.current_connection = None
        self.multiple_connections = []
        
        # Connection UI elements
        self.connection_type_combo = None
        self.line_style_combo = None
        self.connection_props_table = None
        
        # Call parent constructor
        super().__init__("Connection Properties", parent)
        
    def _init_ui(self):
        """Initialize the UI elements."""
        try:
            # If UI elements already exist, return to avoid duplication
            if self.connection_type_combo is not None and self.connection_props_table is not None:
                return
                
            form_layout = QFormLayout()
            form_layout.setVerticalSpacing(8)
            
            # Connection type
            self.connection_type_combo = QComboBox()
            self.connection_type_combo.addItems(["Ethernet", "Fiber", "Wireless", "Serial"])
            self.connection_type_combo.currentTextChanged.connect(
                lambda text: self.property_changed.emit('connection_type', text)
            )
            form_layout.addRow("Type:", self.connection_type_combo)
            
            # Line style
            self.line_style_combo = QComboBox()
            self.line_style_combo.addItems(["Straight", "Orthogonal", "Curved"])
            
            # Important: Use a flag to distinguish between programmatic updates and user changes
            self._style_combo_updating = False
            
            # Connect to a custom handler instead of directly emitting the signal
            self.line_style_combo.currentTextChanged.connect(self._on_line_style_changed)
            
            form_layout.addRow("Line Style:", self.line_style_combo)
            
            # Properties table
            self.connection_props_table = QTableWidget(0, 2)
            self.connection_props_table.setHorizontalHeaderLabels(["Property", "Value"])
            self.connection_props_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.connection_props_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.connection_props_table.setMinimumHeight(150)
            self.connection_props_table.cellChanged.connect(self._on_property_changed)
            form_layout.addRow("Properties:", self.connection_props_table)
            
            # Add form layout to main layout
            self.main_layout.addLayout(form_layout)
            
        except Exception as e:
            self._handle_error("_init_ui", e)
    
    def _on_line_style_changed(self, text):
        """Handle line style combo box changes, distinguishing user actions from programmatic updates."""
        # Only emit the signal if this was a user action, not a programmatic update
        if not self._style_combo_updating:
            self.property_changed.emit('line_style', text)
    
    def reset(self):
        """Reset all fields to their default state."""
        try:
            # Reset connection references
            self.current_connection = None
            self.multiple_connections = []
            
            # Reset connection UI elements
            if self.connection_type_combo:
                self.connection_type_combo.setCurrentIndex(0)
                self.connection_type_combo.setEnabled(True)
            
            if self.line_style_combo:
                self.line_style_combo.setCurrentIndex(0)
            
            # Clear the properties table
            if self.connection_props_table:
                self.connection_props_table.setRowCount(0)
                
        except Exception as e:
            self._handle_error("reset", e)
    
    def set_connection(self, connection):
        """Set the connection to display properties for."""
        try:
            if connection is None:
                self.clear()
                return
            
            # Store reference
            self.current_connection = connection
            self.multiple_connections = None
            
            # Ensure UI components are initialized
            if self.connection_type_combo is None or self.line_style_combo is None or self.connection_props_table is None:
                self._init_ui()  # Re-initialize UI if components are missing
            
            # Check if UI components still haven't been initialized
            if self.connection_props_table is None:
                self.logger.error("UI components not properly initialized in ConnectionSection")
                return
            
            # Disconnect signal to prevent firing while updating
            if self.connection_props_table:
                try:
                    self.connection_props_table.cellChanged.disconnect(self._on_property_changed)
                except Exception:
                    # Signal might not be connected
                    pass
            
            # Clear the properties table
            if self.connection_props_table:
                self.connection_props_table.setRowCount(0)
            
            # Set the connection type in combo box
            if hasattr(connection, 'connection_type') and self.connection_type_combo:
                type_index = {
                    "ethernet": 0,
                    "fiber": 1,
                    "wireless": 2,
                    "serial": 3
                }.get(connection.connection_type.lower(), 0)
                self.connection_type_combo.setCurrentIndex(type_index)
                self.connection_type_combo.setEnabled(True)  # Enable editing for single connection
            
            # Set the line style in combo box
            if hasattr(connection, 'routing_style') and self.line_style_combo:
                style_index = {
                    Connection.STYLE_STRAIGHT: 0,
                    Connection.STYLE_ORTHOGONAL: 1,
                    Connection.STYLE_CURVED: 2
                }.get(connection.routing_style, 0)
                
                # Set flag to prevent triggering style change signal
                self._style_combo_updating = True
                self.line_style_combo.setCurrentIndex(style_index)
                self._style_combo_updating = False
            
            # Display core connection properties
            properties = []
            
            # Check if connection has properties dictionary
            if hasattr(connection, 'properties') and connection.properties:
                # Use the properties dictionary
                for key, value in connection.properties.items():
                    if key not in ['connection_type', 'line_style']:  # Skip properties we handle with dedicated controls
                        properties.append((key, str(value) if value is not None else ""))
            else:
                # Fallback to individual attributes if properties dict doesn't exist
                if hasattr(connection, 'bandwidth'):
                    properties.append(("Bandwidth", connection.bandwidth if connection.bandwidth else ""))
                if hasattr(connection, 'latency'):
                    properties.append(("Latency", connection.latency if connection.latency else ""))
                
                # Use consistent label_text property for display
                if hasattr(connection, 'properties') and 'label_text' in connection.properties:
                    properties.append(("Label", connection.properties['label_text']))
                elif hasattr(connection, 'label_text'):
                    properties.append(("Label", connection.label_text))
                elif hasattr(connection, '_label_text'):
                    properties.append(("Label", connection._label_text if connection._label_text else ""))
                
                # Add source and target info
                if hasattr(connection, 'source_device') and connection.source_device:
                    properties.append(("Source", connection.source_device.name))
                if hasattr(connection, 'target_device') and connection.target_device:
                    properties.append(("Target", connection.target_device.name))
            
            # Add all properties to table
            if self.connection_props_table:
                for i, (key, value) in enumerate(properties):
                    self.connection_props_table.insertRow(i)
                    key_item = QTableWidgetItem(key)
                    key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make property name read-only
                    self.connection_props_table.setItem(i, 0, key_item)
                    self.connection_props_table.setItem(i, 1, QTableWidgetItem(str(value)))
            
            # Reconnect signal
            if self.connection_props_table:
                self.connection_props_table.cellChanged.connect(self._on_property_changed)
            
        except Exception as e:
            self._handle_error("set_connection", e)
            # Ensure signal is reconnected even if there's an error
            try:
                if self.connection_props_table:
                    self.connection_props_table.cellChanged.connect(self._on_property_changed)
            except:
                pass
    
    def set_multiple_connections(self, connections):
        """Set multiple connections for batch editing."""
        try:
            # Store references
            self.current_connection = None
            self.multiple_connections = connections
            
            # Ensure UI components are initialized
            if self.connection_type_combo is None or self.line_style_combo is None or self.connection_props_table is None:
                self._init_ui()  # Re-initialize UI if components are missing
            
            # Check if UI components still haven't been initialized
            if self.connection_props_table is None:
                self.logger.error("UI components not properly initialized in ConnectionSection")
                return
            
            # Disconnect signal to prevent firing while updating
            if self.connection_props_table:
                try:
                    self.connection_props_table.cellChanged.disconnect(self._on_property_changed)
                except Exception:
                    # Signal might not be connected
                    pass
            
            # Clear previous properties
            if self.connection_props_table:
                self.connection_props_table.setRowCount(0)
            
            # Set routing style in combo box - find most common style
            style_counts = {}
            for connection in connections:
                if hasattr(connection, 'routing_style'):
                    style = connection.routing_style
                    style_counts[style] = style_counts.get(style, 0) + 1
            
            # Set to most common style if one exists
            if style_counts:
                most_common_style = max(style_counts.items(), key=lambda x: x[1])[0]
                style_index = {
                    Connection.STYLE_STRAIGHT: 0,
                    Connection.STYLE_ORTHOGONAL: 1,
                    Connection.STYLE_CURVED: 2
                }.get(most_common_style, 0)
                
                # Set flag to prevent triggering style change signal
                self._style_combo_updating = True
                self.line_style_combo.setCurrentIndex(style_index)
                self._style_combo_updating = False
            
            # Set connection type
            if hasattr(connections[0], 'connection_type') and self.connection_type_combo:
                type_index = {
                    "ethernet": 0,
                    "fiber": 1,
                    "wireless": 2,
                    "serial": 3
                }.get(connections[0].connection_type.lower(), 0)
                self.connection_type_combo.setCurrentIndex(type_index)
                self.connection_type_combo.setEnabled(False)  # Disable type editing for multiple connections
            
            # Collect all properties from all connections
            all_properties = set()
            for conn in connections:
                if hasattr(conn, 'properties'):
                    for prop in conn.properties:
                        if prop not in ['connection_type', 'line_style']:  # Skip properties we handle with dedicated controls
                            all_properties.add(prop)
            
            # Add properties to table
            if self.connection_props_table:
                for i, prop in enumerate(sorted(all_properties)):
                    values = set()
                    for conn in connections:
                        if hasattr(conn, 'properties') and prop in conn.properties:
                            values.add(str(conn.properties[prop]))
                    
                    self.connection_props_table.insertRow(i)
                    key_item = QTableWidgetItem(prop)
                    key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
                    self.connection_props_table.setItem(i, 0, key_item)
                    
                    if len(values) == 1:
                        # All connections have the same value
                        value_item = QTableWidgetItem(values.pop())
                        self.connection_props_table.setItem(i, 1, value_item)
                    else:
                        # Clear the value if they differ
                        value_item = QTableWidgetItem("")
                        self.connection_props_table.setItem(i, 1, value_item)
            
            # Reconnect signal
            if self.connection_props_table:
                self.connection_props_table.cellChanged.connect(self._on_property_changed)
            
        except Exception as e:
            self._handle_error("set_multiple_connections", e)
            # Ensure signal is reconnected even if there's an error
            try:
                if self.connection_props_table:
                    self.connection_props_table.cellChanged.connect(self._on_property_changed)
            except:
                pass
    
    def _on_property_changed(self, row, column):
        """Handle changes in connection property table."""
        try:
            if column == 1:  # Only care about value column
                key = self.connection_props_table.item(row, 0).text()
                value = self.connection_props_table.item(row, 1).text()
                self.property_changed.emit(key, value)
                
        except Exception as e:
            self._handle_error("_on_property_changed", e) 