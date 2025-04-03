from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor
import logging

class ConnectionRenderer:
    """Handles rendering appearance of connections."""
    
    def __init__(self, connection):
        """Initialize with reference to parent connection."""
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        
        # Default style properties
        self.line_width = 1
        self.line_style = Qt.SolidLine
        self.base_color = QColor(70, 70, 70)  # Default dark gray
        self.hover_color = QColor(0, 120, 215)  # Default bright blue
        self.selected_color = QColor(255, 140, 0)  # Orange
        
        # Control point appearance
        self.control_point_radius = 8
        self.control_point_border_color = Qt.black
        self.control_point_fill_color = Qt.white
        self.control_point_highlight_color = QColor(0, 120, 215)  # Highlight blue
    
    def set_style_for_type(self, connection_type):
        """Set the visual style based on the connection type."""
        # Import constants if needed (in case this method is called directly)
        from constants import ConnectionTypes
        
        # Default style
        style = {
            'color': QColor(30, 30, 30),
            'style': Qt.SolidLine,
            'width': 2
        }
        
        # Style based on connection type
        if connection_type == ConnectionTypes.ETHERNET:
            style = {'color': QColor(0, 0, 0), 'style': Qt.SolidLine, 'width': 2}
        elif connection_type == ConnectionTypes.SERIAL:
            style = {'color': QColor(0, 0, 255), 'style': Qt.DashLine, 'width': 1.5}
        elif connection_type == ConnectionTypes.FIBER:
            style = {'color': QColor(0, 128, 0), 'style': Qt.SolidLine, 'width': 3}
        elif connection_type == ConnectionTypes.WIRELESS:
            style = {'color': QColor(128, 0, 128), 'style': Qt.DotLine, 'width': 1.5}
        elif connection_type == ConnectionTypes.GIGABIT_ETHERNET:
            style = {'color': QColor(50, 50, 50), 'style': Qt.SolidLine, 'width': 2.5}
        elif connection_type == ConnectionTypes.TEN_GIGABIT_ETHERNET:
            style = {'color': QColor(0, 100, 200), 'style': Qt.SolidLine, 'width': 3}
        elif connection_type == ConnectionTypes.FORTY_GIGABIT_ETHERNET:
            style = {'color': QColor(0, 150, 200), 'style': Qt.SolidLine, 'width': 3.5}
        elif connection_type == ConnectionTypes.HUNDRED_GIGABIT_ETHERNET:
            style = {'color': QColor(0, 200, 200), 'style': Qt.SolidLine, 'width': 4}
        elif connection_type == ConnectionTypes.FIBER_CHANNEL:
            style = {'color': QColor(200, 100, 0), 'style': Qt.SolidLine, 'width': 3}
        elif connection_type == ConnectionTypes.MPLS:
            style = {'color': QColor(100, 0, 100), 'style': Qt.DashDotLine, 'width': 2.5}
        elif connection_type == ConnectionTypes.POINT_TO_POINT:
            style = {'color': QColor(0, 0, 100), 'style': Qt.SolidLine, 'width': 2}
        elif connection_type == ConnectionTypes.VPN:
            style = {'color': QColor(0, 100, 0), 'style': Qt.DashDotDotLine, 'width': 2}
        elif connection_type == ConnectionTypes.SDWAN:
            style = {'color': QColor(0, 128, 128), 'style': Qt.DashDotLine, 'width': 2.5}
        
        # Apply the style
        self.base_color = style['color']
        self.line_style = style['style']
        self.line_width = style['width']
        
        # Update the connection's appearance
        self.apply_style()
        
        return style
    
    def apply_style(self, is_selected=None, is_hover=None):
        """Apply the current style to the connection."""
        if is_selected is None:
            is_selected = self.connection.isSelected()
            
        if is_hover is None:
            is_hover = getattr(self.connection, 'is_hover', False)
        
        # Create the pen based on selection/hover state
        pen = QPen()
        
        if is_selected:
            pen.setColor(self.selected_color)
            pen.setWidth(self.line_width + 1)
        elif is_hover:
            pen.setColor(self.hover_color)
            pen.setWidth(self.line_width + 1)
        else:
            pen.setColor(self.base_color)
            pen.setWidth(self.line_width)
            
        pen.setStyle(self.line_style)
        
        # Apply the pen to the connection
        self.connection.setPen(pen)
    
    def draw_control_points(self, painter, control_points):
        """Draw control points for the connection."""
        if not control_points:
            return
            
        painter.save()
        
        # Draw control points with a more visible appearance
        radius = self.control_point_radius
        
        # Draw white-filled circle with black border
        painter.setPen(QPen(self.control_point_border_color, 2))
        painter.setBrush(QBrush(self.control_point_fill_color))
        
        # Draw each control point
        for cp in control_points:
            # Draw the main control point
            painter.drawEllipse(cp, radius, radius)
            
            # Draw a smaller highlight in the center for better visual feedback
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.control_point_highlight_color))
            painter.drawEllipse(cp, radius/2, radius/2)
        
        painter.restore() 