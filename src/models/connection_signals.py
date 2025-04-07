from PyQt5.QtCore import QObject, pyqtSignal

class ConnectionSignals(QObject):
    """Signals emitted by connections."""
    
    created = pyqtSignal(object)     # Connection object
    deleted = pyqtSignal(object)     # Connection object
    selected = pyqtSignal(object)    # Connection object
    modified = pyqtSignal(object)    # Connection object
    routing_changed = pyqtSignal(object, object)  # Connection, new_style
    source_updated = pyqtSignal(object)  # Connection object
    target_updated = pyqtSignal(object)  # Connection object 