from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter, 
                         QAction, QMenu, QToolBar, QStatusBar, QMessageBox, QFileDialog,
                         QLabel, QSpinBox, QDialog, QDialogButtonBox, QGroupBox, QFormLayout, QDockWidget, QSizePolicy, QToolButton,
                         QActionGroup, QApplication, QInputDialog, QColorDialog, QTreeView, QTreeWidget, QTreeWidgetItem, QFrame,
                         QFontDialog)
from PyQt5.QtCore import Qt, QSettings, QTimer, QPoint, QByteArray, QSize, QSizeF, QPointF, QRect, QRectF
from PyQt5.QtGui import QIcon, QKeySequence, QColor, QFont, QPalette, QPainter, QImage, QPdfWriter
import logging
import os
from PyQt5.QtPrintSupport import QPrinter

from utils import theme_manager
from views.canvas.canvas import Canvas
from constants import Modes
from controllers.menu_manager import MenuManager
from controllers.device_controller import DeviceController
from controllers.connection_controller import ConnectionController
from controllers.boundary_controller import BoundaryController
from controllers.clipboard_manager import ClipboardManager
from controllers.bulk_device_controller import BulkDeviceController
from controllers.bulk_property_controller import BulkPropertyController
from utils.event_bus import EventBus
from utils.recent_files import RecentFiles
from utils.theme_manager import ThemeManager
from utils.font_settings_manager import FontSettingsManager
from utils.icon_manager import icon_manager
from models.device import Device
from models.connection.connection import Connection
from models.boundary.boundary import Boundary
from views.properties import PropertiesPanel
from controllers.properties_controller import PropertiesController
from views.alignment_toolbar import AlignmentToolbar
from controllers.commands import AlignDevicesCommand
from controllers.device_alignment_controller import DeviceAlignmentController
from dialogs.font_settings_dialog import FontSettingsDialog
from dialogs.connection_type_dialog import ConnectionTypeDialog
from dialogs.multi_connection_dialog import MultiConnectionDialog
from utils import alignment_helper
from controllers.selection_manager import SelectionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GraphNIST")
        # Set a reasonable default size instead of maximizing
        self.setGeometry(100, 100, 1280, 800)
        
        # Setup logging first to avoid AttributeError
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Set application icon - use absolute path to ensure it's found
        app_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     "resources", "icons", "svg", "shield_logo.svg")
        
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))
            self.logger.info(f"Application icon loaded from: {app_icon_path}")
        else:
            self.logger.warning(f"Application icon not found at: {app_icon_path}")

        # Initialize theme manager before creating UI elements
        self.theme_manager = ThemeManager()
        
        # Initialize font settings manager
        self.font_settings_manager = FontSettingsManager()

        # Create canvas
        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        
        # Register canvas with theme manager
        self.theme_manager.register_canvas(self.canvas)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Connect status message signal
        self.canvas.statusMessage.connect(self.statusBar().showMessage)
        
        # Create event bus for communication between components
        self.event_bus = EventBus()
        
        # Connect event bus to theme manager
        self.theme_manager.set_event_bus(self.event_bus)
        
        # Initialize recent files manager
        self.recent_files_manager = RecentFiles(self)
        
        # Initialize command_manager with a None value to avoid attribute errors
        self.command_manager = None
        
        # Initialize undo_redo_manager to None to avoid attribute errors
        self.undo_redo_manager = None
        
        # Initialize controllers
        self._init_controllers()
        
        # Create menu manager 
        self.menu_manager = MenuManager(self, self.canvas, self.event_bus)
        
        # Create UI components
        self._create_ui_components()
        
        # Setup alignment tools
        self.setup_alignment_tools()
        
        # Connect signals
        self.connect_signals()
        
        # Set initial mode
        self.set_mode(Modes.SELECT)
        
        # Register event handlers
        self._register_event_handlers()
        
        # Apply the initial theme
        self.theme_manager.apply_theme()
        
        # Connect font change signals
        self._connect_font_signals()
        
        # Remove the line that maximizes the window on startup
        # self.showMaximized()

    def _init_controllers(self):
        """Initialize controllers for device, connection, and boundary management."""
        self.device_controller = DeviceController(self.canvas, self.event_bus)
        self.connection_controller = ConnectionController(self.canvas, self.event_bus)
        self.boundary_controller = BoundaryController(self.canvas, self.event_bus)
        
        # Set the theme manager for controllers
        self.device_controller.theme_manager = self.theme_manager
        self.connection_controller.theme_manager = self.theme_manager
        self.boundary_controller.theme_manager = self.theme_manager
        
        # Initialize clipboard manager
        self.clipboard_manager = ClipboardManager(
            self.canvas, 
            self.device_controller,
            self.connection_controller,
            self.event_bus
        )
        
        # Setup font settings for device controller
        if hasattr(self, 'font_settings_manager') and self.font_settings_manager:
            self.device_controller.font_settings_manager = self.font_settings_manager
        
        # Apply theme to existing devices if any
        is_dark = self.theme_manager.is_dark_theme()
        text_color = QColor(240, 240, 240) if is_dark else QColor(0, 0, 0)
        
        for device in self.canvas.devices:
            if hasattr(device, 'update_theme'):
                device.update_theme(self.theme_manager.get_theme())
                
            # Directly set text colors
            if hasattr(device, 'text_item') and device.text_item:
                device.text_item.setDefaultTextColor(text_color)
                
                # Make text larger and bolder for visibility
                font = device.text_item.font()
                font.setPointSize(10)
                font.setBold(True)
                device.text_item.setFont(font)
        
        # Initialize bulk controllers - these will be fully set up after command_manager is initialized
        self.bulk_device_controller = None
        self.bulk_property_controller = None
        
    def _connect_font_signals(self):
        """Connect signals for font setting changes."""
        # UI font changes
        self.font_settings_manager.ui_font_changed.connect(self._apply_ui_font)
        
        # Device label font changes
        self.font_settings_manager.device_label_font_changed.connect(self._apply_device_label_font)
        
        # Device property font changes
        self.font_settings_manager.device_property_font_changed.connect(self._apply_device_property_font)

    def _apply_ui_font(self, font):
        """Apply UI font to the application."""
        # Update application font
        app = QApplication.instance()
        if app:
            app.setFont(font)
            self.statusBar().showMessage(f"UI font size updated to {font.pointSize()}pt")

    def _apply_device_label_font(self, font):
        """Apply device label font to all devices."""
        # Update all devices on canvas
        for device in self.canvas.devices:
            device.update_font_settings(self.font_settings_manager)
        self.statusBar().showMessage(f"Device label font size updated to {font.pointSize()}pt")

    def _apply_device_property_font(self, font):
        """Apply device property font to all devices."""
        # Update is handled by the same method as label font
        self.statusBar().showMessage(f"Property label font size updated to {font.pointSize()}pt")
        
    def _create_ui_components(self):
        """Create UI components like menus, panels, and toolbars."""
        # Create menus (main window creates Edit menu directly, not via menu_manager)
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_device_menu()  # New menu for device operations
        
        # Create enhanced sidebar toolbar
        self._create_enhanced_sidebar()
        
        # Set up keyboard shortcuts
        self._setup_shortcuts()
        
        # Create properties panel
        self.properties_panel = PropertiesPanel(self)
        self.properties_dock = QDockWidget("Properties", self)
        self.properties_dock.setWidget(self.properties_panel)
        self.properties_dock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        
        # Start with properties panel visible
        self.properties_dock.setVisible(True)

        # Initialize properties controller - defer its creation until command_manager is properly set in main.py
        self.properties_controller = None

    def _create_edit_menu(self):
        """Create the Edit menu with clipboard and undo/redo actions."""
        edit_menu = self.menuBar().addMenu("&Edit")
        
        # Undo/redo actions (will be enabled once command_manager is initialized)
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setEnabled(False)
        self.undo_action = undo_action
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setEnabled(False)
        self.redo_action = redo_action
        edit_menu.addAction(redo_action)
        
        # Connect undo/redo actions if command manager is available
        if self.command_manager:
            undo_action.triggered.connect(self.command_manager.undo)
            redo_action.triggered.connect(self.command_manager.redo)
            undo_action.setEnabled(self.command_manager.can_undo())
            redo_action.setEnabled(self.command_manager.can_redo())
            # Connect to stack changed signal
            self.command_manager.undo_redo_manager.stack_changed.connect(self._update_undo_redo_actions)
        
        edit_menu.addSeparator()
        
        # Cut action
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.clipboard_manager.cut_selected)
        edit_menu.addAction(cut_action)
        
        # Copy action
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.clipboard_manager.copy_selected)
        edit_menu.addAction(copy_action)
        
        # Paste action
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.clipboard_manager.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        # Delete action
        delete_action = QAction("&Delete", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.on_delete_selected_requested)
        edit_menu.addAction(delete_action)
        
        return edit_menu

    def _update_undo_redo_actions(self):
        """Update the undo/redo actions based on state."""
        if self.command_manager and hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(self.command_manager.can_undo())
            self.undo_action.setText(f"&Undo {self.command_manager.get_undo_text()}")
            
        if self.command_manager and hasattr(self, 'redo_action'):
            self.redo_action.setEnabled(self.command_manager.can_redo())
            self.redo_action.setText(f"&Redo {self.command_manager.get_redo_text()}")

    def _create_device_menu(self):
        """Create a dedicated device menu for device operations."""
        device_menu = self.menuBar().addMenu("&Devices")
        
        # Add device action
        add_device_action = QAction("&Add Device...", self)
        add_device_action.setStatusTip("Add a new device to the canvas")
        add_device_action.triggered.connect(lambda: self._on_add_device_requested())
        device_menu.addAction(add_device_action)
        
        # Bulk add action
        bulk_add_action = QAction("Add &Multiple Devices...", self)
        bulk_add_action.setStatusTip("Add multiple different devices in bulk")
        bulk_add_action.triggered.connect(self._on_bulk_add_device_requested)
        device_menu.addAction(bulk_add_action)
        
        device_menu.addSeparator()
        
        # Bulk edit action
        bulk_edit_action = QAction("&Edit Selected Devices...", self)
        bulk_edit_action.setStatusTip("Edit properties of multiple selected devices")
        bulk_edit_action.triggered.connect(self._on_edit_selected_devices)
        device_menu.addAction(bulk_edit_action)
        
        device_menu.addSeparator()
        
        # Device import/export submenu
        export_menu = QMenu("&Export", self)
        
        # CSV export actions
        export_selected_csv_action = QAction("Export Selected Devices as CSV...", self)
        export_selected_csv_action.triggered.connect(self._export_selected_to_csv)
        export_menu.addAction(export_selected_csv_action)
        
        export_all_csv_action = QAction("Export All Devices as CSV...", self)
        export_all_csv_action.triggered.connect(self._export_all_to_csv)
        export_menu.addAction(export_all_csv_action)
        
        export_menu.addSeparator()
        
        # Excel export actions
        export_selected_excel_action = QAction("Export Selected Devices as Excel...", self)
        export_selected_excel_action.triggered.connect(self._export_selected_to_excel)
        export_menu.addAction(export_selected_excel_action)
        
        export_all_excel_action = QAction("Export All Devices as Excel...", self)
        export_all_excel_action.triggered.connect(self._export_all_to_excel)
        export_menu.addAction(export_all_excel_action)
        
        export_menu.addSeparator()
        
        # Add PDF export actions
        export_pdf_action = QAction("Export Canvas to PDF...", self)
        export_pdf_action.triggered.connect(self.export_to_pdf)
        export_menu.addAction(export_pdf_action)
        
        device_menu.addMenu(export_menu)
        
        # Import submenu
        import_menu = QMenu("&Import", self)
        
        # CSV import action
        import_csv_action = QAction("Import Devices from CSV...", self)
        import_csv_action.triggered.connect(self._import_from_csv)
        import_menu.addAction(import_csv_action)
        
        # Excel import action
        import_excel_action = QAction("Import Devices from Excel...", self)
        import_excel_action.triggered.connect(self._import_from_excel)
        import_menu.addAction(import_excel_action)
        
        # Add import submenu
        device_menu.addMenu(import_menu)

    def _export_selected_to_csv(self):
        """Export selected devices to a CSV file."""
        # Get selected devices
        selected_devices = [item for item in self.canvas.scene().selectedItems() if item in self.canvas.devices]
        
        if not selected_devices:
            QMessageBox.warning(self, "Export Failed", "No devices selected to export.")
            return
        
        # Show file dialog
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Selected Devices",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        
        if not filepath:
            return
        
        # Ensure file has .csv extension
        if not filepath.lower().endswith('.csv'):
            filepath += '.csv'
        
        # Import device exporter
        from utils.device_exporter import DeviceExporter
        exporter = DeviceExporter()
        
        # Export devices
        result_path = exporter.export_to_csv(selected_devices, filepath)
        
        if result_path:
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Successfully exported {len(selected_devices)} devices to {result_path}"
            )
            self.statusBar().showMessage(f"Exported {len(selected_devices)} devices to CSV")
        else:
            QMessageBox.critical(
                self, 
                "Export Failed", 
                "Failed to export devices. Check the log for details."
            )
    
    def _export_all_to_csv(self):
        """Export all devices to a CSV file."""
        # Get all devices
        devices = self.canvas.devices
        
        if not devices:
            QMessageBox.warning(self, "Export Failed", "No devices available to export.")
            return
        
        # Show file dialog
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export All Devices",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        
        if not filepath:
            return
        
        # Ensure file has .csv extension
        if not filepath.lower().endswith('.csv'):
            filepath += '.csv'
        
        # Import device exporter
        from utils.device_exporter import DeviceExporter
        exporter = DeviceExporter()
        
        # Export devices
        result_path = exporter.export_to_csv(devices, filepath)
        
        if result_path:
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Successfully exported {len(devices)} devices to {result_path}"
            )
            self.statusBar().showMessage(f"Exported {len(devices)} devices to CSV")
        else:
            QMessageBox.critical(
                self, 
                "Export Failed", 
                "Failed to export devices. Check the log for details."
            )
    
    def _export_selected_to_excel(self):
        """Export selected devices to an Excel file."""
        # Get selected devices
        selected_devices = [item for item in self.canvas.scene().selectedItems() if item in self.canvas.devices]
        
        if not selected_devices:
            QMessageBox.warning(self, "Export Failed", "No devices selected to export.")
            return
        
        # Show file dialog
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Selected Devices",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)",
        )
        
        if not filepath:
            return
        
        # Ensure file has .xlsx extension
        if not filepath.lower().endswith('.xlsx'):
            filepath += '.xlsx'
        
        # Import device exporter
        from utils.device_exporter import DeviceExporter
        exporter = DeviceExporter()
        
        # Export devices
        try:
            result_path = exporter.export_to_excel(selected_devices, filepath)
            
            if result_path:
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Successfully exported {len(selected_devices)} devices to {result_path}"
                )
                self.statusBar().showMessage(f"Exported {len(selected_devices)} devices to Excel")
            else:
                QMessageBox.critical(
                    self, 
                    "Export Failed", 
                    "Failed to export devices. Check the log for details."
                )
        except ImportError:
            QMessageBox.critical(
                self,
                "Export Failed",
                "Excel export requires the openpyxl library. Please install it with: pip install openpyxl"
            )
    
    def _export_all_to_excel(self):
        """Export all devices to an Excel file."""
        # Get all devices
        devices = self.canvas.devices
        
        if not devices:
            QMessageBox.warning(self, "Export Failed", "No devices available to export.")
            return
        
        # Show file dialog
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export All Devices",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)",
        )
        
        if not filepath:
            return
        
        # Ensure file has .xlsx extension
        if not filepath.lower().endswith('.xlsx'):
            filepath += '.xlsx'
        
        # Import device exporter
        from utils.device_exporter import DeviceExporter
        exporter = DeviceExporter()
        
        # Export devices
        try:
            result_path = exporter.export_to_excel(devices, filepath)
            
            if result_path:
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Successfully exported {len(devices)} devices to {result_path}"
                )
                self.statusBar().showMessage(f"Exported {len(devices)} devices to Excel")
            else:
                QMessageBox.critical(
                    self, 
                    "Export Failed", 
                    "Failed to export devices. Check the log for details."
                )
        except ImportError:
            QMessageBox.critical(
                self,
                "Export Failed",
                "Excel export requires the openpyxl library. Please install it with: pip install openpyxl"
            )
    
    def _import_from_csv(self):
        """Import devices from a CSV file."""
        # Show file dialog
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Devices from CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        
        if not filepath:
            return
        
        # Confirm import
        confirm = QMessageBox.question(
            self,
            "Confirm Import",
            "Importing devices will add them to the current canvas. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        # Create device factory function
        def device_factory(name, device_type, properties):
            return self.device_controller.create_device(name, device_type, properties)
        
        # Import device importer
        from utils.device_importer import DeviceImporter
        importer = DeviceImporter(device_factory)
        
        # Import devices
        devices = importer.import_from_csv(filepath)
        
        if devices:
            QMessageBox.information(
                self, 
                "Import Successful", 
                f"Successfully imported {len(devices)} devices from {filepath}"
            )
            self.statusBar().showMessage(f"Imported {len(devices)} devices from CSV")
            
            # Ensure all imported devices are visible
            if devices:
                # Calculate bounds
                min_x = min(device.scenePos().x() for device in devices)
                min_y = min(device.scenePos().y() for device in devices)
                max_x = max(device.scenePos().x() + device.boundingRect().width() for device in devices)
                max_y = max(device.scenePos().y() + device.boundingRect().height() for device in devices)
                
                # Create a rectangle with some padding
                padding = 50
                rect = QRectF(min_x - padding, min_y - padding, 
                             (max_x - min_x) + 2 * padding, 
                             (max_y - min_y) + 2 * padding)
                
                # Center on the imported devices
                self.canvas.fitInView(rect, Qt.KeepAspectRatio)
        else:
            QMessageBox.critical(
                self, 
                "Import Failed", 
                "Failed to import devices. Check the log for details."
            )
    
    def _import_from_excel(self):
        """Import devices from an Excel file."""
        # Show file dialog
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Devices from Excel",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)",
        )
        
        if not filepath:
            return
        
        # Confirm import
        confirm = QMessageBox.question(
            self,
            "Confirm Import",
            "Importing devices will add them to the current canvas. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        # Create device factory function
        def device_factory(name, device_type, properties):
            return self.device_controller.create_device(name, device_type, properties)
        
        # Import device importer
        from utils.device_importer import DeviceImporter
        importer = DeviceImporter(device_factory)
        
        # Import devices
        try:
            devices = importer.import_from_excel(filepath)
            
            if devices:
                QMessageBox.information(
                    self, 
                    "Import Successful", 
                    f"Successfully imported {len(devices)} devices from {filepath}"
                )
                self.statusBar().showMessage(f"Imported {len(devices)} devices from Excel")
                
                # Ensure all imported devices are visible
                if devices:
                    # Calculate bounds
                    min_x = min(device.scenePos().x() for device in devices)
                    min_y = min(device.scenePos().y() for device in devices)
                    max_x = max(device.scenePos().x() + device.boundingRect().width() for device in devices)
                    max_y = max(device.scenePos().y() + device.boundingRect().height() for device in devices)
                    
                    # Create a rectangle with some padding
                    padding = 50
                    rect = QRectF(min_x - padding, min_y - padding, 
                                 (max_x - min_x) + 2 * padding, 
                                 (max_y - min_y) + 2 * padding)
                    
                    # Center on the imported devices
                    self.canvas.fitInView(rect, Qt.KeepAspectRatio)
            else:
                QMessageBox.critical(
                    self, 
                    "Import Failed", 
                    "Failed to import devices. Check the log for details."
                )
        except ImportError:
            QMessageBox.critical(
                self,
                "Import Failed",
                "Excel import requires the openpyxl library. Please install it with: pip install openpyxl"
            )

    def _register_event_handlers(self):
        """Register event handlers with the event bus."""
        if self.event_bus:
            # Device property events
            self.event_bus.on('device_property_changed', self._on_device_property_changed)
            self.event_bus.on('device_display_properties_changed', self._on_device_display_properties_changed)
            
            # Device modification events
            self.event_bus.on('device_added', self._on_device_added)
            self.event_bus.on('device_removed', self._on_device_removed)
            
            # Connection events
            self.event_bus.on('connection_added', self._on_connection_added)
            self.event_bus.on('connection_removed', self._on_connection_removed)
            
            # Bulk operation events
            self.event_bus.on('bulk_devices_added', self._on_bulk_devices_added)
            self.event_bus.on('bulk_properties_changed', self._on_bulk_properties_changed)
            
            # Theme events
            self.event_bus.on('theme_changed', self._on_theme_changed)

    def setup_properties_controller(self):
        """Set up the properties controller after command_manager is initialized."""
        try:
            # Create properties controller if it doesn't exist
            if self.properties_controller is None:
                self.properties_controller = PropertiesController(
                    self.canvas,
                    self.properties_panel,
                    self.event_bus,
                    self.command_manager.undo_redo_manager if self.command_manager else None
                )
                
                # Register the properties controller with the event bus
                self.event_bus.register_controller('properties', self.properties_controller)
                
                # Set properties dock to be initially visible
                if hasattr(self, 'properties_dock'):
                    self.properties_dock.setVisible(True)
                    
                self.logger.info("Properties controller initialized")
            
            # Create and set up selection manager with the event bus
            self.selection_manager = SelectionManager(
                self.canvas,
                self.event_bus,
                self.properties_controller
            )
            
            # Store reference to selection manager in properties controller
            self.properties_controller.selection_manager = self.selection_manager
            
            # Register selection manager with event bus
            self.event_bus.register_controller('selection_manager', self.selection_manager)
            
            self.logger.info("Selection manager initialized with event bus")
            
            # Set up bulk controllers now that command_manager is available
            if self.bulk_device_controller is None:
                self.bulk_device_controller = BulkDeviceController(
                    self.canvas,
                    self.device_controller,
                    self.event_bus,
                    self.command_manager.undo_redo_manager if self.command_manager else None
                )
            
            if self.bulk_property_controller is None:
                self.bulk_property_controller = BulkPropertyController(
                    self.canvas,
                    self.device_controller,
                    self.event_bus,
                    self.command_manager.undo_redo_manager if self.command_manager else None
                )
            
            # Initialize device alignment controller after undo_redo_manager is available
            if not hasattr(self, 'device_alignment_controller') or self.device_alignment_controller is None:
                self.undo_redo_manager = self.command_manager.undo_redo_manager if self.command_manager else None
                self.device_alignment_controller = DeviceAlignmentController(
                    event_bus=self.event_bus,
                    undo_redo_manager=self.undo_redo_manager
                )
                
                # Connect canvas alignment signal to controller
                self.canvas.align_devices_requested.connect(self._on_align_devices_requested)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize properties controller: {str(e)}")
            import traceback
            traceback.print_exc()

    def setup_alignment_tools(self):
        """Set up the alignment controller."""
        # Create alignment controller - use DeviceAlignmentController instead of undefined AlignmentController
        self.alignment_controller = DeviceAlignmentController(
            self.event_bus, 
            self.command_manager.undo_redo_manager if (hasattr(self, 'command_manager') and self.command_manager) else None
        )
        
        # Store a reference to the canvas in the alignment controller
        self.alignment_controller.canvas = self.canvas
        
        # Connect alignment signals
        if self.event_bus:
            self.event_bus.on('devices.aligned', self.on_devices_aligned)

    def _create_enhanced_sidebar(self):
        """Create an enhanced sidebar with all tool actions."""
        # Create toolbar on left side
        toolbar = self.addToolBar("Canvas Tools")
        toolbar.setObjectName("enhanced_sidebar")  # For saving state
        
        # Use smaller icons with more compact text
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Set orientation to vertical and place on left
        toolbar.setOrientation(Qt.Vertical)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        
        # Keep icons at a reasonable size
        toolbar.setIconSize(QSize(24, 24))
        
        # Dictionary to store mode actions
        self.canvas_actions = {}
        
        # === DRAWING TOOLS GROUP ===
        toolbar.addWidget(self._create_toolbar_label("Drawing Tools"))
        
        # Select mode
        select_action = QAction(icon_manager.get_icon("select_tool"), "Select", self)
        select_action.setStatusTip("Select and move devices")
        select_action.setCheckable(True)
        select_action.setChecked(True)  # Default mode
        select_action.triggered.connect(lambda: self._set_canvas_mode(Modes.SELECT))
        toolbar.addAction(select_action)
        self.canvas_actions[Modes.SELECT] = select_action
        
        # Add Device
        add_device_action = QAction(icon_manager.get_icon("add_device"), "Add Device", self)
        add_device_action.setStatusTip("Add a new device to the canvas")
        add_device_action.setCheckable(True)
        add_device_action.triggered.connect(lambda: self._set_canvas_mode(Modes.ADD_DEVICE))
        toolbar.addAction(add_device_action)
        self.canvas_actions[Modes.ADD_DEVICE] = add_device_action
        
        # Add Connection
        add_connection_action = QAction(icon_manager.get_icon("add_connection"), "Add Connection", self)
        add_connection_action.setStatusTip("Add a connection between devices")
        add_connection_action.setCheckable(True)
        add_connection_action.triggered.connect(lambda: self._set_canvas_mode(Modes.ADD_CONNECTION))
        toolbar.addAction(add_connection_action)
        self.canvas_actions[Modes.ADD_CONNECTION] = add_connection_action
        
        # Add Boundary
        add_boundary_action = QAction(icon_manager.get_icon("add_boundary"), "Add Boundary", self)
        add_boundary_action.setStatusTip("Add a boundary shape to the canvas")
        add_boundary_action.setCheckable(True)
        add_boundary_action.triggered.connect(lambda: self._set_canvas_mode(Modes.ADD_BOUNDARY))
        toolbar.addAction(add_boundary_action)
        self.canvas_actions[Modes.ADD_BOUNDARY] = add_boundary_action
        
        # Delete mode
        delete_action = QAction(icon_manager.get_icon("delete"), "Delete", self)
        delete_action.setStatusTip("Delete devices and connections")
        delete_action.setCheckable(True)
        delete_action.triggered.connect(lambda: self._set_canvas_mode(Modes.DELETE))
        toolbar.addAction(delete_action)
        self.canvas_actions[Modes.DELETE] = delete_action
        
        # === EDIT GROUP ===
        toolbar.addSeparator()
        toolbar.addWidget(self._create_toolbar_label("Edit"))
        
        # Copy action
        copy_action = QAction(icon_manager.get_icon("copy"), "Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setStatusTip("Copy selected items")
        copy_action.triggered.connect(self.clipboard_manager.copy_selected)
        toolbar.addAction(copy_action)
        
        # Paste action
        paste_action = QAction(icon_manager.get_icon("paste"), "Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setStatusTip("Paste items from clipboard")
        paste_action.triggered.connect(self.clipboard_manager.paste)
        toolbar.addAction(paste_action)
        
        # === FORMATTING GROUP ===
        toolbar.addSeparator()
        toolbar.addWidget(self._create_toolbar_label("Format"))
        
        # Connection style actions
        # Straight Lines
        straight_action = QAction(icon_manager.get_icon("connection_straight"), "Straight Lines", self)
        straight_action.setStatusTip("Use straight line connections")
        straight_action.setCheckable(True)
        straight_action.setChecked(True)  # Default style
        straight_action.triggered.connect(lambda: self.connection_controller.set_connection_style(Connection.STYLE_STRAIGHT))
        toolbar.addAction(straight_action)
        
        # Orthogonal Lines
        orthogonal_action = QAction(icon_manager.get_icon("connection_orthogonal"), "Right Angles", self)
        orthogonal_action.setStatusTip("Use orthogonal (right angle) connections")
        orthogonal_action.setCheckable(True)
        orthogonal_action.triggered.connect(lambda: self.connection_controller.set_connection_style(Connection.STYLE_ORTHOGONAL))
        toolbar.addAction(orthogonal_action)
        
        # Curved Lines
        curved_action = QAction(icon_manager.get_icon("connection_curved"), "Curved Lines", self)
        curved_action.setStatusTip("Use curved line connections")
        curved_action.setCheckable(True)
        curved_action.triggered.connect(lambda: self.connection_controller.set_connection_style(Connection.STYLE_CURVED))
        toolbar.addAction(curved_action)
        
        # Create a style group for connection styles
        style_group = QActionGroup(self)
        style_group.setExclusive(True)
        style_group.addAction(straight_action)
        style_group.addAction(orthogonal_action)
        style_group.addAction(curved_action)
        
        # Create the alignment button (simple without dropdown)
        align_action = QAction(icon_manager.get_icon("align"), "Align", self)
        align_action.setStatusTip("Align selected devices")
        align_action.triggered.connect(self._show_alignment_menu)
        toolbar.addAction(align_action)
        self.align_action = align_action
        
        # === VIEW GROUP ===
        toolbar.addSeparator()
        toolbar.addWidget(self._create_toolbar_label("View"))
        
        # Add zoom actions
        zoom_in_action = QAction(icon_manager.get_icon("zoom_in"), "Zoom In", self)
        zoom_in_action.setStatusTip("Zoom in the canvas view")
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(icon_manager.get_icon("zoom_out"), "Zoom Out", self)
        zoom_out_action.setStatusTip("Zoom out the canvas view")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        reset_zoom_action = QAction(icon_manager.get_icon("zoom_reset"), "Reset Zoom", self)
        reset_zoom_action.setStatusTip("Reset zoom to 100%")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        toolbar.addAction(reset_zoom_action)
        
        # Reset view action
        reset_view_action = QAction("Reset View", self)
        reset_view_action.setShortcut("Home")
        reset_view_action.triggered.connect(self.canvas.reset_view)
        toolbar.addAction(reset_view_action)
        
        # Set Home Position action
        set_home_action = QAction("Set Current View as Home", self)
        set_home_action.triggered.connect(self._set_current_as_home)
        toolbar.addAction(set_home_action)

    def _show_alignment_menu(self, position=None):
        """Show the alignment menu when the align button is clicked."""
        alignment_menu = QMenu(self)
        
        # Import our new alignment helper
        from utils import alignment_helper
        
        # Test movement option
        test_move_action = alignment_menu.addAction("TEST: Move Selected Devices")
        test_move_action.triggered.connect(lambda: alignment_helper.test_move(self.canvas))
        
        alignment_menu.addSeparator()
        
        # Auto-layout optimization
        optimize_layout_action = alignment_menu.addAction("Optimize Network Layout...")
        optimize_layout_action.setToolTip("Automatically arrange devices to minimize connection crossings")
        optimize_layout_action.triggered.connect(self._on_optimize_layout_requested)
        
        alignment_menu.addSeparator()
        
        # Basic alignment submenu
        basic_align = alignment_menu.addMenu("Basic Alignment")
        
        # Create individual actions to directly call alignment helper functions
        align_left = basic_align.addAction("Align Left")
        align_left.triggered.connect(lambda: alignment_helper.align_left(self.canvas))
        
        align_right = basic_align.addAction("Align Right")
        align_right.triggered.connect(lambda: alignment_helper.align_right(self.canvas))
        
        align_top = basic_align.addAction("Align Top")
        align_top.triggered.connect(lambda: alignment_helper.align_top(self.canvas))
        
        align_bottom = basic_align.addAction("Align Bottom")
        align_bottom.triggered.connect(lambda: alignment_helper.align_bottom(self.canvas))
        
        basic_align.addSeparator()
        
        align_center_h = basic_align.addAction("Center Horizontally")
        align_center_h.triggered.connect(lambda: alignment_helper.align_center_horizontal(self.canvas))
        
        align_center_v = basic_align.addAction("Center Vertically")
        align_center_v.triggered.connect(lambda: alignment_helper.align_center_vertical(self.canvas))
        
        basic_align.addSeparator()
        
        distribute_h = basic_align.addAction("Distribute Horizontally")
        distribute_h.triggered.connect(lambda: alignment_helper.distribute_horizontally(self.canvas))
        
        distribute_v = basic_align.addAction("Distribute Vertically")
        distribute_v.triggered.connect(lambda: alignment_helper.distribute_vertically(self.canvas))
        
        # Network layouts submenu
        network_layouts = alignment_menu.addMenu("Network Layouts")
        
        grid_action = network_layouts.addAction("Grid Arrangement")
        grid_action.triggered.connect(lambda: alignment_helper.arrange_grid(self.canvas))
        
        circle_action = network_layouts.addAction("Circle Arrangement")
        circle_action.triggered.connect(lambda: alignment_helper.arrange_circle(self.canvas))
        
        star_action = network_layouts.addAction("Star Arrangement")
        star_action.triggered.connect(lambda: alignment_helper.arrange_star(self.canvas))
        
        bus_action = network_layouts.addAction("Bus Arrangement")
        bus_action.triggered.connect(lambda: alignment_helper.arrange_bus(self.canvas))
        
        # Show the menu at the cursor position or below the button
        if position:
            alignment_menu.exec_(position)
        else:
            button_pos = self.align_action.parentWidget().mapToGlobal(
                self.align_action.parentWidget().rect().bottomLeft())
            alignment_menu.exec_(button_pos)

    # Event handler methods
    def _on_device_property_changed(self, device, property_name, value=None):
        """Handle device property change events."""
        # If the property is being displayed, update the label
        if hasattr(device, 'display_properties') and property_name in device.display_properties:
            if device.display_properties[property_name]:
                device.update_property_labels()

    def _on_connection_property_changed(self, connection, property_name, value=None):
        """Handle connection property change events."""
        # Check if connection is an actual connection object and not a string
        if isinstance(connection, str):
            self.logger.warning(f"Received string instead of connection object: {connection}")
            return
            
        # Update the connection's appearance based on the changed property
        if hasattr(connection, 'update_appearance'):
            connection.update_appearance()
        # Force a visual update
        if hasattr(connection, 'update'):
            connection.update()
        if hasattr(connection, 'scene') and callable(connection.scene) and connection.scene():
            # Update a slightly larger area to ensure all visual elements are refreshed
            update_rect = connection.sceneBoundingRect().adjusted(-5, -5, 5, 5)
            connection.scene().update(update_rect)
                
    def _on_boundary_property_changed(self, boundary, property_name, value=None):
        """Handle boundary property change events."""
        # Check if boundary is an actual boundary object and not a string
        if isinstance(boundary, str):
            self.logger.warning(f"Received string instead of boundary object: {boundary}")
            return
            
        # Update the boundary's appearance based on the changed property
        if hasattr(boundary, 'update_appearance'):
            boundary.update_appearance()
        # Force a visual update
        if hasattr(boundary, 'update'):
            boundary.update()
        if hasattr(boundary, 'scene') and callable(boundary.scene) and boundary.scene():
            update_rect = boundary.sceneBoundingRect().adjusted(-5, -5, 5, 5)
            boundary.scene().update(update_rect)
                
    def _on_device_display_properties_changed(self, device, property_name=None, enabled=None):
        """Handle changes to which properties are displayed under devices."""
        device.update_property_labels()
        
    def _on_device_added(self, device):
        """Handle device added event."""
        self.statusBar().showMessage(f"Added device: {device.name}", 3000)
        
    def _on_device_removed(self, device):
        """Handle device removed event."""
        self.statusBar().showMessage(f"Removed device: {device.name}", 3000)
        
    def _on_connection_added(self, connection):
        """Handle connection added event."""
        source = connection.source_device.name if hasattr(connection, 'source_device') else "unknown"
        target = connection.target_device.name if hasattr(connection, 'target_device') else "unknown"
        self.statusBar().showMessage(f"Added connection: {source} to {target}", 3000)
        
    def _on_connection_removed(self, connection):
        """Handle connection removed event."""
        self.statusBar().showMessage("Connection removed", 3000)

    def on_devices_aligned(self, alignment_type, devices):
        """Handle device alignment for undo/redo support."""
        if hasattr(self, 'command_manager') and self.command_manager and hasattr(self.command_manager, 'undo_redo_manager'):
            # Create command for undo/redo
            original_positions = {device: device.scenePos() for device in devices}
            
            command = AlignDevicesCommand(
                self.alignment_controller,
                devices,
                original_positions,
                alignment_type
            )
            
            # Push command to undo stack
            self.command_manager.undo_redo_manager.push_command(command)
            
            self.logger.debug(f"Added alignment command to undo stack: {alignment_type}")
            self.statusBar().showMessage(f"Aligned {len(devices)} devices: {alignment_type}", 3000)

    def _on_bulk_devices_added(self, count):
        """Handle bulk device addition event."""
        from PyQt5.QtCore import QTimer
        from constants import Modes
        
        self.statusBar().showMessage(f"Added {count} devices in bulk", 3000)
        
        # Reset to SELECT mode after bulk device addition (with a short delay to ensure UI is updated)
        QTimer.singleShot(100, lambda: self._set_canvas_mode(Modes.SELECT))
    
    def _on_bulk_properties_changed(self, devices):
        """Handle bulk property change event."""
        self.statusBar().showMessage(f"Updated properties for {len(devices)} devices", 3000)
        
    def _on_theme_changed(self, theme_name):
        """Handle theme changed event."""
        from utils.theme_manager import ThemeManager
        
        self.logger.info(f"Theme changed to: {theme_name}")
        
        # Directly update device text colors to ensure visibility
        text_color = QColor(240, 240, 240) if theme_name == ThemeManager.DARK_THEME else QColor(0, 0, 0)
        
        # Update all devices
        for device in self.canvas.devices:
            # Apply theme update via the device's method
            if hasattr(device, 'update_theme'):
                device.update_theme(theme) # type: ignore
                
            # Directly set text colors in case update_theme doesn't work
            if hasattr(device, 'text_item') and device.text_item:
                device.text_item.setDefaultTextColor(text_color)
                
                # Make text larger and bolder for visibility
                font = device.text_item.font()
                font.setPointSize(10)
                font.setBold(True)
                device.text_item.setFont(font)
                
            # Update property labels too
            if hasattr(device, 'property_labels'):
                for label in device.property_labels.values():
                    label.setDefaultTextColor(text_color)
            
            # Force visual update
            device.update()
            if device.scene():
                update_rect = device.sceneBoundingRect().adjusted(-5, -5, 5, 5)
                device.scene().update(update_rect)
        
        # Force canvas update
        self.canvas.viewport().update()

    def _on_add_device_requested(self):
        """Show dialog to add a device at center of view."""
        view_center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
        self.device_controller.on_add_device_requested(view_center)
    
    def _on_bulk_add_device_requested(self):
        """Show dialog to add multiple devices in bulk."""
        if self.bulk_device_controller:
            # Get the center of the current view as default position
            view_center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
            self.bulk_device_controller.show_bulk_add_dialog(view_center)
        else:
            self.logger.error("Bulk device controller not initialized")
    
    def _on_edit_selected_devices(self):
        """Show dialog to edit properties of selected devices."""
        if self.bulk_property_controller:
            self.bulk_property_controller.edit_selected_devices()
        else:
            self.logger.error("Bulk property controller not initialized")

    def _create_file_menu(self):
        """Create the File menu with file operations."""
        file_menu = self.menuBar().addMenu("&File")
        
        # New canvas action
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_canvas)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_canvas)
        file_menu.addAction(open_action)
        
        # Recent files sub-menu (will be populated by recent_files_manager)
        self.recent_menu = file_menu.addMenu("Open &Recent")
        self.recent_files_manager.setup_menu(self.recent_menu, self.load_from_recent)
        
        file_menu.addSeparator()
        
        # Save actions
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_canvas)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_canvas_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        export_pdf_action = QAction("Export to PDF...", self)
        export_pdf_action.setShortcut("Ctrl+E")
        export_pdf_action.triggered.connect(self.export_to_pdf)
        file_menu.addAction(export_pdf_action)
        
        # Exit action
        file_menu.addSeparator()
        exit_action = QAction("E&xit GraphNIST", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        return file_menu

    def _create_view_menu(self):
        """Create the View menu with zoom actions and visualization options."""
        view_menu = self.menuBar().addMenu("View")
        
        # Zoom submenu
        zoom_menu = view_menu.addMenu("Zoom")
        
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        zoom_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        zoom_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        zoom_menu.addAction(reset_zoom_action)
        
        # Reset view action
        reset_view_action = QAction("Reset View", self)
        reset_view_action.setShortcut("Home")
        reset_view_action.triggered.connect(self.canvas.reset_view)
        view_menu.addAction(reset_view_action)
        
        # Set Home Position action
        set_home_action = QAction("Set Current View as Home", self)
        set_home_action.triggered.connect(self._set_current_as_home)
        view_menu.addAction(set_home_action)
        
        view_menu.addSeparator()
        
        # Grid toggle action
        self.toggle_grid_action = QAction("Show Grid", self)
        self.toggle_grid_action.setCheckable(True)
        self.toggle_grid_action.setChecked(self.canvas.show_grid)
        self.toggle_grid_action.setShortcut("Ctrl+G")  # Add keyboard shortcut
        self.toggle_grid_action.triggered.connect(self._toggle_grid)
        view_menu.addAction(self.toggle_grid_action)
        
        # Add theme toggle
        view_menu.addSeparator()
        
        # Theme toggle action
        self.toggle_theme_action = QAction("Toggle Dark Mode", self)
        self.toggle_theme_action.setShortcut("Ctrl+T")
        self.toggle_theme_action.triggered.connect(self._toggle_theme)
        # Set initial state based on current theme
        self.toggle_theme_action.setCheckable(True)
        self.toggle_theme_action.setChecked(self.theme_manager.is_dark_theme())
        view_menu.addAction(self.toggle_theme_action)
        
        # Add font settings action
        view_menu.addSeparator()
        
        # Font settings action
        font_settings_action = QAction("Font Settings...", self)
        font_settings_action.setShortcut("Ctrl+F")
        font_settings_action.triggered.connect(self._show_font_settings)
        view_menu.addAction(font_settings_action)
        
        return view_menu
        
    def _show_font_settings(self):
        """Show the font settings dialog."""
        FontSettingsDialog.show_dialog(self, self.font_settings_manager)
        
    def _toggle_grid(self):
        """Toggle grid visibility and update the action text accordingly."""
        self.canvas.toggle_grid()
        self.toggle_grid_action.setChecked(self.canvas.show_grid)
        grid_state = "on" if self.canvas.show_grid else "off"
        self.statusBar().showMessage(f"Grid turned {grid_state}")

    def _set_current_as_home(self):
        """Set the current view center as the home position."""
        # Get the current center of the viewport in scene coordinates
        viewport_center = self.canvas.mapToScene(
            self.canvas.viewport().rect().center()
        )
        self.canvas.set_home_position(viewport_center)
        self.statusBar().showMessage(f"Home position set to ({viewport_center.x():.1f}, {viewport_center.y():.1f})")

    def _setup_shortcuts(self):
        """Set up additional keyboard shortcuts."""
        # These shortcuts work globally in the main window
        
        # Delete key for deleting selected items
        # This function is already handled by the canvas and mode system
        pass

    def connect_signals(self):
        """Connect all signals and slots."""
        # Connect canvas signals
        self.canvas.add_device_requested.connect(self.device_controller.on_add_device_requested)
        self.canvas.delete_device_requested.connect(self.device_controller.on_delete_device_requested)
        self.canvas.add_connection_requested.connect(self.connection_controller.on_add_connection_requested)
        self.canvas.delete_connection_requested.connect(self.connection_controller.on_delete_connection_requested)
        self.canvas.connect_multiple_devices_requested.connect(self.connection_controller.on_connect_multiple_devices_requested)
        
        # Add debug logging for boundary signal connections
        self.logger.debug("MainWindow: Connecting add_boundary_requested signal to boundary_controller")
        self.canvas.add_boundary_requested.connect(self.boundary_controller.on_add_boundary_requested)
        
        # Check if the signal was connected successfully
        connection_count = self.canvas.receivers(self.canvas.add_boundary_requested)
        self.logger.debug(f"MainWindow: add_boundary_requested has {connection_count} connections after connecting to boundary_controller")
        
        self.canvas.delete_boundary_requested.connect(self.boundary_controller.on_delete_boundary_requested)
        self.canvas.delete_selected_requested.connect(self.on_delete_selected_requested)
        self.canvas.selection_changed.connect(self._on_selection_changed)
        
        # Connect device signals
        self.event_bus.on("device_added", self._on_device_added)
        self.event_bus.on("device_removed", self._on_device_removed)
        self.event_bus.on("device_property_changed", self._on_device_property_changed)
        self.event_bus.on("device_display_properties_changed", self._on_device_display_properties_changed)
        
        # Connect connection signals
        self.event_bus.on("connection_added", self._on_connection_added)
        self.event_bus.on("connection_removed", self._on_connection_removed)
        self.event_bus.on("connection_property_changed", self._on_connection_property_changed)
        
        # Connect boundary signals
        self.event_bus.on("boundary_created", self._on_boundary_added)
        self.event_bus.on("boundary_deleted", self._on_boundary_removed)
        self.event_bus.on("boundary_property_changed", self._on_boundary_property_changed)
        
        # Connect theme signals
        self.event_bus.on("theme_changed", self._on_theme_changed)
        
        # Connect bulk operation signals
        self.event_bus.on("bulk_devices_added", self._on_bulk_devices_added)
        self.event_bus.on("bulk_properties_changed", self._on_bulk_properties_changed)
        
        # Connect alignment signals
        self.event_bus.on("devices_aligned", self.on_devices_aligned)
        
        # Connect double-click signal for device editing
        self.event_bus.on("device_double_clicked", self._on_device_double_clicked)
    
    def _on_boundary_added(self, boundary):
        """Handle when a boundary is added."""
        self.logger.info(f"Boundary added: {boundary.name}")
        # Register with theme manager if not already registered
        if self.theme_manager and not hasattr(boundary, 'theme_manager'):
            self.theme_manager.register_theme_observer(boundary)
            
        # Update status bar
        self.statusBar().showMessage(f"Added boundary: {boundary.name}", 3000)
    
    def _on_boundary_removed(self, boundary):
        """Handle when a boundary is removed."""
        self.logger.info(f"Boundary removed: {boundary.name}")
        if boundary in self.canvas.boundaries:
            self.canvas.boundaries.remove(boundary)
            self.canvas.scene().removeItem(boundary)

    def _on_device_double_clicked(self, device):
        """Handle device double-click by showing properties panel and selecting the device."""
        self.logger.debug(f"MAINWINDOW DEBUG: Device double-clicked: {device.name}")
        # Use selection manager to handle the selection
        if hasattr(self, 'properties_controller') and hasattr(self.properties_controller, 'selection_manager'):
            self.logger.debug("MAINWINDOW DEBUG: Using selection manager to select device")
            self.properties_controller.selection_manager.select_item(device)
            
            # Ensure properties panel is visible
            if hasattr(self, 'properties_dock'):
                self.logger.debug("MAINWINDOW DEBUG: Making properties dock visible after double-click")
                self.properties_dock.setVisible(True)
                self.properties_dock.raise_()

    def _on_selection_changed(self, selected_items):
        """Handle selection changes in the canvas by showing the properties panel."""
        # Minimal logging
        self.logger.debug(f"MainWindow: Selection changed ({len(selected_items)} items)")
        
        if selected_items and len(selected_items) > 0:
            # Show properties panel when objects are selected
            if hasattr(self, 'properties_dock'):
                self.properties_dock.setVisible(True)
                self.properties_dock.raise_()
        else:
            # Hide properties panel when nothing is selected
            if hasattr(self, 'properties_dock'):
                self.properties_dock.setVisible(False)
            
        # No longer need to update the properties panel here as it
        # will be updated through the event bus

    def set_mode(self, mode):
        """Set the current interaction mode."""
        self.canvas.set_mode(mode)
        self.logger.info(f"Mode changed to: {mode}")
        # Update menu/toolbar to reflect current mode
        self.menu_manager.update_mode_actions(mode)
        
    def on_delete_item_requested(self, item):
        """Handle request to delete a non-specific item."""
        if item:
            self.logger.info(f"Deleting item of type {type(item).__name__}")
            
            # Find the top-level parent item if it's part of a composite
            top_item = item
            while top_item.parentItem():
                top_item = top_item.parentItem()
                
            # Dispatch to appropriate controller based on type
            from models.device import Device
            from models.connection.connection import Connection
            from models.boundary.boundary import Boundary
            
            if isinstance(top_item, Device):
                self.device_controller.on_delete_device_requested(top_item)
            elif isinstance(top_item, Connection):
                self.connection_controller.on_delete_connection_requested(top_item)
            elif isinstance(top_item, Boundary):
                self.boundary_controller.on_delete_boundary_requested(top_item)
            else:
                # Generic item with no specific controller
                self.canvas.scene().removeItem(top_item)
        
    def on_delete_selected_requested(self):
        """Handle request to delete all selected items."""
        selected_items = self.canvas.scene().selectedItems()
        
        if not selected_items:
            return
        
        try:
            self.logger.info(f"Attempting to delete {len(selected_items)} selected items")
            
            # Group items by type to handle deletion in the correct order
            connections = [item for item in selected_items if isinstance(item, Connection)]
            devices = [item for item in selected_items if isinstance(item, Device)]
            boundaries = [item for item in selected_items if isinstance(item, Boundary)]
            
            # Use composite command to handle undo/redo for multiple items
            if hasattr(self, 'command_manager') and self.command_manager:
                from controllers.commands import CompositeCommand
                composite_cmd = CompositeCommand(description=f"Delete {len(selected_items)} Selected Items")
                composite_cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                using_commands = True
            else:
                composite_cmd = None
                using_commands = False
            
            # Delete connections first to avoid references to deleted devices
            self.logger.info(f"Deleting {len(connections)} connections")
            for connection in connections:
                if using_commands:
                    from controllers.commands import DeleteConnectionCommand
                    cmd = DeleteConnectionCommand(self.connection_controller, connection)
                    cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                    composite_cmd.add_command(cmd)
                else:
                    self.connection_controller._delete_connection(connection)
            
            # Delete devices
            self.logger.info(f"Deleting {len(devices)} devices")
            for device in devices:
                if using_commands:
                    from controllers.commands import DeleteDeviceCommand
                    cmd = DeleteDeviceCommand(self.device_controller, device)
                    cmd.undo_redo_manager = self.command_manager.undo_redo_manager
                    composite_cmd.add_command(cmd)
                else:
                    self.device_controller._delete_device(device)
            
            # Delete boundaries
            self.logger.info(f"Deleting {len(boundaries)} boundaries")
            for boundary in boundaries:
                if using_commands:
                    from controllers.commands import DeleteBoundaryCommand
                    cmd = DeleteBoundaryCommand(self.boundary_controller, boundary)
                    composite_cmd.add_command(cmd)
                else:
                    self.boundary_controller.on_delete_boundary_requested(boundary)
            
            # Push the composite command if we're using undo/redo
            if composite_cmd and composite_cmd.commands:
                self.logger.info(f"Pushing composite delete command with {len(composite_cmd.commands)} actions")
                self.command_manager.undo_redo_manager.push_command(composite_cmd)
                
            # Force a complete update of the canvas
            self.canvas.viewport().update()
            
            self.logger.info(f"Deleted {len(connections)} connections, {len(devices)} devices, and {len(boundaries)} boundaries")
        except Exception as e:
            self.logger.error(f"Error in delete_selected: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def keyPressEvent(self, event):
        """Handle key press events."""
        # Let the canvas and its modes handle the key first
        if self.canvas.scene().focusItem():
            # If an item has focus, let Qt's standard event handling work
            super().keyPressEvent(event)
            return
            
        # Handle keyboard shortcuts using key combinations directly
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.copy_selected()
            event.accept()
        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.paste()
            event.accept()
        elif event.key() == Qt.Key_X and event.modifiers() & Qt.ControlModifier:
            self.clipboard_manager.cut_selected()
            event.accept()
        else:
            # Pass to parent for default handling
            super().keyPressEvent(event)
    
    def new_canvas(self):
        """Create a new empty canvas."""
        # Check if current canvas has changes that need to be saved
        # For simplicity, always ask to confirm
        confirm = QMessageBox.question(
            self,
            "New GraphNIST Diagram",
            "Creating a new diagram will discard any unsaved changes. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        # Clear the canvas
        self.canvas.clear()
        
        # Update status
        self.statusBar().showMessage("New GraphNIST diagram created")
    
    def save_canvas(self):
        """Save the current canvas to a file."""
        from views.file_dialog import SaveCanvasDialog
        
        success, message = SaveCanvasDialog.save_canvas(self, self.canvas, self.recent_files_manager)
        if success:
            self.logger.info("GraphNIST diagram saved successfully")
            self.statusBar().showMessage("GraphNIST diagram saved successfully")
        else:
            self.logger.warning(f"GraphNIST diagram save failed: {message}")
            self.statusBar().showMessage(f"GraphNIST diagram save failed: {message}")
    
    def save_canvas_as(self):
        """Save the current canvas to a new file."""
        # This is the same as save_canvas since the dialog always asks for a filepath
        self.save_canvas()

    def load_canvas(self):
        """Load a canvas from a file."""
        from views.file_dialog import LoadCanvasDialog
        
        success, message = LoadCanvasDialog.load_canvas(self, self.canvas, self.recent_files_manager)
        if success:
            self.logger.info("GraphNIST diagram loaded successfully")
            self.statusBar().showMessage("GraphNIST diagram loaded successfully")
        else:
            self.logger.warning(f"GraphNIST diagram load failed: {message}")
            self.statusBar().showMessage(f"GraphNIST diagram load failed: {message}")
    
    def load_from_recent(self, filepath):
        """Load a canvas from a recent file."""
        from views.file_dialog import LoadCanvasDialog
        
        success, message = LoadCanvasDialog.load_canvas(self, self.canvas, self.recent_files_manager, filepath)
        if success:
            self.logger.info(f"GraphNIST diagram loaded successfully from recent file: {filepath}")
            self.statusBar().showMessage(f"GraphNIST diagram loaded successfully")
        else:
            self.logger.warning(f"GraphNIST diagram load failed from recent file: {message}")
            self.statusBar().showMessage(f"GraphNIST diagram load failed: {message}")

    def _on_align_devices_requested(self, alignment_type, devices):
        """Handle request to align devices."""
        # Make sure the controller exists
        if not hasattr(self, 'device_alignment_controller') or self.device_alignment_controller is None:
            self.undo_redo_manager = self.command_manager.undo_redo_manager if self.command_manager else None
            self.device_alignment_controller = DeviceAlignmentController(
                event_bus=self.event_bus,
                undo_redo_manager=self.undo_redo_manager
            )
            
        self.device_alignment_controller.align_devices(alignment_type, devices)
    
    def export_to_pdf(self):
        """Export the canvas to PDF format."""
        from dialogs.pdf_export_dialog import PDFExportDialog
        PDFExportDialog.export_canvas(self, self.canvas)

    def _on_optimize_layout_requested(self):
        """Handle request to optimize the network layout."""
        if hasattr(self, 'connection_controller') and self.connection_controller:
            self.connection_controller.show_layout_optimization_dialog()
        else:
            self.logger.error("Connection controller not initialized")

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        from utils.theme_manager import ThemeManager
        theme = self.theme_manager.toggle_theme()
        is_dark = theme == ThemeManager.DARK_THEME
        theme_name = "dark" if is_dark else "light"
        self.toggle_theme_action.setChecked(is_dark)
        self.statusBar().showMessage(f"Switched to {theme_name} theme")
        
        # Directly update device text colors to ensure visibility
        text_color = QColor(240, 240, 240) if is_dark else QColor(0, 0, 0)
        
        # Update all existing devices
        for device in self.canvas.devices:
            # Apply theme update via the device's method
            if hasattr(device, 'update_theme'):
                device.update_theme(theme)
                
            # Directly set text colors in case update_theme doesn't work
            if hasattr(device, 'text_item') and device.text_item:
                device.text_item.setDefaultTextColor(text_color)
                
                # Make text larger and bolder for visibility
                font = device.text_item.font()
                font.setPointSize(10)
                font.setBold(True)
                device.text_item.setFont(font)
                
            # Update property labels too
            if hasattr(device, 'property_labels'):
                for label in device.property_labels.values():
                    label.setDefaultTextColor(text_color)
            
            # Force visual update
            device.update()
            if device.scene():
                update_rect = device.sceneBoundingRect().adjusted(-5, -5, 5, 5)
                device.scene().update(update_rect)
        
        # Force canvas update
        self.canvas.viewport().update()
        
    def _set_canvas_mode(self, mode):
        """Set the canvas interaction mode and update toolbar buttons."""
        if self.canvas.set_mode(mode):
            # Update checked state of all mode actions
            for mode_id, action in self.canvas_actions.items():
                action.setChecked(mode_id == mode)
    
    def _create_toolbar_label(self, text):
        """Create a bold label for toolbar sections."""
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        return label

    def _on_device_selected(self, device):
        """Handle device selection from properties panel."""
        if device:
            # Clear current selection
            self.canvas.scene().clearSelection()
            # Select the clicked device
            device.setSelected(True)
            # Update properties panel
            self._on_selection_changed([device])

    def _on_property_changed(self, item, property_name, value):
        """Handle property changes from the properties panel."""
        if hasattr(item, 'set_property'):
            item.set_property(property_name, value)
            # Update the canvas to reflect changes
            self.canvas.update()

    def _on_change_icon_requested(self, device):
        """Handle request to change a device's icon."""
        if device and hasattr(self.device_controller, 'change_device_icon'):
            self.device_controller.change_device_icon(device)
    
    def _on_property_display_toggled(self, device, property_name, enabled):
        """Handle toggling of property display under a device."""
        if device and hasattr(device, 'set_property_display'):
            device.set_property_display(property_name, enabled)
    
    def _on_property_delete_requested(self, item, property_name):
        """Handle request to delete a custom property."""
        if item and hasattr(item, 'delete_property'):
            item.delete_property(property_name)
            # Update the properties panel
            if hasattr(self.properties_panel, 'update_properties'):
                self.properties_panel.update_properties(item)
