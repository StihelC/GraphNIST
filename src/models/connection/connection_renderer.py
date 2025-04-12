from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QBrush, QColor
import logging

class ConnectionRenderer:
    """Handles rendering appearance of connections."""
    
    # Define connection type colors for both light and dark themes
    CONNECTION_TYPE_COLORS = {
        "light": {
            "ETHERNET": QColor(70, 70, 70),        # Dark gray
            "FIBER": QColor(0, 128, 0),            # Green
            "SERIAL": QColor(139, 69, 19),         # Brown
            "WIRELESS": QColor(0, 0, 255),         # Blue
            "BLUETOOTH": QColor(0, 0, 139),        # Dark blue
            "ZIGBEE": QColor(255, 165, 0),         # Orange
            "POWER": QColor(255, 0, 0),            # Red
            "USB": QColor(128, 0, 128),            # Purple
            "CUSTOM": QColor(70, 70, 70),          # Dark gray
            "POINT_TO_POINT": QColor(0, 0, 100),   # Dark blue
            "VPN": QColor(0, 100, 0),              # Dark green
            "SDWAN": QColor(0, 128, 128)           # Teal
        },
        "dark": {
            "ETHERNET": QColor(200, 200, 200),     # Light gray
            "FIBER": QColor(50, 205, 50),          # Bright green
            "SERIAL": QColor(210, 150, 80),        # Light brown/tan
            "WIRELESS": QColor(30, 144, 255),      # Dodger blue
            "BLUETOOTH": QColor(138, 43, 226),     # Blue violet
            "ZIGBEE": QColor(255, 215, 0),         # Gold
            "POWER": QColor(255, 69, 0),           # Red-orange
            "USB": QColor(186, 85, 211),           # Medium orchid
            "CUSTOM": QColor(180, 180, 180),       # Light gray
            "POINT_TO_POINT": QColor(100, 149, 237), # Cornflower blue
            "VPN": QColor(60, 179, 113),           # Medium sea green
            "SDWAN": QColor(64, 224, 208)          # Turquoise
        }
    }
    
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
        
        # Theme-related properties
        self.theme_manager = None
        self.theme_colors_applied = False
    
    def update_theme(self, theme_name):
        """Update colors based on theme change.
        
        Args:
            theme_name: Name of the theme being applied
        """
        if not self.theme_manager:
            return
            
        # Get colors for current theme
        colors = self.theme_manager.get_connection_colors()
        
        # Apply colors
        self.base_color = colors["base"]
        self.hover_color = colors["hover"]
        self.selected_color = colors["selected"]
        
        # Update control point colors
        if theme_name == self.theme_manager.DARK_THEME:
            self.control_point_border_color = QColor(250, 250, 250)  # Lighter border for dark mode
            self.control_point_fill_color = QColor(60, 60, 60)       # Dark fill
            self.control_point_highlight_color = QColor(0, 140, 255) # Brighter blue highlight
        else:
            self.control_point_border_color = QColor(30, 30, 30)     # Dark border for light mode
            self.control_point_fill_color = QColor(250, 250, 250)    # Light fill
            self.control_point_highlight_color = QColor(0, 120, 215) # Standard blue highlight
        
        # Update appearance based on current connection type
        if hasattr(self.connection, 'connection_type'):
            self.set_style_for_type(self.connection.connection_type)
        else:
            # Just apply current style without changing colors
            self.apply_style()
        
        self.theme_colors_applied = True
    
    def register_theme_manager(self, theme_manager):
        """Register with a theme manager to receive theme updates.
        
        Args:
            theme_manager: ThemeManager instance
        """
        self.theme_manager = theme_manager
        self.theme_manager.register_theme_observer(self)
        
        # Apply current theme immediately
        self.update_theme(theme_manager.get_theme())

    def set_style_for_type(self, connection_type):
        """Set the visual style based on the connection type."""
        # Get current theme name
        current_theme = "dark" if (self.theme_manager and self.theme_manager.is_dark_theme()) else "light"
        
        # Import Connection types if needed
        from .connection import ConnectionTypes
        
        # Default to a style if not found
        style = {
            'color': self.CONNECTION_TYPE_COLORS[current_theme]["CUSTOM"], 
            'style': Qt.SolidLine, 
            'width': 2
        }
        
        # Try to get the connection type name for color lookup
        connection_type_name = None
        if hasattr(connection_type, "name"):
            connection_type_name = connection_type.name
        elif isinstance(connection_type, str):
            connection_type_name = connection_type.upper()
        
        # Look up the color based on connection type name
        if connection_type_name and connection_type_name in self.CONNECTION_TYPE_COLORS[current_theme]:
            color = self.CONNECTION_TYPE_COLORS[current_theme][connection_type_name]
            
            # Now determine the line style and width based on the connection type
            if connection_type == ConnectionTypes.ETHERNET:
                style = {'color': color, 'style': Qt.SolidLine, 'width': 2}
            elif connection_type == ConnectionTypes.FIBER:
                style = {'color': color, 'style': Qt.SolidLine, 'width': 2.5}
            elif connection_type == ConnectionTypes.SERIAL:
                style = {'color': color, 'style': Qt.DashLine, 'width': 1.5}
            elif connection_type == ConnectionTypes.WIRELESS:
                style = {'color': color, 'style': Qt.DotLine, 'width': 1.5}
            elif connection_type == ConnectionTypes.BLUETOOTH:
                style = {'color': color, 'style': Qt.DashDotLine, 'width': 1.5}
            elif connection_type == ConnectionTypes.ZIGBEE:
                style = {'color': color, 'style': Qt.DotLine, 'width': 1.5}
            elif connection_type == ConnectionTypes.POWER:
                style = {'color': color, 'style': Qt.SolidLine, 'width': 3}
            elif connection_type == ConnectionTypes.USB:
                style = {'color': color, 'style': Qt.SolidLine, 'width': 1.5}
            elif connection_type == ConnectionTypes.CUSTOM:
                style = {'color': color, 'style': Qt.SolidLine, 'width': 2}
            elif connection_type == ConnectionTypes.POINT_TO_POINT:
                style = {'color': color, 'style': Qt.SolidLine, 'width': 2}
            elif connection_type == ConnectionTypes.VPN:
                style = {'color': color, 'style': Qt.DashDotDotLine, 'width': 2}
            elif connection_type == ConnectionTypes.SDWAN:
                style = {'color': color, 'style': Qt.DashDotLine, 'width': 2.5}
        
        # Apply the style
        self.base_color = style['color']
        self.line_style = style['style']
        self.line_width = style['width']
        
        # Update the connection's appearance
        self.apply_style()
        
        return style
    
    def _brighten_color(self, color, factor=1.5):
        """Make a color brighter for better visibility in dark theme.
        
        Args:
            color: QColor to brighten
            factor: Brightness factor (higher = brighter)
            
        Returns:
            QColor: Brightened color
        """
        # Create a copy to avoid modifying the original
        result = QColor(color)
        
        # Get HSL components
        h, s, l, a = result.getHslF()
        
        # Increase lightness (but don't go above 1.0)
        l = min(l * factor, 0.9)
        
        # Set the new HSL values
        result.setHslF(h, s, l, a)
        
        return result
    
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
        
        # Draw filled circle with border
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