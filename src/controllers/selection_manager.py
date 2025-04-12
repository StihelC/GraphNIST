from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import logging
from models.connection.connection import Connection

class SelectionManager(QObject):
    """
    Centralized manager for selection state and events.
    
    This class implements a unidirectional data flow for selection:
    1. Selection changes come from Canvas scene only
    2. SelectionManager maintains the canonical selection state
    3. All components observe selection via the event bus
    """
    
    # Signals for backward compatibility during transition
    selection_changed = pyqtSignal(list)  # Emitted when selection changes
    single_item_selected = pyqtSignal(object)  # Emitted when a single item is selected
    multiple_items_selected = pyqtSignal(list)  # Emitted when multiple items are selected
    selection_cleared = pyqtSignal()  # Emitted when selection is cleared
    
    def __init__(self, canvas, event_bus, properties_controller=None):
        """Initialize the selection manager."""
        super().__init__()
        self.canvas = canvas
        self.event_bus = event_bus
        self.properties_controller = properties_controller
        self.logger = logging.getLogger(__name__)
        
        # Track selected items
        self.selected_items = []
        
        # Add debounce timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._process_pending_update)
        self.pending_update = None
        
        # Connect to canvas selection events only
        if hasattr(canvas, 'selection_changed'):
            canvas.selection_changed.connect(self._on_canvas_selection_changed)
        
        # Register selection events on the event bus
        self._register_event_handlers()

    def _register_event_handlers(self):
        """Register selection-related event handlers on the event bus."""
        if self.event_bus:
            # Register selection events that other controllers can listen for
            self.event_bus.register_controller('selection_manager', self)
            
            # Listen for selection command events (for programmatic selection)
            self.event_bus.on('select_item', self.select_item)
            self.event_bus.on('select_items', self.select_items)
            self.event_bus.on('clear_selection', self.clear_selection)
    
    def _process_pending_update(self):
        """Process the pending update after debounce delay."""
        if self.pending_update:
            self.logger.debug(f"SELECTION DEBUG: Processing pending update for {self.pending_update['type']}")
            if self.pending_update['type'] == 'single':
                self._handle_single_selection(self.pending_update['item'])
            elif self.pending_update['type'] == 'multiple':
                self._handle_multiple_selection(self.pending_update['items'])
            elif self.pending_update['type'] == 'clear':
                self._handle_selection_cleared()
            self.pending_update = None
    
    def _on_canvas_selection_changed(self, selected_items):
        """Handle selection changes from the canvas (single source of truth)."""
        self.logger.debug(f"SELECTION DEBUG: Canvas selection changed. Items: {[type(item).__name__ for item in selected_items]}")
        
        # IMPORTANT: Skip processing selection changes when in boundary creation mode
        # This prevents conflicts between selection handling and boundary creation
        if self.canvas and hasattr(self.canvas, 'mode_manager') and hasattr(self.canvas.mode_manager, 'current_mode'):
            from constants import Modes
            if self.canvas.mode_manager.current_mode == Modes.ADD_BOUNDARY:
                self.logger.debug("SELECTION DEBUG: Bypassing selection processing during boundary creation")
                return
        
        # Skip update if we're in the middle of a drag operation
        if self._is_drag_in_progress():
            self.logger.debug("SELECTION DEBUG: Skipping update during drag operation")
            return
        
        # Stop any pending timer
        self.update_timer.stop()
        
        if not selected_items:
            self.pending_update = {'type': 'clear'}
        elif len(selected_items) == 1:
            self.pending_update = {'type': 'single', 'item': selected_items[0]}
        else:
            self.pending_update = {'type': 'multiple', 'items': selected_items}
        
        # Start debounce timer with longer delay
        self.update_timer.start(250)  # 250ms debounce
    
    def _is_drag_in_progress(self):
        """Check if a drag operation is in progress."""
        if not self.canvas:
            return False
            
        # Check group selection manager first
        if hasattr(self.canvas, 'group_selection_manager') and self.canvas.group_selection_manager:
            if self.canvas.group_selection_manager.is_drag_active():
                return True
                
        # Then check canvas's drag tracking
        return hasattr(self.canvas, '_drag_item') and self.canvas._drag_item is not None
    
    def _handle_single_selection(self, item):
        """Handle single item selection."""
        self.logger.debug(f"Selection: Single item {type(item).__name__} (ID: {id(item)})")
        self.selected_items = [item]
        
        # Emit signals for backward compatibility
        self.single_item_selected.emit(item)
        self.selection_changed.emit(self.selected_items)
        
        # Publish selection event to the event bus, but only use one event
        if self.event_bus:
            self.event_bus.emit('selection.changed', items=self.selected_items, count=1, type="single", item=item)
        
        # Only update properties panel directly if no event bus is available
        if self.properties_controller and not self.event_bus:
            self.logger.debug("Directly updating properties panel")
            self.properties_controller.update_properties_panel([item])
    
    def _handle_multiple_selection(self, items):
        """Handle multiple items selection."""
        self.logger.debug(f"Selection: Multiple items ({len(items)})")
        self.selected_items = items
        
        # Emit signals for backward compatibility
        self.multiple_items_selected.emit(items)
        self.selection_changed.emit(self.selected_items)
        
        # Publish selection event to the event bus, but only use one event
        if self.event_bus:
            self.event_bus.emit('selection.changed', items=self.selected_items, count=len(items), type="multiple")
        
        # Only update properties panel directly if no event bus is available
        if self.properties_controller and not self.event_bus:
            self.logger.debug("Directly updating properties panel")
            self.properties_controller.update_properties_panel(items)
    
    def _handle_selection_cleared(self):
        """Handle selection being cleared."""
        self.logger.debug("Selection: Cleared")
        self.selected_items = []
        
        # Emit signals for backward compatibility
        self.selection_cleared.emit()
        self.selection_changed.emit([])
        
        # Publish selection event to the event bus, but only use one event
        if self.event_bus:
            self.event_bus.emit('selection.changed', items=[], count=0, type="cleared")
        
        # Only update properties panel directly if no event bus is available
        if self.properties_controller and not self.event_bus:
            self.logger.debug("Directly updating properties panel")
            self.properties_controller.update_properties_panel([])
    
    def select_item(self, item, clear_existing=True):
        """Select a single item, optionally clearing existing selection."""
        if clear_existing:
            self.canvas.scene().clearSelection()
        item.setSelected(True)
        
        # Force immediate update - skip debounce for programmatic selection
        selected_items = self.canvas.scene().selectedItems()
        if len(selected_items) == 1:
            self._handle_single_selection(item)
        else:
            self._handle_multiple_selection(selected_items)
    
    def select_items(self, items, clear_existing=True):
        """Select multiple items, optionally clearing existing selection."""
        if clear_existing:
            self.canvas.scene().clearSelection()
        for item in items:
            item.setSelected(True)
        
        # Force immediate update - skip debounce for programmatic selection
        selected_items = self.canvas.scene().selectedItems()
        if len(selected_items) > 0:
            self._handle_multiple_selection(selected_items)
    
    def clear_selection(self):
        """Clear all selection."""
        self.canvas.scene().clearSelection()
        
        # Force immediate update - skip debounce for programmatic clear
        self._handle_selection_cleared()
    
    def get_selected_items(self):
        """Get the current selection (used by controllers to query selection state)."""
        return self.selected_items.copy()
    
    def get_selected_devices(self):
        """Get only devices from the current selection."""
        from models.device import Device
        return [item for item in self.selected_items if isinstance(item, Device)]
    
    def get_selected_boundaries(self):
        """Get only boundaries from the current selection."""
        from models.boundary.boundary import Boundary
        return [item for item in self.selected_items if isinstance(item, Boundary)]
    
    def get_selected_connections(self):
        """Get only connections from the current selection."""
        return [item for item in self.selected_items if isinstance(item, Connection)] 