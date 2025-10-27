#!/usr/bin/env python3
"""
Test script to verify that Analysis tab Performance metrics update when False NoRead checkbox changes
"""
import tkinter as tk
import image_label_tool

def test_analysis_tab_updates():
    """Test that checking/unchecking False NoRead updates Analysis tab performance metrics"""
    print("Testing Analysis tab Performance metrics updates with False NoRead...")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        # Initialize the application
        app = image_label_tool.ImageLabelTool(root)
        
        # Set up test data using proper filename patterns (ID_..._timestamp)
        app.all_image_paths = ['ID1_other_timestamp1.jpg', 'ID1_more_timestamp1.jpg', 'ID2_other_timestamp2.jpg']
        app.image_paths = app.all_image_paths.copy()
        app.labels = {
            'ID1_other_timestamp1.jpg': 'read failure',
            'ID1_more_timestamp1.jpg': 'read failure', 
            'ID2_other_timestamp2.jpg': 'read failure'
        }
        app.false_noread = {
            'ID1_other_timestamp1.jpg': False,  # Initially no False NoRead
            'ID1_more_timestamp1.jpg': False,
            'ID2_other_timestamp2.jpg': False
        }
        app.ocr_readable = {}
        app.comments = {}
        app.current_index = 0
        
        # Set total sessions to match our test data
        app.total_sessions_var.set('2')  # 2 sessions: ID1_timestamp1 and ID2_timestamp2
        
        print("=== Initial Test Setup ===")
        print("Session ID1_timestamp1: 2 images, both read failure, no False NoRead")
        print("Session ID2_timestamp2: 1 image, read failure, no False NoRead")
        print("Total sessions: 2")
        print()
        
        # Get initial performance metrics
        app.update_total_stats()
        initial_metrics = app.session_stats_var.get()
        print("Initial Performance Metrics:")
        print(initial_metrics)
        print()
        
        # Now simulate checking False NoRead for session 1
        print("=== Simulating False NoRead checkbox check for Session 1 ===")
        app.false_noread['ID1_other_timestamp1.jpg'] = True
        app.false_noread['ID1_more_timestamp1.jpg'] = True
        
        # Simulate the checkbox change event
        app.false_noread_var.set(True)
        app.on_false_noread_checkbox_changed()
        
        # Get updated performance metrics
        updated_metrics = app.session_stats_var.get()
        print("Updated Performance Metrics after False NoRead check:")
        print(updated_metrics)
        print()
        
        # Verify that metrics have changed
        if initial_metrics != updated_metrics:
            print("✅ SUCCESS: Performance metrics updated when False NoRead checkbox changed!")
        else:
            print("❌ FAILED: Performance metrics did not update")
            return False
            
        # Test unchecking False NoRead
        print("=== Simulating False NoRead checkbox uncheck ===")
        app.false_noread['ID1_other_timestamp1.jpg'] = False
        app.false_noread['ID1_more_timestamp1.jpg'] = False
        
        # Simulate the checkbox change event
        app.false_noread_var.set(False)
        app.on_false_noread_checkbox_changed()
        
        # Get reverted performance metrics
        reverted_metrics = app.session_stats_var.get()
        print("Reverted Performance Metrics after False NoRead uncheck:")
        print(reverted_metrics)
        print()
        
        # Verify that metrics reverted to initial state
        if reverted_metrics == initial_metrics:
            print("✅ SUCCESS: Performance metrics correctly reverted when False NoRead unchecked!")
        else:
            print("❌ FAILED: Performance metrics did not revert properly")
            print("Expected:")
            print(initial_metrics)
            print("Got:")
            print(reverted_metrics)
            return False
        
        # Test with multiple False NoRead sessions
        print("=== Testing Multiple False NoRead Sessions ===")
        app.false_noread['ID1_other_timestamp1.jpg'] = True
        app.false_noread['ID1_more_timestamp1.jpg'] = True
        app.false_noread['ID2_other_timestamp2.jpg'] = True
        
        app.false_noread_var.set(True)
        app.on_false_noread_checkbox_changed()
        
        multiple_metrics = app.session_stats_var.get()
        print("Performance Metrics with multiple False NoRead sessions:")
        print(multiple_metrics)
        print()
        
        # Verify this is different from single False NoRead
        if multiple_metrics != updated_metrics:
            print("✅ SUCCESS: Performance metrics correctly handle multiple False NoRead sessions!")
        else:
            print("❌ FAILED: Performance metrics did not change with multiple False NoRead sessions")
            return False
        
        print("\n🎉 All Analysis tab Performance metrics update tests passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_analysis_tab_updates()
    if success:
        print("\n✓ Analysis tab Performance metrics now update correctly when False NoRead checkbox changes!")
        print("\nFIX SUMMARY:")
        print("✅ Added sessions_false_noread calculation to update_total_stats()")
        print("✅ Updated net_numerator_excl_ocr formula to include False NoRead sessions")
        print("✅ Updated OCR improvement calculation to include False NoRead sessions")
        print("✅ on_false_noread_checkbox_changed() already calls update_total_stats()")
    else:
        print("\n❌ Implementation needs further fixes!")