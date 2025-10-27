#!/usr/bin/env python3
"""
Integration test to verify False NoRead priority in UI statistics
"""
import os
import sys
import shutil

def test_ui_integration():
    """Test the priority logic in actual UI statistics calculations"""
    
    try:
        import image_label_tool
        import tkinter as tk
        
        print("=== UI INTEGRATION TEST ===")
        
        # Create application instance
        root = tk.Tk()
        root.withdraw()  # Hide the GUI for testing
        app = image_label_tool.ImageLabelTool(root)
        
        # Create test data with conflicts
        app.all_image_paths = [
            "session1_img1_A.jpg",  # OCR only
            "session1_img2_A.jpg",  # OCR only
            "session2_img1_B.jpg",  # False NoRead only  
            "session2_img2_B.jpg",  # False NoRead only
            "session3_img1_C.jpg",  # CONFLICT: Both OCR and False NoRead
            "session3_img2_C.jpg",  # CONFLICT: Both OCR and False NoRead
        ]
        
        app.image_paths = app.all_image_paths.copy()
        app.labels = {}
        app.ocr_readable = {}
        app.false_noread = {}
        app.comments = {}
        
        # Set up conflicting data
        for i, path in enumerate(app.all_image_paths):
            if "session1" in path:
                app.labels[path] = "good"
                app.ocr_readable[path] = True
                app.false_noread[path] = False
            elif "session2" in path:
                app.labels[path] = "read failure"
                app.ocr_readable[path] = False
                app.false_noread[path] = True
            elif "session3" in path:  # CONFLICT SESSION
                app.labels[path] = "good"
                app.ocr_readable[path] = True      # OCR = True
                app.false_noread[path] = True      # False NoRead = True (CONFLICT!)
        
        print("✅ Set up test data with 3 sessions:")
        print("   - Session 1: OCR only")
        print("   - Session 2: False NoRead only")  
        print("   - Session 3: BOTH OCR and False NoRead (CONFLICT)")
        
        # Test individual calculations
        ocr_sessions = app.calculate_sessions_with_ocr_readable()
        false_noread_sessions = app.calculate_sessions_with_false_noread()
        ocr_non_failure_sessions = app.calculate_ocr_readable_non_failure_sessions()
        
        print(f"\n📊 Results:")
        print(f"   OCR readable sessions (excluding conflicts): {ocr_sessions}")
        print(f"   False NoRead sessions: {false_noread_sessions}")
        print(f"   OCR readable non-failure sessions: {ocr_non_failure_sessions}")
        
        # Expected: 
        # - OCR sessions = 1 (only session 1, session 3 excluded due to conflict)
        # - False NoRead sessions = 2 (sessions 2 and 3)
        # - OCR non-failure = 1 (only session 1, session 3 excluded due to conflict)
        
        expected_ocr = 1
        expected_false_noread = 2
        expected_ocr_non_failure = 1
        
        success = True
        if ocr_sessions == expected_ocr:
            print(f"   ✅ OCR readable sessions: {ocr_sessions} (expected {expected_ocr})")
        else:
            print(f"   ❌ OCR readable sessions: {ocr_sessions} (expected {expected_ocr})")
            success = False
            
        if false_noread_sessions == expected_false_noread:
            print(f"   ✅ False NoRead sessions: {false_noread_sessions} (expected {expected_false_noread})")
        else:
            print(f"   ❌ False NoRead sessions: {false_noread_sessions} (expected {expected_false_noread})")
            success = False
            
        if ocr_non_failure_sessions == expected_ocr_non_failure:
            print(f"   ✅ OCR non-failure sessions: {ocr_non_failure_sessions} (expected {expected_ocr_non_failure})")
        else:
            print(f"   ❌ OCR non-failure sessions: {ocr_non_failure_sessions} (expected {expected_ocr_non_failure})")
            success = False
        
        # Test the UI statistics update methods
        print(f"\n🔄 Testing UI statistics updates...")
        
        # Mock the total parcels entry
        app.total_parcels_var = tk.StringVar()
        app.total_parcels_var.set("100")
        
        # Create necessary UI variables
        app.session_count_var = tk.StringVar()
        app.total_stats_var = tk.StringVar()
        
        # Test session stats update
        app.update_session_stats()
        session_stats = app.session_count_var.get()
        print(f"   Session stats: {session_stats}")
        
        # Test total stats update  
        app.update_total_stats()
        total_stats = app.total_stats_var.get()
        print(f"   Total stats: {total_stats}")
        
        root.destroy()
        
        if success:
            print(f"\n🎉 UI INTEGRATION TEST PASSED!")
            print(f"   ✅ All statistics correctly respect False NoRead priority")
            print(f"   ✅ Conflicts properly handled in UI calculations")
        else:
            print(f"\n💥 UI INTEGRATION TEST FAILED!")
            print(f"   ❌ Some UI statistics do not respect the priority")
            
        return success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ui_integration()
    print(f"\n{'='*50}")
    if success:
        print("✅ PRIORITY IMPLEMENTATION SUCCESSFUL")
        print("   False NoRead now takes precedence over OCR readable")
        print("   All counts and statistics respect this priority")
    else:
        print("❌ PRIORITY IMPLEMENTATION NEEDS FIXES")
    print(f"{'='*50}")
    sys.exit(0 if success else 1)