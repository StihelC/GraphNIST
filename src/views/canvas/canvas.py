from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QMenu, 
    QGraphicsItem, QApplication, QAction, QInputDialog, QGraphicsPixmapItem, QGraphicsTextItem,
    QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QEvent, QTimer, QRectF, QSettings
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QCursor, QTransform, QPixmap, QIcon

import logging
from constants import Modes

# Import our modularized components
from .graphics_manager import TemporaryGraphicsManager
from .selection_box import SelectionBox
from .mode_manager import CanvasModeManager
# Import ModeManager from controllers, not from local module
from controllers.mode_manager import ModeManager
# Import the new GroupSelectionManager
from controllers.selection import GroupSelectionManager

# Import modes
from .modes.select_mode import SelectMode
from .modes.add_device_mode import AddDeviceMode
from .modes.delete_mode import DeleteMode, DeleteSelectedMode
from .modes.add_boundary_mode import AddBoundaryMode
from .modes.add_connection_mode import AddConnectionMode

from models.device import Device
from models.connection.connection import Connection
from models.boundary.boundary import Boundary

class Canvas(QGraphicsView):
    """Canvas widget for displaying and interacting with network devices."""
    
    # Signals for different actions
    add_device_requested = pyqtSignal(QPointF)
    delete_device_requested = pyqtSignal(object)
    delete_item_requested = pyqtSignal(object)
    add_boundary_requested = pyqtSignal(object)  # QRectF
    add_connection_requested = pyqtSignal(object, object, object)  # source, target, connection_data
    delete_connection_requested = pyqtSignal(object)  # connection
    delete_boundary_requested = pyqtSignal(object)  # boundary
    delete_selected_requested = pyqtSignal()  # Signal for deleting all selected items
    statusMessage = pyqtSignal(str)  # Signal for status bar messages
    selection_changed = pyqtSignal(list)  # Signal for selection changes
    
    # Signal for editing a device
    device_edit_requested = pyqtSignal(object)  # device to edit
    
    # Signal for showing properties of a device
    device_properties_requested = pyqtSignal(object)  # device to show properties for
    
    # Signals for handling multiple devices
    multi_device_edit_requested = pyqtSignal(list)  # devices to edit
    multi_device_delete_requested = pyqtSignal(list)  # devices to delete
    
    # New signal for device alignment
    align_devices_requested = pyqtSignal(str, list)  # alignment_type, devices
    
    # New signal for connecting multiple devices
    connect_multiple_devices_requested = pyqtSignal(list)  # devices
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Create a scene to hold the items
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Lists to store items
        self.devices = []
        self.boundaries = []
        self.connections = []
        
        print("Canvas initialized with empty boundaries list:", self.boundaries)
        
        # Event bus reference (will be set externally)
        self.event_bus = None
        
        # Drag tracking variables
        self._drag_start_pos = None
        self._drag_item = None
        
        # Initialize group selection manager
        self.group_selection_manager = GroupSelectionManager(self)
        
        # Variables for canvas dragging (panning)
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        
        # Set rendering hints for better quality and performance
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Enable viewport optimizations
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        
        # Enable double buffering to reduce flicker
        self.setViewport(QWidget())  # Create a new viewport widget
        self.viewport().setAttribute(Qt.WA_NoSystemBackground)
        
        # Set scene rectangle to support large networks (10,000+ devices)
        self._scene.setSceneRect(-50000, -50000, 100000, 100000)
        
        # Setup appearance
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Grid settings
        self.show_grid = False
        self.grid_size = 20  # Grid size in pixels
        self.grid_color = QColor(200, 200, 200)  # Light gray grid
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Mouse tracking
        self.setMouseTracking(True)
        
        # Initialize helper components
        self.temp_graphics = TemporaryGraphicsManager(self._scene)
        
        # Setup mode manager
        self.mode_manager = CanvasModeManager(self)
        
        # Set up modes
        self._setup_modes()
        
        # Set initial mode
        self.set_mode(Modes.SELECT)
        
        # Initialize zoom settings with more conservative limits
        self.zoom_factor = 1.15  # Zoom in/out factor per step
        self.min_zoom = 0.05     # Minimum zoom level (5%)
        self.max_zoom = 2.5      # Maximum zoom level (250%)
        self.current_zoom = 1.0  # Current zoom level (100%)
        self.initial_transform = self.transform()  # Store initial transform
        
        # Store the initial viewport center point
        self.home_position = QPointF(0, 0)  # Default center of the view
        
        # Enable rubber band selection
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Enhanced rubber band selection setup with stronger styling
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        
        # Set a more visible rubber band style with high contrast colors
        self.setStyleSheet("""
            QGraphicsView {
                selection-background-color: rgba(30, 144, 255, 50);  /* DodgerBlue with transparency */
                selection-color: rgba(30, 144, 255, 255);            /* Solid DodgerBlue border */
                border: 1px solid #888;
            }
            QGraphicsView::rubberBand {
                border: 2px solid rgb(30, 144, 255);                 /* Thicker DodgerBlue border */
                background-color: rgba(30, 144, 255, 40);            /* Translucent fill */
            }
        """)
        
        # Variable to track rubber band selection state
        self._rubber_band_active = False
        self._rubber_band_origin = None  # Track the starting point of rubber band
        self._rubber_band_rect = None    # Track current rubber band rectangle
    
    def _setup_modes(self):
        """Set up the different interaction modes."""
        self.mode_manager = CanvasModeManager(self)
        
        # Register all available modes
        self.mode_manager.register_mode(Modes.SELECT, SelectMode(self))
        self.mode_manager.register_mode(Modes.ADD_DEVICE, AddDeviceMode(self))
        self.mode_manager.register_mode(Modes.DELETE, DeleteMode(self))
        self.mode_manager.register_mode(Modes.DELETE_SELECTED, DeleteSelectedMode(self))
        self.mode_manager.register_mode(Modes.ADD_BOUNDARY, AddBoundaryMode(self))
        self.mode_manager.register_mode(Modes.ADD_CONNECTION, AddConnectionMode(self))
        
        # Set initial mode to select
        self.mode_manager.set_mode(Modes.SELECT)
    
    def set_mode(self, mode):
        """Set the current interaction mode."""
        # Before switching modes, ensure proper cleanup
        self._cleanup_selection_state()
        return self.mode_manager.set_mode(mode)
    
    def _cleanup_selection_state(self):
        """Clean up any lingering selection state."""
        # Reset rubber band tracking
        self._rubber_band_active = False
        self._rubber_band_origin = None
        self._rubber_band_rect = None
        
        # Reset drag tracking
        self._drag_start_pos = None
        self._drag_item = None
        
        # Reset panning state
        self._is_panning = False
        
        # Clear any connecting in progress flag
        self._connecting_in_progress = False
    
    def get_item_at(self, pos):
        """Get item at the given view position."""
        scene_pos = self.mapToScene(pos)
        return self.scene().itemAt(scene_pos, self.transform())
    
    def _on_canvas_selection_changed(self, selected_items):
        """Internal handler for selection changes - emit once to avoid duplication."""
        # Just emit the signal once without any debug info
        self.selection_changed.emit(selected_items)
    
    def mousePressEvent(self, event):
        """Handle mouse press events with improved device dragging and rubber band selection."""
        try:
            # Get scene position and item at the click position
            scene_pos = self.mapToScene(event.pos())
            item = self.get_item_at(event.pos())
            
            # Handle multi-selection drag using the group selection manager
            if (event.button() == Qt.LeftButton and 
                self.mode_manager.current_mode == Modes.SELECT and
                len(self.scene().selectedItems()) > 1):
                
                # Try to start a group drag
                if self.group_selection_manager.start_drag(scene_pos, item):
                    # If successful, accept the event and return
                    event.accept()
                    return
            
            # Check if we're in the middle of a rubber band selection
            if self._rubber_band_active:
                # Let Qt handle the rubber band selection
                super().mousePressEvent(event)
                return
            
            # Handle middle button or shift+left click for panning
            if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier):
                self._is_panning = True
                self._pan_start_x = event.x()
                self._pan_start_y = event.y()
                self.setCursor(Qt.ClosedHandCursor)
                self.setDragMode(QGraphicsView.NoDrag)
                event.accept()
                return
                
            # If space is held for temp pan mode
            if hasattr(self, '_temp_pan_mode') and self._temp_pan_mode:
                self._is_panning = True
                self._pan_start_x = event.x()
                self._pan_start_y = event.y()
                self.setCursor(Qt.ClosedHandCursor)
                self.setDragMode(QGraphicsView.NoDrag)
                event.accept()
                return
            
            # Special case for boundary resize handles
            if (event.button() == Qt.LeftButton and 
                isinstance(item, Boundary) and
                item.isSelected()):
                
                # Convert scene position to boundary local coordinates
                item_pos = item.mapFromScene(scene_pos)
                
                # Check if click is on a resize handle
                if hasattr(item, '_handle_at_position') and item._handle_at_position(item_pos):
                    self.logger.debug(f"Canvas detected click on boundary resize handle")
                    
                    # Just let Qt's event system handle it naturally
                    super().mousePressEvent(event)
                    return
            
            # First, give the mode manager a chance to handle the event for non-select modes
            if self.mode_manager.current_mode != Modes.SELECT:
                handled = self.mode_manager.handle_event("mouse_press_event", event, scene_pos, item)
                if handled:
                    self.logger.debug(f"Mode {self.mode_manager.current_mode} handled the mouse press")
                    return
            
            # If we're in select mode, handle selection differently
            if event.button() == Qt.LeftButton and self.mode_manager.current_mode == Modes.SELECT:
                # Get the Ctrl key state
                is_ctrl_pressed = bool(event.modifiers() & Qt.ControlModifier)
                
                # First check if we clicked on a device or its child
                parent_device = None
                
                # Handle direct click on device
                if item in self.devices:
                    parent_device = item
                    self.logger.debug(f"Canvas detected click on device {item.name}")
                # Handle click on child component by redirecting to parent
                elif item and item.parentItem() and item.parentItem() in self.devices:
                    parent_device = item.parentItem()
                    self.logger.debug(f"Canvas detected click on device child, redirecting to {parent_device.name}")
                
                # Check if the item is a connection (don't need parent redirection)
                is_connection = isinstance(item, Connection)
                
                # Handle selection logic for devices and connections
                if parent_device or is_connection:
                    # Handle item is either a device or already a connection
                    selection_item = parent_device if parent_device else item
                    
                    # Save starting position for undo/redo tracking if it's a device
                    if parent_device:
                        self._drag_start_pos = parent_device.scenePos()
                        self._drag_item = parent_device
                        
                        # Make sure we're in NoDrag mode for device dragging
                        self.setDragMode(QGraphicsView.NoDrag)
                        
                        # Set proper flags for device and its children
                        for child in parent_device.childItems():
                            child.setFlag(QGraphicsItem.ItemIsMovable, False)
                            child.setFlag(QGraphicsItem.ItemIsSelectable, False)
                            child.setAcceptedMouseButtons(Qt.NoButton)
                        
                        parent_device.setFlag(QGraphicsItem.ItemIsMovable, True)
                        parent_device.setFlag(QGraphicsItem.ItemIsSelectable, True)
                    
                    # Handle selection based on Ctrl key
                    if is_ctrl_pressed:
                        # Toggle the item's selection state
                        new_state = not selection_item.isSelected()
                        selection_item.setSelected(new_state)
                        self.logger.debug(f"Ctrl+click on item: {'Selected' if new_state else 'Deselected'} {type(selection_item).__name__}")
                    else:
                        # Regular click: clear selection and select this item
                        self.scene().clearSelection()
                        selection_item.setSelected(True)
                        self.logger.debug(f"Regular click on item: Selected {type(selection_item).__name__}")
                    
                    # Emit selection changed signal immediately
                    selected_items = self.scene().selectedItems()
                    self.selection_changed.emit(selected_items)
                    
                    # Accept the event
                    event.accept()
                    
                    # Pass to parent for drag handling
                    super().mousePressEvent(event)
                    return
                
                # Let the select mode handle other interactions first
                handled = self.mode_manager.handle_event("mouse_press_event", event, scene_pos, item)
                if handled:
                    self.logger.debug("Select mode handled the mouse press")
                    return
                
                # If we get here, we're clicking in empty space for rubber band selection
                # Directly handle rubber band selection based on Ctrl key state
                if not item:
                    # Clear selection if not Ctrl+clicking
                    if not is_ctrl_pressed:
                        self.scene().clearSelection()
                        self.logger.debug("Canvas detected click in empty space, cleared selection")
                        self.selection_changed.emit([])
                    else:
                        self.logger.debug("Canvas detected Ctrl+click in empty space, preserving selection")
                    
                    # Always set rubber band mode before passing to parent
                    self.setDragMode(QGraphicsView.RubberBandDrag)
                    
                    # Mark rubber band as about to start
                    self._rubber_band_origin = scene_pos
                    
                    # Let Qt handle drawing the rubber band
                    super().mousePressEvent(event)
                    return
            
            # For any other case (including right click), let Qt handle it
            super().mousePressEvent(event)
                
        except Exception as e:
            self.logger.error(f"Error in mousePressEvent: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events with improved selection box tracking."""
        try:
            # Use the group selection manager for multi-selection drag
            if event.buttons() & Qt.LeftButton and self.group_selection_manager.is_drag_active():
                # Process the drag through the manager
                current_pos = self.mapToScene(event.pos())
                if self.group_selection_manager.process_drag(current_pos):
                    # If successfully processed, accept the event
                    event.accept()
                    return
            
            # Handle canvas panning
            if self._is_panning:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (event.x() - self._pan_start_x))
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (event.y() - self._pan_start_y))
                self._pan_start_x = event.x()
                self._pan_start_y = event.y()
                event.accept()
                return
                
            # Handle individual device dragging - disable property updates during drag
            if event.buttons() & Qt.LeftButton and self._drag_item:
                # Just call the parent implementation for smooth dragging
                # without triggering additional property updates
                super().mouseMoveEvent(event)
                return
            
            # Check if we're in rubber band selection mode
            if event.buttons() & Qt.LeftButton and self._rubber_band_origin is not None:
                # Let Qt handle the rubber band selection
                super().mouseMoveEvent(event)
                
                # Update our internal tracking if needed
                if not self._rubber_band_active:
                    self._rubber_band_active = True
                    self.logger.debug("Rubber band selection started during mouse move")
                
                # Get the current selection rectangle
                current_pos = self.mapToScene(event.pos())
                selection_rect = QRectF(self._rubber_band_origin, current_pos).normalized()
                
                # Process boundaries - only keep selected if completely contained
                selected_items = self.scene().selectedItems()
                for item in selected_items[:]:  # Create a copy of the list to avoid modification during iteration
                    if isinstance(item, Boundary):
                        # Get the boundary's bounding rectangle
                        boundary_rect = item.sceneBoundingRect()
                        
                        # Check if the boundary is completely contained within the selection rectangle
                        if not selection_rect.contains(boundary_rect):
                            # If not completely contained, deselect it
                            item.setSelected(False)
                            selected_items.remove(item)
                            # Also emit deselected signal to hide properties panel
                            if hasattr(item, 'signals') and hasattr(item.signals, 'selected'):
                                item.signals.selected.emit(item, False)
                
                return
            
            # Let the mode manager handle the event first
            if not self.mode_manager.handle_event("mouse_move_event", event):
                # If the mode didn't handle it, pass to default implementation
                super().mouseMoveEvent(event)
                
        except Exception as e:
            self.logger.error(f"Error in mouseMoveEvent: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def mouseReleaseEvent(self, event):
        """Override mouseReleaseEvent to optimize performance."""
        try:
            # Handle group drag end
            if self.group_selection_manager.is_drag_active():
                # End the group drag
                end_pos = self.mapToScene(event.pos())
                self.group_selection_manager.end_drag(end_pos)
                event.accept()
                
                # Emit selection changed signal exactly once
                selected_items = self.scene().selectedItems()
                self.selection_changed.emit(selected_items)
                return
                
            # Handle end of panning
            if self._is_panning:
                self._is_panning = False
                self.setCursor(Qt.ArrowCursor)
                self.setDragMode(QGraphicsView.RubberBandDrag)
                event.accept()
                return
                
            # Track device move for undo/redo
            if event.button() == Qt.LeftButton and self._drag_item and self._drag_start_pos:
                device = self._drag_item
                end_pos = device.scenePos()
                
                # Only record if position actually changed
                if self._drag_start_pos != end_pos:
                    # Record the move for undo/redo if applicable
                    if self.event_bus:
                        self.event_bus.emit('item.moved', 
                            item=device,
                            old_pos=self._drag_start_pos,
                            new_pos=end_pos
                        )
                    
                    # Clear rubber band mode after drag
                    self.setDragMode(QGraphicsView.NoDrag)
                    
                    # Reset rubber band tracking
                    self._rubber_band_active = False
                    self._rubber_band_origin = None
                    self._rubber_band_rect = None
                    
                # Clear drag tracking
                self._drag_item = None
                self._drag_start_pos = None
                
                # Emit selection changed signal exactly once
                selected_items = self.scene().selectedItems()
                self.selection_changed.emit(selected_items)
                
                # Let parent handle the release
                super().mouseReleaseEvent(event)
                
                # Force a viewport update to clear any artifacts
                self.viewport().update()
                return
                
            # Let the mode manager handle the event first
            if not self.mode_manager.handle_event("mouse_release_event", event):
                # If not handled, call parent implementation
                super().mouseReleaseEvent(event)
                
            # Force a viewport update to clear any artifacts
            self.viewport().update()
                
        except Exception as e:
            self.logger.error(f"Error in mouseReleaseEvent: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Always reset state in case of error
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            self._drag_item = None
            self._drag_start_pos = None
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events with keyboard shortcuts for common operations."""
        try:
            # Check if Shift is being held for temporary pan mode
            if event.key() == Qt.Key_Space:
                # Create a flag indicating we're in temporary pan mode from spacebar
                self._temp_pan_mode = True
                self.setDragMode(QGraphicsView.NoDrag)
                self.setCursor(Qt.OpenHandCursor)
                event.accept()
                return
                
            # First, let the mode manager try to handle the event
            if self.mode_manager.handle_event("key_press_event", event):
                event.accept()
                return
                
            # Global keyboard shortcuts
            
            # Delete key to delete selected items
            if event.key() == Qt.Key_Delete:
                if self.scene().selectedItems():
                    self.delete_selected_requested.emit()
                    event.accept()
                    return
            
            # Escape key to deselect all items
            if event.key() == Qt.Key_Escape:
                self.deselect_all()
                event.accept()
                return
            
            # Check for selection shortcuts (Ctrl+D for devices, Ctrl+C for connections)
            if event.modifiers() & Qt.ControlModifier:
                if event.key() == Qt.Key_D:
                    self.select_all_devices()
                    event.accept()
                    return
                elif event.key() == Qt.Key_C:
                    self.select_all_connections()
                    event.accept()
                    return
                elif event.key() == Qt.Key_A:
                    # Traditional Ctrl+A for select all of everything
                    self.scene().clearSelection()
                    for item in self.scene().items():
                        if item.isVisible() and (item in self.devices or 
                                               isinstance(item, Connection) or
                                               isinstance(item, Boundary)):
                            item.setSelected(True)
                    
                    self.selection_changed.emit(self.scene().selectedItems())
                    self.statusMessage.emit("Selected all items")
                    event.accept()
                    return
                
            # If no shortcuts were triggered, pass to parent
            super().keyPressEvent(event)
            
        except Exception as e:
            # Log errors during event handling
            self.logger.error(f"Error in keyPressEvent: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def keyReleaseEvent(self, event):
        """Handle key release events."""
        # If space bar is released, exit pan mode
        if event.key() == Qt.Key_Space and hasattr(self, '_temp_pan_mode'):
            self.setCursor(Qt.ArrowCursor)
            self._temp_pan_mode = False
            event.accept()
            return
            
        super().keyReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle wheel events for zooming."""
        try:
            # Get the position before zoom to maintain the point under cursor
            old_pos = self.mapToScene(event.pos())
            
            # Zoom in or out based on the wheel delta
            if event.angleDelta().y() > 0:
                # Zoom in
                if self.current_zoom < self.max_zoom:
                    self.scale(self.zoom_factor, self.zoom_factor)
                    self.current_zoom *= self.zoom_factor
                    self.statusMessage.emit(f"Zoom: {int(self.current_zoom * 100)}%")
            else:
                # Zoom out
                if self.current_zoom > self.min_zoom:
                    factor = 1.0 / self.zoom_factor
                    self.scale(factor, factor)
                    self.current_zoom *= factor
                    self.statusMessage.emit(f"Zoom: {int(self.current_zoom * 100)}%")
            
            # Get the position after zoom
            new_pos = self.mapToScene(event.pos())
            
            # Move the scene to keep the point under the cursor
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
            
            event.accept()
        except Exception as e:
            self.logger.error(f"Error in wheelEvent: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def scene(self):
        """Get the graphics scene."""
        return self._scene
    
    def zoom_in(self):
        """Zoom in on the canvas view."""
        if self.current_zoom < self.max_zoom:
            self.scale(self.zoom_factor, self.zoom_factor)
            self.current_zoom *= self.zoom_factor
            self.statusMessage.emit(f"Zoom: {int(self.current_zoom * 100)}%")
    
    def zoom_out(self):
        """Zoom out on the canvas view."""
        if self.current_zoom > self.min_zoom:
            factor = 1.0 / self.zoom_factor
            self.scale(factor, factor)
            self.current_zoom *= factor
            self.statusMessage.emit(f"Zoom: {int(self.current_zoom * 100)}%")
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.setTransform(self.initial_transform)
        self.current_zoom = 1.0
        self.statusMessage.emit("Zoom: 100%")
        
    def set_home_position(self, pos):
        """Set the home position for the canvas."""
        self.home_position = pos
    
    def reset_view(self):
        """Reset the view to the home position with 100% zoom."""
        self.reset_zoom()
        self.centerOn(self.home_position)
        self.statusMessage.emit("View reset to home position")
    
    def set_devices_draggable(self, draggable):
        """Make all devices draggable or not."""
        for device in self.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, draggable)
            device.setFlag(QGraphicsItem.ItemIsSelectable, True)  # Always keep selectable

    def diagnostics(self):
        """Print diagnostic information about current canvas state."""
        self.logger.debug("======= CANVAS DIAGNOSTICS =======")
        self.logger.debug(f"Devices: {len(self.devices)}")
        self.logger.debug(f"Connections: {len(self.connections)}")
        self.logger.debug(f"Boundaries: {len(self.boundaries)}")
        self.logger.debug(f"Drag mode: {self.dragMode()}")
        
        # Check current mode
        current_mode = None
        if hasattr(self, 'mode_manager') and hasattr(self.mode_manager, 'current_mode_instance'):
            current_mode = self.mode_manager.current_mode_instance.__class__.__name__ if self.mode_manager.current_mode_instance else None
        self.logger.debug(f"Current mode: {current_mode}")
        
        # Check selected items
        selected = self.scene().selectedItems()
        self.logger.debug(f"Selected items: {len(selected)}")
        
        # Device check - verify movable flag for all devices
        for i, device in enumerate(self.devices):
            is_movable = bool(device.flags() & QGraphicsItem.ItemIsMovable)
            is_selectable = bool(device.flags() & QGraphicsItem.ItemIsSelectable)
            self.logger.debug(f"Device {i} ({device.name}): movable={is_movable}, selectable={is_selectable}")
        
        self.logger.debug("================================")
    
    # Add methods to support alignment operations
    def align_selected_devices(self, alignment_type):
        """Align selected devices according to the specified type."""
        selected_devices = [item for item in self.scene().selectedItems() 
                          if item in self.devices]
        
        if len(selected_devices) < 2:
            self.statusMessage.emit("At least two devices must be selected for alignment")
            return
                    
        # Emit signal for controller to handle
        self.align_devices_requested.emit(alignment_type, selected_devices)
    
    def connect_all_selected_devices(self):
        """Connect all selected devices together."""
        # Get selected devices
        selected_devices = [i for i in self.scene().selectedItems() if i in self.devices]
        if len(selected_devices) > 1:
            self.logger.debug(f"Connecting {len(selected_devices)} selected devices")
            # Emit signal to connect devices
            self.connect_multiple_devices_requested.emit(selected_devices)
            
            # Schedule a return to SELECT mode after connection is created
            QTimer.singleShot(200, lambda: self.set_mode(Modes.SELECT))
            
            # Update status message
            self.statusMessage.emit(f"Connected {len(selected_devices)} devices")
        else:
            self.statusMessage.emit("Select at least two devices to connect")
    
    def select_all_devices(self):
        """Select all devices on the canvas."""
        # First deselect everything
        self.scene().clearSelection()
        
        # Select all devices
        for device in self.devices:
            device.setSelected(True)
        
        # Emit selection changed signal
        selected_items = self.scene().selectedItems()
        self.selection_changed.emit(selected_items)
        
        self.statusMessage.emit(f"Selected all devices ({len(self.devices)})")
    
    def select_all_connections(self):
        """Select all connections on the canvas."""
        # First deselect everything
        self.scene().clearSelection()
        
        # Select all connections
        for connection in self.connections:
            connection.setSelected(True)
        
        # Emit selection changed signal
        selected_items = self.scene().selectedItems()
        self.selection_changed.emit(selected_items)
        
        self.statusMessage.emit(f"Selected all connections ({len(self.connections)})")
    
    def deselect_all(self):
        """Deselect all items on the canvas."""
        self.scene().clearSelection()
        
        # Emit selection changed signal with empty list
        self.selection_changed.emit([])
        
        self.statusMessage.emit("Deselected all items")

    def contextMenuEvent(self, event):
        """Handle context menu events."""
        # Get the item under the cursor
        item = self.itemAt(event.pos())
        
        # Create context menu
        menu = QMenu(self)
        
        # Get current selection
        selected_items = self.scene().selectedItems()
        
        if len(selected_items) == 1:
            # Single item selected
            if isinstance(selected_items[0], Device):
                menu.addAction("Edit Device", lambda: self.device_edit_requested.emit(selected_items[0]))
                menu.addAction("Delete Device", lambda: self.delete_device_requested.emit(selected_items[0]))
                menu.addAction("Show Properties", lambda: self.device_properties_requested.emit(selected_items[0]))
            elif isinstance(selected_items[0], Connection):
                menu.addAction("Delete Connection", lambda: self.delete_connection_requested.emit(selected_items[0]))
            elif isinstance(selected_items[0], Boundary):
                menu.addAction("Delete Boundary", lambda: self.delete_boundary_requested.emit(selected_items[0]))
        elif len(selected_items) > 1:
            # Multiple items selected
            devices = [item for item in selected_items if isinstance(item, Device)]
            if devices:
                # Add device-specific actions
                device_menu = menu.addMenu("Device Actions")
                device_menu.addAction("Edit Selected Devices", lambda: self.multi_device_edit_requested.emit(devices))
                device_menu.addAction("Delete Selected Devices", lambda: self.multi_device_delete_requested.emit(devices))
                device_menu.addAction("Connect All Selected", lambda: self.connect_all_selected_devices())
                
                # Add alignment submenu
                align_menu = device_menu.addMenu("Align Devices")
                align_menu.addAction("Align Left", lambda: self.align_devices_requested.emit("left", devices))
                align_menu.addAction("Align Right", lambda: self.align_devices_requested.emit("right", devices))
                align_menu.addAction("Align Top", lambda: self.align_devices_requested.emit("top", devices))
                align_menu.addAction("Align Bottom", lambda: self.align_devices_requested.emit("bottom", devices))
                align_menu.addAction("Align Center Horizontal", lambda: self.align_devices_requested.emit("center_h", devices))
                align_menu.addAction("Align Center Vertical", lambda: self.align_devices_requested.emit("center_v", devices))
            
            # Add option to delete all selected items (devices, connections, boundaries)
            menu.addAction("Delete All Selected", lambda: self.delete_selected_requested.emit())
        else:
            # No items selected, just show canvas-related options
            menu.addAction("Reset View", self.reset_view)
            menu.addAction("Toggle Grid", self.toggle_grid)
        
        # Add viewport controls regardless of selection
        if menu.actions():
            menu.addSeparator()
        
        # Add zoom controls
        zoom_menu = menu.addMenu("Zoom")
        zoom_menu.addAction("Zoom In", self.zoom_in)
        zoom_menu.addAction("Zoom Out", self.zoom_out)
        zoom_menu.addAction("Reset Zoom", self.reset_zoom)
        
        # Only show the menu if it has actions
        if menu.actions():
            menu.exec_(event.globalPos())
    
    def edit_device(self, device):
        """Edit a single device."""
        self.logger.debug(f"CANVAS DEBUG: Editing device: {device.name}")
        # Emit signal to show device editor
        self.device_edit_requested.emit(device)
    
    def delete_device(self, device):
        """Delete a single device."""
        self.logger.debug(f"CANVAS DEBUG: Deleting device: {device.name}")
        # Emit signal to delete device
        self.delete_device_requested.emit(device)
    
    def show_properties(self, device):
        """Show properties for a device."""
        self.logger.debug(f"CANVAS DEBUG: Showing properties for device: {device.name}")
        # Emit signal to show properties
        self.device_properties_requested.emit(device)
    
    def edit_selected_devices(self, devices):
        """Edit multiple selected devices."""
        self.logger.debug(f"CANVAS DEBUG: Editing {len(devices)} selected devices")
        # Emit signal to show multi-device editor
        self.multi_device_edit_requested.emit(devices)
    
    def delete_selected_devices(self, devices):
        """Delete multiple selected devices."""
        self.logger.debug(f"CANVAS DEBUG: Deleting {len(devices)} selected devices")
        # Emit signal to delete multiple devices
        self.multi_device_delete_requested.emit(devices)
    
    def connect_selected_devices(self, devices):
        """Connect multiple selected devices."""
        self.logger.debug(f"CANVAS DEBUG: Connecting {len(devices)} selected devices")
        # Call the connect_all_selected_devices method which has the actual implementation
        self.connect_all_selected_devices()

    def drawBackground(self, painter, rect):
        """Draw the background with an optional grid."""
        # Call the parent implementation to fill the background
        super().drawBackground(painter, rect)
        
        # Draw grid if enabled
        if self.show_grid:
            # Save the painter state
            painter.save()
            
            # Create a thin pen for the grid
            grid_pen = QPen(self.grid_color)
            grid_pen.setWidth(1)
            painter.setPen(grid_pen)
            
            # Get the visible rectangle in scene coordinates
            visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
            
            # Calculate grid start and end positions
            start_x = int(visible_rect.left() / self.grid_size) * self.grid_size
            start_y = int(visible_rect.top() / self.grid_size) * self.grid_size
            end_x = int(visible_rect.right() / self.grid_size + 1) * self.grid_size
            end_y = int(visible_rect.bottom() / self.grid_size + 1) * self.grid_size
            
            # Draw vertical lines
            for x in range(start_x, end_x, self.grid_size):
                painter.drawLine(QPointF(x, visible_rect.top()), QPointF(x, visible_rect.bottom()))
            
            # Draw horizontal lines
            for y in range(start_y, end_y, self.grid_size):
                painter.drawLine(QPointF(visible_rect.left(), y), QPointF(visible_rect.right(), y))
            
            # Restore the painter state
            painter.restore()
            
    def toggle_grid(self):
        """Toggle the grid visibility."""
        self.show_grid = not self.show_grid
        self.viewport().update()
        
    def clear(self):
        """Clear the canvas by removing all items and resetting to an empty state."""
        # Clear all devices
        for device in list(self.devices):
            self.scene().removeItem(device)
        self.devices.clear()
        
        # Clear all connections
        for connection in list(self.connections):
            self.scene().removeItem(connection)
        self.connections.clear()
        
        # Clear all boundaries
        for boundary in list(self.boundaries):
            self.scene().removeItem(boundary)
        self.boundaries.clear()
        
        # Clear any temporary graphics
        self.temp_graphics.clear()
        
        # Reset view to default 
        self.reset_zoom()
        
        # Force a viewport update
        self.viewport().update()
        
        # Let interested parties know the canvas is now empty
        if self.event_bus:
            self.event_bus.emit('canvas_cleared')

    def paintEvent(self, event):
        """Override paintEvent for standard scene rendering."""
        # Use standard QGraphicsView rendering
        super().paintEvent(event)
        
        # Magnify mode removed for stability

    def rubberBandChanged(self, viewportRect, fromScenePoint, toScenePoint):
        """Handle rubber band selection changes - called by Qt when rubber band is drawn.
        
        Args:
            viewportRect: The rubber band rectangle in viewport coordinates
            fromScenePoint: Starting point in scene coordinates
            toScenePoint: Ending point in scene coordinates
        """
        # Call the parent implementation first to maintain default behavior
        super().rubberBandChanged(viewportRect, fromScenePoint, toScenePoint)
        
        # Check if rubber band is being activated or updated
        if not viewportRect.isEmpty():
            # Rubber band is active
            if not self._rubber_band_active:
                # Starting rubber band selection - save start point
                self._rubber_band_active = True
                self._rubber_band_origin = fromScenePoint
                self.logger.debug(f"Rubber band selection started at ({fromScenePoint.x():.1f}, {fromScenePoint.y():.1f})")
            
            # Update current rectangle
            self._rubber_band_rect = QRectF(fromScenePoint, toScenePoint).normalized()
            
            # Force GUI update to make rubber band more responsive
            QApplication.processEvents()
            
        else:
            # Rubber band has been released or is inactive
            if self._rubber_band_active:
                # Get the current selection
                selected_items = self.scene().selectedItems()
                
                # Get the selection rectangle
                selection_rect = QRectF(fromScenePoint, toScenePoint).normalized()
                
                # Process boundaries - only keep selected if completely contained
                for item in selected_items[:]:  # Create a copy of the list to avoid modification during iteration
                    if isinstance(item, Boundary):
                        # Get the boundary's bounding rectangle
                        boundary_rect = item.sceneBoundingRect()
                        
                        # Check if the boundary is completely contained within the selection rectangle
                        if not selection_rect.contains(boundary_rect):
                            # If not completely contained, deselect it
                            item.setSelected(False)
                            selected_items.remove(item)
                            # Also emit deselected signal to hide properties panel
                            if hasattr(item, 'signals') and hasattr(item.signals, 'selected'):
                                item.signals.selected.emit(item, False)
                
                count = len(selected_items)
                self.logger.debug(f"Rubber band selection completed with {count} selected items")
                
                # Optimize for multi-selection dragging
                if count > 0:
                    # Disable child selection on all selected devices
                    for item in selected_items:
                        if isinstance(item, Device):
                            # Ensure the device is properly configured for group dragging
                            item.setFlag(QGraphicsItem.ItemIsMovable, True)
                            item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                            
                            # Force all child items to be non-draggable and not independently selectable
                            for child in item.childItems():
                                child.setFlag(QGraphicsItem.ItemIsMovable, False)
                                child.setFlag(QGraphicsItem.ItemIsSelectable, False)
                                child.setAcceptedMouseButtons(Qt.NoButton)
                
                # Reset rubber band state
                self._rubber_band_active = False
                
                # Emit selection changed signal
                self.selection_changed.emit(selected_items)
            
            # Clear tracking variables
            self._rubber_band_origin = None
            self._rubber_band_rect = None

    def debugRubberBandSelection(self):
        """Log debugging information about rubber band selection state."""
        self.logger.debug("======= RUBBER BAND SELECTION DEBUG =======")
        self.logger.debug(f"Rubber band active: {self._rubber_band_active}")
        
        if self._rubber_band_origin:
            self.logger.debug(f"Origin: ({self._rubber_band_origin.x():.1f}, {self._rubber_band_origin.y():.1f})")
        else:
            self.logger.debug("Origin: None")
            
        if self._rubber_band_rect:
            self.logger.debug(f"Rectangle: ({self._rubber_band_rect.x():.1f}, {self._rubber_band_rect.y():.1f}, "
                             f"{self._rubber_band_rect.width():.1f}, {self._rubber_band_rect.height():.1f})")
        else:
            self.logger.debug("Rectangle: None")
            
        self.logger.debug(f"Current drag mode: {self.dragMode()}")
        self.logger.debug(f"Rubber band selection mode: {self.rubberBandSelectionMode()}")
        self.logger.debug(f"Selected items: {len(self.scene().selectedItems())}")
        self.logger.debug("===========================================")
