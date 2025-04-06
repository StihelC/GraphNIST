import logging
from PyQt5.QtCore import QSettings, QObject, pyqtSignal
from PyQt5.QtGui import QFont

class FontSettingsManager(QObject):
    """Manages font settings for the application."""
    
    # Signals for font changes
    ui_font_changed = pyqtSignal(QFont)
    device_label_font_changed = pyqtSignal(QFont)
    device_property_font_changed = pyqtSignal(QFont)
    
    # Default settings
    DEFAULT_UI_FONT_SIZE = 11
    DEFAULT_DEVICE_LABEL_FONT_SIZE = 12
    DEFAULT_DEVICE_PROPERTY_FONT_SIZE = 10
    
    def __init__(self):
        """Initialize the font settings manager."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("GraphNIST", "GraphNIST")
        
        # Initialize font settings with default values if not already set
        if not self.settings.contains("ui_font_size"):
            self.settings.setValue("ui_font_size", self.DEFAULT_UI_FONT_SIZE)
        if not self.settings.contains("device_label_font_size"):
            self.settings.setValue("device_label_font_size", self.DEFAULT_DEVICE_LABEL_FONT_SIZE)
        if not self.settings.contains("device_property_font_size"):
            self.settings.setValue("device_property_font_size", self.DEFAULT_DEVICE_PROPERTY_FONT_SIZE)
            
        # Create font objects
        self.ui_font = QFont("Arial", self.get_ui_font_size())
        self.device_label_font = QFont("Arial", self.get_device_label_font_size())
        self.device_property_font = QFont("Arial", self.get_device_property_font_size())
    
    def get_ui_font_size(self):
        """Get UI font size from settings."""
        return self.settings.value("ui_font_size", self.DEFAULT_UI_FONT_SIZE, type=int)
    
    def get_device_label_font_size(self):
        """Get device label font size from settings."""
        return self.settings.value("device_label_font_size", self.DEFAULT_DEVICE_LABEL_FONT_SIZE, type=int)
    
    def get_device_property_font_size(self):
        """Get device property label font size from settings."""
        return self.settings.value("device_property_font_size", self.DEFAULT_DEVICE_PROPERTY_FONT_SIZE, type=int)
    
    def set_ui_font_size(self, size):
        """Set UI font size and emit change signal."""
        self.settings.setValue("ui_font_size", size)
        self.ui_font.setPointSize(size)
        self.ui_font_changed.emit(self.ui_font)
        self.logger.info(f"UI font size set to {size}")
    
    def set_device_label_font_size(self, size):
        """Set device label font size and emit change signal."""
        self.settings.setValue("device_label_font_size", size)
        self.device_label_font.setPointSize(size)
        self.device_label_font_changed.emit(self.device_label_font)
        self.logger.info(f"Device label font size set to {size}")
    
    def set_device_property_font_size(self, size):
        """Set device property label font size and emit change signal."""
        self.settings.setValue("device_property_font_size", size)
        self.device_property_font.setPointSize(size)
        self.device_property_font_changed.emit(self.device_property_font)
        self.logger.info(f"Device property font size set to {size}")
    
    def get_ui_font(self):
        """Get the UI font object."""
        return self.ui_font
    
    def get_device_label_font(self):
        """Get the device label font object."""
        return self.device_label_font
    
    def get_device_property_font(self):
        """Get the device property label font object."""
        return self.device_property_font 