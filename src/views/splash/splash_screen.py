import logging
import os
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

class SplashScreen:
    """Handles the splash screen display and lifecycle."""
    
    def __init__(self, app, icon_path=None, scale_factor=0.7):
        """
        Initialize the splash screen.
        
        Args:
            app: The QApplication instance
            icon_path: Path to the splash screen image
            scale_factor: Factor to scale the splash image (0.7 = 70% of original size)
        """
        self.app = app
        self.splash = None
        self.logger = logging.getLogger(__name__)
        
        # Try to create the splash screen
        try:
            if icon_path and os.path.exists(icon_path):
                self.logger.info(f"Loading splash screen from: {icon_path}")
                splash_pixmap = QPixmap(icon_path)
                
                if not splash_pixmap.isNull():
                    # Scale the pixmap down if requested
                    if scale_factor != 1.0:
                        original_size = splash_pixmap.size()
                        scaled_width = int(original_size.width() * scale_factor)
                        scaled_height = int(original_size.height() * scale_factor)
                        splash_pixmap = splash_pixmap.scaled(scaled_width, scaled_height, 
                                                          Qt.KeepAspectRatio, 
                                                          Qt.SmoothTransformation)
                    
                    # Create splash screen with the pixmap
                    self.splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
                    self.splash.setWindowFlag(Qt.FramelessWindowHint)
                    
                    # Center splash on screen
                    self._center_on_screen()
                    
                    self.logger.info(f"Splash screen created with size: {splash_pixmap.width()}x{splash_pixmap.height()}")
                else:
                    self.logger.warning("Failed to load splash screen image (null pixmap)")
            else:
                self.logger.warning(f"Splash screen image not found at path: {icon_path}")
        except Exception as e:
            self.logger.error(f"Error creating splash screen: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.splash = None
    
    def _center_on_screen(self):
        """Center the splash screen on the primary display."""
        if self.splash:
            screen = self.app.primaryScreen().geometry()
            splash_size = self.splash.size()
            self.splash.move((screen.width() - splash_size.width()) // 2,
                           (screen.height() - splash_size.height()) // 2)
    
    def show(self, message="Initializing..."):
        """Show the splash screen with an optional message."""
        if self.splash:
            self.splash.show()
            self.update_message(message)
            self.app.processEvents()
            return True
        return False
    
    def update_message(self, message):
        """Update the splash screen message."""
        if self.splash:
            self.splash.showMessage(message, 
                                   alignment=Qt.AlignBottom | Qt.AlignCenter, 
                                   color=Qt.white)
            self.app.processEvents()
    
    def close(self):
        """Close the splash screen."""
        if self.splash:
            self.splash.close()
            self.splash = None
    
    def delay_close(self, ms, callback=None):
        """Close after a delay and optionally call a function."""
        if self.splash:
            def _close_splash():
                self.close()
                if callback:
                    callback()
            
            QTimer.singleShot(ms, _close_splash)
            return True
        else:
            # If no splash, call the callback immediately
            if callback:
                callback()
            return False 