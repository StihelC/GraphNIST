from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                           QComboBox, QPushButton, QHBoxLayout, QLabel, QFileDialog,
                           QSpinBox, QCheckBox, QGroupBox, QTabWidget, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from constants import DeviceTypes, ConnectionTypes
import os
import logging

class DeviceDialog(QDialog):
    """Dialog for creating or editing a device."""
    
    def __init__(self, parent=None, device=None):
        """Initialize the dialog for creating or editing a device."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.critical(f"DIALOG DEBUG: DeviceDialog constructor called with device: {device}")
        
        # Store existing device if we're editing one
        self.device = device
        
        # Path for custom icon
        self.custom_icon_path = ""
        if device and hasattr(device, 'custom_icon_path'):
            self.custom_icon_path = device.custom_icon_path
            self.logger.critical(f"DIALOG DEBUG: Using custom icon path from device: {self.custom_icon_path}")
        
        self.setWindowTitle("Add Device" if not device else "Edit Device")
        self.resize(600, 650)  # Make the dialog wider and taller
        
        # Create layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create the UI
        self._create_ui()
        
        # If editing, populate fields
        if device:
            self._populate_from_device()

    # Common device models for each device type
    DEVICE_MODELS = {
        DeviceTypes.ROUTER: [
            "Cisco ISR 4451", "Cisco ASR 1001-X", "Cisco ASR 9000", "Cisco Catalyst 8300",
            "Juniper MX204", "Juniper SRX380", "Juniper ACX7100", 
            "Arista 7280R3", "Arista 7500R3", 
            "Palo Alto PA-7000", "Fortinet FortiGate 600F",
            "MikroTik CCR2004", "Ubiquiti EdgeRouter 4",
            "HPE FlexNetwork MSR3000", "Huawei AR6000"
        ],
        DeviceTypes.SWITCH: [
            "Cisco Catalyst 9300", "Cisco Nexus 9300", "Cisco 3850", 
            "Juniper EX4650", "Juniper QFX5120",
            "Arista 7050X3", "Arista 7060X4", 
            "HPE Aruba 6300F", "HPE FlexFabric 5945", 
            "Dell PowerSwitch S5248F", "Dell EMC S4148F",
            "Ubiquiti UniFi USW-Pro-48-POE", "MikroTik CRS326",
            "Extreme Networks X870", "Brocade ICX7650"
        ],
        DeviceTypes.FIREWALL: [
            "Palo Alto PA-5450", "Palo Alto PA-3260", 
            "Cisco Firepower 2130", "Cisco ASA 5555-X", 
            "Fortinet FortiGate 600F", "Fortinet FortiGate 3400E",
            "Check Point 16000", "Check Point 6800",
            "Juniper SRX380", "Juniper SRX4600",
            "Sophos XGS 5500", "Sophos XGS 6500",
            "WatchGuard Firebox M590", "Barracuda CloudGen F900",
            "SonicWall NSA 6700"
        ],
        DeviceTypes.SERVER: [
            "Dell PowerEdge R750", "Dell PowerEdge R650",
            "HPE ProLiant DL380 Gen10", "HPE ProLiant DL360 Gen10", 
            "Lenovo ThinkSystem SR650", "Lenovo ThinkSystem SR630",
            "Cisco UCS C240 M6", "Cisco UCS C220 M6",
            "IBM Power System S1022", "IBM Power System S1014",
            "Oracle X9-2", "Oracle X8-2",
            "SuperMicro SuperServer 1029U-TN10RT", "SuperMicro SuperServer 2029U-E1CR4",
            "Huawei FusionServer Pro 2288H V5", "Asus RS700-E10"
        ],
        DeviceTypes.CLOUD: [
            "AWS EC2", "AWS S3", "AWS VPC", "AWS Lambda", "AWS RDS",
            "Azure Virtual Machines", "Azure Blob Storage", "Azure SQL", "Azure Functions",
            "Google Compute Engine", "Google Cloud Storage", "Google Cloud SQL",
            "IBM Cloud Virtual Servers", "IBM Cloud Object Storage",
            "Oracle Cloud Infrastructure", "Alibaba ECS",
            "Digital Ocean Droplets", "Salesforce Cloud"
        ],
        DeviceTypes.WORKSTATION: [
            "Dell OptiPlex 7090", "Dell Precision 5820", 
            "HP EliteDesk 800 G6", "HP Z4 Workstation",
            "Lenovo ThinkCentre M90t", "Lenovo ThinkStation P620",
            "Apple Mac Pro", "Apple Mac Mini M1",
            "Microsoft Surface Studio 2", 
            "ASUS ProArt Station PD5", "ASUS ExpertCenter D7",
            "Acer Veriton X", "Acer ConceptD 500",
            "Intel NUC 11 Extreme", "Alienware Aurora R13"
        ],
        DeviceTypes.GENERIC: [
            "IoT Gateway", "Virtual Appliance", "Embedded Device", 
            "PLC Controller", "Edge Computing Device", "Media Converter",
            "Load Balancer", "VPN Concentrator", "Thin Client",
            "Print Server", "KVM Switch", "Wireless Access Point", 
            "Storage Array", "Tape Library", "UPS System"
        ]
    }
    
    def _create_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout()
        
        # Create a tab widget to organize the content
        tab_widget = QTabWidget()
        
        # ===== Basic Info Tab =====
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        # Connect name changes to update the model field
        self.name_edit.textChanged.connect(self._update_model_from_name)
        form_layout.addRow("Name:", self.name_edit)
        
        # Device type dropdown
        self.type_combo = QComboBox()
        
        # Add device types from constants
        self.type_combo.addItem("Router", DeviceTypes.ROUTER)
        self.type_combo.addItem("Switch", DeviceTypes.SWITCH)
        self.type_combo.addItem("Firewall", DeviceTypes.FIREWALL)
        self.type_combo.addItem("Server", DeviceTypes.SERVER)
        self.type_combo.addItem("Workstation", DeviceTypes.WORKSTATION)
        self.type_combo.addItem("Cloud", DeviceTypes.CLOUD)
        self.type_combo.addItem("Generic", DeviceTypes.GENERIC)
        
        form_layout.addRow("Type:", self.type_combo)
        
        # Device model section - Now clearly shows it's related to the selected device type
        self.model_group = QGroupBox("Device Model")
        model_layout = QVBoxLayout()
        
        # Device type label that shows the currently selected type
        self.selected_type_label = QLabel()
        self.selected_type_label.setStyleSheet("font-weight: bold;")
        model_layout.addWidget(self.selected_type_label)
        
        # Label for model selection
        self.model_label = QLabel("Select a common model for this device type:")
        model_layout.addWidget(self.model_label)
        
        # Model dropdown
        self.model_combo = QComboBox()
        self.model_combo.setPlaceholderText("Select Model...")
        model_layout.addWidget(self.model_combo)
        
        # Add a note about model name usage in bulk creation
        model_note = QLabel("Note: When creating multiple devices, the model name can be used for device naming.")
        model_note.setStyleSheet("font-style: italic; color: #666;")
        model_note.setWordWrap(True)
        model_layout.addWidget(model_note)
        
        # Connect device type dropdown to update models and type label
        self.type_combo.currentIndexChanged.connect(self._update_selected_type_label)
        self.type_combo.currentIndexChanged.connect(self._update_model_dropdown)
        self.type_combo.currentIndexChanged.connect(self._update_rmf_defaults)
        
        # Custom model input
        self.custom_model_layout = QHBoxLayout()
        self.custom_model_label = QLabel("Custom Model:")
        self.custom_model_edit = QLineEdit()
        self.custom_model_layout.addWidget(self.custom_model_label)
        self.custom_model_layout.addWidget(self.custom_model_edit)
        model_layout.addLayout(self.custom_model_layout)
        
        self.model_group.setLayout(model_layout)
        
        # Add basic device info to the tab
        basic_layout.addLayout(form_layout)
        basic_layout.addWidget(self.model_group)
        
        # Additional device properties
        properties_group = QGroupBox("Device Properties")
        properties_layout = QFormLayout()
        
        # IP address field
        self.ip_edit = QLineEdit()
        properties_layout.addRow("IP Address:", self.ip_edit)
        
        # Description field
        self.desc_edit = QLineEdit()
        properties_layout.addRow("Description:", self.desc_edit)
        
        properties_group.setLayout(properties_layout)
        basic_layout.addWidget(properties_group)
        
        # Custom icon selection
        icon_group = QGroupBox("Device Icon")
        icon_layout = QHBoxLayout()
        
        self.icon_label = QLabel("Default icon for selected device type")
        icon_layout.addWidget(self.icon_label)
        
        self.icon_button = QPushButton("Choose Custom Icon...")
        self.icon_button.clicked.connect(self.upload_custom_icon)
        icon_layout.addWidget(self.icon_button)
        
        icon_group.setLayout(icon_layout)
        basic_layout.addWidget(icon_group)
        
        # Add the basic tab to the tab widget
        tab_widget.addTab(basic_tab, "Basic Info")
        
        # ===== RMF Tab =====
        rmf_tab = QWidget()
        rmf_layout = QVBoxLayout(rmf_tab)
        
        rmf_group = QGroupBox("RMF Information")
        rmf_form = QFormLayout()
        
        # Make RMF information editable with default values from device type
        rmf_info_layout = QFormLayout()
        
        # Impact Level - now a combobox
        self.rmf_impact_combo = QComboBox()
        self.rmf_impact_combo.addItems(["Low", "Moderate", "High", "Critical", "Varies"])
        rmf_form.addRow("Impact Level:", self.rmf_impact_combo)
        
        # Security Categorization - now a combobox
        self.rmf_categorization_combo = QComboBox()
        self.rmf_categorization_combo.addItems(["Low", "Moderate", "High", "Varies"])
        rmf_form.addRow("Security Categorization:", self.rmf_categorization_combo)
        
        # STIG Compliance - now a combobox
        self.rmf_stig_combo = QComboBox()
        self.rmf_stig_combo.setEditable(True)
        self.rmf_stig_combo.addItems([
            "DISA Router STIG", 
            "DISA Switch STIG", 
            "DISA Firewall STIG", 
            "DISA OS STIG (based on OS type)",
            "FedRAMP Compliance",
            "Depends on device type"
        ])
        rmf_form.addRow("STIG Compliance:", self.rmf_stig_combo)
        
        # Authorization Requirements - now a combobox
        self.rmf_authorization_combo = QComboBox()
        self.rmf_authorization_combo.setEditable(True)
        self.rmf_authorization_combo.addItems([
            "Boundary device, requires ATO",
            "Infrastructure device, requires ATO",
            "Security device, requires ATO",
            "Server system, requires ATO",
            "Cloud service, requires FedRAMP",
            "End-user system, covered by site ATO",
            "Varies by specific device"
        ])
        rmf_form.addRow("Authorization Requirements:", self.rmf_authorization_combo)
        
        # Description field - now a text edit for better editing
        self.rmf_description_edit = QLineEdit()
        self.rmf_description_edit.setMinimumWidth(300)
        rmf_form.addRow("Description:", self.rmf_description_edit)
        
        rmf_group.setLayout(rmf_form)
        rmf_layout.addWidget(rmf_group)
        
        # STIG compliance dropdown
        self.stig_combo = QComboBox()
        self.stig_combo.addItems(["N/A", "Compliant", "Non-Compliant", "Exception", "In Progress"])
        rmf_form.addRow("Current STIG Status:", self.stig_combo)
        
        # Vulnerability scan dropdown
        self.vuln_combo = QComboBox()
        self.vuln_combo.addItems(["N/A", "Clean", "Critical Findings", "Moderate Findings", "Low Findings", "Pending"])
        rmf_form.addRow("Vulnerability Scan:", self.vuln_combo)
        
        # ATO Status dropdown
        self.ato_combo = QComboBox()
        self.ato_combo.addItems(["N/A", "Full ATO", "Interim ATO", "Pending", "Expired", "No ATO"])
        rmf_form.addRow("ATO Status:", self.ato_combo)
        
        # Accreditation date
        self.accred_date = QLineEdit()
        rmf_form.addRow("Accreditation Date:", self.accred_date)
        
        tab_widget.addTab(rmf_tab, "RMF Info")
        
        # ===== Layout Tab =====
        layout_tab = QWidget()
        layout_layout = QVBoxLayout(layout_tab)
        
        # Grid placement options
        self.grid_group = QGroupBox("Grid Placement")
        grid_layout = QFormLayout()
        
        # Grid layout preview
        self.grid_preview = QLabel("Devices can be aligned to a grid for neat placement")
        grid_layout.addRow(self.grid_preview)
        
        # Enable grid placement
        self.grid_snap_check = QCheckBox("Snap to Grid")
        self.grid_snap_check.setChecked(False)
        grid_layout.addRow("", self.grid_snap_check)
        
        # Grid size
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(10, 200)
        self.grid_size_spin.setValue(50)
        self.grid_size_spin.setSuffix(" px")
        self.grid_size_spin.setEnabled(False)
        grid_layout.addRow("Grid Size:", self.grid_size_spin)
        
        # Connect grid check to enable/disable grid size
        self.grid_snap_check.toggled.connect(self.grid_size_spin.setEnabled)
        self.grid_snap_check.toggled.connect(self._update_grid_preview)
        self.grid_size_spin.valueChanged.connect(self._update_grid_preview)
        
        self.grid_group.setLayout(grid_layout)
        layout_layout.addWidget(self.grid_group)
        
        # Multiple device creation - for new devices only
        self.multiple_check = QCheckBox("Create Multiple Devices")
        self.multiple_check.setChecked(False)
        self.multiple_check.toggled.connect(self._toggle_multiple_options)
        layout_layout.addWidget(self.multiple_check)
        
        # Settings for multiple devices
        self.multiple_group = QGroupBox("Multiple Device Settings")
        self.multiple_group.setVisible(False)
        multiple_layout = QVBoxLayout()
        
        # Number of devices to create
        multiplier_layout = QFormLayout()
        self.multiplier_spin = QSpinBox()
        self.multiplier_spin.setRange(1, 100)
        self.multiplier_spin.setValue(2)
        self.multiplier_spin.valueChanged.connect(self._update_connection_group_state)
        multiplier_layout.addRow("Number of Devices:", self.multiplier_spin)
        multiple_layout.addLayout(multiplier_layout)
        
        # Automatically connect the devices
        self.connect_devices_check = QCheckBox("Connect Devices")
        self.connect_devices_check.setChecked(False)
        self.connect_devices_check.toggled.connect(self._toggle_connection_options)
        multiple_layout.addWidget(self.connect_devices_check)
        
        # Connection settings
        connection_group = QGroupBox("Connection Settings")
        connection_group.setEnabled(False)
        self.connection_group = connection_group
        connection_layout = QFormLayout()
        
        # Connection type
        self.connection_type_combo = QComboBox()
        for conn_type in ConnectionTypes.get_all_types():
            display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, conn_type)
            self.connection_type_combo.addItem(display_name, conn_type)
        connection_layout.addRow("Connection Type:", self.connection_type_combo)
        
        # Connection label
        self.connection_label_edit = QLineEdit("Ethernet")
        self.connection_type_combo.currentIndexChanged.connect(self._update_connection_label)
        connection_layout.addRow("Label:", self.connection_label_edit)
        
        connection_group.setLayout(connection_layout)
        multiple_layout.addWidget(connection_group)
        
        self.multiple_group.setLayout(multiple_layout)
        layout_layout.addWidget(self.multiple_group)
        
        tab_widget.addTab(layout_tab, "Layout")
        
        # Add the tab widget to the main layout
        main_layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Initial updates
        self._update_grid_preview()
        self._update_model_dropdown()
        self._update_selected_type_label()
        self._update_rmf_defaults()

    def _update_selected_type_label(self):
        """Update the label that shows the currently selected device type."""
        device_type = self.type_combo.currentData()
        type_name = self.type_combo.currentText()
        self.selected_type_label.setText(f"Device Type: {type_name}")
        
    def _update_rmf_defaults(self):
        """Update the RMF information fields with defaults based on the selected device type."""
        device_type = self.type_combo.currentData()
        rmf_info = DeviceTypes.get_rmf_info(device_type)
        
        # Set defaults in the editable fields
        index = self.rmf_impact_combo.findText(rmf_info["impact_level"])
        if index >= 0:
            self.rmf_impact_combo.setCurrentIndex(index)
            
        index = self.rmf_categorization_combo.findText(rmf_info["security_categorization"])
        if index >= 0:
            self.rmf_categorization_combo.setCurrentIndex(index)
            
        # For fields that are QComboBox with editable text
        self.rmf_stig_combo.setCurrentText(rmf_info["typical_stig_compliance"])
        self.rmf_authorization_combo.setCurrentText(rmf_info["authorization_requirements"])
        self.rmf_description_edit.setText(rmf_info["description"])
    
    def _update_model_dropdown(self):
        """Update the model dropdown based on the selected device type."""
        self.model_combo.clear()
        
        # Get the current device type
        device_type = self.type_combo.currentData()
        
        # Add a blank item first
        self.model_combo.addItem("Select model...", "")
        
        # Add models for this device type
        if device_type in self.DEVICE_MODELS:
            for model in self.DEVICE_MODELS[device_type]:
                self.model_combo.addItem(model, model)
        
        # Connect the model selection to the custom model field
        self.model_combo.currentIndexChanged.connect(self._update_custom_model_field)
    
    def _update_custom_model_field(self):
        """Update the custom model field based on the selected model."""
        if self.model_combo.currentIndex() > 0:  # If a predefined model is selected
            self.custom_model_edit.setText(self.model_combo.currentText())
        
    def _toggle_multiple_options(self, checked):
        """Show or hide multiple device options based on checkbox state."""
        self.multiple_group.setVisible(checked)
        
        # Adjust dialog size when toggling
        if checked:
            self.adjustSize()
        
        # Only enable multiplier for new devices, not when editing
        if self.device is not None:
            self.multiple_check.setEnabled(False)
            self.multiple_group.setEnabled(False)

    def _toggle_connection_options(self, enabled):
        """Enable or disable the connection type options."""
        for i in range(self.connection_group.layout().count()):
            item = self.connection_group.layout().itemAt(i)
            if isinstance(item, QFormLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if widget and widget != self.connect_devices_check:
                        widget.setEnabled(enabled)
    
    def _update_connection_group_state(self, value):
        """Enable connection options only when creating multiple devices."""
        self.connection_group.setEnabled(value > 1 and self.device is None)
    
    def _update_connection_label(self):
        """Update the label field with the display name of the selected connection type."""
        conn_type = self.connection_type_combo.currentData()
        display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, "Link")
        self.connection_label_edit.setText(display_name)
    
    def _populate_from_device(self):
        """Populate dialog fields from an existing device."""
        if not self.device:
            return
            
        # Set name
        self.name_edit.setText(self.device.name)
        
        # Set device type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.device.device_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Set model if available
        if self.device.properties and 'model' in self.device.properties:
            self.custom_model_edit.setText(self.device.properties['model'])
            
            # Try to find the model in the dropdown
            for i in range(self.model_combo.count()):
                if self.model_combo.itemText(i) == self.device.properties['model']:
                    self.model_combo.setCurrentIndex(i)
                    break
        
        # Set RMF properties if available in device properties
        if self.device.properties:
            # Custom RMF fields if they exist
            if 'rmf_impact_level' in self.device.properties:
                index = self.rmf_impact_combo.findText(self.device.properties['rmf_impact_level'])
                if index >= 0:
                    self.rmf_impact_combo.setCurrentIndex(index)
            
            if 'rmf_categorization' in self.device.properties:
                index = self.rmf_categorization_combo.findText(self.device.properties['rmf_categorization'])
                if index >= 0:
                    self.rmf_categorization_combo.setCurrentIndex(index)
            
            if 'rmf_stig_compliance' in self.device.properties:
                self.rmf_stig_combo.setCurrentText(self.device.properties['rmf_stig_compliance'])
                
            if 'rmf_authorization' in self.device.properties:
                self.rmf_authorization_combo.setCurrentText(self.device.properties['rmf_authorization'])
                
            if 'rmf_description' in self.device.properties:
                self.rmf_description_edit.setText(self.device.properties['rmf_description'])
            
            # STIG Compliance
            if 'stig_compliance' in self.device.properties:
                index = self.stig_combo.findText(self.device.properties['stig_compliance'])
                if index >= 0:
                    self.stig_combo.setCurrentIndex(index)
            
            # Vulnerability Scan
            if 'vulnerability_scan' in self.device.properties:
                index = self.vuln_combo.findText(self.device.properties['vulnerability_scan'])
                if index >= 0:
                    self.vuln_combo.setCurrentIndex(index)
            
            # ATO Status
            if 'ato_status' in self.device.properties:
                index = self.ato_combo.findText(self.device.properties['ato_status'])
                if index >= 0:
                    self.ato_combo.setCurrentIndex(index)
            
            # Accreditation Date
            if 'accreditation_date' in self.device.properties:
                self.accred_date.setText(self.device.properties['accreditation_date'])
        
        # Set properties
        if self.device.properties:
            if 'ip_address' in self.device.properties:
                self.ip_edit.setText(self.device.properties['ip_address'])
            if 'description' in self.device.properties:
                self.desc_edit.setText(self.device.properties['description'])
        
        # Update custom icon label if there's a custom icon
        if hasattr(self.device, 'custom_icon_path') and self.device.custom_icon_path:
            self.custom_icon_path = self.device.custom_icon_path
            self.icon_label.setText(os.path.basename(self.custom_icon_path))

    def upload_custom_icon(self):
        """Open a file dialog to upload a custom icon."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Custom Icon", "", "Images (*.png *.xpm *.jpg)", options=options)
        if file_path:
            self.custom_icon_path = file_path
            self.icon_label.setText(os.path.basename(file_path))
            
            # If we're editing an existing device, update it directly
            if self.device:
                self.device.custom_icon_path = file_path
                self.device._try_load_icon()
                self.device.update()  # Force redraw
    
    def get_name(self):
        """Get the device name from the dialog."""
        return self.name_edit.text().strip()
    
    def get_type(self):
        """Get the selected device type."""
        return self.type_combo.currentData()
    
    def get_properties(self):
        """Get the device properties entered in the dialog."""
        properties = {
            'ip_address': self.ip_edit.text(),
            'description': self.desc_edit.text(),
            'model': self.custom_model_edit.text(),
            'stig_compliance': "" if self.stig_combo.currentText() == "N/A" else self.stig_combo.currentText(),
            'vulnerability_scan': "" if self.vuln_combo.currentText() == "N/A" else self.vuln_combo.currentText(),
            'ato_status': "" if self.ato_combo.currentText() == "N/A" else self.ato_combo.currentText(),
            'accreditation_date': self.accred_date.text(),
            
            # Add custom RMF fields
            'rmf_impact_level': self.rmf_impact_combo.currentText(),
            'rmf_categorization': self.rmf_categorization_combo.currentText(),
            'rmf_stig_compliance': self.rmf_stig_combo.currentText(),
            'rmf_authorization': self.rmf_authorization_combo.currentText(),
            'rmf_description': self.rmf_description_edit.text()
        }
        return properties
    
    def get_device_data(self):
        """Get all device data as a dictionary."""
        data = {
            'name': self.get_name(),
            'type': self.get_type(),
            'properties': self.get_properties()
        }
        
        # Add custom icon path if one was selected
        if self.custom_icon_path:
            data['custom_icon_path'] = self.custom_icon_path
            
        return data
        
    def get_multiplier(self):
        """Get the number of devices to create."""
        if self.multiple_check.isChecked():
            return self.multiplier_spin.value()
        return 1
    
    def should_connect_devices(self):
        """Check if devices should be connected to each other."""
        return (self.multiple_check.isChecked() and 
                self.connect_devices_check.isChecked() and
                self.multiplier_spin.value() > 1)
    
    def get_connection_data(self):
        """Get the connection configuration data."""
        conn_type = self.connection_type_combo.currentData()
        display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, "Link")
        
        print(f"DEBUG - DeviceDialog - Connection type: {conn_type}")
        print(f"DEBUG - DeviceDialog - Display name: {display_name}")
        
        return {
            'type': conn_type,
            'label': display_name,  # Always use the display name
            'bandwidth': ConnectionTypes.DEFAULT_BANDWIDTHS.get(conn_type, ""),
            'latency': ""
        }
    
    def _update_grid_preview(self):
        """Update the grid layout preview based on current settings."""
        devices = self.multiplier_spin.value()
        max_columns = self.grid_size_spin.value()
        
        # Calculate grid dimensions
        columns = min(devices, max_columns)
        rows = (devices + columns - 1) // columns  # Ceiling division
        
        self.grid_preview.setText(f"Grid layout: {rows} row{'s' if rows > 1 else ''} × {columns} column{'s' if columns > 1 else ''}")
    
    def get_spacing_data(self):
        """Get the grid spacing configuration."""
        return {
            'horizontal_spacing': self.grid_size_spin.value(),
            'vertical_spacing': self.grid_size_spin.value(),
            'max_columns': self.grid_size_spin.value()
        }

    def _update_model_from_name(self):
        """This method is now only kept for backward compatibility.
        We no longer automatically update model from name."""
        # Removed auto-update of model from name
        pass

    def _on_save(self):
        """Handle save button click with name validation."""
        # Check if name is blank but we have a model
        if not self.name_edit.text().strip() and self.custom_model_edit.text().strip():
            # Use the model name as the device name with a "1" suffix
            model_name = self.custom_model_edit.text().strip()
            self.name_edit.setText(f"{model_name} 1")
            
        # Now accept the dialog
        self.accept()