from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsScene
import logging

class ConnectionInteractionHandler:
    """Handles user interaction with connections."""
    
    def __init__(self, connection):
        """Initialize with reference to parent connection."""
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        
        # Interaction state
        self.dragging_control_point = None
        self.is_hover = False
        
    def handle_mouse_press(self, event, router):
        """Handle mouse press events, detecting control point selection."""
        # Only process if the router has control points
        if router.has_draggable_points():
            # Get mouse position in item coordinates
            pos = event.pos()
            
            # Check if we clicked on a control point
            control_point_index = router.is_point_on_control(pos)
            if control_point_index is not None:
                self.dragging_control_point = control_point_index
                self.connection.setSelected(True)  # Ensure connection is selected when dragging
                return True
                
        return False
    
    def handle_mouse_move(self, event, router):
        """Handle mouse movement during control point dragging."""
        # Only process if we're actively dragging a control point
        if self.dragging_control_point is not None and router.has_draggable_points():
            # Inform Qt that our geometry is changing
            self.connection.prepareGeometryChange()
            
            # Calculate the update area that needs to be redrawn
            old_rect = self.connection.sceneBoundingRect().adjusted(-200, -200, 200, 200)
            
            # Get mouse position
            pos = event.pos()
            
            # Update the control point position
            router.update_control_point(
                self.dragging_control_point, 
                pos, 
                self.connection._source_port, 
                self.connection._target_port
            )
            
            # Recalculate the path
            new_path = router.calculate_path(self.connection._source_port, self.connection._target_port)
            
            # Set the new path
            self.connection.setPath(new_path)
            
            # Update label position
            if hasattr(self.connection, 'label_manager'):
                self.connection.label_manager.update_position()
            
            # Force a thorough scene update to clean up artifacts
            self._force_scene_update(old_rect)
            
            return True
            
        return False
        
    def handle_mouse_release(self, event):
        """Complete control point dragging."""
        if self.dragging_control_point is not None:
            # Signal that geometry is changing
            self.connection.prepareGeometryChange()
            
            # End the dragging operation
            self.dragging_control_point = None
            
            # Force a massive update to clean everything up
            rect = self.connection.sceneBoundingRect().adjusted(-300, -300, 300, 300)
            self._force_scene_update(rect)
            
            # Emit updated signal if available
            if hasattr(self.connection, 'signals') and hasattr(self.connection.signals, 'updated'):
                self.connection.signals.updated.emit(self.connection)
                
            return True
            
        return False
        
    def handle_hover_enter(self, event, renderer):
        """Handle hover enter events."""
        self.is_hover = True
        renderer.apply_style(is_hover=True)
        return False  # Let the parent class handle it too
        
    def handle_hover_leave(self, event, renderer):
        """Handle hover leave events."""
        self.is_hover = False
        renderer.apply_style(is_hover=False)
        return False  # Let the parent class handle it too
        
    def _force_scene_update(self, rect):
        """Force a thorough scene update in the given rect."""
        if not self.connection.scene():
            return
            
        # Calculate the new bounding rect
        new_rect = self.connection.sceneBoundingRect().adjusted(-200, -200, 200, 200)
        
        # Union with the provided rect for complete coverage
        update_rect = rect.united(new_rect)
        
        # Invalidate and update the scene
        self.connection.scene().invalidate(update_rect, QGraphicsScene.AllLayers)
        self.connection.scene().update(update_rect)
        
        # Update all views
        for view in self.connection.scene().views():
            view.viewport().update()
            
    def update_shape(self, path, router):
        """Update the connection's shape to include control points."""
        if not router.has_draggable_points():
            return path
            
        # Add control points to the shape to make them clickable
        control_points = router.get_control_points()
        if not control_points:
            return path
            
        # Large hit radius for easier selection
        hit_radius = 25  
        
        # Add each control point to the clickable area
        for cp in control_points:
            cp_path = QPainterPath()
            cp_path.addEllipse(cp, hit_radius, hit_radius)
            path.addPath(cp_path)
            
        return path 