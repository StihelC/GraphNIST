import os
from PyQt5.QtGui import QIcon
import logging

class IconManager:
    """Centralized icon management for the application.
    
    This class manages loading of SVG and PNG icons, provides a consistent API
    for accessing icons, and handles fallbacks appropriately.
    """
    
    # Basic UI controls
    SELECT = "select_tool"
    ADD_DEVICE = "add_device"
    ADD_CONNECTION = "add_connection"
    ADD_BOUNDARY = "add_boundary"
    DELETE = "delete"
    MAGNIFY = "magnify"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    ZOOM_RESET = "zoom_reset"
    
    # Clipboard operations
    CUT = "cut"
    COPY = "copy"
    PASTE = "paste"
    
    # File operations
    NEW = "new"
    OPEN = "open"
    SAVE = "save"
    SAVE_AS = "save_as"
    EXPORT = "export"
    
    # Alignment
    ALIGN = "align"
    ALIGN_LEFT = "align_left"
    ALIGN_RIGHT = "align_right"
    ALIGN_TOP = "align_top"
    ALIGN_BOTTOM = "align_bottom"
    ALIGN_CENTER_H = "align_center_h"
    ALIGN_CENTER_V = "align_center_v"
    DISTRIBUTE_H = "distribute_h"
    DISTRIBUTE_V = "distribute_v"
    
    # Connection styles
    CONNECTION_STRAIGHT = "connection_straight"
    CONNECTION_ORTHOGONAL = "connection_orthogonal"
    CONNECTION_CURVED = "connection_curved"
    
    # Miscellaneous
    UNDO = "undo"
    REDO = "redo"
    SETTINGS = "settings"
    GRID = "grid"
    THEME = "theme"
    
    def __init__(self):
        """Initialize the icon manager."""
        self.logger = logging.getLogger(__name__)
        
        # Default paths
        self.svg_path = "src/resources/icons/svg"
        self.png_path = "resources/icons"
        
        # Cache for loaded icons to avoid repeated disk access
        self.icon_cache = {}

    def get_icon(self, name, fallback=None):
        """Load an icon from SVG if available or fallback to regular image.
        
        Args:
            name (str): Icon name without extension
            fallback (str, optional): Fallback icon path if SVG not found
        
        Returns:
            QIcon: The loaded icon
        """
        # Check cache first
        if name in self.icon_cache:
            return self.icon_cache[name]
            
        # Try to load SVG version first
        svg_path = os.path.join(self.svg_path, f"{name}.svg")
        if os.path.exists(svg_path):
            icon = QIcon(svg_path)
            self.icon_cache[name] = icon
            return icon
        
        # Try fallback if provided
        if fallback and os.path.exists(fallback):
            icon = QIcon(fallback)
            self.icon_cache[name] = icon
            return icon
            
        # Default fallback to PNG
        png_path = os.path.join(self.png_path, f"{name}.png")
        if os.path.exists(png_path):
            icon = QIcon(png_path)
            self.icon_cache[name] = icon
            return icon
            
        # Return empty icon if nothing found
        self.logger.warning(f"Icon not found: {name}")
        return QIcon()
        
    def clear_cache(self):
        """Clear the icon cache to reload icons from disk."""
        self.icon_cache.clear()
        
    def set_paths(self, svg_path=None, png_path=None):
        """Set custom paths for icon directories.
        
        Args:
            svg_path (str, optional): Path to SVG icon directory
            png_path (str, optional): Path to PNG icon directory
        """
        if svg_path:
            self.svg_path = svg_path
        if png_path:
            self.png_path = png_path
        
        # Clear cache after changing paths
        self.clear_cache()

# Create a singleton instance
icon_manager = IconManager() 