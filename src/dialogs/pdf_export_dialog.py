from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFileDialog,
                           QLabel, QCheckBox, QPushButton, QComboBox, QMessageBox,
                           QGroupBox, QRadioButton, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPageSize
import os

from utils.pdf_exporter import PDFExporter

class PDFExportDialog(QDialog):
    """Dialog for configuring PDF export options."""
    
    # Map user-friendly page size names to QPageSize values
    PAGE_SIZES = {
        "A4": QPageSize.A4,
        "Letter": QPageSize.Letter,
        "A3": QPageSize.A3,
        "Legal": QPageSize.Legal,
        "Tabloid": QPageSize.Tabloid
    }
    
    def __init__(self, parent=None, canvas=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle("Export to PDF")
        self.setMinimumWidth(450)
        
        # Create layout
        self._create_layout()
        
    def _create_layout(self):
        """Create the dialog layout."""
        layout = QVBoxLayout()
        
        # Page setup group
        page_group = QGroupBox("Page Setup")
        page_layout = QVBoxLayout()
        
        # Page size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Page Size:"))
        
        self.size_combo = QComboBox()
        for name in self.PAGE_SIZES.keys():
            self.size_combo.addItem(name)
        size_layout.addWidget(self.size_combo)
        page_layout.addLayout(size_layout)
        
        # Orientation
        orientation_layout = QHBoxLayout()
        orientation_layout.addWidget(QLabel("Orientation:"))
        
        self.portrait_radio = QRadioButton("Portrait")
        self.landscape_radio = QRadioButton("Landscape")
        self.landscape_radio.setChecked(True)  # Default to landscape
        
        orientation_layout.addWidget(self.portrait_radio)
        orientation_layout.addWidget(self.landscape_radio)
        orientation_layout.addStretch()
        page_layout.addLayout(orientation_layout)
        
        # Margins
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Margin (mm):"))
        
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 50)
        self.margin_spin.setValue(10)
        margin_layout.addWidget(self.margin_spin)
        margin_layout.addStretch()
        page_layout.addLayout(margin_layout)
        
        page_group.setLayout(page_layout)
        layout.addWidget(page_group)
        
        # Content options group
        content_group = QGroupBox("Content Options")
        content_layout = QVBoxLayout()
        
        # Fit to page option
        self.fit_check = QCheckBox("Fit to one page")
        self.fit_check.setChecked(True)
        content_layout.addWidget(self.fit_check)
        
        # Draw border option
        self.border_check = QCheckBox("Draw border around content")
        self.border_check.setChecked(True)  # Default to enabled for better visibility
        content_layout.addWidget(self.border_check)
        
        # Include metadata option
        self.metadata_check = QCheckBox("Include metadata (creation date, application name)")
        self.metadata_check.setChecked(True)
        content_layout.addWidget(self.metadata_check)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.export_button = QPushButton("Export...")
        self.export_button.clicked.connect(self._on_export)
        self.export_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _on_export(self):
        """Called when the user clicks the Export button."""
        # Show file dialog to get save location
        default_dir = os.path.expanduser("~/Documents")
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export PDF",
            default_dir,
            "PDF Files (*.pdf);;All Files (*)",
        )
        
        if not filepath:
            return  # User canceled
        
        # Ensure file has .pdf extension
        if not filepath.lower().endswith('.pdf'):
            filepath += '.pdf'
        
        # Get options from dialog controls
        options = self._get_export_options()
        
        # Export to PDF
        success, message = PDFExporter.export_to_pdf(self.canvas, filepath, options)
        
        # Show result message
        if success:
            QMessageBox.information(self, "Export Successful", message)
            self.accept()  # Close dialog on success
        else:
            QMessageBox.critical(self, "Export Failed", message)
    
    def _get_export_options(self):
        """Get the export options from dialog controls."""
        # Get page size
        page_size_name = self.size_combo.currentText()
        page_size = self.PAGE_SIZES.get(page_size_name, QPageSize.A4)
        
        # Get orientation
        orientation = 'portrait' if self.portrait_radio.isChecked() else 'landscape'
        
        # Get margin value (convert from mm to points)
        margin = self.margin_spin.value()
        
        return {
            'page_size': page_size,
            'orientation': orientation,
            'margin': margin,
            'fit_to_page': self.fit_check.isChecked(),
            'draw_border': self.border_check.isChecked(),
            'include_metadata': self.metadata_check.isChecked()
        }

    @staticmethod
    def export_canvas(parent, canvas):
        """Show export dialog and export the canvas if confirmed."""
        dialog = PDFExportDialog(parent, canvas)
        return dialog.exec_() == QDialog.Accepted 