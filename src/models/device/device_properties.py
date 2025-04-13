from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QPointF
import logging

class DeviceProperties:
    """Manages device properties and their visual representation."""
    
    def __init__(self, device):
        """Initialize the device properties manager.
        
        Args:
            device: The parent device instance
        """
        self.device = device
        self.logger = logging.getLogger(__name__)
        
        # Initialize display properties dictionary
        self.display_properties = {}
        
        # Create property labels
        self.property_labels = {}
    
    def set_property(self, name, value):
        """Set a device property with validation.
        
        Args:
            name: Property name
            value: Property value
            
        Returns:
            bool: True if property was set, False otherwise
        """
        try:
            if hasattr(self.device, 'properties'):
                # Special handling for specific properties
                if name == 'name':
                    old_name = self.device.name
                    self.device.name = value
                    self.device.visuals.update_label_position()
                    self.logger.debug(f"Changed device name from '{old_name}' to '{value}'")
                    return True
                elif name == 'color':
                    self.device.properties[name] = value
                    self.device.visuals.update_color(value)
                    return True
                else:
                    # Standard property
                    old_value = self.device.properties.get(name)
                    self.device.properties[name] = value
                    
                    # Check if this property is displayed
                    if name in self.property_labels:
                        self.update_property_label(name)
                    
                    # Emit signal if available
                    if hasattr(self.device.signals, 'property_changed'):
                        self.device.signals.property_changed.emit(self.device, name, value)
                    
                    self.logger.debug(f"Set property '{name}' from '{old_value}' to '{value}'")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting property {name}: {str(e)}")
            return False

    def get_property(self, name, default=None):
        """Get a device property.
        
        Args:
            name: Property name
            default: Default value if property doesn't exist
            
        Returns:
            The property value or default
        """
        # Special case for name
        if name == 'name':
            return self.device.name
            
        # Get from properties dict
        if hasattr(self.device, 'properties'):
            return self.device.properties.get(name, default)
            
        return default

    def toggle_property_display(self, property_name, show):
        """Toggle the display of a property on the device."""
        if show:
            # Create and show property label if not already visible
            if property_name not in self.property_labels:
                self._create_property_label(property_name)
            
            # Mark this property as displayed
            self.display_properties[property_name] = True
        else:
            # Hide property label if shown
            if property_name in self.property_labels:
                label = self.property_labels[property_name]
                if label.scene():
                    self.device.scene().removeItem(label)
                del self.property_labels[property_name]
            
            # Mark this property as not displayed
            self.display_properties[property_name] = False
        
        # Force update
        self.device.update()
        
        return True

    def _create_property_label(self, property_name):
        """Create a text label for a property."""
        if property_name in self.device.properties:
            # Get property value
            raw_value = self.device.properties[property_name]
            
            # Extract actual value if it's in {'value': X} format
            if isinstance(raw_value, dict) and 'value' in raw_value:
                value = raw_value['value']
            else:
                value = raw_value
                
            # Format property name: replace underscores with spaces and apply title case
            display_name = property_name.replace('_', ' ').title()
            
            # Format the label with a cleaner format
            label_text = f"{display_name}: {value}"
            
            # Create label
            label = QGraphicsTextItem(label_text, self.device)
            
            # Apply font settings if available
            if hasattr(self.device, 'font_settings_manager') and self.device.font_settings_manager:
                # Get font settings
                font_size = self.device.font_settings_manager.get_font_size('property')
                font_bold = self.device.font_settings_manager.get_font_bold('property')
                font_italic = self.device.font_settings_manager.get_font_italic('property')
                
                # Create and apply font
                font = QFont()
                font.setPointSize(font_size)
                font.setBold(font_bold)
                font.setItalic(font_italic)
                label.setFont(font)
            else:
                # Use default font settings
                font = QFont()
                font.setPointSize(8)
                label.setFont(font)
            
            # Set color
            if hasattr(self.device, 'theme_manager') and self.device.theme_manager:
                theme_is_dark = self.device.theme_manager.is_dark_theme()
                color = QColor(255, 255, 255) if theme_is_dark else QColor(0, 0, 0)
                label.setDefaultTextColor(color)
            
            # Store reference
            self.property_labels[property_name] = label
            
            # Position all labels
            self._update_property_label_positions()
            
            # Set z-value high to ensure visibility
            label.setZValue(15)
            
            return label
        
        return None

    def update_property_label(self, property_name):
        """Update an existing property label."""
        if property_name in self.property_labels and property_name in self.device.properties:
            # Get property value
            raw_value = self.device.properties[property_name]
            
            # Extract actual value if it's in {'value': X} format
            if isinstance(raw_value, dict) and 'value' in raw_value:
                value = raw_value['value']
            else:
                value = raw_value
            
            # Format property name: replace underscores with spaces and apply title case
            display_name = property_name.replace('_', ' ').title()
            
            label_text = f"{display_name}: {value}"
            self.property_labels[property_name].setPlainText(label_text)
            
            # Reposition in case size changed
            self._update_property_label_positions()

    def _update_property_label_positions(self):
        """Update the positions of all property labels."""
        if not self.property_labels:
            return
            
        # Get device dimensions
        rect = self.device.boundingRect()
        device_width = rect.width()
        
        # Start position - below the device name
        x_pos = 0
        y_pos = rect.height() + 20  # Start below device name
        
        # Position each label
        for property_name, label in self.property_labels.items():
            # Center the label
            label_width = label.boundingRect().width()
            x_pos = (device_width - label_width) / 2
            
            # Set position
            label.setPos(x_pos, y_pos)
            
            # Move down for next label
            y_pos += label.boundingRect().height() + 2

    def update_all_property_labels(self):
        """Update all property labels with current values."""
        # Update all existing property labels
        for property_name in list(self.property_labels.keys()):
            self.update_property_label(property_name)
            
        # Apply font settings if available
        if hasattr(self.device, 'font_settings_manager') and self.device.font_settings_manager:
            self.update_font(self.device.font_settings_manager)
            
        # Make sure positions are correct
        self._update_property_label_positions()

    def update_font(self, font_settings_manager):
        """Update font settings for all property labels.
        
        Args:
            font_settings_manager: Font settings manager instance
        """
        if not self.property_labels:
            return
            
        # Get font settings for properties
        font_size = font_settings_manager.get_font_size('property')
        font_bold = font_settings_manager.get_font_bold('property')
        font_italic = font_settings_manager.get_font_italic('property')
        
        # Create font object
        font = QFont()
        font.setPointSize(font_size)
        font.setBold(font_bold)
        font.setItalic(font_italic)
        
        # Apply to all property labels
        for label in self.property_labels.values():
            label.setFont(font)
            
        # Reposition in case sizes changed
        self._update_property_label_positions()
        
        # Force update
        self.device.update()

    def get_property_display_state(self, property_name):
        """Check if a property is currently displayed."""
        return self.display_properties.get(property_name, False)

    def update_theme(self, theme_name=None):
        """Update property labels for theme changes."""
        if not hasattr(self.device, 'theme_manager') or self.device.theme_manager is None:
            return
            
        # Get theme info
        theme_manager = self.device.theme_manager
        theme_is_dark = theme_manager.is_dark_theme()
        
        # Update all property labels
        for label in self.property_labels.values():
            color = QColor(255, 255, 255) if theme_is_dark else QColor(0, 0, 0)
            label.setDefaultTextColor(color) 