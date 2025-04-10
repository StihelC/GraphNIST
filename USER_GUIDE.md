# GraphNIST User Guide

## Getting Started

### Launching the Application
1. Open a terminal/command prompt
2. Navigate to the GraphNIST directory
3. Run the application:
   ```bash
   python src/main.py
   ```

### Basic Interface Overview
- **Toolbar**: Contains tools for adding devices, connections, and boundaries
- **Canvas**: The main workspace where you create your network diagram
- **Property Panel**: Located on the right side, shows properties of selected items
- **Menu Bar**: Contains file operations, view options, and tools

## Creating Network Diagrams

### Adding Devices
1. Select a device type from the toolbar (e.g., Router, Switch, Firewall)
2. Click on the canvas to place the device
3. Use the property panel to configure:
   - Device name
   - IP address
   - Other relevant properties

### Creating Connections
1. Select the "Add Connection" tool from the toolbar
2. Click on the source device
3. Click on the destination device
4. Configure connection properties:
   - Bandwidth
   - Latency
   - Routing style (Straight, Orthogonal, or Curved)

### Creating Boundaries
1. Select the "Add Boundary" tool
2. Click and drag on the canvas to create a boundary
3. Configure boundary properties:
   - Name
   - Color
   - Description

## Advanced Features

### Layout Optimization
1. Select the devices you want to optimize (or none to optimize all)
2. Go to Tools → Optimize Layout
3. Choose from:
   - Force-directed layout
   - Hierarchical layout
   - Radial layout
   - Grid layout
4. Click Apply to rearrange the devices

### Multiple Device Connections
1. Select multiple devices
2. Right-click and choose "Connect Devices"
3. Select a connection strategy:
   - Mesh network
   - Chain connection
   - Closest device
   - Closest device of specific type

### Theme Customization
1. Go to View → Toggle Dark Mode to switch between light and dark themes
2. Your theme preference will be saved for future sessions

## Tips and Best Practices

### Organization
- Use boundaries to group related devices
- Name devices and connections clearly
- Use different colors for different types of devices
- Keep the diagram clean and well-spaced

### Performance
- For large networks, use the layout optimization tools
- Consider using the grid layout for very large networks
- Use boundaries to hide/show sections of the network

### Troubleshooting
- If a device is not connecting, check if it's inside a boundary
- If the layout looks messy, try different optimization algorithms
- If properties are not updating, try selecting the item again

## Keyboard Shortcuts

- **Ctrl + N**: New diagram
- **Ctrl + O**: Open diagram
- **Ctrl + S**: Save diagram
- **Ctrl + Z**: Undo
- **Ctrl + Y**: Redo
- **Delete**: Remove selected items
- **Ctrl + A**: Select all items
- **Ctrl + D**: Deselect all items

## Saving and Exporting

### Saving Your Work
1. Go to File → Save
2. Choose a location and filename
3. Your diagram will be saved with all properties and layout information

### Opening Saved Diagrams
1. Go to File → Open
2. Select your saved diagram file
3. The diagram will load with all properties and layout preserved

## Support

If you encounter any issues or have questions:
1. Check the README.md file for more information
2. Look for error messages in the application logs
3. Contact the development team through the project's GitHub repository 