#!/usr/bin/env python3
"""
Simple focused test for mutual exclusivity
"""
import tkinter as tk
import image_label_tool
import os
import shutil

def test_simple_mutual_exclusivity():
    """Simple test focusing just on mutual exclusivity logic"""
    
    print("=== SIMPLE MUTUAL EXCLUSIVITY TEST ===")
    
    try:
        # Create minimal test setup
        root = tk.Tk()
        root.withdraw()  # Hide GUI
        app = image_label_tool.ImageLabelTool(root)
        
        # Set up minimal data
        test_path = "test_image.jpg"
        app.all_image_paths = [test_path]
        app.image_paths = [test_path]
        app.current_index = 0
        
        app.labels = {}
        app.ocr_readable = {}
        app.false_noread = {}
        app.comments = {}
        
        # Initialize variables
        app.ocr_readable_var = tk.BooleanVar()
        app.false_noread_var = tk.BooleanVar()
        
        print("✅ Test setup complete")
        
        # Test 1: Check OCR (should uncheck False NoRead)
        print("\n📋 Test 1: Check OCR checkbox")
        app.false_noread_var.set(True)  # Pre-set False NoRead
        app.false_noread[test_path] = True
        
        print(f"   Before: OCR={app.ocr_readable_var.get()}, False_NoRead={app.false_noread_var.get()}")
        
        app.ocr_readable_var.set(True)
        app.on_ocr_checkbox_changed()
        
        print(f"   After:  OCR={app.ocr_readable_var.get()}, False_NoRead={app.false_noread_var.get()}")
        print(f"   Stored: OCR={app.ocr_readable.get(test_path)}, False_NoRead={app.false_noread.get(test_path)}")
        
        if app.ocr_readable_var.get() == True and app.false_noread_var.get() == False:
            print("   ✅ OCR checkbox correctly unchecked False NoRead")
            test1_pass = True
        else:
            print("   ❌ OCR checkbox failed to uncheck False NoRead")
            test1_pass = False
        
        # Test 2: Check False NoRead (should uncheck OCR)
        print("\n📋 Test 2: Check False NoRead checkbox")
        
        print(f"   Before: OCR={app.ocr_readable_var.get()}, False_NoRead={app.false_noread_var.get()}")
        
        app.false_noread_var.set(True)
        app.on_false_noread_checkbox_changed()
        
        print(f"   After:  OCR={app.ocr_readable_var.get()}, False_NoRead={app.false_noread_var.get()}")
        print(f"   Stored: OCR={app.ocr_readable.get(test_path)}, False_NoRead={app.false_noread.get(test_path)}")
        
        if app.ocr_readable_var.get() == False and app.false_noread_var.get() == True:
            print("   ✅ False NoRead checkbox correctly unchecked OCR")
            test2_pass = True
        else:
            print("   ❌ False NoRead checkbox failed to uncheck OCR")
            test2_pass = False
        
        # Test 3: Uncheck False NoRead (OCR should remain unchecked)
        print("\n📋 Test 3: Uncheck False NoRead")
        
        print(f"   Before: OCR={app.ocr_readable_var.get()}, False_NoRead={app.false_noread_var.get()}")
        
        app.false_noread_var.set(False)
        app.on_false_noread_checkbox_changed()
        
        print(f"   After:  OCR={app.ocr_readable_var.get()}, False_NoRead={app.false_noread_var.get()}")
        print(f"   Stored: OCR={app.ocr_readable.get(test_path)}, False_NoRead={app.false_noread.get(test_path)}")
        
        if app.ocr_readable_var.get() == False and app.false_noread_var.get() == False:
            print("   ✅ Both checkboxes correctly unchecked")
            test3_pass = True
        else:
            print("   ❌ Unexpected state after unchecking")
            test3_pass = False
        
        # Test 4: Check that stored data never has conflicts
        print("\n📋 Test 4: Data integrity check")
        
        # Set up a potential conflict scenario
        app.ocr_readable_var.set(True)
        app.on_ocr_checkbox_changed()  # This should set OCR=True, False_NoRead=False
        
        # Now try to set False NoRead
        app.false_noread_var.set(True)
        app.on_false_noread_checkbox_changed()  # This should set OCR=False, False_NoRead=True
        
        stored_ocr = app.ocr_readable.get(test_path, False)
        stored_false_noread = app.false_noread.get(test_path, False)
        
        print(f"   Final stored state: OCR={stored_ocr}, False_NoRead={stored_false_noread}")
        
        # Check that both are not True simultaneously
        both_true = stored_ocr and stored_false_noread
        if not both_true:
            print("   ✅ Data integrity maintained - no conflicts in storage")
            test4_pass = True
        else:
            print("   ❌ Data integrity violated - both checkboxes stored as True")
            test4_pass = False
        
        root.destroy()
        
        overall_success = test1_pass and test2_pass and test3_pass and test4_pass
        return overall_success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🔬 SIMPLE MUTUAL EXCLUSIVITY TEST")
    print("="*40)
    
    success = test_simple_mutual_exclusivity()
    
    print(f"\n{'='*40}")
    if success:
        print("🎉 MUTUAL EXCLUSIVITY TEST PASSED!")
        print("✅ All core functionality working correctly")
        print("✅ OCR and False NoRead are mutually exclusive")
        print("✅ Data storage maintains integrity")
    else:
        print("💥 MUTUAL EXCLUSIVITY TEST FAILED!")
        print("❌ Core functionality needs fixes")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)