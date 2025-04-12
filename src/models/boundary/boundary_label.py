from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

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