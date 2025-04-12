import logging
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor

from views.canvas.modes.base_mode import CanvasMode
from ..graphics_manager import TemporaryGraphicsManager

class AddBoundaryMode(CanvasMode):
    """Mode for adding boundaries to the canvas."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.logger = logging.getLogger(__name__)
        self.start_pos = None
        self.current_rect = None
        self.is_drawing = False
        self.name = "Add Boundary Mode"  # Add explicit name for this mode
    
    def handle_mouse_press(self, event, scene_pos, item):
        """Start drawing a boundary."""
        if event.button() == Qt.LeftButton:
            self.start_pos = scene_pos
            self.is_drawing = True
            self.logger.debug(f"AddBoundaryMode: Starting boundary at {scene_pos.x():.1f}, {scene_pos.y():.1f}")
            
            # Make sure we're not blocked by selection signals
            if hasattr(self.canvas, 'blockSignals'):
                was_blocked = self.canvas.signalsBlocked()
                self.canvas.blockSignals(True)
                self.canvas.blockSignals(was_blocked)
                
            return True
        return False
        
    def mouse_move_event(self, event):
        """Update boundary preview while drawing."""
        if self.is_drawing and self.start_pos:
            scene_pos = self.canvas.mapToScene(event.pos())
            rect = QRectF(self.start_pos, scene_pos).normalized()
            
            # Show preview rectangle
            if self.current_rect:
                self.canvas.temp_graphics.update_rect(self.current_rect, rect)
            else:
                # Create a semi-transparent blue preview rectangle
                pen = QPen(QColor(30, 120, 255, 200), 2, Qt.SolidLine)
                brush = QBrush(QColor(30, 120, 255, 80))
                self.current_rect = self.canvas.temp_graphics.add_rect(rect, pen, brush)
                
            return True
        return False
        
    def mouse_release_event(self, event, scene_pos=None, item=None):
        """Finish drawing the boundary."""
        if self.is_drawing and event.button() == Qt.LeftButton and self.start_pos:
            # If scene_pos is not provided, get it from the event
            if scene_pos is None:
                scene_pos = self.canvas.mapToScene(event.pos())
                
            rect = QRectF(self.start_pos, scene_pos).normalized()
            
            # Cache current rect for cleanup
            tmp_rect = self.current_rect
            
            # Reset state immediately
            self.is_drawing = False
            self.start_pos = None
            self.current_rect = None
            
            # Remove temporary graphics
            if tmp_rect is not None:
                self.canvas.temp_graphics.remove_item(tmp_rect)
            
            # Only create if the rectangle has sufficient size
            if rect.width() > 10 and rect.height() > 10:
                # Create boundary directly
                if hasattr(self.canvas, 'add_boundary_requested'):
                    try:
                        self.logger.info(f"AddBoundaryMode: Emitting add_boundary_requested with rect {rect.x():.1f},{rect.y():.1f} size {rect.width():.1f}x{rect.height():.1f}")
                        self.canvas.add_boundary_requested.emit(rect)
                    except Exception as e:
                        self.logger.error(f"Error emitting add_boundary_requested: {str(e)}")
                        # Try direct creation as fallback only if signal emission fails
                        self._create_boundary(rect)
                else:
                    self.logger.error("AddBoundaryMode: No add_boundary_requested signal available")
                    # Try direct creation as fallback
                    self._create_boundary(rect)
            
            return True
        
        return False

    def _create_boundary(self, rect):
        """Create a boundary with the given rect."""
        # IMPORTANT: Temporarily disable selection signals to prevent selection manager interference
        was_blocked = False
        if hasattr(self.canvas, 'blockSignals'):
            was_blocked = self.canvas.signalsBlocked()
            self.canvas.blockSignals(True)
            
        try:
            self.logger.debug(f"AddBoundaryMode: Creating boundary {rect.x():.1f},{rect.y():.1f} {rect.width():.1f}x{rect.height():.1f}")
            
            # If signal approach failed, try direct creation as fallback
            if hasattr(self.canvas, 'parent') and self.canvas.parent():
                try:
                    main_window = self.canvas.parent()
                    if hasattr(main_window, 'boundary_controller') and main_window.boundary_controller:
                        self.logger.debug("AddBoundaryMode: Attempting direct boundary creation through controller")
                        boundary = main_window.boundary_controller.create_boundary(rect)
                        if boundary:
                            self.logger.info("AddBoundaryMode: Successfully created boundary through direct controller call")
                            
                            # Force scene update to ensure boundary visibility
                            update_rect = rect.adjusted(-50, -50, 50, 50)
                            self.canvas.scene().update(update_rect)
                            self.canvas.viewport().update()
                except Exception as e:
                    self.logger.error(f"AddBoundaryMode: Error in direct boundary creation: {str(e)}")
                    import traceback
                    self.logger.error(traceback.format_exc())
                
        finally:
            # Always restore signal blocking state
            if hasattr(self.canvas, 'blockSignals'):
                self.canvas.blockSignals(was_blocked)
            
            # Final force update
            self.canvas.viewport().update()
        
    def cursor(self):
        """Use crosshair cursor for boundary drawing."""
        return Qt.CrossCursor
