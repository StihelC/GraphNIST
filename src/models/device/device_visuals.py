from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QFileDialog
from PyQt5.QtGui import QPixmap, QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
import os
import logging

class DeviceVisuals:
    """Class for managing the visual aspects of a device."""
    
    def __init__(self, device):
        """Initialize the device visual components.
        
        Args:
            device: The parent device instance
        """
        self.device = device
        self.logger = logging.getLogger(__name__)
        
        # Initialize component variables
        self.text_item = None
        self.icon_item = None
        self.rect_item = None
        
        # Size settings
        self.width = 80
        self.height = 80
        
        # Create visual components
        self._create_visuals()
    
    def _create_visuals(self):
        """Create the visual representation of the device."""
        # Skip background rectangle creation - we don't want a box in the background
        # self.rect_item = QGraphicsRectItem(0, 0, self.width, self.height, self.device)
        
        # Set the visual appearance based on device type - use a default gray if no color specified
        # device_color = self.device.properties.get('color', QColor(150, 150, 150))
        
        # Create a visually distinct appearance
        # brush = QBrush(device_color)
        # self.rect_item.setBrush(brush)
        # self.rect_item.setPen(QPen(Qt.black, 1))
        
        # Set z-value for the background rect (lowest)
        # self.rect_item.setZValue(1)
        
        # Initialize rect_item as None to indicate no background rectangle
        self.rect_item = None
        
        # Load the device icon first so it appears above the background
        self._try_load_icon()
        
        # NOTE: We don't create the text label here anymore.
        # It's now created only in the Device constructor via DeviceLabel.create_label()
        # This avoids duplicate label creation
        
        # Make device children non-movable by default
        for child in self.device.childItems():
            child.setFlag(QGraphicsItem.ItemIsSelectable, False)
            child.setFlag(QGraphicsItem.ItemIsMovable, False)
            child.setAcceptedMouseButtons(Qt.NoButton)
    
    def update_label_position(self):
        """Position the device name label below the device."""
        if hasattr(self.device, 'label') and self.device.label:
            self.device.label.update_position()
    
    def _try_load_icon(self):
        """Try to load the device icon, first from custom icon, then from standard paths."""
        # Try custom icon first if provided
        if self.device.custom_icon_path and os.path.exists(self.device.custom_icon_path):
            self.logger.debug(f"Loading custom icon: {self.device.custom_icon_path}")
            if self._load_icon(self.device.custom_icon_path):
                return
        
        # Get default icon name based on device type
        icon_name = self.device.properties.get('icon', 'device.svg')
        
        # Find and load the icon
        if not self._try_load_icon_by_name(icon_name):
            # Fall back to generic icon if type-specific icon not found
            self._try_load_icon_by_name('device.svg')
    
    def _get_icon_directories(self):
        """Get the directories to search for icons."""
        directories = []
        
        # Get the base directory - use __file__ to find the package directory
        try:
            # First, add the src/resources/icons directory
            # Since device_visuals.py is in src/models/device/, we need to go up 3 levels
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            resource_dir = os.path.join(base_dir, 'src', 'resources', 'icons')
            directories.append(resource_dir)
            
            # Also check for svg subdirectory
            svg_dir = os.path.join(resource_dir, 'svg')
            directories.append(svg_dir)
            
            # For non-development environments, also check standard locations
            alt_dir = os.path.join(base_dir, 'resources', 'icons')
            directories.append(alt_dir)
            
            alt_svg_dir = os.path.join(alt_dir, 'svg')
            directories.append(alt_svg_dir)
            
            # Log the directories we're searching
            self.logger.debug(f"Icon search directories: {directories}")
        except Exception as e:
            self.logger.error(f"Error setting up icon directories: {e}")
            # Fallback to some default paths
            directories = [
                os.path.join('src', 'resources', 'icons', 'svg'),
                os.path.join('src', 'resources', 'icons'),
                os.path.join('resources', 'icons', 'svg'),
                os.path.join('resources', 'icons')
            ]
        
        return directories
    
    def _try_load_icon_by_name(self, name):
        """Try to load an icon by name from various directories."""
        for directory in self._get_icon_directories():
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return self._load_icon(path)
        
        self.logger.warning(f"Could not find icon {name} in any search directories")
        return False
    
    def _load_icon(self, path):
        """Load an icon from a file path."""
        try:
            if path.lower().endswith('.svg'):
                return self._load_svg_icon(path)
            else:
                return self._load_pixmap_icon(path)
        except Exception as e:
            self.logger.error(f"Error loading icon from {path}: {str(e)}")
            return False
    
    def _load_svg_icon(self, path):
        """Load an SVG icon."""
        try:
            # Create a QGraphicsSvgItem to display the SVG
            renderer = QSvgRenderer(path)
            svg_item = QGraphicsSvgItem()
            svg_item.setSharedRenderer(renderer)
            
            # Scale to fit our device box - make it fill more of the box
            svg_rect = renderer.defaultSize()
            scale_x = self.width * 1.0 / svg_rect.width()  # Full scale 1.0
            scale_y = self.height * 1.0 / svg_rect.height()  # Full scale 1.0
            scale = min(scale_x, scale_y)
            
            # Apply scaling
            svg_item.setScale(scale)
            
            # Center in the device box
            svg_width = svg_rect.width() * scale
            svg_height = svg_rect.height() * scale
            x_pos = (self.width - svg_width) / 2
            y_pos = (self.height - svg_height) / 2
            
            # Set position
            svg_item.setPos(x_pos, y_pos)
            
            # Add to device
            svg_item.setParentItem(self.device)
            svg_item.setZValue(10)  # Set z-value above background (1) but below text (20)
            
            # Store reference
            self.icon_item = svg_item
            
            # Successfully loaded
            self.logger.debug(f"Successfully loaded SVG icon: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load SVG icon {path}: {str(e)}")
            return False
    
    def _load_pixmap_icon(self, path):
        """Load a pixmap (raster) icon."""
        try:
            # Load pixmap
            pixmap = QPixmap(path)
            if pixmap.isNull():
                self.logger.error(f"Failed to load pixmap from {path}")
                return False
            
            # Scale to fit in device box
            scaled_pixmap = pixmap.scaled(
                int(self.width * 1.0),  # Full scale 1.0
                int(self.height * 1.0), # Full scale 1.0
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Set the pixmap on the device
            self.device.setPixmap(scaled_pixmap)
            
            # Center in the device box
            x_pos = (self.width - scaled_pixmap.width()) / 2
            y_pos = (self.height - scaled_pixmap.height()) / 2
            
            # Store original pixmap for reference
            self.device.original_pixmap = pixmap
            
            # Set device offset so icon is centered
            self.device.setOffset(x_pos, y_pos)
            
            # Successfully loaded
            self.logger.debug(f"Successfully loaded pixmap icon: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load pixmap icon {path}: {str(e)}")
            return False
    
    def upload_custom_icon(self):
        """Open a file dialog to upload a custom icon."""
        try:
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setNameFilter("Images (*.png *.jpg *.svg)")
            
            if dialog.exec_():
                file_path = dialog.selectedFiles()[0]
                self.device.custom_icon_path = file_path
                
                # Clear any existing icon
                if self.icon_item and self.icon_item.parentItem() == self.device:
                    self.device.scene().removeItem(self.icon_item)
                    self.icon_item = None
                
                # Load the new icon
                self._try_load_icon()
                return True
                
            return False
        except Exception as e:
            self.logger.error(f"Error uploading custom icon: {str(e)}")
            return False
    
    def update_color(self, color):
        """Update the device's background color."""
        # We no longer have a rect_item, so this method is a no-op
        # but we'll keep it to maintain compatibility
        pass
    
    def update_theme(self, theme_name=None):
        """Update visual elements based on theme."""
        theme_is_dark = False
        if hasattr(self.device, 'theme_manager') and self.device.theme_manager:
            theme_is_dark = self.device.theme_manager.is_dark_theme()
            
        # Skip updating rectangle outline since we removed it
        # if self.rect_item:
        #     outline_color = QColor(200, 200, 200) if theme_is_dark else QColor(0, 0, 0)
        #     self.rect_item.setPen(QPen(outline_color, 1))
        
        # Let the device label handle its own theme update
        if hasattr(self.device, 'label') and self.device.label:
            self.device.label.update_theme(theme_name) 