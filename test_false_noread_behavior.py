#!/usr/bin/env python3
"""
Test script to verify False NoRead checkbox is only enabled for read failure images
"""
import tkinter as tk
import image_label_tool

def test_false_noread_checkbox_behavior():
    """Test that False NoRead checkbox is only enabled for read failure images"""
    print("Testing False NoRead checkbox enable/disable behavior...")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        # Initialize the application
        app = image_label_tool.ImageLabelTool(root)
        
        # Set up test images
        app.all_image_paths = ['test1_123_20241021.jpg', 'test2_456_20241021.jpg']
        app.image_paths = app.all_image_paths.copy()
        app.labels = {}
        app.false_noread = {}
        app.ocr_readable = {}
        app.current_index = 0
        
        print("=== Test 1: Unclassified image ===")
        # Test 1: Unclassified image should have disabled checkbox
        app.labels['test1_123_20241021.jpg'] = "(Unclassified)"
        app.show_image()
        
        checkbox_state = str(app.false_noread_checkbox['state'])
        print(f"Checkbox state for unclassified image: {checkbox_state}")
        assert checkbox_state == 'disabled', f"Expected disabled, got {checkbox_state}"
        print("✅ Test 1 passed: Unclassified image has disabled False NoRead checkbox")
        
        print("\n=== Test 2: Read failure image ===")
        # Test 2: Read failure image should have enabled checkbox
        app.labels['test1_123_20241021.jpg'] = "read failure"
        app.show_image()
        
        checkbox_state = str(app.false_noread_checkbox['state'])
        print(f"Checkbox state for read failure image: {checkbox_state}")
        assert checkbox_state == 'normal', f"Expected normal, got {checkbox_state}"
        print("✅ Test 2 passed: Read failure image has enabled False NoRead checkbox")
        
        print("\n=== Test 3: Change from read failure to unreadable ===")
        # Test 3: Check a False NoRead box, then change classification
        app.false_noread_var.set(True)
        app.false_noread['test1_123_20241021.jpg'] = True
        print(f"False NoRead checked: {app.false_noread_var.get()}")
        assert app.false_noread_var.get() == True, "Failed to check False NoRead"
        
        # Change classification to unreadable
        app.label_var.set("unreadable")
        app.set_label_radio()
        
        # Check that checkbox is now disabled and unchecked
        checkbox_state = str(app.false_noread_checkbox['state'])
        checkbox_value = app.false_noread_var.get()
        stored_value = app.false_noread.get('test1_123_20241021.jpg', False)
        
        print(f"After changing to unreadable:")
        print(f"  Checkbox state: {checkbox_state}")
        print(f"  Checkbox value: {checkbox_value}")
        print(f"  Stored value: {stored_value}")
        
        assert checkbox_state == 'disabled', f"Expected disabled, got {checkbox_state}"
        assert checkbox_value == False, f"Expected False, got {checkbox_value}"
        assert stored_value == False, f"Expected stored False, got {stored_value}"
        print("✅ Test 3 passed: Changing from read failure to unreadable disables and unchecks False NoRead")
        
        print("\n=== Test 4: Other classification types ===")
        # Test 4: Test other classifications
        test_classifications = ["no label", "incomplete", "unreadable"]
        
        for classification in test_classifications:
            app.labels['test1_123_20241021.jpg'] = classification
            app.show_image()
            
            checkbox_state = str(app.false_noread_checkbox['state'])
            print(f"Checkbox state for '{classification}': {checkbox_state}")
            assert checkbox_state == 'disabled', f"Expected disabled for {classification}, got {checkbox_state}"
        
        print("✅ Test 4 passed: All non-read-failure classifications have disabled False NoRead checkbox")
        
        print("\n=== Test 5: Keyboard shortcut behavior ===")
        # Test 5: Test keyboard shortcut only works when enabled
        app.labels['test1_123_20241021.jpg'] = "unreadable"
        app.show_image()
        
        # Try to use F key shortcut when disabled
        initial_value = app.false_noread_var.get()
        app.label_shortcut_f()  # Should do nothing
        after_shortcut_value = app.false_noread_var.get()
        
        print(f"Keyboard shortcut test (disabled): {initial_value} -> {after_shortcut_value}")
        assert initial_value == after_shortcut_value, "Keyboard shortcut should not work when disabled"
        
        # Change to read failure and test shortcut works
        app.labels['test1_123_20241021.jpg'] = "read failure"
        app.show_image()
        
        initial_value = app.false_noread_var.get()
        app.label_shortcut_f()  # Should toggle
        after_shortcut_value = app.false_noread_var.get()
        
        print(f"Keyboard shortcut test (enabled): {initial_value} -> {after_shortcut_value}")
        assert initial_value != after_shortcut_value, "Keyboard shortcut should work when enabled"
        print("✅ Test 5 passed: Keyboard shortcut only works when checkbox is enabled")
        
        print("\n🎉 All False NoRead checkbox behavior tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_false_noread_checkbox_behavior()
    if success:
        print("\n✓ False NoRead checkbox now only works for read failure images!")
    else:
        print("\n❌ Implementation needs fixes!")