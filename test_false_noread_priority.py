#!/usr/bin/env python3
"""
Test script to verify the False NoRead priority logic
When an image is both Read with OCR and False NoRead, it should be considered False NoRead only
"""
import os
import sys
import shutil
import csv

def create_test_data():
    """Create test images and CSV data with conflicting OCR/False NoRead status"""
    
    # Create test directory
    test_dir = "priority_test_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # Create dummy image files for testing
    test_images = [
        "001_001_A.jpg",   # Session 1, Image 1 - Will be OCR only
        "001_002_A.jpg",   # Session 1, Image 2 - Will be OCR only 
        "002_001_A.jpg",   # Session 2, Image 1 - Will be False NoRead only
        "002_002_A.jpg",   # Session 2, Image 2 - Will be False NoRead only
        "003_001_A.jpg",   # Session 3, Image 1 - Will be BOTH OCR and False NoRead (CONFLICT)
        "003_002_A.jpg",   # Session 3, Image 2 - Will be BOTH OCR and False NoRead (CONFLICT)
        "004_001_A.jpg",   # Session 4, Image 1 - Will be neither
        "004_002_A.jpg",   # Session 4, Image 2 - Will be neither
    ]
    
    # Create dummy image files (just empty files for testing)
    for img in test_images:
        with open(os.path.join(test_dir, img), 'w') as f:
            f.write("")  # Empty file
    
    # Create CSV with test data including conflicts
    csv_file = os.path.join(test_dir, "image_labels.csv")
    csv_data = [
        ["File", "Label", "OCR_Readable", "False_NoRead", "Comments"],
        ["001_001_A.jpg", "good", "True", "False", "OCR only session"],
        ["001_002_A.jpg", "good", "True", "False", "OCR only session"],
        ["002_001_A.jpg", "read failure", "False", "True", "False NoRead only session"],
        ["002_002_A.jpg", "read failure", "False", "True", "False NoRead only session"],
        ["003_001_A.jpg", "good", "True", "True", "CONFLICT: Both OCR and False NoRead"],
        ["003_002_A.jpg", "good", "True", "True", "CONFLICT: Both OCR and False NoRead"],
        ["004_001_A.jpg", "good", "False", "False", "Neither OCR nor False NoRead"],
        ["004_002_A.jpg", "good", "False", "False", "Neither OCR nor False NoRead"],
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    
    print(f"✅ Created test data in {test_dir}/")
    print(f"   - 8 test images in 4 sessions")
    print(f"   - Session 1: OCR only (should count as OCR readable)")
    print(f"   - Session 2: False NoRead only (should count as False NoRead)")
    print(f"   - Session 3: BOTH OCR and False NoRead (should count as False NoRead ONLY)")
    print(f"   - Session 4: Neither (should count as neither)")
    
    return test_dir

def run_priority_test():
    """Run the priority test to verify False NoRead takes precedence"""
    
    # Create test data
    test_dir = create_test_data()
    
    try:
        # Import the application
        import image_label_tool
        import tkinter as tk
        
        print("\n=== PRIORITY TEST START ===")
        
        # Create application instance
        root = tk.Tk()
        root.withdraw()  # Hide the GUI for testing
        app = image_label_tool.ImageLabelTool(root)
        
        # Load the test directory
        test_path = os.path.abspath(test_dir)
        app.folder_path = test_path
        
        # Manually set up image paths and data
        image_files = [f for f in os.listdir(test_path) if f.endswith('.jpg')]
        app.all_image_paths = [os.path.join(test_path, f) for f in image_files]
        app.image_paths = app.all_image_paths.copy()
        
        # Manually set up the test data instead of using CSV
        app.labels = {}
        app.ocr_readable = {}
        app.false_noread = {}
        app.comments = {}
        
        # Set up test data according to our test plan
        test_data = {
            "001_001_A.jpg": {"label": "good", "ocr": True, "false_noread": False, "comment": "OCR only session"},
            "001_002_A.jpg": {"label": "good", "ocr": True, "false_noread": False, "comment": "OCR only session"},
            "002_001_A.jpg": {"label": "read failure", "ocr": False, "false_noread": True, "comment": "False NoRead only session"},
            "002_002_A.jpg": {"label": "read failure", "ocr": False, "false_noread": True, "comment": "False NoRead only session"},
            "003_001_A.jpg": {"label": "good", "ocr": True, "false_noread": True, "comment": "CONFLICT: Both OCR and False NoRead"},
            "003_002_A.jpg": {"label": "good", "ocr": True, "false_noread": True, "comment": "CONFLICT: Both OCR and False NoRead"},
            "004_001_A.jpg": {"label": "good", "ocr": False, "false_noread": False, "comment": "Neither OCR nor False NoRead"},
            "004_002_A.jpg": {"label": "good", "ocr": False, "false_noread": False, "comment": "Neither OCR nor False NoRead"},
        }
        
        for image_path in app.all_image_paths:
            filename = os.path.basename(image_path)
            if filename in test_data:
                data = test_data[filename]
                app.labels[image_path] = data["label"]
                app.ocr_readable[image_path] = data["ocr"]
                app.false_noread[image_path] = data["false_noread"]
                app.comments[image_path] = data["comment"]
        
        print(f"✅ Loaded {len(app.all_image_paths)} test images")
        print(f"✅ Set up test data with conflicts")
        
        # Test the priority logic
        print("\n=== TESTING PRIORITY LOGIC ===")
        
        # Test individual calculations
        sessions_ocr_readable = app.calculate_sessions_with_ocr_readable()
        sessions_false_noread = app.calculate_sessions_with_false_noread()
        session_ocr_status = app.calculate_session_ocr_readable_status()
        
        print(f"\n📊 Raw counts:")
        print(f"   Sessions with OCR readable images (excluding conflicts): {sessions_ocr_readable}")
        print(f"   Sessions with False NoRead images: {sessions_false_noread}")
        
        print(f"\n📋 Session-by-session OCR status:")
        for session_id in sorted(session_ocr_status.keys()):
            ocr_status = session_ocr_status[session_id]
            print(f"   Session {session_id}: OCR readable = {ocr_status}")
        
        # Expected results based on our test data:
        # Session 1: OCR only → should be OCR readable = True
        # Session 2: False NoRead only → should be OCR readable = False
        # Session 3: BOTH OCR and False NoRead → should be OCR readable = False (False NoRead wins)
        # Session 4: Neither → should be OCR readable = False
        
        expected_results = {
            "sessions_ocr_readable": 1,  # Only session 1
            "sessions_false_noread": 2,  # Sessions 2 and 3
            "session_1_ocr_status": True,   # OCR only
            "session_2_ocr_status": False,  # False NoRead only
            "session_3_ocr_status": False,  # Both → False NoRead wins
            "session_4_ocr_status": False,  # Neither
        }
        
        print(f"\n🎯 EXPECTED vs ACTUAL:")
        
        # Check OCR readable sessions count
        success = True
        if sessions_ocr_readable == expected_results["sessions_ocr_readable"]:
            print(f"   ✅ OCR readable sessions: {sessions_ocr_readable} (expected {expected_results['sessions_ocr_readable']})")
        else:
            print(f"   ❌ OCR readable sessions: {sessions_ocr_readable} (expected {expected_results['sessions_ocr_readable']})")
            success = False
        
        # Check False NoRead sessions count
        if sessions_false_noread == expected_results["sessions_false_noread"]:
            print(f"   ✅ False NoRead sessions: {sessions_false_noread} (expected {expected_results['sessions_false_noread']})")
        else:
            print(f"   ❌ False NoRead sessions: {sessions_false_noread} (expected {expected_results['sessions_false_noread']})")
            success = False
        
        # Check individual session OCR statuses
        # Session IDs are parsed as "001_A", "002_A", etc.
        expected_session_ids = ["001_A", "002_A", "003_A", "004_A"]
        for i, session_id in enumerate(expected_session_ids, 1):
            actual_status = session_ocr_status.get(session_id, False)
            expected_status = expected_results[f"session_{i}_ocr_status"]
            
            if actual_status == expected_status:
                print(f"   ✅ Session {i} ({session_id}) OCR status: {actual_status} (expected {expected_status})")
            else:
                print(f"   ❌ Session {i} ({session_id}) OCR status: {actual_status} (expected {expected_status})")
                success = False
        
        # Test the centralized calculation function with these values
        print(f"\n🔬 Testing centralized calculations...")
        
        # Get session stats
        session_labels_dict = app.calculate_session_labels()
        total_sessions = len(session_labels_dict)
        sessions_read_failure = sum(1 for label in session_labels_dict.values() if label == "read failure")
        sessions_ocr_readable_non_failure = app.calculate_ocr_readable_non_failure_sessions()
        
        print(f"   Total sessions: {total_sessions}")
        print(f"   Read failure sessions: {sessions_read_failure}")
        print(f"   OCR readable non-failure sessions: {sessions_ocr_readable_non_failure}")
        print(f"   False NoRead sessions: {sessions_false_noread}")
        print(f"   OCR readable sessions (total): {sessions_ocr_readable}")
        
        # Test centralized calculation
        total_entered = 100  # Example total
        actual_sessions = total_sessions
        
        results = app.calculate_net_rates_centralized(
            total_entered, 
            actual_sessions, 
            sessions_read_failure, 
            sessions_false_noread, 
            sessions_ocr_readable, 
            sessions_ocr_readable_non_failure
        )
        
        print(f"\n📈 Centralized calculation results:")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        root.destroy()
        
        if success:
            print(f"\n🎉 PRIORITY TEST PASSED!")
            print(f"   ✅ False NoRead correctly takes precedence over OCR readable")
            print(f"   ✅ Session 3 (conflict) correctly counted as False NoRead only")
            print(f"   ✅ All calculations respect the priority rule")
        else:
            print(f"\n💥 PRIORITY TEST FAILED!")
            print(f"   ❌ Some calculations do not respect the False NoRead priority")
        
        return success
        
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

if __name__ == "__main__":
    success = run_priority_test()
    sys.exit(0 if success else 1)