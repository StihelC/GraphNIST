import sys
import unittest
from PyQt5.QtWidgets import QApplication, QGraphicsScene
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QColor

# Import the boundary class
from models.boundary.boundary import Boundary

class TestBoundaryResize(unittest.TestCase):
    """Test case for boundary resizing functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Create the QApplication once for all tests."""
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
            
    def setUp(self):
        """Set up the test fixture."""
        # Create a scene and boundary for testing
        self.scene = QGraphicsScene()
        
        # Create a boundary with known size
        self.initial_rect = QRectF(100, 100, 200, 150)
        self.boundary = Boundary(self.initial_rect, "Test Boundary", QColor(0, 0, 255, 128))
        
        # Add to scene
        self.scene.addItem(self.boundary)
        
        # Select the boundary so resize handles are active
        self.boundary.setSelected(True)
        
        # Log setup
        print(f"Test setup: Boundary created with rect {self.initial_rect}")
        
    def test_resize_se_handle(self):
        """Test resizing the boundary using the southeast handle."""
        # Get initial state
        initial_rect = self.boundary.rect()
        print(f"Initial rect: {initial_rect}")
        
        # Ensure boundary is selected
        self.boundary.setSelected(True)
        
        # Find the position of the southeast handle
        se_handle_pos = QPointF(
            initial_rect.right() - 5,  # Center of handle
            initial_rect.bottom() - 5
        )
        
        # Create a delta to drag
        delta_x = 50
        delta_y = 30
        
        # Simulate a mouse press on the SE handle
        self.boundary._resize_handle = 'SE'  # Force resize mode
        self.boundary._resizing = True
        self.boundary._resize_start_pos = se_handle_pos
        self.boundary._resize_start_rect = initial_rect
        
        # Simulate a mouse move
        drag_pos = se_handle_pos + QPointF(delta_x, delta_y)
        
        # Create a mock event
        class MockMouseEvent:
            def __init__(self, pos):
                self._pos = pos
            
            def pos(self):
                return self._pos
                
            def accept(self):
                pass
        
        mock_event = MockMouseEvent(drag_pos)
        
        # Trigger the resize by calling mouseMoveEvent
        self.boundary.mouseMoveEvent(mock_event)
        
        # Check if the boundary was resized
        new_rect = self.boundary.rect()
        print(f"New rect after resize: {new_rect}")
        
        # Check if width and height changed by the expected amount
        self.assertAlmostEqual(new_rect.width(), initial_rect.width() + delta_x, delta=1.0)
        self.assertAlmostEqual(new_rect.height(), initial_rect.height() + delta_y, delta=1.0)
        
        # Verify the top-left position didn't change
        self.assertAlmostEqual(new_rect.left(), initial_rect.left(), delta=1.0)
        self.assertAlmostEqual(new_rect.top(), initial_rect.top(), delta=1.0)
        
    def test_resize_nw_handle(self):
        """Test resizing the boundary using the northwest handle."""
        # Get initial state
        initial_rect = self.boundary.rect()
        print(f"Initial rect: {initial_rect}")
        
        # Find the position of the northwest handle
        nw_handle_pos = QPointF(
            initial_rect.left() + 5,  # Center of handle
            initial_rect.top() + 5
        )
        
        # Create a delta to drag
        delta_x = -30  # Move left
        delta_y = -20  # Move up
        
        # Simulate a mouse press on the NW handle
        self.boundary._resize_handle = 'NW'  # Force resize mode
        self.boundary._resizing = True
        self.boundary._resize_start_pos = nw_handle_pos
        self.boundary._resize_start_rect = initial_rect
        
        # Simulate a mouse move
        drag_pos = nw_handle_pos + QPointF(delta_x, delta_y)
        
        # Create a mock event
        class MockMouseEvent:
            def __init__(self, pos):
                self._pos = pos
            
            def pos(self):
                return self._pos
                
            def accept(self):
                pass
        
        mock_event = MockMouseEvent(drag_pos)
        
        # Trigger the resize by calling mouseMoveEvent
        self.boundary.mouseMoveEvent(mock_event)
        
        # Check if the boundary was resized
        new_rect = self.boundary.rect()
        print(f"New rect after resize: {new_rect}")
        
        # Check if width and height changed by the expected amount
        self.assertAlmostEqual(new_rect.width(), initial_rect.width() - delta_x, delta=1.0)
        self.assertAlmostEqual(new_rect.height(), initial_rect.height() - delta_y, delta=1.0)
        
        # Verify the top-left position moved
        self.assertAlmostEqual(new_rect.left(), initial_rect.left() + delta_x, delta=1.0)
        self.assertAlmostEqual(new_rect.top(), initial_rect.top() + delta_y, delta=1.0)
        
    def test_detect_handle(self):
        """Test that resize handles are properly detected on a boundary."""
        # Get the SE handle position
        rect = self.boundary.rect()
        se_pos = QPointF(rect.right() - 5, rect.bottom() - 5)
        
        # Test detection
        handle = self.boundary._handle_at_position(se_pos)
        
        # Should detect the SE handle
        self.assertEqual(handle, 'SE', "Should detect SE resize handle")
        
        # Check another position
        nw_pos = QPointF(rect.left() + 5, rect.top() + 5)
        handle = self.boundary._handle_at_position(nw_pos)
        
        # Should detect the NW handle
        self.assertEqual(handle, 'NW', "Should detect NW resize handle")
        
        # Test a point not on a handle
        center_pos = QPointF(rect.center())
        handle = self.boundary._handle_at_position(center_pos)
        
        # Should not detect any handle
        self.assertIsNone(handle, "Should not detect a handle in the center")

if __name__ == '__main__':
    unittest.main() 