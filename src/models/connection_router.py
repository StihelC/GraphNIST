from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainterPath
import logging

class ConnectionRouter:
    """Base class for connection routing strategies."""
    
    def __init__(self, connection):
        """Initialize with reference to parent connection."""
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        
    def calculate_path(self, source_port, target_port):
        """Calculate and return a QPainterPath between ports."""
        raise NotImplementedError("Subclasses must implement calculate_path()")
        
    def get_control_points(self):
        """Return any control points for the path."""
        return []
        
    def has_draggable_points(self):
        """Return True if this router has draggable control points."""
        return False
        
    def update_control_point(self, index, position, source_port, target_port):
        """Update a specific control point to a new position."""
        pass
    
    def is_point_on_control(self, position, control_index):
        """Check if a position is on a control point."""
        return False


class StraightLineRouter(ConnectionRouter):
    """Routes connections as straight lines between points."""
    
    def calculate_path(self, source_port, target_port):
        """Create a simple straight path between ports."""
        path = QPainterPath()
        path.moveTo(source_port)
        path.lineTo(target_port)
        return path


class OrthogonalRouter(ConnectionRouter):
    """Routes connections as orthogonal (90-degree) paths."""
    
    def __init__(self, connection):
        super().__init__(connection)
        self.control_points = []
        
    def calculate_path(self, source_port, target_port):
        """Create an orthogonal path between ports."""
        # Initialize control points if needed
        if not self.control_points or len(self.control_points) != 2:
            self._initialize_control_points(source_port, target_port)
        else:
            # Make sure control points maintain orthogonality
            self._maintain_orthogonal_constraints(source_port, target_port)
            
        # Create path through control points
        path = QPainterPath()
        path.moveTo(source_port)
        for cp in self.control_points:
            path.lineTo(cp)
        path.lineTo(target_port)
        
        return path
        
    def has_draggable_points(self):
        """Orthogonal routes have draggable control points."""
        return True
        
    def get_control_points(self):
        """Return the control points for this path."""
        return self.control_points
        
    def is_point_on_control(self, position, threshold=20):
        """Check if the given position is near a control point."""
        for i, cp in enumerate(self.control_points):
            if (position - cp).manhattanLength() < threshold:
                return i
        return None
        
    def _initialize_control_points(self, source_port, target_port):
        """Initialize control points for orthogonal routing."""
        sx, sy = source_port.x(), source_port.y()
        tx, ty = target_port.x(), target_port.y()
        dx, dy = tx - sx, ty - sy
        
        # Decide on horizontal-first or vertical-first routing
        if abs(dx) > abs(dy):
            # Horizontal dominant - go horizontally first
            middle_x = sx + dx/2
            self.control_points = [
                QPointF(middle_x, sy),  # First point - horizontal from source
                QPointF(middle_x, ty)   # Second point - vertical to target
            ]
        else:
            # Vertical dominant - go vertically first
            middle_y = sy + dy/2
            self.control_points = [
                QPointF(sx, middle_y),  # First point - vertical from source
                QPointF(tx, middle_y)   # Second point - horizontal to target
            ]
            
    def _maintain_orthogonal_constraints(self, source_port, target_port):
        """Ensure control points maintain orthogonal routing when ports move."""
        if len(self.control_points) != 2:
            self._initialize_control_points(source_port, target_port)
            return
            
        sx, sy = source_port.x(), source_port.y()
        tx, ty = target_port.x(), target_port.y()
        
        # Determine if we should use horizontal-first or vertical-first based on current layout
        dx, dy = tx - sx, ty - sy
        horizontal_first = abs(dx) > abs(dy)
        
        if horizontal_first:
            # Horizontal first: use x-midpoint between source and target
            middle_x = sx + dx/2
            self.control_points = [
                QPointF(middle_x, sy),  # First point - horizontal from source
                QPointF(middle_x, ty)   # Second point - vertical to target
            ]
        else:
            # Vertical first: use y-midpoint between source and target
            middle_y = sy + dy/2
            self.control_points = [
                QPointF(sx, middle_y),  # First point - vertical from source
                QPointF(tx, middle_y)   # Second point - horizontal to target
            ]

    def update_control_point(self, index, position, source_port, target_port):
        """Update a specific control point, maintaining orthogonality."""
        if index is None or index >= len(self.control_points):
            return
            
        # Determine if we're in horizontal-first or vertical-first mode based on current layout
        sx, sy = source_port.x(), source_port.y()
        tx, ty = target_port.x(), target_port.y()
        dx, dy = tx - sx, ty - sy
        horizontal_first = abs(dx) > abs(dy)
        
        # Update control points based on drag direction
        if index == 0:  # First control point
            if horizontal_first:
                # In horizontal-first mode, first point moves horizontally only
                new_x = position.x()
                self.control_points[0] = QPointF(new_x, sy)  # Keep y at source level
                self.control_points[1] = QPointF(new_x, ty)  # Keep x aligned with first point
            else:
                # In vertical-first mode, first point moves vertically only
                new_y = position.y()
                self.control_points[0] = QPointF(sx, new_y)  # Keep x at source level
                self.control_points[1] = QPointF(tx, new_y)  # Keep y aligned with first point
        else:  # Second control point
            if horizontal_first:
                # In horizontal-first mode, second point maintains x from first point
                # and only adjusts vertically
                new_y = position.y()
                self.control_points[1] = QPointF(self.control_points[0].x(), new_y)
            else:
                # In vertical-first mode, second point maintains y from first point
                # and only adjusts horizontally
                new_x = position.x()
                self.control_points[1] = QPointF(new_x, self.control_points[0].y())


class CurvedRouter(ConnectionRouter):
    """Routes connections as curved bezier paths."""
    
    def calculate_path(self, source_port, target_port):
        """Create a bezier curve path between ports."""
        path = QPainterPath()
        
        sx, sy = source_port.x(), source_port.y()
        tx, ty = target_port.x(), target_port.y()
        
        # Calculate control points for a nice curve
        dx, dy = tx - sx, ty - sy
        cp1 = QPointF(sx + dx/3, sy)
        cp2 = QPointF(tx - dx/3, ty)
        
        path.moveTo(source_port)
        path.cubicTo(cp1, cp2, target_port)
        
        return path 