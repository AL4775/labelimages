# Testing the Double-Click Zoom Feature

## How to Test the New Zoom Functionality

### Prerequisites
1. Run the Aurora FIS Analytics Label Tool (version 2.2.0+)
2. Load a folder containing images
3. Navigate to any image to test the zoom feature

### Test Cases

#### Test 1: Basic Double-Click Zoom In
1. **Action**: Double-click anywhere on the image
2. **Expected Result**: 
   - Image zooms in by 2x (200%)
   - The clicked point becomes the center of the new view
   - Mode switches to "1:1 Scale" if previously in "Fit to Window"
   - Scale info shows the new zoom level

#### Test 2: Ctrl+Double-Click Zoom Out
1. **Setup**: First zoom in using double-click (or zoom buttons)
2. **Action**: Hold Ctrl key and double-click anywhere on the image
3. **Expected Result**:
   - Image zooms out by 0.5x (50%)
   - The clicked point remains centered in the new view
   - Scale info shows the reduced zoom level

#### Test 3: Precise Area Targeting
1. **Action**: Find a small detail (like text or a barcode corner)
2. **Action**: Double-click exactly on that detail
3. **Expected Result**: 
   - The detail should be perfectly centered after zoom
   - You can inspect the area without needing to pan

#### Test 4: Multiple Zoom Operations
1. **Action**: Double-click to zoom in (2x)
2. **Action**: Double-click again on a different area (4x total)
3. **Action**: Ctrl+double-click to zoom out (2x)
4. **Expected Result**: Each operation should maintain smooth centering

#### Test 5: Mode Integration
1. **Setup**: Start in "Fit to Window" mode
2. **Action**: Double-click to zoom in
3. **Expected Result**: Should switch to "1:1 Scale" mode automatically
4. **Action**: Use "Fit to Window" button
5. **Action**: Double-click again
6. **Expected Result**: Should work from fitted mode again

#### Test 6: Zoom Limits
1. **Action**: Double-click repeatedly to zoom in
2. **Expected Result**: Should stop at 500% maximum zoom
3. **Action**: Ctrl+double-click repeatedly to zoom out
4. **Expected Result**: Should stop at 10% minimum zoom

#### Test 7: Integration with Other Controls
1. **Action**: Use double-click zoom to get to some zoom level
2. **Action**: Use mouse wheel to adjust zoom
3. **Action**: Use zoom buttons to adjust further
4. **Expected Result**: All controls should work together seamlessly

### Visual Confirmation

#### What You Should See:
- **Scale Info**: Updates immediately showing new zoom percentage
- **Scrollbars**: Appear when zoomed image is larger than canvas
- **Centered View**: Clicked point stays in the same screen position
- **Smooth Operation**: No flickering or visual artifacts

#### What Should NOT Happen:
- **No Text Blinking**: Status text should not blink during zoom operations
- **No Pan Interference**: Dragging should still work for panning after zoom
- **No Mode Conflicts**: Switching between modes should be smooth

### Performance Testing

#### Large Images:
1. Load a very large image (>2000x2000 pixels)
2. Test double-click zoom operations
3. **Expected**: Should remain responsive

#### Multiple Operations:
1. Perform 10+ rapid zoom in/out operations
2. **Expected**: Should remain smooth and responsive

### Error Cases to Check

#### Edge Cases:
1. **Double-click at image edge**: Should handle boundaries gracefully
2. **Zoom beyond limits**: Should respect min/max zoom constraints
3. **Very small images**: Should work with images smaller than canvas
4. **Rapid clicking**: Should not accumulate multiple zoom events

### Reporting Issues

If you encounter any problems:
1. Note the specific action performed
2. Record the zoom level before and after
3. Check if the clicked point remained centered
4. Verify the scale information display
5. Test if other zoom controls still work

### Success Criteria
✅ Double-click zooms in by exactly 2x  
✅ Ctrl+double-click zooms out by exactly 2x  
✅ Clicked point remains centered after zoom  
✅ Integration with existing controls works  
✅ Mode switching functions properly  
✅ Performance remains smooth  
✅ Zoom limits are respected  

The feature is working correctly when all these criteria are met!