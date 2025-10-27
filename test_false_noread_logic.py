#!/usr/bin/env python3
"""
Test script to verify False NoRead checkbox behavior without requiring actual images
"""
import tkinter as tk
import image_label_tool

def test_false_noread_checkbox_logic():
    """Test the False NoRead checkbox enable/disable logic"""
    print("Testing False NoRead checkbox logic...")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        # Initialize the application
        app = image_label_tool.ImageLabelTool(root)
        
        # Set up minimal test data
        app.all_image_paths = ['test1.jpg']
        app.image_paths = app.all_image_paths.copy()
        app.labels = {}
        app.false_noread = {}
        app.current_index = 0
        
        print("=== Test 1: Function logic for unclassified image ===")
        # Test the logic function directly
        app.labels['test1.jpg'] = "(Unclassified)"
        
        # Test the update function directly
        app.update_false_noread_checkbox_state()
        
        checkbox_state = str(app.false_noread_checkbox['state'])
        print(f"Checkbox state for unclassified: {checkbox_state}")
        assert checkbox_state == 'disabled', f"Expected disabled, got {checkbox_state}"
        print("✅ Test 1 passed: Unclassified image disables checkbox")
        
        print("\n=== Test 2: Function logic for read failure image ===")
        app.labels['test1.jpg'] = "read failure"
        app.update_false_noread_checkbox_state()
        
        checkbox_state = str(app.false_noread_checkbox['state'])
        print(f"Checkbox state for read failure: {checkbox_state}")
        assert checkbox_state == 'normal', f"Expected normal, got {checkbox_state}"
        print("✅ Test 2 passed: Read failure image enables checkbox")
        
        print("\n=== Test 3: Auto-uncheck when changing classification ===")
        # First set False NoRead to True for read failure
        app.false_noread['test1.jpg'] = True
        app.false_noread_var.set(True)
        print(f"Initial False NoRead state: {app.false_noread_var.get()}")
        
        # Change to unreadable
        app.labels['test1.jpg'] = "unreadable"
        app.update_false_noread_checkbox_state()
        
        checkbox_state = str(app.false_noread_checkbox['state'])
        checkbox_value = app.false_noread_var.get()
        stored_value = app.false_noread.get('test1.jpg', False)
        
        print(f"After changing to unreadable:")
        print(f"  Checkbox state: {checkbox_state}")
        print(f"  Checkbox UI value: {checkbox_value}")
        print(f"  Stored value: {stored_value}")
        
        assert checkbox_state == 'disabled', f"Expected disabled, got {checkbox_state}"
        assert checkbox_value == False, f"Expected False, got {checkbox_value}"
        assert stored_value == False, f"Expected stored False, got {stored_value}"
        print("✅ Test 3 passed: Changing to non-read-failure unchecks and disables")
        
        print("\n=== Test 4: Test all classification types ===")
        test_classifications = [
            ("(Unclassified)", "disabled"),
            ("no label", "disabled"),
            ("read failure", "normal"),
            ("incomplete", "disabled"),
            ("unreadable", "disabled")
        ]
        
        for classification, expected_state in test_classifications:
            app.labels['test1.jpg'] = classification
            app.update_false_noread_checkbox_state()
            
            actual_state = str(app.false_noread_checkbox['state'])
            print(f"'{classification}' -> {actual_state} (expected: {expected_state})")
            assert actual_state == expected_state, f"Expected {expected_state} for {classification}, got {actual_state}"
        
        print("✅ Test 4 passed: All classifications behave correctly")
        
        print("\n=== Test 5: Keyboard shortcut logic ===")
        # Test keyboard shortcut function logic
        
        # Test with disabled checkbox (unreadable)
        app.labels['test1.jpg'] = "unreadable"
        app.update_false_noread_checkbox_state()
        app.false_noread_var.set(False)
        
        # Mock the should_ignore_keyboard_shortcuts_new to return False
        original_should_ignore = app.should_ignore_keyboard_shortcuts_new
        app.should_ignore_keyboard_shortcuts_new = lambda: False
        
        initial_value = app.false_noread_var.get()
        app.label_shortcut_f()  # Should do nothing when disabled
        after_value = app.false_noread_var.get()
        
        print(f"Shortcut on disabled checkbox: {initial_value} -> {after_value}")
        assert initial_value == after_value, "Shortcut should not work when disabled"
        
        # Test with enabled checkbox (read failure)
        app.labels['test1.jpg'] = "read failure"
        app.update_false_noread_checkbox_state()
        app.false_noread_var.set(False)
        
        initial_value = app.false_noread_var.get()
        app.label_shortcut_f()  # Should toggle when enabled
        after_value = app.false_noread_var.get()
        
        print(f"Shortcut on enabled checkbox: {initial_value} -> {after_value}")
        assert initial_value != after_value, "Shortcut should work when enabled"
        
        # Restore original function
        app.should_ignore_keyboard_shortcuts_new = original_should_ignore
        
        print("✅ Test 5 passed: Keyboard shortcut respects checkbox state")
        
        print("\n🎉 All False NoRead checkbox logic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_false_noread_checkbox_logic()
    if success:
        print("\n✓ False NoRead checkbox logic is working correctly!")
    else:
        print("\n❌ Implementation needs fixes!")