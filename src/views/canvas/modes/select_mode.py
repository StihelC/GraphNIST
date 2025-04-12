import logging
from PyQt5.QtCore import Qt, QEvent, QPointF, QPoint, QRectF, QTimer
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPen, QColor, QBrush

from views.canvas.modes.base_mode import CanvasMode
from models.boundary.boundary import Boundary
from models.device import Device
from models.connection.connection import Connection
from constants import Modes

class SelectMode(CanvasMode):
    """Mode for selecting and manipulating devices and boundaries."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
        self.mouse_press_pos = None
        self.click_item = None
        self.drag_threshold = 3  # Lower threshold for better response
        self.name = "Select Mode"  # Add explicit name for this mode
    
    def activate(self):
        """Enable dragging when select mode is active."""
        self.logger.debug("SelectMode: Activated")
        
        # Clear any selection boxes that might be lingering
        self.canvas.viewport().update()
        
        # Ensure we're in rubber band drag mode
        self.canvas.setDragMode(self.canvas.RubberBandDrag)
        
        # Make sure rubber band selection is visible and uses a larger selection area
        self.canvas.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        
        # Make all devices draggable and selectable
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, True)
            device.setFlag(QGraphicsItem.ItemIsSelectable, True)
            
            # Force all child items to be non-draggable and not independently selectable
            for child in device.childItems():
                child.setFlag(QGraphicsItem.ItemIsMovable, False)
                child.setFlag(QGraphicsItem.ItemIsSelectable, False)
                # This is critical - disable mouse events on child items
                child.setAcceptedMouseButtons(Qt.NoButton)
        
        # Make all connections selectable and focusable
        for connection in self.canvas.connections:
            connection.setFlag(QGraphicsItem.ItemIsSelectable, True)
            connection.setFlag(QGraphicsItem.ItemIsFocusable, True)
        
        # Make all boundaries selectable
        for boundary in self.canvas.boundaries:
            boundary.setFlag(QGraphicsItem.ItemIsSelectable, True)
            boundary.setFlag(QGraphicsItem.ItemIsMovable, True)
        
        # Reset state variables
        self.mouse_press_pos = None
        self.click_item = None
    
    def deactivate(self):
        """Disable dragging when leaving select mode."""
        self.logger.debug("SelectMode: Deactivated")
        
        # Disable dragging for all devices
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, False)
        
        # Make sure we clean up any pending drag state
        self.mouse_press_pos = None
        self.click_item = None
        
        # We intentionally keep connections selectable even in other modes
        # so they can be selected by clicking directly on them
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Handle mouse button press events."""
        self.mouse_press_pos = scene_pos
        
        # Get modifiers state early to be available throughout the method
        modifiers = event.modifiers()
        is_ctrl_pressed = bool(modifiers & Qt.ControlModifier)
        
        # DEBUG: Log mouse press events
        selected_items = self.canvas.scene().selectedItems()
        is_multi_selection = len(selected_items) > 1
        self.logger.debug(f"DEBUG-DRAG: SelectMode.handle_mouse_press - pos={scene_pos}, item={type(item).__name__ if item else 'None'}, multi_selection={is_multi_selection}, selected_count={len(selected_items)}")
        
        # For double clicks on boundaries, start editing the label
        if event.type() == QEvent.MouseButtonDblClick and isinstance(item, Boundary):
            if hasattr(item, 'label') and item.label:
                item.label.start_editing()
                return True
        
        # Handle left button clicks
        if event.button() == Qt.LeftButton:
            # Check if we're clicking on an item
            self.click_item = None
            
            # Find the actual item that can be selected (device, connection, boundary)
            original_item = item  # Keep track of the originally clicked item
            selectable_item = None
            
            # Logic for handling clicks on items or their children
            if item:
                # Check if it's a device, connection, or boundary
                from models.device import Device
                from models.connection.connection import Connection
                from models.boundary.boundary import Boundary
                
                if isinstance(item, (Device, Connection, Boundary)):
                    # Directly clicked on a selectable item
                    selectable_item = item
                    self.logger.debug(f"Direct click on {type(item).__name__}")
                elif item.parentItem():
                    # Clicked on a child item, check if parent is selectable
                    parent = item.parentItem()
                    if isinstance(parent, (Device, Connection, Boundary)):
                        selectable_item = parent
                        self.logger.debug(f"Click on child of {type(parent).__name__}")
            
            # If we found a selectable item
            if selectable_item:
                # Always store the clicked item to properly handle dragging
                self.click_item = selectable_item
                
                # Get current selection to determine multi-selection status
                selected_items = self.canvas.scene().selectedItems()
                is_multi_selection = len(selected_items) > 1
                
                # Log the state for debugging
                self.logger.debug(f"DEBUG-DRAG: SelectMode: Clicked item={type(selectable_item).__name__}, "
                                 f"ctrl_pressed={is_ctrl_pressed}, "
                                 f"currently_selected={selectable_item.isSelected()}, "
                                 f"multi_selection={is_multi_selection}")
                
                # Improved selection logic for multi-selection
                if is_ctrl_pressed:
                    # Ctrl+click: toggle selection state without affecting others
                    new_state = not selectable_item.isSelected()
                    selectable_item.setSelected(new_state)
                    self.logger.debug(f"Ctrl+click: {'Selected' if new_state else 'Deselected'} {type(selectable_item).__name__}")
                else:
                    # Check if we're clicking on an already selected item in a multi-selection
                    if is_multi_selection and selectable_item.isSelected():
                        # Click on already selected item in multi-selection - don't clear selection
                        # This is what enables dragging multiple items together
                        self.logger.debug(f"DEBUG-DRAG: Clicked on selected item in multi-selection, preserving selection of {len(selected_items)} items")
                    else:
                        # Regular click: clear others and select this item
                        self.canvas.scene().clearSelection()
                        selectable_item.setSelected(True)
                        self.logger.debug(f"Regular click: Selected {type(selectable_item).__name__}")
                
                # Emit selection changed signal immediately with no delay
                selected_items = self.canvas.scene().selectedItems()
                self.logger.debug(f"Emitting selection_changed with {len(selected_items)} items")
                if hasattr(self.canvas, 'selection_changed'):
                    self.canvas.selection_changed.emit(selected_items)
                
                # Make sure draggable items are set up correctly
                if isinstance(selectable_item, (Device, Boundary)):
                    # Ensure it's set as movable
                    selectable_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                    
                    # Critical fix: always accept the event to ensure proper handling
                    event.accept()
                    
                    # If we clicked on a child but are handling the parent,
                    # make sure the event gets to the parent device
                    if original_item != selectable_item:
                        selectable_item.mousePressEvent(event)
                
                # Important: return True to indicate we fully handled this event
                # This prevents conflicts with other handlers
                return True
            
            # If clicked in empty space, let the Canvas handle it
            # Canvas will handle rubber band selection and Ctrl+click in empty space
            return False
        
        # If right button, let context menu handle it
        elif event.button() == Qt.RightButton:
            return False
        
        # By default, return False to let Qt handle the event
        return False
    
    def mouse_move_event(self, event):
        """Handle mouse move events."""
        # Let the canvas handle all mouse movement for both individual and group drag
        return False
    
    def mouse_release_event(self, event, scene_pos=None, item=None):
        """Handle mouse release to complete selection box operation."""
        if event.button() == Qt.LeftButton:
            try:
                # First, ensure any group drag is properly completed
                if hasattr(self.canvas, 'group_selection_manager') and self.canvas.group_selection_manager:
                    if self.canvas.group_selection_manager.is_drag_active():
                        self.canvas.group_selection_manager.end_drag()
                
                # Ensure all devices have the correct flags
                for device in self.canvas.devices:
                    if device.scene():
                        device.setFlag(QGraphicsItem.ItemIsMovable, True)
                        device.setFlag(QGraphicsItem.ItemIsSelectable, True)
                        
                        # Child items should never be movable or selectable
                        for child in device.childItems():
                            child.setFlag(QGraphicsItem.ItemIsMovable, False)
                            child.setFlag(QGraphicsItem.ItemIsSelectable, False)
                
                # Make sure rubber band drag mode is restored
                self.canvas.setDragMode(QGraphicsView.RubberBandDrag)
                
                # Force the scene to update
                if self.canvas.scene():
                    self.canvas.scene().update()
                    
                # Emit the selection_changed signal
                if hasattr(self.canvas, 'selection_changed'):
                    selected_items = self.canvas.scene().selectedItems()
                    self.canvas.selection_changed.emit(selected_items)
                    
            except Exception as e:
                self.logger.error(f"Error in mouse release: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            
            # Reset state variables
            self.mouse_press_pos = None
            self.click_item = None
            
            return True
        
        return False
    
    def key_press_event(self, event):
        """Handle key press events for selection operations."""
        # Handle Ctrl+A for select all
        if event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            for item in self.canvas.scene().items():
                if item.isVisible() and (item in self.canvas.devices or item in self.canvas.boundaries):
                    item.setSelected(True)
            
            # Emit selection changed signal
            self.canvas.selection_changed.emit(self.canvas.scene().selectedItems())
            return True
            
        # Handle Escape key to clear selection
        if event.key() == Qt.Key_Escape:
            self.canvas.scene().clearSelection()
            # Emit selection changed signal
            self.canvas.selection_changed.emit([])
            return True
            
        return False
