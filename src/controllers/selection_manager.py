from PyQt5.QtCore import QObject, pyqtSignal
import logging

class SelectionManager(QObject):
    """Manages selection state and events for the canvas."""
    
    # Signals
    selection_changed = pyqtSignal(list)  # Emitted when selection changes
    single_item_selected = pyqtSignal(object)  # Emitted when a single item is selected
    multiple_items_selected = pyqtSignal(list)  # Emitted when multiple items are selected
    selection_cleared = pyqtSignal()  # Emitted when selection is cleared
    
    def __init__(self, canvas, properties_controller):
        """Initialize the selection manager."""
        super().__init__()
        self.canvas = canvas
        self.properties_controller = properties_controller
        self.logger = logging.getLogger(__name__)
        
        # Connect canvas signals
        if hasattr(canvas, 'selection_changed'):
            canvas.selection_changed.connect(self._on_canvas_selection_changed)
        
        # Connect device signals
        for device in canvas.devices:
            if hasattr(device, 'signals') and hasattr(device.signals, 'selected'):
                device.signals.selected.connect(self._on_device_selected)
    
    def _on_canvas_selection_changed(self, selected_items):
        """Handle selection changes from the canvas."""
        self.logger.debug(f"SELECTION DEBUG: Canvas selection changed. Items: {[type(item).__name__ for item in selected_items]}")
        self.logger.debug(f"SELECTION DEBUG: Selection source: Canvas scene selection changed")
        
        if not selected_items:
            self.logger.debug("SELECTION DEBUG: No items selected, clearing selection")
            self._handle_selection_cleared()
            return
            
        if len(selected_items) == 1:
            self.logger.debug(f"SELECTION DEBUG: Single item selected: {type(selected_items[0]).__name__}")
            self._handle_single_selection(selected_items[0])
        else:
            self.logger.debug(f"SELECTION DEBUG: Multiple items selected: {len(selected_items)}")
            self._handle_multiple_selection(selected_items)
    
    def _on_device_selected(self, device):
        """Handle device selection events."""
        self.logger.debug(f"SELECTION DEBUG: Device selected: {device.name} (ID: {id(device)})")
        self.logger.debug(f"SELECTION DEBUG: Selection source: Device direct selection")
        self._handle_single_selection(device)
    
    def _handle_single_selection(self, item):
        """Handle single item selection."""
        self.logger.debug(f"SELECTION DEBUG: Handling single selection for {type(item).__name__} (ID: {id(item)})")
        self.selected_items = [item]
        self.single_item_selected.emit(item)
        self.selection_changed.emit(self.selected_items)
        
        # Update properties panel
        if self.properties_controller:
            self.logger.debug("SELECTION DEBUG: Updating properties panel for single selection")
            self.properties_controller.update_properties_panel([item])
    
    def _handle_multiple_selection(self, items):
        """Handle multiple items selection."""
        self.logger.debug(f"SELECTION DEBUG: Handling multiple selection for {len(items)} items")
        self.selected_items = items
        self.multiple_items_selected.emit(items)
        self.selection_changed.emit(self.selected_items)
        
        # Update properties panel
        if self.properties_controller:
            self.logger.debug("SELECTION DEBUG: Updating properties panel for multiple selection")
            self.properties_controller.update_properties_panel(items)
    
    def _handle_selection_cleared(self):
        """Handle selection being cleared."""
        self.logger.debug("SELECTION DEBUG: Handling selection cleared")
        self.selected_items = []
        self.selection_cleared.emit()
        self.selection_changed.emit([])
        
        # Clear properties panel
        if self.properties_controller:
            self.logger.debug("SELECTION DEBUG: Clearing properties panel")
            self.properties_controller.update_properties_panel([])
    
    def select_item(self, item, clear_existing=True):
        """Select a single item, optionally clearing existing selection."""
        if clear_existing:
            self.canvas.scene().clearSelection()
        item.setSelected(True)
    
    def select_items(self, items, clear_existing=True):
        """Select multiple items, optionally clearing existing selection."""
        if clear_existing:
            self.canvas.scene().clearSelection()
        for item in items:
            item.setSelected(True)
    
    def clear_selection(self):
        """Clear all selection."""
        self.canvas.scene().clearSelection() 