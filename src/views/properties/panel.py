from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QScrollArea, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
import logging

from models.device import Device
from models.connection import Connection  
from models.boundary import Boundary

from .general_section import GeneralSection
from .device_section import DeviceSection
from .connection_section import ConnectionSection
from .boundary_section import BoundarySection

class PropertiesPanel(QWidget):
    """A panel for displaying and editing properties of selected items."""
    
    # Signals for property changes
    name_changed = pyqtSignal(str)
    z_value_changed = pyqtSignal(float)
    device_property_changed = pyqtSignal(str, object)
    connection_property_changed = pyqtSignal(str, object)
    boundary_property_changed = pyqtSignal(str, object)
    change_icon_requested = pyqtSignal(object)
    property_display_toggled = pyqtSignal(str, bool)
    property_delete_requested = pyqtSignal(str)
    device_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)  # Increased minimum width for better readability
        self.current_item = None
        self.current_items = []
        self.boundary_devices = []
        
        # Initialize UI components as None
        self.tab_widget = None
        self.content_layout = None
        self.content_widget = None
        self.no_selection_label = None
        
        # Section panels
        self.general_section = None
        self.device_section = None
        self.connection_section = None
        self.boundary_section = None
        
        # Initialize the UI
        self._init_ui()
        
        # Connect section signals
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the UI elements."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # Scrollable area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        
        # Title for the panel
        title = QLabel("Properties")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 16px;
                color: #2c3e50;
                padding: 5px;
                border-bottom: 2px solid #3498db;
            }
        """)
        self.content_layout.addWidget(title)
        
        # Create tab widget for organizing properties
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: #f8f9fa;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
        
        # Create section panels only if they don't exist
        if not self.general_section:
            self.general_section = GeneralSection()
        if not self.device_section:
            self.device_section = DeviceSection()
        if not self.connection_section:
            self.connection_section = ConnectionSection()
        if not self.boundary_section:
            self.boundary_section = BoundarySection()
        
        # Add sections to the tab widget (clear it first to avoid duplicates)
        if self.tab_widget.count() > 0:
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
        
        self.tab_widget.addTab(self.general_section, "General")
        self.tab_widget.addTab(self.device_section, "Devices")
        self.tab_widget.addTab(self.connection_section, "Connections")
        self.tab_widget.addTab(self.boundary_section, "Boundaries")
        
        # Connect section signals
        self._connect_signals()
        
        # Add tab widget to layout
        self.content_layout.addWidget(self.tab_widget)
        self.content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
        
        # Create the no selection label
        self.no_selection_label = QLabel("No item selected")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.content_layout.addWidget(self.no_selection_label)
        self.no_selection_label.hide()  # Hide by default
        
        # Disable all specific tabs by default
        self._disable_all_tabs()
    
    def _connect_signals(self):
        """Connect signals from section panels to this panel's signals."""
        # Connect general section signals
        self.general_section.name_changed.connect(self.name_changed)
        self.general_section.z_value_changed.connect(self.z_value_changed)
        
        # Connect device section signals
        self.device_section.property_changed.connect(self.device_property_changed)
        self.device_section.display_toggled.connect(self.property_display_toggled)
        self.device_section.property_deleted.connect(self.property_delete_requested)
        self.device_section.change_icon_requested.connect(self.change_icon_requested)
        
        # Connect connection section signals
        self.connection_section.property_changed.connect(self.connection_property_changed)
        
        # Connect boundary section signals
        self.boundary_section.property_changed.connect(self.boundary_property_changed)
        self.boundary_section.device_selected.connect(self.device_selected)
    
    def _disable_all_tabs(self):
        """Disable all specific tabs."""
        if self.tab_widget:
            self.tab_widget.setTabEnabled(1, False)  # Devices tab
            self.tab_widget.setTabEnabled(2, False)  # Connections tab
            self.tab_widget.setTabEnabled(3, False)  # Boundaries tab
    
    def _check_ui_initialized(self):
        """Check if UI components are initialized and create them if needed."""
        if not self.general_section or not self.device_section or not self.connection_section or not self.boundary_section:
            # Create section panels if they don't exist
            try:
                if not self.general_section:
                    self.general_section = GeneralSection()
                if not self.device_section:
                    self.device_section = DeviceSection()
                if not self.connection_section:
                    self.connection_section = ConnectionSection()
                if not self.boundary_section:
                    self.boundary_section = BoundarySection()
                
                # Clear the tab widget if it exists
                if self.tab_widget and self.tab_widget.count() > 0:
                    while self.tab_widget.count() > 0:
                        self.tab_widget.removeTab(0)
                
                # Add sections to the tab widget
                if self.tab_widget:
                    self.tab_widget.addTab(self.general_section, "General")
                    self.tab_widget.addTab(self.device_section, "Devices")
                    self.tab_widget.addTab(self.connection_section, "Connections")
                    self.tab_widget.addTab(self.boundary_section, "Boundaries")
                    
                # Reconnect signals if needed
                self._connect_signals()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error initializing UI components: {str(e)}")
    
    def set_item(self, item):
        """Set the current item and update the panel."""
        logger = logging.getLogger(__name__)
        try:
            # Ensure UI is initialized
            self._check_ui_initialized()
            
            self.current_item = item
            self.current_items = []
            
            # Hide the no selection label
            if self.no_selection_label:
                self.no_selection_label.setVisible(False)
            
            # Reset all sections
            if self.general_section:
                self.general_section.reset()
            if self.device_section:
                self.device_section.reset()
            if self.connection_section:
                self.connection_section.reset()
            if self.boundary_section:
                self.boundary_section.reset()
            
            # Update general properties that all items share
            if hasattr(item, 'name') and self.general_section:
                self.general_section.set_name(item.name)
            
            # Update Z-value (layer)
            if hasattr(item, 'zValue') and self.general_section:
                self.general_section.set_z_value(int(item.zValue()))
            
            # Show specific properties based on item type
            if isinstance(item, Device):
                logger.info("PANEL DEBUG: Item is a Device, showing device properties")
                if self.tab_widget:
                    self.tab_widget.setTabEnabled(1, True)  # Devices tab
                    self.tab_widget.setTabEnabled(2, False)  # Connections tab
                    self.tab_widget.setTabEnabled(3, False)  # Boundaries tab
                if self.device_section:
                    self.device_section.set_device(item)
            elif isinstance(item, Connection):
                logger.info("PANEL DEBUG: Item is a Connection, showing connection properties")
                if self.tab_widget:
                    self.tab_widget.setTabEnabled(1, False)  # Devices tab
                    self.tab_widget.setTabEnabled(2, True)  # Connections tab
                    self.tab_widget.setTabEnabled(3, False)  # Boundaries tab
                if self.connection_section:
                    self.connection_section.set_connection(item)
            elif isinstance(item, Boundary):
                logger.info("PANEL DEBUG: Item is a Boundary, showing boundary properties")
                if self.tab_widget:
                    self.tab_widget.setTabEnabled(1, False)  # Devices tab
                    self.tab_widget.setTabEnabled(2, False)  # Connections tab
                    self.tab_widget.setTabEnabled(3, True)  # Boundaries tab
                if self.boundary_section:
                    self.boundary_section.set_boundary(item)
            else:
                logger.info(f"PANEL DEBUG: Unknown item type: {type(item).__name__}")
                # Disable all specific tabs for unknown types
                self._disable_all_tabs()
                
        except Exception as e:
            logger.error(f"Error in set_item: {str(e)}")
            self._disable_all_tabs()
    
    def display_item_properties(self, item):
        """Alias for set_item to maintain backward compatibility."""
        self.set_item(item)
    
    def set_boundary_contained_devices(self, devices):
        """Set the list of devices contained within the selected boundary."""
        self.boundary_devices = devices
        
        # If a boundary is currently selected, update its display
        if self.current_item and isinstance(self.current_item, Boundary):
            self.boundary_section.set_contained_devices(devices)
    
    def show_mixed_selection(self, items):
        """Display interface for editing mixed selection of items."""
        try:
            logger = logging.getLogger(__name__)
            
            # Ensure UI is initialized
            self._check_ui_initialized()
            
            # Clear single item reference
            self.current_item = None
            self.current_items = items
            
            # Hide the no selection label
            if self.no_selection_label:
                self.no_selection_label.setVisible(False)
            
            # Reset all sections
            if self.general_section:
                self.general_section.reset()
            if self.device_section:
                self.device_section.reset()
            if self.connection_section:
                self.connection_section.reset()
            if self.boundary_section:
                self.boundary_section.reset()
            
            # Extract items by type
            devices = [item for item in items if isinstance(item, Device)]
            connections = [item for item in items if isinstance(item, Connection)]
            boundaries = [item for item in items if isinstance(item, Boundary)]
            
            # Set the header based on selected items
            header_text = []
            if devices:
                header_text.append(f"{len(devices)} Devices")
            if connections:
                header_text.append(f"{len(connections)} Connections")
            if boundaries:
                header_text.append(f"{len(boundaries)} Boundaries")
                
            # Set tab enabled states
            if self.tab_widget:
                self.tab_widget.setTabEnabled(0, True)  # General tab
                self.tab_widget.setTabEnabled(1, bool(devices))  # Devices tab
                self.tab_widget.setTabEnabled(2, bool(connections))  # Connections tab
                self.tab_widget.setTabEnabled(3, bool(boundaries))  # Boundaries tab
                
                # Switch to the first enabled tab
                for i in range(4):
                    if self.tab_widget.isTabEnabled(i):
                        self.tab_widget.setCurrentIndex(i)
                        break
            
            # Update sections with multiple items
            if devices and self.device_section:
                self.device_section.set_multiple_devices(devices)
            if connections and self.connection_section:
                self.connection_section.set_multiple_connections(connections)
            if boundaries and self.boundary_section:
                self.boundary_section.set_multiple_boundaries(boundaries)
                
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in show_mixed_selection: {str(e)}")
            self._disable_all_tabs()
    
    def show_multiple_devices(self, devices):
        """Alias for show_mixed_selection to maintain backward compatibility."""
        self.show_mixed_selection([device for device in devices if isinstance(device, Device)])
    
    def clear(self):
        """Clear all content from the properties panel."""
        logger = logging.getLogger(__name__)
        try:
            # Reset current item reference
            self.current_item = None
            self.current_items = []
            self.boundary_devices = []
            
            # Reset all sections
            if self.general_section:
                self.general_section.reset()
            if self.device_section:
                self.device_section.reset()
            if self.connection_section:
                self.connection_section.reset()
            if self.boundary_section:
                self.boundary_section.reset()
            
            # Disable all specific tabs
            self._disable_all_tabs()
            
            # Show the no selection label
            if self.no_selection_label:
                self.no_selection_label.setVisible(True)
                
        except Exception as e:
            logger.error(f"Error in clear: {str(e)}") 