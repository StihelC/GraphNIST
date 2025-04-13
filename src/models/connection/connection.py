from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsItem, QGraphicsEllipseItem, QMenu, QAction, QGraphicsScene
from PyQt5.QtGui import QPainterPath, QPen, QColor, QPainterPathStroker
from PyQt5.QtCore import Qt, QPointF, QRectF, QObject, pyqtSignal, QTimer
import uuid
import logging
from enum import Enum, auto

from .connection_signals import ConnectionSignals
from .connection_renderer import ConnectionRenderer
from .connection_label_manager import ConnectionLabelManager
from .connection_interaction_handler import ConnectionInteractionHandler
from constants import RoutingStyle as ConstRoutingStyle

class ConnectionTypes(Enum):
    """Types of connections between devices."""
    ETHERNET = auto()
    SERIAL = auto()
    FIBER = auto()
    WIRELESS = auto()
    BLUETOOTH = auto()
    ZIGBEE = auto()
    POWER = auto()
    USB = auto()
    CUSTOM = auto()
    POINT_TO_POINT = auto()
    VPN = auto()
    SDWAN = auto()
    
    @staticmethod
    def get_all_types():
        """Get a list of all connection types.
        
        Returns:
            list: List of all connection types
        """
        return list(ConnectionTypes)
    
    @staticmethod
    def get_type_names():
        """Get a list of all connection type names.
        
        Returns:
            list: List of connection type names as strings
        """
        return [t.name for t in ConnectionTypes]
    
    @staticmethod
    def from_string(type_name):
        """Convert a string to a ConnectionType.
        
        Args:
            type_name: String name of the connection type
            
        Returns:
            ConnectionType: Corresponding enum value, or None if not found
        """
        try:
            return ConnectionTypes[type_name.upper()]
        except KeyError:
            return ConnectionTypes.CUSTOM

class RoutingStyle(Enum):
    """Styles for routing connections between devices."""
    STRAIGHT = auto()
    ORTHOGONAL = auto()
    CURVED = auto()
    
    @staticmethod
    def get_all_styles():
        """Get a list of all routing styles.
        
        Returns:
            list: List of all routing styles
        """
        return list(RoutingStyle)
    
    @staticmethod
    def get_style_names():
        """Get a list of all routing style names.
        
        Returns:
            list: List of routing style names as strings
        """
        return [s.name for s in RoutingStyle]
    
    @staticmethod
    def from_string(style_name):
        """Convert a string to a RoutingStyle.
        
        Args:
            style_name: String name of the routing style
            
        Returns:
            RoutingStyle: Corresponding enum value, or ORTHOGONAL if not found
        """
        try:
            return RoutingStyle[style_name.upper()]
        except KeyError:
            return RoutingStyle.ORTHOGONAL
    
    @staticmethod
    def from_constant(style_constant):
        """Convert a constant to a RoutingStyle enum.
        
        Args:
            style_constant: Constant from constants.RoutingStyle
            
        Returns:
            RoutingStyle: Corresponding enum value
        """
        if style_constant == ConstRoutingStyle.STRAIGHT:
            return RoutingStyle.STRAIGHT
        elif style_constant == ConstRoutingStyle.CURVED:
            return RoutingStyle.CURVED
        else:
            return RoutingStyle.ORTHOGONAL

# Define router classes directly here to avoid import errors
class ConnectionRouter:
    """Base router class for calculating connection paths."""
    
    def __init__(self, connection):
        self.connection = connection
        
    def calculate_path(self):
        """Calculate and return a QPainterPath for the connection."""
        raise NotImplementedError("Subclasses must implement calculate_path()")
    
    def has_draggable_points(self):
        """Check if this router supports draggable control points.
        
        Returns:
            bool: True if this router has draggable control points
        """
        return False
    
    def get_control_points(self):
        """Get the list of control points for this router.
        
        Returns:
            list: List of QPointF control points or empty list
        """
        return []

class DirectRouter(ConnectionRouter):
    """Router that creates a direct line between source and target."""
    
    def calculate_path(self):
        """Calculate a straight line path."""
        # Get positions
        source_pos = self.connection.source_pos
        target_pos = self.connection.target_pos
        
        # Create path
        path = QPainterPath()
        path.moveTo(source_pos)
        path.lineTo(target_pos)
        
        return path

class OrthogonalRouter(ConnectionRouter):
    """Router that creates orthogonal (right-angled) paths."""
    
    def calculate_path(self):
        """Calculate an orthogonal path."""
        # Get positions
        source_pos = self.connection.source_pos
        target_pos = self.connection.target_pos
        
        # Determine mid point
        mid_x = (source_pos.x() + target_pos.x()) / 2
        
        # Create path
        path = QPainterPath()
        path.moveTo(source_pos)
        path.lineTo(QPointF(mid_x, source_pos.y()))
        path.lineTo(QPointF(mid_x, target_pos.y()))
        path.lineTo(target_pos)
        
        return path

class CurvedRouter(ConnectionRouter):
    """Router that creates curved paths."""
    
    def calculate_path(self):
        """Calculate a curved path."""
        # Get positions
        source_pos = self.connection.source_pos
        target_pos = self.connection.target_pos
        
        # Calculate control point
        control_x = (source_pos.x() + target_pos.x()) / 2
        control_y = (source_pos.y() + target_pos.y()) / 2
        
        # Offset control point perpendicularly
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        dist = (dx*dx + dy*dy) ** 0.5
        
        if dist > 0:
            offset = min(dist / 2, 50)  # Cap offset for very long connections
            control_x += -dy * 0.5
            control_y += dx * 0.5
        
        # Create path
        path = QPainterPath()
        path.moveTo(source_pos)
        path.quadTo(QPointF(control_x, control_y), target_pos)
        
        return path

class Connection(QGraphicsPathItem):
    """A connection between two devices in the topology."""

    # Backward compatibility constants
    STYLE_STRAIGHT = RoutingStyle.STRAIGHT
    STYLE_ORTHOGONAL = RoutingStyle.ORTHOGONAL
    STYLE_CURVED = RoutingStyle.CURVED

    def __init__(self, source_device, dest_device, connection_type=None, routing_style=None, props=None, theme_manager=None):
        """Initialize a new connection.
        
        Args:
            source_device: The source QGraphicsItem
            dest_device: The destination QGraphicsItem
            connection_type: The type of connection (from ConnectionTypes)
            routing_style: How the connection should be routed (from RoutingStyle)
            props: Dictionary of connection properties
            theme_manager: Optional ThemeManager instance for theme-aware rendering
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.id = str(uuid.uuid4())  # Unique identifier
        
        # Set devices
        self.source_device = source_device
        self.dest_device = dest_device
        
        # Set target_device as a direct attribute for compatibility with older code
        # (property getter might not be accessible during initialization)
        self.target_device = self.dest_device
        
        # Add to device connection lists
        if hasattr(source_device, 'connections'):
            source_device.connections.append(self)
        if hasattr(dest_device, 'connections'):
            dest_device.connections.append(self)
        
        # If connection_type not provided, default to Ethernet
        self.connection_type = connection_type or ConnectionTypes.ETHERNET
        
        # Initialize routing style property and router
        self._routing_style = None
        self.router = None
        
        # Port positions with initialization to avoid None values
        self._source_port = source_device.scenePos()
        self._target_port = dest_device.scenePos()
        
        # Update port positions based on device positions
        if hasattr(source_device, 'get_nearest_port') and hasattr(dest_device, 'get_center_position'):
            self._source_port = source_device.get_nearest_port(dest_device.get_center_position())
        
        if hasattr(dest_device, 'get_nearest_port') and hasattr(source_device, 'get_center_position'):
            self._target_port = dest_device.get_nearest_port(source_device.get_center_position())
        
        # Properties dictionary
        self.properties = props or {}
        
        # Ensure properties has keys for compatibility
        if 'Bandwidth' not in self.properties:
            self.properties['Bandwidth'] = "1G"
        if 'Latency' not in self.properties:
            self.properties['Latency'] = "0ms"
        
        # State tracking
        self.is_hover = False
        self.control_points = []
        self.show_control_points = False
        self._was_selected = False
        
        # Create renderer for managing appearance
        self.renderer = ConnectionRenderer(self)
        
        # Create label manager - ensure only one
        self.label_manager = ConnectionLabelManager(self)
        
        # Create signal handler
        self.signals = ConnectionSignals()
        
        # Register with theme manager if provided
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.register_theme_manager(self.theme_manager)
        
        # Make selectable and hoverable
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Set z-value to be behind devices but in front of boundaries (layer 5)
        self.setZValue(5)
        
        # Set initial style based on connection type
        self.renderer.set_style_for_type(self.connection_type)
        
        # Create the router based on routing style
        # Convert from constants.RoutingStyle to enum RoutingStyle if needed
        if isinstance(routing_style, str):
            routing_style = RoutingStyle.from_string(routing_style)
        elif routing_style is not None and not isinstance(routing_style, RoutingStyle):
            routing_style = RoutingStyle.from_constant(routing_style)
            
        self.routing_style = routing_style or RoutingStyle.ORTHOGONAL
        
        # Connect to device signals
        self._connect_signals()
        
        # Set tooltip
        self.update_tooltip()
        
        # Update the path initially
        self.update_path()
        
        # Add debounce timer for selection
        self.selection_timer = QTimer()
        self.selection_timer.setSingleShot(True)
        self.selection_timer.timeout.connect(self._on_selection_timer)
        self.pending_selection = None
    
    def register_theme_manager(self, theme_manager):
        """Register with a theme manager to receive theme updates.
        
        Args:
            theme_manager: ThemeManager instance
        """
        self.theme_manager = theme_manager
        self.renderer.register_theme_manager(theme_manager)
    
    @property
    def routing_style(self):
        """Get the current routing style."""
        return self._routing_style
    
    @routing_style.setter
    def routing_style(self, style):
        """Set the routing style and update the router."""
        # Only update if style actually changed
        if style != self._routing_style:
            # Store old selection state
            was_selected = self.isSelected()
            
            # Update routing style
            self._routing_style = style
            
            # Create the appropriate router
            self.router = self._create_router(style)
            
            # Update the path with the new router
            self.update_path()
    
    @property
    def source_pos(self):
        """Get the source position."""
        if self._source_port:
            return self._source_port
        return self.source_device.scenePos()
    
    @property
    def target_pos(self):
        """Get the target position."""
        if self._target_port:
            return self._target_port
        return self.dest_device.scenePos()
    
    @property
    def label_text(self):
        """Get the label text."""
        return self.label_manager.label_text
    
    @label_text.setter
    def label_text(self, value):
        """Set the label text."""
        if self.label_manager:
            self.label_manager.label_text = value
            
            # Also update properties dictionary for consistency
            if hasattr(self, 'properties') and isinstance(self.properties, dict):
                self.properties['label_text'] = value
        
    def _create_router(self, style):
        """Create the appropriate router for the given style."""
        if style == RoutingStyle.STRAIGHT:
            return DirectRouter(self)
        elif style == RoutingStyle.ORTHOGONAL:
            return OrthogonalRouter(self)
        elif style == RoutingStyle.CURVED:
            return CurvedRouter(self)
        else:
            self.logger.warning(f"Unknown routing style: {style}, falling back to ORTHOGONAL")
            return OrthogonalRouter(self)
    
    def _connect_signals(self):
        """Connect to relevant signals from devices."""
        try:
            if hasattr(self.source_device, 'positionChanged'):
                self.source_device.positionChanged.connect(self.update_path)
            
            if hasattr(self.dest_device, 'positionChanged'):
                self.dest_device.positionChanged.connect(self.update_path)
            
            # Connect to signals that may be used by custom devices
            if hasattr(self.source_device, 'signals') and hasattr(self.source_device.signals, 'moved'):
                self.source_device.signals.moved.connect(self._handle_device_moved)
            
            if hasattr(self.dest_device, 'signals') and hasattr(self.dest_device.signals, 'moved'):
                self.dest_device.signals.moved.connect(self._handle_device_moved)
        except Exception as e:
            self.logger.error(f"Failed to connect signals: {e}")
    
    def _handle_device_moved(self, device):
        """Handle device movement by updating the connection path."""
        # Update port positions based on device movement
        if device == self.source_device and hasattr(self.source_device, 'get_nearest_port'):
            self._source_port = self.source_device.get_nearest_port(self.dest_device.get_center_position())
        elif device == self.dest_device and hasattr(self.dest_device, 'get_nearest_port'):
            self._target_port = self.dest_device.get_nearest_port(self.source_device.get_center_position())
        
        # Update the path
        self.update_path()
    
    def update_path(self):
        """Update the connection path based on current device positions."""
        try:
            # Store selection state
            was_selected = self.isSelected()
            
            # Update port positions if needed
            if hasattr(self.source_device, 'get_nearest_port') and hasattr(self.dest_device, 'get_center_position'):
                self._source_port = self.source_device.get_nearest_port(self.dest_device.get_center_position())
            
            if hasattr(self.dest_device, 'get_nearest_port') and hasattr(self.source_device, 'get_center_position'):
                self._target_port = self.dest_device.get_nearest_port(self.source_device.get_center_position())
            
            # Capture old rect for update
            old_rect = self.sceneBoundingRect().adjusted(-100, -100, 100, 100)
            
            # Notify Qt that our geometry will change
            self.prepareGeometryChange()
            
            # Ensure we have a valid router
            if not self.router:
                self.logger.debug("Router was None, recreating with current style")
                self.router = self._create_router(self._routing_style)
            
            # Calculate the new path using the router
            if self.router:
                # Debug log to help diagnose straight line issue
                self.logger.debug(f"Updating path with {type(self.router).__name__}, style={self._routing_style.name}")
                
                # Clear any existing path before setting the new one
                try:
                    # First try with source_pos and target_pos arguments (connection_router.py style)
                    new_path = self.router.calculate_path(self.source_pos, self.target_pos)
                except TypeError:
                    # Fall back to no-argument version (connection.py style)
                    new_path = self.router.calculate_path()
                
                # Set the new path
                self.setPath(new_path)
                
                # Make sure style is properly applied
                self.renderer.apply_style(is_selected=was_selected)
            
            # Restore selection state
            self.setSelected(was_selected)
            
            # Update the label position if label manager exists
            if hasattr(self, 'label_manager') and self.label_manager:
                self.label_manager.update_position()
            
            # Force a full update of the entire affected area
            if self.scene():
                new_rect = self.sceneBoundingRect().adjusted(-100, -100, 100, 100)
                update_rect = old_rect.united(new_rect)
                
                # Invalidate scene caches and force redraw
                self.scene().invalidate(update_rect, QGraphicsScene.AllLayers)
                self.scene().update(update_rect)
            
            # Force update on all views
            if self.scene():
                for view in self.scene().views():
                    view.viewport().update()
        
        except Exception as e:
            self.logger.error(f"Error updating path: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def paint(self, painter, option, widget=None):
        """Draw the connection and control points when selected."""
        # Make sure our style is always correctly applied
        if self.isSelected() != self._was_selected:
            # Selection state changed
            self._was_selected = self.isSelected()
            self.logger.debug(f"Connection selection changed to {self.isSelected()}, style: {self.routing_style.name}")
            
            # Apply style for visual appearance (color, etc.), but don't change the path
            self.renderer.apply_style()
            
            # Log router type to help diagnose issues
            if self.router:
                self.logger.debug(f"Current router: {type(self.router).__name__}, has_draggable: {self.router.has_draggable_points()}")
        
        # Draw the connection path
        super().paint(painter, option, widget)
        
        # Draw control points when selected and available
        if self.isSelected() and self.router and self.router.has_draggable_points():
            control_points = self.router.get_control_points()
            if control_points:
                self.renderer.draw_control_points(painter, control_points)
    
    def shape(self):
        """Return the shape used for hit detection."""
        # Get the base shape from the parent class
        path = super().shape()
        
        # Make the hit area a bit larger to make it easier to select
        pen_width = max(self.renderer.line_width * 2, 10)  # Use at least 10 pixels for hit detection
        stroker = QPainterPathStroker()
        stroker.setWidth(pen_width)
        return stroker.createStroke(path)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Set selected to show properties panel
        self.setSelected(True)
        
        # Emit selected signal to show properties panel
        self.signals.selected.emit(self, True)  # Emit with both connection and selection state
        
        # Pass the event to the parent class
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        # Accept the event to ensure it's processed
        event.accept()
        super().mouseReleaseEvent(event)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        self.is_hover = True
        self.renderer.apply_style()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        self.is_hover = False
        self.renderer.apply_style()
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        """Handle item changes, including selection state."""
        if change == QGraphicsItem.ItemSelectedChange:
            # Stop any pending timer
            self.selection_timer.stop()
            
            # Store the new selection state
            self.pending_selection = value
            
            # Keep track of current style to ensure it doesn't change
            current_style = self._routing_style
            
            # Log selection change 
            self.logger.debug(f"Selection change: {value}, current style: {current_style.name if current_style else 'None'}")
            
            # Start the debounce timer
            self.selection_timer.start(100)  # 100ms debounce
            
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Show context menu on right click."""
        menu = QMenu()
        
        # Style menu
        style_menu = menu.addMenu("Routing Style")
        straight_action = style_menu.addAction("Straight")
        orthogonal_action = style_menu.addAction("Orthogonal")
        curved_action = style_menu.addAction("Curved")
        
        # Type menu
        menu.addSeparator()
        type_menu = menu.addMenu("Connection Type")
        
        ethernet_action = type_menu.addAction("Ethernet")
        serial_action = type_menu.addAction("Serial")
        fiber_action = type_menu.addAction("Fiber")
        wireless_action = type_menu.addAction("Wireless")
        bluetooth_action = type_menu.addAction("Bluetooth")
        
        # Delete option
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        
        # Show menu and handle selection
        action = menu.exec_(event.screenPos())
        
        if action == straight_action:
            self.routing_style = RoutingStyle.STRAIGHT
        elif action == orthogonal_action:
            self.routing_style = RoutingStyle.ORTHOGONAL
        elif action == curved_action:
            self.routing_style = RoutingStyle.CURVED
        elif action == ethernet_action:
            self.connection_type = ConnectionTypes.ETHERNET
            self.renderer.set_style_for_type(ConnectionTypes.ETHERNET)
        elif action == serial_action:
            self.connection_type = ConnectionTypes.SERIAL
            self.renderer.set_style_for_type(ConnectionTypes.SERIAL)
        elif action == fiber_action:
            self.connection_type = ConnectionTypes.FIBER
            self.renderer.set_style_for_type(ConnectionTypes.FIBER)
        elif action == wireless_action:
            self.connection_type = ConnectionTypes.WIRELESS
            self.renderer.set_style_for_type(ConnectionTypes.WIRELESS)
        elif action == bluetooth_action:
            self.connection_type = ConnectionTypes.BLUETOOTH
            self.renderer.set_style_for_type(ConnectionTypes.BLUETOOTH)
        elif action == delete_action:
            self.delete()
    
    def delete(self):
        """Remove this connection."""
        # Store scene and path for later update
        scene = self.scene()
        path_rect = self.boundingRect()
        scene_path = self.mapToScene(path_rect).boundingRect().adjusted(-20, -20, 20, 20)
        
        # If we have a label, include its area in the update region
        if hasattr(self.label_manager, 'label') and self.label_manager.label and self.label_manager.label.scene():
            label_rect = self.label_manager.label.sceneBoundingRect()
            scene_path = scene_path.united(label_rect.adjusted(-5, -5, 5, 5))
        
        # Disconnect from devices
        if self.source_device:
            if hasattr(self.source_device, 'remove_connection'):
                self.source_device.remove_connection(self)
            elif hasattr(self.source_device, 'connections'):
                if self in self.source_device.connections:
                    self.source_device.connections.remove(self)
        
        if self.dest_device:
            if hasattr(self.dest_device, 'remove_connection'):
                self.dest_device.remove_connection(self)
            elif hasattr(self.dest_device, 'connections'):
                if self in self.dest_device.connections:
                    self.dest_device.connections.remove(self)
        
        # Emit signal before removal
        self.signals.deleted.emit(self)
        
        # Remove from scene
        if scene:
            scene.removeItem(self)
            
            # Force update of the area where the connection was
            scene.update(scene_path)
            
            # Force update on all views
            for view in scene.views():
                view.viewport().update()
    
    def update_tooltip(self):
        """Update the tooltip with connection information."""
        # Get both device names
        source_name = getattr(self.source_device, 'name', 'Unknown')
        dest_name = getattr(self.dest_device, 'name', 'Unknown')
        
        # Connection type
        conn_type = getattr(self.connection_type, 'name', str(self.connection_type))
        
        # Build tooltip
        tooltip = f"Connection: {source_name} → {dest_name}\n"
        tooltip += f"Type: {conn_type}\n"
        
        # Add properties to tooltip
        if self.properties:
            tooltip += "Properties:\n"
            for k, v in self.properties.items():
                tooltip += f"  {k}: {v}\n"
                
        # Apply tooltip
        self.setToolTip(tooltip)

    def set_routing_style(self, style):
        """Set the routing style of the connection.
        
        This is a convenience method that redirects to the routing_style property setter.
        
        Args:
            style: The new routing style to use
        """
        was_selected = self.isSelected()
        self.routing_style = style
        
        # Make sure the appearance is updated
        self.renderer.apply_style(is_selected=was_selected)
        
        # Force update the scene
        if self.scene():
            update_rect = self.sceneBoundingRect().adjusted(-100, -100, 100, 100)
            self.scene().update(update_rect)
    
    @property
    def target_device(self):
        """Get the target device (alias for dest_device)."""
        return self.dest_device
    
    @target_device.setter
    def target_device(self, device):
        """Set both dest_device and target_device to the same value."""
        self.dest_device = device

    def _on_selection_timer(self):
        """Handle selection after debounce delay."""
        if self.pending_selection is not None:
            is_selected = self.pending_selection
            self.pending_selection = None
            if hasattr(self.signals, 'selected'):
                self.signals.selected.emit(self, is_selected) 