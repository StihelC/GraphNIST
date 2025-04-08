from PyQt5.QtCore import QPointF
import math

def align_left(canvas):
    """Align selected devices to the leftmost edge."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for alignment")
        return
    
    # Find minimum x coordinate
    min_x = min(device.scenePos().x() for device in selected_devices)
    
    # Debug output
    print(f"Aligning {len(selected_devices)} devices to left position: {min_x}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Store which devices are selected
    selection_states = {device: device.isSelected() for device in selected_devices}
    
    # Temporarily unselect all devices to bypass the multi-selection position change blocking
    for device in selected_devices:
        if device.isSelected():
            device.setSelected(False)
    
    # Update positions
    for device in selected_devices:
        original_positions[device] = device.scenePos()
        current_x = device.scenePos().x()
        
        if current_x != min_x:
            new_pos = QPointF(min_x, device.scenePos().y())
            new_positions[device] = new_pos
            
            # Force update connections before move
            if hasattr(device, 'update_connections'):
                device.update_connections()
                
            # Set position with explicit update
            device.setPos(new_pos)
            
            # Force update after positioning
            if hasattr(device, 'update_connections'):
                device.update_connections()
            device.update()
            
            print(f"Moving device {device.name if hasattr(device, 'name') else 'unnamed'} from x={current_x} to x={min_x}")
    
    # Restore selection state
    for device, was_selected in selection_states.items():
        device.setSelected(was_selected)
    
    # Force a more aggressive update of the canvas
    if hasattr(canvas, 'scene'):
        canvas.scene().update()
    canvas.viewport().update()
    canvas.update()
    
    # Force update of all items
    for item in canvas.scene().items():
        item.update()
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Align Left", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Left aligned {len(selected_devices)} devices to position {min_x}")

def _bypass_multi_selection(canvas, devices, operation_func):
    """
    Helper function to bypass multi-selection position change blocking.
    
    Args:
        canvas: The canvas containing the devices
        devices: List of devices to operate on
        operation_func: Function that performs the actual positioning operation
            This function will be called with the devices as its argument
            
    Returns:
        The result of operation_func if any
    """
    # Store which devices are selected
    selection_states = {device: device.isSelected() for device in devices}
    
    # Temporarily unselect all devices to bypass the multi-selection position change blocking
    for device in devices:
        if device.isSelected():
            device.setSelected(False)
    
    try:
        # Perform the operation with selection disabled
        result = operation_func(devices)
        
        # Force a more aggressive update of the canvas
        if hasattr(canvas, 'scene'):
            canvas.scene().update()
        canvas.viewport().update()
        canvas.update()
        
        # Force update of all items
        for item in canvas.scene().items():
            item.update()
            
        return result
    finally:
        # Always restore selection state, even if an error occurs
        for device, was_selected in selection_states.items():
            device.setSelected(was_selected)

def align_right(canvas):
    """Align selected devices to the rightmost edge."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for alignment")
        return
    
    # Find the rightmost edge considering device width
    max_x = max(device.scenePos().x() + device.boundingRect().width() for device in selected_devices)
    
    # Debug output
    print(f"Aligning {len(selected_devices)} devices to right position: {max_x}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        for device in devices:
            original_positions[device] = device.scenePos()
            right_edge = device.scenePos().x() + device.boundingRect().width()
            if right_edge != max_x:
                new_x = max_x - device.boundingRect().width()
                new_pos = QPointF(new_x, device.scenePos().y())
                new_positions[device] = new_pos
                
                # Force update connections before move
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                    
                # Set position with explicit update
                device.setPos(new_pos)
                
                # Force update after positioning
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                device.update()
                
                print(f"Moving device {device.name if hasattr(device, 'name') else 'unnamed'} from right edge {right_edge} to {max_x}")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Align Right", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Right aligned {len(selected_devices)} devices to position {max_x}")

def align_top(canvas):
    """Align selected devices to the topmost edge."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for alignment")
        return
    
    # Find minimum y coordinate
    min_y = min(device.scenePos().y() for device in selected_devices)
    
    # Debug output
    print(f"Aligning {len(selected_devices)} devices to top position: {min_y}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        for device in devices:
            original_positions[device] = device.scenePos()
            current_y = device.scenePos().y()
            
            if current_y != min_y:
                new_pos = QPointF(device.scenePos().x(), min_y)
                new_positions[device] = new_pos
                
                # Force update connections before move
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                    
                # Set position with explicit update
                device.setPos(new_pos)
                
                # Force update after positioning
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                device.update()
                
                print(f"Moving device {device.name if hasattr(device, 'name') else 'unnamed'} from y={current_y} to y={min_y}")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Align Top", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Top aligned {len(selected_devices)} devices to position {min_y}")

def align_bottom(canvas):
    """Align selected devices to the bottommost edge."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for alignment")
        return
    
    # Find the bottommost edge considering device height
    max_y = max(device.scenePos().y() + device.boundingRect().height() for device in selected_devices)
    
    # Debug output
    print(f"Aligning {len(selected_devices)} devices to bottom position: {max_y}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        for device in devices:
            original_positions[device] = device.scenePos()
            bottom_edge = device.scenePos().y() + device.boundingRect().height()
            
            if bottom_edge != max_y:
                new_y = max_y - device.boundingRect().height()
                new_pos = QPointF(device.scenePos().x(), new_y)
                new_positions[device] = new_pos
                
                # Force update connections before move
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                    
                # Set position with explicit update
                device.setPos(new_pos)
                
                # Force update after positioning
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                device.update()
                
                print(f"Moving device {device.name if hasattr(device, 'name') else 'unnamed'} from bottom edge {bottom_edge} to {max_y}")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Align Bottom", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Bottom aligned {len(selected_devices)} devices to position {max_y}")

def align_center_horizontal(canvas):
    """Align devices to the horizontal center of the selection."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for alignment")
        return
    
    # Calculate the center y-coordinate
    total_y = 0
    for device in selected_devices:
        total_y += device.scenePos().y() + (device.boundingRect().height() / 2)
    
    center_y = total_y / len(selected_devices)
    
    # Debug output
    print(f"Aligning {len(selected_devices)} devices to horizontal center: {center_y}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        for device in devices:
            original_positions[device] = device.scenePos()
            current_center_y = device.scenePos().y() + (device.boundingRect().height() / 2)
            
            if current_center_y != center_y:
                new_y = center_y - (device.boundingRect().height() / 2)
                new_pos = QPointF(device.scenePos().x(), new_y)
                new_positions[device] = new_pos
                
                # Force update connections before move
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                    
                # Set position with explicit update
                device.setPos(new_pos)
                
                # Force update after positioning
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                device.update()
                
                print(f"Moving device {device.name if hasattr(device, 'name') else 'unnamed'} from center y={current_center_y} to y={center_y}")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Center Horizontally", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Horizontally centered {len(selected_devices)} devices")

def align_center_vertical(canvas):
    """Align devices to the vertical center of the selection."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for alignment")
        return
    
    # Calculate the center x-coordinate
    total_x = 0
    for device in selected_devices:
        total_x += device.scenePos().x() + (device.boundingRect().width() / 2)
    
    center_x = total_x / len(selected_devices)
    
    # Debug output
    print(f"Aligning {len(selected_devices)} devices to vertical center: {center_x}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        for device in devices:
            original_positions[device] = device.scenePos()
            current_center_x = device.scenePos().x() + (device.boundingRect().width() / 2)
            
            if current_center_x != center_x:
                new_x = center_x - (device.boundingRect().width() / 2)
                new_pos = QPointF(new_x, device.scenePos().y())
                new_positions[device] = new_pos
                
                # Force update connections before move
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                    
                # Set position with explicit update
                device.setPos(new_pos)
                
                # Force update after positioning
                if hasattr(device, 'update_connections'):
                    device.update_connections()
                device.update()
                
                print(f"Moving device {device.name if hasattr(device, 'name') else 'unnamed'} from center x={current_center_x} to x={center_x}")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Center Vertically", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Vertically centered {len(selected_devices)} devices")

def distribute_horizontally(canvas):
    """Distribute devices evenly in a horizontal line with spacing based on connection labels."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for distribution")
        return
    
    # Sort devices by x position
    sorted_devices = sorted(selected_devices, key=lambda d: d.scenePos().x())
    
    # Find leftmost and rightmost device
    leftmost_device = sorted_devices[0]
    rightmost_device = sorted_devices[-1]
    leftmost_x = leftmost_device.scenePos().x()
    
    # Calculate appropriate spacing
    # Get average label width for connections between devices
    label_widths = []
    for device in canvas.devices:
        if hasattr(device, 'connections'):
            for conn in device.connections:
                if hasattr(conn, 'label') and conn.label:
                    # Get the bounding rect of the label text
                    if hasattr(conn.label, 'boundingRect'):
                        label_widths.append(conn.label.boundingRect().width())
    
    # Use average label width or default if no labels
    avg_label_width = 100  # Default minimum spacing
    if label_widths:
        avg_label_width = max(100, sum(label_widths) / len(label_widths) + 50)  # Add 50px buffer for visibility
    
    # Calculate spacing between devices based on their widths and label sizes
    spacing = avg_label_width * 1.5  # Add extra space for visibility of connection lines
    
    # Debug output
    print(f"Distributing {len(selected_devices)} devices horizontally with spacing of {spacing}px")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        # Sort again to ensure order is correct
        sorted_devs = sorted(devices, key=lambda d: d.scenePos().x())
        
        # Keep the leftmost device in place, space others evenly
        for i, device in enumerate(sorted_devs):
            original_positions[device] = device.scenePos()
            
            # Calculate new position
            new_x = leftmost_x + (i * (spacing + device.boundingRect().width()))
            new_pos = QPointF(new_x, device.scenePos().y())
            new_positions[device] = new_pos
            
            # Force update connections before move
            if hasattr(device, 'update_connections'):
                device.update_connections()
                
            # Set position with explicit update
            device.setPos(new_pos)
            
            # Force update after positioning
            if hasattr(device, 'update_connections'):
                device.update_connections()
            device.update()
            
            print(f"Distributing device {device.name if hasattr(device, 'name') else 'unnamed'} to x={new_x}")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Distribute Horizontally", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Horizontally distributed {len(selected_devices)} devices with spacing based on connection labels")

def distribute_vertically(canvas):
    """Distribute devices evenly in a vertical line with spacing based on connection labels."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for distribution")
        return
    
    # Sort devices by y position
    sorted_devices = sorted(selected_devices, key=lambda d: d.scenePos().y())
    
    # Find topmost device
    topmost_device = sorted_devices[0]
    topmost_y = topmost_device.scenePos().y()
    
    # Calculate appropriate spacing
    # Get average label width for connections between devices
    label_heights = []
    for device in canvas.devices:
        if hasattr(device, 'connections'):
            for conn in device.connections:
                if hasattr(conn, 'label') and conn.label:
                    # Get the bounding rect of the label text
                    if hasattr(conn.label, 'boundingRect'):
                        label_heights.append(conn.label.boundingRect().height())
    
    # Use average label height or default if no labels
    avg_label_height = 50  # Default minimum spacing
    if label_heights:
        avg_label_height = max(50, sum(label_heights) / len(label_heights) + 30)  # Add 30px buffer for visibility
    
    # Calculate spacing between devices based on their heights and label sizes
    spacing = avg_label_height * 1.5  # Add extra space for visibility of connection lines
    
    # Debug output
    print(f"Distributing {len(selected_devices)} devices vertically with spacing of {spacing}px")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        # Sort again to ensure order is correct
        sorted_devs = sorted(devices, key=lambda d: d.scenePos().y())
        
        # Keep the topmost device in place, space others evenly
        for i, device in enumerate(sorted_devs):
            original_positions[device] = device.scenePos()
            
            # Calculate new position
            new_y = topmost_y + (i * (spacing + device.boundingRect().height()))
            new_pos = QPointF(device.scenePos().x(), new_y)
            new_positions[device] = new_pos
            
            # Force update connections before move
            if hasattr(device, 'update_connections'):
                device.update_connections()
                
            # Set position with explicit update
            device.setPos(new_pos)
            
            # Force update after positioning
            if hasattr(device, 'update_connections'):
                device.update_connections()
            device.update()
            
            print(f"Distributing device {device.name if hasattr(device, 'name') else 'unnamed'} to y={new_y}")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Distribute Vertically", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Vertically distributed {len(selected_devices)} devices with spacing based on connection labels")

def _handle_undo_redo(canvas, action_name, devices, original_positions, new_positions):
    """Helper to add alignment operations to the undo/redo stack if available."""
    # Find main window
    main_window = canvas.window()
    if (hasattr(main_window, 'command_manager') and 
        main_window.command_manager and 
        hasattr(main_window.command_manager, 'undo_redo_manager')):
        
        try:
            # Create the alignment command
            from controllers.commands import AlignDevicesCommand
            # Try creating the command with the correct parameters
            cmd = AlignDevicesCommand(devices, original_positions, new_positions, action_name)
            
            # Push to the undo/redo stack
            main_window.command_manager.undo_redo_manager.push_command(cmd)
            
            # Update status
            main_window.statusBar().showMessage(f"{action_name}: Aligned {len(devices)} devices", 3000)
        except Exception as e:
            # Log error and fallback to simpler message
            print(f"Error creating undo/redo command: {e}")
            canvas.statusMessage.emit(f"{action_name}: Aligned {len(devices)} devices")
    else:
        # Fallback message if undo/redo not available
        canvas.statusMessage.emit(f"{action_name}: Aligned {len(devices)} devices")

# Network layouts
def arrange_grid(canvas):
    """Arrange devices in a grid pattern."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for grid arrangement")
        return
    
    # Calculate grid dimensions
    device_count = len(selected_devices)
    cols = max(2, int(math.sqrt(device_count)))
    rows = (device_count + cols - 1) // cols  # Ceiling division
    
    # Find average device size for spacing
    avg_width = sum(device.boundingRect().width() for device in selected_devices) / device_count
    avg_height = sum(device.boundingRect().height() for device in selected_devices) / device_count
    
    # Calculate spacing
    h_spacing = avg_width * 1.5
    v_spacing = avg_height * 1.5
    
    # Find center of all devices
    center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in selected_devices) / device_count
    center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in selected_devices) / device_count
    
    # Calculate top-left corner of grid
    start_x = center_x - (cols * h_spacing / 2)
    start_y = center_y - (rows * v_spacing / 2)
    
    # Debug output
    print(f"Arranging {len(selected_devices)} devices in a {rows}x{cols} grid, starting at ({start_x}, {start_y})")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        # Position each device
        for i, device in enumerate(devices):
            original_positions[device] = device.scenePos()
            
            row = i // cols
            col = i % cols
            
            new_x = start_x + (col * h_spacing)
            new_y = start_y + (row * v_spacing)
            
            new_positions[device] = QPointF(new_x, new_y)
            
            # Force update connections before move
            if hasattr(device, 'update_connections'):
                device.update_connections()
                
            # Set position with explicit update
            device.setPos(new_x, new_y)
            
            # Force update after positioning
            if hasattr(device, 'update_connections'):
                device.update_connections()
            device.update()
            
            print(f"Arranging device {device.name if hasattr(device, 'name') else 'unnamed'} to grid position ({col}, {row}) at ({new_x}, {new_y})")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Grid Arrangement", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Arranged {len(selected_devices)} devices in a grid pattern")

def arrange_circle(canvas):
    """Arrange devices in a circular pattern."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for circle arrangement")
        return
    
    device_count = len(selected_devices)
    
    # Find center of all devices
    center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in selected_devices) / device_count
    center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in selected_devices) / device_count
    center = QPointF(center_x, center_y)
    
    # Calculate appropriate radius based on device sizes
    avg_size = sum(max(device.boundingRect().width(), device.boundingRect().height()) 
                 for device in selected_devices) / device_count
    radius = max(avg_size * 2, device_count * avg_size / (2 * math.pi))
    
    # Debug output
    print(f"Arranging {len(selected_devices)} devices in a circle around ({center_x}, {center_y}) with radius {radius}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        # Position devices around the circle
        for i, device in enumerate(devices):
            original_positions[device] = device.scenePos()
            
            angle = (2 * math.pi * i) / device_count
            
            # Calculate position offset by device dimensions
            new_x = center.x() + radius * math.cos(angle) - (device.boundingRect().width() / 2)
            new_y = center.y() + radius * math.sin(angle) - (device.boundingRect().height() / 2)
            
            new_positions[device] = QPointF(new_x, new_y)
            
            # Force update connections before move
            if hasattr(device, 'update_connections'):
                device.update_connections()
                
            # Set position with explicit update
            device.setPos(new_x, new_y)
            
            # Force update after positioning
            if hasattr(device, 'update_connections'):
                device.update_connections()
            device.update()
            
            print(f"Arranging device {device.name if hasattr(device, 'name') else 'unnamed'} to circle position at angle {angle:.2f} radians at ({new_x}, {new_y})")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Circle Arrangement", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Arranged {len(selected_devices)} devices in a circle pattern")

def arrange_star(canvas):
    """Arrange devices in a star pattern (one center, others around)."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 3:
        canvas.statusMessage.emit("At least three devices must be selected for star arrangement")
        return
        
    device_count = len(selected_devices)
    
    # Find center of all devices
    center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in selected_devices) / device_count
    center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in selected_devices) / device_count
    center = QPointF(center_x, center_y)
    
    # Calculate appropriate radius
    avg_size = sum(max(device.boundingRect().width(), device.boundingRect().height()) 
                 for device in selected_devices) / device_count
    radius = max(avg_size * 2, (device_count - 1) * avg_size / (2 * math.pi))
    
    # Debug output
    print(f"Arranging {len(selected_devices)} devices in a star pattern around ({center_x}, {center_y}) with radius {radius}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        # First device goes to the center
        center_device = devices[0]
        original_positions[center_device] = center_device.scenePos()
        
        new_center_pos = QPointF(
            center.x() - (center_device.boundingRect().width() / 2),
            center.y() - (center_device.boundingRect().height() / 2)
        )
        new_positions[center_device] = new_center_pos
        
        # Force update connections before move
        if hasattr(center_device, 'update_connections'):
            center_device.update_connections()
            
        # Set position with explicit update
        center_device.setPos(new_center_pos)
        
        # Force update after positioning
        if hasattr(center_device, 'update_connections'):
            center_device.update_connections()
        center_device.update()
        
        print(f"Arranging device {center_device.name if hasattr(center_device, 'name') else 'unnamed'} to center at ({new_center_pos.x()}, {new_center_pos.y()})")
        
        # Remaining devices go around in a circle
        outer_devices = devices[1:]
        for i, device in enumerate(outer_devices):
            original_positions[device] = device.scenePos()
            
            angle = (2 * math.pi * i) / len(outer_devices)
            
            new_x = center.x() + radius * math.cos(angle) - (device.boundingRect().width() / 2)
            new_y = center.y() + radius * math.sin(angle) - (device.boundingRect().height() / 2)
            
            new_pos = QPointF(new_x, new_y)
            new_positions[device] = new_pos
            
            # Force update connections before move
            if hasattr(device, 'update_connections'):
                device.update_connections()
                
            # Set position with explicit update
            device.setPos(new_pos)
            
            # Force update after positioning
            if hasattr(device, 'update_connections'):
                device.update_connections()
            device.update()
            
            print(f"Arranging device {device.name if hasattr(device, 'name') else 'unnamed'} to star point at angle {angle:.2f} radians at ({new_x}, {new_y})")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Star Arrangement", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Arranged {len(selected_devices)} devices in a star pattern")

def arrange_bus(canvas):
    """Arrange devices in a horizontal bus pattern."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if len(selected_devices) < 2:
        canvas.statusMessage.emit("At least two devices must be selected for bus arrangement")
        return
        
    device_count = len(selected_devices)
    
    # Find center of all devices
    center_x = sum(device.scenePos().x() + device.boundingRect().width()/2 for device in selected_devices) / device_count
    center_y = sum(device.scenePos().y() + device.boundingRect().height()/2 for device in selected_devices) / device_count
    
    # Calculate appropriate spacing
    avg_width = sum(device.boundingRect().width() for device in selected_devices) / device_count
    spacing = avg_width * 1.5
    
    # Calculate total width of the bus
    total_width = spacing * (device_count - 1)
    start_x = center_x - (total_width / 2)
    
    # Debug output
    print(f"Arranging {len(selected_devices)} devices in a bus pattern starting at x={start_x}, y={center_y}")
    
    # Save original positions for undo/redo
    original_positions = {}
    new_positions = {}
    
    # Define the operation to perform
    def perform_alignment(devices):
        # Position each device
        for i, device in enumerate(devices):
            original_positions[device] = device.scenePos()
            
            new_x = start_x + (i * spacing) - (device.boundingRect().width() / 2)
            new_pos = QPointF(new_x, center_y - (device.boundingRect().height() / 2))
            
            new_positions[device] = new_pos
            
            # Force update connections before move
            if hasattr(device, 'update_connections'):
                device.update_connections()
                
            # Set position with explicit update
            device.setPos(new_pos)
            
            # Force update after positioning
            if hasattr(device, 'update_connections'):
                device.update_connections()
            device.update()
            
            print(f"Arranging device {device.name if hasattr(device, 'name') else 'unnamed'} to bus position {i} at ({new_x}, {center_y - (device.boundingRect().height() / 2)})")
    
    # Perform the alignment with multi-selection bypass
    _bypass_multi_selection(canvas, selected_devices, perform_alignment)
    
    # Add to undo/redo stack if available
    _handle_undo_redo(canvas, "Bus Arrangement", selected_devices, original_positions, new_positions)
    
    canvas.statusMessage.emit(f"Arranged {len(selected_devices)} devices in a bus pattern")

def test_move(canvas):
    """Test function to directly move selected devices by a fixed amount."""
    selected_devices = [item for item in canvas.scene().selectedItems() 
                      if item in canvas.devices]
    if not selected_devices:
        canvas.statusMessage.emit("No devices selected")
        return
    
    # Store which devices are selected
    selection_states = {device: device.isSelected() for device in selected_devices}
    
    # Temporarily unselect all devices to bypass the multi-selection position change blocking
    for device in selected_devices:
        if device.isSelected():
            device.setSelected(False)
    
    # Move all selected devices 100 pixels to the right - making this more dramatic
    for device in selected_devices:
        current_pos = device.scenePos()
        # Create a new position 100 pixels to the right
        new_pos = QPointF(current_pos.x() + 100, current_pos.y())
        
        # Force update of all connections before and after move
        if hasattr(device, 'update_connections'):
            device.update_connections()
            
        # Set position with explicit update flags
        device.setPos(new_pos)
        
        # Force update after positioning
        if hasattr(device, 'update_connections'):
            device.update_connections()
        device.update()
        
        # Debug output
        print(f"Moved device {device.name if hasattr(device, 'name') else 'unnamed'} from {current_pos} to {new_pos}")
    
    # Restore selection state
    for device, was_selected in selection_states.items():
        device.setSelected(was_selected)
    
    # Force a more aggressive update of the canvas
    if hasattr(canvas, 'scene'):
        canvas.scene().update()
    canvas.viewport().update()
    canvas.update()
    
    # Force update of all items
    for item in canvas.scene().items():
        item.update()
    
    canvas.statusMessage.emit(f"Test: Moved {len(selected_devices)} device(s) 100px right") 