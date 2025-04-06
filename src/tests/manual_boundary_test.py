#!/usr/bin/env python3
"""
Manual test script for boundary resizing functionality.

This script creates a standalone test window with a single boundary
that can be selected and resized, without the complexity of the full application.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QBrush

# Import the boundary class
sys.path.insert(0, '..')  # Add parent directory to path
from models.boundary import Boundary

class BoundaryTestWindow(QMainWindow):
    """Test window for boundary resizing."""
    
    def __init__(self):
        super().__init__()
        
        # Set up logging
        logging.basicConfig(level=logging.DEBUG, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("Boundary Resize Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create scene and view
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 700, 500)
        
        # Set background color
        self.scene.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)
        
        # Create a boundary
        self.create_boundary()
        
    def create_boundary(self):
        """Create a test boundary in the scene."""
        # Create a boundary in the center of the scene
        rect = QRectF(200, 150, 300, 200)
        
        # Create blue semi-transparent boundary
        boundary = Boundary(rect, "Test Boundary", QColor(0, 0, 255, 100))
        
        # Add to scene
        self.scene.addItem(boundary)
        
        # Select it by default so resize handles are visible
        boundary.setSelected(True)
        
        self.logger.info(f"Created boundary: {boundary.name} with rect {boundary.rect()}")
        self.logger.info("Click and drag the resize handles to test resizing functionality")
        self.logger.info("The small squares in the corners are the resize handles")

def main():
    """Main entry point for the test application."""
    app = QApplication(sys.argv)
    window = BoundaryTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 