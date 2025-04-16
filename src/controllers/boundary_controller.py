from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor
import logging
import traceback

from models.boundary.boundary import Boundary
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
            
        # Connect to canvas signals if they exist
        # These connections are now handled in main_window.py to prevent duplicates
        # if hasattr(canvas, 'add_boundary_requested'):
        #     self.canvas.add_boundary_requested.connect(self.on_add_boundary_requested)
        #     self.logger.info("Connected to canvas add_boundary_requested signal")
        
        # if hasattr(canvas, 'delete_boundary_requested'):
        #     self.canvas.delete_boundary_requested.connect(self.on_delete_boundary_requested)
        #     self.logger.info("Connected to canvas delete_boundary_requested signal")
    
    def on_add_boundary_requested(self, rect, name=None, color=None):
        """Handle request to add a boundary with the given rect."""
        self.logger.info(f"Adding boundary at rect {rect.x()},{rect.y()} size {rect.width()}x{rect.height()}")
        
        # Use command pattern if undo_redo_manager is available
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            command = AddBoundaryCommand(self, rect, name, color)
            self.undo_redo_manager.push_command(command)
            boundary = command.created_boundary
            
            # Debug output
            if boundary:
                self.logger.info(f"Created boundary '{boundary.name}' using command")
                return boundary
            else:
                self.logger.error("Failed to create boundary with command")
                # Fall back to direct creation
                return self.create_boundary(rect, name, color)
        else:
            # Direct creation as fallback
            boundary = self.create_boundary(rect, name, color)
            if boundary:
                self.logger.info(f"Created boundary '{boundary.name}' directly")
            else:
                self.logger.error("Failed to create boundary directly")
            return boundary
    
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
        try:
            self.logger.info(f"Creating boundary at rect {rect.x()},{rect.y()} size {rect.width()}x{rect.height()}")
            
            # Use default name and color if not provided
            if not name:
                name = f"Boundary {len(self.canvas.boundaries) + 1}"
            if not color:
                color = QColor(60, 150, 230, 120)  # Brighter blue with higher opacity
            
            # Create the boundary
            boundary = Boundary(rect, name, color, theme_manager=self.theme_manager)
            
            # Ensure good visibility
            boundary.setVisible(True)
            boundary.setZValue(0)
            boundary.setOpacity(1.0)
            
            # Add to scene
            scene = self.canvas.scene()
            if not scene:
                self.logger.error("No scene available to add boundary to")
                return None
                
            self.logger.debug(f"Adding boundary to scene at {rect.x()},{rect.y()}")
            scene.addItem(boundary)
            
            # Add to boundaries list
            if not hasattr(self.canvas, 'boundaries'):
                self.logger.warning("Canvas has no boundaries list, creating it")
                self.canvas.boundaries = []
                
            self.logger.debug(f"Adding boundary to canvas.boundaries list (current count: {len(self.canvas.boundaries)})")
            self.canvas.boundaries.append(boundary)
            
            # Register with theme manager
            if self.theme_manager and hasattr(self.theme_manager, 'register_theme_observer'):
                self.theme_manager.register_theme_observer(boundary)
            
            # Notify through event bus
            if self.event_bus:
                self.event_bus.emit("boundary_created", boundary)
            
            # Force update to ensure visibility
            scene.update(boundary.sceneBoundingRect().adjusted(-20, -20, 20, 20))
            self.canvas.viewport().update()
            
            self.logger.info(f"Successfully created boundary '{name}', total count: {len(self.canvas.boundaries)}")
            return boundary
        except Exception as e:
            self.logger.error(f"Error creating boundary: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
    
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

    def delete_boundary(self, boundary):
        """Delete a boundary from the canvas."""
        try:
            if boundary in self.canvas.boundaries:
                # Remove from canvas
                self.canvas.boundaries.remove(boundary)
                
                # Remove from scene if it's in a scene
                if boundary.scene():
                    # Remove all child items first
                    for child in boundary.childItems():
                        if child.scene():
                            child.scene().removeItem(child)
                    
                    # Remove the boundary itself
                    boundary.scene().removeItem(boundary)
                
                # Emit signal
                self.event_bus.emit("boundary_deleted", boundary)
                
                self.logger.info(f"Deleting boundary '{boundary.name}'")
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting boundary: {str(e)}")
            return False
