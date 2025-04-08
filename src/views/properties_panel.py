from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QPushButton, QScrollArea, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QPlainTextEdit, QSpacerItem, QSizePolicy, QFrame, QGridLayout, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPalette
import logging

class PropertiesPanel(QWidget):
    """A panel for displaying and editing properties of selected items."""
    
    # Signals for property changes
    name_changed = pyqtSignal(str)
    z_value_changed = pyqtSignal(float)
    device_property_changed = pyqtSignal(str, object)
    connection_property_changed = pyqtSignal(str, object)
    boundary_property_changed = pyqtSignal(str, object)
    change_icon_requested = pyqtSignal(object)
    property_display_toggled = pyqtSignal(str, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.current_item = None
        self.boundary_devices = []
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI elements."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # Scrollable area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        
        # Title for the panel
        title = QLabel("Properties")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        self.content_layout.addWidget(title)
        
        # Create sections
        self.general_group = self._create_general_section()
        self.device_group = self._create_device_section()
        self.connection_group = self._create_connection_section()
        self.boundary_group = self._create_boundary_section()
        
        # Add sections to layout
        self.content_layout.addWidget(self.general_group)
        self.content_layout.addWidget(self.device_group)
        self.content_layout.addWidget(self.connection_group)
        self.content_layout.addWidget(self.boundary_group)
        self.content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_general_section(self):
        """Create the general properties section."""
        group = QGroupBox("General")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(
            lambda: self.name_changed.emit(self.name_edit.text())
        )
        layout.addRow("Name:", self.name_edit)
        
        # Z-Index (layer) control
        self.z_index_spin = QSpinBox()
        self.z_index_spin.setRange(-100, 100)
        self.z_index_spin.valueChanged.connect(
            lambda value: self.z_value_changed.emit(float(value))
        )
        layout.addRow("Layer (Z-Index):", self.z_index_spin)
        
        return group
    
    def _create_device_section(self):
        """Create the device-specific properties section."""
        group = QGroupBox("Device Properties")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
        # Device type 
        self.device_type_label = QLabel()
        layout.addRow("Type:", self.device_type_label)
        
        # Device model
        self.device_model_label = QLabel()
        layout.addRow("Model:", self.device_model_label)
        
        # RMF ATO Accreditation section
        self.rmf_group = QGroupBox("RMF ATO Accreditation")
        rmf_layout = QFormLayout()
        
        # STIG Compliance
        self.stig_label = QLabel()
        rmf_layout.addRow("STIG Compliance:", self.stig_label)
        
        # Vulnerability Scan
        self.vuln_label = QLabel()
        rmf_layout.addRow("Vulnerability Scan:", self.vuln_label)
        
        # ATO Status
        self.ato_label = QLabel()
        rmf_layout.addRow("ATO Status:", self.ato_label)
        
        # Accreditation Date
        self.accred_date_label = QLabel()
        rmf_layout.addRow("Accreditation Date:", self.accred_date_label)
        
        self.rmf_group.setLayout(rmf_layout)
        layout.addRow(self.rmf_group)
        
        # Add button to change device icon
        self.change_icon_button = QPushButton("Change Icon")
        self.change_icon_button.setStyleSheet("QPushButton { padding: 4px 8px; }")
        self.change_icon_button.clicked.connect(self._on_change_icon_clicked)
        layout.addRow("Icon:", self.change_icon_button)
        
        # Display options group
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout(display_group)
        display_layout.setSpacing(6)
        self.display_checkboxes = {}
        
        # We'll populate these checkboxes dynamically when a device is selected
        display_layout.addWidget(QLabel("Show properties under icon:"))
        
        layout.addRow(display_group)
        
        # Custom properties table
        self.device_props_table = QTableWidget(0, 2)
        self.device_props_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.device_props_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.device_props_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.device_props_table.setMinimumHeight(100)
        layout.addRow(self.device_props_table)
        
        # Connect to slot that handles property changes
        self.device_props_table.cellChanged.connect(self._on_device_property_changed)
        
        return group
    
    def _create_connection_section(self):
        """Create the connection-specific properties section."""
        group = QGroupBox("Connection Properties")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
        # Connection type
        self.connection_type_combo = QComboBox()
        layout.addRow("Type:", self.connection_type_combo)
        
        # Source device
        self.connection_source_label = QLabel()
        layout.addRow("Source:", self.connection_source_label)
        
        # Target device
        self.connection_target_label = QLabel()
        layout.addRow("Target:", self.connection_target_label)
        
        # Line style selection
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["Straight", "Orthogonal", "Curved"])
        self.line_style_combo.currentTextChanged.connect(
            lambda text: self.connection_property_changed.emit("line_style", text)
        )
        layout.addRow("Line Style:", self.line_style_combo)
        
        # Connection properties
        self.connection_props_table = QTableWidget(0, 2)
        self.connection_props_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.connection_props_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.connection_props_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.connection_props_table.setMinimumHeight(100)
        layout.addRow(self.connection_props_table)
        
        # Connect to slot that handles property changes
        self.connection_props_table.cellChanged.connect(self._on_connection_property_changed)
        
        return group
    
    def _create_boundary_section(self):
        """Create the boundary-specific properties section."""
        group = QGroupBox("Boundary Information")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QFormLayout(group)
        layout.setVerticalSpacing(8)
        
        # Add color selection button
        self.color_button = QPushButton("Change Color")
        self.color_button.setStyleSheet("QPushButton { padding: 4px 8px; }")
        self.color_button.clicked.connect(self._on_boundary_color_change)
        layout.addRow("Color:", self.color_button)
        
        # Add font size spinner
        self.boundary_font_size_spin = QSpinBox()
        self.boundary_font_size_spin.setRange(8, 24)
        self.boundary_font_size_spin.setSuffix(" pt")
        self.boundary_font_size_spin.valueChanged.connect(
            lambda value: self.boundary_property_changed.emit("font_size", value)
        )
        layout.addRow("Text Size:", self.boundary_font_size_spin)
        
        # Show contained devices
        self.boundary_devices_table = QTableWidget(0, 1)
        self.boundary_devices_table.setHorizontalHeaderLabels(["Contained Devices"])
        self.boundary_devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.boundary_devices_table.setMinimumHeight(100)
        layout.addRow(self.boundary_devices_table)
        
        return group
    
    def display_item_properties(self, item):
        """Update the panel with the selected item's properties."""
        logger = logging.getLogger(__name__)
        logger.info(f"PANEL DEBUG: Displaying properties for item type: {type(item).__name__}, id: {id(item)}")
        
        # Important: No longer require double click to update panel
        
        # Clear the content layout first
        self._reset_layout(self.content_layout)
        
        # Update current item reference
        self.current_item = item
        logger.info(f"PANEL DEBUG: Set current_item reference to: {type(self.current_item).__name__}")
        
        # Recreate sections if they've been deleted
        if not hasattr(self, 'general_group') or not self._widget_exists(self.general_group):
            logger.info("PANEL DEBUG: Recreating panel sections")
            self.general_group = self._create_general_section()
            self.device_group = self._create_device_section()
            self.connection_group = self._create_connection_section()
            self.boundary_group = self._create_boundary_section()
        
        # Add all groups back but only show relevant ones
        self.content_layout.addWidget(self.general_group)
        self.content_layout.addWidget(self.device_group)
        self.content_layout.addWidget(self.connection_group)
        self.content_layout.addWidget(self.boundary_group)
        
        # Initially hide all specific property groups
        self.device_group.setVisible(False)
        self.connection_group.setVisible(False)
        self.boundary_group.setVisible(False)
        
        # Update general properties that all items share
        if hasattr(item, 'name'):
            logger.info(f"PANEL DEBUG: Setting name field to: {item.name}")
            self.name_edit.setText(item.name)
        else:
            self.name_edit.clear()
        
        # Update Z-value (layer)
        z_value = item.zValue()
        logger.info(f"PANEL DEBUG: Setting z-index to: {z_value}")
        self.z_index_spin.setValue(int(z_value))
        
        # Show specific properties based on item type
        from models.device import Device
        from models.connection import Connection
        from models.boundary import Boundary
        
        if isinstance(item, Device):
            logger.info("PANEL DEBUG: Item is a Device, showing device properties")
            self._display_device_properties(item)
        elif isinstance(item, Connection):
            logger.info("PANEL DEBUG: Item is a Connection, showing connection properties")
            self._display_connection_properties(item)
        elif isinstance(item, Boundary):
            logger.info("PANEL DEBUG: Item is a Boundary, showing boundary properties")
            self._display_boundary_properties(item)
        else:
            logger.info(f"PANEL DEBUG: Unknown item type: {type(item).__name__}")
    
    def _display_device_properties(self, device):
        """Display properties for a device."""
        # Ensure the device section is visible
        self.device_group.setVisible(True)
        self.connection_group.setVisible(False)
        self.boundary_group.setVisible(False)
        
        # Set basic properties
        self.name_edit.setText(device.name)
        self.z_index_spin.setValue(int(device.zValue()))
        self.device_type_label.setText(device.device_type.capitalize())
        
        # Set model if available
        model_text = device.properties.get('model', '')
        self.device_model_label.setText(model_text)
        
        # Set RMF ATO properties if available
        self.stig_label.setText(device.properties.get('stig_compliance', ''))
        self.vuln_label.setText(device.properties.get('vulnerability_scan', ''))
        self.ato_label.setText(device.properties.get('ato_status', ''))
        self.accred_date_label.setText(device.properties.get('accreditation_date', ''))
        
        # Populate device properties table
        self.device_props_table.setRowCount(0)
        self.device_props_table.clearContents()
        self.device_props_table.blockSignals(True)
        
        # Add ALL device properties to the table, including those displayed as separate fields
        # This ensures all properties are editable
        row = 0
        for prop, value in device.properties.items():
            # Skip only the icon property
            if prop not in ['icon', 'color', 'width', 'height']:
                self.device_props_table.insertRow(row)
                
                # Create property name item (not editable)
                propItem = QTableWidgetItem(prop)
                propItem.setFlags(propItem.flags() & ~Qt.ItemIsEditable)
                self.device_props_table.setItem(row, 0, propItem)
                
                # Create value item (editable)
                self.device_props_table.setItem(row, 1, QTableWidgetItem(str(value)))
                row += 1
        
        self.device_props_table.blockSignals(False)
        
        # Update display options checkboxes
        self._update_device_display_options(device)
    
    def _get_display_options_group(self):
        """Helper method to find the Display Options group within the device group."""
        for i in range(self.device_group.layout().count()):
            item = self.device_group.layout().itemAt(i)
            if (item and item.widget() and 
                isinstance(item.widget(), QGroupBox) and 
                item.widget().title() == "Display Options"):
                return item.widget()
        return None
    
    def _reset_layout(self, layout):
        """Remove all widgets from a layout."""
        if layout is None:
            return
        
        # Handle the case when layout is actually a QGroupBox
        if isinstance(layout, QGroupBox):
            # Get the actual layout from the group box
            box_layout = layout.layout()
            if box_layout:
                self._reset_layout(box_layout)
            return
        
        # Handle the case when it's a real layout with a count method
        if hasattr(layout, 'count'):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()
                elif item.layout():
                    self._reset_layout(item.layout())
                elif item.spacerItem():
                    # Just remove spacer items
                    pass
    
    def _display_connection_properties(self, connection):
        """Update the panel with connection-specific properties."""
        self.connection_group.show()
        
        # Disconnect signal to prevent firing while updating
        self.connection_props_table.cellChanged.disconnect(self._on_connection_property_changed)
        
        # Clear previous properties
        self.connection_props_table.setRowCount(0)
        
        # Set routing style in combo box
        if hasattr(connection, 'routing_style'):
            style_index = {
                connection.STYLE_STRAIGHT: 0,
                connection.STYLE_ORTHOGONAL: 1,
                connection.STYLE_CURVED: 2
            }.get(connection.routing_style, 0)
            self.line_style_combo.setCurrentIndex(style_index)
        
        # Display core connection properties
        properties = []
        
        # Check if connection has properties dictionary
        if hasattr(connection, 'properties') and connection.properties:
            # Use the properties dictionary
            for key, value in connection.properties.items():
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
            
            properties.append(("Type", connection.connection_type if hasattr(connection, 'connection_type') else "ethernet"))
            
            # Add source and target info
            if hasattr(connection, 'source_device') and connection.source_device:
                properties.append(("Source", connection.source_device.name))
            if hasattr(connection, 'target_device') and connection.target_device:
                properties.append(("Target", connection.target_device.name))
        
        # Add all properties to table
        for i, (key, value) in enumerate(properties):
            self.connection_props_table.insertRow(i)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make property name read-only
            self.connection_props_table.setItem(i, 0, key_item)
            self.connection_props_table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        # Reconnect signal
        self.connection_props_table.cellChanged.connect(self._on_connection_property_changed)
    
    def _display_boundary_properties(self, boundary):
        """Display properties specific to boundaries."""
        # Show boundary specific properties
        self.boundary_group.setVisible(True)
        
        # Update color button appearance based on boundary color
        if hasattr(boundary, 'color'):
            self._update_color_button(boundary.color)
        
        # Update font size spinner value based on boundary's label font size
        if hasattr(boundary, 'get_font_size'):
            font_size = boundary.get_font_size()
            self.boundary_font_size_spin.setValue(font_size)
        
        # Note: Contained devices are displayed separately via set_boundary_contained_devices
        self.boundary_devices_table.setRowCount(0)
        
        # Find devices that are contained within this boundary
        if self.boundary_devices:
            for row, device in enumerate(self.boundary_devices):
                self.boundary_devices_table.insertRow(row)
                self.boundary_devices_table.setItem(row, 0, QTableWidgetItem(device.name))
    
    def set_boundary_contained_devices(self, devices):
        """Set the list of devices contained within the selected boundary."""
        self.boundary_devices = devices
        
        # If a boundary is currently selected, update its display
        if self.current_item and self.boundary_group.isVisible():
            self._display_boundary_properties(self.current_item)
    
    def _on_device_property_changed(self, row, column):
        """Handle changes in device property table."""
        if column == 1:  # Only care about value column
            key = self.device_props_table.item(row, 0).text()
            value = self.device_props_table.item(row, 1).text()
            self.device_property_changed.emit(key, value)
    
    def _on_connection_property_changed(self, row, column):
        """Handle changes in connection property table."""
        if column == 1:  # Only care about value column
            key = self.connection_props_table.item(row, 0).text()
            value = self.connection_props_table.item(row, 1).text()
            self.connection_property_changed.emit(key, value)
    
    def _on_change_icon_clicked(self):
        """Handle click on change icon button."""
        if self.current_item:
            # Always emit the signal instead of directly calling the method
            # This maintains proper MVC separation
            self.change_icon_requested.emit(self.current_item)
    
    def show_multiple_devices(self, devices):
        """Show a simplified interface for editing common properties across all selected devices."""
        if not devices:
            self.clear()
            return
        
        # First clear the panel
        self.clear()
        
        # Store reference to these devices
        self.current_item = None  # Clear single item reference
        self.current_items = devices
        
        # Create a scrollable container for properties
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        
        # Header with count of selected devices
        header = QLabel(f"<b>{len(devices)} Devices Selected</b>")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Create a form for all properties
        props_group = QGroupBox("Common Properties")
        props_layout = QFormLayout()
        
        # Get the most common device type if possible
        device_types = {}
        for device in devices:
            if hasattr(device, 'device_type'):
                device_type = device.device_type
                if device_type in device_types:
                    device_types[device_type] += 1
                else:
                    device_types[device_type] = 1
        
        # Display the most common device type as read-only info
        if device_types:
            most_common_type = max(device_types.items(), key=lambda x: x[1])[0]
            type_label = QLabel(most_common_type)
            props_layout.addRow("Device Type:", type_label)
        
        # Collect all properties from all devices
        # Exclude properties that should not be shown or cannot be meaningfully bulk-edited
        excluded_props = ["name", "device_type", "width", "height", "color", "icon", "position", "port_positions", "selected"]
        
        # Collect all properties from all devices
        all_properties = set()
        for device in devices:
            if hasattr(device, 'properties'):
                for prop in device.properties:
                    if prop not in excluded_props:
                        all_properties.add(prop)
        
        # Sort properties alphabetically
        sorted_props = sorted(all_properties)
        
        # Create editable fields for each property
        for prop in sorted_props:
            # Format name for display
            display_name = prop.replace('_', ' ').title()
            
            # Create input field
            if prop.lower() in ["description", "notes"]:
                # Multi-line text for descriptions
                field = QPlainTextEdit()
                field.setMaximumHeight(80)
                field.setPlaceholderText(f"Set {display_name} for all selected devices")
            else:
                # Single line for most properties
                field = QLineEdit()
                field.setPlaceholderText(f"Set {display_name} for all selected devices")
            
            # Store property name for signal handler
            field.setProperty("property_name", prop)
            
            # Connect signals based on field type
            if isinstance(field, QPlainTextEdit):
                field.textChanged.connect(self._handle_multi_edit_text_changed)
            else:
                field.editingFinished.connect(self._handle_multi_edit_finished)
            
            # Add to form layout
            props_layout.addRow(f"{display_name}:", field)
        
        props_group.setLayout(props_layout)
        main_layout.addWidget(props_group)
        
        # Add a "Display Options" section
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()
        
        # Create checkboxes for all displayable properties
        checkbox_grid = QGridLayout()
        checkbox_grid.setColumnStretch(0, 1)
        checkbox_grid.setColumnStretch(1, 1)
        
        # Add checkboxes in two columns
        self.display_checkboxes = {}
        
        for i, prop in enumerate(sorted(all_properties)):
            # Format name for display
            display_name = prop.replace('_', ' ').title()
            
            checkbox = QCheckBox(display_name)
            checkbox.setProperty("property_name", prop)
            
            # Get initial state based on majority of devices
            display_count = sum(1 for device in devices if hasattr(device, 'get_property_display_state') and device.get_property_display_state(prop))
            checkbox.setChecked(display_count > len(devices) / 2)
            
            # Connect state change handler
            checkbox.stateChanged.connect(self._handle_display_state_changed)
            
            # Add to grid in two columns
            row = i // 2
            col = i % 2
            checkbox_grid.addWidget(checkbox, row, col)
            
            # Store reference
            self.display_checkboxes[prop] = checkbox
        
        display_layout.addLayout(checkbox_grid)
        display_group.setLayout(display_layout)
        main_layout.addWidget(display_group)
        
        # Add the main container to the content layout
        self.content_layout.addWidget(main_container)
    
    def _handle_multi_edit_finished(self):
        """Handle editing completed for a line edit in multi-device mode."""
        sender = self.sender()
        if sender and isinstance(sender, QLineEdit):
            prop_name = sender.property("property_name")
            value = sender.text()
            if prop_name and value:
                self.device_property_changed.emit(prop_name, value)
    
    def _handle_multi_edit_text_changed(self):
        """Handle text changes in multi-device mode."""
        sender = self.sender()
        if sender and isinstance(sender, QPlainTextEdit):
            prop_name = sender.property("property_name")
            value = sender.toPlainText()
            if prop_name and value:
                self.device_property_changed.emit(prop_name, value)
    
    def _handle_display_state_changed(self, state):
        """Handle display checkbox state changes in multi-device mode."""
        sender = self.sender()
        if sender:
            prop_name = sender.property("property_name")
            if prop_name:
                # Convert from Qt.CheckState to boolean (partial is considered True)
                display_enabled = state != Qt.Unchecked
                self.property_display_toggled.emit(prop_name, display_enabled)
    
    def _handle_checkbox_state_changed(self, state):
        """Handle checkbox state changes for device properties display."""
        sender = self.sender()
        if sender:
            prop_name = sender.property("property_name")
            if prop_name:
                display_enabled = state == Qt.Checked
                self.property_display_toggled.emit(prop_name, display_enabled)
    
    def _widget_exists(self, widget):
        """Check if a widget still exists and is valid."""
        try:
            # This will raise an error if the widget is deleted
            return widget is not None and widget.isVisible() is not None
        except (RuntimeError, AttributeError):
            return False
            
    def clear(self):
        """Clear all content from the properties panel."""
        # Reset current item reference
        self.current_item = None
        self.boundary_devices = []
        
        # Clear the content layout first
        self._reset_layout(self.content_layout)
        
        # Recreate the sections if they've been deleted
        if not hasattr(self, 'general_group') or not self._widget_exists(self.general_group):
            self.general_group = self._create_general_section()
            self.device_group = self._create_device_section()
            self.connection_group = self._create_connection_section()
            self.boundary_group = self._create_boundary_section()
        else:
            # Otherwise just hide the sections
            self.general_group.hide()
            self.device_group.hide()
            self.connection_group.hide()
            self.boundary_group.hide()
        
        # Show a "No selection" message with improved styling
        no_selection_label = QLabel("No item selected")
        no_selection_label.setAlignment(Qt.AlignCenter)
        no_selection_label.setStyleSheet("color: #95a5a6; font-style: italic; padding: 20px;")
        self.content_layout.addWidget(no_selection_label)
    
    def _emit_property_change(self, prop_name, value):
        """Emit property change signal for multiple device editing."""
        self.device_property_changed.emit(prop_name, value)

    def _emit_display_toggle(self, prop_name, state):
        """Emit property display toggle signal for multiple device editing."""
        # Convert from Qt.CheckState to boolean
        # Treat PartiallyChecked as checked (true)
        display_enabled = state != Qt.Unchecked
        self.property_display_toggled.emit(prop_name, display_enabled)

    def _update_device_display_options(self, device):
        """Update the display options for a device."""
        # Clear existing checkboxes
        for i in reversed(range(self._get_display_options_group().layout().count())):
            widget = self._get_display_options_group().layout().itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.display_checkboxes.get('title', None):
                self._get_display_options_group().layout().removeWidget(widget)
                widget.deleteLater()
        
        # Clear display_checkboxes dict except for title checkbox
        title_checkbox = self.display_checkboxes.get('title', None)
        self.display_checkboxes = {}
        if title_checkbox:
            self.display_checkboxes['title'] = title_checkbox
        
        # Common properties to show (in order)
        common_properties = [
            ("ip_address", "IP Address"),
            ("model", "Model"),
            ("hostname", "Hostname"),
            ("description", "Description"),
            ("location", "Location"),
            ("stig_compliance", "STIG Compliance"),
            ("vulnerability_scan", "Vulnerability Scan"),
            ("ato_status", "ATO Status"),
            ("accreditation_date", "Accreditation Date")
        ]
        
        # Add checkboxes for common properties first, then device-specific ones
        used_props = set()
        for prop_key, display_name in common_properties:
            if prop_key in device.properties:
                self._add_display_checkbox(device, prop_key, display_name)
                used_props.add(prop_key)
        
        # Now add any other properties from the device that weren't in common_properties
        for prop in device.properties.keys():
            if prop not in used_props and prop not in ['icon', 'color', 'width', 'height']:
                display_name = prop.replace('_', ' ').title()
                self._add_display_checkbox(device, prop, display_name)
    
    def _add_display_checkbox(self, device, prop_key, display_name):
        """Add a checkbox for controlling the display of a device property."""
        # Create the checkbox with a friendly display name
        checkbox = QCheckBox(display_name)
        
        # Set the initial state from the device
        is_displayed = device.get_property_display_state(prop_key)
        checkbox.setChecked(is_displayed)
        
        # Store the property key as a property on the checkbox
        checkbox.setProperty("property_name", prop_key)
        
        # Connect the state changed signal
        checkbox.stateChanged.connect(self._handle_checkbox_state_changed)
        
        # Add to layout and store reference
        self._get_display_options_group().layout().addWidget(checkbox)
        self.display_checkboxes[prop_key] = checkbox
    
    def _on_boundary_color_change(self):
        """Handle boundary color change request."""
        if not self.current_item:
            return
            
        current_color = None
        if hasattr(self.current_item, 'color'):
            current_color = self.current_item.color
        
        # Open color dialog with current color preselected
        color_dialog = QColorDialog(self)
        if current_color:
            color_dialog.setCurrentColor(current_color)
        
        if color_dialog.exec_():
            selected_color = color_dialog.selectedColor()
            # Update the button appearance
            self._update_color_button(selected_color)
            # Pass the color to the controller
            self.boundary_property_changed.emit("color", selected_color)
    
    def _update_color_button(self, color):
        """Update the color button to show the current boundary color."""
        if not hasattr(self, 'color_button'):
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
