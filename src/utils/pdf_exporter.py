from PyQt5.QtCore import QRectF, QPointF, Qt, QMarginsF
from PyQt5.QtGui import QPainter, QPageSize, QPdfWriter, QColor, QPen, QTransform, QBrush
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtSvg import QSvgRenderer, QGraphicsSvgItem
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
    def _prepare_svg_items_for_export(scene):
        """Ensure that SVG items have transparent backgrounds for PDF export.
        
        This method temporarily modifies SVG rendering for PDF export purposes.
        """
        modified_items = []
        
        for item in scene.items():
            # Check if the item is a device with an SVG icon
            if hasattr(item, 'icon_item') and item.icon_item is not None:
                if isinstance(item.icon_item, QGraphicsSvgItem):
                    # Force SVG renderer to use proper transparency
                    item.icon_item.setCacheMode(QGraphicsItem.NoCache)
                    modified_items.append(item.icon_item)
                    
                    # Ensure background rectangle is hidden for SVG icons
                    if hasattr(item, 'rect_item') and item.rect_item is not None:
                        # Store current visibility state to restore later
                        item._rect_visibility_before_export = item.rect_item.isVisible()
                        # Make sure it's hidden
                        item.rect_item.setVisible(False)
                        modified_items.append(item.rect_item)
            
            # Handle SVG items directly
            if isinstance(item, QGraphicsSvgItem):
                item.setCacheMode(QGraphicsItem.NoCache)
                modified_items.append(item)
        
        return modified_items
    
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
                pdf_writer.setCreator("GraphNIST PDF Exporter")
                pdf_writer.setTitle("GraphNIST Canvas Export")
            
            # Store visibility and style states
            visibility_states = {}
            text_color_states = {}
            connection_pen_states = {}
            
            # Make everything visible and ensure text is black for export
            for item in canvas.scene().items():
                # Store visibility state
                visibility_states[item] = item.isVisible()
                item.setVisible(True)  # Make all items visible for export
                
                # Force text items to be black for PDF export
                if hasattr(item, 'defaultTextColor') and callable(getattr(item, 'defaultTextColor')):
                    # Store original text color
                    text_color_states[item] = item.defaultTextColor()
                    # Set text to black for PDF export
                    item.setDefaultTextColor(QColor(0, 0, 0))
                
                # Handle QGraphicsTextItem separately (they might be children of devices)
                elif hasattr(item, 'childItems') and callable(getattr(item, 'childItems')):
                    for child in item.childItems():
                        if hasattr(child, 'defaultTextColor') and callable(getattr(child, 'defaultTextColor')):
                            text_color_states[child] = child.defaultTextColor()
                            child.setDefaultTextColor(QColor(0, 0, 0))
                
                # Handle connection labels specially
                if hasattr(item, 'label') and item.label is not None:
                    if hasattr(item.label, 'defaultTextColor') and callable(getattr(item.label, 'defaultTextColor')):
                        text_color_states[item.label] = item.label.defaultTextColor()
                        item.label.setDefaultTextColor(QColor(0, 0, 0))
                
                # Force connections to be black for PDF export
                if hasattr(item, 'pen') and callable(getattr(item, 'pen')) and callable(getattr(item, 'setPen', None)):
                    # Store original pen for connections
                    connection_pen_states[item] = item.pen()
                    # Create a black pen with the same width and style
                    black_pen = QPen(connection_pen_states[item])
                    black_pen.setColor(QColor(0, 0, 0))
                    item.setPen(black_pen)
                
                # Handle boundaries specially
                if hasattr(item, 'boundary_type') or (hasattr(item, 'boundaryType') and item.boundaryType):
                    if hasattr(item, 'setPen') and callable(getattr(item, 'setPen')):
                        connection_pen_states[item] = item.pen()
                        border_pen = QPen(connection_pen_states[item])
                        border_pen.setColor(QColor(0, 0, 0))
                        item.setPen(border_pen)
            
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
            
            # Prepare SVG items for proper transparency in PDF
            svg_items = PDFExporter._prepare_svg_items_for_export(canvas.scene())
            logger.info(f"Prepared {len(svg_items)} SVG items for PDF export")
            
            # Create painter for drawing
            painter = QPainter()
            if not painter.begin(pdf_writer):
                logger.error("Failed to initialize painter on PDF writer")
                # Restore visibility and text colors
                for item, was_visible in visibility_states.items():
                    item.setVisible(was_visible)
                for item, color in text_color_states.items():
                    item.setDefaultTextColor(color)
                for item, pen in connection_pen_states.items():
                    item.setPen(pen)
                return False, "Failed to initialize PDF document"
            
            try:
                # Enable high quality rendering
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.TextAntialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                
                # Calculate the usable page size in scene coordinates
                page_rect = QRectF(0, 0, pdf_writer.width(), pdf_writer.height())
                logger.info(f"Page rect for PDF export: {page_rect}")
                
                # Draw background first - use white for the page background
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                painter.fillRect(page_rect, QColor(255, 255, 255))
                
                # Set composition mode for proper transparency handling
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                
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
                    
                    # For devices with SVG icons, ensure the background rectangle is invisible
                    # This extra step ensures absolute transparency
                    for item in canvas.scene().items():
                        if hasattr(item, 'device_type') and hasattr(item, 'rect_item') and item.rect_item:
                            if hasattr(item, 'icon_item') and isinstance(item.icon_item, QGraphicsSvgItem):
                                item.rect_item.setBrush(QBrush(Qt.transparent))
                                item.rect_item.setPen(QPen(Qt.transparent, 0))
                    
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
                    
                    # For devices with SVG icons, ensure the background rectangle is invisible
                    # This extra step ensures absolute transparency
                    for item in canvas.scene().items():
                        if hasattr(item, 'device_type') and hasattr(item, 'rect_item') and item.rect_item:
                            if hasattr(item, 'icon_item') and isinstance(item.icon_item, QGraphicsSvgItem):
                                item.rect_item.setBrush(QBrush(Qt.transparent))
                                item.rect_item.setPen(QPen(Qt.transparent, 0))
                    
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
                
                # Restore visibility states and text colors
                for item, was_visible in visibility_states.items():
                    item.setVisible(was_visible)
                
                # Restore original text colors
                for item, color in text_color_states.items():
                    item.setDefaultTextColor(color)
                
                # Restore original connection pens
                for item, pen in connection_pen_states.items():
                    item.setPen(pen)
                
                # Restore rectangle visibility for device items
                for item in canvas.scene().items():
                    if hasattr(item, '_rect_visibility_before_export'):
                        if hasattr(item, 'rect_item') and item.rect_item is not None:
                            item.rect_item.setVisible(item._rect_visibility_before_export)
                        delattr(item, '_rect_visibility_before_export')
            
            logger.info(f"Canvas successfully exported to PDF: {filepath}")
            return True, f"Canvas successfully exported to PDF: {filepath}"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error exporting to PDF: {str(e)}")
            return False, f"Error exporting to PDF: {str(e)}" 