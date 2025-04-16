# GraphNIST

## Overview

GraphNIST is a sophisticated network infrastructure simulation tool that provides a visual canvas for designing, documenting, and analyzing network topologies. Built with PyQt5, it offers an intuitive interface for network engineers, architects, and educators to create detailed network diagrams with functional properties. The application follows a Model-View-Controller (MVC) architecture for maintainability and extensibility.

## Key Features

- **Interactive Canvas**: Drag-and-drop interface for creating network diagrams
- **Multi-layered Visualization**: Boundaries (layer 0), connections (layer 7), and devices (layer 10)
- **Device Management**: Add, configure, move, and delete various network devices
- **Connection Management**: Create links between devices with multiple routing styles
- **Boundary Management**: Group related devices into logical boundaries
- **Dark Mode Support**: Complete application-wide theme switching
- **Advanced Topology Layouts**: Force-directed, hierarchical, radial, and grid layouts
- **Multiple Connection Strategies**: Mesh, chain, closest device, and type-specific connections
- **Property Management**: Customizable device and connection properties
- **Undo/Redo Support**: Comprehensive operation history tracking
- **Export Capabilities**: Save diagrams in various formats (PNG, SVG)
- **Custom Device Types**: Create and manage custom device templates
- **Real-time Validation**: Automatic validation of network configurations
- **Keyboard Shortcuts**: Comprehensive keyboard shortcuts for efficient workflow

## Architecture

GraphNIST is built using a Model-View-Controller (MVC) architecture:

### Models
- **Device**: Network devices (routers, switches, firewalls, etc.)
- **Connection**: Links between devices with properties like bandwidth, latency
- **Boundary**: Logical groupings of devices
- **ConnectionRenderer**: Handles visual appearance of connections
- **ThemeManager**: Manages application-wide theme switching
- **UndoRedoManager**: Tracks operations for undo/redo functionality

### Views
- **Canvas**: Main workspace for topology display and manipulation
- **MainWindow**: Application frame with menus, toolbars, and status bar
- **PropertyPanel**: Dynamic panel for editing object properties
- **Dialogs**: Various configuration dialogs
- **ThemeSwitcher**: Interface for theme management

### Controllers
- **DeviceController**: Handles device operations
- **ConnectionController**: Manages connections between devices
- **BoundaryController**: Controls boundary operations
- **PropertiesController**: Manages property updates
- **UndoRedoManager**: Tracks operations for undo/redo
- **ThemeManager**: Manages application-wide theme switching

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)

### Installation Steps

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

### Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run tests:
   ```bash
   pytest
   ```

## Documentation

For detailed usage instructions and tutorials, please refer to the [USER_GUIDE.md](USER_GUIDE.md) file.

## Project Structure

```
GraphNIST/
├── src/                    # Source code
│   ├── main.py             # Application entry point
│   ├── constants.py        # Global constants and enums
│   ├── controllers/        # Controller classes
│   ├── models/             # Data model classes
│   ├── views/              # UI components
│   ├── dialogs/            # Dialog windows
│   ├── utils/              # Utility classes
│   └── tests/              # Test suite
├── resources/              # Application resources
│   ├── icons/             # Icon assets
│   ├── themes/            # Theme definitions
│   └── templates/         # Device templates
├── logs/                   # Application logs
├── docs/                   # Documentation
├── README.md               # Project overview
├── USER_GUIDE.md           # User documentation
├── requirements.txt        # Core dependencies
└── requirements-dev.txt    # Development dependencies
```

## Troubleshooting

### Common Issues

1. **Theme not loading properly**
   - Ensure pyqtdarktheme is installed
   - Check if the theme files are in the correct location

2. **Device icons not displaying**
   - Verify the resources/icons directory exists
   - Check file permissions

3. **Application crashes on startup**
   - Verify all dependencies are installed
   - Check Python version compatibility
   - Review logs in the logs directory

### Getting Help

- Check the [USER_GUIDE.md](USER_GUIDE.md) for detailed documentation
- Open an issue on GitHub for bug reports
- Contact the development team for support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed
- Use meaningful commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt5 team for the excellent GUI framework
- Contributors and maintainers
- Users for their feedback and suggestions
