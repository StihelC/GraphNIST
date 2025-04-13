from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import logging

class DeviceLabel:
    """Manages the device label/name display."""
    
    def __init__(self, device):
        """Initialize the device label manager.
        
        Args:
            device: The parent device instance
        """
        self.device = device
        self.logger = logging.getLogger(__name__)
        
        # Text item for the device name
        self.text_item = None
        
        # Default font settings
        self.font_size = 9
        self.font_bold = True
        self.is_italic = False
        
    def create_label(self, name=None):
        """Create or recreate the device label.
        
        Args:
            name: Optional name to set (uses device.name if None)
        """
        # Remove existing label if present
        if self.text_item and self.text_item.scene():
            self.device.scene().removeItem(self.text_item)
        
        # Use provided name or device name
        text = name if name is not None else self.device.name
        
        # Create new text item
        self.text_item = QGraphicsTextItem(text, self.device)
        
        # Apply font settings
        font = QFont()
        font.setPointSize(self.font_size)
        font.setBold(self.font_bold)
        font.setItalic(self.is_italic)
        self.text_item.setFont(font)
        
        # Set color based on theme
        self._update_color()
        
        # Position the label
        self.update_position()
        
        # Set z-value to be above device
        self.text_item.setZValue(20)
        
        return self.text_item
    
    def update_text(self, new_text=None):
        """Update the text of the device label.
        
        Args:
            new_text: New text to set (uses device.name if None)
        """
        if not self.text_item:
            return self.create_label(new_text)
            
        # Update text
        text = new_text if new_text is not None else self.device.name
        self.text_item.setPlainText(text)
        
        # Reposition after text change
        self.update_position()
        
        return self.text_item
    
    def update_position(self):
        """Update the position of the label."""
        if not self.text_item:
            return
            
        # Get device dimensions
        device_rect = self.device.boundingRect()
        device_width = device_rect.width()
        device_height = device_rect.height()
        
        # Get label dimensions
        label_width = self.text_item.boundingRect().width()
        
        # Center below the device
        x_pos = (device_width - label_width) / 2
        y_pos = device_height + 3  # Small gap below device
        
        # Set new position
        self.text_item.setPos(x_pos, y_pos)
    
    def update_font(self, size=None, bold=None, italic=None):
        """Update font settings for the label.
        
        Args:
            size: Font size in points
            bold: Whether font should be bold
            italic: Whether font should be italic
        """
        # Update settings if provided
        if size is not None:
            self.font_size = size
        if bold is not None:
            self.font_bold = bold
        if italic is not None:
            self.is_italic = italic
            
        # If label exists, update its font
        if self.text_item:
            font = self.text_item.font()
            font.setPointSize(self.font_size)
            font.setBold(self.font_bold)
            font.setItalic(self.is_italic)
            self.text_item.setFont(font)
            
            # Reposition after font change (may affect size)
            self.update_position()
    
    def _update_color(self):
        """Update text color based on theme."""
        if not self.text_item:
            return
            
        # Default to black if no theme manager
        color = QColor(0, 0, 0)
        
        # Use theme-based color if available
        if hasattr(self.device, 'theme_manager') and self.device.theme_manager:
            theme_is_dark = self.device.theme_manager.is_dark_theme()
            color = QColor(255, 255, 255) if theme_is_dark else QColor(0, 0, 0)
            
        # Set the color
        self.text_item.setDefaultTextColor(color)
    
    def update_theme(self, theme_name=None):
        """Update for theme changes."""
        self._update_color()
        
    def set_visible(self, visible):
        """Show or hide the label."""
        if self.text_item:
            self.text_item.setVisible(visible) 