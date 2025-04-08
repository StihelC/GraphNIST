from PyQt5.QtCore import QObject, QPointF, Qt
from PyQt5.QtWidgets import QGraphicsView
import logging

from models.device import Device
from models.boundary import Boundary


class GroupSelectionManager(QObject):
    """
    Manager for group selection operations that handles the logic for selecting and
    manipulating multiple items together.
    """
    
    def __init__(self, canvas):
        """Initialize the group selection manager."""
        super().__init__()
        self.canvas = canvas
        self.logger = logging.getLogger(__name__)
        
        # Variables for tracking multi-selection drag state
        self._multi_drag_active = False
        self._multi_drag_start_pos = None
        self._multi_drag_items = {}

    def start_drag(self, scene_pos, item=None):
        """
        Start a drag operation for multiple selected items.
        
        Args:
            scene_pos: The scene position where the drag starts
            item: The item that was clicked (optional)
        
        Returns:
            bool: True if a multi-selection drag was started, False otherwise
        """
        if not self.canvas or not self.canvas.scene():
            return False
            
        # Get selected items
        selected_items = self.canvas.scene().selectedItems()
        
        # We need at least 2 items for a multi-selection drag
        if len(selected_items) < 2:
            return False
            
        # Check if we clicked on a selected item
        is_selected_item = item and item.isSelected()
        
        # If we clicked on a child of a selected item, use the parent
        if not is_selected_item and item and item.parentItem() and item.parentItem().isSelected():
            is_selected_item = True
            item = item.parentItem()
            
        # Only start a multi-drag if we clicked on a selected item
        if is_selected_item:
            self._multi_drag_active = True
            self._multi_drag_start_pos = scene_pos
            self._multi_drag_items = {}
            
            # Store positions of all selected items
            for selected_item in selected_items:
                if isinstance(selected_item, (Device, Boundary)):
                    self._multi_drag_items[selected_item] = selected_item.scenePos()
                    
                    # Log item being stored
                    if hasattr(selected_item, 'name'):
                        self.logger.debug(f"GROUP-DRAG: {selected_item.name} at {selected_item.scenePos()}")
                    else:
                        self.logger.debug(f"GROUP-DRAG: {type(selected_item).__name__} at {selected_item.scenePos()}")
            
            # Set NoDrag mode to override Qt's default behavior
            self.canvas.setDragMode(QGraphicsView.NoDrag)
            
            self.logger.debug(f"GROUP-DRAG: Started group selection drag with {len(self._multi_drag_items)} items")
            return True
            
        return False
    
    def process_drag(self, scene_pos):
        """
        Process a drag movement for multiple selected items.
        
        Args:
            scene_pos: The current scene position of the mouse
            
        Returns:
            bool: True if the drag was handled, False otherwise
        """
        if not self._multi_drag_active or not self._multi_drag_start_pos:
            return False
            
        # Calculate movement delta
        delta_x = scene_pos.x() - self._multi_drag_start_pos.x()
        delta_y = scene_pos.y() - self._multi_drag_start_pos.y()
        
        # Move all items in the selection by the same delta
        moved_count = 0
        for item, start_pos in self._multi_drag_items.items():
            if item.scene():  # Make sure item still exists
                # Calculate new position
                new_pos = QPointF(start_pos.x() + delta_x, start_pos.y() + delta_y)
                # Set the position directly
                item.setPos(new_pos)
                moved_count += 1
                
                # Update connections for devices
                if isinstance(item, Device) and hasattr(item, 'update_connections'):
                    item.update_connections()
        
        # Force viewport update if items were moved
        if moved_count > 0:
            self.canvas.viewport().update()
            self.logger.debug(f"GROUP-DRAG: Moved {moved_count} items by delta ({delta_x:.1f}, {delta_y:.1f})")
            
        return moved_count > 0
    
    def end_drag(self):
        """
        End a drag operation for multiple selected items.
        
        Returns:
            bool: True if a multi-selection drag was ended, False otherwise
        """
        if not self._multi_drag_active:
            return False
            
        self.logger.debug(f"GROUP-DRAG: Ending group selection drag with {len(self._multi_drag_items)} items")
        
        # Record moves to event bus for undo/redo
        if hasattr(self.canvas, 'event_bus') and self.canvas.event_bus:
            for item, start_pos in self._multi_drag_items.items():
                if item.scene():
                    end_pos = item.scenePos()
                    if start_pos != end_pos:
                        self.canvas.event_bus.emit('item.moved',
                            item=item,
                            old_pos=start_pos,
                            new_pos=end_pos
                        )
                        
                        # Log the moved items
                        if hasattr(item, 'name'):
                            self.logger.debug(f"GROUP-DRAG: Moved {item.name} from {start_pos} to {end_pos}")
                        else:
                            self.logger.debug(f"GROUP-DRAG: Moved {type(item).__name__} from {start_pos} to {end_pos}")
        
        # Reset state
        self._multi_drag_active = False
        self._multi_drag_start_pos = None
        self._multi_drag_items = {}
        
        # Restore rubber band mode
        self.canvas.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Update the scene
        if self.canvas.scene():
            self.canvas.scene().update()
            
        return True
    
    def is_drag_active(self):
        """
        Check if a multi-selection drag is currently active.
        
        Returns:
            bool: True if a drag is active, False otherwise
        """
        return self._multi_drag_active
        
    def get_drag_items(self):
        """
        Get the items being dragged.
        
        Returns:
            dict: A dictionary of items and their original positions
        """
        return self._multi_drag_items.copy() if self._multi_drag_active else {} 