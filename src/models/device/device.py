from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QPainterPath, QPainter, QPixmap
import uuid
import logging
import os

from .device_signals import DeviceSignals
from .device_visuals import DeviceVisuals
from .device_interaction import DeviceInteraction
from .device_properties import DeviceProperties
from .device_label import DeviceLabel
from constants import DeviceTypes

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
        
        # Device identifiers
        self.id = str(uuid.uuid4())
        self.name = name
        self.device_type = device_type
        self.custom_icon_path = custom_icon_path
        
        # Initialize properties with defaults
        self.properties = self._init_properties(properties)
        
        # Set flags for interactivity - CRITICAL for dragging
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        
        # Ensure it accepts mouse events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        
        # Accept hover events to improve interactivity
        self.setAcceptHoverEvents(True)
        
        # Set z-value to be above connections and boundaries (layer 10)
        self.setZValue(10)
        
        # Theme manager reference (will be set by main window)
        self.theme_manager = theme_manager
        
        # Font settings manager reference (will be set externally)
        self.font_settings_manager = None
        
        # List of connections attached to this device
        self.connections = []
        
        # Create signals object
        self.signals = DeviceSignals()
        
        # Create component objects - create these before creating visual components
        self.visuals = DeviceVisuals(self)
        self.interaction = DeviceInteraction(self)
        self.props = DeviceProperties(self)
        self.label = DeviceLabel(self)
        
        # Create device label explicitly - don't rely on visuals to create it
        # to avoid duplicate label creation
        self.label.create_label()
    
    def _init_properties(self, custom_properties=None):
        """Initialize the device properties based on type and custom values."""
        # Get default properties for this device type
        default_props = self.DEVICE_PROPERTIES.get(self.device_type, self.DEVICE_PROPERTIES[DeviceTypes.GENERIC]).copy()
        
        # Override with custom properties if provided
        if custom_properties:
            default_props.update(custom_properties)
        
        return default_props
    
    def boundingRect(self):
        """Return the bounding rectangle of the device."""
        # Base on visuals bounding rect
        width = self.visuals.width
        height = self.visuals.height
        return QRectF(0, 0, width, height)
    
    def shape(self):
        """Return the shape of the device for collision detection."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    def paint(self, painter, option, widget=None):
        """Paint the device on the canvas."""
        # Call base class paint method for pixmap rendering
        super().paint(painter, option, widget)
        
        # Add connection points visualization if showing
        if hasattr(self.interaction, '_show_connection_points') and self.interaction._show_connection_points:
            # Get connection points
            points = self.interaction.get_connection_points()
            
            # Draw connection points
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.blue)
            
            # Draw each connection point
            for point in points:
                painter.drawEllipse(point, 4, 4)
                
            painter.restore()
    
    def itemChange(self, change, value):
        """Handle item state changes."""
        # Handle position changes
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Emit position changed signal
            if hasattr(self.signals, 'moved'):
                self.signals.moved.emit(self)
                
            # Update connections
            self.update_connections()
        
        # Handle selection changes
        elif change == QGraphicsItem.ItemSelectedChange:
            # We no longer need to adjust the rect_item since it was removed
            # Instead, we can adjust the z-value when selected to make it more visible
            is_selected = bool(value)
            if is_selected:
                # When selected, increase z-value to bring it to front
                self.setZValue(20)
            else:
                # When deselected, restore normal z-value
                self.setZValue(10)
        
        # Pass to parent class
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Save the cursor position relative to the item's top-left corner
        # This will keep the drag point consistent relative to where the user clicked
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.pos()
        
        # Let the interaction handler process the event
        self.interaction.mouse_press(event)
        
        # IMPORTANT: Always call the parent handler for left-button presses
        # This ensures QGraphicsPixmapItem's default drag behavior is preserved
        super().mousePressEvent(event)
        
        # Mark the event as accepted to ensure it's processed
        event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        # Let the interaction handler process the event
        self.interaction.mouse_move(event)
        
        # Apply the offset correction during drag to maintain relative position
        if event.buttons() & Qt.LeftButton and hasattr(self, '_drag_offset'):
            current_pos = self.mapToScene(event.pos())
            target_pos = current_pos - self.mapToScene(self._drag_offset) + self.mapToScene(QPointF(0, 0))
            self.setPos(target_pos)
            return
        
        # Always call parent handler to ensure movement works
        super().mouseMoveEvent(event)
        
        # Mark the event as accepted
        event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        # Let the interaction handler process the event
        self.interaction.mouse_release(event)
        
        # Clean up drag offset
        if event.button() == Qt.LeftButton and hasattr(self, '_drag_offset'):
            delattr(self, '_drag_offset')
        
        # Always call parent handler
        super().mouseReleaseEvent(event)
        
        # Mark the event as accepted
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click events."""
        # Let the interaction handler process the event
        self.interaction.mouse_double_click(event)
        
        # Call parent handler
        super().mouseDoubleClickEvent(event)
        
        # Mark the event as accepted
        event.accept()
    
    def add_connection(self, connection):
        """Add a connection to this device."""
        if connection not in self.connections:
            self.connections.append(connection)
    
    def remove_connection(self, connection):
        """Remove a connection from this device."""
        if connection in self.connections:
            self.connections.remove(connection)
    
    def update_connections(self):
        """Update all connections attached to this device."""
        # Just delegate to each connection to update itself
        for connection in self.connections:
            if connection.scene():  # Only update if still in scene
                connection.update_path()
    
    def get_center_position(self):
        """Get the center position of the device in scene coordinates."""
        rect = self.boundingRect()
        center = QPointF(rect.width() / 2, rect.height() / 2)
        return self.mapToScene(center)
    
    def delete(self):
        """Delete this device and its connections."""
        try:
            # Remove all connections first
            for connection in list(self.connections):
                # Avoid direct removal to prevent list modification during iteration
                if connection.scene():
                    connection.delete()
            
            # Clear the connections list
            self.connections.clear()
            
            # Remove any property labels
            for label in list(self.props.property_labels.values()):
                if label.scene():
                    label.scene().removeItem(label)
            
            # Clear property labels
            self.props.property_labels.clear()
            
            # Remove from scene if in a scene
            if self.scene():
                self.scene().removeItem(self)
                
            # Emit signal
            self.signals.deleted.emit(self)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting device: {str(e)}")
            return False
    
    def update_theme(self, theme_name=None):
        """Update device appearance for theme changes."""
        # Update each component
        if hasattr(self, 'visuals'):
            self.visuals.update_theme(theme_name)
        if hasattr(self, 'label'):
            self.label.update_theme(theme_name)
        if hasattr(self, 'props'):
            self.props.update_theme(theme_name)
        
        # Force update
        self.update()
    
    def update_font_settings(self, font_settings_manager):
        """Update device font settings."""
        self.font_settings_manager = font_settings_manager
        
        # Update device name font
        if hasattr(self, 'label'):
            font_size = font_settings_manager.get_font_size('device_name')
            font_bold = font_settings_manager.get_font_bold('device_name')
            font_italic = font_settings_manager.get_font_italic('device_name')
            
            self.label.update_font(font_size, font_bold, font_italic)
            
        # Update property labels font
        if hasattr(self, 'props'):
            self.props.update_font(font_settings_manager)
            
        # Force update
        self.update()
    
    def get_connection_ports(self):
        """Get connection ports in scene coordinates."""
        if hasattr(self, 'interaction'):
            # Get local points
            local_points = self.interaction.get_connection_points()
            
            # Convert to scene coordinates
            return [self.mapToScene(point) for point in local_points]
        
        # Fallback to center point
        return [self.get_center_position()]
    
    def get_nearest_port(self, scene_pos):
        """Get the nearest connection port to the given scene position."""
        if hasattr(self, 'interaction'):
            return self.interaction.get_nearest_port(scene_pos)
        
        # Fallback to center position
        return self.get_center_position()
        
    def set_property(self, name, value):
        """Set a device property."""
        if hasattr(self, 'props'):
            return self.props.set_property(name, value)
        return False
        
    def get_property(self, name, default=None):
        """Get a device property."""
        if hasattr(self, 'props'):
            return self.props.get_property(name, default)
        
        # Special case for name
        if name == 'name':
            return self.name
            
        # Get from properties dict
        if hasattr(self, 'properties'):
            return self.properties.get(name, default)
            
        return default
        
    def toggle_property_display(self, property_name, show):
        """Toggle the display of a property on the device."""
        if hasattr(self, 'props'):
            return self.props.toggle_property_display(property_name, show)
        return False
        
    def get_property_display_state(self, property_name):
        """Check if a property is currently displayed."""
        if hasattr(self, 'props'):
            return self.props.get_property_display_state(property_name)
        return False
        
    def update_property_labels(self):
        """Update all property labels - called when property display settings change."""
        if hasattr(self, 'props'):
            self.props.update_all_property_labels()
            
        # Force update
        self.update() 