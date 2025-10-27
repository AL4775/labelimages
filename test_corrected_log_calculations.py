#!/usr/bin/env python3
"""
Test script to verify the corrected False NoRead calculations in Log tab
"""
import tkinter as tk
import image_label_tool

def test_corrected_log_calculations():
    """Test the corrected formulas where False NoRead is added to successful reads"""
    print("Testing CORRECTED False NoRead calculations in Log tab...")
    
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
        
        # Expected calculation with CORRECTED formulas:
        # total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
        # total_readable_excl_ocr = 3 - 3 + 2 = 2
        # successful_reads_excl_ocr = total_readable_excl_ocr - sessions_read_failure + sessions_false_noread  
        # successful_reads_excl_ocr = 2 - 2 + 1 = 1
        
        total_entered = analysis_data.get('total_entered', 0)
        actual_sessions = analysis_data.get('actual_sessions', 0)
        sessions_read_failure = analysis_data.get('read_failure_count', 0)
        
        expected_total_readable = total_entered - actual_sessions + sessions_read_failure
        expected_successful_reads = max(0, expected_total_readable - sessions_read_failure + sessions_false_noread)
        
        print(f"\n=== Expected Calculations (CORRECTED) ===")
        print(f"total_readable_excl_ocr = {total_entered} - {actual_sessions} + {sessions_read_failure} = {expected_total_readable}")
        print(f"successful_reads_excl_ocr = {expected_total_readable} - {sessions_read_failure} + {sessions_false_noread} = {expected_successful_reads}")
        
        if expected_total_readable > 0:
            expected_rate = (expected_successful_reads / expected_total_readable) * 100
            print(f"Expected net read rate excl OCR: {expected_rate:.2f}%")
        else:
            print("Expected net read rate excl OCR: 0.00% (no readable sessions)")
        
        print(f"\n=== Actual Performance Results ===")
        print(f"Net read performance (excl OCR): {performance['excl_ocr']:.2f}%")
        print(f"Net read performance (incl OCR): {performance['incl_ocr']:.2f}%")
        
        # Verify the calculation matches expectation
        if expected_total_readable > 0:
            expected_performance = (expected_successful_reads / expected_total_readable) * 100
            assert abs(performance['excl_ocr'] - expected_performance) < 0.01, f"Expected {expected_performance:.2f}%, got {performance['excl_ocr']:.2f}%"
            print("✅ Performance calculation matches expected result")
        
        print("\n🎉 CORRECTED False NoRead calculations in Log tab are working correctly!")
        
        # Test edge case: multiple False NoRead sessions
        print("\n=== Edge Case Test: Multiple False NoRead Sessions ===")
        app.false_noread = {
            'ID1_other_timestamp1.jpg': True,  # Session 1 False NoRead
            'ID1_more_timestamp1.jpg': True,
            'ID2_other_timestamp2.jpg': True,  # Session 2 False NoRead
            'ID3_other_timestamp3.jpg': False
        }
        
        sessions_false_noread_multi = app.calculate_sessions_with_false_noread()
        print(f"Multiple sessions False NoRead: {sessions_false_noread_multi}")
        
        performance_multi = app.calculate_net_reading_performance(mock_log_results, app.get_analysis_data())
        print(f"Performance with multiple False NoRead sessions: {performance_multi['excl_ocr']:.2f}%")
        
        # Expected: successful_reads = 2 - 2 + 2 = 2, rate = 2/2 = 100%
        expected_multi = (2 / 2) * 100
        assert abs(performance_multi['excl_ocr'] - expected_multi) < 0.01, f"Expected {expected_multi:.2f}%, got {performance_multi['excl_ocr']:.2f}%"
        print("✅ Multiple False NoRead sessions calculation correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_corrected_log_calculations()
    if success:
        print("\n✓ Corrected Log tab False NoRead calculations are working correctly!")
        print("\nFORMULA SUMMARY:")
        print("✅ total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure")
        print("✅ successful_reads_excl_ocr = total_readable_excl_ocr - sessions_read_failure + sessions_false_noread")
    else:
        print("\n❌ Implementation needs fixes!")