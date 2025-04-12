from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
import logging

class BaseSection(QGroupBox):
    """Base class for all property sections."""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.logger = logging.getLogger(__name__)
        
        # Apply common styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(10, 15, 10, 10)
        
        # Initialize UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI elements. Should be overridden by subclasses."""
        pass
    
    def reset(self):
        """Reset all fields to their default state. Should be overridden by subclasses."""
        pass
    
    def _clear_layout(self, layout):
        """Safely clear a layout of all widgets."""
        if layout is None:
            return
            
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def _handle_error(self, method_name, error):
        """Common error handling for all section methods."""
        self.logger.error(f"Error in {self.__class__.__name__}.{method_name}: {str(error)}") 