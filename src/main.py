import sys
import logging
from PyQt5.QtWidgets import QApplication
import os
from PyQt5.QtCore import QDir, Qt
import datetime

from views.main_window import MainWindow
from controllers.command_manager import CommandManager
from controllers.undo_redo_manager import UndoRedoManager

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate timestamped log filename
    log_filename = os.path.join(logs_dir, f'graphnist_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # File handler 
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Logging configured. Log file: {log_filename}")

def main():
    # Set up detailed logging
    setup_logging()
    
    # Enable high DPI scaling - MUST be done before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application name and organization for settings
    app.setApplicationName("GraphNIST")
    app.setOrganizationName("GraphNIST")
    
    # Set current directory to application path for resource loading
    app_path = os.path.dirname(os.path.abspath(__file__))
    QDir.setCurrent(app_path)
    
    # Import main window here to avoid circular imports
    from views.main_window import MainWindow
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    main_window.resize(1200, 800)  # Set default size
    
    # Setup command manager after window is created
    # Pass the event_bus from main_window to UndoRedoManager
    undo_redo_manager = UndoRedoManager(main_window.event_bus)
    
    # Pass both undo_redo_manager and event_bus to CommandManager
    command_manager = CommandManager(undo_redo_manager, main_window.event_bus)
    main_window.command_manager = command_manager
    
    # Now that command_manager is set up, create the properties controller
    main_window.setup_properties_controller()
    
    # Setup controllers with undo/redo manager
    main_window.device_controller.undo_redo_manager = undo_redo_manager
    main_window.connection_controller.undo_redo_manager = undo_redo_manager
    main_window.boundary_controller.undo_redo_manager = undo_redo_manager
    
    # Set font settings manager on the device controller
    main_window.device_controller.font_settings_manager = main_window.font_settings_manager
    
    # Set theme manager on the connection controller
    main_window.connection_controller.theme_manager = main_window.theme_manager
    
    # Update undo/redo in the edit menu that was already created
    main_window._update_undo_redo_actions()
    
    # Apply font settings to existing devices
    for device in main_window.canvas.devices:
        device.update_font_settings(main_window.font_settings_manager)
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()