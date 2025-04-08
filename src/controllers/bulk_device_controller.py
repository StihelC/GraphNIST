import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QPushButton, QLabel, QSpinBox, QComboBox, QDialogButtonBox, QGroupBox, QFormLayout
from PyQt5.QtCore import QPointF, Qt

from models.device import Device
from constants import DeviceTypes
from controllers.commands import Command, CompositeCommand

class BulkAddDevicesCommand(Command):
    """Command for adding multiple devices at once."""
    
    def __init__(self, device_controller, devices):
        """Initialize the command.
        
        Args:
            device_controller: The device controller to use for operations
            devices: List of (name, type, position, properties) tuples for devices to add
        """
        super().__init__("Add Multiple Devices")
        self.device_controller = device_controller
        self.device_data = devices
        self.created_devices = []
        
    def execute(self):
        """Execute the command by creating all devices."""
        self.created_devices = []
        
        for name, device_type, position, properties in self.device_data:
            device = self.device_controller._create_device(name, device_type, position, properties)
            self.created_devices.append(device)
            
        return True
        
    def undo(self):
        """Undo the command by removing all created devices."""
        for device in self.created_devices:
            self.device_controller._delete_device(device)
            
        self.created_devices = []
        return True


class BulkDeviceController:
    """Controller for bulk device operations."""
    
    def __init__(self, canvas, device_controller, event_bus, undo_redo_manager=None):
        """Initialize the bulk device controller.
        
        Args:
            canvas: The canvas to operate on
            device_controller: The device controller for creating individual devices
            event_bus: Event bus for broadcasting events
            undo_redo_manager: Undo/redo manager for command pattern support
        """
        self.canvas = canvas
        self.device_controller = device_controller
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
    
    def show_bulk_add_dialog(self, position=None):
        """Show a dialog to add multiple devices at once.
        
        Args:
            position: Optional starting position for the first device
        """
        dialog = BulkDeviceAddDialog(position)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Get device data from the dialog
            device_data = dialog.get_device_data()
            if device_data:
                self._bulk_add_devices(device_data)
    
    def _bulk_add_devices(self, device_data):
        """Add multiple devices at once.
        
        Args:
            device_data: List of (name, type, position, properties) tuples
        """
        self.logger.info(f"Adding {len(device_data)} devices in bulk")
        
        # Use command pattern if undo/redo manager is available
        if self.undo_redo_manager:
            cmd = BulkAddDevicesCommand(self.device_controller, device_data)
            self.undo_redo_manager.push_command(cmd)
        else:
            # Add devices directly without undo support
            for name, device_type, position, properties in device_data:
                self.device_controller._create_device(name, device_type, position, properties)
        
        # Notify that multiple devices were added
        if self.event_bus:
            self.event_bus.emit("bulk_devices_added", len(device_data))


class BulkDeviceAddDialog(QDialog):
    """Dialog for adding multiple devices in bulk."""
    
    def __init__(self, position=None, parent=None):
        """Initialize the dialog.
        
        Args:
            position: Optional starting position for the first device
            parent: Parent widget
        """
        super().__init__(parent)
        self.position = position or QPointF(0, 0)
        self.setWindowTitle("Add Multiple Devices")
        self.setMinimumWidth(500)
        
        # Import device models from DeviceDialog to keep them consistent
        from views.device_dialog import DeviceDialog
        self.DEVICE_MODELS = DeviceDialog.DEVICE_MODELS
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # General controls
        layout.addWidget(QLabel("<b>Create multiple devices at once</b>"))
        
        # Grid layout for device types
        devices_group = QGroupBox("Device Types and Counts")
        grid_layout = QGridLayout()
        
        # Headers
        grid_layout.addWidget(QLabel("<b>Device Type</b>"), 0, 0)
        grid_layout.addWidget(QLabel("<b>Count</b>"), 0, 1)
        grid_layout.addWidget(QLabel("<b>Model</b>"), 0, 2)
        
        # Add entries for each device type
        self.device_counts = {}
        self.device_models = {}
        row = 1
        
        # Use the get_all_types method to get all device types
        for device_type in DeviceTypes.get_all_types():
            if device_type == DeviceTypes.GENERIC:
                continue  # Skip generic type
                
            # Label with device type
            label = QLabel(device_type.title())
            grid_layout.addWidget(label, row, 0)
            
            # Spin box for count
            count_spin = QSpinBox()
            count_spin.setRange(0, 100)
            count_spin.setValue(0)
            grid_layout.addWidget(count_spin, row, 1)
            
            # Model dropdown for this device type
            model_combo = QComboBox()
            model_combo.addItem("Default", "")  # Default empty model
            
            # Add models from the device dialog
            if device_type in self.DEVICE_MODELS:
                for model in self.DEVICE_MODELS[device_type]:
                    model_combo.addItem(model, model)
            
            # Enable the model combo only if count is > 0
            model_combo.setEnabled(False)
            count_spin.valueChanged.connect(lambda value, combo=model_combo: combo.setEnabled(value > 0))
            
            grid_layout.addWidget(model_combo, row, 2)
            
            # Store references
            self.device_counts[device_type] = count_spin
            self.device_models[device_type] = model_combo
            
            row += 1
        
        devices_group.setLayout(grid_layout)
        layout.addWidget(devices_group)
        
        # Layout options
        layout.addWidget(QLabel("<b>Layout Options</b>"))
        
        self.layout_type = QComboBox()
        self.layout_type.addItems(["Grid", "Horizontal Line", "Vertical Line", "Circle"])
        layout.addWidget(self.layout_type)
        
        # Spacing controls
        spacing_layout = QGridLayout()
        spacing_layout.addWidget(QLabel("Horizontal Spacing:"), 0, 0)
        
        self.h_spacing = QSpinBox()
        self.h_spacing.setRange(10, 500)
        self.h_spacing.setValue(100)
        spacing_layout.addWidget(self.h_spacing, 0, 1)
        
        spacing_layout.addWidget(QLabel("Vertical Spacing:"), 1, 0)
        
        self.v_spacing = QSpinBox()
        self.v_spacing.setRange(10, 500)
        self.v_spacing.setValue(100)
        spacing_layout.addWidget(self.v_spacing, 1, 1)
        
        layout.addLayout(spacing_layout)
        
        # Device naming
        layout.addWidget(QLabel("<b>Device Naming</b>"))
        
        self.naming_prefix = QComboBox()
        self.naming_prefix.addItems(["Type", "Custom Prefix"])
        self.naming_prefix.setEditable(True)
        layout.addWidget(self.naming_prefix)
        
        # RMF Defaults
        rmf_group = QGroupBox("RMF Information (Applied to all devices)")
        rmf_layout = QFormLayout()
        
        self.stig_combo = QComboBox()
        self.stig_combo.addItems(["Use default for type", "Compliant", "Non-Compliant", "Exception", "In Progress"])
        rmf_layout.addRow("STIG Compliance:", self.stig_combo)
        
        self.vuln_combo = QComboBox()
        self.vuln_combo.addItems(["Use default for type", "Clean", "Critical Findings", "Moderate Findings", "Low Findings", "Pending"])
        rmf_layout.addRow("Vulnerability Scan:", self.vuln_combo)
        
        self.ato_combo = QComboBox()
        self.ato_combo.addItems(["Use default for type", "Full ATO", "Interim ATO", "Pending", "Expired", "No ATO"])
        rmf_layout.addRow("ATO Status:", self.ato_combo)
        
        rmf_group.setLayout(rmf_layout)
        layout.addWidget(rmf_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_device_data(self):
        """Get the device data from the dialog inputs.
        
        Returns:
            List of (name, type, position, properties) tuples
        """
        device_data = []
        total_devices = 0
        
        # Count total devices to create
        for device_type, spin_box in self.device_counts.items():
            total_devices += spin_box.value()
        
        # If no devices selected, return empty list
        if total_devices == 0:
            return []
        
        # Calculate positions based on layout
        layout_type = self.layout_type.currentText()
        h_spacing = self.h_spacing.value()
        v_spacing = self.v_spacing.value()
        
        # Choose naming scheme
        naming_prefix = self.naming_prefix.currentText()
        # Check if using default or custom naming
        use_default_naming = (naming_prefix == "Type")
        # If the naming prefix is editable but empty, consider it as no prefix
        use_empty_prefix = not use_default_naming and not naming_prefix.strip()
        
        # Get common RMF properties
        common_properties = {}
        if self.stig_combo.currentIndex() > 0:
            common_properties["stig_compliance"] = self.stig_combo.currentText()
        if self.vuln_combo.currentIndex() > 0:
            common_properties["vulnerability_scan"] = self.vuln_combo.currentText()
        if self.ato_combo.currentIndex() > 0:
            common_properties["ato_status"] = self.ato_combo.currentText()
        
        device_index = 1
        
        # Create device data for each type
        for device_type, spin_box in self.device_counts.items():
            count = spin_box.value()
            if count == 0:
                continue
            
            # Get the selected model for this device type
            model_combo = self.device_models[device_type]
            model = model_combo.currentData() if model_combo.currentIndex() > 0 else ""
                
            for i in range(count):
                # Calculate position based on selected layout
                if layout_type == "Grid":
                    row = (device_index - 1) // 5
                    col = (device_index - 1) % 5
                    pos = QPointF(
                        self.position.x() + col * h_spacing,
                        self.position.y() + row * v_spacing
                    )
                elif layout_type == "Horizontal Line":
                    pos = QPointF(
                        self.position.x() + (device_index - 1) * h_spacing,
                        self.position.y()
                    )
                elif layout_type == "Vertical Line":
                    pos = QPointF(
                        self.position.x(),
                        self.position.y() + (device_index - 1) * v_spacing
                    )
                elif layout_type == "Circle":
                    import math
                    radius = max(h_spacing, v_spacing) * 1.5
                    angle = (2 * math.pi / total_devices) * (device_index - 1)
                    pos = QPointF(
                        self.position.x() + radius * math.cos(angle),
                        self.position.y() + radius * math.sin(angle)
                    )
                
                # Generate name based on selected naming scheme
                if use_default_naming:
                    # If model is selected, use it as the base for the name
                    if model:
                        name = f"{model} {device_index}"
                    else:
                        # Fallback to device type if no model
                        name = f"{device_type.title()}{device_index}"
                elif use_empty_prefix:
                    # If prefix is empty, prefer model name if available
                    if model:
                        name = f"{model} {device_index}"
                    else:
                        # Fallback to device type if no model and no prefix
                        name = f"{device_type.title()}{device_index}"
                else:
                    # Use custom prefix as specified
                    name = f"{naming_prefix}{device_index}"
                
                # Create properties
                properties = common_properties.copy()
                if model:
                    properties["model"] = model
                
                # Add device data
                device_data.append((name, device_type, pos, properties))
                device_index += 1
        
        return device_data
