#!/usr/bin/env python3
"""
Test script to verify that centralized net rate calculations work correctly
"""
import tkinter as tk
import image_label_tool

def test_centralized_calculations():
    """Test that centralized calculations produce the same results as before"""
    print("Testing centralized net rate calculations...")
    
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
            'ID2_other_timestamp2.jpg': 'incomplete',
            'ID3_other_timestamp3.jpg': 'no label'
        }
        app.false_noread = {
            'ID1_other_timestamp1.jpg': True,  # Session ID1_timestamp1 has False NoRead
            'ID1_more_timestamp1.jpg': True,   # Same session
            'ID2_other_timestamp2.jpg': False,
            'ID3_other_timestamp3.jpg': False
        }
        app.ocr_readable = {
            'ID2_other_timestamp2.jpg': True,  # Session ID2_timestamp2 has OCR readable
            'ID3_other_timestamp3.jpg': True   # Session ID3_timestamp3 has OCR readable
        }
        app.comments = {}
        app.current_index = 0
        
        # Set total sessions
        app.total_sessions_var.set('4')  # 3 actual sessions + 1 missing
        
        print("=== Test Data Setup ===")
        print("Session ID1_timestamp1: 2 images, read failure, False NoRead")
        print("Session ID2_timestamp2: 1 image, incomplete, OCR readable")
        print("Session ID3_timestamp3: 1 image, no label, OCR readable")
        print("Total entered sessions: 4")
        print("Actual sessions: 3")
        print()
        
        # Test centralized calculation directly
        total_entered = 4
        actual_sessions = 3
        sessions_read_failure = 1  # ID1_timestamp1
        sessions_false_noread = 1  # ID1_timestamp1
        sessions_ocr_readable = 2  # ID2_timestamp2, ID3_timestamp3
        sessions_ocr_readable_non_failure = 2  # Both OCR sessions are not read failure
        
        print("=== Testing Centralized Calculation ===")
        net_rates = app.calculate_net_rates_centralized(
            total_entered, actual_sessions, sessions_read_failure,
            sessions_false_noread, sessions_ocr_readable, sessions_ocr_readable_non_failure
        )
        
        print(f"Total readable excl OCR: {net_rates['total_readable_excl_ocr']}")
        print(f"Total readable incl OCR: {net_rates['total_readable_incl_ocr']}")
        print(f"Successful reads excl OCR: {net_rates['successful_reads_excl_ocr']}")
        print(f"Successful reads incl OCR: {net_rates['successful_reads_incl_ocr']}")
        print(f"Net rate excl OCR: {net_rates['net_rate_excl_ocr']:.2f}%")
        print(f"Net rate incl OCR: {net_rates['net_rate_incl_ocr']:.2f}%")
        print(f"OCR improvement: {net_rates['ocr_improvement_percentage']:.2f}%")
        print()
        
        # Expected calculations:
        # total_readable_excl_ocr = 4 - 3 + 1 = 2
        # total_readable_incl_ocr = 2 + 2 = 4
        # successful_reads_excl_ocr = 2 - 1 + 1 = 2
        # successful_reads_incl_ocr = 2 + 2 = 4
        # net_rate_excl_ocr = 2/2 = 100%
        # net_rate_incl_ocr = 4/4 = 100%
        # ocr_improvement = (4-2)/2 * 100 = 100%
        
        expected = {
            'total_readable_excl_ocr': 2,
            'total_readable_incl_ocr': 4,
            'successful_reads_excl_ocr': 2,
            'successful_reads_incl_ocr': 4,
            'net_rate_excl_ocr': 100.0,
            'net_rate_incl_ocr': 100.0,
            'ocr_improvement_percentage': 100.0
        }
        
        print("=== Verification ===")
        all_correct = True
        for key, expected_value in expected.items():
            actual_value = net_rates[key]
            if abs(actual_value - expected_value) < 0.01:  # Allow for floating point precision
                print(f"✅ {key}: {actual_value} (expected {expected_value})")
            else:
                print(f"❌ {key}: {actual_value} (expected {expected_value})")
                all_correct = False
        
        if not all_correct:
            return False
        
        # Test that Analysis tab uses centralized calculation
        print("\n=== Testing Analysis Tab Integration ===")
        app.update_total_stats()
        analysis_metrics = app.session_stats_var.get()
        print("Analysis tab metrics:")
        print(analysis_metrics)
        
        # Check that the metrics contain the expected values
        if "100.00%" in analysis_metrics and "Net read rate (excl. OCR)" in analysis_metrics:
            print("✅ Analysis tab correctly uses centralized calculations")
        else:
            print("❌ Analysis tab not using centralized calculations correctly")
            return False
        
        # Test that Log tab functions still work
        print("\n=== Testing Log Tab Integration ===")
        analysis_data = app.get_analysis_data()
        mock_log_results = {'unique_ids': 3, 'total_noread': 0, 'false_triggers': 0, 'effective_session_count': 3}
        
        performance = app.calculate_net_reading_performance(mock_log_results, analysis_data)
        print(f"Log tab net reading performance:")
        print(f"  Excl OCR: {performance['excl_ocr']:.2f}%")
        print(f"  Incl OCR: {performance['incl_ocr']:.2f}%")
        
        # Should match centralized calculation
        if abs(performance['excl_ocr'] - net_rates['net_rate_excl_ocr']) < 0.01:
            print("✅ Log tab correctly uses centralized calculations")
        else:
            print("❌ Log tab not using centralized calculations correctly")
            return False
        
        print("\n🎉 All centralized calculation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_centralized_calculations()
    if success:
        print("\n✓ Centralized net rate calculations are working correctly!")
        print("\nCENTRALIZATION BENEFITS:")
        print("✅ Single source of truth for net rate calculations")
        print("✅ Consistent formulas across Analysis tab and Log tab")
        print("✅ Easier maintenance and updates")
        print("✅ Reduced code duplication")
        print("✅ Better testability")
    else:
        print("\n❌ Centralization needs fixes!")