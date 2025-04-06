import sys
import unittest
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PyQt5.QtCore import Qt, QPointF, QRectF, QEvent
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QColor, QMouseEvent

# Add parent directory to path to make imports work
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the boundary class
from src.models.boundary import Boundary

# Create a mock theme manager for testing
class MockThemeManager:
    """A simple mock for the theme manager used in testing."""
    
    def __init__(self, is_dark=False):
        self.dark_theme = is_dark
        
    def is_dark_theme(self):
        return self.dark_theme

class TestBoundaryEventHandling(unittest.TestCase):
    """Test case for boundary event handling functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Create the QApplication once for all tests."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
            
    def setUp(self):
        """Set up the test fixture."""
        # Create a scene, view, and boundary for testing
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        
        # Create a mock theme manager
        self.theme_manager = MockThemeManager()
        
        # Create a boundary with known size
        self.initial_rect = QRectF(100, 100, 200, 150)
        self.boundary = Boundary(self.initial_rect, "Test Boundary", QColor(0, 0, 255, 128), 
                                theme_manager=self.theme_manager)
        
        # Add to scene
        self.scene.addItem(self.boundary)
        
        # Select the boundary so resize handles are active
        self.boundary.setSelected(True)
        
        # Log setup
        print(f"Test setup: Boundary created with rect {self.initial_rect}")
        
    def test_boundary_properties(self):
        """Test basic properties of the boundary."""
        # Test the boundary's rect
        self.assertEqual(self.boundary.rect(), self.initial_rect, "Boundary rectangle should match initial rect")
        
        # Test the boundary's name
        self.assertEqual(self.boundary.name, "Test Boundary", "Boundary name should match")
        
        # Test selection state
        self.assertTrue(self.boundary.isSelected(), "Boundary should be selected")
        
        # Test initial resize state
        self.assertFalse(self.boundary._resizing, "Boundary should not be in resize mode initially")
        self.assertIsNone(self.boundary._resize_handle, "No resize handle should be selected initially")
        
        # Check resize handles exist
        self.assertIn('NW', self.boundary._handles, "NW resize handle should exist")
        self.assertIn('SE', self.boundary._handles, "SE resize handle should exist")
        
    def test_handle_positions(self):
        """Test that resize handle positions are calculated correctly."""
        # Get handle rectangles
        nw_rect = self.boundary._get_handle_rect('NW')
        se_rect = self.boundary._get_handle_rect('SE')
        e_rect = self.boundary._get_handle_rect('E')
        s_rect = self.boundary._get_handle_rect('S')
        
        # Check positions relative to boundary
        # The rect in boundary is the initial_rect (which was passed to constructor)
        rect = self.boundary.rect()
        
        # NW handle should be at the top-left of the rect
        self.assertEqual(nw_rect.left(), rect.left(), "NW handle should be at left edge of rect")
        self.assertEqual(nw_rect.top(), rect.top(), "NW handle should be at top edge of rect")
        
        handle_size = self.boundary._resize_handle_size
        
        # SE handle should be at bottom-right of rect minus handle size
        self.assertAlmostEqual(se_rect.left(), rect.right() - handle_size, delta=1.0, 
                               msg="SE handle should be at right edge minus handle size")
        self.assertAlmostEqual(se_rect.top(), rect.bottom() - handle_size, delta=1.0,
                               msg="SE handle should be at bottom edge minus handle size")
                               
        # E handle should be at the middle right of the rect
        self.assertAlmostEqual(e_rect.left(), rect.right() - handle_size, delta=1.0, 
                              msg="E handle should be at right edge minus handle size")
        self.assertAlmostEqual(e_rect.top(), rect.top() + rect.height()/2 - handle_size/2, delta=1.0,
                              msg="E handle should be at vertical center of rect")
        
        # S handle should be at the bottom middle of the rect
        self.assertAlmostEqual(s_rect.left(), rect.left() + rect.width()/2 - handle_size/2, delta=1.0,
                              msg="S handle should be at horizontal center of rect")
        self.assertAlmostEqual(s_rect.top(), rect.bottom() - handle_size, delta=1.0,
                              msg="S handle should be at bottom edge minus handle size")
    
    def test_all_resize_handles_exist(self):
        """Test that all 8 resize handles are properly implemented."""
        # The boundary should have 8 resize handles
        expected_handles = ['NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W']
        for handle in expected_handles:
            self.assertIn(handle, self.boundary._handles, f"{handle} resize handle should exist")
            # Get the rectangle for this handle
            handle_rect = self.boundary._get_handle_rect(handle)
            self.assertIsNotNone(handle_rect, f"{handle} handle rect should be properly defined")
            self.assertFalse(handle_rect.isEmpty(), f"{handle} handle rect should not be empty")
    
    def test_boundary_color(self):
        """Test that boundary color can be set and retrieved properly."""
        # Initial color (from constructor)
        initial_color = self.boundary.color
        self.assertEqual(initial_color, QColor(0, 0, 255, 128), "Initial color should match constructor parameter")
        
        # Set a new color
        new_color = QColor(255, 0, 0, 150)  # Semi-transparent red
        self.boundary.set_color(new_color)
        
        # Verify the color was updated
        self.assertEqual(self.boundary.color, new_color, "Color should be updated after set_color call")
        
        # The brush should also be updated
        brush_color = self.boundary.brush().color()
        self.assertEqual(brush_color, new_color, "Brush color should match the boundary color")

if __name__ == '__main__':
    unittest.main() 