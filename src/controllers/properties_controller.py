from PyQt5.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLabel, QCheckBox, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QPointF, QTimer
from PyQt5.QtGui import QColor
import logging
import traceback

from models.device import Device
from models.connection import Connection
from models.boundary import Boundary
from controllers.commands import (
    UpdatePropertyCommand, SetZValueCommand, UpdateNameCommand, Command,
    TogglePropertyDisplayCommand, UpdateConnectionTypeCommand,
    UpdateConnectionStyleCommand
)

class SetItemNameCommand(Command):
    """Command to change an item's name."""
    
    def __init__(self, item, old_name, new_name):
        super().__init__(f"Change {type(item).__name__} Name")
        self.item = item
        self.old_name = old_name
        self.new_name = new_name
    
    def execute(self):
        self.item.name = self.new_name
        if hasattr(self.item, 'update_name'):
            self.item.update_name()
        elif hasattr(self.item, 'text_item'):
            self.item.text_item.setPlainText(self.new_name)
    
    def undo(self):
        self.item.name = self.old_name
        if hasattr(self.item, 'update_name'):
            self.item.update_name()
        elif hasattr(self.item, 'text_item'):
            self.item.text_item.setPlainText(self.old_name)

class SetItemZValueCommand(Command):
    """Command to change an item's Z value (layer)."""
    
    def __init__(self, item, old_value, new_value):
        super().__init__(f"Change {type(item).__name__} Layer")
        self.item = item
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        self.item.setZValue(self.new_value)
    
    def undo(self):
        self.item.setZValue(self.old_value)

class PropertiesController:
    """Controller for managing properties panel interactions."""
    
    def __init__(self, canvas, properties_panel, event_bus, undo_redo_manager=None):
        """Initialize the properties controller."""
        super().__init__()
        self.canvas = canvas
        self.panel = properties_panel
        self.event_bus = event_bus
        self.undo_redo_manager = undo_redo_manager
        self.logger = logging.getLogger(__name__)
        self.selected_item = None
        self.selected_items = []
        
        # Add debounce timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._process_pending_update)
        self.pending_update = None
        
        # Connect panel signals
        self.panel.name_changed.connect(self._on_name_changed)
        self.panel.z_value_changed.connect(self._on_z_value_changed)
        self.panel.device_property_changed.connect(self._on_device_property_changed)
        self.panel.connection_property_changed.connect(self._on_connection_property_changed)
        self.panel.boundary_property_changed.connect(self._on_boundary_property_changed)
        self.panel.change_icon_requested.connect(self._on_change_icon_requested)
        self.panel.property_display_toggled.connect(self._on_property_display_toggled)
        self.panel.property_delete_requested.connect(self._on_property_delete_requested)
        
        # Subscribe to selection events on the event bus
        self._register_event_handlers()
        
        # Initialize selection manager reference (will be set externally)
        self.selection_manager = None
    
    def _register_event_handlers(self):
        """Register for selection events on the event bus."""
        if self.event_bus:
            # Register this controller
            self.event_bus.register_controller('properties_controller', self)
            
            # Subscribe to the consolidated selection events
            self.event_bus.on('selection.changed', self._on_selection_changed)
    
    def _on_selection_changed(self, items=None, count=0, type=None, item=None, **kwargs):
        """Handle consolidated selection change events from event bus."""
        if not self.event_bus:
            return
            
        self.logger.debug(f"Properties: Selection change of type '{type}' with {count} items")
        
        if type == "single" and item:
            self._on_single_item_selected(item)
        elif type == "multiple" and items:
            self._on_multiple_items_selected(items)
        elif type == "cleared" or count == 0:
            self._on_selection_cleared()
        elif count == 1 and items:
            # Fallback for single item in items list
            self._on_single_item_selected(items[0])
        elif count > 1 and items:
            # Fallback for multiple items
            self._on_multiple_items_selected(items)
    
    def _process_pending_update(self):
        """Process the pending update after debounce delay."""
        if self.pending_update:
            self.logger.debug(f"PROPERTIES DEBUG: Processing pending update for {self.pending_update['type']}")
            if self.pending_update['type'] == 'single':
                self._on_single_item_selected(self.pending_update['item'])
            elif self.pending_update['type'] == 'multiple':
                self._on_multiple_items_selected(self.pending_update['items'])
            elif self.pending_update['type'] == 'clear':
                self._on_selection_cleared()
            self.pending_update = None
    
    def update_properties_panel(self, selected_items=None):
        """Update properties panel based on selection with debounce."""
        self.logger.debug(f"PROPERTIES DEBUG: Update requested for {len(selected_items) if selected_items else 0} items")
        
        # Stop any pending timer
        self.update_timer.stop()
        
        if not selected_items:
            self.pending_update = {'type': 'clear'}
        elif len(selected_items) == 1:
            self.pending_update = {'type': 'single', 'item': selected_items[0]}
        else:
            self.pending_update = {'type': 'multiple', 'items': selected_items}
        
        # Start debounce timer
        self.update_timer.start(100)  # 100ms debounce
    
    def _on_single_item_selected(self, item):
        """Handle single item selection."""
        self.logger.debug(f"PROPERTIES DEBUG: Processing single item selection for {type(item).__name__} (ID: {id(item)})")
        self.selected_item = item
        self.selected_items = []
        
        # Ensure panel is visible
        if hasattr(self.panel, 'parent') and hasattr(self.panel.parent(), 'setVisible'):
            self.logger.debug("PROPERTIES DEBUG: Making properties panel visible")
            self.panel.parent().setVisible(True)
            self.panel.parent().raise_()
            
        # Update panel
        self.logger.debug("PROPERTIES DEBUG: Updating properties panel for single item")
        
        # If the item is a boundary name text item, get its parent boundary
        if hasattr(item, 'parentItem') and isinstance(item.parentItem(), Boundary):
            item = item.parentItem()
            
        self.panel.display_item_properties(item)
        
        # If a boundary is selected, find contained devices
        if isinstance(item, Boundary):
            self.logger.debug("PROPERTIES DEBUG: Boundary selected, finding contained devices")
            contained_devices = self._get_devices_in_boundary(item)
            self.panel.set_boundary_contained_devices(contained_devices)
    
    def _on_multiple_items_selected(self, items):
        """Handle when multiple items are selected."""
        try:
            if not items:
                self.panel.clear()
                return
                
            # Show mixed selection interface
            self.panel.show_mixed_selection(items)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error handling multiple selection: {str(e)}")
            self.panel.clear()  # Fallback to clear state
    
    def _on_selection_cleared(self):
        """Handle selection being cleared."""
        self.logger.debug("PROPERTIES DEBUG: Selection cleared")
        self.selected_item = None
        self.selected_items = []
        
        # Ensure panel is visible
        if hasattr(self.panel, 'parent') and hasattr(self.panel.parent(), 'setVisible'):
            self.logger.debug("PROPERTIES DEBUG: Making properties panel visible")
            self.panel.parent().setVisible(True)
            self.panel.parent().raise_()
            
        # Clear panel
        self.logger.debug("PROPERTIES DEBUG: Clearing properties panel")
        self.panel.clear()
    
    def _on_name_changed(self, new_name):
        """Handle name change in properties panel."""
        if not self.selected_item or not hasattr(self.selected_item, 'name'):
            return
            
        old_name = self.selected_item.name
        if old_name != new_name:
            self.logger.info(f"Changing name from '{old_name}' to '{new_name}'")
            
            if self.undo_redo_manager:
                cmd = SetItemNameCommand(self.selected_item, old_name, new_name)
                self.undo_redo_manager.push_command(cmd)
            else:
                self.selected_item.name = new_name
                if hasattr(self.selected_item, 'update_name'):
                    self.selected_item.update_name()
                elif hasattr(self.selected_item, 'text_item'):
                    self.selected_item.text_item.setPlainText(new_name)
            
            # Notify via event bus based on item type
            if isinstance(self.selected_item, Device):
                self.event_bus.emit("device_name_changed", self.selected_item)
            elif isinstance(self.selected_item, Connection):
                self.event_bus.emit("connection_name_changed", self.selected_item)
            elif isinstance(self.selected_item, Boundary):
                self.event_bus.emit("boundary_name_changed", self.selected_item)
    
    def _on_z_value_changed(self, new_z_value):
        """Handle Z-value (layer) change in properties panel."""
        if not self.selected_item:
            return
            
        old_z_value = self.selected_item.zValue()
        if old_z_value != new_z_value:
            self.logger.info(f"Changing Z-value from {old_z_value} to {new_z_value}")
            
            if self.undo_redo_manager:
                cmd = SetItemZValueCommand(self.selected_item, old_z_value, new_z_value)
                self.undo_redo_manager.push_command(cmd)
            else:
                self.selected_item.setZValue(new_z_value)
            
            # Force canvas update
            self.canvas.viewport().update()
            
            # Notify via event bus
            item_type = type(self.selected_item).__name__.lower()
            self.event_bus.emit(f"{item_type}_layer_changed", self.selected_item)
    
    def _on_device_property_changed(self, key, value):
        """Handle device property change in properties panel."""
        # For multiple devices selected
        if self.selected_items:
            # Apply the change to all selected devices
            for device in self.selected_items:
                if hasattr(device, 'properties'):
                    # Handle existing or new properties
                    if key in device.properties:
                        self._update_device_property(device, key, value)
                    else:
                        # Add new property
                        self._add_device_property(device, key, value)
            return
                
        # For single device selected
        if not self.selected_item or not isinstance(self.selected_item, Device):
            return
            
        if hasattr(self.selected_item, 'properties'):
            if key in self.selected_item.properties:
                self._update_device_property(self.selected_item, key, value)
            else:
                # Add new property
                self._add_device_property(self.selected_item, key, value)
            
    def _update_device_property(self, device, key, value):
        """Update a device property with undo/redo support."""
        old_value = device.properties[key]
        
        # Try to convert value to appropriate type
        if isinstance(old_value, int):
            try:
                value = int(value)
            except ValueError:
                pass
        elif isinstance(old_value, float):
            try:
                value = float(value)
            except ValueError:
                pass
        elif isinstance(old_value, bool):
            value = value.lower() in ('true', 'yes', '1')
        
        if old_value != value:
            self.logger.info(f"Changing device property {key} from '{old_value}' to '{value}'")
            
            # Use command pattern if undo_redo_manager available
            if self.undo_redo_manager:
                from controllers.commands import DevicePropertyCommand, ConnectionPropertyCommand
                
                # Choose the appropriate command class based on the item type
                if isinstance(device, Device):
                    cmd = DevicePropertyCommand(device, key, old_value, value)
                else:
                    cmd = ConnectionPropertyCommand(device, key, old_value, value)
                    
                self.undo_redo_manager.push_command(cmd)
            else:
                device.properties[key] = value
            
            # Force a redraw
            device.update()
            
            # Notify via event bus
            self.event_bus.emit("device_property_changed", device, key, value)
    
    def _add_device_property(self, device, key, value):
        """Add a new property to a device."""
        if not hasattr(device, 'properties'):
            device.properties = {}
            
        self.logger.info(f"Adding new device property '{key}' with value '{value}'")
        
        # Use command pattern if undo_redo_manager available
        if self.undo_redo_manager:
            from controllers.commands import DevicePropertyCommand
            cmd = DevicePropertyCommand(device, key, None, value, is_new=True)
            self.undo_redo_manager.push_command(cmd)
        else:
            device.properties[key] = value
        
        # Force a redraw
        device.update()
        
        # Notify via event bus
        self.event_bus.emit("device_property_added", device, key, value)
    
    def _on_connection_property_changed(self, key, value):
        """Handle connection property change in properties panel."""
        if not self.selected_item or not isinstance(self.selected_item, Connection):
            return
            
        if key == 'line_style':
            try:
                # Convert string to RoutingStyle enum
                from models.connection import RoutingStyle
                if isinstance(value, str):
                    new_style = RoutingStyle.from_string(value)
                else:
                    new_style = value
                    
                old_style = self.selected_item.routing_style
                
                if old_style != new_style:
                    self.logger.info(f"Changing connection routing style from {old_style} to {new_style}")
                    
                    if self.undo_redo_manager:
                        class ChangeConnectionStyleCommand(Command):
                            def __init__(self, connection, old_style, new_style):
                                super().__init__("Change Connection Style")
                                self.connection = connection
                                self.old_style = old_style
                                self.new_style = new_style
                            
                            def execute(self):
                                self.connection.routing_style = self.new_style
                            
                            def undo(self):
                                self.connection.routing_style = self.old_style
                        
                        cmd = ChangeConnectionStyleCommand(self.selected_item, old_style, new_style)
                        self.undo_redo_manager.push_command(cmd)
                    else:
                        self.selected_item.routing_style = new_style
            except Exception as e:
                self.logger.error(f"Error changing connection style: {str(e)}")
                self.logger.error(traceback.format_exc())
        
        # Handle standard properties that should be in the properties dictionary
        elif key in ["Bandwidth", "Latency", "Label"]:
            # Ensure properties dictionary exists
            if not hasattr(self.selected_item, 'properties'):
                self.selected_item.properties = {}
                
            # Update the value in the properties dictionary
            old_value = self.selected_item.properties.get(key)
            if old_value != value:
                # If the key is "Label", use "label_text" in the properties dictionary
                property_key = "label_text" if key == "Label" else key
                self.selected_item.properties[property_key] = value
                
                # Also update the corresponding attribute
                if key == "Bandwidth":
                    self.selected_item.bandwidth = value
                elif key == "Latency":
                    self.selected_item.latency = value
                elif key == "Label":
                    self.selected_item.label_text = value
                    
                self.event_bus.emit("connection_property_changed", self.selected_item, property_key)
    
    def _on_boundary_property_changed(self, key, value):
        """Handle boundary property change."""
        if not self.selected_item or not isinstance(self.selected_item, Boundary):
            return
        
        # Handle different boundary properties
        if key == "color":
            # Handle color change
            if isinstance(value, QColor):
                old_color = self.selected_item.color
                if old_color != value:
                    self.logger.info(f"Changing boundary color from {old_color.name()} to {value.name()}")
                    
                    if self.undo_redo_manager:
                        # Create a command for undo/redo if available
                        from controllers.commands import SetBoundaryColorCommand
                        cmd = SetBoundaryColorCommand(self.selected_item, old_color, value)
                        self.undo_redo_manager.push_command(cmd)
                    else:
                        # Direct change without undo/redo
                        self.selected_item.set_color(value)
                    
                    # Notify via event bus
                    self.event_bus.emit("boundary_color_changed", self.selected_item, value)
        elif key == "font_size":
            # Get the current font size
            old_size = self.selected_item.get_font_size()
            
            if old_size != value:
                # Create a command to change the font size
                class SetBoundaryFontSizeCommand(Command):
                    def __init__(self, boundary, old_size, new_size):
                        super().__init__(f"Change Boundary Text Size")
                        self.boundary = boundary
                        self.old_size = old_size
                        self.new_size = new_size
                    
                    def execute(self):
                        self.boundary.set_font_size(self.new_size)
                    
                    def undo(self):
                        self.boundary.set_font_size(self.old_size)
                
                # Execute the command via the undo/redo manager if available
                if self.undo_redo_manager:
                    cmd = SetBoundaryFontSizeCommand(self.selected_item, old_size, value)
                    self.undo_redo_manager.push_command(cmd)
                else:
                    # Just set the font size directly
                    self.selected_item.set_font_size(value)
                
                # Notify about the change
                self.event_bus.emit("boundary_font_size_changed", self.selected_item)
        elif key == "name":
            # Handle name change
            if hasattr(self.selected_item, 'name'):
                old_name = self.selected_item.name
                if old_name != value:
                    self.logger.info(f"Changing boundary name from '{old_name}' to '{value}'")
                    
                    if self.undo_redo_manager:
                        cmd = UpdateNameCommand(self.selected_item, old_name, value)
                        self.undo_redo_manager.push_command(cmd)
                    else:
                        self.selected_item.name = value
                        # Update visual text
                        if hasattr(self.selected_item, 'update_name'):
                            self.selected_item.update_name()
                    
                    # Notify via event bus
                    self.event_bus.emit("boundary_name_changed", self.selected_item)
    
    def _on_change_icon_requested(self, item):
        """Handle explicit request to change a device's icon from the Change Icon button."""
        if isinstance(item, Device):
            self.logger.info(f"Change Icon button clicked for device: {item.name}. Opening icon selection dialog.")
            # This function is only called when the Change Icon button is explicitly clicked
            if hasattr(item, 'upload_custom_icon') and callable(item.upload_custom_icon):
                item.upload_custom_icon()
    
    def _on_property_display_toggled(self, key, enabled):
        """Handle toggling display of a property under device icon."""
        # For multiple devices selected
        if self.selected_items:
            # Apply the change to all selected devices
            for device in self.selected_items:
                if isinstance(device, Device):
                    # Use device's toggle method 
                    device.toggle_property_display(key, enabled)
                    # Force a visual update of the device
                    device.update()
                    device.update_property_labels()
            # Notify via event bus for all devices at once
            self.event_bus.emit("multiple_devices_display_properties_changed", self.selected_items, key, enabled)
            return
                
        # For single device selected
        if not self.selected_item or not isinstance(self.selected_item, Device):
            return
            
        # Use device's toggle method
        self.selected_item.toggle_property_display(key, enabled)
        
        # Notify via event bus
        self.event_bus.emit("device_display_properties_changed", self.selected_item, key, enabled)

    def on_property_changed(self, property_name, value):
        """Handle property changes from the panel."""
        if self.selected_items:
            # Handle multiple selected items
            self._handle_multiple_property_change(property_name, value)
        elif self.selected_item:
            # Handle single selected item
            self._handle_single_property_change(property_name, value)
    
    def _handle_multiple_property_change(self, property_name, value):
        """Handle property change for multiple selected devices."""
        # Store original values for undo/redo
        original_values = {}
        
        for device in self.selected_items:
            if hasattr(device, 'properties') and property_name in device.properties:
                original_values[device] = device.properties.get(property_name)
        
        # If using command pattern
        if self.undo_redo_manager:
            from controllers.commands import BulkChangePropertyCommand
            
            cmd = BulkChangePropertyCommand(
                self.selected_items,
                property_name,
                value,
                original_values,
                self.event_bus  # Pass event bus to the command
            )
            
            self.undo_redo_manager.push_command(cmd)
        else:
            # Apply changes directly
            for device in self.selected_items:
                if hasattr(device, 'properties'):
                    device.properties[property_name] = value
                    # Notify about property change
                    if self.event_bus:
                        self.event_bus.emit('device_property_changed', device, property_name)
        
        # Notify that multiple devices' properties were changed
        if self.event_bus:
            self.event_bus.emit('bulk_properties_changed', self.selected_items)
    
    def _handle_single_property_change(self, property_name, value):
        """Handle property change for a single selected device."""
        if not self.selected_item or not isinstance(self.selected_item, Device):
            return
            
        if hasattr(self.selected_item, 'properties') and property_name in self.selected_item.properties:
            old_value = self.selected_item.properties[property_name]
            
            # Try to convert value to appropriate type
            if isinstance(old_value, int):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif isinstance(old_value, float):
                try:
                    value = float(value)
                except ValueError:
                    pass
            elif isinstance(old_value, bool):
                value = value.lower() in ('true', 'yes', '1')
            
            if old_value != value:
                self.logger.info(f"Changing device property '{property_name}' from '{old_value}' to '{value}'")
                self.selected_item.properties[property_name] = value
                
                # Update property labels if this property is set to be displayed
                if (hasattr(self.selected_item, 'display_properties') and 
                    property_name in self.selected_item.display_properties and 
                    self.selected_item.display_properties[property_name]):
                    self.selected_item.update_property_labels()
                
                # Notify via event bus
                if self.event_bus:
                    self.event_bus.emit("device_property_changed", self.selected_item, property_name, value)
    
    def _on_property_delete_requested(self, property_name):
        """Handle property deletion requests."""
        # For multiple devices selected
        if self.selected_items:
            # Apply the deletion to all selected devices
            for device in self.selected_items:
                if hasattr(device, 'properties') and property_name in device.properties:
                    self._delete_device_property(device, property_name)
            return
                
        # For single device selected
        if not self.selected_item or not isinstance(self.selected_item, Device):
            return
            
        if hasattr(self.selected_item, 'properties') and property_name in self.selected_item.properties:
            self._delete_device_property(self.selected_item, property_name)
    
    def _delete_device_property(self, device, property_name):
        """Delete a property from a device with undo/redo support."""
        if not hasattr(device, 'properties') or property_name not in device.properties:
            return
            
        # Store the current value for undo purposes
        old_value = device.properties[property_name]
        display_state = False
        if hasattr(device, 'display_properties'):
            display_state = device.display_properties.get(property_name, False)
            
        self.logger.info(f"Deleting device property '{property_name}' with value '{old_value}'")
        
        # Use command pattern if undo_redo_manager available
        if self.undo_redo_manager:
            from controllers.commands import DeletePropertyCommand
            cmd = DeletePropertyCommand(device, property_name, old_value, display_state)
            self.undo_redo_manager.push_command(cmd)
        else:
            # Direct deletion without undo/redo
            del device.properties[property_name]
            if hasattr(device, 'display_properties') and property_name in device.display_properties:
                del device.display_properties[property_name]
            
            # Update display if needed
            device.update_property_labels()
        
        # Force a redraw
        device.update()
        
        # Notify via event bus
        self.event_bus.emit("device_property_deleted", device, property_name)

    def _get_devices_in_boundary(self, boundary):
        """Get all devices contained within a boundary."""
        if not hasattr(boundary, 'scene'):
            return []
            
        # Get all devices in the scene
        all_devices = [item for item in boundary.scene().items() if isinstance(item, Device)]
        
        # Filter devices that are within the boundary's bounds
        boundary_rect = boundary.boundingRect()
        boundary_pos = boundary.pos()
        contained_devices = []
        
        for device in all_devices:
            device_pos = device.pos()
            if (boundary_rect.contains(device_pos - boundary_pos)):
                contained_devices.append(device)
                
        return contained_devices

    def handle_selection_changed(self, selected_items):
        """Handle selection changes from the MainWindow.
        
        This is a wrapper around update_properties_panel to maintain compatibility
        with the MainWindow's signal handling.
        """
        self.logger.debug(f"PROPERTIES DEBUG: Selection changed, handling {len(selected_items) if selected_items else 0} items")
        self.update_properties_panel(selected_items)

class TogglePropertyDisplayCommand(Command):
    """Command for toggling device property display."""
    
    def __init__(self, device, property_name, old_state, new_state):
        """Initialize the command."""
        super().__init__(f"Toggle Display of '{property_name}'")
        self.device = device
        self.property_name = property_name
        self.old_state = old_state
        self.new_state = new_state
        
    def execute(self):
        """Execute the command."""
        if not hasattr(self.device, 'display_properties'):
            self.device.display_properties = {}
        self.device.display_properties[self.property_name] = self.new_state
        self.device.update_property_labels()
        
    def undo(self):
        """Undo the command."""
        self.device.display_properties[self.property_name] = self.old_state
        self.device.update_property_labels()
