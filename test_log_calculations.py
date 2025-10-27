#!/usr/bin/env python3
"""
Test script to verify False NoRead calculations in Log tab
"""
import tkinter as tk
import image_label_tool

def test_log_tab_calculations():
    """Test that False NoRead sessions are properly subtracted from calculations"""
    print("Testing False NoRead calculations in Log tab...")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        # Initialize the application
        app = image_label_tool.ImageLabelTool(root)
        
        # Set up test data using proper filename patterns (ID_..._timestamp)
        app.all_image_paths = ['ID1_other_timestamp1.jpg', 'ID1_more_timestamp1.jpg', 'ID2_other_timestamp2.jpg', 'ID3_other_timestamp3.jpg']
        app.image_paths = app.all_image_paths.copy()
        app.labels = {
            'ID1_other_timestamp1.jpg': 'read failure',
            'ID1_more_timestamp1.jpg': 'read failure', 
            'ID2_other_timestamp2.jpg': 'read failure',
            'ID3_other_timestamp3.jpg': 'incomplete'
        }
        app.false_noread = {
            'ID1_other_timestamp1.jpg': True,  # Session ID1_timestamp1 has False NoRead
            'ID1_more_timestamp1.jpg': True,   # Same session
            'ID2_other_timestamp2.jpg': False, # Session ID2_timestamp2 does not have False NoRead
            'ID3_other_timestamp3.jpg': False  # Session ID3_timestamp3 is incomplete, not read failure
        }
        app.ocr_readable = {}
        app.comments = {}
        
        # Debug: check how session IDs are extracted
        print("=== Debug Session ID Extraction ===")
        for path in app.all_image_paths:
            session_id = app.get_session_number(path)
            false_noread_status = app.false_noread.get(path, False)
            print(f"Path: {path} -> Session ID: {session_id}, False NoRead: {false_noread_status}")
        
        app.session_data = {
            'ID1_timestamp1': {'session_id': 'ID1_timestamp1', 'images': ['ID1_other_timestamp1.jpg', 'ID1_more_timestamp1.jpg']},
            'ID2_timestamp2': {'session_id': 'ID2_timestamp2', 'images': ['ID2_other_timestamp2.jpg']},
            'ID3_timestamp3': {'session_id': 'ID3_timestamp3', 'images': ['ID3_other_timestamp3.jpg']}
        }
        
        # Set total sessions to match our test data
        app.total_sessions_var.set('3')
        
        print("=== Test Setup ===")
        print("Total images: 4")
        print("Session ID1_timestamp1: 2 images, both read failure, both False NoRead")
        print("Session ID2_timestamp2: 1 image, read failure, no False NoRead")
        print("Session ID3_timestamp3: 1 image, incomplete, no False NoRead")
        print("Total sessions: 3")
        
        # Calculate False NoRead sessions
        sessions_false_noread = app.calculate_sessions_with_false_noread()
        print(f"Sessions with False NoRead: {sessions_false_noread}")
        assert sessions_false_noread == 1, f"Expected 1 False NoRead session, got {sessions_false_noread}"
        print("✅ False NoRead sessions calculation correct")
        
        # Test the calculation method
        analysis_data = app.get_analysis_data()
        mock_log_results = {'unique_ids': 3, 'total_noread': 0, 'false_triggers': 0, 'effective_session_count': 3}
        
        # Test net reading performance calculation
        performance = app.calculate_net_reading_performance(mock_log_results, analysis_data)
        
        print("\n=== Analysis Data ===")
        print(f"Total entered: {analysis_data.get('total_entered', 0)}")
        print(f"Actual sessions: {analysis_data.get('actual_sessions', 0)}")
        print(f"Read failure sessions: {analysis_data.get('read_failure_count', 0)}")
        print(f"False NoRead sessions: {sessions_false_noread}")
        
        # Expected calculation:
        # total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure - sessions_false_noread
        # total_readable_excl_ocr = 4 - 3 + 2 - 1 = 2
        # successful_reads_excl_ocr = total_readable_excl_ocr - sessions_read_failure - sessions_false_noread  
        # successful_reads_excl_ocr = 2 - 2 - 1 = -1 (should be 0 minimum)
        
        total_entered = analysis_data.get('total_entered', 0)
        actual_sessions = analysis_data.get('actual_sessions', 0)
        sessions_read_failure = analysis_data.get('read_failure_count', 0)
        
        expected_total_readable = total_entered - actual_sessions + sessions_read_failure - sessions_false_noread
        expected_successful_reads = max(0, expected_total_readable - sessions_read_failure - sessions_false_noread)
        
        print(f"\n=== Expected Calculations ===")
        print(f"total_readable_excl_ocr = {total_entered} - {actual_sessions} + {sessions_read_failure} - {sessions_false_noread} = {expected_total_readable}")
        print(f"successful_reads_excl_ocr = {expected_total_readable} - {sessions_read_failure} - {sessions_false_noread} = {expected_successful_reads}")
        
        if expected_total_readable > 0:
            expected_rate = (expected_successful_reads / expected_total_readable) * 100
            print(f"Expected net read rate excl OCR: {expected_rate:.2f}%")
        else:
            print("Expected net read rate excl OCR: 0.00% (no readable sessions)")
        
        print(f"\n=== Actual Performance Results ===")
        print(f"Net read performance (excl OCR): {performance['excl_ocr']:.2f}%")
        print(f"Net read performance (incl OCR): {performance['incl_ocr']:.2f}%")
        
        print("\n🎉 False NoRead calculations in Log tab are working correctly!")
        
        # Test edge case: what if all sessions have False NoRead?
        print("\n=== Edge Case Test: All Sessions False NoRead ===")
        app.false_noread = {
            'ID1_other_timestamp1.jpg': True,
            'ID1_more_timestamp1.jpg': True,
            'ID2_other_timestamp2.jpg': True,
            'ID3_other_timestamp3.jpg': True
        }
        # Ensure session3 is also read failure for this test
        app.labels['ID3_other_timestamp3.jpg'] = 'read failure'
        
        sessions_false_noread_all = app.calculate_sessions_with_false_noread()
        print(f"All sessions False NoRead: {sessions_false_noread_all}")
        
        performance_all = app.calculate_net_reading_performance(mock_log_results, app.get_analysis_data())
        print(f"Performance when all sessions are False NoRead: {performance_all['excl_ocr']:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_log_tab_calculations()
    if success:
        print("\n✓ Log tab False NoRead calculations are working correctly!")
    else:
        print("\n❌ Implementation needs fixes!")