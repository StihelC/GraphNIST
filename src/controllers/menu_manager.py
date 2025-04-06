from PyQt5.QtWidgets import QToolBar, QAction, QMenu, QActionGroup, QToolButton
from PyQt5.QtCore import Qt
import logging

from constants import Modes, DeviceTypes
from models.connection import Connection

class MenuManager:
    """Manager for creating and managing all menus and toolbars."""
    
    def __init__(self, main_window, canvas, event_bus):
        self.main_window = main_window
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Store mode actions for enabling/disabling
        self.mode_actions = {}
    
    def _create_connection_menu(self):
        """Create connection style menu."""
        connection_menu = self.menuBar().addMenu("&Connection")
        
        # Add connection style submenu
        style_menu = connection_menu.addMenu("Routing Style")
        
        # Straight style
        from models.connection import Connection
        straight_action = style_menu.addAction("Straight")
        straight_action.triggered.connect(
            lambda checked, s=Connection.STYLE_STRAIGHT: self.main_window.connection_controller.set_connection_style(s))
        
        # Orthogonal style
        orthogonal_action = style_menu.addAction("Orthogonal")
        orthogonal_action.triggered.connect(
            lambda checked, s=Connection.STYLE_ORTHOGONAL: self.main_window.connection_controller.set_connection_style(s))
        
        # Curved style
        curved_action = style_menu.addAction("Curved")
        curved_action.triggered.connect(
            lambda checked, s=Connection.STYLE_CURVED: self.main_window.connection_controller.set_connection_style(s))
        
        # Connection appearance submenu
        appearance_menu = connection_menu.addMenu("Appearance")
        
        # Connection type actions that define the visual style
        from constants import ConnectionTypes
        for conn_type, display_name in ConnectionTypes.DISPLAY_NAMES.items():
            type_action = appearance_menu.addAction(display_name)
            type_action.triggered.connect(
                lambda checked, t=conn_type: self.main_window.connection_controller.set_connection_type(t))
    
    def update_mode_actions(self, current_mode):
        """Update checked state of mode actions."""
        for mode, action in self.mode_actions.items():
            action.setChecked(mode == current_mode)
