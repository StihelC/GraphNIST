from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPointF

class DeviceInteraction:
    """Handles mouse interaction and events for a device."""
    
    def __init__(self, device):
        """Initialize the device interaction handler.
        
        Args:
            device: The parent device instance
        """
        self.device = device
        self.logger = self.device.logger
        
        # Tracking variables for drag operations
        self._start_pos = None
        self._is_dragging = False
        self._drag_threshold = 5  # pixels to consider a drag vs click
        
        # For connection drawing
        self._show_connection_points = False
    
    def mouse_press(self, event):
        """Handle mouse press event."""
        # Cache the start position for potential drag tracking
        self._start_pos = event.pos()
        
        # Detect left click vs right click
        if event.button() == Qt.LeftButton:
            # Start tracking for possible drag
            self._is_dragging = True
            
            # Raise the device to the top
            prev_z = self.device.zValue()
            top_z = self._get_top_z_value()
            if top_z > prev_z:
                self.device.setZValue(top_z + 1)
                
            # Emit signal at the start of potential drag
            if hasattr(self.device.signals, 'drag_started'):
                self.device.signals.drag_started.emit(self.device)
            
            # Let the event propagate for selection and dragging
            # Important: return False to allow Qt's default drag behavior
            return False
            
        elif event.button() == Qt.RightButton:
            # Context menu is typically handled by the canvas or controller
            # Just accept the right click
            return True
            
        return False
    
    def mouse_move(self, event):
        """Handle mouse move event."""
        # Only care about mouse move during drag operations
        if not self._is_dragging:
            return False
            
        # Update connected lines if device moved
        self.device.update_connections()
        
        # Event handled
        return True
    
    def mouse_release(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton and self._is_dragging:
            # Reset drag tracking state
            self._is_dragging = False
            
            # Emit signal at the end of drag
            if hasattr(self.device.signals, 'drag_finished'):
                self.device.signals.drag_finished.emit(self.device)
                
            # Update connected lines
            self.device.update_connections()
            
            # Calculate if this was actually a drag or just a click
            start_point = self._start_pos
            end_point = event.pos()
            
            if start_point and self._calc_distance(start_point, end_point) < self._drag_threshold:
                # This was just a click, not a drag
                # Don't handle specially, let Qt handle selection
                return False
                
            # This was a real drag, consider it handled
            return True
            
        return False
    
    def mouse_double_click(self, event):
        """Handle double-click event."""
        if event.button() == Qt.LeftButton:
            # Emit double-click signal
            if hasattr(self.device.signals, 'double_clicked'):
                self.device.signals.double_clicked.emit(self.device)
            return True
            
        return False
    
    def hover_enter(self, event):
        """Handle hover enter event."""
        # Could show device tooltip or handle hover effects
        return False
    
    def hover_leave(self, event):
        """Handle hover leave event."""
        # Could hide device tooltip or handle hover effects
        return False
    
    def show_connection_points(self, show=True):
        """Show or hide connection points for the device."""
        self._show_connection_points = show
        # Update visual state for connection points
        self.device.update()
    
    def _calc_distance(self, p1, p2):
        """Calculate distance between two points."""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        return (dx * dx + dy * dy) ** 0.5
    
    def _get_top_z_value(self):
        """Get the highest z-value among visible items in the scene."""
        if not self.device.scene():
            return self.device.zValue()
            
        top_z = self.device.zValue()
        for item in self.device.scene().items():
            if item.isVisible() and item.zValue() > top_z:
                top_z = item.zValue()
                
        return top_z
        
    def get_connection_points(self):
        """Get connection points for the device (default: 4 cardinal points)."""
        # Calculate the device center
        rect = self.device.boundingRect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        
        # Get the device rectangle
        w = rect.width()
        h = rect.height()
        
        # Define connection points at cardinal directions
        points = [
            QPointF(center_x, 0),             # North
            QPointF(w, center_y),             # East
            QPointF(center_x, h),             # South
            QPointF(0, center_y),             # West
        ]
        
        return points
        
    def get_nearest_port(self, scene_pos):
        """Get the nearest connection port to the given scene position."""
        # Convert scene position to local coordinates
        local_pos = self.device.mapFromScene(scene_pos)
        
        # Get all connection points
        ports = self.get_connection_points()
        
        # Find the nearest point
        nearest_point = None
        min_distance = float('inf')
        
        for point in ports:
            distance = self._calc_distance(point, local_pos)
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
                
        # Convert the local point back to scene coordinates
        if nearest_point:
            return self.device.mapToScene(nearest_point)
            
        # Fallback to device center
        device_rect = self.device.boundingRect()
        return self.device.mapToScene(QPointF(device_rect.width() / 2, device_rect.height() / 2)) 