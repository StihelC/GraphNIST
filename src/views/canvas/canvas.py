from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QMenu, 
    QGraphicsItem, QApplication, QAction, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QEvent, QTimer, QRectF, QSettings
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QCursor, QTransform

import logging
from constants import Modes

# Import our modularized components
from .graphics_manager import TemporaryGraphicsManager
from .selection_box import SelectionBox
from .mode_manager import CanvasModeManager

# Import modes
from .modes.select_mode import SelectMode
from .modes.add_device_mode import AddDeviceMode
from .modes.delete_mode import DeleteMode, DeleteSelectedMode
from .modes.add_boundary_mode import AddBoundaryMode
from .modes.add_connection_mode import AddConnectionMode
from .modes.magnify_mode import MagnifyMode

from models.device import Device
from models.connection import Connection
from models.boundary import Boundary

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
        
        # Event bus reference (will be set externally)
        self.event_bus = None
        
        # Drag tracking variables
        self._drag_start_pos = None
        self._drag_item = None
        
        # Variables for canvas dragging (panning)
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        
        # Set rendering hints for better quality
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
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
        
        # Enable wheel events
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Set viewport update mode to get smoother updates
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Enhanced rubber band selection setup with stronger styling
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Set a more visible rubber band style - use QSS that's guaranteed to work
        self.setStyleSheet("""
            QGraphicsView {
                selection-background-color: rgba(0, 100, 255, 50);
            }
        """)
            
        # Variable to track if rubber band selection is active
        self._rubber_band_active = False
    
    def _setup_modes(self):
        """Initialize all available interaction modes."""
        # Use a dictionary to create modes
        mode_classes = {
            Modes.SELECT: SelectMode,
            Modes.ADD_DEVICE: AddDeviceMode,
            Modes.DELETE: DeleteMode,
            Modes.DELETE_SELECTED: DeleteSelectedMode,
            Modes.ADD_BOUNDARY: AddBoundaryMode,
            Modes.ADD_CONNECTION: AddConnectionMode,
            Modes.MAGNIFY: MagnifyMode
        }
        
        # Create and register each mode with the manager
        for mode_id, mode_class in mode_classes.items():
            try:
                mode = mode_class(self)
                self.mode_manager.register_mode(mode_id, mode)
            except Exception as e:
                self.logger.error(f"Failed to initialize mode {mode_class.__name__}: {e}")
    
    def set_mode(self, mode):
        """Set the current interaction mode."""
        return self.mode_manager.set_mode(mode)
    
    def get_item_at(self, pos):
        """Get item at the given view position."""
        scene_pos = self.mapToScene(pos)
        return self.scene().itemAt(scene_pos, self.transform())
    
    def mousePressEvent(self, event):
        """Handle mouse press events with improved device dragging support."""
        try:
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
                
            # Get item at click position
            scene_pos = self.mapToScene(event.pos())
            item = self.get_item_at(event.pos())
            
            # Special handling for boundary resize in select mode
            if (event.button() == Qt.LeftButton and 
                self.mode_manager.current_mode == Modes.SELECT and
                isinstance(item, Boundary) and
                item.isSelected()):
                
                # Convert scene position to boundary local coordinates
                item_pos = item.mapFromScene(scene_pos)
                
                # Check if click is on a resize handle
                if hasattr(item, '_handle_at_position') and item._handle_at_position(item_pos):
                    self.logger.debug(f"Canvas detected click on boundary resize handle")
                    
                    # Simply fall through to default processing
                    # Let the boundary handle the resize in its own mousePressEvent
                    # No special handling needed here
                    
                    # Just let Qt's event system handle it naturally
                    return
            
            # Special handling for device dragging in select mode
            if (event.button() == Qt.LeftButton and 
                self.mode_manager.current_mode == Modes.SELECT):
                
                # First check if we need to redirect to a parent device
                parent_device = None
                
                # Handle direct click on device
                if item in self.devices:
                    parent_device = item
                # Handle click on child component by redirecting to parent
                elif item and item.parentItem() and item.parentItem() in self.devices:
                    parent_device = item.parentItem()
                    # Important: We need to redirect the event to the parent
                    item = parent_device
                
                if parent_device:
                    # Save starting position for undo/redo tracking
                    self._drag_start_pos = parent_device.scenePos()
                    self._drag_item = parent_device
                    
                    # Make sure we're in NoDrag mode for device dragging
                    self.setDragMode(QGraphicsView.NoDrag)
                    
                    # Ensure all children have proper flags
                    for child in parent_device.childItems():
                        child.setFlag(QGraphicsItem.ItemIsMovable, False)
                        child.setFlag(QGraphicsItem.ItemIsSelectable, False)
                        child.setAcceptedMouseButtons(Qt.NoButton)
                    
                    # Make sure the parent device is properly draggable
                    parent_device.setFlag(QGraphicsItem.ItemIsMovable, True)
                    parent_device.setFlag(QGraphicsItem.ItemIsSelectable, True)
                    
                    # Don't clear selection if the device is already selected or if Ctrl is pressed
                    # This is the key change to preserve multi-selection
                    if not parent_device.isSelected() and not (event.modifiers() & Qt.ControlModifier):
                        self.scene().clearSelection()
                    parent_device.setSelected(True)
                        
                    # Let Qt handle the drag
                    super().mousePressEvent(event)
                    return
            
            # Handle rubber band selection for empty space clicks
            if not item and event.button() == Qt.LeftButton and self.mode_manager.current_mode == Modes.SELECT:
                # Clear selection if not adding to selection
                if not (event.modifiers() & Qt.ControlModifier):
                    self.scene().clearSelection()
                
                # Set rubber band mode
                self.setDragMode(QGraphicsView.RubberBandDrag)
                
                # Let Qt handle the rubber band
                super().mousePressEvent(event)
                return
            
            # Let the mode manager handle the event
            handled = self.mode_manager.handle_event("mouse_press_event", event, scene_pos, item)
            
            # If not handled, pass to default implementation
            if not handled:
                super().mousePressEvent(event)
                
        except Exception as e:
            self.logger.error(f"Error in mousePressEvent: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        try:
            # Handle canvas panning
            if self._is_panning:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (event.x() - self._pan_start_x))
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (event.y() - self._pan_start_y))
                self._pan_start_x = event.x()
                self._pan_start_y = event.y()
                event.accept()
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
        """Handle mouse release events."""
        # End canvas panning
        if hasattr(self, '_is_panning') and self._is_panning:
            if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier):
                self._is_panning = False
                self.setCursor(Qt.ArrowCursor)
                self.setDragMode(QGraphicsView.RubberBandDrag)  # Restore rubber band mode
                event.accept()
                return
        
        # Reset rubber band selection tracking
        if hasattr(self, '_rubber_band_active') and self._rubber_band_active and event.button() == Qt.LeftButton:
            self._rubber_band_active = False
            self.logger.debug("Rubber band selection complete")
        
        # Handle drag finish
        if hasattr(self, '_drag_item') and self._drag_item:
            # Get the final position
            drag_end_pos = self._drag_item.scenePos()
            
            # If we have undo/redo support and the item actually moved
            if (hasattr(self, 'undo_redo_manager') and self.undo_redo_manager and 
                self._drag_start_pos != drag_end_pos):
                
                # Create a move command for the undo/redo system
                from controllers.commands import MoveItemCommand
                
                # Double-check that we have valid positions
                if self._drag_start_pos and drag_end_pos:
                    # Create and execute the command
                    cmd = MoveItemCommand(
                        self._drag_item,
                        self._drag_start_pos,
                        drag_end_pos
                    )
                    
                    # Reset drag tracking variables
                    self._drag_start_pos = None
                    self._drag_item = None
        
        # Let the active mode handle the event
        scene_pos = self.mapToScene(event.pos())
        item = self.get_item_at(event.pos())
        
        # Process the event with mode manager
        handled = self.mode_manager.handle_event("mouse_release_event", event, scene_pos, item)
        if not handled:
            super().mouseReleaseEvent(event)
        
        # After mouse release, always ensure we're in rubber band drag mode if in select mode
        if self.mode_manager.current_mode == Modes.SELECT:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Get final selection state after mouse release
        selected_items = self.scene().selectedItems()
        
        # Emit selection changed signal if there are selected items
        # This ensures properties panel updates after selection operations
        if selected_items:
            # Use small delay to ensure UI state is stable - reduces flicker
            QTimer.singleShot(50, lambda: self._emit_selection_changed(selected_items))
            
    def _emit_selection_changed(self, items):
        """Emit selection changed signal with items. Used for delayed emission."""
        if items:
            self.selection_changed.emit(items)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # If space bar is pressed, switch to pan mode temporarily
        if event.key() == Qt.Key_Space:
            self.setCursor(Qt.OpenHandCursor)
            self._temp_pan_mode = True
            event.accept()
            return
            
        # Handle delete key for selected items
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene().selectedItems()
            if selected_items:
                # Emit signal to delete all selected items
                self.delete_selected_requested.emit()
                event.accept()
                return
        
        # Connect selected devices with Ctrl+L
        if event.key() == Qt.Key_L and event.modifiers() & Qt.ControlModifier:
            selected_devices = [i for i in self.scene().selectedItems() if i in self.devices]
            if len(selected_devices) > 1:
                self.connect_all_selected_devices()
                self.statusMessage.emit(f"Connected {len(selected_devices)} devices")
                event.accept()
                return

        # If not handled above, pass to mode manager or parent
        if not self.mode_manager.handle_event("key_press_event", event):
            super().keyPressEvent(event)
            
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
        """Emit signal to connect all selected devices together."""
        # Static flag to prevent re-entry during event processing
        if hasattr(self, '_connecting_in_progress') and self._connecting_in_progress:
            self.logger.debug("Ignoring re-entrant call to connect_all_selected_devices")
            return
        
        try:
            # Set flag to prevent re-entry
            self._connecting_in_progress = True
            
            # Get selected devices
            selected_devices = [i for i in self.scene().selectedItems() if i in self.devices]
            if len(selected_devices) > 1:
                # Emit the signal only once with all needed information
                self.logger.debug(f"Emitting connect_multiple_devices_requested for {len(selected_devices)} devices")
                self.connect_multiple_devices_requested.emit(selected_devices)
        finally:
            # Always clean up the flag when done
            self._connecting_in_progress = False
    
    def device_selected(self, device, is_selected):
        """Handle device selection events."""
        self.logger.debug(f"SELECTION DEBUG: Device selected: {device.name}, is_selected={is_selected}")
        
        # If device is selected, make sure selection_changed signal is emitted
        if is_selected:
            # This helps with the properties panel visibility issue
            selected_items = self.scene().selectedItems()
            if selected_items:
                # Emit immediately to update properties panel
                self.selection_changed.emit(selected_items)
                
                # Also attempt to show the properties panel directly
                parent = self
                while parent:
                    if hasattr(parent, 'properties_dock'):
                        parent.properties_dock.setVisible(True)
                        break
                    parent = parent.parent()
                    
                # If parent window not found, try to find through application
                if not hasattr(parent, 'properties_dock'):
                    import sys
                    if 'PyQt5.QtWidgets' in sys.modules:
                        app = sys.modules['PyQt5.QtWidgets'].QApplication.instance()
                        if app:
                            for widget in app.topLevelWidgets():
                                if hasattr(widget, 'properties_dock'):
                                    widget.properties_dock.setVisible(True)
                                    break
    
    def contextMenuEvent(self, event):
        """Handle context menu event."""
        menu = QMenu(self)
        
        # Get scene position for potential device/connection creation
        scene_pos = self.mapToScene(event.pos())
        item = self.scene().itemAt(scene_pos, self.transform())
        
        # Check if any devices are selected
        selected_devices = [item for item in self.scene().selectedItems() if item in self.devices]
        
        # Different context menu based on what's under the cursor
        if not item:
            # Empty canvas area menu
            add_device_action = menu.addAction("Add Device...")
            add_device_action.triggered.connect(lambda: self.add_device_requested.emit(scene_pos))
            
            bulk_add_action = menu.addAction("Add Multiple Devices...")
            # Find the main window and call its bulk add method
            bulk_add_action.triggered.connect(self._request_bulk_add)
            
            # Add more empty canvas actions here...
            
        elif item in self.devices:
            # Device-specific menu options
            if len(selected_devices) > 1:
                # If multiple devices are selected, offer bulk edit and alignment
                bulk_edit_action = menu.addAction(f"Edit {len(selected_devices)} Devices...")
                bulk_edit_action.triggered.connect(self._request_bulk_edit)
                
                # Add connect selected devices option
                connect_action = menu.addAction(f"Connect {len(selected_devices)} Devices...")
                connect_action.triggered.connect(self.connect_all_selected_devices)
                
                # Add alignment submenu
                align_menu = menu.addMenu("Align Devices")
                
                # Basic alignment options
                basic_align = align_menu.addMenu("Basic Alignment")
                
                basic_actions = {
                    "Align Left": "left",
                    "Align Right": "right",
                    "Align Top": "top",
                    "Align Bottom": "bottom",
                    "Align Center Horizontally": "center_h",
                    "Align Center Vertically": "center_v",
                    "Distribute Horizontally": "distribute_h",
                    "Distribute Vertically": "distribute_v"
                }
                
                for action_text, alignment_type in basic_actions.items():
                    action = basic_align.addAction(action_text)
                    action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                           self.align_selected_devices(a_type))
                
                # Network layouts submenu
                network_layouts = align_menu.addMenu("Network Layouts")
                
                layout_actions = {
                    "Grid Arrangement": "grid",
                    "Circle Arrangement": "circle",
                    "Star Arrangement": "star",
                    "Bus Arrangement": "bus"
                }
                
                for action_text, alignment_type in layout_actions.items():
                    action = network_layouts.addAction(action_text)
                    action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                           self.align_selected_devices(a_type))
                
                # NIST RMF related layouts
                security_layouts = align_menu.addMenu("Security Architectures")
                
                security_actions = {
                    "DMZ Architecture": "dmz",
                    "Defense-in-Depth Layers": "defense_in_depth",
                    "Segmented Network": "segments",
                    "Zero Trust Architecture": "zero_trust",
                    "SCADA/ICS Zones": "ics_zones"
                }
                
                for action_text, alignment_type in security_actions.items():
                    action = security_layouts.addAction(action_text)
                    action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                           self.align_selected_devices(a_type))
        
        # Add bulk edit option if multiple devices are selected, regardless of what was clicked
        elif len(selected_devices) > 1:
            bulk_edit_action = menu.addAction(f"Edit {len(selected_devices)} Devices...")
            bulk_edit_action.triggered.connect(self._request_bulk_edit)
            
            # Add connect selected devices option
            connect_action = menu.addAction(f"Connect {len(selected_devices)} Devices...")
            connect_action.triggered.connect(self.connect_all_selected_devices)
            
            # Add alignment options
            align_menu = menu.addMenu("Align Devices")
            
            # Basic alignment options
            basic_align = align_menu.addMenu("Basic Alignment")
            
            basic_actions = {
                "Align Left": "left",
                "Align Right": "right",
                "Align Top": "top",
                "Align Bottom": "bottom",
                "Align Center Horizontally": "center_h",
                "Align Center Vertically": "center_v",
                "Distribute Horizontally": "distribute_h",
                "Distribute Vertically": "distribute_v"
            }
            
            for action_text, alignment_type in basic_actions.items():
                action = basic_align.addAction(action_text)
                action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                       self.align_selected_devices(a_type))
            
            # Network layouts submenu
            network_layouts = align_menu.addMenu("Network Layouts")
            
            layout_actions = {
                "Grid Arrangement": "grid",
                "Circle Arrangement": "circle",
                "Star Arrangement": "star",
                "Bus Arrangement": "bus"
            }
            
            for action_text, alignment_type in layout_actions.items():
                action = network_layouts.addAction(action_text)
                action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                       self.align_selected_devices(a_type))
            
            # NIST RMF related layouts
            security_layouts = align_menu.addMenu("Security Architectures")
            
            security_actions = {
                "DMZ Architecture": "dmz",
                "Defense-in-Depth Layers": "defense_in_depth",
                "Segmented Network": "segments",
                "Zero Trust Architecture": "zero_trust",
                "SCADA/ICS Zones": "ics_zones"
            }
            
            for action_text, alignment_type in security_actions.items():
                action = security_layouts.addAction(action_text)
                action.triggered.connect(lambda checked=False, a_type=alignment_type: 
                                       self.align_selected_devices(a_type))
            
        # Execute the menu
        menu.exec_(event.globalPos())

    def _request_bulk_add(self):
        """Request bulk device addition through main window."""
        # Find the main window through parent hierarchy
        main_window = self.window()
        if hasattr(main_window, '_on_bulk_add_device_requested'):
            main_window._on_bulk_add_device_requested()
    
    def _request_bulk_edit(self):
        """Request bulk property editing through main window."""
        # Find the main window through parent hierarchy
        main_window = self.window()
        if hasattr(main_window, '_on_edit_selected_devices'):
            main_window._on_edit_selected_devices()

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
        """Override paintEvent to handle magnify lens drawing.
        
        This allows us to draw the magnified content on top of the normal scene.
        """
        # First, let Qt handle normal rendering
        super().paintEvent(event)
        
        # Then, if we're in magnify mode, add the magnified content
        if self.mode_manager.current_mode == Modes.MAGNIFY:
            try:
                magnify_mode = self.mode_manager.get_mode(Modes.MAGNIFY)
                if magnify_mode and magnify_mode.active:
                    # Create a painter for the viewport
                    painter = QPainter(self.viewport())
                    magnify_mode.draw_magnified_content(painter)
                    painter.end()
            except Exception as e:
                self.logger.error(f"Error in magnify drawing: {str(e)}")
                import traceback
                traceback.print_exc()
