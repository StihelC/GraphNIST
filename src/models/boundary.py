from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PyQt5.QtGui import QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject, QTimer
import logging

class BoundarySignals(QObject):
    """Signals for the Boundary class."""
    name_changed = pyqtSignal(object, str)  # boundary, new_name
    selected = pyqtSignal(object, bool)  # boundary, is_selected

class EditableTextItem(QGraphicsTextItem):
    """An editable text item that supports interactive editing."""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFlag(QGraphicsTextItem.ItemIsSelectable, True)
        self._editable = False
        self._original_text = text
        
        # Style
        # Default to dark text, will update in refresh_theme
        self.setFont(QFont("Arial", 10, QFont.Bold))
        self.refresh_theme()
    
    def refresh_theme(self):
        """Update text color based on current theme."""
        # Check if our parent is a Boundary and it has theme info
        parent_boundary = self.parentItem()
        if parent_boundary and hasattr(parent_boundary, 'theme_manager') and parent_boundary.theme_manager:
            # Set appropriate color based on theme
            if parent_boundary.theme_manager.is_dark_theme():
                self.setDefaultTextColor(QColor(240, 240, 240, 220))  # Light color for dark theme
            else:
                self.setDefaultTextColor(QColor(20, 20, 20, 200))  # Dark color for light theme
        else:
            # Default to dark text if no theme info
            self.setDefaultTextColor(QColor(20, 20, 20, 200))
    
    def start_editing(self):
        """Make the text editable."""
        if not self._editable:
            self._editable = True
            self._original_text = self.toPlainText()
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setFocus()
    
    def finish_editing(self):
        """Finish editing and return to normal state."""
        if self._editable:
            self._editable = False
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.clearFocus()
            return self.toPlainText()
        return None
    
    def cancel_editing(self):
        """Cancel editing and revert changes."""
        if self._editable:
            self.setPlainText(self._original_text)
            self.finish_editing()
    
    def mouseDoubleClickEvent(self, event):
        """Enter edit mode on double click."""
        self.start_editing()
        super().mouseDoubleClickEvent(event)
    
    def focusOutEvent(self, event):
        """Complete editing when focus is lost."""
        if self._editable:
            new_text = self.finish_editing()
            # Notify parent of text change
            if self.parentItem() and hasattr(self.parentItem(), 'text_edited'):
                self.parentItem().text_edited(new_text)
        super().focusOutEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events during editing."""
        if self._editable:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # Apply changes on Enter
                new_text = self.finish_editing()
                # Notify parent of text change
                if self.parentItem() and hasattr(self.parentItem(), 'text_edited'):
                    self.parentItem().text_edited(new_text)
                return
            elif event.key() == Qt.Key_Escape:
                # Cancel editing on Escape
                self.cancel_editing()
                return
        super().keyPressEvent(event)

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
        
        # Set z-value to be behind everything else (layer 0)
        self.setZValue(0)
        
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
        
        # Apply visual style
        self._apply_style()
        
        # Create label
        self._create_label()
        
        # Setup for resizing
        self._setup_resize_handles()

    def _apply_style(self):
        """Apply visual styling to the boundary."""
        # Set border with semi-transparency
        self.setPen(QPen(QColor(self.color.red(), self.color.green(), 
                               self.color.blue(), 160), 2, Qt.SolidLine))
        
        # Set fill with transparency
        self.setBrush(QBrush(self.color))
    
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
        """Handle item changes, including selection state."""
        if change == QGraphicsItem.ItemSelectedChange:
            # Stop any pending timer
            self.selection_timer.stop()
            
            # Store the new selection state
            self.pending_selection = value
            
            # Start the debounce timer
            self.selection_timer.start(100)  # 100ms debounce
            
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event with visual feedback."""
        # Highlight boundary when hovering
        self.setPen(QPen(QColor(self.color.red(), self.color.green(), 
                               self.color.blue(), 220), 3, Qt.SolidLine))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        # Reset cursor and appearance when mouse leaves
        self.setCursor(Qt.ArrowCursor)
        self._apply_style()
        super().hoverLeaveEvent(event)
    
    def update_geometry(self, rect):
        """Update the boundary's rect."""
        self.setRect(rect)
        self._update_label_position()
    
    def delete(self):
        """Clean up resources before deletion."""
        # Store scene and rect before removal for updating
        scene = self.scene()
        update_rect = self.sceneBoundingRect().adjusted(-10, -10, 10, 10)
        
        # Remove the label first if it exists
        if hasattr(self, 'label') and self.label:
            if self.label.scene():
                # Include label area in update region
                if hasattr(self.label, 'boundingRect'):
                    label_rect = self.label.sceneBoundingRect()
                    update_rect = update_rect.united(label_rect)
                self.scene().removeItem(self.label)
            self.label = None
            
        # Emit signals or perform additional cleanup if needed
        if hasattr(self, 'signals'):
            # You might want to add a deleted signal in BoundarySignals class
            if hasattr(self.signals, 'deleted'):
                self.signals.deleted.emit(self)
        
        # Force update the scene area after deletion
        if scene:
            scene.update(update_rect)
            # Force update on all views
            for view in scene.views():
                view.viewport().update()

    def update_color(self):
        """Update boundary visual appearance after color change."""
        if hasattr(self, 'color'):
            # Apply the color to the boundary's brush and pen
            brush = self.brush()
            brush.setColor(self.color)
            self.setBrush(brush)
            
            # Update the pen too for consistent appearance
            pen = QPen(QColor(self.color.red(), self.color.green(), 
                             self.color.blue(), 160), 2, Qt.SolidLine)
            self.setPen(pen)
            
            # Force redraw
            self.update()

    def update_name(self):
        """Update the displayed name text."""
        if hasattr(self, 'label') and self.label:
            self.label.setPlainText(self.name)

    def update_theme(self, theme_name=None):
        """Update boundary styling based on the theme."""
        if hasattr(self, 'label') and self.label:
            self.label.refresh_theme()
            
    def get_theme_manager(self):
        """Try to find a theme manager if one isn't already set."""
        if self.theme_manager:
            return self.theme_manager
            
        # Try to get from scene
        scene = self.scene()
        if scene:
            # Try to get from scene views
            views = scene.views()
            if views:
                view = views[0]  # Get first view
                # Try to get from view
                if hasattr(view, 'theme_manager'):
                    self.theme_manager = view.theme_manager
                    return self.theme_manager
                # Try to get from view's parent
                if hasattr(view, 'parent') and callable(view.parent):
                    parent = view.parent()
                    if parent and hasattr(parent, 'theme_manager'):
                        self.theme_manager = parent.theme_manager
                        return self.theme_manager
        
        return None
    
    def _setup_resize_handles(self):
        """Set up resize handle properties and state."""
        # Define resize handle properties
        self._resizing = False
        self._resize_handle_size = 10
        self._resize_handle = None  # Will store which handle is being dragged
        self._resize_start_pos = None
        self._resize_start_rect = None
        
        # Define handle positions: NW, N, NE, E, SE, S, SW, W (8 handles)
        self._handles = ['NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W']
        
        # Handle cursors for each position
        self._handle_cursors = {
            'NW': Qt.SizeFDiagCursor,
            'SE': Qt.SizeFDiagCursor,
            'NE': Qt.SizeBDiagCursor,
            'SW': Qt.SizeBDiagCursor,
            'N': Qt.SizeVerCursor,
            'S': Qt.SizeVerCursor,
            'E': Qt.SizeHorCursor,
            'W': Qt.SizeHorCursor
        }
    
    def _get_handle_rect(self, handle):
        """Get the rectangle for a resize handle."""
        rect = self.rect()
        handle_size = self._resize_handle_size
        half_handle = handle_size / 2
        
        # Get the center points for the sides
        center_top = QPointF(rect.left() + rect.width() / 2, rect.top())
        center_bottom = QPointF(rect.left() + rect.width() / 2, rect.bottom())
        center_left = QPointF(rect.left(), rect.top() + rect.height() / 2)
        center_right = QPointF(rect.right(), rect.top() + rect.height() / 2)
        
        # Create handle rectangles based on position
        if handle == 'NW':
            return QRectF(rect.left(), rect.top(), handle_size, handle_size)
        elif handle == 'N':
            return QRectF(center_top.x() - half_handle, rect.top(), handle_size, handle_size)
        elif handle == 'NE':
            return QRectF(rect.right() - handle_size, rect.top(), handle_size, handle_size)
        elif handle == 'E':
            return QRectF(rect.right() - handle_size, center_right.y() - half_handle, handle_size, handle_size)
        elif handle == 'SE':
            return QRectF(rect.right() - handle_size, rect.bottom() - handle_size, handle_size, handle_size)
        elif handle == 'S':
            return QRectF(center_bottom.x() - half_handle, rect.bottom() - handle_size, handle_size, handle_size)
        elif handle == 'SW':
            return QRectF(rect.left(), rect.bottom() - handle_size, handle_size, handle_size)
        elif handle == 'W':
            return QRectF(rect.left(), center_left.y() - half_handle, handle_size, handle_size)
        
        return QRectF()
    
    def _handle_at_position(self, pos):
        """Determine if the given position is on a resize handle."""
        # Check if position is on any of the resize handles
        # Use a more generous hit area for easier selection
        for handle in self._handles:
            rect = self._get_handle_rect(handle)
            # Create a larger hit area for better touch/mouse interaction
            hit_rect = rect.adjusted(-5, -5, 5, 5)
            if hit_rect.contains(pos):
                return handle
        return None
    
    def paint(self, painter, option, widget):
        """Paint the boundary and its resize handles."""
        # Draw the standard boundary
        super().paint(painter, option, widget)
        
        # Only draw resize handles when properly selected
        if self.isSelected():
            # Check if we're in a rubber band selection
            canvas = self._get_canvas()
            if canvas and hasattr(canvas, '_rubber_band_rect') and canvas._rubber_band_rect:
                # Get the boundary's bounding rectangle
                boundary_rect = self.sceneBoundingRect()
                
                # Check if the boundary is completely contained within the selection rectangle
                if not canvas._rubber_band_rect.contains(boundary_rect):
                    # If not completely contained, don't show resize handles
                    return
            
            # Determine handle colors based on theme
            if self.theme_manager and self.theme_manager.is_dark_theme():
                painter.setPen(QPen(Qt.white, 1))
                painter.setBrush(QBrush(QColor(220, 220, 220)))
            else:
                painter.setPen(QPen(Qt.black, 1))
                painter.setBrush(QBrush(Qt.white))
            
            # Draw each resize handle
            for handle in self._handles:
                handle_rect = self._get_handle_rect(handle)
                painter.drawRect(handle_rect)
    
    def hoverMoveEvent(self, event):
        """Handle hover move events for showing appropriate cursor over resize handles."""
        # Only change cursor if selected
        if not self.isSelected():
            self.setCursor(Qt.ArrowCursor)
            return super().hoverMoveEvent(event)
        
        # Check if hovering over a resize handle
        handle = self._handle_at_position(event.pos())
        if handle:
            # Set the appropriate cursor based on handle position
            self.setCursor(self._handle_cursors[handle])
        else:
            # Reset to default cursor when not over a handle
            self.setCursor(Qt.ArrowCursor)
            
        super().hoverMoveEvent(event)
    
    def setRect(self, rect):
        """Override setRect to ensure resize operations are properly applied.
        
        This is a critical method to ensure resize handles work correctly.
        """
        # Call the parent method
        result = super().setRect(rect)
        
        # Since this method might be called during resize operations,
        # ensure we update associated items like labels
        self._update_label_position()
        
        # Force update to ensure visual appearance reflects the changes
        self.update()
        
        return result
    
    def mousePressEvent(self, event):
        """Handle mouse press events for selection and resizing."""
        # Only log important debug info
        if self.isSelected():
            self.logger.debug(f"Boundary '{self.name}' received mousePressEvent")
        
        # Convert coordinates properly - must use event.pos() which returns item coordinates
        pos = event.pos()
        
        # Ensure this boundary is selected to show properties panel
        self.setSelected(True)
        
        # Emit signal to show properties panel (if available)
        if hasattr(self, 'signals') and hasattr(self.signals, 'selected'):
            self.signals.selected.emit(self, True)
        
        # Check if clicking on a resize handle
        handle = self._handle_at_position(pos)
        
        if handle and self.isSelected():
            # Start resizing
            self._resizing = True
            self._resize_handle = handle
            self._resize_start_pos = pos
            self._resize_start_rect = self.rect()
            
            self.logger.debug(f"Starting resize operation with handle: {handle}")
            
            # Explicitly accept the event to indicate we're handling it
            event.accept()
            
            # Disable movement during resize
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            
            return  # Stop event propagation
        else:
            # Not resizing, proceed with normal selection/move
            self._resizing = False
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for resizing."""
        pos = event.pos()
        
        if self._resizing and self._resize_handle:
            # Calculate how much the mouse has moved
            delta = event.pos() - self._resize_start_pos
            
            # Create a copy of the start rect to modify
            new_rect = QRectF(self._resize_start_rect)
            
            # Update the rectangle based on which handle is being dragged
            if self._resize_handle == 'NW':
                new_rect.setTopLeft(new_rect.topLeft() + delta)
            elif self._resize_handle == 'N':
                new_rect.setTop(new_rect.top() + delta.y())
            elif self._resize_handle == 'NE':
                new_rect.setTopRight(new_rect.topRight() + delta)
            elif self._resize_handle == 'E':
                new_rect.setRight(new_rect.right() + delta.x())
            elif self._resize_handle == 'SE':
                new_rect.setBottomRight(new_rect.bottomRight() + delta)
            elif self._resize_handle == 'S':
                new_rect.setBottom(new_rect.bottom() + delta.y())
            elif self._resize_handle == 'SW':
                new_rect.setBottomLeft(new_rect.bottomLeft() + delta)
            elif self._resize_handle == 'W':
                new_rect.setLeft(new_rect.left() + delta.x())
            
            # Ensure minimum size
            if new_rect.width() < 50:
                if self._resize_handle in ['NW', 'W', 'SW']:
                    new_rect.setLeft(new_rect.right() - 50)
                else:
                    new_rect.setRight(new_rect.left() + 50)
                    
            if new_rect.height() < 50:
                if self._resize_handle in ['NW', 'N', 'NE']:
                    new_rect.setTop(new_rect.bottom() - 50)
                else:
                    new_rect.setBottom(new_rect.top() + 50)
            
            # Use our overridden setRect method to update the boundary
            self.prepareGeometryChange()  # Important for QGraphicsItem to handle resize properly
            self.setRect(new_rect)
            
            # Force scene update
            if self.scene():
                self.scene().update()
                
            # Explicitly accept the event
            event.accept()
        else:
            # Not resizing, proceed with normal movement
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events after resizing."""
        if self._resizing:
            # End resizing operation
            self.logger.debug(f"Completed resize operation with handle: {self._resize_handle}")
            
            self._resizing = False
            self._resize_handle = None
            
            # Re-enable moving
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            
            event.accept()
            
            # Maintain selection state and update cursor
            self.setSelected(True)
            handle = self._handle_at_position(event.pos())
            if handle:
                self.setCursor(self._handle_cursors[handle])
            else:
                self.setCursor(Qt.ArrowCursor)
                
            # Force an update to ensure proper rendering
            self.update()
        else:
            # Not resizing, proceed with normal release
            super().mouseReleaseEvent(event)

    def set_font_size(self, size):
        """Change the boundary label's font size."""
        if hasattr(self, 'label') and self.label:
            font = self.label.font()
            font.setPointSize(size)
            self.label.setFont(font)
            # Update label position to account for size change
            self._update_label_position()
    
    def get_font_size(self):
        """Get the boundary label's font size."""
        if hasattr(self, 'label') and self.label:
            return self.label.font().pointSize()
        return 10  # Default font size

    def _get_canvas(self):
        """Get the canvas view that contains this boundary."""
        # Get the scene
        scene = self.scene()
        if not scene:
            return None
            
        # Get the views of the scene
        views = scene.views()
        if not views:
            return None
            
        # Return the first view (should be the canvas)
        return views[0]

    def _on_selection_timer(self):
        """Handle selection after debounce delay."""
        if self.pending_selection is not None:
            is_selected = self.pending_selection
            self.pending_selection = None
            if hasattr(self.signals, 'selected'):
                self.signals.selected.emit(self, is_selected)

