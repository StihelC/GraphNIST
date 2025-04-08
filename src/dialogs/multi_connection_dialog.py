from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox,
                            QDialogButtonBox, QLabel, QLineEdit, QCheckBox,
                            QRadioButton, QButtonGroup, QGroupBox, QHBoxLayout)
from PyQt5.QtCore import Qt
from constants import ConnectionTypes, DeviceTypes

class MultiConnectionDialog(QDialog):
    """Dialog for configuring properties when connecting multiple devices."""
    
    # Define connection strategies
    STRATEGY_MESH = "mesh"
    STRATEGY_CHAIN = "chain"
    STRATEGY_CLOSEST = "closest"
    STRATEGY_CLOSEST_TYPE = "closest_type"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect Multiple Devices")
        self.setMinimumWidth(400)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header label
        header_label = QLabel("Configure connections between selected devices")
        header_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(header_label)
        
        # Connection strategy selection
        strategy_group = QGroupBox("Connection Strategy")
        strategy_layout = QVBoxLayout()
        
        # Create button group for radio buttons
        self.strategy_button_group = QButtonGroup(self)
        
        # Mesh option (all-to-all)
        self.mesh_radio = QRadioButton("Create mesh network (connect all-to-all)")
        self.mesh_radio.setToolTip("Connect every device to every other device")
        self.strategy_button_group.addButton(self.mesh_radio, 1)
        strategy_layout.addWidget(self.mesh_radio)
        
        # Chain option
        self.chain_radio = QRadioButton("Chain connection (device 1 → 2 → 3 → etc.)")
        self.chain_radio.setToolTip("Connect devices in a sequential chain")
        self.strategy_button_group.addButton(self.chain_radio, 2)
        strategy_layout.addWidget(self.chain_radio)
        
        # Closest neighbor option
        self.closest_radio = QRadioButton("Connect each to closest device")
        self.closest_radio.setToolTip("Connect each device to its spatially closest neighbor")
        self.strategy_button_group.addButton(self.closest_radio, 3)
        strategy_layout.addWidget(self.closest_radio)
        
        # Closest of specific type option
        closest_type_layout = QHBoxLayout()
        self.closest_type_radio = QRadioButton("Connect each to closest device of type:")
        self.closest_type_radio.setToolTip("Connect each device to its closest neighbor of a specific type")
        self.strategy_button_group.addButton(self.closest_type_radio, 4)
        closest_type_layout.addWidget(self.closest_type_radio)
        
        # Device type selection dropdown
        self.device_type_combo = QComboBox()
        for dev_type in DeviceTypes.get_all_types():
            # Format the type for display (capitalize, replace underscores)
            display_name = dev_type.replace('_', ' ').title()
            self.device_type_combo.addItem(display_name, dev_type)
        closest_type_layout.addWidget(self.device_type_combo)
        
        strategy_layout.addLayout(closest_type_layout)
        
        # Set mesh as default
        self.mesh_radio.setChecked(True)
        
        # Enable/disable the device type combo box based on radio selection
        self.closest_type_radio.toggled.connect(
            lambda checked: self.device_type_combo.setEnabled(checked))
        self.device_type_combo.setEnabled(False)
        
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)
        
        # Form for connection properties
        conn_group = QGroupBox("Connection Properties")
        form = QFormLayout()
        
        # Connection type selection
        self.connection_type_combo = QComboBox()
        for conn_type in ConnectionTypes.get_all_types():
            display_name = ConnectionTypes.DISPLAY_NAMES.get(conn_type, conn_type)
            self.connection_type_combo.addItem(display_name, conn_type)
        form.addRow("Connection Type:", self.connection_type_combo)
        
        # Connection label field
        self.connection_label = QLineEdit()
        self.connection_label.setText(
            ConnectionTypes.DISPLAY_NAMES.get(ConnectionTypes.ETHERNET, "Link"))
        self.connection_type_combo.currentIndexChanged.connect(self._update_connection_label)
        form.addRow("Label:", self.connection_label)
        
        # Bandwidth field
        self.bandwidth_edit = QLineEdit()
        self.bandwidth_edit.setText(
            ConnectionTypes.DEFAULT_BANDWIDTHS.get(ConnectionTypes.ETHERNET, "1G"))
        self.connection_type_combo.currentIndexChanged.connect(self._update_bandwidth)
        form.addRow("Bandwidth:", self.bandwidth_edit)
        
        # Latency field
        self.latency_edit = QLineEdit()
        self.latency_edit.setText("0ms")
        form.addRow("Latency:", self.latency_edit)
        
        conn_group.setLayout(form)
        layout.addWidget(conn_group)
        
        # Bidirectional option
        self.bidirectional_checkbox = QCheckBox("Create bidirectional connections")
        self.bidirectional_checkbox.setChecked(True)
        self.bidirectional_checkbox.setToolTip("If checked, connections will be created in both directions")
        layout.addWidget(self.bidirectional_checkbox)
        
        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
    
    def _update_connection_label(self):
        """Update the label field based on the selected connection type."""
        conn_type = self.connection_type_combo.currentData()
        self.connection_label.setText(
            ConnectionTypes.DISPLAY_NAMES.get(conn_type, "Link"))
    
    def _update_bandwidth(self):
        """Update the bandwidth field based on the selected connection type."""
        conn_type = self.connection_type_combo.currentData()
        self.bandwidth_edit.setText(
            ConnectionTypes.DEFAULT_BANDWIDTHS.get(conn_type, "1G"))
    
    def get_connection_strategy(self):
        """Get the selected connection strategy."""
        strategy_id = self.strategy_button_group.checkedId()
        if strategy_id == 1:
            return self.STRATEGY_MESH
        elif strategy_id == 2:
            return self.STRATEGY_CHAIN
        elif strategy_id == 3:
            return self.STRATEGY_CLOSEST
        elif strategy_id == 4:
            return self.STRATEGY_CLOSEST_TYPE
        return self.STRATEGY_MESH  # Default to mesh
    
    def get_connection_data(self):
        """Get the connection configuration data."""
        return {
            'type': self.connection_type_combo.currentData(),
            'label': self.connection_label.text(),
            'bandwidth': self.bandwidth_edit.text(),
            'latency': self.latency_edit.text(),
            'strategy': self.get_connection_strategy(),
            'target_device_type': self.device_type_combo.currentData() if self.closest_type_radio.isChecked() else None,
            'bidirectional': self.bidirectional_checkbox.isChecked()
        }
