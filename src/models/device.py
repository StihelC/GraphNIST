from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem, QFileDialog, QApplication
from PyQt5.QtGui import QPixmap, QColor, QPen, QBrush, QPainterPath, QPainter, QFont, QPalette
from PyQt5.QtCore import QRectF, Qt, QPointF, QObject, pyqtSignal
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
import uuid
import os
import logging
from constants import DeviceTypes
import traceback
import hashlib

class DeviceSignals(QObject):
    """Signals emitted by devices."""
    moved = pyqtSignal(object)  # device
    double_clicked = pyqtSignal(object)  # device
    deleted = pyqtSignal(object)  # device

class Device(QGraphicsPixmapItem):
    """Represents a network device in the topology."""
    
    # Device properties organized by type
    DEVICE_PROPERTIES = {
        DeviceTypes.ROUTER: {
            'icon': 'router.svg',
            'routing_protocol': 'OSPF',
            'forwarding_table': {}
        },
        DeviceTypes.SWITCH: {
            'icon': 'switch.svg',
            'ports': 24,
            'managed': True,
            'vlan_support': True
        },
        DeviceTypes.FIREWALL: {
            'icon': 'firewall.svg',
            'rules': [],
            'inspection_type': 'stateful'
        },
        DeviceTypes.SERVER: {
            'icon': 'server.svg',
            'services': [],
            'os': 'Linux'
        },
        DeviceTypes.WORKSTATION: {
            'icon': 'workstation.svg',
            'os': 'Windows'
        },
        DeviceTypes.CLOUD: {
            'icon': 'cloud.svg',
            'provider': 'AWS'
        },
        DeviceTypes.GENERIC: {
            'icon': 'device.svg'
        }
    }
    
    def __init__(self, name, device_type, properties=None, custom_icon_path=None, theme_manager=None):
        """Initialize a network device."""
        super().__init__()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Device properties
        self.id = str(uuid.uuid4())
        self.name = name
        self.device_type = device_type
        self.properties = self._init_properties(properties)
        
        # Path to custom icon if uploaded
        self.custom_icon_path = custom_icon_path
        self.logger.debug(f"Custom icon path set to: {self.custom_icon_path}")
        
        # Create signals object
        self.signals = DeviceSignals()
        
        # Set flags for interactivity - improved to ensure better clicking
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)  # Always selectable
        self.setFlag(QGraphicsItem.ItemIsMovable, True)     # Always movable initially
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)  # Track position changes
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)  # Better position tracking
        
        # Accept hover events to improve interactivity
        self.setAcceptHoverEvents(True)
        
        # Accept mouse buttons explicitly to ensure click is recognized
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        
        # Set z-value to be above connections and boundaries (layer 10)
        self.setZValue(10)
        
        # Size settings - increased for better visibility
        self.width = 80
        self.height = 80
        
        # Track selection state
        self.is_selected = False
        
        # Track connection points visibility
        self._show_connection_points = False

        # Flag to track if device is being dragged (new)
        self._is_dragging = False
        
        # List of connections attached to this device
        self.connections = []
        
        # Initialize component variables
        self.label = None
        self.image = None
        self.box = None
        self.rect_item = None
        self.text_item = None
        self.icon_item = None
        
        # Create child items
        self._create_visuals()
        
        # Set up parent-child relationships
        if self.text_item:
            self.text_item.setParentItem(self)
        if self.icon_item:
            self.icon_item.setParentItem(self)
        if self.rect_item:
            self.rect_item.setParentItem(self)
        
        # Make device children non-movable by default
        # This ensures that device components can't be moved separately
        for child in self.childItems():
            child.setFlag(QGraphicsItem.ItemIsSelectable, False)
            child.setFlag(QGraphicsItem.ItemIsMovable, False)
            child.setAcceptedMouseButtons(Qt.NoButton)
        
        # Initialize display properties dictionary
        self.display_properties = {}
        
        # Create property labels
        self.property_labels = {}
        
        # Font settings manager reference (will be set externally)
        self.font_settings_manager = None
        
        # Apply theme settings if theme manager is provided
        if theme_manager:
            self.update_theme(theme_manager.get_theme())
    
    def _init_properties(self, custom_properties=None):
        """Initialize the device properties based on type and custom values."""
        # Get default properties for this device type
        default_props = self.DEVICE_PROPERTIES.get(self.device_type, self.DEVICE_PROPERTIES[DeviceTypes.GENERIC]).copy()
        
        # Override with custom properties if provided
        if custom_properties:
            default_props.update(custom_properties)
        
        return default_props
    
    def _create_visuals(self):
        """Create the visual representation of the device."""
        # Create background rectangle
        self.rect_item = QGraphicsRectItem(0, 0, self.width, self.height, self)
        
        # Set the visual appearance based on device type - use a default gray if no color specified
        device_color = self.properties.get('color', QColor(150, 150, 150))  # Default gray if no color in properties
        
        # Create a visually distinct appearance with gradient or solid color
        brush = QBrush(device_color)
        self.rect_item.setBrush(brush)
        self.rect_item.setPen(QPen(Qt.black, 1))
        
        # Create a completely new text item that will always be visible
        self.text_item = QGraphicsTextItem()
        self.text_item.setPlainText(self.name)
        self.text_item.setParentItem(self)  # Make it a child of the device
        
        # IMPORTANT: Do not change this text color handling - it correctly sets white text in dark mode
        # and black text in light mode. Changing this will break theme handling.
        theme_is_dark = False
        if hasattr(self, 'theme_manager') and self.theme_manager:
            theme_is_dark = self.theme_manager.is_dark_theme()
        self.text_item.setDefaultTextColor(QColor(255, 255, 255) if theme_is_dark else QColor(0, 0, 0))
        
        # Make text bold but use smaller font size for better appearance
        font = QFont()
        font.setPointSize(9)  # Fixed smaller font size
        font.setBold(True)
        self.text_item.setFont(font)
        
        # Position text below the device
        text_width = self.text_item.boundingRect().width()
        text_x = (self.width - text_width) / 2
        self.text_item.setPos(text_x, self.height + 3)
        
        # Make sure it's visible and has high z-index
        self.text_item.setZValue(20)  # Very high to ensure it's above everything
        
        # Try to load the icon as a separate item
        self._try_load_icon()
    
    def _try_load_icon(self):
        """Try to load an icon for the device type or name from multiple possible locations."""
        # First check for custom icon path (highest priority)
        if self.custom_icon_path and os.path.exists(self.custom_icon_path):
            self.logger.info(f"ICON DEBUG: Loading custom icon from: {self.custom_icon_path}")
            if self._load_icon(self.custom_icon_path):
                return True
        
        # Log the current working directory to help with debugging path issues
        cwd = os.getcwd()
        self.logger.info(f"ICON DEBUG: Current working directory: {cwd}")
        
        # Get all possible icon folders
        icon_folders = self._get_icon_directories()
        self.logger.info(f"ICON DEBUG: Searching in icon folders: {icon_folders}")
        
        # Search for device type icons first with multiple case variations
        type_variations = [
            self.device_type.lower(),
            self.device_type,
            self.device_type.upper(),
            self.device_type.capitalize()
        ]
        
        # Try each type variation with each icon folder
        for folder in icon_folders:
            for type_var in type_variations:
                icon_path = os.path.join(folder, f"{type_var}.svg")
                self.logger.info(f"ICON DEBUG: Checking type icon at: {icon_path}")
                if os.path.exists(icon_path):
                    self.logger.info(f"ICON DEBUG: Found type icon at: {icon_path}")
                    if self._load_icon(icon_path):
                        return True

        # Try the icon name specified in properties
        icon_name = self.properties.get('icon', 'device.svg')
        if icon_name:
            for folder in icon_folders:
                icon_path = os.path.join(folder, icon_name)
                self.logger.info(f"ICON DEBUG: Checking property icon at: {icon_path}")
                if os.path.exists(icon_path):
                    self.logger.info(f"ICON DEBUG: Found property icon at: {icon_path}")
                    if self._load_icon(icon_path):
                        return True
        
        # Try device name-based icons
        if self._try_load_icon_by_name(self.name):
            return True
        
        # Try default "generic" icon as last resort
        for folder in icon_folders:
            default_icon = os.path.join(folder, "device.svg")
            if os.path.exists(default_icon):
                self.logger.info(f"ICON DEBUG: Using default icon: {default_icon}")
                if self._load_icon(default_icon):
                    return True
        
        self.logger.warning(f"ICON DEBUG: No icon found for device {self.name} of type {self.device_type}")
        return False

    def _get_icon_directories(self):
        """Get all possible icon directories, relative to different references."""
        import sys
        import os.path
        
        # Start with current directory and known relative paths
        icon_dirs = ["icons"]
        
        # Add application directory and its relative paths
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logger.info(f"ICON DEBUG: Application directory: {app_dir}")
        
        # Add all possible icon locations relative to the app directory
        icon_dirs.extend([
            os.path.join(app_dir, "icons"),
            os.path.join(app_dir, "resources", "icons"),
            os.path.join(app_dir, "resources", "icons", "svg"),  # Add SVG subdirectory
            os.path.join(app_dir, "src", "resources", "icons"),
            os.path.join(app_dir, "src", "resources", "icons", "svg"),  # Add SVG subdirectory
            os.path.join(app_dir, "src", "icons"),
            # For development environments, try a few levels up
            os.path.join(app_dir, "..", "resources", "icons"),
            os.path.join(app_dir, "..", "resources", "icons", "svg"),  # Add SVG subdirectory
            os.path.join(app_dir, "..", "icons"),
        ])
        
        # Filter to only directories that actually exist
        existing_dirs = [d for d in icon_dirs if os.path.isdir(d)]
        
        # If we found no existing directories, return the theoretical ones anyway
        return existing_dirs if existing_dirs else icon_dirs

    def _try_load_icon_by_name(self, name):
        """Try to load an icon that matches the device name."""
        # Normalize name (lowercase, remove spaces)
        normalized_name = name.lower().replace(" ", "_")
        
        # Check for different image formats, prioritize vector formats
        extensions = ['.svg', '.png', '.jpg', '.jpeg', '.webp']
        
        # Get all possible icon folders
        icon_folders = self._get_icon_directories()
        
        # Try each combination of folder, name variation, and extension
        name_variations = [
            normalized_name,
            name,
            name.lower(),
        ]
        
        for folder in icon_folders:
            for name_var in name_variations:
                for ext in extensions:
                    path = os.path.join(folder, f"{name_var}{ext}")
                    if os.path.exists(path):
                        self.logger.info(f"ICON DEBUG: Found matching icon at {path}")
                        if self._load_icon(path):
                            return True
        
        return False

    def _load_icon(self, path):
        """Load and set the icon from the given path, preserving quality."""
        self.logger.info(f"ICON DEBUG: Attempting to load icon from: {path}")
        
        # Check if we already have an icon item and remove it
        if hasattr(self, 'icon_item') and self.icon_item:
            self.logger.info("ICON DEBUG: Removing existing icon item before adding new one")
            if self.icon_item.scene():
                self.scene().removeItem(self.icon_item)
            self.icon_item = None
        
        # Check if this is an SVG file
        if path.lower().endswith('.svg'):
            return self._load_svg_icon(path)
        else:
            return self._load_pixmap_icon(path)
            
    def _load_svg_icon(self, path):
        """Load and set SVG icon with high quality rendering."""
        try:
            # Create SVG renderer to check if SVG is valid
            renderer = QSvgRenderer(path)
            if not renderer.isValid():
                self.logger.error(f"ICON DEBUG: Invalid SVG file: {path}")
                return False
                
            # Create a new SVG item
            svg_item = QGraphicsSvgItem(path)
            
            # Ensure SVG transparency is preserved
            svg_item.setCacheMode(QGraphicsItem.NoCache)  # Disable caching to ensure proper rendering
            
            # Calculate aspect ratio to maintain proportions
            default_size = renderer.defaultSize()
            if default_size.width() == 0 or default_size.height() == 0:
                self.logger.error(f"ICON DEBUG: Invalid SVG dimensions: {default_size.width()}x{default_size.height()}")
                return False
                
            aspect_ratio = default_size.width() / default_size.height()
            
            # Determine dimensions while maintaining aspect ratio
            if aspect_ratio >= 1:  # Wider than tall
                dest_width = self.width
                dest_height = int(self.width / aspect_ratio)
                dest_x = 0
                dest_y = (self.height - dest_height) // 2
            else:  # Taller than wide
                dest_height = self.height
                dest_width = int(self.height * aspect_ratio)
                dest_y = 0
                dest_x = (self.width - dest_width) // 2
            
            # Scale and position the SVG
            svg_item.setScale(dest_width / default_size.width())
            svg_item.setPos(dest_x, dest_y)
            svg_item.setZValue(1)  # Put icon above the background rectangle
            
            # Store as icon_item
            self.icon_item = svg_item
            self.icon_item.setParentItem(self)
            
            # Hide background rectangle when using SVG
            if hasattr(self, 'rect_item') and self.rect_item:
                self.rect_item.setVisible(False)
                # Completely clear the brush to avoid gray background
                self.rect_item.setBrush(QBrush(Qt.transparent))
                self.rect_item.setPen(QPen(Qt.transparent, 0))
            
            self.logger.info(f"ICON DEBUG: Successfully loaded SVG icon from {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"ICON DEBUG: Error loading SVG: {str(e)}")
            return False
            
    def _load_pixmap_icon(self, path):
        """Load and set a bitmap icon (PNG, JPG, etc.)."""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.logger.info(f"ICON DEBUG: Successfully loaded pixmap from {path}, size: {pixmap.width()}x{pixmap.height()}")
            
            # Show background rectangle for bitmap icons
            if hasattr(self, 'rect_item') and self.rect_item:
                self.rect_item.setVisible(True)
            
            # Create a new pixmap with the exact device dimensions
            square_pixmap = QPixmap(self.width, self.height)
            square_pixmap.fill(Qt.transparent)  # Make it transparent
            
            # Calculate aspect ratio to maintain proportions
            src_width = pixmap.width()
            src_height = pixmap.height()
            
            if src_width == 0 or src_height == 0:
                self.logger.error(f"ICON DEBUG: Invalid image dimensions in {path}: {src_width}x{src_height}")
                return False
                
            aspect_ratio = src_width / src_height
            
            # Determine target dimensions while maintaining aspect ratio
            if aspect_ratio >= 1:  # Wider than tall
                dest_width = self.width
                dest_height = int(self.width / aspect_ratio)
                dest_x = 0
                dest_y = (self.height - dest_height) // 2
            else:  # Taller than wide
                dest_height = self.height
                dest_width = int(self.height * aspect_ratio)
                dest_y = 0
                dest_x = (self.width - dest_width) // 2
            
            self.logger.info(f"ICON DEBUG: Scaled size: {dest_width}x{dest_height}, position: ({dest_x},{dest_y})")
            
            # Draw the image with high quality
            painter = QPainter(square_pixmap)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            
            # Draw the image centered with proper aspect ratio
            painter.drawPixmap(
                dest_x, dest_y, dest_width, dest_height,
                pixmap
            )
            painter.end()
            
            # Use the properly scaled pixmap
            self.icon_item = QGraphicsPixmapItem(square_pixmap, self)
            self.icon_item.setPos(0, 0)  # Position at top-left corner
            
            # Make sure icon is visible
            self.icon_item.setZValue(1)  # Put icon above the background rectangle
            
            self.logger.info(f"ICON DEBUG: Successfully created icon_item")
            return True
        else:
            self.logger.error(f"ICON DEBUG: Failed to load icon from: {path}, pixmap is null")
            return False
    
    def upload_custom_icon(self):
        """Open a file dialog to upload a custom high-resolution icon."""
        stack = traceback.extract_stack()
        self.logger.critical(f"ICON DEBUG: upload_custom_icon called from:")
        for frame in stack[:-1]:  # Skip the current frame
            self.logger.critical(f"ICON DEBUG: - {frame.filename}:{frame.lineno} in {frame.name}")
        
        self.logger.critical(f"ICON DEBUG: Opening file dialog for device: {self.name}, id: {id(self)}")
        
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            None, 
            "Select Icon (Vector graphics recommended)", 
            "", 
            "Images (*.svg *.png *.jpg *.jpeg *.bmp *.tiff *.webp)", 
            options=options
        )
        if file_path:
            self.logger.critical(f"ICON DEBUG: Custom icon selected: {file_path}")
            self.custom_icon_path = file_path
            # Remove existing icon if any
            if hasattr(self, 'icon_item') and self.icon_item:
                if self.icon_item.scene():
                    self.scene().removeItem(self.icon_item)
                self.icon_item = None
            # Reload the icon
            self._try_load_icon()
            self.update()  # Force redraw
            return True
        else:
            self.logger.critical(f"ICON DEBUG: Custom icon selection canceled for device: {self.name}")
            return False
    
    def boundingRect(self):
        """Return the bounding rectangle of the device."""
        # Include space for device and text label
        text_height = 25  # Default minimum height for text area
        
        # Calculate actual text height if text_item exists
        if hasattr(self, 'text_item') and self.text_item:
            text_rect = self.text_item.boundingRect()
            text_height = text_rect.height() + 8  # Add padding
            
            # If we have a text background, use its height instead
            if hasattr(self, 'text_background') and self.text_background:
                bg_rect = self.text_background.boundingRect()
                text_height = bg_rect.height() + 3  # Add small padding
        
        # Return rectangle that includes both device and text
        return QRectF(0, 0, self.width, self.height + text_height)
    
    def shape(self):
        """Return a more precise shape for hit detection."""
        path = QPainterPath()
        path.addRect(0, 0, self.width, self.height)  # Just the main rectangle, not the text
        return path
    
    def paint(self, painter, option, widget=None):
        """Paint the device with connection points if needed."""
        # First call the parent implementation for basic drawing
        super().paint(painter, option, widget)
        
        # For SVG icons, ensure the background is always transparent
        if hasattr(self, 'icon_item') and isinstance(self.icon_item, QGraphicsSvgItem):
            if hasattr(self, 'rect_item') and self.rect_item:
                # Make sure the background is transparent
                self.rect_item.setVisible(False)
                self.rect_item.setBrush(QBrush(Qt.transparent))
                self.rect_item.setPen(QPen(Qt.transparent, 0))
        
        # Ensure name is not empty
        if not self.name or self.name.strip() == "":
            # Generate a device number from a hash of the UUID
            hash_value = hashlib.md5(str(self.id).encode()).hexdigest()
            device_number = int(hash_value[:8], 16) % 10000  # Use modulo to keep it in a reasonable range
            self.name = f"Device {device_number}"
        
        # Ensure text_item exists and is visible
        if not hasattr(self, 'text_item') or not self.text_item:
            # Create text item
            self.text_item = QGraphicsTextItem()
            self.text_item.setParentItem(self)
            self.text_item.setPlainText(self.name)
            
            # IMPORTANT: Do not change this text color handling - it correctly sets white text in dark mode
            # and black text in light mode. Changing this will break theme handling.
            from utils.theme_manager import ThemeManager
            theme_mgr = ThemeManager()
            is_dark = theme_mgr.is_dark_theme()
            
            if is_dark:
                self.text_item.setDefaultTextColor(QColor(255, 255, 255))  # Pure white for dark mode
                self.logger.debug(f"Creating text item with WHITE text for device {self.name} in DARK mode")
            else:
                self.text_item.setDefaultTextColor(QColor(0, 0, 0))  # Pure black for light mode
                self.logger.debug(f"Creating text item with BLACK text for device {self.name} in LIGHT mode")
            
            # Make text bold but use smaller font size for better appearance
            font = QFont()
            font.setPointSize(9)  # Fixed smaller font size
            font.setBold(True)
            self.text_item.setFont(font)
            
            # Position text
            text_width = self.text_item.boundingRect().width()
            text_x = (self.width - text_width) / 2
            self.text_item.setPos(text_x, self.height + 3)
            
            # Set to highest z-index
            self.text_item.setZValue(20)
        else:
            # Ensure text is current
            if self.text_item.toPlainText() != self.name:
                self.text_item.setPlainText(self.name)
                
                # Update text position
                text_width = self.text_item.boundingRect().width()
                text_x = (self.width - text_width) / 2
                self.text_item.setPos(text_x, self.height + 3)
            
            # IMPORTANT: Do not change this text color handling - it correctly sets white text in dark mode
            # and black text in light mode. Changing this will break theme handling.
            from utils.theme_manager import ThemeManager
            theme_mgr = ThemeManager()
            is_dark = theme_mgr.is_dark_theme()
            
            # Only update color, DO NOT modify font properties here
            if is_dark and self.text_item.defaultTextColor() != QColor(255, 255, 255):
                self.text_item.setDefaultTextColor(QColor(255, 255, 255))  # Pure white for dark mode
                self.logger.debug(f"Updating text color to WHITE for device {self.name} in DARK mode")
            elif not is_dark and self.text_item.defaultTextColor() != QColor(0, 0, 0):
                self.text_item.setDefaultTextColor(QColor(0, 0, 0))  # Pure black for light mode
                self.logger.debug(f"Updating text color to BLACK for device {self.name} in LIGHT mode")
            
            # Ensure text is visible
            self.text_item.setVisible(True)
        
        # Skip drawing selection indicator and connection points when dragging to improve performance
        if self._is_dragging:
            return
            
        # Most painting is handled by child items, but we draw connection points here
        
        # Check if we need to show connection points
        showing_points = self._show_connection_points
        
        # Also show connection points when in connection mode
        if not showing_points and self.scene():
            from constants import Modes
            canvas = self._get_canvas()
            if canvas and hasattr(canvas, 'mode_manager'):
                mode_mgr = canvas.mode_manager
                if hasattr(mode_mgr, 'get_current_mode') and mode_mgr.current_mode == Modes.ADD_CONNECTION:
                    showing_points = True
                    
                    # Check if this device is being hovered in connection mode
                    if hasattr(mode_mgr, 'get_mode_instance'):
                        mode = mode_mgr.get_mode_instance()
                        is_hovered = hasattr(mode, 'hover_device') and mode.hover_device == self
        
        # Draw connection points if needed
        if showing_points:
            painter.save()
            
            # Use a lighter color if this device is being hovered in connection mode
            is_hovered = False
            canvas = self._get_canvas()
            if canvas and hasattr(canvas, 'mode_manager'):
                if hasattr(canvas.mode_manager, 'get_mode_instance'):
                    mode = canvas.mode_manager.get_mode_instance()
                    is_hovered = hasattr(mode, 'hover_device') and mode.hover_device == self
            
            if is_hovered:
                # Highlighted port appearance
                painter.setPen(QPen(QColor(65, 105, 225), 2))  # Royal blue
                painter.setBrush(QBrush(QColor(65, 105, 225, 100)))
                radius = 6
            else:
                # Normal port appearance
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.setBrush(QBrush(QColor(200, 200, 200, 150)))
                radius = 4
            
            # Draw each port
            for port in self.get_connection_ports():
                painter.drawEllipse(port, radius, radius)
                
            painter.restore()
    
    def _get_canvas(self):
        """Helper method to get the canvas that contains this device."""
        if not self.scene():
            return None
        
        # Try to get parent, which should be the canvas
        parent = self.scene().views()[0] if self.scene().views() else None
        return parent
    
    def get_connection_ports(self):
        """Get all available connection ports as local coordinates."""
        # Define 16 connection points around the device (doubled from the original 8)
        center_x = self.width / 2
        center_y = self.height / 2
        
        # First port is at the top (North), additional ports follow clockwise
        ports = [
            # Top quarter (North)
            QPointF(center_x * 0.5, 0),                 # NNW
            QPointF(center_x, 0),                       # N
            QPointF(center_x * 1.5, 0),                 # NNE
            
            # Right top quarter (East-North)
            QPointF(self.width, center_y * 0.25),       # ENE
            QPointF(self.width, center_y * 0.5),        # ENE
            QPointF(self.width, center_y * 0.75),       # E
            
            # Right bottom quarter (East-South)
            QPointF(self.width, center_y),              # E
            QPointF(self.width, center_y * 1.25),       # ESE
            QPointF(self.width, center_y * 1.5),        # ESE
            
            # Bottom quarter (South)
            QPointF(center_x * 1.5, self.height),       # SSE
            QPointF(center_x, self.height),             # S
            QPointF(center_x * 0.5, self.height),       # SSW
            
            # Left bottom quarter (West-South)
            QPointF(0, center_y * 1.5),                 # WSW
            QPointF(0, center_y * 1.25),                # WSW
            QPointF(0, center_y),                       # W
            
            # Left top quarter (West-North)
            QPointF(0, center_y * 0.75),                # WNW
            QPointF(0, center_y * 0.5),                 # WNW
            QPointF(0, center_y * 0.25)                 # WNW
        ]
        
        return ports
    
    def get_nearest_port(self, pos):
        """Get the nearest connection port to the given position."""
        # Create connection port positions in scene coordinates
        ports_local = self.get_connection_ports()
        ports_scene = [self.mapToScene(port) for port in ports_local]
        
        # Find nearest port
        nearest_port = None
        min_distance = float('inf')
        
        for port in ports_scene:
            dx = port.x() - pos.x()
            dy = port.y() - pos.y()
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_port = port
        
        # Debug nearest port
        if nearest_port:
            self.logger.debug(f"Nearest port for {self.name}: ({nearest_port.x()}, {nearest_port.y()})")
            
        return nearest_port
    
    def get_center_position(self):
        """Get the center position of the device in scene coordinates."""
        rect = self.boundingRect()
        return self.mapToScene(rect.center())
    
    def _distance(self, p1, p2):
        """Calculate distance between two points."""
        return ((p1.x() - p2.x()) ** 2 + (p2.y() - p2.y()) ** 2) ** 0.5
    
    def setProperty(self, name, value):
        """Set a custom property."""
        if name == 'show_connection_points':
            self._show_connection_points = value
            self.update()  # Force redraw
        elif name == 'device_type':
            # Update the device type
            old_type = self.device_type
            self.device_type = value
            
            # If the device type changed, update device properties based on the new type
            if old_type != value:
                # Get default properties for the new device type
                default_props = self.DEVICE_PROPERTIES.get(value, self.DEVICE_PROPERTIES[DeviceTypes.GENERIC]).copy()
                
                # Keep existing custom properties
                for key, val in self.properties.items():
                    if key not in default_props:
                        default_props[key] = val
                
                # Update properties
                self.properties = default_props
                
                # Reload the icon based on new device type
                self._try_load_icon()
                self.update()  # Force redraw
        else:
            # Store in properties dict
            self.properties[name] = value
            
            # For model changes, consider updating the icon
            if name == 'model' and value:
                self._try_load_icon()
                self.update()  # Force redraw
    
    def add_connection(self, connection):
        """Add a connection to this device's connections list."""
        if connection not in self.connections:
            self.connections.append(connection)
    
    def remove_connection(self, connection):
        """Remove a connection from this device's connections list."""
        if connection in self.connections:
            self.connections.remove(connection)
            
    def set_property(self, property_name, value):
        """Set a property and update the device accordingly."""
        # Log the property change
        self.logger.debug(f"Setting property {property_name} to {value} for device {self.name}")
        
        # Handle special properties
        if property_name == 'name':
            self.name = value
            self.update_name()
        elif property_name == 'z_value':
            try:
                z_value = float(value)
                self.setZValue(z_value)
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid z-value: {value}")
        elif property_name == 'device_type':
            # Use our specialized setProperty method for device_type
            self.setProperty('device_type', value)
        else:
            # Regular property
            self.setProperty(property_name, value)
            
            # Update property labels if displayed
            if property_name in self.display_properties and self.display_properties[property_name]:
                self.update_property_labels()
                
        # Force visual update
        self.update()
    
    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Item is about to move
            self.logger.debug(f"CHANGE DEBUG: Device '{self.name}' position changing")
            
            # Get the canvas
            if self.scene() and self.scene().views():
                canvas = self.scene().views()[0]
                
                # Check if we're in a group drag operation
                if (hasattr(canvas, 'group_selection_manager') and 
                    canvas.group_selection_manager and 
                    canvas.group_selection_manager.is_drag_active()):
                    
                    # If this item is being dragged as part of a group, let the manager handle it
                    drag_items = canvas.group_selection_manager.get_drag_items()
                    if self in drag_items:
                        self.logger.debug(f"HANDLED: Device '{self.name}' movement handled by GroupSelectionManager")
                        return value  # Allow the movement as it's managed by the GroupSelectionManager
                
                # Check if we're in select mode
                if hasattr(canvas, 'mode_manager'):
                    from constants import Modes
                    if canvas.mode_manager.current_mode == Modes.SELECT:
                        # In select mode, check if we're part of a multi-selection
                        selected_items = self.scene().selectedItems()
                        if len(selected_items) > 1 and self.isSelected():
                            # If we're part of a multi-selection, block individual movement
                            self.logger.debug(f"BLOCKED: Device '{self.name}' movement blocked as part of multi-selection")
                            return self.pos()
                
                # For single item movement, allow the change
                return value
            
        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # Item has moved
            self.logger.debug(f"CHANGE DEBUG: Device '{self.name}' position changed")
            
            # Only emit the moved signal - avoid property label updates during drag
            if hasattr(self.signals, 'moved'):
                self.signals.moved.emit(self)
            
            # Only update property labels if not dragging
            if not self._is_dragging:
                self.update_property_labels()
            
        elif change == QGraphicsItem.ItemSelectedChange:
            # Selection state is about to change - store state
            self.is_selected = bool(value)
            self.logger.debug(f"CHANGE DEBUG: Device '{self.name}' selection changing to {self.is_selected}")
            
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            # Selection state has changed - let the scene handle selection notifications
            self.logger.debug(f"CHANGE DEBUG: Device '{self.name}' selection state changed to {self.isSelected()}")
            
            # Let the scene handle selection change notification through scene().selectedItems()
            # This ensures all selection follows a single path through the canvas scene
            
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """Handle mouse press events, ensuring single-click selection."""
        # Save the cursor position relative to item position for smoother dragging
        self.drag_offset = event.pos()
        
        # Set the dragging flag to true when a left mouse button press occurs
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            # Store the initial position
            self.initial_pos = self.pos()
            
            # Critical: Save the exact drag offset based on mouse position
            self.logger.debug(f"Device {self.name}: Drag start at {event.pos().x()}, {event.pos().y()}")
        
        # Accept the event immediately to ensure it's processed
        event.accept()
        
        # Update selection state explicitly to ensure it's reflected
        if self.isSelected() != self.is_selected:
            self.is_selected = self.isSelected()
            self.logger.debug(f"Device {self.name}: Updated selection state to {self.is_selected}")
        
        # Call parent implementation to ensure default handling
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events, ensuring selection state is updated."""
        # Accept the event immediately
        event.accept()
        
        # Reset the dragging flag when mouse is released
        self._is_dragging = False
        
        # Clear the drag offset and initial position
        if hasattr(self, 'drag_offset'):
            self.drag_offset = None
        if hasattr(self, 'initial_pos'):
            self.initial_pos = None
        
        # Only emit selected signal if selection state actually changed
        if self.isSelected() != self.is_selected:
            self.is_selected = self.isSelected()
            self.logger.debug(f"Device {self.name}: Selection state changed on release to {self.is_selected}")
            
            # Emit selected signal to update properties panel
            if hasattr(self.signals, 'selected'):
                self.signals.selected.emit(self, self.is_selected)
        
        # After drag finishes, do a full update of the device and its connections
        self.update_connections()
        self.update_property_labels()
        self.update()
        
        # Call parent implementation
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click event to show properties panel."""
        self.logger.debug(f"DEVICE DEBUG: Double click event on device: {self.name}, id: {id(self)}")
        
        # Accept the event
        event.accept()
        
        # Ensure the item is selected without emitting selection signals
        if not self.isSelected():
            self.setSelected(True)
            self.is_selected = True
        
        # Emit the double-clicked signal to notify listeners
        if hasattr(self.signals, 'double_clicked'):
            self.signals.double_clicked.emit(self)
            self.logger.debug(f"DEVICE DEBUG: Emitted double_clicked signal for device: {self.name}")
        
        # Don't call parent implementation to prevent unwanted behaviors
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement during device dragging."""
        # Only handle left-button drag events
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return
        
        # Use the precise drag_offset to maintain position relative to mouse
        if hasattr(self, 'drag_offset') and self.drag_offset:
            # Calculate new position based on drag offset
            new_pos = self.mapToParent(event.pos() - self.drag_offset)
            
            # Set the position directly instead of moving with delta
            self.setPos(new_pos)
            
            # Minimize update frequency by using a smaller delta threshold
            current_pos = self.pos()
            if hasattr(self, '_last_drag_pos'):
                # Calculate delta movement
                delta_x = abs(current_pos.x() - self._last_drag_pos.x())
                delta_y = abs(current_pos.y() - self._last_drag_pos.y())
                
                # Only update connections if moved at least 3 pixels in either direction
                # This greatly reduces the number of updates
                if delta_x < 3 and delta_y < 3:
                    # Skip further processing for small movements
                    event.accept()
                    return
            
            # Store position for next comparison
            self._last_drag_pos = current_pos
            
            # Emit the move signal for things that need to track position
            if hasattr(self, 'signals') and hasattr(self.signals, 'moved'):
                self.signals.moved.emit(self)
            
            # Use the more efficient connection update method during dragging
            if hasattr(self, 'connections') and self.connections:
                # Use minimal updates for better performance during drag
                self._update_connections_minimal()
                
                # Force a minimal update of the device itself
                self.update()
        else:
            # Fall back to parent implementation if no drag offset
            super().mouseMoveEvent(event)
        
        event.accept()
    
    def update_connections(self):
        """Update all connections attached to this device with better error handling."""
        if not hasattr(self, 'connections') or not self.connections:
            return
        
        # Get the scene and prepare for batch updates
        scene = self.scene()
        if not scene:
            return
            
        # Start batch update
        scene.blockSignals(True)
        
        try:
            # Use a set to track updated connections to avoid duplicates
            updated_connections = set()
            
            for connection in list(self.connections):  # Use a copy to avoid modification issues during iteration
                try:
                    # Skip invalid connections or already updated ones
                    if connection is None or connection in updated_connections:
                        continue
                    
                    updated_connections.add(connection)
                    
                    # Use hasattr to safely check for the update_path method
                    if hasattr(connection, 'update_path'):
                        connection.update_path()
                    # For compatibility with older code that might use different method names
                    elif hasattr(connection, '_update_path'):
                        connection._update_path()
                    elif hasattr(connection, 'update'):
                        connection.update()
                    
                except Exception as e:
                    self.logger.error(f"Error updating connection: {str(e)}")
                    import traceback
                    self.logger.error(traceback.format_exc())
            
            # Update area slightly larger than the device to include connections
            # but only if we actually updated connections
            if updated_connections:
                update_rect = self.sceneBoundingRect().adjusted(-20, -20, 20, 20)
                scene.update(update_rect)
            
        finally:
            # End batch update
            scene.blockSignals(False)
    
    def _update_connections_minimal(self):
        """A minimal connection update that only updates paths without full redraws."""
        if not hasattr(self, 'connections') or not self.connections:
            return
        
        # Get the scene and prepare for batch updates
        scene = self.scene()
        if not scene:
            return
            
        # Skip updates if we're not visible
        if not self.isVisible():
            return
            
        # Don't send signals during drag updates
        scene.blockSignals(True)
        
        try:
            # Use a set to track updated connections to avoid duplicates
            updated_connections = set()
            
            for connection in list(self.connections):
                try:
                    # Skip invalid connections or already updated ones
                    if connection is None or connection in updated_connections:
                        continue
                    
                    updated_connections.add(connection)
                    
                    # Only update the path without triggering full redraws
                    if hasattr(connection, 'update_path'):
                        connection.update_path()
                    elif hasattr(connection, '_update_path'):
                        connection._update_path()
                    
                except Exception:
                    # Silently fail during dragging - full error handling will be done on release
                    pass
            
            # Update only the immediate area around the device
            # but only if we actually updated connections
            if updated_connections:
                update_rect = self.sceneBoundingRect().adjusted(-10, -10, 10, 10)
                scene.update(update_rect)
            
        finally:
            # End batch update
            scene.blockSignals(False)
    
    def delete(self):
        """Clean up resources before deletion."""
        # Store scene and bounding rect before removal for later update
        scene = self.scene()
        update_rect = self.sceneBoundingRect().adjusted(-10, -10, 10, 10)
        
        # Remove the text label if it exists
        if hasattr(self, 'text_item') and self.text_item:
            if self.text_item.scene():
                self.scene().removeItem(self.text_item)
            self.text_item = None
        
        # Remove the icon if it exists
        if hasattr(self, 'icon_item') and self.icon_item:
            if self.icon_item.scene():
                self.scene().removeItem(self.icon_item)
            self.icon_item = None
        
        # Disconnect all signals
        if hasattr(self, 'signals'):
            if hasattr(self.signals, 'deleted'):
                self.signals.deleted.emit(self)
        
        # Clean up connections
        connections_to_remove = list(self.connections)  # Create a copy to avoid modification during iteration
        for connection in connections_to_remove:
            if hasattr(connection, 'delete'):
                connection.delete()
        
        # Force update the scene area after deletion
        if scene:
            scene.update(update_rect)
            # Force update on all views
            for view in scene.views():
                view.viewport().update()

    def update_name(self):
        """Update device name display after name change."""
        # Ensure name is not empty
        if not self.name or self.name.strip() == "":
            # Generate a device number from a hash of the UUID instead of using the UUID directly
            hash_value = hashlib.md5(str(self.id).encode()).hexdigest()
            device_number = int(hash_value[:8], 16) % 10000  # Use modulo to keep it in a reasonable range
            self.name = f"Device {device_number}"
            
        # Create text_item if it doesn't exist
        if not hasattr(self, 'text_item') or not self.text_item:
            self.text_item = QGraphicsTextItem()
            self.text_item.setParentItem(self)
            
            # IMPORTANT: Do not change this text color handling - it correctly sets white text in dark mode
            # and black text in light mode. Changing this will break theme handling.
            from utils.theme_manager import ThemeManager
            theme_mgr = ThemeManager()
            is_dark = theme_mgr.is_dark_theme()
            
            if is_dark:
                self.text_item.setDefaultTextColor(QColor(255, 255, 255))  # Pure white for dark mode
                self.logger.debug(f"Setting WHITE text for device {self.name} in update_name (DARK mode)")
            else:
                self.text_item.setDefaultTextColor(QColor(0, 0, 0))  # Pure black for light mode
                self.logger.debug(f"Setting BLACK text for device {self.name} in update_name (LIGHT mode)")
            
            # Make text bold but use smaller font size for better appearance
            font = QFont()
            font.setPointSize(9)  # Fixed smaller font size
            font.setBold(True)
            self.text_item.setFont(font)
            
            # Set high z-index
            self.text_item.setZValue(20)
        
        # Update the text
        self.text_item.setPlainText(self.name)
        
        # IMPORTANT: Do not change this text color handling - it correctly sets white text in dark mode
        # and black text in light mode. Changing this will break theme handling.
        from utils.theme_manager import ThemeManager
        theme_mgr = ThemeManager()
        is_dark = theme_mgr.is_dark_theme()
        
        # Only update color if it needs to change - preserve all other properties
        if is_dark and self.text_item.defaultTextColor() != QColor(255, 255, 255):
            self.text_item.setDefaultTextColor(QColor(255, 255, 255))  # Pure white for dark mode
            self.logger.debug(f"Forcing WHITE text for device {self.name} in update_name (DARK mode)")
        elif not is_dark and self.text_item.defaultTextColor() != QColor(0, 0, 0):
            self.text_item.setDefaultTextColor(QColor(0, 0, 0))  # Pure black for light mode
            self.logger.debug(f"Forcing BLACK text for device {self.name} in update_name (LIGHT mode)")
        
        # Center the text under the device
        text_width = self.text_item.boundingRect().width()
        text_x = (self.width - text_width) / 2
        self.text_item.setPos(text_x, self.height + 3)
        
        # Force text to be visible
        self.text_item.setVisible(True)
        
        # Update property positions as name might have changed size
        self.update_property_labels()

    def update_color(self):
        """Update device visual appearance after color change."""
        if hasattr(self, 'color'):
            # Store the color in the properties dictionary
            if hasattr(self, 'properties'):
                self.properties['color'] = self.color
            
            # Update the visual appearance with the new color
            if hasattr(self, 'rect_item'):
                # Create a new brush with the updated color
                brush = QBrush(self.color)
                self.rect_item.setBrush(brush)
                
                # Use black border regardless of color for consistency
                self.rect_item.setPen(QPen(Qt.black, 1))
                
                # Force a redraw of the device
                if self.scene():
                    update_rect = self.sceneBoundingRect().adjusted(-5, -5, 5, 5)
                    self.scene().update(update_rect)
                
                self.update()  # This calls the Qt update method
                
                self.logger.debug(f"Device '{self.name}' color updated to {self.color.name()}")

    def center_pos(self):
        """Get the center position of the device in scene coordinates."""
        return self.get_center_position()

    def setFlag(self, flag, enabled):
        """Override setFlag to properly propagate flags to child items."""
        # Call the base implementation first
        super().setFlag(flag, enabled)
        
        # Only handle ItemIsMovable flag
        if flag == QGraphicsItem.ItemIsMovable:
            # Apply the same flag to all child items
            for child in self.childItems():
                # Use setFlag directly instead of setFlags
                child.setFlag(QGraphicsItem.ItemIsMovable, enabled)

    def update_property_labels(self):
        """Update the property labels."""
        # Get properties that should be displayed
        visible_props = [prop for prop, visible in self.display_properties.items() if visible]
        
        # Get display format preference
        show_property_names = self.properties.get('show_property_names', True)
        
        # Create or update labels for each visible property
        for prop_name in visible_props:
            # Skip if property no longer exists in properties
            if prop_name not in self.properties:
                # Remove the label if it exists
                if prop_name in self.property_labels:
                    if self.property_labels[prop_name] in self.childItems():
                        self.scene().removeItem(self.property_labels[prop_name])
                    del self.property_labels[prop_name]
                # Remove from display_properties as well
                if prop_name in self.display_properties:
                    del self.display_properties[prop_name]
                continue
                
            # Get the property value
            prop_value = self.properties.get(prop_name, "")
            
            # Convert to string to handle non-string values (numbers, booleans, etc.)
            str_prop_value = str(prop_value) if prop_value is not None else ""
            
            # Skip empty values
            if not prop_value or str_prop_value.strip() == "" or str_prop_value == "N/A":
                # If the property exists but is blank or N/A, remove the label if it exists
                if prop_name in self.property_labels:
                    if self.property_labels[prop_name] in self.childItems():
                        self.scene().removeItem(self.property_labels[prop_name])
                    del self.property_labels[prop_name]
                continue
                
            # Format the display value based on the property and display format preference
            display_value = ""
            if prop_name == 'ip_address':
                # For IP address, always show just the value
                display_value = str(prop_value)
            elif prop_name == 'model':
                # For model, always show just the value
                display_value = str(prop_value)
            elif prop_name in ['stig_compliance', 'vulnerability_scan', 'ato_status', 'accreditation_date']:
                # Format RMF properties with shorter display names
                if prop_name == 'stig_compliance':
                    display_value = f"STIG: {str(prop_value)}" if show_property_names else str(prop_value)
                elif prop_name == 'vulnerability_scan':
                    display_value = f"Vuln: {str(prop_value)}" if show_property_names else str(prop_value)
                elif prop_name == 'ato_status':
                    display_value = f"ATO: {str(prop_value)}" if show_property_names else str(prop_value)
                elif prop_name == 'accreditation_date':
                    display_value = f"Accred: {str(prop_value)}" if show_property_names else str(prop_value)
            else:
                # For other properties, show "name: value" or just "value" based on preference
                display_value = f"{prop_name}: {str(prop_value)}" if show_property_names else str(prop_value)
                
            # Skip if value is empty
            if not display_value.strip():
                continue
                
            # Create or update label
            if prop_name not in self.property_labels:
                self.property_labels[prop_name] = QGraphicsTextItem(self)
                self.property_labels[prop_name].setPlainText(display_value)
                
                # Apply font settings if available
                if self.font_settings_manager:
                    font = self.font_settings_manager.get_device_property_font()
                    self.property_labels[prop_name].setFont(font)
                    
                # Set appearance based on theme
                is_dark = getattr(self, 'current_theme', None) == 'dark'
                text_color = QColor(240, 240, 240) if is_dark else QColor(0, 0, 0)
                self.property_labels[prop_name].setDefaultTextColor(text_color)
            else:
                # Update existing label
                self.property_labels[prop_name].setPlainText(display_value)
                
        # Remove labels for properties that should not be displayed
        for prop_name in list(self.property_labels.keys()):
            if prop_name not in visible_props or not self.properties.get(prop_name, ""):
                if self.property_labels[prop_name] in self.childItems():
                    self.scene().removeItem(self.property_labels[prop_name])
                del self.property_labels[prop_name]
                
        # Position labels
        self._update_property_label_positions()
    
    def _show_property(self, property_name, show):
        """Show or hide a specific property."""
        if property_name in self.property_labels:
            label = self.property_labels[property_name]
            label.setVisible(show)
    
    def _update_property_label_positions(self):
        """Update the positions of all property labels."""
        # Start position below the device name
        y_offset = self.height + 25  # Start below device name
        
        # Get all visible labels
        visible_labels = []
        for prop_name, label in self.property_labels.items():
            if self.display_properties.get(prop_name, False) and label:
                visible_labels.append(label)
        
        # Position each label
        for label in visible_labels:
            # Center horizontally
            width = label.boundingRect().width()
            x = (self.width - width) / 2
            
            # Position vertically with a small gap
            label.setPos(x, y_offset)
            
            # Increment y_offset for the next label
            y_offset += label.boundingRect().height() + 3  # Small gap between labels

    def update_font_settings(self, font_settings_manager):
        """Update the device's font settings."""
        self.font_settings_manager = font_settings_manager
        
        # Update device name font
        if hasattr(self, 'text_item') and self.text_item:
            # Get the font but preserve our font size
            new_font = font_settings_manager.get_device_label_font()
            current_font = self.text_item.font()
            
            # Keep our size but take other properties from the font settings
            new_font.setPointSize(current_font.pointSize())
            
            # Apply the font
            self.text_item.setFont(new_font)
            
            # Recenter the name text
            text_width = self.text_item.boundingRect().width()
            text_x = (self.width - text_width) / 2
            self.text_item.setPos(text_x, self.height + 3)
        
        # Update property label fonts
        for label in self.property_labels.values():
            label.setFont(font_settings_manager.get_device_property_font())
        
        # Reposition property labels after font change
        self.update_property_labels()
    
    def update_theme(self, theme_name):
        """Update the device's appearance based on the theme."""
        if not theme_name:
            return
            
        self.current_theme = theme_name
        is_dark = theme_name == 'dark'
            
        # Update text color based on theme
        text_color = QColor(240, 240, 240) if is_dark else QColor(0, 0, 0)
        if self.text_item:
            self.text_item.setDefaultTextColor(text_color)
            
        # Update property label colors
        for prop_name, label in self.property_labels.items():
            if label and hasattr(label, 'setDefaultTextColor'):
                label.setDefaultTextColor(text_color)
                
        # Update property visibility
        for prop_name, visible in self.display_properties.items():
            if visible:
                self._show_property(prop_name, visible)
                
    def toggle_property_display(self, property_name, show):
        """Toggle the display of a property on the canvas."""
        # If property has been deleted, don't do anything
        if property_name not in self.properties:
            if property_name in self.display_properties:
                del self.display_properties[property_name]
            return
            
        # Record the display state
        self.display_properties[property_name] = show
        
        # Update the display
        self._show_property(property_name, show)
        
        # Update the property labels' positions
        self._update_property_label_positions()
    
    def get_property_display_state(self, property_name):
        """Get whether a property is being displayed."""
        # If property doesn't exist, it's not displayed
        if property_name not in self.properties:
            return False
            
        return self.display_properties.get(property_name, False)
    
    def update(self):
        """Update the device display."""
        super().update()
        self.update_property_labels()

    def update_label_positions(self):
        """Update positions of the name label and property labels."""
        # Update text label position to stay centered under the device
        if hasattr(self, 'text_item') and self.text_item:
            text_width = self.text_item.boundingRect().width()
            text_x = (self.width - text_width) / 2
            self.text_item.setPos(text_x, self.height + 3)
        
        # Make sure all other child items stay aligned with the device
        for child in self.childItems():
            # Skip text_item and property labels
            if child == self.text_item or child in self.property_labels.values():
                continue
            # All other children should be at 0,0 relative to device
            elif child.pos() != QPointF(0, 0):
                child.setPos(QPointF(0, 0))
        
        # Update property labels
        self.update_property_labels()