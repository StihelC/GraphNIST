import logging
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QCursor, QTransform
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsView

from .base_mode import CanvasMode

class MagnifyMode(CanvasMode):
    """Mode that provides a magnifying glass functionality."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.name = "Magnify"
        self.logger = logging.getLogger(__name__)
        
        # Magnification settings
        self.magnification_factor = 2.0
        self.lens_size = 150
        
        # Tracking variables
        self.active = False
        self.current_pos = None
        
        # Visual elements
        self.lens_item = None
        self.magnified_view = None
        self.border_pen = QPen(QColor(40, 40, 40), 2)
        self.lens_brush = QBrush(QColor(255, 255, 255, 40))
        
    def activate(self):
        """Prepare the magnify mode when activated."""
        self.canvas.setCursor(self.cursor())
        self.active = False
        
        # Initialize the lens as a circular shape
        self.lens_item = QGraphicsEllipseItem(0, 0, self.lens_size, self.lens_size)
        self.lens_item.setPen(self.border_pen)
        self.lens_item.setBrush(self.lens_brush)
        self.lens_item.setZValue(1000)  # Ensure it's drawn on top of everything
        self.lens_item.setVisible(False)
        self.canvas.scene().addItem(self.lens_item)
        
        self.logger.debug("Magnify mode activated")
    
    def deactivate(self):
        """Clean up when leaving magnify mode."""
        if self.lens_item:
            self.canvas.scene().removeItem(self.lens_item)
            self.lens_item = None
            
        self.active = False
        self.current_pos = None
        self.logger.debug("Magnify mode deactivated")
    
    def cursor(self):
        """Return the cursor to use for magnify mode."""
        return Qt.CrossCursor
    
    def mouse_press_event(self, event, scene_pos, item):
        """Handle mouse press - toggle magnification."""
        if event.button() == Qt.LeftButton:
            self.active = not self.active
            
            if self.active:
                self.current_pos = scene_pos
                self.update_lens_position(scene_pos)
                self.lens_item.setVisible(True)
            else:
                self.lens_item.setVisible(False)
                
            return True
        return False
    
    def mouse_move_event(self, event):
        """Update the magnification lens position as the mouse moves."""
        if self.active and self.lens_item:
            scene_pos = self.canvas.mapToScene(event.pos())
            self.current_pos = scene_pos
            self.update_lens_position(scene_pos)
            return True
        return False
    
    def mouse_release_event(self, event, scene_pos, item):
        """Handle mouse release events."""
        return False
    
    def update_lens_position(self, pos):
        """Update the lens position to follow the mouse."""
        if self.lens_item:
            # Center the lens on the cursor position
            half_size = self.lens_size / 2
            self.lens_item.setRect(pos.x() - half_size, pos.y() - half_size, 
                                   self.lens_size, self.lens_size)
            
            # Schedule a repaint to update the view with magnification
            self.canvas.viewport().update()
    
    def draw_magnified_content(self, painter):
        """Draw the magnified content when painting the canvas."""
        if not self.active or not self.current_pos:
            return
            
        # Get the lens rectangle in scene coordinates
        lens_rect = self.lens_item.rect()
        center = lens_rect.center()
        
        # Calculate the source rectangle (smaller area to be magnified)
        source_half_size = self.lens_size / (self.magnification_factor * 2)
        source_rect = QRectF(
            center.x() - source_half_size,
            center.y() - source_half_size,
            source_half_size * 2,
            source_half_size * 2
        )
        
        # Save the current state
        painter.save()
        
        # Set up clipping to the lens shape (circular)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setClipRect(lens_rect)
        
        # Calculate the viewport to scene transformation
        view_transform = self.canvas.transform()
        
        # Reset painter transform to paint directly on the viewport
        painter.resetTransform()
        
        # Calculate destination rectangle in viewport coordinates
        dest_rect = QRectF(
            view_transform.map(lens_rect.topLeft()),
            view_transform.map(lens_rect.bottomRight())
        )
        
        # Create a magnified transformation (QTransform doesn't have clone method)
        magnify_transform = QTransform(view_transform)
        
        # Scale the transformation from the center of the lens
        magnify_transform.scale(self.magnification_factor, self.magnification_factor)
        magnify_transform.translate(-center.x() * (self.magnification_factor - 1), 
                                 -center.y() * (self.magnification_factor - 1))
        
        # Set the magnified transformation for drawing
        painter.setTransform(magnify_transform)
        
        # Turn off clipping temporarily to allow drawing outside the lens when magnified
        painter.setClipping(False)
        
        # Render the magnified scene content
        self.canvas.scene().render(
            painter, 
            source=source_rect
        )
        
        # Draw a circular border to define the lens
        painter.resetTransform()
        painter.setClipRect(self.canvas.viewport().rect())
        painter.setPen(self.border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(view_transform.map(center), 
                           lens_rect.width() / 2 * view_transform.m11(),
                           lens_rect.height() / 2 * view_transform.m22())
        
        # Restore the painter state
        painter.restore() 