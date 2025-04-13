from PyQt5.QtCore import QObject, pyqtSignal

class DeviceSignals(QObject):
    """Signals emitted by devices."""
    moved = pyqtSignal(object)  # device
    double_clicked = pyqtSignal(object)  # device
    deleted = pyqtSignal(object)  # device
    drag_started = pyqtSignal(object)  # device
    drag_finished = pyqtSignal(object)  # device
    property_changed = pyqtSignal(object, str, object)  # device, property_name, value
    position_changed = pyqtSignal(object, object, object)  # device, old_pos, new_pos 