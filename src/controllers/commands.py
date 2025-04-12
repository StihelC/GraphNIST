import copy
from venv import logger
from PyQt5.QtCore import QPointF, QRectF
from controllers.undo_redo_manager import Command
from models.device import Device
from models.connection.connection import Connection
from models.boundary.boundary import Boundary
import logging

class AddDeviceCommand(Command):
    """Command to add a device to the canvas."""
    
    def __init__(self, device_controller, device_type, position, name=None, properties=None, custom_icon_path=None):
        super().__init__(f"Add {device_type} Device")
        self.device_controller = device_controller
        self.device_type = device_type
        self.position = position
        self.name = name
        self.properties = properties or {}
        self.custom_icon_path = custom_icon_path
        self.created_device = None
        self.logger = logging.getLogger(__name__)
    
    def execute(self):
        """Create and add the device."""
        # Check if we're in a bulk creation process
        in_bulk = hasattr(self.device_controller, '_in_bulk_creation') and self.device_controller._in_bulk_creation
        self.logger.debug(f"CMD: AddDeviceCommand execute for {self.name}, in_bulk_creation={in_bulk}")
        
        if in_bulk:
            # In bulk creation, the device was already created directly
            self.logger.debug(f"CMD: Skipping device creation for {self.name} (already created in bulk)")
            return None
        
        self.created_device = self.device_controller._create_device(
            self.name, 
            self.device_type, 
            self.position,
            self.properties,
            self.custom_icon_path
        )
        self.logger.debug(f"CMD: Created device {self.name} through command execution")
        return self.created_device
    
    def undo(self):
        """Remove the device."""
        if self.created_device:
            # Set flag to prevent recursive command creation
            if hasattr(self.device_controller, 'undo_redo_manager') and self.device_controller.undo_redo_manager:
                self.device_controller.undo_redo_manager.is_executing_command = True
            
            # Delete the device
            self.device_controller.on_delete_device_requested(self.created_device)
            
            # Reset flag
            if hasattr(self.device_controller, 'undo_redo_manager') and self.device_controller.undo_redo_manager:
                self.device_controller.undo_redo_manager.is_executing_command = False
                
            # Force canvas update
            if hasattr(self.device_controller, 'canvas') and self.device_controller.canvas:
                self.device_controller.canvas.viewport().update()


class DeleteDeviceCommand(Command):
    """Command to delete a device from the canvas."""
    
    def __init__(self, device_controller, device):
        super().__init__(f"Delete Device {device.name}")
        self.device_controller = device_controller
        self.device = device
        self.position = device.scenePos()
        self.device_type = device.device_type
        self.name = device.name
        self.properties = copy.deepcopy(device.properties) if hasattr(device, 'properties') else None
        self.custom_icon_path = device.custom_icon_path if hasattr(device, 'custom_icon_path') else None
        
        # Save connections
        self.connections = []
        if hasattr(device, 'connections'):
            for conn in device.connections:
                # Save connection info
                source_id = conn.source_device.id
                target_id = conn.target_device.id
                source_port = getattr(conn, '_source_port', None)
                target_port = getattr(conn, '_target_port', None)
                properties = copy.deepcopy(conn.properties) if hasattr(conn, 'properties') else None
                
                # Create connection info dictionary
                self.connections.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'source_port': source_port,
                    'target_port': target_port,
                    'properties': properties
                })
    
    def execute(self):
        """Delete the device."""
        self.device_controller._delete_device(self.device)
    
    def undo(self):
        """Recreate the device and its connections."""
        # Recreate the device
        new_device = self.device_controller._create_device(
            self.name,
            self.device_type,
            self.position,
            self.properties,
            self.custom_icon_path
        )
        
        # Force canvas update
        if hasattr(self.device_controller, 'canvas') and self.device_controller.canvas:
            self.device_controller.canvas.viewport().update()
        
        # TODO: Reconnect the device's connections
        # This would require access to the connection controller and a way to find devices by ID
        # For now, connections will need to be restored manually


class AddBoundaryCommand(Command):
    """Command to add a boundary to the canvas."""
    
    def __init__(self, boundary_controller, rect, name=None, color=None):
        super().__init__("Add Boundary")
        self.boundary_controller = boundary_controller
        self.rect = rect
        self.name = name
        self.color = color
        self.created_boundary = None
    
    def execute(self):
        """Create and add the boundary."""
        self.created_boundary = self.boundary_controller.create_boundary(
            self.rect,
            self.name,
            self.color
        )
        return self.created_boundary
    
    def undo(self):
        """Remove the boundary."""
        if self.created_boundary:
            self.boundary_controller.on_delete_boundary_requested(self.created_boundary)


class DeleteBoundaryCommand(Command):
    """Command to delete a boundary from the canvas."""
    
    def __init__(self, boundary_controller, boundary):
        super().__init__(f"Delete Boundary {boundary.name}")
        self.boundary_controller = boundary_controller
        self.boundary = boundary
        self.rect = boundary.rect()
        self.name = boundary.name
        self.color = boundary.color if hasattr(boundary, 'color') else None
    
    def execute(self):
        """Delete the boundary."""
        self.boundary_controller.on_delete_boundary_requested(self.boundary)
    
    def undo(self):
        """Recreate the boundary."""
        new_boundary = self.boundary_controller.create_boundary(
            self.rect,
            self.name,
            self.color
        )
        return new_boundary


class AddConnectionCommand(Command):
    """Command to add a connection between two devices."""
    
    def __init__(self, controller, source_device, target_device, properties=None):
        # Get device names safely for the command description
        source_name = source_device.name if hasattr(source_device, 'name') else "Unknown source"
        target_name = target_device.name if hasattr(target_device, 'name') else "Unknown target"
        
        super().__init__(f"Add Connection {source_name} to {target_name}")
        self.controller = controller
        self.source_device = source_device
        self.target_device = target_device
        self.properties = properties or {}
        self.connection = None
    
    def execute(self):
        """Create the connection."""
        # Check if a connection already exists before creating a new one
        if hasattr(self.controller, '_connection_exists') and self.controller._connection_exists(self.source_device, self.target_device):
            # Connection already exists, don't create a duplicate
            return None
            
        self.connection = self.controller.create_connection(
            source_device=self.source_device,
            target_device=self.target_device,
            properties=self.properties
        )
        return self.connection
    
    def undo(self):
        """Delete the connection."""
        if self.connection:
            self.controller._delete_connection(self.connection)
            self.connection = None


class DeleteConnectionCommand(Command):
    """Command to delete a connection from the network topology."""
    
    def __init__(self, connection_controller, connection):
        """Initialize the command.
        
        Args:
            connection_controller: The controller that manages connections
            connection: The connection to delete
        """
        logger = logging.getLogger(__name__)
        
        # First, set up basic properties to ensure they're always available
        self.controller = connection_controller
        self.connection = connection
        
        # Safely extract source device info
        self.source_device = None
        source_name = "Unknown Source"
        if hasattr(connection, 'source_device') and connection.source_device:
            self.source_device = connection.source_device
            source_name = getattr(self.source_device, 'name', 'Unknown Source')
            
        # Safely extract target device info (handling both naming conventions)
        self.target_device = None
        target_name = "Unknown Target"
        
        # Handle both naming conventions (dest_device and target_device)
        if hasattr(connection, 'dest_device') and connection.dest_device:
            self.target_device = connection.dest_device
            target_name = getattr(self.target_device, 'name', 'Unknown Target')
            # Add target_device attribute to maintain consistency
            connection.target_device = self.target_device
        elif hasattr(connection, 'target_device') and connection.target_device:
            self.target_device = connection.target_device
            target_name = getattr(self.target_device, 'name', 'Unknown Target')
            
        # Initialize with safe command name 
        super().__init__(f"Delete Connection {source_name} to {target_name}")
        logger.info(f"Initializing DeleteConnectionCommand from {source_name} to {target_name}")
            
        # Get other properties safely
        self.connection_type = getattr(connection, 'connection_type', 'ethernet')
        self.routing_style = getattr(connection, 'routing_style', 'straight')
        self.properties = {}
        
        # Safely copy properties
        if hasattr(connection, 'properties') and connection.properties:
            import copy
            self.properties = copy.deepcopy(connection.properties)
    
    def execute(self):
        """Delete the connection."""
        self.controller._delete_connection(self.connection)
    
    def undo(self):
        """Recreate the connection."""
        if self.source_device and self.target_device:
            # Create the properties dictionary with all needed parameters
            conn_properties = self.properties.copy() if self.properties else {}
            
            # Ensure connection_type and other essential properties are included
            conn_properties['connection_type'] = self.connection_type
            conn_properties['routing_style'] = self.routing_style
            
            # Create the connection using the controller
            new_connection = self.controller.create_connection(
                source_device=self.source_device, 
                target_device=self.target_device,
                properties=conn_properties
            )
            return new_connection
        return None


class MoveItemCommand(Command):
    """Command to move an item (device or boundary) on the canvas."""
    
    def __init__(self, item, old_pos, new_pos):
        if isinstance(item, Device):
            name = f"Move Device {item.name}"
        elif isinstance(item, Boundary):
            name = f"Move Boundary {item.name}"
        else:
            name = "Move Item"
        
        super().__init__(name)
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self):
        """Move the item to the new position."""
        self.item.setPos(self.new_pos)
    
    def undo(self):
        """Move the item back to the old position."""
        self.item.setPos(self.old_pos)


class CompositeCommand(Command):
    """A command that groups multiple commands together."""
    
    def __init__(self, commands=None, description="Composite Command"):
        super().__init__(description)
        self.commands = commands or []
        self.logger = logging.getLogger(__name__)
        
    def add_command(self, command):
        """Add a command to the composite."""
        self.commands.append(command)
        
    def execute(self):
        """Execute all commands in the composite."""
        self.logger.debug(f"Executing composite command with {len(self.commands)} sub-commands")
        results = []
        
        for command in self.commands:
            result = command.execute()
            # Only store non-None results, as None typically means operation was skipped (e.g., connection already exists)
            if result is not None:
                results.append(result)
            
        return results
        
    def undo(self):
        """Undo all commands in reverse order."""
        self.logger.debug(f"Undoing composite command with {len(self.commands)} sub-commands")
        # Undo in reverse order
        for command in reversed(self.commands):
            command.undo()


class AlignDevicesCommand(Command):
    """Command to align multiple devices."""
    
    def __init__(self, alignment_controller, devices, original_positions, alignment_type):
        super().__init__(f"Align Devices {alignment_type}")
        self.alignment_controller = alignment_controller
        self.devices = devices
        self.original_positions = original_positions
        self.alignment_type = alignment_type
        self.new_positions = {device: device.scenePos() for device in devices}
        self.logger = logging.getLogger(__name__)
    
    def execute(self):
        """Execute the alignment (already done, just for interface conformity)."""
        # The alignment has already been performed, this is just for conformity
        pass
    
    def undo(self):
        """Restore the original positions of the devices."""
        self.logger.debug(f"Undoing alignment of {len(self.devices)} devices")
        
        for device, orig_pos in self.original_positions.items():
            if device.scene():  # Check if device still exists in scene
                device.setPos(orig_pos)
                if hasattr(device, 'update_connections'):
                    device.update_connections()
        
        # Force canvas update
        if hasattr(self.alignment_controller, 'canvas') and self.alignment_controller.canvas:
            self.alignment_controller.canvas.viewport().update()
    
    def redo(self):
        """Re-apply the alignment."""
        self.logger.debug(f"Redoing alignment of {len(self.devices)} devices")
        
        for device, new_pos in self.new_positions.items():
            if device.scene():  # Check if device still exists in scene
                device.setPos(new_pos)
                if hasattr(device, 'update_connections'):
                    device.update_connections()
        
        # Force canvas update
        if hasattr(self.alignment_controller, 'canvas') and self.alignment_controller.canvas:
            self.alignment_controller.canvas.viewport().update()


class BulkChangePropertyCommand(Command):
    """Command for changing a property on multiple devices at once."""
    
    def __init__(self, devices, property_name, new_value, original_values, event_bus=None):
        """Initialize the command.
        
        Args:
            devices: List of devices to modify
            property_name: Name of the property to change
            new_value: New value for the property
            original_values: Dictionary mapping devices to their original values
            event_bus: Optional event bus for notifications
        """
        super().__init__(f"Change {property_name} on multiple devices")
        self.devices = devices
        self.property_name = property_name
        self.new_value = new_value
        self.original_values = original_values
        self.event_bus = event_bus
        
    def execute(self):
        """Execute the command by applying the new property value to all devices."""
        for device in self.devices:
            if hasattr(device, 'properties'):
                device.properties[self.property_name] = self.new_value
                # Notify event bus if available
                if self.event_bus:
                    self.event_bus.emit('device_property_changed', device, self.property_name)
                    
                # Update labels if this property is displayed under the device
                if hasattr(device, 'display_properties') and device.display_properties.get(self.property_name, False):
                    device.update_property_labels()
        
        # Emit bulk change notification
        if self.event_bus:
            self.event_bus.emit('bulk_properties_changed', self.devices)
            
        return True
        
    def undo(self):
        """Undo the command by restoring original property values."""
        for device, orig_value in self.original_values.items():
            if hasattr(device, 'properties'):
                device.properties[self.property_name] = orig_value
                # Notify event bus if available
                if self.event_bus:
                    self.event_bus.emit('device_property_changed', device, self.property_name)
                    
                # Update labels if this property is displayed under the device
                if hasattr(device, 'display_properties') and device.display_properties.get(self.property_name, False):
                    device.update_property_labels()
        
        # Emit bulk change notification
        if self.event_bus:
            self.event_bus.emit('bulk_properties_changed', list(self.original_values.keys()))
            
        return True

class BulkTogglePropertyDisplayCommand(Command):
    """Command to toggle display of properties for multiple devices at once."""
    
    def __init__(self, devices, property_name, display_enabled, original_states, event_bus=None):
        super().__init__(f"Toggle Display of {property_name}")
        self.devices = devices
        self.property_name = property_name
        self.display_enabled = display_enabled
        self.original_states = original_states
        self.event_bus = event_bus
    
    def execute(self):
        """Apply the display setting to all devices."""
        for device in self.devices:
            if hasattr(device, 'display_properties'):
                device.display_properties[self.property_name] = self.display_enabled
                device.update()
                
                # Notify event bus if available
                if self.event_bus:
                    self.event_bus.emit("device_display_properties_changed", 
                                      device, self.property_name, self.display_enabled)
    
    def undo(self):
        """Restore original display settings for all devices."""
        for device_id, original_state in self.original_states.items():
            # Find the device by ID
            for device in self.devices:
                if device.id == device_id:
                    if hasattr(device, 'display_properties'):
                        device.display_properties[self.property_name] = original_state
                        device.update()
                        
                        # Notify event bus if available
                        if self.event_bus:
                            self.event_bus.emit("device_display_properties_changed", 
                                              device, self.property_name, original_state)
                    break

class DevicePropertyCommand(Command):
    """Command to change a device property."""
    
    def __init__(self, device, property_name, old_value, new_value, is_new=False):
        action = "Add" if is_new else "Change"
        super().__init__(f"{action} {device.name} {property_name}")
        self.device = device
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.is_new = is_new
    
    def execute(self):
        """Set the new property value."""
        if hasattr(self.device, 'properties'):
            self.device.properties[self.property_name] = self.new_value
            self.device.update()
            
            # Initialize display property if this is a new property
            if self.is_new and hasattr(self.device, 'display_properties'):
                self.device.display_properties[self.property_name] = False
    
    def undo(self):
        """Restore the old property value or remove the property if it was newly added."""
        if hasattr(self.device, 'properties'):
            if self.is_new:
                # If this was a new property, remove it completely
                if self.property_name in self.device.properties:
                    del self.device.properties[self.property_name]
                
                # Also remove from display properties if it exists
                if hasattr(self.device, 'display_properties') and self.property_name in self.device.display_properties:
                    del self.device.display_properties[self.property_name]
            else:
                # Otherwise restore the old value
                self.device.properties[self.property_name] = self.old_value
            
            self.device.update()

class ConnectionPropertyCommand(Command):
    """Command to change a connection property."""
    
    def __init__(self, connection, property_name, old_value, new_value, is_new=False):
        action = "Add" if is_new else "Change"
        super().__init__(f"{action} Connection {property_name}")
        self.connection = connection
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.is_new = is_new
    
    def execute(self):
        """Set the new property value."""
        if hasattr(self.connection, 'properties'):
            self.connection.properties[self.property_name] = self.new_value
            self.connection.update()
    
    def undo(self):
        """Restore the old property value or remove the property if it was newly added."""
        if hasattr(self.connection, 'properties'):
            if self.is_new:
                # If this was a new property, remove it completely
                if self.property_name in self.connection.properties:
                    del self.connection.properties[self.property_name]
            else:
                # Otherwise restore the old value
                self.connection.properties[self.property_name] = self.old_value
            
            self.connection.update()

class DeletePropertyCommand(Command):
    """Command to delete a device property with undo/redo support."""
    
    def __init__(self, device, property_name, old_value, display_state):
        """Initialize the command.
        
        Args:
            device: The device whose property is being deleted
            property_name: Name of the property to delete
            old_value: Original value of the property (for undo)
            display_state: Whether the property was being displayed
        """
        super().__init__(f"Delete {device.name} {property_name}")
        self.device = device
        self.property_name = property_name
        self.old_value = old_value
        self.display_state = display_state
        self.logger = logging.getLogger(__name__)
    
    def execute(self):
        """Delete the property."""
        if hasattr(self.device, 'properties') and self.property_name in self.device.properties:
            del self.device.properties[self.property_name]
            
            # Also remove from display properties if it exists
            if hasattr(self.device, 'display_properties') and self.property_name in self.device.display_properties:
                del self.device.display_properties[self.property_name]
                
            # Update the display
            if hasattr(self.device, 'update_property_labels'):
                self.device.update_property_labels()
            
            # Force a visual update
            self.device.update()
            
            self.logger.debug(f"Deleted property {self.property_name} from device {self.device.name}")
    
    def undo(self):
        """Restore the deleted property."""
        if hasattr(self.device, 'properties'):
            # Restore the property value
            self.device.properties[self.property_name] = self.old_value
            
            # Restore display state if it was being displayed
            if hasattr(self.device, 'display_properties') and self.display_state:
                self.device.display_properties[self.property_name] = self.display_state
                
            # Update the display
            if hasattr(self.device, 'update_property_labels'):
                self.device.update_property_labels()
            
            # Force a visual update
            self.device.update()
            
            self.logger.debug(f"Restored property {self.property_name} to device {self.device.name}")

class UpdatePropertyCommand(Command):
    """Command to update a property of an item with undo/redo support."""
    
    def __init__(self, item, property_name, old_value, new_value):
        """Initialize the command.
        
        Args:
            item: The item whose property is being changed
            property_name: Name of the property to change
            old_value: Original value of the property
            new_value: New value to set
        """
        item_name = getattr(item, 'name', 'Unknown')
        super().__init__(f"Update {item_name} {property_name}")
        self.item = item
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        """Set the new property value."""
        if hasattr(self.item, 'properties'):
            self.item.properties[self.property_name] = self.new_value
            if hasattr(self.item, 'update'):
                self.item.update()
    
    def undo(self):
        """Restore the old property value."""
        if hasattr(self.item, 'properties'):
            self.item.properties[self.property_name] = self.old_value
            if hasattr(self.item, 'update'):
                self.item.update()

class SetZValueCommand(Command):
    """Command to change an item's Z value (layer)."""
    
    def __init__(self, item, old_value, new_value):
        """Initialize the command.
        
        Args:
            item: The item whose Z value is being changed
            old_value: Original Z value
            new_value: New Z value to set
        """
        item_name = getattr(item, 'name', type(item).__name__)
        super().__init__(f"Change {item_name} Layer")
        self.item = item
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        """Set the new Z value."""
        self.item.setZValue(self.new_value)
    
    def undo(self):
        """Restore the old Z value."""
        self.item.setZValue(self.old_value)

class UpdateNameCommand(Command):
    """Command to update an item's name with undo/redo support."""
    
    def __init__(self, item, old_name, new_name):
        """Initialize the command.
        
        Args:
            item: The item whose name is being changed
            old_name: Original name
            new_name: New name to set
        """
        super().__init__(f"Rename {type(item).__name__}")
        self.item = item
        self.old_name = old_name
        self.new_name = new_name
    
    def execute(self):
        """Set the new name."""
        self.item.name = self.new_name
        if hasattr(self.item, 'update_name'):
            self.item.update_name()
        elif hasattr(self.item, 'text_item'):
            self.item.text_item.setPlainText(self.new_name)
    
    def undo(self):
        """Restore the old name."""
        self.item.name = self.old_name
        if hasattr(self.item, 'update_name'):
            self.item.update_name()
        elif hasattr(self.item, 'text_item'):
            self.item.text_item.setPlainText(self.old_name)

class TogglePropertyDisplayCommand(Command):
    """Command to toggle whether a property is displayed under a device."""
    
    def __init__(self, device, property_name, old_state, new_state):
        """Initialize the command.
        
        Args:
            device: The device whose property display is being toggled
            property_name: Name of the property to toggle display for
            old_state: Original display state (True/False)
            new_state: New display state (True/False)
        """
        super().__init__(f"Toggle {device.name} {property_name} Display")
        self.device = device
        self.property_name = property_name
        self.old_state = old_state
        self.new_state = new_state
    
    def execute(self):
        """Set the new display state."""
        if hasattr(self.device, 'display_properties'):
            self.device.display_properties[self.property_name] = self.new_state
            self.device.update()
    
    def undo(self):
        """Restore the old display state."""
        if hasattr(self.device, 'display_properties'):
            self.device.display_properties[self.property_name] = self.old_state
            self.device.update()

class UpdateConnectionTypeCommand(Command):
    """Command to update a connection's type with undo/redo support."""
    
    def __init__(self, connection, old_type, new_type):
        """Initialize the command.
        
        Args:
            connection: The connection whose type is being changed
            old_type: Original connection type
            new_type: New connection type to set
        """
        super().__init__("Change Connection Type")
        self.connection = connection
        self.old_type = old_type
        self.new_type = new_type
    
    def execute(self):
        """Set the new connection type."""
        if hasattr(self.connection, 'set_connection_type'):
            self.connection.set_connection_type(self.new_type)
        else:
            self.connection.connection_type = self.new_type
            # Update appearance if possible
            if hasattr(self.connection, 'update_appearance'):
                self.connection.update_appearance()
            elif hasattr(self.connection, 'update'):
                self.connection.update()
    
    def undo(self):
        """Restore the old connection type."""
        if hasattr(self.connection, 'set_connection_type'):
            self.connection.set_connection_type(self.old_type)
        else:
            self.connection.connection_type = self.old_type
            # Update appearance if possible
            if hasattr(self.connection, 'update_appearance'):
                self.connection.update_appearance()
            elif hasattr(self.connection, 'update'):
                self.connection.update()

class UpdateConnectionStyleCommand(Command):
    """Command to update a connection's routing style with undo/redo support."""
    
    def __init__(self, connection, old_style, new_style):
        """Initialize the command.
        
        Args:
            connection: The connection whose routing style is being changed
            old_style: Original routing style
            new_style: New routing style to set
        """
        super().__init__("Change Connection Style")
        self.connection = connection
        self.old_style = old_style
        self.new_style = new_style
    
    def execute(self):
        """Set the new routing style."""
        if hasattr(self.connection, 'set_routing_style'):
            self.connection.set_routing_style(self.new_style)
        else:
            self.connection.routing_style = self.new_style
            # Update path if possible
            if hasattr(self.connection, 'update_path'):
                self.connection.update_path()
    
    def undo(self):
        """Restore the old routing style."""
        if hasattr(self.connection, 'set_routing_style'):
            self.connection.set_routing_style(self.old_style)
        else:
            self.connection.routing_style = self.old_style
            # Update path if possible
            if hasattr(self.connection, 'update_path'):
                self.connection.update_path()

class OptimizeLayoutCommand(Command):
    """Command for optimizing the layout of devices with undo/redo support."""
    
    def __init__(self, controller, devices, algorithm="force_directed"):
        """Initialize the layout optimization command.
        
        Args:
            controller: ConnectionController instance
            devices: List of devices to optimize
            algorithm: Layout algorithm to use
        """
        super().__init__(f"Optimize Layout ({algorithm})")
        self.controller = controller
        self.devices = devices
        self.algorithm = algorithm
        self.original_positions = {device: device.scenePos() for device in devices}
        self.new_positions = {}  # Will be populated after execute
    
    def execute(self):
        """Execute the layout optimization."""
        # Run the layout optimization
        result = self.controller.optimize_topology_layout(self.devices, self.algorithm)
        
        # Store the new positions for undo/redo
        self.new_positions = {device: device.scenePos() for device in self.devices}
        
        return result
    
    def undo(self):
        """Undo the layout optimization by restoring original positions."""
        for device, position in self.original_positions.items():
            device.setPos(position)
        
        # Update all connections
        for device in self.devices:
            for connection in device.connections:
                if hasattr(connection, 'update_path'):
                    connection.update_path()
                elif hasattr(connection, '_update_path'):
                    connection._update_path()
        
        # Force update the canvas
        if hasattr(self.controller, 'canvas') and self.controller.canvas:
            self.controller.canvas.viewport().update()
    
    def redo(self):
        """Redo the layout optimization by applying new positions."""
        for device, position in self.new_positions.items():
            device.setPos(position)
        
        # Update all connections
        for device in self.devices:
            for connection in device.connections:
                if hasattr(connection, 'update_path'):
                    connection.update_path()
                elif hasattr(connection, '_update_path'):
                    connection._update_path()
        
        # Force update the canvas
        if hasattr(self.controller, 'canvas') and self.controller.canvas:
            self.controller.canvas.viewport().update()

class SetBoundaryColorCommand(Command):
    """Command to change a boundary's color."""
    
    def __init__(self, boundary, old_color, new_color):
        super().__init__(f"Change Boundary Color")
        self.boundary = boundary
        self.old_color = old_color
        self.new_color = new_color
        self.logger = logging.getLogger(__name__)
    
    def execute(self):
        """Set the boundary's color to the new color."""
        self.logger.debug(f"Setting boundary {self.boundary.name} color to {self.new_color.name()}")
        self.boundary.set_color(self.new_color)
    
    def undo(self):
        """Restore the boundary's original color."""
        self.logger.debug(f"Restoring boundary {self.boundary.name} color to {self.old_color.name()}")
        self.boundary.set_color(self.old_color)
