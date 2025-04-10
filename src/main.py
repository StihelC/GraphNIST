import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDir, Qt, QTimer
import os
import datetime

from views.main_window import MainWindow
from controllers.command_manager import CommandManager
from controllers.undo_redo_manager import UndoRedoManager
from views.splash import SplashScreen

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

def initialize_application(splash):
    """Initialize the application with progress updates shown in splash screen."""
    # Import main window here to avoid circular imports
    splash.update_message("Creating main window...")
    from views.main_window import MainWindow
    
    # Create main window
    main_window = MainWindow()
    
    # Update splash message
    splash.update_message("Setting up controllers...")
    
    # Setup command manager after window is created
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
    
    # Update splash message
    splash.update_message("Initializing UI components...")
    
    # Set font settings manager on the device controller
    main_window.device_controller.font_settings_manager = main_window.font_settings_manager
    
    # Set theme manager on the connection controller
    main_window.connection_controller.theme_manager = main_window.theme_manager
    
    # Update undo/redo in the edit menu that was already created
    main_window._update_undo_redo_actions()
    
    # Final splash message
    splash.update_message("Starting GraphNIST...")
    
    # Apply font settings to existing devices
    for device in main_window.canvas.devices:
        device.update_font_settings(main_window.font_settings_manager)
    
    return main_window

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
    
    # Create the splash screen with 70% of the original size
    splash_path = os.path.join(app_path, 'resources', 'icons', 'svg', 'loading.png')
    splash = SplashScreen(app, splash_path, scale_factor=0.7)
    
    # Show splash screen with initial message
    if not splash.show("Initializing..."):
        # If splash failed, initialize and show main window immediately
        main_window = initialize_application(splash)
        main_window.show()
        main_window.resize(1200, 800)
    else:
        # Initialize with splash screen
        main_window = initialize_application(splash)
        
        # Set up function to close splash and show main window
        def show_main_window():
            main_window.show()
            main_window.resize(1200, 800)
        
        # Schedule splash screen to close after 1500ms
        splash.delay_close(1500, show_main_window)
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()