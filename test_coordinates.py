#!/usr/bin/env python3
"""
Test coordinate conversion logic for zoom centering
"""

def test_coordinate_conversion():
    """Test the coordinate conversion math"""
    
    print("🧮 Testing coordinate conversion logic...\n")
    
    # Simulate the scenario from the debug output
    click_canvas_x, click_canvas_y = 1118, 338
    canvas_width, canvas_height = 1441, 1048
    padding_x, padding_y = 720, 524
    zoom_level = 1.0  # Start at 1x zoom
    
    # Simulate current scroll position (initially at 0,0)
    scroll_x_frac, scroll_y_frac = 0.0, 0.0
    
    print(f"Initial state:")
    print(f"  Click: ({click_canvas_x}, {click_canvas_y})")
    print(f"  Canvas: {canvas_width}x{canvas_height}")
    print(f"  Padding: ({padding_x}, {padding_y})")
    print(f"  Zoom: {zoom_level}x")
    print(f"  Scroll: ({scroll_x_frac:.3f}, {scroll_y_frac:.3f})")
    
    # Step 1: Convert click to scroll region coordinates
    # With no scroll, canvasx() would return the same as click_canvas_x
    canvas_x = click_canvas_x  # Simplified - no scroll initially
    canvas_y = click_canvas_y
    
    print(f"\nStep 1 - Canvas coordinates:")
    print(f"  Canvas coords: ({canvas_x}, {canvas_y})")
    
    # Step 2: Convert to image coordinates (subtract padding)
    image_canvas_x = canvas_x - padding_x
    image_canvas_y = canvas_y - padding_y
    
    print(f"\nStep 2 - Image canvas coordinates:")
    print(f"  Image canvas coords: ({image_canvas_x}, {image_canvas_y})")
    
    # Step 3: Convert to original image coordinates
    abs_x = image_canvas_x / zoom_level
    abs_y = image_canvas_y / zoom_level
    
    print(f"\nStep 3 - Original image coordinates:")
    print(f"  Original image coords: ({abs_x:.1f}, {abs_y:.1f})")
    
    # Now simulate zoom to 1.48x
    new_zoom_level = 1.48
    print(f"\n🔍 After zoom to {new_zoom_level}x:")
    
    # Calculate where the point should be in the new scaled image
    scaled_point_x = abs_x * new_zoom_level + padding_x
    scaled_point_y = abs_y * new_zoom_level + padding_y
    
    print(f"  Scaled point in scroll region: ({scaled_point_x:.1f}, {scaled_point_y:.1f})")
    
    # Calculate centering
    center_x = canvas_width / 2
    center_y = canvas_height / 2
    
    print(f"  Canvas center: ({center_x:.1f}, {center_y:.1f})")
    
    # Calculate required scroll position
    target_left = scaled_point_x - center_x
    target_top = scaled_point_y - center_y
    
    print(f"  Target scroll position: ({target_left:.1f}, {target_top:.1f})")
    
    # Simulate scroll region size after zoom
    image_width, image_height = 800, 600  # Original test image size
    new_width = int(image_width * new_zoom_level)
    new_height = int(image_height * new_zoom_level)
    scroll_width = new_width + 2 * padding_x
    scroll_height = new_height + 2 * padding_y
    
    print(f"  Scroll region: {scroll_width}x{scroll_height}")
    
    # Calculate max scroll
    max_scroll_x = max(0, scroll_width - canvas_width)
    max_scroll_y = max(0, scroll_height - canvas_height)
    
    print(f"  Max scroll: ({max_scroll_x:.1f}, {max_scroll_y:.1f})")
    
    # Calculate final scroll fractions
    if max_scroll_x > 0:
        final_scroll_x = max(0, min(target_left, max_scroll_x)) / max_scroll_x
    else:
        final_scroll_x = 0.0
        
    if max_scroll_y > 0:
        final_scroll_y = max(0, min(target_top, max_scroll_y)) / max_scroll_y
    else:
        final_scroll_y = 0.0
        
    print(f"  Final scroll fractions: ({final_scroll_x:.3f}, {final_scroll_y:.3f})")
    
    print(f"\n✅ Coordinate conversion test complete!")

if __name__ == "__main__":
    test_coordinate_conversion()