from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QIcon, QFont
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PyQt5.QtWidgets import QApplication
import sys

def create_placeholder_icons():
    """Create simple placeholder icons for the application."""
    # Initialize QApplication first
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    icons = {
        "select.png": create_select_icon,
        "add_device.png": create_add_device_icon,
        "add_connection.png": create_add_connection_icon,
        "add_boundary.png": create_add_boundary_icon,
        "delete.png": create_delete_icon,
        "magnify.png": create_magnify_icon,
        "zoom_in.png": create_zoom_in_icon,
        "zoom_out.png": create_zoom_out_icon,
        "zoom_reset.png": create_zoom_reset_icon
    }
    
    for filename, icon_func in icons.items():
        pixmap = icon_func()
        pixmap.save(f"resources/icons/{filename}")
        print(f"Created {filename}")

def create_select_icon():
    """Create a select tool icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw cursor arrow
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.setBrush(QBrush(QColor(220, 220, 220)))
    
    points = [QPoint(8, 8), QPoint(22, 18), QPoint(18, 22), QPoint(22, 26), QPoint(26, 22), QPoint(22, 18)]
    painter.drawPolygon(*points)
    
    painter.end()
    return pixmap

def create_add_device_icon():
    """Create an add device icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw computer/device shape
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.setBrush(QBrush(QColor(200, 220, 240)))
    painter.drawRect(8, 8, 16, 12)
    
    # Draw stand
    painter.drawRect(12, 20, 8, 4)
    
    # Draw plus sign
    painter.setPen(QPen(QColor(0, 180, 0), 2))
    painter.drawLine(26, 8, 26, 16)
    painter.drawLine(22, 12, 30, 12)
    
    painter.end()
    return pixmap

def create_add_connection_icon():
    """Create an add connection icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw two circles
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.setBrush(QBrush(QColor(200, 220, 240)))
    painter.drawEllipse(6, 6, 10, 10)
    painter.drawEllipse(16, 16, 10, 10)
    
    # Draw connection line
    painter.setPen(QPen(QColor(40, 40, 40), 2, Qt.DashLine))
    painter.drawLine(12, 12, 20, 20)
    
    painter.end()
    return pixmap

def create_add_boundary_icon():
    """Create an add boundary icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw dashed rectangle
    painter.setPen(QPen(QColor(40, 40, 40), 2, Qt.DashLine))
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(6, 6, 20, 20)
    
    painter.end()
    return pixmap

def create_delete_icon():
    """Create a delete icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw X
    painter.setPen(QPen(QColor(200, 40, 40), 3))
    painter.drawLine(8, 8, 24, 24)
    painter.drawLine(24, 8, 8, 24)
    
    painter.end()
    return pixmap

def create_magnify_icon():
    """Create a magnifying glass icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw magnifying glass circle
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.setBrush(QBrush(QColor(240, 240, 240, 180)))
    painter.drawEllipse(8, 8, 14, 14)
    
    # Draw handle
    painter.setPen(QPen(QColor(40, 40, 40), 3))
    painter.drawLine(20, 20, 26, 26)
    
    # Draw plus sign inside
    painter.setPen(QPen(QColor(40, 40, 40), 1))
    painter.drawLine(15, 15, 15, 15)
    
    painter.end()
    return pixmap

def create_zoom_in_icon():
    """Create a zoom in icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw magnifying glass circle
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.setBrush(QBrush(QColor(240, 240, 240, 180)))
    painter.drawEllipse(8, 8, 14, 14)
    
    # Draw handle
    painter.setPen(QPen(QColor(40, 40, 40), 3))
    painter.drawLine(20, 20, 26, 26)
    
    # Draw plus sign inside
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.drawLine(12, 15, 18, 15)
    painter.drawLine(15, 12, 15, 18)
    
    painter.end()
    return pixmap

def create_zoom_out_icon():
    """Create a zoom out icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw magnifying glass circle
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.setBrush(QBrush(QColor(240, 240, 240, 180)))
    painter.drawEllipse(8, 8, 14, 14)
    
    # Draw handle
    painter.setPen(QPen(QColor(40, 40, 40), 3))
    painter.drawLine(20, 20, 26, 26)
    
    # Draw minus sign inside
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.drawLine(12, 15, 18, 15)
    
    painter.end()
    return pixmap

def create_zoom_reset_icon():
    """Create a zoom reset icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw magnifying glass circle
    painter.setPen(QPen(QColor(40, 40, 40), 2))
    painter.setBrush(QBrush(QColor(240, 240, 240, 180)))
    painter.drawEllipse(8, 8, 14, 14)
    
    # Draw handle
    painter.setPen(QPen(QColor(40, 40, 40), 3))
    painter.drawLine(20, 20, 26, 26)
    
    # Draw "1:1" text
    painter.setPen(QPen(QColor(40, 40, 40)))
    painter.setFont(QFont("Arial", 7))
    painter.drawText(QRect(9, 10, 12, 10), Qt.AlignCenter, "1:1")
    
    painter.end()
    return pixmap

if __name__ == "__main__":
    create_placeholder_icons() 