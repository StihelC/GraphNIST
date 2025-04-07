import logging
import os
import qdarktheme
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QColor, QPalette

class ThemeManager:
    """Manages application themes (light and dark mode)."""
    
    # Theme constants
    LIGHT_THEME = "light"
    DARK_THEME = "dark"
    
    # Canvas color settings
    CANVAS_COLORS = {
        LIGHT_THEME: {
            "background": QColor(240, 240, 240),  # Light gray
            "grid": QColor(200, 200, 200),        # Light gray grid
        },
        DARK_THEME: {
            "background": QColor(45, 45, 45),      # Dark gray
            "grid": QColor(70, 70, 70),            # Slightly lighter gray for grid
        }
    }
    
    # Connection colors
    CONNECTION_COLORS = {
        LIGHT_THEME: {
            "base": QColor(70, 70, 70),           # Dark gray
            "hover": QColor(0, 120, 215),         # Blue
            "selected": QColor(255, 140, 0),      # Orange
        },
        DARK_THEME: {
            "base": QColor(180, 180, 180),        # Light gray
            "hover": QColor(0, 140, 255),         # Brighter blue
            "selected": QColor(255, 160, 0),      # Brighter orange
        }
    }
    
    def __init__(self):
        """Initialize the theme manager."""
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("GraphNIST", "GraphNIST")
        self.current_theme = self.settings.value("theme", self.LIGHT_THEME)
        
        # Store references to theme-aware widgets
        self.canvas = None
        self.theme_observers = []
        
        # Reference to event bus (will be set by main window)
        self.event_bus = None
    
    def set_event_bus(self, event_bus):
        """Set the event bus for theme change notifications."""
        self.event_bus = event_bus
    
    def apply_theme(self, app=None):
        """Apply the current theme to the application.
        
        Args:
            app: QApplication instance (optional)
        """
        try:
            # Fall back to getting the application instance if not provided
            if app is None:
                app = QApplication.instance()
            
            set_theme(app, self.current_theme)
            
            # Update all registered theme-aware widgets
            self._update_theme_aware_widgets()
            
            return True
        except Exception as e:
            self.logger.error(f"Error applying theme: {str(e)}")
            return False
    
    def toggle_theme(self, app=None):
        """Toggle between light and dark themes.
        
        Args:
            app: QApplication instance (optional)
        
        Returns:
            str: The new theme name
        """
        # Toggle the theme
        self.current_theme = self.DARK_THEME if self.current_theme == self.LIGHT_THEME else self.LIGHT_THEME
        
        # Save the theme preference
        self.settings.setValue("theme", self.current_theme)
        
        # Apply the new theme
        self.apply_theme(app)
        
        # Emit theme changed event if event bus is available
        if self.event_bus:
            self.event_bus.emit("theme_changed", self.current_theme)
            self.logger.info(f"Emitted theme_changed event: {self.current_theme}")
        
        return self.current_theme
    
    def get_theme(self):
        """Get the current theme name.
        
        Returns:
            str: The current theme name
        """
        return self.current_theme
    
    def is_dark_theme(self):
        """Check if dark theme is active.
        
        Returns:
            bool: True if dark theme is active, False otherwise
        """
        return self.current_theme == self.DARK_THEME
    
    def register_canvas(self, canvas):
        """Register a canvas to receive theme updates.
        
        Args:
            canvas: The Canvas widget to update when theme changes
        """
        self.canvas = canvas
    
    def register_theme_observer(self, observer):
        """Register an object to be notified of theme changes.
        
        The observer must have a method called update_theme(theme_name)
        
        Args:
            observer: Object with update_theme method
        """
        if hasattr(observer, 'update_theme') and callable(getattr(observer, 'update_theme')):
            self.theme_observers.append(observer)
        else:
            self.logger.warning(f"Observer {observer} does not have update_theme method")
    
    def _update_theme_aware_widgets(self):
        """Update all registered theme-aware widgets."""
        # Update canvas colors if registered
        if self.canvas:
            self._update_canvas_theme()
        
        # Notify all theme observers
        for observer in self.theme_observers:
            try:
                # Make sure the observer has the update_theme method
                if hasattr(observer, 'update_theme') and callable(getattr(observer, 'update_theme')):
                    # Apply theme update
                    observer.update_theme(self.current_theme)
                    
                    # Special handling for devices to ensure text visibility
                    if hasattr(observer, 'text_item') and observer.text_item:
                        # Set appropriate text color based on theme
                        text_color = QColor(240, 240, 240) if self.current_theme == self.DARK_THEME else QColor(0, 0, 0)
                        observer.text_item.setDefaultTextColor(text_color)
                        
                        # Update property label colors too
                        if hasattr(observer, 'property_labels'):
                            for label in observer.property_labels.values():
                                label.setDefaultTextColor(text_color)
                        
                        # Force a visual update
                        observer.update()
                        
                        # Force scene update if in a scene
                        if observer.scene():
                            scene = observer.scene()
                            update_rect = observer.sceneBoundingRect().adjusted(-5, -5, 5, 5)
                            scene.update(update_rect)
            except Exception as e:
                self.logger.error(f"Error updating observer {observer}: {str(e)}")
    
    def _update_canvas_theme(self):
        """Update the canvas colors based on current theme."""
        if not self.canvas:
            return
        
        try:
            # Get color settings for current theme
            colors = self.CANVAS_COLORS[self.current_theme]
            
            # Update canvas background color
            self.canvas.setBackgroundBrush(QColor(colors["background"]))
            
            # Update grid color
            self.canvas.grid_color = colors["grid"]
            
            # Force update
            self.canvas.viewport().update()
        except Exception as e:
            self.logger.error(f"Error updating canvas theme: {str(e)}")
    
    def get_connection_colors(self):
        """Get connection colors for the current theme.
        
        Returns:
            dict: Dictionary of connection colors
        """
        return self.CONNECTION_COLORS[self.current_theme]

def set_theme(app, theme_name):
    try:
        if theme_name.lower() == "dark":
            # Replace setup_theme with apply_stylesheet
            app.setStyleSheet(qdarktheme.load_stylesheet(theme="dark"))
        elif theme_name.lower() == "light":
            # Replace setup_theme with apply_stylesheet
            app.setStyleSheet(qdarktheme.load_stylesheet(theme="light"))
        else:
            # Default fallback theme handling
            app.setStyleSheet("")
    except Exception as e:
        import logging
        logging.error(f"Error applying theme: {str(e)}")