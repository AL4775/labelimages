#!/usr/bin/env python3
"""
Test to validate that coordinate calculations work when using consistent image processing
"""

from PIL import Image
import os

def test_coordinate_consistency():
    """Test that coordinates calculated in fitted mode work correctly in 1:1 mode"""
    
    # Test with a known image
    test_image_path = r"C:\Users\arnau\Downloads\labelimages-main\test_images\test.jpg"
    if not os.path.exists(test_image_path):
        print("❌ Test image not found")
        return False
        
    print("🧪 Testing coordinate consistency...")
    
    # Load and process image the same way the app does
    img = Image.open(test_image_path)
    original_width, original_height = img.size
    print(f"📏 Original image: {original_width}x{original_height}")
    
    # Simulate fitted mode calculation
    canvas_width, canvas_height = 506, 279  # From debug output
    scale_x = canvas_width / original_width
    scale_y = canvas_height / original_height
    fitted_scale = min(scale_x, scale_y)
    
    display_width = int(original_width * fitted_scale)
    display_height = int(original_height * fitted_scale)
    
    offset_x = (canvas_width - display_width) // 2
    offset_y = (canvas_height - display_height) // 2
    
    print(f"📏 Fitted mode:")
    print(f"   Scale: {fitted_scale:.3f}")
    print(f"   Display size: {display_width}x{display_height}")
    print(f"   Offset: ({offset_x}, {offset_y})")
    
    # Simulate a click
    click_x, click_y = 370, 114
    
    # Calculate fitted mode coordinates
    if (click_x >= offset_x and click_x <= offset_x + display_width and 
        click_y >= offset_y and click_y <= offset_y + display_height):
        fitted_abs_x = (click_x - offset_x) / fitted_scale
        fitted_abs_y = (click_y - offset_y) / fitted_scale
        print(f"📍 Fitted calculation: click ({click_x}, {click_y}) -> image ({fitted_abs_x:.1f}, {fitted_abs_y:.1f})")
    else:
        print(f"📍 Click outside image area")
        return False
    
    # Simulate 1:1 mode with 2x zoom
    zoom_level = fitted_scale * 2.0
    new_width = int(original_width * zoom_level)
    new_height = int(original_height * zoom_level)
    
    print(f"📏 1:1 mode after 2x zoom:")
    print(f"   Zoom level: {zoom_level:.3f}")
    print(f"   Display size: {new_width}x{new_height}")
    
    # Test if coordinates are valid for the new image size
    if fitted_abs_x >= 0 and fitted_abs_x <= original_width and fitted_abs_y >= 0 and fitted_abs_y <= original_height:
        print(f"✅ Coordinates are valid for original image")
        
        # Test centering calculation
        padding_x = max(canvas_width // 2, 200)
        padding_y = max(canvas_height // 2, 200)
        
        scaled_point_x = fitted_abs_x * zoom_level + padding_x
        scaled_point_y = fitted_abs_y * zoom_level + padding_y
        
        print(f"📍 Centering calculation:")
        print(f"   Padding: ({padding_x}, {padding_y})")
        print(f"   Scaled point: ({scaled_point_x:.1f}, {scaled_point_y:.1f})")
        
        # Check if scaled coordinates are reasonable
        scroll_width = new_width + 2 * padding_x
        scroll_height = new_height + 2 * padding_y
        
        if scaled_point_x >= 0 and scaled_point_x <= scroll_width and scaled_point_y >= 0 and scaled_point_y <= scroll_height:
            print(f"✅ Scaled coordinates are within scroll region ({scroll_width}x{scroll_height})")
            return True
        else:
            print(f"❌ Scaled coordinates outside scroll region")
            return False
    else:
        print(f"❌ Coordinates invalid for original image")
        return False

if __name__ == "__main__":
    success = test_coordinate_consistency()
    print(f"\n{'✅ Test PASSED' if success else '❌ Test FAILED'}")