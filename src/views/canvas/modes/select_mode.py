import logging
from PyQt5.QtCore import Qt, QEvent, QPointF
from PyQt5.QtWidgets import QGraphicsItem

from views.canvas.modes.base_mode import CanvasMode
from models.boundary import Boundary
from models.device import Device
from models.connection import Connection

class SelectMode(CanvasMode):
    """Mode for selecting and manipulating devices and boundaries."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
        self.mouse_press_pos = None
        self.drag_started = False
        self.click_item = None
        self.drag_threshold = 5  # Minimum drag distance to consider it a drag
        self.name = "Select Mode"  # Add explicit name for this mode
        self.drag_start_positions = {}  # Track start positions of items being dragged
    
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
    
    def deactivate(self):
        """Disable dragging when leaving select mode."""
        self.logger.debug("SelectMode: Deactivated")
        
        # Disable dragging for all devices
        for device in self.canvas.devices:
            device.setFlag(QGraphicsItem.ItemIsMovable, False)
        
        # We intentionally keep connections selectable even in other modes
        # so they can be selected by clicking directly on them
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Handle mouse button press events."""
        self.mouse_press_pos = scene_pos
        self.drag_started = False
        self.drag_start_positions = {}  # Reset drag positions
        
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
                from models.connection import Connection
                from models.boundary import Boundary
                
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
                self.click_item = selectable_item
                
                # If clicked on an item that's not selected and not adding to selection
                if not selectable_item.isSelected() and not (event.modifiers() & Qt.ControlModifier):
                    self.canvas.scene().clearSelection()
                
                # Select the item
                selectable_item.setSelected(True)
                
                # Emit the selection changed signal to ensure properties panel is updated ONCE
                # (removing intermediate signals that cause flicker)
                if hasattr(self.canvas, 'selection_changed'):
                    # This is a critical change - emit with slight delay to ensure UI is updated
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(10, lambda: self.canvas.selection_changed.emit([selectable_item]))
                
                # Only devices and boundaries can be dragged
                if isinstance(selectable_item, Device) or isinstance(selectable_item, Boundary):
                    # Make sure it's set as movable
                    selectable_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                    
                    # Important: If we clicked on a child item but are dragging the parent,
                    # we need to let the event system know we're handling this item
                    if original_item != selectable_item:
                        # Forward this event to the parent device to start dragging it
                        event.accept()
                        selectable_item.mousePressEvent(event)
                    
                    # Return False to allow Qt's native drag behavior to kick in
                    # Do NOT emit another selection changed signal here - it causes flicker
                    return False
                else:
                    # For connections, just return without emitting another signal
                    return True
            
            # If clicked in empty space, clear selection unless Ctrl is pressed
            elif not (event.modifiers() & Qt.ControlModifier):
                self.canvas.scene().clearSelection()
                # Return True to indicate we handled the event
                return True
            
        # If right button, do nothing and let the context menu handle it
        elif event.button() == Qt.RightButton:
            return False
        
        # By default, return False to let Qt handle the event
        return False
    
    def mouse_move_event(self, event):
        """Handle mouse move events for selection box and dragging."""
        if event.buttons() & Qt.LeftButton and self.mouse_press_pos:
            # Get current scene position
            scene_pos = self.canvas.mapToScene(event.pos())
            
            # Calculate distance moved
            dx = scene_pos.x() - self.mouse_press_pos.x()
            dy = scene_pos.y() - self.mouse_press_pos.y()
            dist = (dx*dx + dy*dy) ** 0.5
            
            # If we've moved far enough to consider it a drag
            if dist > self.drag_threshold and not self.drag_started:
                self.drag_started = True
                
                # Set drag mode based on whether we're dragging a device or creating selection box
                if self.click_item:
                    # Ensure proper drag mode for device dragging
                    self.canvas.setDragMode(self.canvas.NoDrag)
                    
                    # Track the starting position of all selected items for multi-selection drag
                    self.drag_start_positions = {}
                    for selected_item in self.canvas.scene().selectedItems():
                        if isinstance(selected_item, (Device, Boundary)):
                            self.drag_start_positions[selected_item] = selected_item.scenePos()
                else:
                    # Use rubber band mode for selection box
                    self.canvas.setDragMode(self.canvas.RubberBandDrag)
                    self.logger.debug("Started rubber band selection")
            
            # If we're in drag mode and have a clicked item, handle multi-item dragging
            if self.drag_started and self.click_item and self.drag_start_positions:
                # Calculate the drag offset from the click item's position
                clicked_item_pos = self.click_item.scenePos()
                total_dx = clicked_item_pos.x() - self.drag_start_positions[self.click_item].x()
                total_dy = clicked_item_pos.y() - self.drag_start_positions[self.click_item].y()
                
                # Apply the same offset to all other selected items
                for item, start_pos in self.drag_start_positions.items():
                    if item != self.click_item:  # Skip the clicked item (already moved by Qt)
                        new_pos = QPointF(start_pos.x() + total_dx, start_pos.y() + total_dy)
                        item.setPos(new_pos)
                        
                        # Update connections if it's a device
                        if isinstance(item, Device) and hasattr(item, 'update_connections'):
                            item.update_connections()
            
            return True
        
        return False
    
    def mouse_release_event(self, event, scene_pos=None, item=None):
        """Handle mouse release to complete selection box or drag operation."""
        if event.button() == Qt.LeftButton and self.mouse_press_pos:
            # If we were dragging multiple items, notify about position changes
            if self.drag_started and self.drag_start_positions and hasattr(self.canvas, 'event_bus'):
                for item, start_pos in self.drag_start_positions.items():
                    if item.scenePos() != start_pos:  # Only report items that actually moved
                        self.canvas.event_bus.emit('item.moved', 
                            item=item, 
                            old_pos=start_pos,
                            new_pos=item.scenePos()
                        )
            
            # Reset state variables
            self.mouse_press_pos = None
            self.drag_started = False
            self.drag_start_positions = {}
            
            # Always switch back to rubber band selection mode for next operation
            self.canvas.setDragMode(self.canvas.RubberBandDrag)
            
            # Clear reference to clicked item
            self.click_item = None
            
            # Notify about selection changes
            selected_items = self.canvas.scene().selectedItems()
            self.logger.debug(f"Selection complete: {len(selected_items)} items selected")
            self.canvas.selection_changed.emit(selected_items)
            
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
