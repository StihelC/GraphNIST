#!/usr/bin/env python
"""
Script to create missing icons for GraphNIST
This generates simple placeholder SVG icons for toolbar buttons
"""

import os
import sys
from pathlib import Path

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
svg_dir = os.path.join(src_dir, 'resources', 'icons', 'svg')

# Create the output directory if it doesn't exist
os.makedirs(svg_dir, exist_ok=True)

# Define functions to create SVG content for each missing icon
def create_add_device_svg():
    """Create an SVG for add device button - rectangle with plus sign"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="4" width="20" height="16" stroke="#000" fill="none" stroke-width="1.5"/>
    <line x1="12" y1="8" x2="12" y2="16" stroke="#000" stroke-width="2"/>
    <line x1="8" y1="12" x2="16" y2="12" stroke="#000" stroke-width="2"/>
</svg>'''

def create_add_connection_svg():
    """Create an SVG for add connection button - two dots with a line"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle cx="6" cy="12" r="3" fill="#000"/>
    <circle cx="18" cy="12" r="3" fill="#000"/>
    <line x1="9" y1="12" x2="15" y2="12" stroke="#000" stroke-width="1.5"/>
</svg>'''

def create_add_boundary_svg():
    """Create an SVG for add boundary button - dashed rectangle"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="4" width="20" height="16" stroke="#000" fill="none" stroke-width="1.5" stroke-dasharray="4,2"/>
</svg>'''

def create_delete_svg():
    """Create an SVG for delete button - trash can"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M6 7L8 21H16L18 7" stroke="#000" fill="none" stroke-width="1.5"/>
    <path d="M4 7H20" stroke="#000" stroke-width="1.5"/>
    <path d="M9 7V4H15V7" stroke="#000" fill="none" stroke-width="1.5"/>
    <line x1="10" y1="11" x2="10" y2="17" stroke="#000" stroke-width="1.5"/>
    <line x1="14" y1="11" x2="14" y2="17" stroke="#000" stroke-width="1.5"/>
</svg>'''

def create_magnify_svg():
    """Create an SVG for magnify button - magnifying glass"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle cx="10" cy="10" r="6" stroke="#000" fill="none" stroke-width="1.5"/>
    <line x1="14.5" y1="14.5" x2="19" y2="19" stroke="#000" stroke-width="2"/>
</svg>'''

def create_zoom_in_svg():
    """Create an SVG for zoom in button - magnifying glass with plus"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle cx="10" cy="10" r="6" stroke="#000" fill="none" stroke-width="1.5"/>
    <line x1="14.5" y1="14.5" x2="19" y2="19" stroke="#000" stroke-width="2"/>
    <line x1="10" y1="7" x2="10" y2="13" stroke="#000" stroke-width="1.5"/>
    <line x1="7" y1="10" x2="13" y2="10" stroke="#000" stroke-width="1.5"/>
</svg>'''

def create_zoom_out_svg():
    """Create an SVG for zoom out button - magnifying glass with minus"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle cx="10" cy="10" r="6" stroke="#000" fill="none" stroke-width="1.5"/>
    <line x1="14.5" y1="14.5" x2="19" y2="19" stroke="#000" stroke-width="2"/>
    <line x1="7" y1="10" x2="13" y2="10" stroke="#000" stroke-width="1.5"/>
</svg>'''

def create_zoom_reset_svg():
    """Create an SVG for zoom reset button - magnifying glass with 1:1"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle cx="10" cy="10" r="6" stroke="#000" fill="none" stroke-width="1.5"/>
    <line x1="14.5" y1="14.5" x2="19" y2="19" stroke="#000" stroke-width="2"/>
    <text x="7" y="13" font-family="sans-serif" font-size="7" font-weight="bold">1:1</text>
</svg>'''

# Map of icon names to their creation functions
ICONS_TO_CREATE = {
    "add_device.svg": create_add_device_svg,
    "add_connection.svg": create_add_connection_svg,
    "add_boundary.svg": create_add_boundary_svg,
    "delete.svg": create_delete_svg,
    "magnify.svg": create_magnify_svg,
    "zoom_in.svg": create_zoom_in_svg,
    "zoom_out.svg": create_zoom_out_svg,
    "zoom_reset.svg": create_zoom_reset_svg
}

def main():
    """Create missing icons"""
    print(f"Creating missing icons in {svg_dir}")
    
    # Create each icon
    created_count = 0
    for icon_name, create_func in ICONS_TO_CREATE.items():
        icon_path = os.path.join(svg_dir, icon_name)
        
        # Skip if icon already exists
        if os.path.exists(icon_path):
            print(f"Skipping existing icon: {icon_name}")
            continue
            
        # Create the icon
        svg_content = create_func()
        with open(icon_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        print(f"Created icon: {icon_name}")
        created_count += 1
    
    print(f"Created {created_count} icons.")
    
if __name__ == "__main__":
    main() 