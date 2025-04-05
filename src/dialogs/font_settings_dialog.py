from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, 
    QLabel, QSpinBox, QPushButton, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt
import logging

class FontSettingsDialog(QDialog):
    """Dialog for configuring font settings in the application."""
    
    def __init__(self, parent=None, font_settings_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Font Settings")
        self.setFixedWidth(450)
        self.font_settings_manager = font_settings_manager
        self.logger = logging.getLogger(__name__)
        
        self._create_layout()
        self._load_current_settings()
        
    def _create_layout(self):
        """Create the dialog layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # UI Font Settings Group
        ui_group = QGroupBox("UI Font Settings")
        ui_layout = QFormLayout()
        
        self.ui_font_spin = QSpinBox()
        self.ui_font_spin.setRange(7, 16)  # Reasonable range for UI
        self.ui_font_spin.setSuffix(" pt")
        self.ui_font_spin.valueChanged.connect(self._preview_ui_font)
        
        ui_layout.addRow("UI Font Size:", self.ui_font_spin)
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        # Device Font Settings Group
        device_group = QGroupBox("Device Font Settings")
        device_layout = QFormLayout()
        
        self.device_label_font_spin = QSpinBox()
        self.device_label_font_spin.setRange(8, 20)  # Wider range for device labels
        self.device_label_font_spin.setSuffix(" pt")
        self.device_label_font_spin.valueChanged.connect(self._preview_device_label_font)
        
        self.device_property_font_spin = QSpinBox()
        self.device_property_font_spin.setRange(6, 16)  # Range for property labels
        self.device_property_font_spin.setSuffix(" pt")
        self.device_property_font_spin.valueChanged.connect(self._preview_device_property_font)
        
        device_layout.addRow("Device Name Font Size:", self.device_label_font_spin)
        device_layout.addRow("Property Labels Font Size:", self.device_property_font_spin)
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Preview section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.ui_preview = QLabel("UI Text Preview")
        self.ui_preview.setAlignment(Qt.AlignCenter)
        
        self.device_label_preview = QLabel("Device Name")
        self.device_label_preview.setAlignment(Qt.AlignCenter)
        
        self.device_property_preview = QLabel("IP: 192.168.1.1")
        self.device_property_preview.setAlignment(Qt.AlignCenter)
        
        preview_layout.addWidget(self.ui_preview)
        preview_layout.addWidget(self.device_label_preview)
        preview_layout.addWidget(self.device_property_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_settings)
        self.apply_button.setEnabled(False)  # Disabled until changes are made
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._save_and_close)
        self.ok_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _load_current_settings(self):
        """Load current font settings from manager."""
        if self.font_settings_manager:
            # Load values into spin boxes
            self.ui_font_spin.setValue(self.font_settings_manager.get_ui_font_size())
            self.device_label_font_spin.setValue(self.font_settings_manager.get_device_label_font_size())
            self.device_property_font_spin.setValue(self.font_settings_manager.get_device_property_font_size())
            
            # Update previews
            self._update_previews()
            
            # Connect value change signals
            self.ui_font_spin.valueChanged.connect(lambda: self.apply_button.setEnabled(True))
            self.device_label_font_spin.valueChanged.connect(lambda: self.apply_button.setEnabled(True))
            self.device_property_font_spin.valueChanged.connect(lambda: self.apply_button.setEnabled(True))
    
    def _update_previews(self):
        """Update the font preview labels."""
        # UI font preview
        ui_font = self.font_settings_manager.get_ui_font()
        ui_font.setPointSize(self.ui_font_spin.value())
        self.ui_preview.setFont(ui_font)
        
        # Device label font preview
        device_label_font = self.font_settings_manager.get_device_label_font()
        device_label_font.setPointSize(self.device_label_font_spin.value())
        self.device_label_preview.setFont(device_label_font)
        
        # Device property font preview
        device_property_font = self.font_settings_manager.get_device_property_font()
        device_property_font.setPointSize(self.device_property_font_spin.value())
        self.device_property_preview.setFont(device_property_font)
    
    def _preview_ui_font(self, size):
        """Preview UI font size change."""
        ui_font = self.font_settings_manager.get_ui_font()
        ui_font.setPointSize(size)
        self.ui_preview.setFont(ui_font)
    
    def _preview_device_label_font(self, size):
        """Preview device label font size change."""
        device_label_font = self.font_settings_manager.get_device_label_font()
        device_label_font.setPointSize(size)
        self.device_label_preview.setFont(device_label_font)
    
    def _preview_device_property_font(self, size):
        """Preview device property font size change."""
        device_property_font = self.font_settings_manager.get_device_property_font()
        device_property_font.setPointSize(size)
        self.device_property_preview.setFont(device_property_font)
    
    def _reset_to_defaults(self):
        """Reset all font settings to default values."""
        self.ui_font_spin.setValue(self.font_settings_manager.DEFAULT_UI_FONT_SIZE)
        self.device_label_font_spin.setValue(self.font_settings_manager.DEFAULT_DEVICE_LABEL_FONT_SIZE)
        self.device_property_font_spin.setValue(self.font_settings_manager.DEFAULT_DEVICE_PROPERTY_FONT_SIZE)
        self.apply_button.setEnabled(True)
    
    def _apply_settings(self):
        """Apply the current settings without closing the dialog."""
        if self.font_settings_manager:
            self.font_settings_manager.set_ui_font_size(self.ui_font_spin.value())
            self.font_settings_manager.set_device_label_font_size(self.device_label_font_spin.value())
            self.font_settings_manager.set_device_property_font_size(self.device_property_font_spin.value())
            self.apply_button.setEnabled(False)
    
    def _save_and_close(self):
        """Save settings and close the dialog."""
        self._apply_settings()
        self.accept()

    @classmethod
    def show_dialog(cls, parent, font_settings_manager):
        """Show the font settings dialog and return result."""
        dialog = cls(parent, font_settings_manager)
        result = dialog.exec_()
        return result == QDialog.Accepted 