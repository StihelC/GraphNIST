from PyQt5.QtCore import QObject, pyqtSignal

class ConnectionSignals(QObject):
    """Signals for connection events."""
    selected = pyqtSignal(object)  # connection
    deleted = pyqtSignal(object)   # connection
    updated = pyqtSignal(object)   # connection 