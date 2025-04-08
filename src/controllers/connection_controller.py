import random
from PyQt5.QtWidgets import QMessageBox, QGraphicsItem, QDialog
from PyQt5.QtCore import Qt, QTimer
import logging
import traceback
import math

from models.connection import Connection
from controllers.commands import AddConnectionCommand, DeleteConnectionCommand
from constants import ConnectionTypes, RoutingStyle, Modes
from dialogs.multi_connection_dialog import MultiConnectionDialog

class ConnectionController:
    """Controller for managing connection-related operations."""
    
    def __init__(self, canvas, event_bus, undo_redo_manager=None):
        self.canvas = canvas
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        self.undo_redo_manager = undo_redo_manager
        self.theme_manager = None  # Will be set by main window
        self.connecting_device = None
        self.temp_line_id = None
        
        # Debug flag for more verbose logging
        self.debug_mode = True
        
        # Flag to prevent multiple connection dialogs
        self.connection_operation_in_progress = False
        
        # Connect to canvas signals
        self.canvas.add_connection_requested.connect(self.on_add_connection_requested)
        # IMPORTANT: Do not connect connect_multiple_devices_requested signal here.
        # It's already connected in MainWindow.connect_signals() which would cause duplicate calls.
        # This was fixed on April 7, 2025 - previously caused dialogs to be shown twice.
    
    def on_add_connection_requested(self, source_device, target_device, properties=None):
        """Handle request to add a new connection."""
        try:
            self.logger.info(f"Adding connection between devices")
            
            # Make sure both devices are actual Device objects
            if not hasattr(source_device, 'get_nearest_port') or not hasattr(target_device, 'get_nearest_port'):
                self.logger.error("Invalid device objects provided for connection")
                return False
            
            # Check if a connection already exists between these devices in EITHER direction
            if self._connection_exists(source_device, target_device):
                self.logger.info(f"Connection already exists between {source_device.name} and {target_device.name}")
                return False
            
            # Calculate optimal connection ports
            target_center = target_device.get_center_position()
            source_center = source_device.get_center_position()
            
            source_port = source_device.get_nearest_port(target_center)
            target_port = target_device.get_nearest_port(source_center)
            
            # Delegate to shared method
            result = self.on_connection_requested(source_device, target_device, source_port, target_port, properties)
            
            # Reset to SELECT mode after connection is created (with a small delay to ensure UI is updated)
            QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
            
            return result
        except Exception as e:
            self.logger.error(f"Error handling add connection request: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def on_connection_requested(self, source_device, target_device, source_port=None, target_port=None, properties=None):
        """Common method for creating a connection with undo/redo support."""
        try:
            # Use command pattern if available
            if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
                from controllers.commands import AddConnectionCommand
                command = AddConnectionCommand(
                    controller=self, 
                    source_device=source_device, 
                    target_device=target_device, 
                    properties=properties
                )
                self.undo_redo_manager.push_command(command)
                return command.connection  # Return the created connection
            else:
                # No undo/redo support, create directly
                return self.create_connection(source_device, target_device, source_port, target_port, properties)
        except Exception as e:
            self.logger.error(f"Error creating connection: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def on_delete_connection_requested(self, connection):
        """Handle request to delete a specific connection."""
        try:
            # Use command pattern if undo_redo_manager is available and not already in command
            if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
                from controllers.commands import DeleteConnectionCommand
                command = DeleteConnectionCommand(self, connection)
                self.undo_redo_manager.push_command(command)
            else:
                # Direct implementation
                self._delete_connection(connection)
        except Exception as e:
            self.logger.error(f"Error in on_delete_connection_requested: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _delete_connection(self, connection):
        """Actual implementation of connection deletion."""
        if connection is None:
            self.logger.warning("Attempted to delete a null connection")
            return
        
        try:
            # Get devices - handle both target_device and dest_device naming
            source_device = getattr(connection, 'source_device', None)
            
            # Handle both target_device and dest_device naming conventions
            if hasattr(connection, 'target_device'):
                target_device = connection.target_device
            elif hasattr(connection, 'dest_device'):
                target_device = connection.dest_device
                # Add target_device attribute for consistency
                connection.target_device = target_device
            else:
                target_device = None
            
            if source_device and target_device:
                self.logger.info(f"Deleting connection between {source_device.name} and {target_device.name}")
            else:
                self.logger.info("Deleting connection with unknown endpoints")
            
            # Remove from device connections list
            if source_device:
                if hasattr(source_device, 'remove_connection'):
                    source_device.remove_connection(connection)
                elif hasattr(source_device, 'connections') and isinstance(source_device.connections, list):
                    if connection in source_device.connections:
                        source_device.connections.remove(connection)
            
            if target_device:
                if hasattr(target_device, 'remove_connection'):
                    target_device.remove_connection(connection)
                elif hasattr(target_device, 'connections') and isinstance(target_device.connections, list):
                    if connection in target_device.connections:
                        target_device.connections.remove(connection)
            
            # Remove from scene
            if hasattr(connection, 'scene') and callable(connection.scene) and connection.scene():
                self.canvas.scene().removeItem(connection)
            else:
                # Find the connection renderer and remove it if present
                for item in self.canvas.scene().items():
                    if hasattr(item, 'connection') and item.connection == connection:
                        self.canvas.scene().removeItem(item)
            
            # Remove from canvas connections list
            if connection in self.canvas.connections:
                self.canvas.connections.remove(connection)
            else:
                self.logger.warning("Connection not in canvas connections list")
            
            # Notify through event bus
            self.event_bus.emit("connection_removed", connection)
            
            # Force update the canvas view
            self.canvas.viewport().update()
        except Exception as e:
            self.logger.error(f"Error in _delete_connection: {str(e)}")
            self.logger.error(traceback.format_exc())

    def create_connection(self, source_device, target_device, source_port=None, target_port=None, properties=None):
        """Create a connection between two devices."""
        try:
            # Double-check if connection already exists to prevent duplicates
            if self._connection_exists(source_device, target_device):
                self.logger.info(f"Connection already exists between {source_device.name} and {target_device.name}, skipping creation")
                return None
            
            # Create the connection object with debug logging
            if self.debug_mode:
                self.logger.info(f"Creating connection between {source_device.name} and {target_device.name}")
            
            # Get connection type from properties
            connection_type = ConnectionTypes.ETHERNET  # Default
            if properties:
                if 'type' in properties:
                    connection_type = properties['type']
                elif 'connection_type' in properties:
                    connection_type = properties['connection_type']
            
            # Initialize connection with the correct parameters
            connection = Connection(
                source_device=source_device, 
                dest_device=target_device,
                connection_type=connection_type,
                routing_style=RoutingStyle.ORTHOGONAL,  # Default to orthogonal
                props=properties,
                theme_manager=self.theme_manager
            )
            
            # Ensure the connection is selectable with additional debugging
            connection.setFlag(QGraphicsItem.ItemIsSelectable, True)
            connection.setFlag(QGraphicsItem.ItemIsFocusable, True)
            connection.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
            
            if self.debug_mode:
                self.logger.debug(f"Connection flags: ItemIsSelectable={bool(connection.flags() & QGraphicsItem.ItemIsSelectable)}")
                self.logger.debug(f"Connection mouse buttons: {connection.acceptedMouseButtons()}")
            
            # Set connection label if available in properties
            if properties:
                # Get the appropriate label text
                label_text = None
                if 'label_text' in properties and properties['label_text']:
                    label_text = properties['label_text']
                elif 'label' in properties and properties['label']:
                    label_text = properties['label']
                
                # If we have a label text, set it on the connection
                if label_text and hasattr(connection, 'label_text'):
                    connection.label_text = label_text
                    
                    # Force an update of the label position
                    if hasattr(connection.label_manager, 'update_position'):
                        connection.label_manager.update_position()
            
            # Add to scene
            self.canvas.scene().addItem(connection)
            
            # Track in connections list
            self.canvas.connections.append(connection)
            
            # Notify through event bus
            self.event_bus.emit("connection_created", connection)
            
            return connection
            
        except Exception as e:
            self.logger.error(f"Error creating connection: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def on_connect_multiple_devices_requested(self, devices):
        """Handle request to connect multiple devices together.
        
        This creates connections between devices based on the selected strategy.
        
        Args:
            devices: List of selected devices to connect
        """
        self.logger.info(f"CONNECTION DEBUG: Started on_connect_multiple_devices_requested with {len(devices)} devices")
        self.logger.info(f"CONNECTION DEBUG: Current operation flag state: {self.connection_operation_in_progress}")
        
        if len(devices) < 2:
            self.logger.warning("Need at least 2 devices to create connections")
            return False
        
        # Check if a connection operation is already in progress
        if self.connection_operation_in_progress:
            self.logger.info("CONNECTION DEBUG: Connection operation already in progress, ignoring duplicate request")
            return False
            
        # Set flag to indicate connection operation is in progress
        self.connection_operation_in_progress = True
        self.logger.info("CONNECTION DEBUG: Set connection_operation_in_progress = True")
        
        dialog = None
        try:
            # Show the multi-connection dialog to get user input
            self.logger.info("CONNECTION DEBUG: Creating and showing MultiConnectionDialog")
            dialog = MultiConnectionDialog(self.canvas.parent())
            result = dialog.exec_()
            self.logger.info(f"CONNECTION DEBUG: Dialog closed with result: {result}")
            
            if result != QDialog.Accepted:
                self.logger.info("User cancelled the connection dialog")
                self.connection_operation_in_progress = False  # Ensure flag is reset on cancel
                self.logger.info("CONNECTION DEBUG: Reset connection_operation_in_progress = False on cancel")
                return False
                
            # Get the connection data from the dialog
            connection_data = dialog.get_connection_data()
            
            strategy = connection_data['strategy']
            bidirectional = connection_data.get('bidirectional', True)
            
            properties = {
                'type': connection_data['type'],
                'label': connection_data['label'],
                'bandwidth': connection_data['bandwidth'],
                'latency': connection_data['latency']
            }
            
            self.logger.info(f"CONNECTION DEBUG: Using {strategy} strategy to connect {len(devices)} devices")
            
            # Use a composite command if undo/redo is available
            if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
                try:
                    from controllers.commands import CompositeCommand, AddConnectionCommand
                    
                    composite_cmd = CompositeCommand(description=f"Connect {len(devices)} Devices ({strategy})")
                    added_connections = 0  # Track the number of actual connections added
                    
                    # Create connections based on selected strategy
                    # MESH strategy: connect all devices to each other
                    if strategy == "mesh":
                        self.logger.info(f"Creating mesh network connections for {len(devices)} devices")
                        for i in range(len(devices)):
                            source_device = devices[i]
                            for j in range(len(devices)):
                                if i == j:  # Skip self
                                    continue
                                    
                                target_device = devices[j]
                                
                                # For non-bidirectional connections, only create one direction
                                if not bidirectional and j <= i:
                                    continue
                                
                                # Skip if connection already exists in either direction
                                if self._connection_exists(source_device, target_device):
                                    self.logger.info(f"Connection already exists between {source_device.name} and {target_device.name}, skipping")
                                    continue
                                
                                # Create the connection command
                                conn_cmd = AddConnectionCommand(
                                    controller=self,
                                    source_device=source_device, 
                                    target_device=target_device,
                                    properties=properties
                                )
                                
                                composite_cmd.add_command(conn_cmd)
                                added_connections += 1
                    
                    # CHAIN strategy: connect devices in sequence
                    elif strategy == "chain":
                        self.logger.info(f"Creating chain connections for {len(devices)} devices")
                        # Sort devices by position (left to right, then top to bottom)
                        sorted_devices = sorted(devices, key=lambda d: (d.scenePos().y(), d.scenePos().x()))
                        
                        for i in range(len(sorted_devices)-1):
                            source_device = sorted_devices[i]
                            target_device = sorted_devices[i+1]
                            
                            # Create forward connection if it doesn't already exist
                            if not self._connection_exists(source_device, target_device):
                                conn_cmd = AddConnectionCommand(
                                    controller=self,
                                    source_device=source_device, 
                                    target_device=target_device,
                                    properties=properties
                                )
                                composite_cmd.add_command(conn_cmd)
                                added_connections += 1
                            else:
                                self.logger.info(f"Forward connection already exists between {source_device.name} and {target_device.name}, skipping")
                            
                            # Create backward connection if bidirectional
                            if bidirectional and not self._connection_exists(target_device, source_device):
                                conn_cmd = AddConnectionCommand(
                                    controller=self,
                                    source_device=target_device,
                                    target_device=source_device,
                                    properties=properties
                                )
                                composite_cmd.add_command(conn_cmd)
                                added_connections += 1
                            elif bidirectional:
                                self.logger.info(f"Backward connection already exists between {target_device.name} and {source_device.name}, skipping")
                    
                    # Execute the composite command
                    if composite_cmd.commands:  # Only push if there are actual commands to execute
                        self.undo_redo_manager.push_command(composite_cmd)
                        self.logger.info(f"Created {added_connections} connections using strategy '{strategy}'")
                        
                        # Notify through event bus
                        self.event_bus.emit("multiple_connections_added", added_connections)
                        
                        # Reset to SELECT mode after connection is created (with a small delay to ensure UI is updated)
                        QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
                        
                        return True
                    else:
                        self.logger.info("No new connections were created")
                        return False
                except Exception as e:
                    self.logger.error(f"Error in on_connect_multiple_devices_requested with undo/redo: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    return False
            else:
                # Direct implementation without undo/redo
                try:
                    self.logger.warning("Creating connections without undo support")
                    connection_count = 0
                    
                    # Only implementing mesh and chain modes for the direct creation path
                    # as this is less commonly used
                    if strategy == "mesh":
                        # Mesh mode: connect all devices to each other
                        for i in range(len(devices)):
                            source_device = devices[i]
                            for j in range(i+1, len(devices)):
                                target_device = devices[j]
                                
                                # Skip if connection already exists in either direction
                                if self._connection_exists(source_device, target_device):
                                    continue
                                
                                # Create the connection
                                connection = self.create_connection(source_device, target_device, None, None, properties)
                                if connection:
                                    connection_count += 1
                    else:
                        # Chain mode for all other strategies as fallback
                        sorted_devices = sorted(devices, key=lambda d: (d.scenePos().y(), d.scenePos().x()))
                        for i in range(len(sorted_devices)-1):
                            source_device = sorted_devices[i]
                            target_device = sorted_devices[i+1]
                            
                            # Skip if connection already exists in either direction
                            if self._connection_exists(source_device, target_device):
                                continue
                            
                            # Create the connection
                            connection = self.create_connection(source_device, target_device, None, None, properties)
                            if connection:
                                connection_count += 1
                    
                    self.logger.info(f"Created {connection_count} connections")
                    
                    # Reset to SELECT mode after connection is created (with a small delay to ensure UI is updated)
                    QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
                    
                    return connection_count > 0
                except Exception as e:
                    self.logger.error(f"Error in on_connect_multiple_devices_requested without undo/redo: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    return False
        except Exception as e:
            self.logger.error(f"Error in on_connect_multiple_devices_requested: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
        finally:
            # Make absolutely sure the flag is always reset
            self.connection_operation_in_progress = False
            self.logger.info("CONNECTION DEBUG: Reset connection_operation_in_progress = False in finally block")
            
            # Reset to SELECT mode after connection operation (regardless of success or failure)
            QTimer.singleShot(100, lambda: self.canvas.set_mode(Modes.SELECT))
            
            # Clean up dialog if it exists
            if dialog:
                try:
                    dialog.close()
                    dialog.deleteLater()
                except:
                    pass

    def _connection_exists(self, source_device, target_device):
        """Check if a connection already exists between source and target devices.
        
        IMPORTANT: This method checks for connections in BOTH directions (source→target and target→source).
        This prevents duplicate connections from being created when:
        1. Adding single connections between two devices
        2. Using the multiple connection strategies (mesh, chain, closest, etc.)
        3. Adding connections involving devices in boundaries/groups
        
        Any code that calls this method should expect it to return True if ANY connection exists
        between the two devices, regardless of direction.
        """
        # Check direct connections first
        for conn in self.canvas.connections:
            # Get source and target of existing connection
            conn_source = getattr(conn, 'source_device', None)
            
            # Get target using either target_device or dest_device attribute
            conn_target = None
            if hasattr(conn, 'target_device'):
                conn_target = conn.target_device
            elif hasattr(conn, 'dest_device'):
                conn_target = conn.dest_device
            
            # Check if this connection matches our source/target pair in either direction
            if ((conn_source == source_device and conn_target == target_device) or
                (conn_source == target_device and conn_target == source_device)):
                return True
                
            # Also check if these two devices are already connected via same source/target device's connections
            if hasattr(source_device, 'connections') and hasattr(target_device, 'connections'):
                for src_conn in source_device.connections:
                    for tgt_conn in target_device.connections:
                        if src_conn == tgt_conn:  # Same connection object exists in both devices' connection lists
                            return True
        
        return False

    def _show_error(self, message):
        """Show error message dialog."""
        QMessageBox.critical(self.canvas.parent(), "Error", message)

    def set_connection_style(self, style):
        """Set the routing style for selected connections."""
        selected_connections = [
            item for item in self.canvas.scene().selectedItems() 
            if isinstance(item, Connection)
        ]
        
        if self.debug_mode:
            self.logger.debug(f"Found {len(selected_connections)} selected connections")
            
        if not selected_connections:
            self.logger.info("No connections selected to change style")
            return
            
        self.logger.info(f"Setting connection style to {style} for {len(selected_connections)} connections")
        
        # Update style for each selected connection
        for connection in selected_connections:
            if hasattr(connection, 'set_routing_style'):
                connection.set_routing_style(style)
        
        # Force a complete update of the canvas
        self.canvas.viewport().update()

    def set_connection_type(self, connection_type):
        """Set the connection type and visual appearance for selected connections."""
        selected_connections = [
            item for item in self.canvas.scene().selectedItems() 
            if isinstance(item, Connection)
        ]
        
        if self.debug_mode:
            self.logger.debug(f"Found {len(selected_connections)} selected connections")
            
        if not selected_connections:
            self.logger.info("No connections selected to change type")
            return
            
        # Get display name for connection type
        display_name = ConnectionTypes.DISPLAY_NAMES.get(connection_type, "Link")
            
        self.logger.info(f"Setting connection type to {display_name} for {len(selected_connections)} connections")
        
        # Update type and visual style for each selected connection
        for connection in selected_connections:
            connection.connection_type = connection_type
            
            # Update the label to show the connection type
            connection.label_text = display_name
            
            # Apply visual style based on type
            if hasattr(connection, 'set_style_for_type'):
                connection.set_style_for_type(connection_type)
                
        # Force update the view
        self.canvas.viewport().update()
        
    def get_all_connections(self):
        """Get all connections in the canvas."""
        return self.canvas.connections
        
    def debug_connections(self):
        """Print debug information about all connections."""
        if not self.debug_mode:
            return
            
        connections = self.get_all_connections()
        self.logger.debug(f"Total connections: {len(connections)}")
        
        for i, conn in enumerate(connections):
            flags = conn.flags()
            self.logger.debug(f"Connection {i}: ID={conn.id} | Selectable={bool(flags & QGraphicsItem.ItemIsSelectable)} | "
                             f"Visible={conn.isVisible()} | Selected={conn.isSelected()}")

    def optimize_topology_layout(self, devices=None, algorithm="force_directed", iterations=50):
        """Automatically organize the network topology to minimize connection crossings and create an aesthetic layout.
        
        Args:
            devices: List of devices to organize. If None, all devices on the canvas are considered.
            algorithm: Layout algorithm to use ("force_directed", "hierarchical", "radial", or "grid").
            iterations: Number of iterations for iterative algorithms.
        """
        self.logger.info(f"Starting topology optimization using {algorithm} algorithm")
        
        # Get devices if not provided
        if devices is None:
            devices = self.canvas.devices
        
        # Get connections
        connections = self.canvas.connections
        
        if not devices:
            self.logger.warning("No devices to optimize layout for")
            return False
        
        # Store original positions (for undo support)
        original_positions = {device: device.scenePos() for device in devices}
        
        # Choose and apply layout algorithm
        if algorithm == "force_directed":
            self._apply_force_directed_layout(devices, connections, iterations)
        elif algorithm == "hierarchical":
            self._apply_hierarchical_layout(devices, connections)
        elif algorithm == "radial":
            self._apply_radial_layout(devices, connections)
        elif algorithm == "grid":
            self._apply_grid_layout(devices, connections)
        else:
            self.logger.warning(f"Unknown layout algorithm: {algorithm}, using force_directed")
            self._apply_force_directed_layout(devices, connections, iterations)
        
        # Apply a final normalization to ensure all devices are visible and well-distributed
        self._normalize_layout(devices)
        
        # Update all connections
        for connection in connections:
            connection.update_path()
        
        # Emit a signal that devices have moved
        for device in devices:
            if hasattr(device, 'signals') and hasattr(device.signals, 'moved'):
                device.signals.moved.emit(device)
        
        # Force update the canvas
        self.canvas.viewport().update()
        
        # Return success
        return True

    def _normalize_layout(self, devices):
        """Apply final normalization to ensure devices fit well within the viewport.
        
        This is an important final step that ensures all devices remain visible after layout optimization.
        It centers the devices and scales them to fit within the visible area.
        """
        if not devices:
            return
        
        from PyQt5.QtCore import QRectF, QPointF
        
        # Get scene dimensions
        scene_rect = self.canvas.scene().sceneRect()
        target_width = scene_rect.width() * 0.8  # Use 80% of scene width (previously 70%)
        target_height = scene_rect.height() * 0.8  # Use 80% of scene height (previously 70%)
        
        # Calculate current bounding box of all devices
        min_x = min(device.scenePos().x() for device in devices)
        max_x = max(device.scenePos().x() + device.boundingRect().width() for device in devices)
        min_y = min(device.scenePos().y() for device in devices)
        max_y = max(device.scenePos().y() + device.boundingRect().height() for device in devices)
        
        current_width = max(1, max_x - min_x)  # Prevent division by zero
        current_height = max(1, max_y - min_y)
        
        # Calculate scaling factors
        scale_x = target_width / current_width
        scale_y = target_height / current_height
        scale = min(scale_x, scale_y, 1.5)  # Use the smaller scale, but allow some enlargement up to 1.5x
        
        # Calculate the center of the scene
        scene_center_x = scene_rect.width() / 2
        scene_center_y = scene_rect.height() / 2
        
        # Calculate current center of devices
        devices_center_x = (min_x + max_x) / 2
        devices_center_y = (min_y + max_y) / 2
        
        self.logger.info(f"NORMALIZE: Scaling by {scale:.2f}, moving from ({devices_center_x:.0f}, {devices_center_y:.0f}) to ({scene_center_x:.0f}, {scene_center_y:.0f})")
        
        # Apply scaling and centering
        for device in devices:
            # Get current position relative to device center
            pos = device.scenePos()
            rel_x = pos.x() - devices_center_x
            rel_y = pos.y() - devices_center_y
            
            # Scale and recenter in scene
            new_x = scene_center_x + rel_x * scale
            new_y = scene_center_y + rel_y * scale
            
            # Update position
            device.setPos(new_x, new_y)

    def _apply_force_directed_layout(self, devices, connections, iterations=50):
        """Apply force-directed layout to arrange devices.
        
        This algorithm simulates physical forces between devices:
        - Connected devices attract each other
        - All devices repel each other (avoiding overlap)
        - Devices are constrained to stay within canvas bounds
        
        NOTE: Parameters have been tuned to keep devices more contained within the user's view.
        Previously devices could be positioned too far apart, making them hard to see.
        """
        import random
        from PyQt5.QtCore import QPointF
        
        self.logger.info(f"Applying force-directed layout algorithm with {iterations} iterations")
        
        # Get canvas dimensions
        scene_rect = self.canvas.scene().sceneRect()
        width = scene_rect.width()
        height = scene_rect.height()
        
        # Create a mapping of connections for quick lookup
        connection_map = {}
        for conn in connections:
            src = conn.source_device
            tgt = conn.target_device
            if src not in connection_map:
                connection_map[src] = []
            if tgt not in connection_map:
                connection_map[tgt] = []
            connection_map[src].append(tgt)
            connection_map[tgt].append(src)
        
        # Parameters - adjusted for a much more compact layout
        k = 25.0  # Optimal distance between nodes (smaller = more compact)
        temperature = width / 15  # Lower temperature for smaller movements
        cooling_factor = 0.85  # Faster cooling for quicker convergence
        
        # Position devices randomly in a smaller central area for better initial layout
        center_x = width / 2
        center_y = height / 2
        initial_radius = min(width, height) / 5  # Smaller initial radius
        
        # Only randomize positions if devices are very clustered
        positions = [device.scenePos() for device in devices]
        pos_x = [p.x() for p in positions]
        pos_y = [p.y() for p in positions]
        x_range = max(pos_x) - min(pos_x) if pos_x else 0
        y_range = max(pos_y) - min(pos_y) if pos_y else 0
        
        # If devices are too clustered, randomize positions
        if x_range < width / 10 or y_range < height / 10:
            self.logger.info("Initial positions too clustered, randomizing")
            for device in devices:
                angle = random.random() * 2 * 3.14159
                distance = random.random() * initial_radius
                x = center_x + distance * math.cos(angle)
                y = center_y + distance * math.sin(angle)
                device.setPos(x, y)
        
        # Iterate to optimize layout
        for i in range(iterations):
            # Calculate forces and move devices
            displacement = {device: QPointF(0, 0) for device in devices}
            
            # Calculate repulsive forces between all pairs of devices
            for v in devices:
                for u in devices:
                    if u == v:
                        continue
                    
                    # Calculate direction vector
                    delta = QPointF(v.scenePos() - u.scenePos())
                    distance = max(0.1, (delta.x()**2 + delta.y()**2)**0.5)
                    
                    # Repulsive force: inversely proportional to distance
                    force = k**2 / distance
                    
                    # Apply force along the direction vector
                    displacement[v] += delta * (force / distance)
            
            # Calculate attractive forces between connected devices
            for v in devices:
                if v in connection_map:
                    for u in connection_map[v]:
                        # Calculate direction vector
                        delta = QPointF(v.scenePos() - u.scenePos())
                        distance = max(0.1, (delta.x()**2 + delta.y()**2)**0.5)
                        
                        # Attractive force: proportional to distance
                        # Using higher attraction strength for more compact layout
                        force = distance**2 / (k * 0.5)  # Stronger attraction (0.5 instead of 0.7)
                        
                        # Apply force against the direction vector
                        displacement[v] -= delta * (force / distance)
            
            # Apply displacement with temperature control
            for v in devices:
                disp = displacement[v]
                disp_length = max(0.1, (disp.x()**2 + disp.y()**2)**0.5)
                
                # Limit max displacement to temperature
                limited_disp = disp * min(disp_length, temperature) / disp_length
                
                # Update position
                new_pos = v.scenePos() + limited_disp
                
                # Constrain to canvas bounds (with larger margin for better visibility)
                margin = width * 0.1  # 10% margin from edges
                new_x = min(max(margin, new_pos.x()), width - margin)
                new_y = min(max(margin, new_pos.y()), height - margin)
                
                # Set new position
                v.setPos(new_x, new_y)
            
            # Cool down temperature
            temperature *= cooling_factor
            
            # Log progress for longer iterations
            if iterations > 20 and i % (iterations // 5) == 0:
                self.logger.info(f"Force-directed layout progress: {i}/{iterations} iterations")
        
        self.logger.info("Force-directed layout complete")

    def _apply_hierarchical_layout(self, devices, connections):
        """Apply hierarchical layout to arrange devices in levels based on connectivity."""
        from PyQt5.QtCore import QPointF
        
        self.logger.info("Applying hierarchical layout algorithm")
        
        # Get canvas dimensions
        scene_rect = self.canvas.scene().sceneRect()
        width = scene_rect.width()
        height = scene_rect.height()
        
        # Create adjacency list
        adjacency = {device: [] for device in devices}
        for conn in connections:
            src = conn.source_device
            tgt = conn.target_device
            if src in adjacency and tgt in adjacency:
                adjacency[src].append(tgt)
                adjacency[tgt].append(src)
        
        # Find root nodes (devices with fewest connections or routers)
        root_candidates = []
        for device in devices:
            is_router = hasattr(device, 'device_type') and device.device_type == "router"
            connections_count = len(adjacency[device])
            score = -100 if is_router else -connections_count  # Prefer routers, then devices with more connections
            root_candidates.append((score, device))
        
        # Sort by the score (first element of the tuple), not by device
        root_candidates.sort(key=lambda x: x[0])  # Sort by score (ascending)
        roots = [device for _, device in root_candidates[:max(1, len(devices) // 10)]]  # Take top ~10% as roots
        
        # Create hierarchy using BFS from roots
        levels = {root: 0 for root in roots}
        visited = set(roots)
        queue = list(roots)
        
        while queue:
            device = queue.pop(0)
            level = levels[device]
            
            for neighbor in adjacency[device]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    levels[neighbor] = level + 1
                    queue.append(neighbor)
        
        # Handle any devices not visited by BFS (isolated or unreached)
        max_level = max(levels.values()) if levels else 0
        for device in devices:
            if device not in levels:
                levels[device] = max_level + 1
        
        # Determine number of devices per level
        level_counts = {}
        for device, level in levels.items():
            if level not in level_counts:
                level_counts[level] = 0
            level_counts[level] += 1
        
        # Position devices by level - using more compact spacing
        margin_x = width * 0.05  # Use just 5% margin on each side
        margin_y = height * 0.07  # 7% margin top/bottom
        available_width = width - 2 * margin_x
        available_height = height - 2 * margin_y
        
        max_level = max(levels.values())
        
        # Compact level heights - use less vertical space when few levels
        max_level_height = 120  # Maximum height for each level
        min_level_height = 70   # Minimum height for each level
        
        # Adjust level height based on number of levels
        if max_level <= 1:
            level_height = max_level_height
        else:
            level_height = min(max_level_height, 
                              max(min_level_height, available_height / (max_level + 1)))
        
        # Sort devices by connectivity for better placement
        devices_by_level = {}
        for device in devices:
            level = levels[device]
            if level not in devices_by_level:
                devices_by_level[level] = []
            devices_by_level[level].append((len(adjacency[device]), device))
        
        # Position devices level by level
        for level, devices_with_weight in devices_by_level.items():
            # Sort by number of connections within each level
            devices_with_weight.sort(key=lambda x: x[0], reverse=True)
            
            level_count = len(devices_with_weight)
            
            # Calculate optimal device spacing
            if level_count == 1:
                # Center a single device
                level_width = available_width 
            else:
                # Calculate horizontal spacing between devices
                level_width = min(available_width / level_count, 120)  # Cap max spacing
            
            # Center the level in the available width
            level_start_x = margin_x + (available_width - level_width * level_count) / 2
            
            for i, (_, device) in enumerate(devices_with_weight):
                x = level_start_x + (i + 0.5) * level_width
                y = margin_y + level * level_height
                
                # Add small random offset for better visualization
                jitter = level_width * 0.08  # 8% jitter for more natural layout
                x += jitter * (0.5 - random.random())
                y += (level_height * 0.05) * (0.5 - random.random())  # Less vertical jitter
                
                device.setPos(x, y)
        
        self.logger.info("Hierarchical layout complete")

    def _apply_radial_layout(self, devices, connections):
        """Apply radial layout to arrange devices in concentric circles around a center."""
        from PyQt5.QtCore import QPointF
        import math, random
        
        self.logger.info("Applying radial layout algorithm")
        
        # Get canvas dimensions
        scene_rect = self.canvas.scene().sceneRect()
        center_x = scene_rect.width() / 2
        center_y = scene_rect.height() / 2
        
        # Create adjacency list
        adjacency = {device: [] for device in devices}
        for conn in connections:
            src = conn.source_device
            tgt = conn.target_device
            if src in adjacency and tgt in adjacency:
                adjacency[src].append(tgt)
                adjacency[tgt].append(src)
        
        # Find central node (device with most connections or first router)
        central_device = None
        max_connections = -1
        
        for device in devices:
            conn_count = len(adjacency[device])
            is_router = hasattr(device, 'device_type') and device.device_type == "router"
            
            if is_router and (central_device is None or not hasattr(central_device, 'device_type') or 
                              central_device.device_type != "router" or conn_count > max_connections):
                central_device = device
                max_connections = conn_count
            elif not is_router and (central_device is None or conn_count > max_connections):
                if central_device is None or not hasattr(central_device, 'device_type') or central_device.device_type != "router":
                    central_device = device
                    max_connections = conn_count
        
        if not central_device and devices:
            central_device = devices[0]  # Fallback
        
        if not central_device:
            self.logger.warning("No devices available for radial layout")
            return
        
        # Position central device at center
        central_device.setPos(center_x, center_y)
        
        # Create distance rings from center using BFS
        distances = {central_device: 0}
        visited = {central_device}
        queue = [central_device]
        
        while queue:
            device = queue.pop(0)
            distance = distances[device]
            
            for neighbor in adjacency[device]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = distance + 1
                    queue.append(neighbor)
        
        # Handle any unvisited devices
        max_distance = max(distances.values()) if distances else 0
        for device in devices:
            if device not in distances:
                distances[device] = max_distance + 1
        
        # Count devices at each distance
        distance_counts = {}
        for device, dist in distances.items():
            if dist not in distance_counts:
                distance_counts[dist] = 0
            distance_counts[dist] += 1
        
        # Determine maximum radius - more compact
        max_distance = max(distances.values())
        
        # More compact radial layout with smarter radius scaling
        if max_distance <= 1:
            # Special case for simple networks with just one level
            radius_unit = min(center_x, center_y) * 0.4  # Fixed radius for single-ring layouts
        else:
            # For multi-level networks, scale the radius based on the number of levels
            # and use a non-linear scale that gets more compact with more levels
            base_radius = min(center_x, center_y) * 0.6  # Maximum radius is 60% of the smaller dimension
            
            if max_distance <= 3:
                # For networks with few levels, use a linear scale
                radius_unit = base_radius / max(1, max_distance)
            else:
                # For deeper networks, use a non-linear scale that gets tighter with more rings
                radius_unit = base_radius / (max(1, max_distance) ** 0.8)
        
        # Group devices by distance
        devices_by_distance = {}
        for device, dist in distances.items():
            if device == central_device:
                continue  # Skip central device
            
            if dist not in devices_by_distance:
                devices_by_distance[dist] = []
            
            # Store device with its connection count for sorting
            devices_by_distance[dist].append((len(adjacency[device]), device))
        
        # Position devices on concentric circles
        for dist, devices_with_weight in devices_by_distance.items():
            # Sort devices by connection count within each ring
            devices_with_weight.sort(key=lambda x: x[0], reverse=True)
            
            count = len(devices_with_weight)
            
            # Calculate radius for this ring
            radius = dist * radius_unit
            
            # Calculate device spacing based on the number in this ring
            # Ensure minimum angular separation for many devices on the same ring
            min_angle_sep = math.pi / 36  # 5 degrees minimum separation
            
            # Position each device on this ring
            for i, (_, device) in enumerate(devices_with_weight):
                # Calculate angle, distributing devices evenly around the circle
                if count == 1:
                    # Single device on the ring, position at angle 0
                    angle = 0
                else:
                    # Calculate base angle
                    angle = 2 * math.pi * i / count
                    
                    # For rings with many devices, might need to adjust to avoid overlap
                    if count > 36:  # If more than 36 devices (less than 10 degrees apart)
                        # Add slight randomization to break perfect symmetry
                        angle += min_angle_sep * 0.3 * (random.random() - 0.5)
                
                # Add small random variation to radius for more natural layout
                radius_jitter = radius * 0.1 * (0.5 - random.random())
                actual_radius = radius + radius_jitter
                
                # Calculate position
                x = center_x + actual_radius * math.cos(angle)
                y = center_y + actual_radius * math.sin(angle)
                
                device.setPos(x, y)
        
        self.logger.info("Radial layout complete")

    def _apply_grid_layout(self, devices, connections):
        """Apply grid layout to arrange devices in a uniform grid pattern."""
        from PyQt5.QtCore import QPointF
        import math
        
        self.logger.info("Applying grid layout algorithm")
        
        # Get canvas dimensions
        scene_rect = self.canvas.scene().sceneRect()
        width = scene_rect.width()
        height = scene_rect.height()
        
        # Use more compact margins (percentage-based)
        margin_ratio = 0.08  # 8% margin from each edge
        margin_x = width * margin_ratio
        margin_y = height * margin_ratio
        
        available_width = width - 2 * margin_x
        available_height = height - 2 * margin_y
        
        # Determine grid dimensions based on number of devices
        num_devices = len(devices)
        if num_devices <= 0:
            return
        
        # Calculate optimal grid dimensions to maintain aspect ratio
        # while ensuring devices aren't too spread out
        grid_ratio = available_width / available_height
        
        # Calculate optimal number of columns based on device count and aspect ratio
        if num_devices <= 4:
            # For a few devices, use a simple layout
            if num_devices <= 2:
                cols = num_devices
            else:
                cols = 2  # 2x2 grid for 3-4 devices
        else:
            # Balance between aspect ratio and reasonable column count
            ideal_cols = math.sqrt(num_devices * grid_ratio)
            cols = max(2, min(12, math.ceil(ideal_cols)))  # Between 2 and 12 columns
        
        rows = math.ceil(num_devices / cols)
        
        # Calculate cell size with minimum and maximum sizes
        min_cell_width = 80  # Minimum cell width to avoid crowding
        max_cell_width = 180  # Maximum cell width to avoid too much empty space
        
        min_cell_height = 80  # Minimum cell height
        max_cell_height = 180  # Maximum cell height
        
        # Calculate grid cell dimensions
        ideal_cell_width = available_width / max(1, cols)
        ideal_cell_height = available_height / max(1, rows)
        
        # Apply constraints to ensure good spacing
        cell_width = max(min_cell_width, min(ideal_cell_width, max_cell_width))
        cell_height = max(min_cell_height, min(ideal_cell_height, max_cell_height))
        
        # Calculate total grid width and height to center it
        total_grid_width = cell_width * cols
        total_grid_height = cell_height * rows
        
        # Calculate starting position to center the grid
        start_x = margin_x + (available_width - total_grid_width) / 2
        start_y = margin_y + (available_height - total_grid_height) / 2
        
        # Create adjacency list and count connections
        adjacency = {device: [] for device in devices}
        connection_count = {device: 0 for device in devices}
        
        for conn in connections:
            src = conn.source_device
            tgt = conn.target_device
            if src in adjacency and tgt in adjacency:
                adjacency[src].append(tgt)
                adjacency[tgt].append(src)
                connection_count[src] += 1
                connection_count[tgt] += 1
        
        # Sort devices by device type and connection count
        sorted_devices = []
        for device in devices:
            device_type = getattr(device, 'device_type', '')
            # Higher values = higher priority
            type_priority = {
                'router': 100,
                'switch': 90,
                'firewall': 80,
                'server': 70,
                'cloud': 60,
                'workstation': 50
            }.get(device_type, 0)
            
            sorted_devices.append((-(type_priority + connection_count[device]), device))
        
        sorted_devices.sort(key=lambda x: x[0])  # Sort by priority (first element of tuple)
        sorted_devices = [d for _, d in sorted_devices]  # Extract just the devices
        
        # Position devices in grid with a small jitter for better visualization
        for i, device in enumerate(sorted_devices):
            row = i // cols
            col = i % cols
            
            # Calculate base position at the center of the cell
            x = start_x + (col + 0.5) * cell_width
            y = start_y + (row + 0.5) * cell_height
            
            # Add a small random offset for more natural appearance
            jitter = min(cell_width, cell_height) * 0.06  # 6% jitter
            x += jitter * (random.random() - 0.5)
            y += jitter * (random.random() - 0.5)
            
            device.setPos(x, y)
        
        self.logger.info("Grid layout complete")

    def optimize_selected_devices(self, algorithm="force_directed"):
        """Apply layout optimization to currently selected devices with undo/redo support."""
        selected_items = self.canvas.scene().selectedItems()
        selected_devices = [item for item in selected_items if item in self.canvas.devices]
        
        if not selected_devices:
            self.logger.warning("No devices selected for optimization")
            self._show_error("Please select at least two devices to optimize layout")
            return False
        
        if len(selected_devices) < 2:
            self.logger.warning("Need at least two devices for layout optimization")
            self._show_error("Please select at least two devices to optimize layout")
            return False
        
        self.logger.info(f"Optimizing layout for {len(selected_devices)} selected devices using {algorithm} algorithm")
        
        # Use command pattern if undo/redo manager is available
        if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
            from controllers.commands import OptimizeLayoutCommand
            command = OptimizeLayoutCommand(self, selected_devices, algorithm)
            self.undo_redo_manager.push_command(command)
            return True
        else:
            # Direct execution without undo support
            return self.optimize_topology_layout(selected_devices, algorithm)

    def get_line_intersection(self, line1_start, line1_end, line2_start, line2_end):
        """Helper method to detect if two lines intersect."""
        # Implementation of line intersection detection using vector cross product
        def ccw(a, b, c):
            return (c.y() - a.y()) * (b.x() - a.x()) > (b.y() - a.y()) * (c.x() - a.x())
        
        def segment_intersect(a, b, c, d):
            return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)
        
        return segment_intersect(line1_start, line1_end, line2_start, line2_end)

    def count_connection_crossings(self, connections=None):
        """Count the number of connection line crossings in the current layout."""
        if connections is None:
            connections = self.canvas.connections
        
        crossings = 0
        for i, conn1 in enumerate(connections):
            # Get line endpoints for first connection
            src1 = conn1.source_device.scenePos()
            tgt1 = conn1.target_device.scenePos()
            
            for j in range(i+1, len(connections)):
                conn2 = connections[j]
                
                # Skip if connections share an endpoint
                if (conn1.source_device == conn2.source_device or
                    conn1.source_device == conn2.target_device or
                    conn1.target_device == conn2.source_device or
                    conn1.target_device == conn2.target_device):
                    continue
                
                # Get line endpoints for second connection
                src2 = conn2.source_device.scenePos()
                tgt2 = conn2.target_device.scenePos()
                
                # Check for intersection
                if self.get_line_intersection(src1, tgt1, src2, tgt2):
                    crossings += 1
        
        return crossings

    def show_layout_optimization_dialog(self):
        """Show the layout optimization dialog and apply the selected algorithm."""
        # Import here to avoid circular imports
        from views.layout_optimization_dialog import LayoutOptimizationDialog
        
        # Check if we have any devices
        if not self.canvas.devices:
            self._show_error("No devices available to optimize layout")
            return False
        
        # Create and show the dialog
        dialog = LayoutOptimizationDialog(self.canvas.parent())
        
        # Set default scope based on current selection
        selected_items = self.canvas.scene().selectedItems()
        selected_devices = [item for item in selected_items if item in self.canvas.devices]
        if len(selected_devices) >= 2:
            dialog.selected_only_radio.setChecked(True)
        else:
            dialog.all_devices_radio.setChecked(True)
        
        # Show dialog
        if dialog.exec_() != QDialog.Accepted:
            self.logger.info("User cancelled layout optimization")
            return False
        
        # Get parameters
        params = dialog.get_parameters()
        algorithm = params['algorithm']
        iterations = params['iterations']
        selected_only = params['selected_only']
        
        self.logger.info(f"Applying layout optimization with {algorithm} algorithm")
        
        # Apply to selected devices or all devices
        if selected_only:
            if len(selected_devices) < 2:
                self._show_error("Please select at least two devices to optimize layout")
                return False
            return self.optimize_selected_devices(algorithm=algorithm)
        else:
            # Create command for all devices with undo/redo support
            if self.undo_redo_manager and not self.undo_redo_manager.is_in_command_execution():
                from controllers.commands import OptimizeLayoutCommand
                command = OptimizeLayoutCommand(self, self.canvas.devices, algorithm)
                self.undo_redo_manager.push_command(command)
                return True
            else:
                # Direct execution without undo support
                return self.optimize_topology_layout(self.canvas.devices, algorithm, iterations)
