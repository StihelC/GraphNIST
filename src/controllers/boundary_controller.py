from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor
import logging
import traceback

from models.boundary import Boundary
from controllers.commands import AddBoundaryCommand, DeleteBoundaryCommand

class BoundaryController:
    """Controller for managing boundary-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.undo_redo_manager = undo_redo_manager
        
        # Get theme manager reference from canvas
        self.theme_manager = getattr(canvas, 'theme_manager', None)
        if not self.theme_manager:
            # Try to get from parent
            parent = getattr(canvas, 'parent', lambda: None)()
            if parent:
                self.theme_manager = getattr(parent, 'theme_manager', None)
        
        # Initialize boundary counter for naming
        self.boundary_counter = 0
        
        # Register with event bus for theme changes
        if self.event_bus:
            self.event_bus.on('theme_changed', self.update_boundaries_theme)
    
    def on_add_boundary_requested(self, rect, name=None, color=None):
        """Handle request to add a boundary with the given rect."""
        # Use command pattern if undo_redo_manager is available
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = AddBoundaryCommand(self, rect, name, color)
            self.undo_redo_manager.push_command(command)
            return command.created_boundary
        else:
            # Original implementation
            return self.create_boundary(rect, name, color)
    
    def on_delete_boundary_requested(self, boundary):
        """Handle request to delete a specific boundary."""
        # Use command pattern if undo_redo_manager is available and not already in command
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = DeleteBoundaryCommand(self, boundary)
            self.undo_redo_manager.push_command(command)
        else:
            # Original implementation
            if boundary:
                self.logger.info(f"Deleting boundary '{boundary.name}'")
                
                # Use the boundary's delete method to ensure label is properly removed
                if hasattr(boundary, 'delete'):
                    boundary.delete()
                else:
                    # Fallback if delete method not available
                    if hasattr(boundary, 'label') and boundary.label:
                        self.canvas.scene().removeItem(boundary.label)
                
                # Remove from scene
                self.canvas.scene().removeItem(boundary)
                
                # Remove from boundaries list
                if boundary in self.canvas.boundaries:
                    self.canvas.boundaries.remove(boundary)
                
                # Notify through event bus
                self.event_bus.emit("boundary_deleted", boundary)
    
    def create_boundary(self, rect, name=None, color=None):
        """Create a new boundary with the given parameters."""
        # Implementation for creating a boundary directly
        # Will be used by both normal calls and from commands
        from models.boundary import Boundary
        from PyQt5.QtGui import QColor
        
        # Use default name if none provided
        if not name:
            name = f"Boundary {len(self.canvas.boundaries) + 1}"
        
        # Use default color if none provided
        if not color:
            color = QColor(40, 120, 200, 80)
        
        # Create the boundary with theme manager
        boundary = Boundary(rect, name, color, theme_manager=self.theme_manager)
        
        # Add to scene
        self.canvas.scene().addItem(boundary)
        
        # Add to boundaries list
        self.canvas.boundaries.append(boundary)
        
        self.logger.info(f"Created boundary '{name}'")
        
        # Notify through event bus
        self.event_bus.emit("boundary_created", boundary)
        
        # Register with theme manager if available
        if self.theme_manager and hasattr(self.theme_manager, 'register_theme_observer'):
            self.theme_manager.register_theme_observer(boundary)
        
        return boundary
    
    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)

    def update_boundaries_theme(self, theme_name=None):
        """Update all boundaries with the current theme."""
        if not self.theme_manager:
            return
            
        self.logger.info(f"Updating boundaries for theme: {theme_name or self.theme_manager.get_theme()}")
        
        # Update all boundaries on the canvas
        for boundary in getattr(self.canvas, 'boundaries', []):
            # Ensure boundary has theme manager
            if not hasattr(boundary, 'theme_manager') or boundary.theme_manager is None:
                boundary.theme_manager = self.theme_manager
                
            # Update theme
            if hasattr(boundary, 'update_theme'):
                boundary.update_theme(theme_name)
