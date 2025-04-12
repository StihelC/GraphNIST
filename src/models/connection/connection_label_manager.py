from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtGui import QFont, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QPointF, QRectF
import logging

class EditableTextItem(QGraphicsTextItem):
    """A text item that can be edited and has a background."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setFlag(QGraphicsTextItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsTextItem.ItemIsFocusable, True)
        
        # Background appearance
        self.background_color = QColor(255, 255, 255, 220)  # Slightly transparent white
        self.border_color = QColor(200, 200, 200)
        self.background_padding = 4  # Padding around text
        
        # Store reference to the label manager
        self.label_manager = None
        
        # Add a hover state
        self.hover = False
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        self.hover = True
        # Show a different cursor to indicate editability
        self.setCursor(Qt.IBeamCursor)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        self.hover = False
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
        
    def paint(self, painter, option, widget):
        """Paint a background rect behind the text."""
        # Draw background rectangle
        painter.save()
        
        # Different background color when hovered
        if self.hover:
            painter.setBrush(QColor(245, 245, 245, 240))  # Slightly brighter when hovered
            painter.setPen(QPen(QColor(180, 180, 180), 1.5))  # Darker border when hovered
        else:
            painter.setBrush(self.background_color)
            painter.setPen(QPen(self.border_color, 1))
        
        # Get text rect with padding
        rect = self.boundingRect()
        bg_rect = rect.adjusted(
            -self.background_padding, 
            -self.background_padding, 
            self.background_padding, 
            self.background_padding
        )
        
        # Draw rounded rectangle
        painter.drawRoundedRect(bg_rect, 3, 3)
        painter.restore()
        
        # Draw the text
        super().paint(painter, option, widget)
    
    def boundingRect(self):
        """Return bounding rectangle including background padding."""
        rect = super().boundingRect()
        # Expand the rect to include the background padding
        return QRectF(
            rect.x() - self.background_padding,
            rect.y() - self.background_padding,
            rect.width() + (self.background_padding * 2),
            rect.height() + (self.background_padding * 2)
        )
        
    def mouseDoubleClickEvent(self, event):
        """Enter edit mode on double click."""
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus()
        # Position cursor at click position
        super().mouseDoubleClickEvent(event)
        
    def focusOutEvent(self, event):
        """Finish editing when focus is lost."""
        # Disable text editing when focus is lost
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        
        # Notify parent of text change
        if self.parentItem() and hasattr(self.parentItem(), 'on_label_edited'):
            self.parentItem().on_label_edited(self.toPlainText())
        elif self.label_manager:
            # Notify the connection label manager
            self.label_manager.on_label_edited(self.toPlainText())
            
        super().focusOutEvent(event)
        
    def keyPressEvent(self, event):
        """Handle Enter key to finish editing."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.clearFocus()  # This will trigger focusOutEvent
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        super().mouseReleaseEvent(event)
        
        # Make sure the parent connection stays selected
        if self.parentItem():
            self.parentItem().setSelected(True)
    
    def parentObject(self):
        """This method is no longer needed."""
        return self.label_manager

class ConnectionLabelManager:
    """Manages label creation and positioning for connections."""
    
    def __init__(self, connection):
        """Initialize with reference to parent connection."""
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        
        # Label properties
        self.label = None
        self._label_text = "Link"  # Default label text
        self.text_color = QColor(40, 40, 40)  # Near black
        
        # Create the label
        self.create_label()
        
    @property
    def label_text(self):
        """Get the label text."""
        return self._label_text
    
    @label_text.setter
    def label_text(self, value):
        """Set the label text and update the label."""
        # Ensure the value isn't a QPointF object
        if isinstance(value, QPointF):
            self.logger.warning(f"Attempted to set label_text to QPointF: {value}")
            return
            
        self._label_text = value
        
        # Update the label if it exists
        if self.label:
            self.label.setPlainText(self._label_text)
            self.update_position()
    
    def create_label(self):
        """Create or update the connection label."""
        if not self.label:
            # Use our custom EditableTextItem instead of plain QGraphicsTextItem
            self.label = EditableTextItem(self.connection)
            # Set reference to this label manager
            self.label.label_manager = self
            
            # Style the label
            self.label.setDefaultTextColor(self.text_color)
            font = QFont()
            font.setPointSize(8)
            self.label.setFont(font)
            
            # Make sure the label is focusable and accepts hover events
            self.label.setFlag(self.label.ItemIsFocusable, True)
            self.label.setAcceptHoverEvents(True)
        
        # Set the text - safely
        if hasattr(self, '_label_text') and self._label_text and not isinstance(self._label_text, QPointF):
            self.label.setPlainText(self._label_text)
        else:
            # Default label
            self.label.setPlainText("Link")
        
        # Position the label
        self.update_position()
    
    def update_position(self):
        """Place label at center of connection path."""
        try:
            # First check if label exists
            if not hasattr(self, 'label') or self.label is None:
                return
                
            # Get path center point - use safe access to path
            path = self.connection.path()
            if path and not path.isEmpty():
                # Calculate center point of the path
                center_point = path.pointAtPercent(0.5)
                
                # Get actual text dimensions without the background padding
                text_rect = self.label.document().documentLayout().documentSize()
                text_width = text_rect.width()
                text_height = text_rect.height()
                
                # Position label at center point, offset by half its text dimensions
                self.label.setPos(
                    center_point.x() - text_width/2,
                    center_point.y() - text_height/2
                )
            else:
                # Fallback if no valid path exists
                source_port = getattr(self.connection, '_source_port', None)
                target_port = getattr(self.connection, '_target_port', None)
                
                if source_port and target_port:
                    # Use midpoint between source and target ports
                    mid_x = (source_port.x() + target_port.x()) / 2
                    mid_y = (source_port.y() + target_port.y()) / 2
                    
                    # Get actual text dimensions
                    text_rect = self.label.document().documentLayout().documentSize()
                    text_width = text_rect.width()
                    text_height = text_rect.height()
                    
                    self.label.setPos(
                        mid_x - text_width/2,
                        mid_y - text_height/2
                    )
        except Exception as e:
            self.logger.error(f"Error updating label position: {str(e)}")
    
    def on_label_edited(self, new_text):
        """Handle when the label text has been edited."""
        self._label_text = new_text
        
        # Update any properties dictionary on the connection
        if hasattr(self.connection, 'properties') and isinstance(self.connection.properties, dict):
            # Use the standard "label_text" property instead of adding a duplicate "Label" property
            self.connection.properties["label_text"] = new_text 