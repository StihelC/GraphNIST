import json
from PyQt5.QtCore import QPointF, QRectF, QByteArray
from PyQt5.QtGui import QColor
import uuid
import os

class CanvasSerializer:
    """Handles serialization and deserialization of canvas elements."""
    
    @staticmethod
    def serialize_canvas(canvas):
        """Convert canvas state to serializable dictionary."""
        data = {
            'version': '1.0',
            'devices': [],
            'connections': [],
            'boundaries': []
        }
        
        # Debug print for canvas boundaries
        print("\nSerializing canvas with:", len(getattr(canvas, 'boundaries', [])), "boundaries")
        if hasattr(canvas, 'boundaries'):
            for i, boundary in enumerate(canvas.boundaries):
                print(f"  Canvas boundary {i+1}: {boundary.name if hasattr(boundary, 'name') else 'unnamed'}")
        
        # Serialize all devices
        for device in canvas.devices:
            try:
                device_data = CanvasSerializer.serialize_device(device)
                data['devices'].append(device_data)
            except Exception as e:
                import traceback
                print(f"Error serializing device {device.name if hasattr(device, 'name') else 'unknown'}: {str(e)}")
                traceback.print_exc()
        
        # Serialize all connections
        if hasattr(canvas, 'connections'):
            for connection in canvas.connections:
                try:
                    connection_data = CanvasSerializer.serialize_connection(connection)
                    data['connections'].append(connection_data)
                except Exception as e:
                    import traceback
                    print(f"Error serializing connection: {str(e)}")
                    traceback.print_exc()
        
        # Serialize all boundaries
        if hasattr(canvas, 'boundaries'):
            print(f"Canvas has {len(canvas.boundaries)} boundaries to serialize")
            for boundary in canvas.boundaries:
                try:
                    print(f"  Serializing boundary: {boundary.name if hasattr(boundary, 'name') else 'unnamed'}")
                    boundary_data = CanvasSerializer.serialize_boundary(boundary)
                    print(f"  Serialized boundary data: {boundary_data}")
                    data['boundaries'].append(boundary_data)
                except Exception as e:
                    import traceback
                    print(f"Error serializing boundary: {str(e)}")
                    traceback.print_exc()
        else:
            print("Canvas has no 'boundaries' attribute")
        
        # Debug print for serialized data
        print(f"Serialized data has {len(data['boundaries'])} boundaries")
        
        return data
    
    @staticmethod
    def serialize_device(device):
        """Convert a device to a serializable dictionary."""
        pos = device.scenePos()
        
        # Create a deep copy of properties with QColor conversion
        serialized_properties = CanvasSerializer._process_properties(device.properties)
        
        device_data = {
            'id': device.id,
            'name': device.name,
            'device_type': device.device_type,
            'properties': serialized_properties,
            'position': {'x': pos.x(), 'y': pos.y()}
        }
        
        # Include display properties if they exist
        if hasattr(device, 'display_properties') and device.display_properties:
            device_data['display_properties'] = device.display_properties.copy()
        
        # Include custom icon path if it exists
        if hasattr(device, 'custom_icon_path') and device.custom_icon_path:
            device_data['custom_icon_path'] = device.custom_icon_path
        
        return device_data
    
    @staticmethod
    def _process_properties(props):
        """Process properties dictionary to make it JSON serializable."""
        if props is None:
            return {}
            
        result = {}
        try:
            for key, value in props.items():
                try:
                    # Handle QColor objects
                    if isinstance(value, QColor):
                        result[key] = CanvasSerializer._serialize_color(value)
                    # Handle lists/arrays
                    elif isinstance(value, list):
                        result[key] = [CanvasSerializer._process_value(item) for item in value]
                    # Handle dictionaries (recursive)
                    elif isinstance(value, dict):
                        result[key] = CanvasSerializer._process_properties(value)
                    else:
                        # Try to serialize the value or convert to string if needed
                        result[key] = CanvasSerializer._process_value(value)
                except Exception as e:
                    # If any property fails to serialize, use a string representation or default value
                    import traceback
                    print(f"Warning: Failed to serialize property '{key}', using string representation: {str(e)}")
                    result[key] = str(value) if value is not None else ""
        except Exception as e:
            import traceback
            print(f"Error processing properties: {str(e)}")
            traceback.print_exc()
            # Return whatever we've processed so far
        
        return result
    
    @staticmethod
    def _process_value(value):
        """Process a single value to make it JSON serializable."""
        try:
            if isinstance(value, QColor):
                return CanvasSerializer._serialize_color(value)
            elif hasattr(value, 'toDict') and callable(value.toDict):
                return value.toDict()
            # Handle enum types
            elif hasattr(value, '__module__') and 'enum' in value.__module__.lower():
                # It's likely an enum, try to get the name first
                if hasattr(value, 'name'):
                    return value.name
                # Then try value
                elif hasattr(value, 'value'):
                    return value.value
                # Fall back to string representation
                else:
                    return str(value)
            elif hasattr(value, '__dict__'):
                # Custom object, convert to dict
                return {k: CanvasSerializer._process_value(v) for k, v in value.__dict__.items() 
                        if not k.startswith('_')}  # Skip private attributes
            else:
                # Return as is, and let JSON serialization handle it
                return value
        except Exception as e:
            # If we can't process the value, just return a string representation
            print(f"Warning: Failed to process value {type(value)}, using string representation: {str(e)}")
            return str(value) if value is not None else ""
    
    @staticmethod
    def _serialize_color(color):
        """Convert QColor to serializable format."""
        if not color or not isinstance(color, QColor):
            return {'r': 0, 'g': 0, 'b': 0, 'a': 255}
            
        return {
            'r': color.red(),
            'g': color.green(),
            'b': color.blue(),
            'a': color.alpha()
        }
    
    @staticmethod
    def serialize_connection(connection):
        """Convert a connection to a serializable dictionary."""
        connection_data = {
            'id': connection.id,
            'source_device_id': connection.source_device.id,
            'target_device_id': connection.target_device.id,
            'label_text': connection.label_text if hasattr(connection, 'label_text') else '',
        }
        
        # Convert connection_type enum to serializable format
        if hasattr(connection, 'connection_type'):
            # Handle different possible types of connection type
            if hasattr(connection.connection_type, 'name'):
                # It's an enum, use the name
                connection_data['connection_type'] = connection.connection_type.name
            elif hasattr(connection.connection_type, 'value'):
                # Another type of enum with value
                connection_data['connection_type'] = connection.connection_type.value
            else:
                # Try to convert to string as fallback
                connection_data['connection_type'] = str(connection.connection_type)
        else:
            connection_data['connection_type'] = "ETHERNET"  # Default type
        
        # Convert routing_style enum to serializable format
        if hasattr(connection, 'routing_style'):
            # Handle different possible types of routing style
            if hasattr(connection.routing_style, 'name'):
                # It's an enum, use the name
                connection_data['routing_style'] = connection.routing_style.name
            elif hasattr(connection.routing_style, 'value'):
                # Another type of enum with value
                connection_data['routing_style'] = connection.routing_style.value
            else:
                # Try to convert to string as fallback
                connection_data['routing_style'] = str(connection.routing_style)
        else:
            connection_data['routing_style'] = None
        
        # Add line style properties safely
        if hasattr(connection, 'renderer'):
            connection_data['line_width'] = connection.renderer.line_width
            connection_data['line_style'] = int(connection.renderer.line_style)  # Convert Qt.PenStyle to int
            connection_data['line_color'] = CanvasSerializer._serialize_color(connection.renderer.base_color)
        else:
            # Fallback default values
            connection_data['line_width'] = 1
            connection_data['line_style'] = 1  # Qt.SolidLine
            connection_data['line_color'] = CanvasSerializer._serialize_color(QColor(0, 0, 0))
        
        # Add properties from the properties dictionary if it exists
        if hasattr(connection, 'properties') and connection.properties:
            # Add bandwidth and latency from properties dictionary
            connection_data['bandwidth'] = connection.properties.get('Bandwidth', '')
            connection_data['latency'] = connection.properties.get('Latency', '')
            
            # Add all other properties
            connection_data['properties'] = CanvasSerializer._process_properties(connection.properties)
        else:
            # Set empty values for backward compatibility
            connection_data['bandwidth'] = ''
            connection_data['latency'] = ''
            connection_data['properties'] = {}
            
        return connection_data
    
    @staticmethod
    def serialize_boundary(boundary):
        """Convert a boundary to a serializable dictionary."""
        rect = boundary.rect()
        
        return {
            'name': boundary.name,
            'rect': {
                'x': rect.x(),
                'y': rect.y(),
                'width': rect.width(),
                'height': rect.height()
            },
            'color': CanvasSerializer._serialize_color(boundary.color)
        }
    
    @staticmethod
    def deserialize_canvas(data, canvas):
        """Restore canvas state from serialized data."""
        # Debug print for input data
        print(f"\nDeserializing canvas data with {len(data.get('boundaries', []))} boundaries")
        
        # Clear existing elements
        CanvasSerializer._clear_canvas(canvas)
        
        # Debug print after clearing
        print(f"After clearing, canvas has {len(getattr(canvas, 'boundaries', []))} boundaries")
        
        # Create device lookup for connection references
        device_lookup = {}
        
        # Restore devices first
        for device_data in data.get('devices', []):
            device = CanvasSerializer.deserialize_device(device_data, canvas)
            if device:
                device_lookup[device_data['id']] = device
        
        # Restore boundaries
        boundary_count = len(data.get('boundaries', []))
        print(f"Deserializing {boundary_count} boundaries")
        for i, boundary_data in enumerate(data.get('boundaries', [])):
            print(f"  Deserializing boundary {i+1}: {boundary_data.get('name')}")
            boundary = CanvasSerializer.deserialize_boundary(boundary_data, canvas)
            if boundary:
                print(f"  Successfully created boundary: {boundary.name}")
            else:
                print(f"  Failed to create boundary from data: {boundary_data}")
        
        # Debug print after boundaries
        print(f"After deserializing boundaries, canvas has {len(getattr(canvas, 'boundaries', []))} boundaries")
        
        # Restore connections last (they need device references)
        for connection_data in data.get('connections', []):
            CanvasSerializer.deserialize_connection(connection_data, canvas, device_lookup)
        
        # Update the view to show all items
        canvas.viewport().update()
        
        # Final debug print
        print(f"Final canvas state: {len(canvas.devices)} devices, {len(getattr(canvas, 'connections', []))} connections, {len(getattr(canvas, 'boundaries', []))} boundaries")
    
    @staticmethod
    def _clear_canvas(canvas):
        """Remove all items from the canvas."""
        # Debug print before clearing
        print(f"Clearing canvas with {len(canvas.devices)} devices, {len(getattr(canvas, 'connections', []))} connections, {len(getattr(canvas, 'boundaries', []))} boundaries")
        
        # Remove all devices
        for device in list(canvas.devices):
            canvas.scene().removeItem(device)
        canvas.devices.clear()
        
        # Remove all connections
        if hasattr(canvas, 'connections'):
            for connection in list(canvas.connections):
                canvas.scene().removeItem(connection)
            canvas.connections.clear()
        
        # Remove all boundaries
        if hasattr(canvas, 'boundaries'):
            for boundary in list(canvas.boundaries):
                canvas.scene().removeItem(boundary)
            canvas.boundaries.clear()
        
        # Debug print after clearing
        print(f"After clearing: devices={len(canvas.devices)}, connections={len(getattr(canvas, 'connections', []))}, boundaries={len(getattr(canvas, 'boundaries', []))}")
    
    @staticmethod
    def deserialize_device(data, canvas):
        """Create a device from serialized data."""
        from models.device import Device
        
        try:
            # Convert serialized color properties back to QColor objects
            properties = data.get('properties', {})
            converted_properties = CanvasSerializer._convert_color_properties(properties)
            
            # Get the custom icon path if present
            custom_icon_path = data.get('custom_icon_path')
            
            # Verify the custom icon path exists
            if custom_icon_path and not os.path.exists(custom_icon_path):
                print(f"Warning: Custom icon not found at {custom_icon_path}")
                custom_icon_path = None
            
            # Create device with serialized properties
            device = Device(
                data['name'],
                data['device_type'],
                converted_properties,
                custom_icon_path
            )
            
            # Explicitly force icon loading if we have a custom path
            if custom_icon_path:
                device._try_load_icon()
            
            # Set ID if present
            if 'id' in data:
                device.id = data['id']
            
            # Restore display properties if present
            if 'display_properties' in data:
                device.display_properties = data['display_properties'].copy()
                device.update_property_labels()
            
            # Position the device
            pos = data.get('position', {'x': 0, 'y': 0})
            device.setPos(QPointF(pos['x'], pos['y']))
            
            # Add to scene
            canvas.scene().addItem(device)
            canvas.devices.append(device)
            
            return device
            
        except Exception as e:
            import traceback
            print(f"Error deserializing device: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def _convert_color_properties(props):
        """Convert serialized color objects back to QColor."""
        if props is None:
            return {}
            
        result = {}
        for key, value in props.items():
            if isinstance(value, dict) and all(k in value for k in ['r', 'g', 'b']):
                # This looks like a serialized color
                result[key] = QColor(
                    value.get('r', 0),
                    value.get('g', 0),
                    value.get('b', 0),
                    value.get('a', 255)
                )
            elif isinstance(value, dict):
                # Recursive for nested dictionaries
                result[key] = CanvasSerializer._convert_color_properties(value)
            elif isinstance(value, list):
                # Process lists
                result[key] = [
                    CanvasSerializer._convert_color_value(item) for item in value
                ]
            else:
                result[key] = value
                
        return result
    
    @staticmethod
    def _convert_color_value(value):
        """Convert a single value from serialized format to proper object if needed."""
        if isinstance(value, dict):
            if all(k in value for k in ['r', 'g', 'b']):
                return QColor(
                    value.get('r', 0),
                    value.get('g', 0),
                    value.get('b', 0),
                    value.get('a', 255)
                )
            return CanvasSerializer._convert_color_properties(value)
        return value
    
    @staticmethod
    def deserialize_connection(data, canvas, device_lookup):
        """Create a connection from serialized data."""
        from models.connection import Connection, ConnectionTypes, RoutingStyle
        from PyQt5.QtCore import Qt
        
        try:
            # Get source and target devices
            source_device_id = data.get('source_device_id')
            target_device_id = data.get('target_device_id')
            
            if not source_device_id or not target_device_id:
                print("Missing source or target device ID")
                return None
            
            source_device = device_lookup.get(source_device_id)
            target_device = device_lookup.get(target_device_id)
            
            if not source_device or not target_device:
                print("Could not find source or target device")
                return None
            
            # Create connection
            connection_type_str = data.get('connection_type')
            routing_style_str = data.get('routing_style')
            
            # Convert connection type string to enum
            connection_type = None
            if connection_type_str:
                # Try to convert string to ConnectionTypes enum
                try:
                    if hasattr(ConnectionTypes, 'from_string'):
                        connection_type = ConnectionTypes.from_string(connection_type_str)
                    elif hasattr(ConnectionTypes, connection_type_str):
                        connection_type = getattr(ConnectionTypes, connection_type_str)
                    else:
                        # Default to ETHERNET if we can't convert
                        connection_type = ConnectionTypes.ETHERNET
                except Exception as e:
                    print(f"Error converting connection type '{connection_type_str}': {e}")
                    connection_type = ConnectionTypes.ETHERNET
            
            # Convert routing style string to enum
            routing_style = None
            if routing_style_str:
                # Try to convert string to RoutingStyle enum
                try:
                    if hasattr(RoutingStyle, 'from_string'):
                        routing_style = RoutingStyle.from_string(routing_style_str)
                    elif hasattr(RoutingStyle, routing_style_str):
                        routing_style = getattr(RoutingStyle, routing_style_str)
                    else:
                        # Default to ORTHOGONAL if we can't convert
                        routing_style = RoutingStyle.ORTHOGONAL
                except Exception as e:
                    print(f"Error converting routing style '{routing_style_str}': {e}")
                    routing_style = RoutingStyle.ORTHOGONAL
            
            # Prepare properties dictionary
            props = {}
            if 'properties' in data and data['properties']:
                props.update(data['properties'])
            
            # Add backward compatibility for bandwidth and latency
            if 'bandwidth' in data and data['bandwidth']:
                props['Bandwidth'] = data['bandwidth']
            if 'latency' in data and data['latency']:
                props['Latency'] = data['latency']
            
            # Add label text to properties
            label_text = data.get('label_text', '')
            if label_text:
                props['label_text'] = label_text
            
            # Create the connection with properties
            connection = Connection(source_device, target_device, connection_type, routing_style, props)
            
            # Set ID if present
            if 'id' in data:
                connection.id = data['id']
            
            # Ensure label text is set
            if hasattr(connection, 'label_manager') and connection.label_manager:
                connection.label_manager.label_text = label_text
            
            # Set line style properties safely
            if hasattr(connection, 'renderer') and connection.renderer:
                # Set line width
                if 'line_width' in data:
                    connection.renderer.line_width = data['line_width']
                
                # Set line color
                if 'line_color' in data and isinstance(data['line_color'], dict):
                    color_data = data['line_color']
                    color = QColor(
                        color_data.get('r', 0),
                        color_data.get('g', 0),
                        color_data.get('b', 0),
                        color_data.get('a', 255)
                    )
                    connection.renderer.base_color = color
                
                # Set line style
                if 'line_style' in data:
                    connection.renderer.line_style = data['line_style']
                
                # Apply the style
                connection.renderer.apply_style()
                
            # Add to scene
            canvas.scene().addItem(connection)
            if not hasattr(canvas, 'connections'):
                canvas.connections = []
            canvas.connections.append(connection)
            
            # Force update the path
            if hasattr(connection, 'update_path'):
                connection.update_path()
            
            return connection
            
        except Exception as e:
            import traceback
            print(f"Error deserializing connection: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def deserialize_boundary(data, canvas):
        """Create a boundary from serialized data."""
        from models.boundary import Boundary
        
        try:
            # Debug print for input data
            print(f"  Deserializing boundary: {data}")
            
            # Extract boundary data
            name = data.get('name', 'Boundary')
            
            # Create rectangle
            rect_data = data.get('rect', {'x': 0, 'y': 0, 'width': 100, 'height': 100})
            rect = QRectF(
                rect_data.get('x', 0),
                rect_data.get('y', 0),
                rect_data.get('width', 100),
                rect_data.get('height', 100)
            )
            
            # Create color
            color_data = data.get('color', {'r': 40, 'g': 120, 'b': 200, 'a': 80})
            color = QColor(
                color_data.get('r', 40),
                color_data.get('g', 120),
                color_data.get('b', 200),
                color_data.get('a', 80)
            )
            
            # Get theme_manager from canvas
            theme_manager = None
            if hasattr(canvas, 'theme_manager'):
                theme_manager = canvas.theme_manager
            # If not available directly, try to get from parent window
            elif hasattr(canvas, 'parent') and callable(canvas.parent):
                parent = canvas.parent()
                if parent and hasattr(parent, 'theme_manager'):
                    theme_manager = parent.theme_manager
            
            print(f"  Using theme_manager: {theme_manager}")
            
            # Create boundary with theme manager
            boundary = Boundary(rect, name, color, theme_manager=theme_manager)
            
            # Add to scene
            canvas.scene().addItem(boundary)
            
            # Add to boundaries list
            if not hasattr(canvas, 'boundaries'):
                print("  ERROR: Canvas has no 'boundaries' attribute, creating it now")
                canvas.boundaries = []
            canvas.boundaries.append(boundary)
            
            # Debug confirmation
            print(f"  Added boundary to canvas, now has {len(canvas.boundaries)} boundaries")
            
            return boundary
            
        except Exception as e:
            import traceback
            print(f"Error deserializing boundary: {e}")
            traceback.print_exc()
            return None
