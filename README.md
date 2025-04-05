# GraphNIST

## Overview

GraphNIST is a sophisticated network infrastructure simulation tool that provides a visual canvas for designing, documenting, and analyzing network topologies. Built with PyQt5, it offers an intuitive interface for network engineers, architects, and educators to create detailed network diagrams with functional properties. The application follows a Model-View-Controller (MVC) architecture for maintainability and extensibility.

## Key Features

### Core Functionality
- **Interactive Canvas**: Drag-and-drop interface for creating network diagrams
- **Multi-layered Visualization**: Boundaries (layer 0), connections (layer 5), and devices (layer 10)
- **Device Management**: Add, configure, move, and delete various network devices
- **Connection Management**: Create links between devices with multiple routing styles
- **Boundary Management**: Group related devices into logical boundaries
- **Dark Mode Support**: Complete application-wide theme switching

### Advanced Features
- **Advanced Topology Layouts**:
  - Force-directed layout for optimal device positioning
  - Hierarchical layout for structured networks
  - Radial layout for hub-and-spoke designs
  - Grid layout for regular arrangements
- **Multiple Connection Strategies**:
  - Mesh network (all-to-all connections)
  - Chain connection (sequential linking)
  - Closest device connection (each connects to nearest neighbor)
  - Closest device of specific type connection
- **Property Management**:
  - Customizable device and connection properties
  - Visual property display under devices
  - Property label movement during device repositioning
- **Advanced UI**:
  - Undo/redo support for all operations
  - Recent files tracking
  - Comprehensive right-click context menus
  - Detailed property panels

## Architecture

GraphNIST is built using a Model-View-Controller (MVC) architecture to maintain separation of concerns:

### Models
The data structures that represent the network components:
- **Device**: Network devices (routers, switches, firewalls, etc.)
- **Connection**: Links between devices with properties like bandwidth, latency
- **Boundary**: Logical groupings of devices
- **ConnectionRenderer**: Handles visual appearance of connections
- **ConnectionTypes/RoutingStyle**: Enums for connection types and routing styles

### Views
The user interface components:
- **Canvas**: The main workspace where topology is displayed and manipulated
- **MainWindow**: Application frame with menus, toolbars, and status bar
- **PropertyPanel**: Dynamic panel for editing object properties
- **Dialogs**: Various configuration dialogs for devices and connections

### Controllers
Manage interactions between models and views:
- **DeviceController**: Handles device creation, deletion, and modification
- **ConnectionController**: Manages connections between devices
- **BoundaryController**: Controls boundary creation and manipulation
- **PropertiesController**: Updates property displays and handles property changes
- **UndoRedoManager**: Tracks operations for undo/redo functionality
- **ThemeManager**: Manages application-wide dark/light theme switching

## Component Relationships

```
┌─────────────────────┐     ┌────────────────────┐     ┌─────────────────────┐
│      Models         │     │     Controllers    │     │       Views         │
│                     │     │                    │     │                     │
│  ┌───────────────┐  │     │ ┌────────────────┐ │     │ ┌─────────────────┐ │
│  │    Device     │◄─┼─────┼─┤DeviceController│◄┼─────┼─┤     Canvas      │ │
│  └───────────────┘  │     │ └────────────────┘ │     │ └─────────────────┘ │
│                     │     │                    │     │                     │
│  ┌───────────────┐  │     │ ┌────────────────┐ │     │ ┌─────────────────┐ │
│  │  Connection   │◄─┼─────┼─┤  Connection    │◄┼─────┼─┤   MainWindow    │ │
│  └───────────────┘  │     │ │  Controller    │ │     │ └─────────────────┘ │
│                     │     │ └────────────────┘ │     │                     │
│  ┌───────────────┐  │     │ ┌────────────────┐ │     │ ┌─────────────────┐ │
│  │   Boundary    │◄─┼─────┼─┤   Boundary     │◄┼─────┼─┤ Property Panel  │ │
│  └───────────────┘  │     │ │  Controller    │ │     │ └─────────────────┘ │
│                     │     │ └────────────────┘ │     │                     │
└─────────────────────┘     └────────────────────┘     └─────────────────────┘
                                      │
                                      ▼
                            ┌────────────────────┐
                            │   EventBus         │
                            │ (Communication)    │
                            └────────────────────┘
```

## Topology Optimization Algorithms

GraphNIST includes sophisticated algorithms for automatic layout optimization:

### Force-Directed Layout
- Simulates physical forces between devices:
  - Connected devices attract each other
  - All devices repel each other to avoid overlap
  - Gradually reaches equilibrium through iterations
- Best for natural, visually pleasing layouts

### Hierarchical Layout
- Arranges devices in levels based on connectivity
- Identifies "root" devices (typically routers) as starting points
- Creates connections that flow downward through levels
- Ideal for showing network hierarchy

### Radial Layout
- Positions devices in concentric circles around a central node
- Central node is typically the most connected device
- Devices are arranged by distance from the center
- Effective for visualizing hub-and-spoke topologies

### Grid Layout
- Arranges devices in a uniform grid pattern
- Prioritizes device placement by type and connectivity
- Supports dynamic cell sizing to optimize space
- Best for organized, clean diagrams

## Connection Strategies

### Mesh Network
Creates connections between all selected devices, optionally bidirectional

### Chain Connection
Sorts devices by position and connects them sequentially (node 1 → node 2 → node 3...)

### Closest Device Connection
Each device connects to its nearest neighbor based on Euclidean distance

### Closest Device of Specific Type
Each device connects to the nearest device of a specified type (e.g., all workstations connect to nearest switch)

## Layer Management

GraphNIST uses a z-index system to manage the stacking order of elements:
- **Boundaries (Layer 0)**: Always at the bottom as containers
- **Connections (Layer 5)**: In the middle, connecting devices
- **Devices (Layer 10)**: Always on top for easy selection and manipulation

## Routing Styles

Connections between devices can use different routing styles:
- **Straight**: Direct line between devices
- **Orthogonal**: Right-angled paths (horizontal and vertical segments only)
- **Curved**: Quadratic Bezier curves for a more natural flow

## Theme Support

GraphNIST provides comprehensive dark mode support:
- **ThemeManager**: Central manager for application-wide theme changes
- **Theme-aware widgets**: UI components that adapt to theme changes
- **Connection theming**: Different color schemes for connections in light/dark modes
- **Toggle**: Easy switching between light and dark modes via the View menu

## File Management

- **Canvas serialization**: Save and load complete network topologies
- **Recent files**: Track and quickly access recently opened files
- **File validation**: Ensures loaded files are valid and compatible

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/GraphNIST.git
   cd GraphNIST
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python src/main.py
   ```

## Usage Guide

### Creating Devices
1. Select the device type from the toolbar
2. Click on the canvas to place the device
3. Edit properties through the property panel

### Creating Connections
1. Select the "Add Connection" tool
2. Click on the source device, then the destination device
3. Configure connection properties in the panel

### Creating Boundaries
1. Select the "Add Boundary" tool
2. Click and drag to define the boundary area
3. Configure name and color through the property panel

### Optimizing Layouts
1. Select devices to optimize (or select none for all devices)
2. Go to Tools → Optimize Layout
3. Choose the desired algorithm and parameters
4. Click Apply to rearrange the devices

### Using Dark Mode
1. Go to View → Toggle Dark Mode
2. The application will immediately switch themes
3. Your preference is saved for future sessions

## Project Structure

```
GraphNIST/
├── src/                    # Source code
│   ├── main.py             # Application entry point
│   ├── constants.py        # Global constants and enums
│   ├── controllers/        # Controller classes
│   │   ├── device_controller.py
│   │   ├── connection_controller.py
│   │   ├── boundary_controller.py
│   │   ├── properties_controller.py
│   │   ├── commands.py     # Command classes for undo/redo
│   │   └── ...
│   ├── models/             # Data model classes
│   │   ├── device.py
│   │   ├── connection.py
│   │   ├── boundary.py
│   │   ├── connection_renderer.py
│   │   └── ...
│   ├── views/              # UI components
│   │   ├── main_window.py
│   │   ├── canvas.py
│   │   ├── property_panel.py
│   │   └── ...
│   ├── dialogs/            # Dialog windows
│   │   ├── device_dialog.py
│   │   ├── multi_connection_dialog.py
│   │   └── ...
│   ├── utils/              # Utility classes
│   │   ├── theme_manager.py
│   │   ├── event_bus.py
│   │   ├── recent_files.py
│   │   └── ...
│   └── resources/          # Application resources
│       ├── icons/
│       └── styles/
├── requirements.txt        # Project dependencies
└── README.md               # This documentation
```

## Development Guidelines

### Adding a New Device Type
1. Add the type to `DeviceTypes` in `constants.py`
2. Add appropriate icons in the resources directory
3. Update the `device.py` model with type-specific properties
4. Extend the device toolbar in `main_window.py` if necessary

### Adding a New Connection Type
1. Add the type to `ConnectionTypes` in `constants.py`
2. Extend the `ConnectionRenderer` class to handle the new type
3. Update the connection type selection UI

### Creating a New Layout Algorithm
1. Add a new method in `ConnectionController` following the pattern of existing algorithms
2. Update the layout dialog to include the new algorithm
3. Implement the algorithm logic using the device and connection APIs

## Contributing

Contributions to GraphNIST are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Add your changes with appropriate tests
4. Submit a pull request with a clear description of the changes

## License

GraphNIST is open-source software licensed under the MIT license.
