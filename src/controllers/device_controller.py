from PyQt5.QtWidgets import QDialog, QMessageBox, QGraphicsItem
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QFontMetrics, QColor, QFont
import logging
import traceback
import math

from models.device import Device
from models.connection import Connection
from views.device_dialog import DeviceDialog
from constants import DeviceTypes, ConnectionTypes
from controllers.commands import AddDeviceCommand, DeleteDeviceCommand

class DeviceController:
    """Controller for managing device-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Initialize device counter for generating unique names
        self.device_counter = 0
        self.undo_redo_manager = undo_redo_manager
        
        # Font settings manager reference (will be set externally)
        self.font_settings_manager = None
        
        # Theme manager reference (will be set by main window)
        self.theme_manager = None
    
    def create_device(self, device_type, pos=None, use_command=True, show_dialog=True,
                      device_data=None, custom_icon_path=None, properties=None):
        """Create a new device on the canvas.
        
        Args:
            device_type: Type of device to create
            pos: Position to place the device (optional, center if None)
            use_command: Whether to use command pattern for undo/redo
            show_dialog: Whether to show the device dialog
            device_data: Pre-filled device data dictionary
            custom_icon_path: Path to custom icon
            properties: Custom device properties
            
        Returns:
            The created device, or None if creation was cancelled
        """
        try:
            self.logger.info(f"Creating device of type {device_type}")
            
            # Default position at center if none provided
            if pos is None:
                scene_rect = self.canvas.scene().sceneRect()
                pos = QPointF(scene_rect.width() / 2, scene_rect.height() / 2)
                self.logger.info(f"Using default position: {pos}")
            
            # Show dialog to get device details if requested
            if show_dialog:
                dialog = DeviceDialog(device_data=device_data, device_type=device_type)
                result = dialog.exec_()
                
                # If dialog was accepted, get the device data
                if result == QDialog.Accepted:
                    device_data = dialog.get_values()
                    self.logger.info(f"Device dialog accepted, creating device with name: {device_data.get('name')}")
                    
                    # Check if multiple devices should be created
                    if dialog.is_multiple():
                        count = dialog.get_multiplier()
                        spacing_data = dialog.get_spacing_data()
                        connection_data = dialog.get_connection_data()
                        
                        # Create multiple devices
                        if use_command and self.undo_redo_manager:
                            from controllers.commands import CompositeCommand
                            cmd = CompositeCommand("Create multiple devices")
                            devices = self._create_multiple_devices_with_commands(
                                device_data, pos, count, cmd, 
                                should_connect=dialog.should_connect(),
                                connection_data=connection_data,
                                spacing_data=spacing_data
                            )
                            self.undo_redo_manager.execute_command(cmd)
                            return devices
                        else:
                            return self._create_multiple_devices(
                                device_data, pos, count, 
                                should_connect=dialog.should_connect(),
                                connection_data=connection_data,
                                spacing_data=spacing_data
                            )
                else:
                    self.logger.info("Device dialog cancelled, not creating device")
                    return None
            
            # If no dialog shown, or dialog accepted, create the device
            name = device_data.get('name') if device_data else f"{device_type}_{self.device_counter}"
            properties = device_data.get('properties') if device_data else properties
            custom_icon = device_data.get('custom_icon_path') if device_data else custom_icon_path
            
            # Create device object
            device = Device(name, device_type, properties, custom_icon)
            self.logger.info(f"Created device object: {device.name}, type: {device.device_type}")
            
            # Set position
            device.setPos(pos)
            
            # Apply font settings if available
            if self.font_settings_manager:
                device.update_font_settings(self.font_settings_manager)
            
            # Register device as theme observer if theme manager is available
            if self.theme_manager:
                self.theme_manager.register_theme_observer(device)
                # Apply current theme immediately
                device.update_theme(self.theme_manager.get_theme())
            
            # Increment counter for next device
            self.device_counter += 1
            
            # Create and execute command if using command pattern
            if use_command and self.undo_redo_manager:
                self.logger.info("Using command pattern to add device")
                cmd = AddDeviceCommand(self.canvas, device)
                self.undo_redo_manager.execute_command(cmd)
            else:
                # Otherwise add directly to canvas
                self.logger.info("Adding device directly to canvas")
                self.canvas.scene().addItem(device)
                self.canvas.devices.append(device)
            
            # Connect signals
            if hasattr(self.canvas, 'device_drag_started'):
                device.signals.drag_started.connect(self.canvas.device_drag_started)
            if hasattr(self.canvas, 'device_drag_finished'):
                device.signals.drag_finished.connect(self.canvas.device_drag_finished)
            
            # Emit creation signal
            self.event_bus.emit("device_created", device)
            
            # Log success
            self.logger.info(f"Successfully created device: {device.name}")
            return device
            
        except Exception as e:
            self.logger.error(f"Error creating device: {str(e)}")
            self.logger.error(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Failed to create device: {str(e)}")
            return None
            
    def on_add_device_requested(self, pos=None):
        """Show dialog to add a new device."""
        try:
            # Only create dialog when explicitly requested
            self.logger.info("Explicitly opening device dialog for adding a new device")
            dialog = DeviceDialog(self.canvas.parent())
            if dialog.exec_() == QDialog.Accepted:
                device_data = dialog.get_device_data()
                multiplier = dialog.get_multiplier()
                
                # Get connection options
                should_connect = dialog.should_connect_devices()
                connection_data = dialog.get_connection_data() if should_connect else None
                
                # Get grid spacing data
                spacing_data = dialog.get_spacing_data()
                
                # Store connection data temporarily for spacing calculations
                if should_connect:
                    self.canvas.connection_data = connection_data
                else:
                    self.canvas.connection_data = None
                
                if multiplier <= 1:
                    # Create a single device with undo support
                    if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
                        # Create device using command for undo support
                        cmd = AddDeviceCommand(
                            self, 
                            device_data['type'], 
                            pos, 
                            device_data['name'],
                            device_data.get('properties', {}),
                            device_data.get('custom_icon_path')
                        )
                        self.undo_redo_manager.push_command(cmd)
                        return True
                    else:
                        # Create without undo support
                        self._create_device(
                            device_data['name'],
                            device_data['type'],
                            pos,
                            device_data.get('properties', {}),
                            device_data.get('custom_icon_path')
                        )
                else:
                    # Create multiple devices in a grid
                    self.logger.debug(f"BULK ADD: Starting creation of {multiplier} devices with spacing: {spacing_data}")
                    
                    # Calculate initial position if not provided
                    if pos is None:
                        scene_rect = self.canvas.scene().sceneRect()
                        pos = QPointF(scene_rect.width() / 2, scene_rect.height() / 2)
                    
                    # Create devices with proper spacing
                    devices = []
                    for i in range(multiplier):
                        # Calculate position based on grid
                        row = i // 5  # 5 devices per row
                        col = i % 5
                        device_pos = QPointF(
                            pos.x() + col * spacing_data['horizontal'],
                            pos.y() + row * spacing_data['vertical']
                        )
                        
                        # Create device with incremented name
                        device_name = f"{device_data['name']} {i + 1}"
                        device = self._create_device(
                            device_name,
                            device_data['type'],
                            device_pos,
                            device_data.get('properties', {}),
                            device_data.get('custom_icon_path')
                        )
                        
                        if device:
                            devices.append(device)
                    
                    # Connect devices if specified
                    if should_connect and devices and len(devices) > 1:
                        self._connect_multiple_devices(devices, connection_data)
                    
                self.logger.info(f"Added {multiplier} device(s) of type {device_data['type']}")
                return True
        except Exception as e:
            self.logger.error(f"Error adding device: {str(e)}")
            self.logger.debug(traceback.format_exc())
            self._show_error(f"Failed to add device: {str(e)}")
        return False
    
    def _create_multiple_devices(self, device_data, pos, count, should_connect=False, 
                               connection_data=None, spacing_data=None):
        """Create multiple devices with optional connections."""
        devices = []
        base_name = device_data.get('name', '')
        base_type = device_data.get('type')
        properties = device_data.get('properties', {})
        custom_icon = device_data.get('custom_icon_path')
        
        # Calculate grid dimensions for aesthetic layout
        # Use a 3-column grid by default, but adjust based on count
        max_columns = 3
        if count <= 3:
            max_columns = count
        elif count <= 6:
            max_columns = 3
        elif count <= 9:
            max_columns = 3
        else:
            max_columns = 4
            
        columns = min(count, max_columns)
        rows = (count + columns - 1) // columns  # Ceiling division
        
        # Set default spacing
        horizontal_spacing = 150  # Default horizontal spacing
        vertical_spacing = 150   # Default vertical spacing
        
        # Override with spacing data if provided
        if spacing_data:
            horizontal_spacing = spacing_data.get('horizontal', horizontal_spacing)
            vertical_spacing = spacing_data.get('vertical', vertical_spacing)
        
        # Create devices in grid
        for i in range(count):
            row = i // columns
            col = i % columns
            
            # Calculate position
            x = pos.x() + col * horizontal_spacing
            y = pos.y() + row * vertical_spacing
            
            # Create device with incremented name
            device_name = f"{base_name} {i + 1}"
            device = self._create_device(
                device_name,
                base_type,
                QPointF(x, y),
                properties,
                custom_icon
            )
            
            if device:
                devices.append(device)
        
        # Connect devices if specified
        if should_connect and devices and len(devices) > 1:
            self._connect_multiple_devices(devices, connection_data)
        
        return devices

    def _create_multiple_devices_with_commands(self, device_data, pos, count, composite_cmd, should_connect=False, connection_data=None, spacing_data=None):
        """Create multiple devices with undo/redo support."""
        devices = []
        base_name = device_data.get('name', '')
        model_name = device_data.get('properties', {}).get('model', '')
        
        # If we have a model name, use it as the base for naming
        if model_name:
            base_name = model_name
            
        # Create a copy of the device data for this instance
        instance_data = device_data.copy()
        
        for i in range(count):
            # Set the name using the model name with sequential numbering
            instance_data['name'] = f"{base_name} {i + 1}"
            
            # Create device command
            cmd = AddDeviceCommand(
                self,
                instance_data['type'],
                pos,
                instance_data['name'],
                instance_data.get('properties', {}),
                instance_data.get('custom_icon_path')
            )
            
            # Add command to composite
            composite_cmd.add_command(cmd)
            
            # Execute command to create device
            device = cmd.execute()
            if device:
                devices.append(device)
                
                # Update position for next device if spacing data is provided
                if spacing_data and i < count - 1:
                    pos = self._calculate_next_position(pos, spacing_data, i + 1)
        
        # Connect devices if requested
        if should_connect and len(devices) > 1:
            self._connect_multiple_devices(devices, connection_data)
            
        return devices
    
    def _connect_devices(self, device_info, connection_data):
        """Connect devices in a grid pattern."""
        try:
            devices = device_info['devices']
            positions = device_info['positions']
            grid_size = device_info['grid_size']
            rows, cols = grid_size
            
            # Create a 2D grid representation for easier lookup
            grid = {}
            for row, col, device in positions:
                grid[(row, col)] = device
            
            self.logger.debug(f"Connecting devices in grid of {rows}x{cols}")
            for row in range(rows):
                for col in range(cols):
                    # Connect horizontally to the right
                    if col < cols-1 and (row, col) in grid and (row, col+1) in grid:
                        source = grid[(row, col)]
                        target = grid[(row, col+1)]
                        self.logger.debug(f"Creating horizontal connection: {source.name} -> {target.name}")
                        self._create_connection(source, target, connection_data)
                    
                    # Connect vertically downward
                    if row < rows-1 and (row, col) in grid and (row+1, col) in grid:
                        source = grid[(row, col)]
                        target = grid[(row+1, col)]
                        self.logger.debug(f"Creating vertical connection: {source.name} -> {target.name}")
                        self._create_connection(source, target, connection_data)
                    
        except Exception as e:
            self.logger.error(f"Error creating connections: {str(e)}")
            traceback.print_exc()
            self._show_error(f"Failed to create connections: {str(e)}")

    def _connect_devices_with_commands(self, device_info, connection_data, composite_cmd):
        """Connect devices with chosen connection strategy and undo/redo support."""
        try:
            devices = device_info['devices']
            strategy = connection_data.get('strategy', 'mesh')
            bidirectional = connection_data.get('bidirectional', True)
            
            # Import the necessary command class
            from controllers.commands import AddConnectionCommand
            
            # Get the connection controller
            connection_controller = self._get_connection_controller()
            
            # Log detailed connection controller retrieval attempts
            self.logger.debug(f"Connection controller lookup: {connection_controller}")
            
            if not connection_controller:
                self.logger.error("Connection controller not found, attempting alternative access methods")
                
                # Try alternative methods to get the connection controller
                if hasattr(self.event_bus, 'controllers') and 'connection_controller' in self.event_bus.controllers:
                    connection_controller = self.event_bus.controllers['connection_controller']
                    self.logger.info("Retrieved connection controller from event_bus.controllers dictionary")
                elif hasattr(self.canvas, 'parent') and hasattr(self.canvas.parent(), 'connection_controller'):
                    connection_controller = self.canvas.parent().connection_controller
                    self.logger.info("Retrieved connection controller from canvas parent")
                else:
                    # Create our own connections if we can't find the controller
                    self.logger.warning("Creating connections directly instead of using controller")
                    self._connect_devices(device_info, connection_data)
                    return
            
            self.logger.info(f"Connecting devices using strategy: {strategy}")
            
            # Apply the selected connection strategy
            if strategy == "mesh":
                # All-to-all connections (mesh)
                self._create_mesh_connections(devices, connection_controller, connection_data, composite_cmd, bidirectional)
            
            elif strategy == "chain":
                # Sequential chain connections (1→2→3→...)
                self._create_chain_connections(devices, connection_controller, connection_data, composite_cmd, bidirectional)
            
            elif strategy == "closest":
                # Each device connects to its closest neighbor
                self._create_closest_connections(devices, connection_controller, connection_data, composite_cmd, bidirectional)
            
            elif strategy == "closest_type":
                # Each device connects to its closest neighbor of a specific type
                target_type = connection_data.get('target_device_type')
                self._create_closest_type_connections(devices, target_type, connection_controller, 
                                                    connection_data, composite_cmd, bidirectional)
            else:
                self.logger.warning(f"Unknown connection strategy: {strategy}, defaulting to mesh")
                self._create_mesh_connections(devices, connection_controller, connection_data, composite_cmd, bidirectional)
                
        except Exception as e:
            self.logger.error(f"Error creating connections with commands: {str(e)}")
            traceback.print_exc()

    def _create_mesh_connections(self, devices, connection_controller, connection_data, composite_cmd, bidirectional):
        """Create all-to-all (mesh) connections between devices."""
        from controllers.commands import AddConnectionCommand
        
        self.logger.debug(f"Creating mesh connections between {len(devices)} devices")
        
        for i, source in enumerate(devices):
            for j, target in enumerate(devices):
                if source != target:  # Don't connect to self
                    if not bidirectional and j <= i:
                        # Skip if we only want one-direction connections and
                        # we've already created the reciprocal connection
                        continue
                        
                    self.logger.debug(f"Adding connection: {source.name} → {target.name}")
                    conn_cmd = AddConnectionCommand(
                        connection_controller,
                        source,
                        target,
                        None,  # source_port (will be calculated)
                        None,  # target_port (will be calculated)
                        connection_data
                    )
                    composite_cmd.add_command(conn_cmd)

    def _create_chain_connections(self, devices, connection_controller, connection_data, composite_cmd, bidirectional):
        """Create sequential chain connections between devices (1→2→3→...)."""
        from controllers.commands import AddConnectionCommand
        
        self.logger.debug(f"Creating chain connections between {len(devices)} devices")
        
        # Sort devices by position (left to right, then top to bottom) for better logical flow
        devices_sorted = sorted(devices, key=lambda d: (d.scenePos().y(), d.scenePos().x()))
        
        for i in range(len(devices_sorted) - 1):
            source = devices_sorted[i]
            target = devices_sorted[i + 1]
            
            self.logger.debug(f"Adding chain connection: {source.name} → {target.name}")
            conn_cmd = AddConnectionCommand(
                connection_controller,
                source,
                target,
                None,
                None,
                connection_data
            )
            composite_cmd.add_command(conn_cmd)
            
            # Add reverse connection if bidirectional
            if bidirectional:
                self.logger.debug(f"Adding reverse chain connection: {target.name} → {source.name}")
                conn_cmd = AddConnectionCommand(
                    connection_controller,
                    target,
                    source,
                    None,
                    None,
                    connection_data
                )
                composite_cmd.add_command(conn_cmd)

    def _create_closest_connections(self, devices, connection_controller, connection_data, composite_cmd, bidirectional):
        """Connect each device to its closest neighbor."""
        from controllers.commands import AddConnectionCommand
        import math
        
        self.logger.debug(f"Creating closest-neighbor connections for {len(devices)} devices")
        
        # For each device, find the closest other device
        for source in devices:
            closest_device = None
            min_distance = float('inf')
            
            source_pos = source.scenePos()
            
            for target in devices:
                if source == target:  # Skip self
                    continue
                    
                target_pos = target.scenePos()
                # Calculate Euclidean distance
                distance = math.sqrt(
                    (source_pos.x() - target_pos.x()) ** 2 + 
                    (source_pos.y() - target_pos.y()) ** 2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_device = target
            
            if closest_device:
                self.logger.debug(f"Adding closest connection: {source.name} → {closest_device.name}")
                conn_cmd = AddConnectionCommand(
                    connection_controller,
                    source,
                    closest_device,
                    None,
                    None,
                    connection_data
                )
                composite_cmd.add_command(conn_cmd)
                
                # If bidirectional and we haven't already created the reverse connection
                if bidirectional:
                    self.logger.debug(f"Adding reverse closest connection: {closest_device.name} → {source.name}")
                    conn_cmd = AddConnectionCommand(
                        connection_controller,
                        closest_device,
                        source,
                        None,
                        None,
                        connection_data
                    )
                    composite_cmd.add_command(conn_cmd)

    def _create_closest_type_connections(self, devices, target_type, connection_controller, 
                                      connection_data, composite_cmd, bidirectional):
        """Connect each device to its closest neighbor of a specific type."""
        from controllers.commands import AddConnectionCommand
        import math
        
        self.logger.debug(f"Creating closest-type connections for {len(devices)} devices, targeting type: {target_type}")
        
        # Filter devices by the target type
        target_devices = [d for d in devices if d.device_type == target_type]
        
        if not target_devices:
            self.logger.warning(f"No devices of type '{target_type}' found for connection")
            return
        
        # For each device, find the closest device of the target type
        for source in devices:
            # Skip if source is of the target type and we only want connections to different types
            if source.device_type == target_type and not connection_data.get('connect_same_type', False):
                continue
            
            closest_device = None
            min_distance = float('inf')
            
            source_pos = source.scenePos()
            
            for target in target_devices:
                if source == target:  # Skip self
                    continue
                    
                target_pos = target.scenePos()
                # Calculate Euclidean distance
                distance = math.sqrt(
                    (source_pos.x() - target_pos.x()) ** 2 + 
                    (source_pos.y() - target_pos.y()) ** 2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_device = target
            
            if closest_device:
                self.logger.debug(f"Adding closest-type connection: {source.name} → {closest_device.name}")
                conn_cmd = AddConnectionCommand(
                    connection_controller,
                    source,
                    closest_device,
                    None,
                    None,
                    connection_data
                )
                composite_cmd.add_command(conn_cmd)
                
                # If bidirectional and target device isn't of the same type as source
                if bidirectional and closest_device not in target_devices:
                    self.logger.debug(f"Adding reverse closest-type connection: {closest_device.name} → {source.name}")
                    conn_cmd = AddConnectionCommand(
                        connection_controller,
                        closest_device,
                        source,
                        None,
                        None,
                        connection_data
                    )
                    composite_cmd.add_command(conn_cmd)

    def _create_device(self, name, device_type, position, properties=None, custom_icon_path=None):
        """Create a device object and add it to the canvas."""
        try:
            # Use the model name if available and no name was provided
            if not name and properties and 'model' in properties and properties['model']:
                model_name = properties['model']
                self.device_counter += 1
                name = f"{model_name} {self.device_counter}"
            # Otherwise generate sequential device name if not provided or keep the passed name
            elif not name:
                # Generate Device N
                self.device_counter += 1
                name = f"Device {self.device_counter}"
            elif name.lower().startswith("device "):
                # If it's already named Device X, extract the number to track, but don't increment
                try:
                    parts = name.split()
                    if len(parts) > 1 and parts[-1].isdigit():
                        device_num = int(parts[-1])
                        if device_num > self.device_counter:
                            self.device_counter = device_num
                except:
                    pass
            
            # Create device with properties
            device = Device(name, device_type, properties, custom_icon_path)
            
            # Set position
            if position:
                device.setPos(position)
            
            # Apply theme if available
            if self.theme_manager:
                # Register device with theme manager
                self.theme_manager.register_theme_observer(device)
                # Apply current theme immediately
                device.update_theme(self.theme_manager.get_theme())
            
            # Set font settings if available
            if self.font_settings_manager:
                device.font_settings_manager = self.font_settings_manager
                device.update_font_settings(self.font_settings_manager)
            
            # Add to scene and tracking list
            scene = self.canvas.scene()
            if scene:
                scene.addItem(device)
                self.canvas.devices.append(device)
                
                # Connect signals
                if hasattr(self.canvas, 'device_drag_started'):
                    device.signals.drag_started.connect(self.canvas.device_drag_started)
                if hasattr(self.canvas, 'device_drag_finished'):
                    device.signals.drag_finished.connect(self.canvas.device_drag_finished)
                
                # Emit creation signal
                self.event_bus.emit("device_created", device)
                
                # Force a view update
                self.canvas.viewport().update()
                
                return device
            else:
                self.logger.error("No scene available to add device")
                return None
            
        except Exception as e:
            self.logger.error(f"Error creating device: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
    
    def on_delete_device_requested(self, device):
        """Handle request to delete a device."""
        # Use command manager if available, otherwise delete directly
        if hasattr(self, 'command_manager') and self.command_manager:
            from controllers.commands import DeleteDeviceCommand
            cmd = DeleteDeviceCommand(self, device)
            self.command_manager.execute_command(cmd)
        else:
            self._delete_device(device)

    def _delete_device(self, device):
        """Delete a device from the canvas.
        
        This method ensures all device components (image, label, box) are deleted together.
        """
        try:
            self.logger.info(f"Deleting device: {device}")
            
            # First, remove the device from device list
            if device in self.canvas.devices:
                self.canvas.devices.remove(device)
            
            # Remove any connected connections
            connected_connections = []
            for conn in self.canvas.connections[:]:  # Use a copy of the list to avoid modification during iteration
                if conn.source_device == device or conn.target_device == device:
                    connected_connections.append(conn)
            
            # Use connection controller to properly delete the connections
            for conn in connected_connections:
                self.event_bus.emit('connection.delete_requested', connection=conn)
            
            # Remove all child components first (if the device is a composite with children)
            if hasattr(device, 'childItems'):
                # Create a copy of the list to avoid modification during iteration
                children = list(device.childItems())
                for child in children:
                    self.canvas.scene().removeItem(child)
            
            # Now remove the device itself from the scene
            self.canvas.scene().removeItem(device)
            
            # Notify UI of the change
            self.canvas.viewport().update()
            
            # Notify the event bus - use emit instead of publish
            self.event_bus.emit('device.deleted', device=device)
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting device: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)

    def _get_connection_controller(self):
        """Helper to get the connection controller for proper deletion routing."""
        connection_controller = None
        
        # Method 1: Try to get from event_bus get_controller method
        if hasattr(self.event_bus, 'get_controller'):
            connection_controller = self.event_bus.get_controller('connection_controller')
            if connection_controller:
                self.logger.debug("Found connection_controller via event_bus.get_controller")
                return connection_controller
        
        # Method 2: Try direct access through main window
        if hasattr(self.canvas, 'parent'):
            parent = self.canvas.parent()
            if hasattr(parent, 'connection_controller'):
                connection_controller = parent.connection_controller
                self.logger.debug("Found connection_controller via canvas.parent()")
                return connection_controller
        
        # Method 3: Try to find in event_bus controllers dictionary
        if hasattr(self.event_bus, 'controllers'):
            if 'connection_controller' in self.event_bus.controllers:
                connection_controller = self.event_bus.controllers['connection_controller']
                self.logger.debug("Found connection_controller via event_bus.controllers")
                return connection_controller
                
        self.logger.error("Failed to find connection_controller")
        return None

    def _remove_connection_manually(self, conn):
        """Manual connection cleanup when connection controller isn't available."""
        if conn in self.canvas.connections:
            self.canvas.connections.remove(conn)
        
        if conn.scene():
            self.canvas.scene().removeItem(conn)
        
        # Remove from devices' connection lists
        if hasattr(conn.source_device, 'connections'):
            if conn in conn.source_device.connections:
                conn.source_device.connections.remove(conn)
        
        if hasattr(conn.target_device, 'connections'):
            if conn in conn.target_device.connections:
                conn.target_device.connections.remove(conn)

    def _connect_multiple_devices(self, devices, connection_data):
        """Connect multiple devices in a chain."""
        if len(devices) < 2:
            return
            
        # Get connection properties
        conn_type = connection_data.get('type', ConnectionTypes.ETHERNET)
        label = connection_data.get('label', 'Ethernet')
        bandwidth = connection_data.get('bandwidth', '')
        latency = connection_data.get('latency', '')
        
        # Create connections between adjacent devices
        for i in range(len(devices) - 1):
            source = devices[i]
            target = devices[i + 1]
            
            # Create connection
            connection = Connection(source, target, conn_type)
            
            # Set label using label_text property
            if hasattr(connection, 'label_text'):
                connection.label_text = label
            
            # Set properties
            if bandwidth:
                connection.properties['Bandwidth'] = bandwidth
            if latency:
                connection.properties['Latency'] = latency
            
            # Add to canvas
            self.canvas.scene().addItem(connection)
            self.canvas.connections.append(connection)
            
            # Apply theme if available
            if self.theme_manager and hasattr(connection, 'renderer'):
                connection.renderer.update_theme(self.theme_manager.get_theme())
