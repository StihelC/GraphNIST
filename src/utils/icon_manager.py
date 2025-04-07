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
    ADD_CONNECTION = "connection_straight"
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
        
        # Fix paths to correct locations
        self.svg_path = "src/resources/icons/svg"
        self.png_path = "src/resources/icons"
        
        # Add application-root-relative paths for when running from different directories
        # Get the path to the current file (icon_manager.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to get to the src directory
        src_dir = os.path.dirname(current_dir)
        
        # Define absolute paths based on src directory
        self.abs_svg_path = os.path.join(src_dir, "resources", "icons", "svg")
        self.abs_png_path = os.path.join(src_dir, "resources", "icons")
        
        # Map requested icon names to existing icon files
        # This allows us to use existing icons for toolbar buttons
        # All of these files were confirmed to exist in the svg directory
        self.DEFAULT_ICON_NAMES = {
            # These match exactly with the SVG filenames
            "select_tool": "select_tool",         # select_tool.svg
            "add_device": "add_device",           # add_device.svg
            "add_connection": "add_connection",   # add_connection.svg  
            "add_boundary": "add_boundary",       # add_boundary.svg
            "delete": "delete",                   # delete.svg
            "magnify": "magnify",                 # magnify.svg
            "zoom_in": "zoom_in",                 # zoom_in.svg
            "zoom_out": "zoom_out",               # zoom_out.svg
            "zoom_reset": "zoom_reset",           # zoom_reset.svg
            "undo": "undo",                       # undo.svg
            "redo": "redo",                       # redo.svg
            "align": "align",                     # align.svg
            "cut": "cut",                         # cut.svg
            "copy": "copy",                       # copy.svg
            "paste": "paste",                     # paste.svg
            "connection_straight": "connection_straight",    # connection_straight.svg
            "connection_orthogonal": "connection_orthogonal",# connection_orthogonal.svg
            "connection_curved": "connection_curved",        # connection_curved.svg

            # Device type icons - not directly used in toolbar but used elsewhere
            "device": "device",                   # device.svg
            "router": "router",                   # router.svg
            "switch": "switch",                   # switch.svg
            "server": "server",                   # server.svg
            "workstation": "workstation",         # workstation.svg
            "firewall": "firewall",               # firewall.svg
            "cloud": "cloud",                     # cloud.svg
        }
        
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
        
        # Log what we're trying to load for debugging
        self.logger.debug(f"Trying to load icon: {name}")
        
        # Map the icon name to an existing icon if available
        icon_name = self.DEFAULT_ICON_NAMES.get(name, name)
        if icon_name != name:
            self.logger.debug(f"Mapped icon name from '{name}' to '{icon_name}'")
            
        # Try to load SVG version first using relative path
        svg_path = os.path.join(self.svg_path, f"{icon_name}.svg")
        if os.path.exists(svg_path):
            self.logger.debug(f"Found icon at relative path: {svg_path}")
            icon = QIcon(svg_path)
            self.icon_cache[name] = icon
            return icon
            
        # Try absolute SVG path if relative didn't work
        abs_svg_path = os.path.join(self.abs_svg_path, f"{icon_name}.svg")
        if os.path.exists(abs_svg_path):
            self.logger.debug(f"Found icon at absolute path: {abs_svg_path}")
            icon = QIcon(abs_svg_path)
            self.icon_cache[name] = icon
            return icon
        
        # Try fallback if provided
        if fallback and os.path.exists(fallback):
            self.logger.debug(f"Using provided fallback: {fallback}")
            icon = QIcon(fallback)
            self.icon_cache[name] = icon
            return icon
            
        # Try PNG with relative path
        png_path = os.path.join(self.png_path, f"{icon_name}.png")
        if os.path.exists(png_path):
            self.logger.debug(f"Found PNG at relative path: {png_path}")
            icon = QIcon(png_path)
            self.icon_cache[name] = icon
            return icon
            
        # Try absolute PNG path if relative didn't work
        abs_png_path = os.path.join(self.abs_png_path, f"{icon_name}.png")
        if os.path.exists(abs_png_path):
            self.logger.debug(f"Found PNG at absolute path: {abs_png_path}")
            icon = QIcon(abs_png_path)
            self.icon_cache[name] = icon
            return icon
            
        # Fallback to a known existing icon like device.svg if available
        default_icon_path = os.path.join(self.abs_svg_path, "device.svg")
        if os.path.exists(default_icon_path):
            self.logger.info(f"Icon '{name}' not found, using default device.svg")
            icon = QIcon(default_icon_path)
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