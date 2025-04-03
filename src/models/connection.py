from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsItem, QMenu, QAction, QGraphicsScene
from PyQt5.QtGui import QPainterPath
from PyQt5.QtCore import Qt, QPointF
import uuid
import logging

from models.connection_signals import ConnectionSignals
from models.connection_router import StraightLineRouter, OrthogonalRouter, CurvedRouter
from models.connection_renderer import ConnectionRenderer
from models.connection_label_manager import ConnectionLabelManager
from models.connection_interaction_handler import ConnectionInteractionHandler
from constants import ConnectionTypes

class Connection(QGraphicsPathItem):
    """Represents a connection between two devices in the topology."""
    
    # Routing styles
    STYLE_STRAIGHT = 0
    STYLE_ORTHOGONAL = 1
    STYLE_CURVED = 2
    
    def __init__(self, source_device, target_device, source_port=None, target_port=None):
        """Initialize a connection between two devices."""
        super().__init__()
        
        # Basic setup
        self.logger = logging.getLogger(__name__)
        self.id = str(uuid.uuid4())
        self.source_device = source_device
        self.target_device = target_device
        
        self.logger.info(f"Creating connection between {source_device.name} and {target_device.name}")
        
        # Add to devices' connections list
        source_device.add_connection(self)
        target_device.add_connection(self)
        
        # Port positions
        self.source_port = source_port or source_device.get_nearest_port(target_device.get_center_position())
        self.target_port = target_port or target_device.get_nearest_port(source_device.get_center_position())
        self._source_port = self.source_port
        self._target_port = self.target_port
        
        # Store raw device positions
        self.source_pos = source_device.scenePos()
        self.target_pos = target_device.scenePos()
        
        # Visual properties
        self.connection_type = "ethernet"  # Default type
        self.bandwidth = "1G"  # Default bandwidth
        self.latency = "0ms"  # Default latency
        
        # Add properties dictionary for storing connection properties
        self.properties = {
            "Bandwidth": self.bandwidth,
            "Latency": self.latency,
            "Label": "Link"
        }
        
        # Create signals object
        self.signals = ConnectionSignals()
        
        # Initialize components
        self._routing_style = self.STYLE_ORTHOGONAL  # Default to orthogonal
        self.router = self._create_router(self._routing_style)
        self.renderer = ConnectionRenderer(self)
        self.label_manager = ConnectionLabelManager(self)
        self.interaction_handler = ConnectionInteractionHandler(self)
        
        # State tracking
        self._was_selected = False
        
        # Configure selectable behavior
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setAcceptHoverEvents(True)
        
        # Set Z-value
        self.setZValue(-1)
        
        # Create the path
        self.update_path()
        
        # Setup listeners for device movement
        self._connect_to_device_changes()
    
    @property
    def routing_style(self):
        """Get the current routing style."""
        return self._routing_style
    
    @routing_style.setter
    def routing_style(self, style):
        """Set the routing style and update the router."""
        if style != self._routing_style:
            self._routing_style = style
            self.router = self._create_router(style)
            self.update_path()
    
    @property
    def label_text(self):
        """Get the label text."""
        return self.label_manager.label_text
    
    @label_text.setter
    def label_text(self, value):
        """Set the label text."""
        self.label_manager.label_text = value
        
    def _create_router(self, style):
        """Create the appropriate router for the given style."""
        if style == self.STYLE_STRAIGHT:
            return StraightLineRouter(self)
        elif style == self.STYLE_ORTHOGONAL:
            return OrthogonalRouter(self)
        elif style == self.STYLE_CURVED:
            return CurvedRouter(self)
        else:
            self.logger.warning(f"Unknown routing style: {style}, falling back to ORTHOGONAL")
            return OrthogonalRouter(self)
    
    def _connect_to_device_changes(self):
        """Connect to device signals to update when devices move."""
        if hasattr(self.source_device, 'signals') and hasattr(self.source_device.signals, 'moved'):
            self.source_device.signals.moved.connect(self._handle_device_moved)
        
        if hasattr(self.target_device, 'signals') and hasattr(self.target_device.signals, 'moved'):
            self.target_device.signals.moved.connect(self._handle_device_moved)
    
    def _handle_device_moved(self, device):
        """Handle device movement by updating the connection path."""
        # Update port positions based on device movement
        if device == self.source_device:
            self._source_port = self.source_device.get_nearest_port(self.target_device.get_center_position())
        elif device == self.target_device:
            self._target_port = self.target_device.get_nearest_port(self.source_device.get_center_position())
        
        # Update the path
        self.update_path()
    
    def update_path(self):
        """Update the connection path based on current device positions."""
        try:
            # Store current label text and selection state
            current_label_text = self.label_manager.label_text
            was_selected = self.isSelected()
            
            # Always recalculate port positions to ensure they're up to date
            self._source_port = self.source_device.get_nearest_port(self.target_device.get_center_position())
            self._target_port = self.target_device.get_nearest_port(self.source_device.get_center_position())
            
            # Capture old rect for update
            old_rect = self.sceneBoundingRect().adjusted(-100, -100, 100, 100)
            
            # Notify Qt that our geometry will change
            self.prepareGeometryChange()
            
            # Calculate the new path using the router
            new_path = self.router.calculate_path(self._source_port, self._target_port)
            
            # Set the new path
            self.setPath(new_path)
            
            # Restore selection state
            self.setSelected(was_selected)
            
            # Update the label position
            self.label_manager.update_position()
            
            # Force a full update of the entire affected area
            if self.scene():
                new_rect = self.sceneBoundingRect().adjusted(-100, -100, 100, 100)
                update_rect = old_rect.united(new_rect)
                
                # Invalidate scene caches and force redraw
                self.scene().invalidate(update_rect, QGraphicsScene.AllLayers)
                self.scene().update(update_rect)
                
                # Force update on all views
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
            self._was_selected = self.isSelected()
            self.renderer.apply_style()
        
        # Draw the connection path
        super().paint(painter, option, widget)
        
        # Only draw control points when selected and the router has control points
        if self.isSelected() and self.router.has_draggable_points():
            # Get control points from the router
            control_points = self.router.get_control_points()
            if control_points:
                # Delegate rendering to the renderer
                self.renderer.draw_control_points(painter, control_points)
    
    def shape(self):
        """Custom shape to include control points in hit testing."""
        # Get the base shape
        path = super().shape()
        
        # Let the interaction handler add control points to the shape
        return self.interaction_handler.update_shape(path, self.router)
    
    def mousePressEvent(self, event):
        """Handle mouse press, detecting control point selection."""
        # Let the interaction handler check for control point selection
        if self.interaction_handler.handle_mouse_press(event, self.router):
            event.accept()
            return
        
        # Fall back to standard handling
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle control point dragging with orthogonal constraints."""
        # Let the interaction handler manage control point dragging
        if self.interaction_handler.handle_mouse_move(event, self.router):
            event.accept()
            return
        
        # Fall back to standard handling
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Complete control point dragging."""
        # Let the interaction handler complete the drag operation
        if self.interaction_handler.handle_mouse_release(event):
            event.accept()
            return
        
        # Fall back to standard handling
        super().mouseReleaseEvent(event)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        # Let the interaction handler update hover state
        self.interaction_handler.handle_hover_enter(event, self.renderer)
        
        # Continue with standard handling
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        # Let the interaction handler update hover state
        self.interaction_handler.handle_hover_leave(event, self.renderer)
        
        # Continue with standard handling
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        """Handle item changes like selection."""
        if change == QGraphicsItem.ItemSelectedChange:
            # Emit signal when selection changes
            if value:
                self.signals.selected.emit(self)
            
            # Update appearance
            self.renderer.apply_style(is_selected=bool(value))
        
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Show context menu on right click."""
        menu = QMenu()
        
        # Style menu
        straight_action = menu.addAction("Straight")
        orthogonal_action = menu.addAction("Orthogonal")
        curved_action = menu.addAction("Curved")
        
        # Type menu
        menu.addSeparator()
        type_menu = menu.addMenu("Connection Type")
        
        ethernet_action = type_menu.addAction("Ethernet")
        serial_action = type_menu.addAction("Serial")
        fiber_action = type_menu.addAction("Fiber")
        
        # Delete option
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        
        # Show menu and handle selection
        action = menu.exec_(event.screenPos())
        
        if action == straight_action:
            self.routing_style = self.STYLE_STRAIGHT
        elif action == orthogonal_action:
            self.routing_style = self.STYLE_ORTHOGONAL
        elif action == curved_action:
            self.routing_style = self.STYLE_CURVED
        elif action == ethernet_action:
            self.connection_type = ConnectionTypes.ETHERNET
            self.renderer.set_style_for_type(ConnectionTypes.ETHERNET)
        elif action == serial_action:
            self.connection_type = ConnectionTypes.SERIAL
            self.renderer.set_style_for_type(ConnectionTypes.SERIAL)
        elif action == fiber_action:
            self.connection_type = ConnectionTypes.FIBER
            self.renderer.set_style_for_type(ConnectionTypes.FIBER)
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
        
        if self.target_device:
            if hasattr(self.target_device, 'remove_connection'):
                self.target_device.remove_connection(self)
        
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