from PyQt5.QtCore import QObject, pyqtSignal

class BoundarySignals(QObject):
    """Signals for the Boundary class."""
    name_changed = pyqtSignal(object, str)  # boundary, new_name
    selected = pyqtSignal(object, bool)  # boundary, is_selected
    drag_started = pyqtSignal(object)  # boundary
    drag_finished = pyqtSignal(object)  # boundary 