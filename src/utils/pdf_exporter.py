from PyQt5.QtCore import QRectF, QPointF, Qt, QMarginsF
from PyQt5.QtGui import QPainter, QPageSize, QPdfWriter, QColor, QPen, QTransform
from PyQt5.QtPrintSupport import QPrinter
import logging
import os
from datetime import datetime

class PDFExporter:
    """Utility class for exporting the canvas to PDF format."""
    
    # Constants for page orientation 
    # Using integer constants because of issues with enum imports in some PyQt5 versions
    PORTRAIT = 0
    LANDSCAPE = 1
    
    @staticmethod
    def export_to_pdf(canvas, filepath, options=None):
        """
        Export canvas contents to a PDF file.
        
        Args:
            canvas: The canvas object to export
            filepath: The destination file path for the PDF
            options: Dictionary of export options including:
                - page_size: QPageSize enum value (default: A4)
                - orientation: 'portrait' or 'landscape' (default: 'landscape')
                - margin: margin in pixels (default: 20)
                - include_metadata: add metadata to PDF (default: True)
                - fit_to_page: fit all content to a single page (default: True)
        
        Returns:
            tuple: (success, message)
        """
        try:
            # Setup logging
            logger = logging.getLogger(__name__)
            
            # Validate file path
            if not filepath.lower().endswith('.pdf'):
                filepath += '.pdf'
            
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            # Setup default options
            if options is None:
                options = {}
                
            page_size_name = options.get('page_size', QPageSize.A4)
            orientation = options.get('orientation', 'landscape')
            margin = options.get('margin', 20)
            fit_to_page = options.get('fit_to_page', True)
            
            # Create PDF writer
            pdf_writer = QPdfWriter(filepath)
            
            # Set page properties
            page_size = QPageSize(page_size_name)
            
            # In PyQt5, we use integer values for orientation:
            # 0 = Portrait, 1 = Landscape
            # Using constants directly because of inconsistencies in enum handling
            # across different PyQt5 versions
            if orientation.lower() == 'landscape':
                pdf_writer.setPageOrientation(PDFExporter.LANDSCAPE)  # 1 = Landscape
            else:
                pdf_writer.setPageOrientation(PDFExporter.PORTRAIT)  # 0 = Portrait
                
            # Set resolution for better quality
            pdf_writer.setResolution(300)  # 300 DPI
            
            # Set page size
            pdf_writer.setPageSize(page_size)
            
            # Set margins using QMarginsF
            margins = QMarginsF(margin, margin, margin, margin)
            pdf_writer.setPageMargins(margins)
            
            # Add metadata if requested
            if options.get('include_metadata', True):
                pdf_writer.setCreator("NISTO PDF Exporter")
                pdf_writer.setTitle("NISTO Canvas Export")
            
            # Store visibility state of all items to restore later
            visibility_states = {}
            for item in canvas.scene().items():
                visibility_states[item] = item.isVisible()
                item.setVisible(True)  # Make all items visible for export
                
            # Calculate scene rect containing all items
            scene_rect = canvas.scene().itemsBoundingRect()
            
            # Ensure the scene rect is valid and not empty
            if scene_rect.isEmpty():
                # If the scene is empty, create a default rect
                scene_rect = QRectF(-100, -100, 200, 200)
            else:
                # Add some margin to the scene rect
                scene_rect.adjust(-20, -20, 20, 20)
            
            # Log the scene rect for debugging
            logger.info(f"Scene rect for PDF export: {scene_rect}")
            logger.info(f"Number of items in scene: {len(canvas.scene().items())}")
            
            # Create painter for drawing
            painter = QPainter()
            if not painter.begin(pdf_writer):
                logger.error("Failed to initialize painter on PDF writer")
                # Restore visibility states
                for item, was_visible in visibility_states.items():
                    item.setVisible(was_visible)
                return False, "Failed to initialize PDF document"
            
            try:
                # Enable high quality rendering
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.TextAntialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                
                # Calculate the usable page size in scene coordinates
                page_rect = QRectF(0, 0, pdf_writer.width(), pdf_writer.height())
                logger.info(f"Page rect for PDF export: {page_rect}")
                
                # Draw background first
                painter.fillRect(page_rect, QColor(255, 255, 255))
                
                # Set up the transform to map the scene to the PDF page
                if fit_to_page:
                    # Calculate the scaling factor to fit the scene into the page
                    x_scale = page_rect.width() / scene_rect.width() if scene_rect.width() > 0 else 1
                    y_scale = page_rect.height() / scene_rect.height() if scene_rect.height() > 0 else 1
                    
                    # Use the smaller scaling factor to preserve aspect ratio
                    scale = min(x_scale, y_scale) * 0.9  # Scale slightly smaller for some margin
                    logger.info(f"PDF scaling factor: {scale}")
                    
                    # Calculate the target rectangle (scaled and centered)
                    target_rect = QRectF(
                        (page_rect.width() - scene_rect.width() * scale) / 2,
                        (page_rect.height() - scene_rect.height() * scale) / 2,
                        scene_rect.width() * scale,
                        scene_rect.height() * scale
                    )
                    
                    # Render using the explicit source and target rects
                    canvas.scene().render(painter, target_rect, scene_rect)
                else:
                    # For multi-page printing, we'd need to create multiple pages and
                    # handle pagination here
                    target_rect = QRectF(
                        margin, 
                        margin, 
                        page_rect.width() - margin * 2, 
                        page_rect.height() - margin * 2
                    )
                    canvas.scene().render(painter, target_rect, scene_rect, Qt.KeepAspectRatio)
                
                # Optional - draw a border for the content area
                if options.get('draw_border', False):
                    painter.setPen(QPen(QColor(0, 0, 0), 1))
                    if fit_to_page:
                        # Draw border around the actual content
                        painter.drawRect(target_rect)
                    else:
                        painter.drawRect(QRectF(
                            margin, 
                            margin, 
                            page_rect.width() - margin * 2, 
                            page_rect.height() - margin * 2
                        ))
            finally:
                # End painting
                painter.end()
                
                # Restore visibility states
                for item, was_visible in visibility_states.items():
                    item.setVisible(was_visible)
            
            logger.info(f"Canvas successfully exported to PDF: {filepath}")
            return True, f"Canvas successfully exported to PDF: {filepath}"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error exporting to PDF: {str(e)}")
            return False, f"Error exporting to PDF: {str(e)}" 