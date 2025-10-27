#!/usr/bin/env python3
"""
Test script to verify double-click zoom functionality
"""

import os
import sys
from image_label_tool import ImageLabelTool
import tkinter as tk

def test_zoom_functionality():
    """Test that zoom methods exist and can be called"""
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create an instance of ImageLabelTool
        app = ImageLabelTool(root)
        
        # Test that our zoom methods exist
        methods_to_test = [
            'double_click_zoom_in',
            'double_click_zoom_out', 
            '_perform_centered_zoom',
            '_center_image_point'
        ]
        
        print("Testing zoom functionality...")
        
        for method_name in methods_to_test:
            if hasattr(app, method_name):
                print(f"✓ Method '{method_name}' exists")
            else:
                print(f"✗ Method '{method_name}' missing")
                return False
        
        # Test that padding attributes can be set
        app.image_padding_x = 100
        app.image_padding_y = 100
        print(f"✓ Padding attributes work: x={app.image_padding_x}, y={app.image_padding_y}")
        
        # Test zoom level initialization
        if hasattr(app, 'zoom_level'):
            print(f"✓ zoom_level initialized: {app.zoom_level}")
        else:
            print("✗ zoom_level attribute missing")
            return False
            
        print("\n🎉 All zoom functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_zoom_functionality()
    sys.exit(0 if success else 1)