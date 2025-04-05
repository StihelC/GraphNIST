import os
import json
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtCore import QSettings

class RecentFiles:
    """Manages a list of recently opened files."""
    
    MAX_RECENT_FILES = 10  # Maximum number of files to remember
    
    def __init__(self, parent=None):
        """Initialize with the parent widget that will receive signals."""
        self.parent = parent
        self.settings = QSettings("GraphNIST", "GraphNIST")
        self.recent_files = self._load_recent_files()
        self.recent_file_actions = []
    
    def _load_recent_files(self):
        """Load the list of recent files from settings."""
        try:
            recent_files = self.settings.value("recentFiles", [])
            # Convert to list if it's not already (happens with some QSettings implementations)
            if not isinstance(recent_files, list):
                recent_files = []
            # Filter out files that no longer exist
            return [f for f in recent_files if os.path.exists(f)]
        except Exception as e:
            print(f"Error loading recent files: {e}")
            return []
    
    def _save_recent_files(self):
        """Save the list of recent files to settings."""
        try:
            self.settings.setValue("recentFiles", self.recent_files)
            self.settings.sync()
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def add_file(self, filepath):
        """Add a file to the recent files list."""
        if not filepath or not os.path.exists(filepath):
            return
        
        # Remove if it already exists to avoid duplicates
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        
        # Add to the beginning of the list
        self.recent_files.insert(0, filepath)
        
        # Trim list to maximum size
        if len(self.recent_files) > self.MAX_RECENT_FILES:
            self.recent_files = self.recent_files[:self.MAX_RECENT_FILES]
        
        # Save the updated list
        self._save_recent_files()
        
        # Update the actions if they exist
        if self.recent_file_actions:
            self.update_actions()
    
    def clear_recent_files(self):
        """Clear the list of recent files."""
        self.recent_files = []
        self._save_recent_files()
        self.update_actions()
    
    def get_recent_files(self):
        """Get the list of recent files."""
        return self.recent_files
    
    def setup_menu(self, menu, file_selected_callback):
        """Set up the Recent Files submenu with actions.
        
        Args:
            menu: QMenu to add actions to
            file_selected_callback: Function to call when a file is selected
        """
        self.file_selected_callback = file_selected_callback
        self.recent_file_actions = []
        
        # Create actions for recent files
        for i in range(self.MAX_RECENT_FILES):
            action = QAction(self.parent)
            action.setVisible(False)
            action.triggered.connect(self._create_callback(i))
            self.recent_file_actions.append(action)
            menu.addAction(action)
        
        # Add separator and clear action
        menu.addSeparator()
        self.clear_action = QAction("Clear Recent Files", self.parent)
        self.clear_action.triggered.connect(self.clear_recent_files)
        menu.addAction(self.clear_action)
        
        # Update the actions to show current files
        self.update_actions()
    
    def _create_callback(self, index):
        """Create a callback function for a specific index in the recent files list."""
        def callback():
            if index < len(self.recent_files):
                filepath = self.recent_files[index]
                if os.path.exists(filepath):
                    self.file_selected_callback(filepath)
                else:
                    # Remove file from list if it no longer exists
                    self.recent_files.pop(index)
                    self._save_recent_files()
                    self.update_actions()
        return callback
    
    def update_actions(self):
        """Update the recent file actions to reflect current list."""
        # Update actions visibility and text
        for i, action in enumerate(self.recent_file_actions):
            if i < len(self.recent_files):
                filepath = self.recent_files[i]
                filename = os.path.basename(filepath)
                # Show the file index (1-based) for keyboard navigation
                action.setText(f"&{i+1}. {filename}")
                action.setData(filepath)
                action.setVisible(True)
                # Set full path as tooltip
                action.setToolTip(filepath)
            else:
                action.setVisible(False)
        
        # Update clear action visibility
        if hasattr(self, 'clear_action'):
            self.clear_action.setEnabled(len(self.recent_files) > 0) 