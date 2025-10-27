#!/usr/bin/env python3
"""
Test script to verify mutual exclusivity between OCR and False NoRead checkboxes
"""
import tkinter as tk
import image_label_tool
import os
import shutil

def test_mutual_exclusivity():
    """Test that OCR and False NoRead checkboxes are mutually exclusive"""
    
    print("=== MUTUAL EXCLUSIVITY TEST ===")
    
    # Create a test directory with a dummy image
    test_dir = "mutual_exclusive_test"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Create a dummy image file
    test_image = os.path.join(test_dir, "001_001_A.jpg")
    with open(test_image, 'w') as f:
        f.write("")  # Empty file for testing
    
    try:
        # Create application instance
        root = tk.Tk()
        root.withdraw()  # Hide the GUI for testing
        app = image_label_tool.ImageLabelTool(root)
        
        # Set up the test image
        app.all_image_paths = [os.path.abspath(test_image)]
        app.image_paths = app.all_image_paths.copy()
        app.current_index = 0
        
        # Initialize data structures
        app.labels = {}
        app.ocr_readable = {}
        app.false_noread = {}
        app.comments = {}
        
        # Initialize checkbox variables
        app.ocr_readable_var = tk.BooleanVar()
        app.false_noread_var = tk.BooleanVar()
        
        print(f"✅ Set up test with image: {os.path.basename(test_image)}")
        
        # Test Case 1: Neither checkbox initially checked
        print(f"\n📋 Test Case 1: Initial state (neither checked)")
        print(f"   OCR readable: {app.ocr_readable_var.get()}")
        print(f"   False NoRead: {app.false_noread_var.get()}")
        
        expected_ocr = False
        expected_false_noread = False
        
        if app.ocr_readable_var.get() == expected_ocr and app.false_noread_var.get() == expected_false_noread:
            print(f"   ✅ Initial state correct")
        else:
            print(f"   ❌ Initial state incorrect")
            return False
        
        # Test Case 2: Check OCR - should uncheck False NoRead
        print(f"\n📋 Test Case 2: Check OCR checkbox")
        app.ocr_readable_var.set(True)
        app.on_ocr_checkbox_changed()
        
        print(f"   OCR readable: {app.ocr_readable_var.get()}")
        print(f"   False NoRead: {app.false_noread_var.get()}")
        
        if app.ocr_readable_var.get() == True and app.false_noread_var.get() == False:
            print(f"   ✅ OCR checked, False NoRead correctly unchecked")
        else:
            print(f"   ❌ Mutual exclusivity failed when checking OCR")
            return False
        
        # Test Case 3: Check False NoRead - should uncheck OCR
        print(f"\n📋 Test Case 3: Check False NoRead checkbox")
        app.false_noread_var.set(True)
        app.on_false_noread_checkbox_changed()
        
        print(f"   OCR readable: {app.ocr_readable_var.get()}")
        print(f"   False NoRead: {app.false_noread_var.get()}")
        
        if app.ocr_readable_var.get() == False and app.false_noread_var.get() == True:
            print(f"   ✅ False NoRead checked, OCR correctly unchecked")
        else:
            print(f"   ❌ Mutual exclusivity failed when checking False NoRead")
            return False
        
        # Test Case 4: Uncheck False NoRead - OCR should remain unchecked
        print(f"\n📋 Test Case 4: Uncheck False NoRead")
        app.false_noread_var.set(False)
        app.on_false_noread_checkbox_changed()
        
        print(f"   OCR readable: {app.ocr_readable_var.get()}")
        print(f"   False NoRead: {app.false_noread_var.get()}")
        
        if app.ocr_readable_var.get() == False and app.false_noread_var.get() == False:
            print(f"   ✅ Both checkboxes correctly unchecked")
        else:
            print(f"   ❌ Unexpected state after unchecking False NoRead")
            return False
        
        # Test Case 5: Check OCR again - should work normally
        print(f"\n📋 Test Case 5: Check OCR again")
        app.ocr_readable_var.set(True)
        app.on_ocr_checkbox_changed()
        
        print(f"   OCR readable: {app.ocr_readable_var.get()}")
        print(f"   False NoRead: {app.false_noread_var.get()}")
        
        if app.ocr_readable_var.get() == True and app.false_noread_var.get() == False:
            print(f"   ✅ OCR checked correctly")
        else:
            print(f"   ❌ Failed to check OCR again")
            return False
        
        # Test Case 6: Uncheck OCR - both should be unchecked
        print(f"\n📋 Test Case 6: Uncheck OCR")
        app.ocr_readable_var.set(False)
        app.on_ocr_checkbox_changed()
        
        print(f"   OCR readable: {app.ocr_readable_var.get()}")
        print(f"   False NoRead: {app.false_noread_var.get()}")
        
        if app.ocr_readable_var.get() == False and app.false_noread_var.get() == False:
            print(f"   ✅ Both checkboxes correctly unchecked")
        else:
            print(f"   ❌ Unexpected state after unchecking OCR")
            return False
        
        # Test data persistence
        print(f"\n📋 Test Case 7: Data persistence")
        image_path = app.all_image_paths[0]
        
        # Check OCR and verify it's stored
        app.ocr_readable_var.set(True)
        app.on_ocr_checkbox_changed()
        
        ocr_stored = app.ocr_readable.get(image_path, False)
        false_noread_stored = app.false_noread.get(image_path, False)
        
        print(f"   Stored OCR readable: {ocr_stored}")
        print(f"   Stored False NoRead: {false_noread_stored}")
        
        if ocr_stored == True and false_noread_stored == False:
            print(f"   ✅ Data correctly stored")
        else:
            print(f"   ❌ Data storage incorrect")
            return False
        
        # Check False NoRead and verify OCR is cleared from storage
        app.false_noread_var.set(True)
        app.on_false_noread_checkbox_changed()
        
        ocr_stored = app.ocr_readable.get(image_path, False)
        false_noread_stored = app.false_noread.get(image_path, False)
        
        print(f"   After False NoRead - OCR stored: {ocr_stored}")
        print(f"   After False NoRead - False NoRead stored: {false_noread_stored}")
        
        if ocr_stored == False and false_noread_stored == True:
            print(f"   ✅ Data correctly updated with mutual exclusivity")
        else:
            print(f"   ❌ Data storage doesn't respect mutual exclusivity")
            return False
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test data
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n🧹 Cleaned up test data: {test_dir}")

def run_comprehensive_mutual_exclusivity_test():
    """Run comprehensive test including UI behavior simulation"""
    
    print("🔬 COMPREHENSIVE MUTUAL EXCLUSIVITY TEST")
    print("="*50)
    
    success = test_mutual_exclusivity()
    
    if success:
        print(f"\n🎉 MUTUAL EXCLUSIVITY TEST PASSED!")
        print(f"✅ OCR and False NoRead checkboxes are properly mutually exclusive")
        print(f"✅ Checking one automatically unchecks the other")
        print(f"✅ Data storage respects mutual exclusivity")
        print(f"✅ Both checkboxes can be unchecked (neither selected)")
        print(f"")
        print(f"BEHAVIOR SUMMARY:")
        print(f"• Initially: Neither checkbox checked")
        print(f"• Check OCR → False NoRead automatically unchecked")
        print(f"• Check False NoRead → OCR automatically unchecked")  
        print(f"• Uncheck either → Both remain unchecked")
        print(f"• Data storage updated correctly for all scenarios")
    else:
        print(f"\n💥 MUTUAL EXCLUSIVITY TEST FAILED!")
        print(f"❌ Implementation needs fixes")
    
    return success

if __name__ == "__main__":
    import sys
    success = run_comprehensive_mutual_exclusivity_test()
    sys.exit(0 if success else 1)