from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt5.QtGui import QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer
import logging

from .boundary_signals import BoundarySignals
from .boundary_label import EditableTextItem

class Boundary(QGraphicsRectItem):
    """A rectangular grouping boundary for grouping devices together."""
    
    def __init__(self, rect, name=None, color=None, parent=None, theme_manager=None):
        """Initialize the boundary.
        
        Args:
            rect: QRectF defining the boundary's size and position
            name: Optional name for the boundary
            color: Optional color for the boundary
            parent: Optional parent item
            theme_manager: Optional theme manager for styling
        """
        super().__init__(rect, parent)
        
        # Set z-value to be behind everything else (layer 0) but still visible
        self.setZValue(0)
        
        # Ensure the item doesn't stack behind parent (critical for visibility)
        self.setFlag(QGraphicsItem.ItemStacksBehindParent, False)
        self.setOpacity(1.0)  # Full opacity
        
        self.logger = logging.getLogger(__name__)
        
        # Add debounce timer for selection
        self.selection_timer = QTimer()
        self.selection_timer.setSingleShot(True)
        self.selection_timer.timeout.connect(self._on_selection_timer)
        self.pending_selection = None
        
        # Check input parameters and provide defaults
        if name is None:
            name = "Boundary"
        
        if color is None:
            color = QColor(40, 120, 200, 80)  # Default semi-transparent blue
        
        # Store theme manager reference
        self.theme_manager = theme_manager
        
        # Create signals object
        self.signals = BoundarySignals()
        
        # Set basic properties
        self.name = name
        self.color = color
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        self.setVisible(True)  # Explicitly set to visible
        
        # Apply visual style
        self._apply_style()
        
        # Create label
        self._create_label()
        
        # Setup for resizing
        self._setup_resize_handles()

    def _apply_style(self):
        """Apply visual styling to the boundary."""
        # Set more visible border with higher opacity
        border_color = QColor(self.color.red(), self.color.green(), self.color.blue(), 200)
        self.setPen(QPen(border_color, 2, Qt.SolidLine))
        
        # Make the fill slightly more opaque but still see-through
        fill_color = QColor(self.color)
        if fill_color.alpha() < 100:  # If too transparent
            fill_color.setAlpha(100)  # Set to more visible value
        
        self.setBrush(QBrush(fill_color))
        
        # Force a redraw
        self.update()
    
    def _create_label(self):
        """Create and position the editable label text."""
        # Try to find a theme manager if not already set
        if not self.theme_manager:
            self.theme_manager = self.get_theme_manager()
            
        # Create editable text item as a child of this boundary
        self.label = EditableTextItem(self.name, self)
        
        # Position at bottom left outside the boundary
        self._update_label_position()
    
    def _update_label_position(self):
        """Update the label position relative to the boundary."""
        if hasattr(self, 'label') and self.label:
            # Position at bottom left outside the boundary rectangle
            rect = self.rect()
            # Use local coordinates since the label is a child item
            self.label.setPos(rect.left(), rect.bottom() + 5)
    
    def text_edited(self, new_text):
        """Handle when the label text has been edited."""
        if new_text != self.name:
            old_name = self.name
            self.name = new_text
            # Emit signal for name change
            self.signals.name_changed.emit(self, new_text)
            print(f"Boundary name changed from '{old_name}' to '{new_text}'")
    
    def set_name(self, name):
        """Change the boundary name."""
        if name != self.name:
            self.name = name
            if hasattr(self, 'label') and self.label:
                self.label.setPlainText(name)
    
    def set_color(self, color):
        """Change the boundary color."""
        self.color = color
        self._apply_style()
    
    def itemChange(self, change, value):
        """Handle item change events."""
        if change == QGraphicsRectItem.ItemSelectedHasChanged:
            # Queue up selection change with a slight delay to avoid double-firing
            self.pending_selection = value
            self.selection_timer.start(100)  # Short delay of 100ms
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter events."""
        # Intentionally pass through to parent for hover tracking
        # but don't call super().hoverEnterEvent(event) to avoid default behavior
        # that might interfere with resize handles
        pass
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave events."""
        # Intentionally pass through to parent for hover tracking
        # but don't call super().hoverLeaveEvent(event) to avoid default behavior
        # that might interfere with resize handles
        pass
    
    def update_geometry(self, rect):
        """Update the boundary geometry."""
        super().setRect(rect)
        self._update_label_position()
    
    def delete(self):
        """Delete the boundary and clean up resources."""
        # Remove label if it exists
        if hasattr(self, 'label') and self.label:
            if self.label.scene():
                self.label.scene().removeItem(self.label)
            self.label = None
        
        # Clean up any timers
        if hasattr(self, 'selection_timer'):
            self.selection_timer.stop()
            self.selection_timer = None
        
        # If I'm still in a scene, remove myself
        if self.scene():
            self.scene().removeItem(self)
        
    def update_color(self):
        """Update the visual appearance of the boundary with current color."""
        # Set more visible border with higher opacity
        border_color = QColor(self.color.red(), self.color.green(), self.color.blue(), 200)
        self.setPen(QPen(border_color, 2, Qt.SolidLine))
        
        # Make the fill slightly more opaque but still see-through
        fill_color = QColor(self.color)
        fill_color.setAlpha(100)  # Set to semi-transparent
        
        self.setBrush(QBrush(fill_color))
        self.update()
    
    def update_name(self):
        """Update the label text to match the current name."""
        if hasattr(self, 'label') and self.label:
            self.label.setPlainText(self.name)
    
    def update_theme(self, theme_name=None):
        """Update visual styling based on theme."""
        if hasattr(self, 'label') and self.label:
            self.label.refresh_theme()
    
    def get_theme_manager(self):
        """Find a theme manager if one wasn't explicitly passed."""
        # Check if there's a scene
        scene = self.scene()
        if not scene:
            return None
            
        # Check scene's views
        views = scene.views()
        if not views:
            return None
            
        # Get the main canvas view
        view = views[0]
        
        # First, check if the view has a theme manager directly
        if hasattr(view, 'theme_manager') and view.theme_manager:
            return view.theme_manager
            
        # If not, check if the parent window has a theme manager
        if hasattr(view, 'parent') and callable(view.parent):
            parent = view.parent()
            if parent and hasattr(parent, 'theme_manager') and parent.theme_manager:
                return parent.theme_manager
                
        # No theme manager found
        return None

    def _setup_resize_handles(self):
        """Set up the resize handles for the boundary."""
        # Define resize handles
        self.handles = {
            "top_left": None,
            "top_right": None,
            "bottom_left": None,
            "bottom_right": None,
            "top": None,
            "bottom": None,
            "left": None,
            "right": None
        }
        
        # Track which handle is being dragged
        self.active_handle = None
        
        # Start position for resize operation
        self.resize_start_rect = None
        self.resize_start_pos = None
    
    def _get_handle_rect(self, handle):
        """Get the rect for a specific resize handle."""
        rect = self.rect()
        handle_size = 10
        
        # Only show handles when selected
        if not self.isSelected():
            return QRectF(0, 0, 0, 0)
            
        # Calculate positions for different handles
        if handle == "top_left":
            return QRectF(rect.left() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size)
        elif handle == "top_right":
            return QRectF(rect.right() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size)
        elif handle == "bottom_left":
            return QRectF(rect.left() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size)
        elif handle == "bottom_right":
            return QRectF(rect.right() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size)
        elif handle == "top":
            return QRectF(rect.center().x() - handle_size/2, rect.top() - handle_size/2, handle_size, handle_size)
        elif handle == "bottom":
            return QRectF(rect.center().x() - handle_size/2, rect.bottom() - handle_size/2, handle_size, handle_size)
        elif handle == "left":
            return QRectF(rect.left() - handle_size/2, rect.center().y() - handle_size/2, handle_size, handle_size)
        elif handle == "right":
            return QRectF(rect.right() - handle_size/2, rect.center().y() - handle_size/2, handle_size, handle_size)
        
        return QRectF(0, 0, 0, 0)
    
    def _handle_at_position(self, pos):
        """Check if a position is over a resize handle."""
        # Only show handles when selected
        if not self.isSelected():
            return None
            
        # Check each handle
        for handle_name in self.handles:
            handle_rect = self._get_handle_rect(handle_name)
            if handle_rect.contains(pos):
                return handle_name
                
        return None

    def paint(self, painter, option, widget):
        """Paint the boundary and its resize handles."""
        # Paint the main boundary
        super().paint(painter, option, widget)
        
        # Only show handles when selected
        if self.isSelected():
            # Set handle appearance
            if self.theme_manager and self.theme_manager.is_dark_theme():
                # Light handles for dark theme
                painter.setPen(QPen(QColor(220, 220, 220), 1))
                painter.setBrush(QBrush(QColor(180, 180, 180, 180)))
            else:
                # Dark handles for light theme
                painter.setPen(QPen(QColor(40, 40, 40), 1))
                painter.setBrush(QBrush(QColor(80, 80, 80, 180)))
            
            # Draw each handle
            for handle_name in self.handles:
                handle_rect = self._get_handle_rect(handle_name)
                if not handle_rect.isEmpty():
                    painter.drawRect(handle_rect)
    
    def hoverMoveEvent(self, event):
        """Update cursor based on resize handles."""
        pos = event.pos()
        handle = self._handle_at_position(pos)
        
        if handle:
            # Set appropriate cursor for resize
            if handle in ["top_left", "bottom_right"]:
                self.setCursor(Qt.SizeFDiagCursor)
            elif handle in ["top_right", "bottom_left"]:
                self.setCursor(Qt.SizeBDiagCursor)
            elif handle in ["top", "bottom"]:
                self.setCursor(Qt.SizeVerCursor)
            elif handle in ["left", "right"]:
                self.setCursor(Qt.SizeHorCursor)
        else:
            # Standard cursor for no handle
            self.setCursor(Qt.ArrowCursor)
        
        # Let parent handle any other hover logic
        super().hoverMoveEvent(event)
    
    def setRect(self, rect):
        """Override setRect to update the label position."""
        super().setRect(rect)
        self._update_label_position()
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging and resizing."""
        # Check if press is on a resize handle
        pos = event.pos()
        handle = self._handle_at_position(pos)
        
        if handle and event.button() == Qt.LeftButton:
            # Start resize operation
            self.active_handle = handle
            self.resize_start_rect = self.rect()
            self.resize_start_pos = pos
            
            # Important: accept the event to get mouseMoveEvent callbacks
            event.accept()
            
            # Log the resize start
            self.logger.debug(f"Boundary resize start with handle: {handle}")
            return
            
        # If not a resize handle, pass to default handler for moving
        super().mousePressEvent(event)
        
        # Track whether this is a move operation
        if event.button() == Qt.LeftButton and not handle:
            # Track drag start for signals
            if hasattr(self, 'signals') and hasattr(self.signals, 'drag_started'):
                self.signals.drag_started.emit(self)
                
            # If connected to a canvas with a group selection manager, notify it
            canvas = self._get_canvas()
            if canvas and hasattr(canvas, 'group_selection_manager') and canvas.group_selection_manager:
                if self.isSelected():
                    # Start group drag if this is a selected item
                    scene_pos = self.mapToScene(event.pos())
                    canvas.group_selection_manager.start_drag(scene_pos, self)
                
    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing or dragging."""
        if self.active_handle and self.resize_start_rect and self.resize_start_pos:
            # This is a resize operation
            pos = event.pos()
            dx = pos.x() - self.resize_start_pos.x()
            dy = pos.y() - self.resize_start_pos.y()
            
            # Get original rect
            r = self.resize_start_rect
            new_rect = QRectF(r)
            
            # Adjust rect based on active handle
            if self.active_handle == "top_left":
                new_rect.setTopLeft(r.topLeft() + QPointF(dx, dy))
            elif self.active_handle == "top_right":
                new_rect.setTopRight(r.topRight() + QPointF(dx, dy))
            elif self.active_handle == "bottom_left":
                new_rect.setBottomLeft(r.bottomLeft() + QPointF(dx, dy))
            elif self.active_handle == "bottom_right":
                new_rect.setBottomRight(r.bottomRight() + QPointF(dx, dy))
            elif self.active_handle == "top":
                new_rect.setTop(r.top() + dy)
            elif self.active_handle == "bottom":
                new_rect.setBottom(r.bottom() + dy)
            elif self.active_handle == "left":
                new_rect.setLeft(r.left() + dx)
            elif self.active_handle == "right":
                new_rect.setRight(r.right() + dx)
            
            # Apply the new rect
            self.setRect(new_rect.normalized())
            
            # Accept the event to indicate we've handled it
            event.accept()
        else:
            # Regular drag operation
            super().mouseMoveEvent(event)
            
            # Update associated connections if this is a device
            # Note: For device drag movement, see the Device class
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release after resize or drag."""
        if self.active_handle:
            # End resize operation
            self.active_handle = None
            self.resize_start_rect = None
            self.resize_start_pos = None
            
            # Accept the event to prevent further processing
            event.accept()
            return
            
        # Pass to parent for regular release handling
        super().mouseReleaseEvent(event)
        
        # Check if this was a drag operation and notify interested parties
        if event.button() == Qt.LeftButton:
            # Track drag end for signals
            if hasattr(self, 'signals') and hasattr(self.signals, 'drag_finished'):
                self.signals.drag_finished.emit(self)
                
            # If connected to a canvas with a group selection manager, notify it
            canvas = self._get_canvas()
            if canvas and hasattr(canvas, 'group_selection_manager') and canvas.group_selection_manager:
                canvas.group_selection_manager.end_drag()
                
    def set_font_size(self, size):
        """Set the font size for the label."""
        if hasattr(self, 'label') and self.label:
            font = self.label.font()
            font.setPointSize(size)
            self.label.setFont(font)
            self.update()  # Force redraw
    
    def get_font_size(self):
        """Get the current font size of the label."""
        if hasattr(self, 'label') and self.label:
            return self.label.font().pointSize()
        return 10  # Default size
    
    def _get_canvas(self):
        """Get the canvas this boundary belongs to."""
        # Check if there's a scene
        scene = self.scene()
        if not scene:
            return None
            
        # Check scene's views
        views = scene.views()
        if not views:
            return None
            
        # The first view is typically the canvas
        return views[0]
    
    def _on_selection_timer(self):
        """Handle selection state change after debounce delay."""
        if self.pending_selection is not None:
            # Emit selection signal
            if hasattr(self, 'signals') and hasattr(self.signals, 'selected'):
                self.signals.selected.emit(self, bool(self.pending_selection))
            self.pending_selection = None 