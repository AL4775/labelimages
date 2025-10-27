# Double-Click Zoom Feature

## Version 2.2.0 - New Feature: Enhanced Double-Click Zoom

### Overview
The Aurora FIS Analytics Label Tool now includes intelligent double-click zoom functionality that provides a more intuitive way to zoom into and out of images.

### Features

#### Double-Click Zoom In
- **Action**: Double-click left mouse button on any area of the image
- **Effect**: Zooms in by 2x (200%) centered at the clicked location
- **Behavior**: 
  - If in "Fit to Window" mode, switches to 1:1 scale mode and applies 2x zoom
  - If already in 1:1 scale mode, increases current zoom level by 2x
  - Maximum zoom limit: 500% (5.0x)

#### Ctrl+Double-Click Zoom Out  
- **Action**: Hold Ctrl key + Double-click left mouse button
- **Effect**: Zooms out by 0.5x (50%) centered at the clicked location
- **Behavior**:
  - If in "Fit to Window" mode, switches to 1:1 scale mode and applies 0.5x zoom  
  - If already in 1:1 scale mode, decreases current zoom level by 0.5x
  - Minimum zoom limit: 10% (0.1x)

### Technical Implementation

#### Smart Centering
- The zoom operation centers the view on the exact pixel where you clicked
- Uses coordinate transformation to maintain the clicked point in the same relative position after zoom
- Automatically adjusts scroll position to keep the zoom target visible

#### Integration with Existing Features
- Works seamlessly with existing zoom controls (zoom buttons, mouse wheel)
- Preserves all existing pan and navigation functionality  
- Compatible with both "Fit to Window" and "1:1 Scale" display modes

#### Event Handling
- Double-click events are bound to the canvas: `<Double-Button-1>` and `<Control-Double-Button-1>`
- Returns "break" to prevent interference with existing click handlers
- Does not trigger text blinking (maintains smooth user experience)

### Usage Examples

#### Zooming into a Specific Detail
1. Find an area of interest in the image (e.g., a barcode, text region)
2. Double-click directly on that area
3. The image will zoom in 2x with that point centered in the view
4. Use scrollbars or mouse to pan around the zoomed view

#### Zooming Out from Current View
1. While zoomed in, hold Ctrl and double-click anywhere
2. The image will zoom out 0.5x while keeping the clicked point centered
3. Continue Ctrl+double-clicking to zoom out further

#### Combining with Other Controls
- Use mouse wheel for fine zoom adjustments
- Use "Fit to Window" button to return to fitted view
- Use "1:1 Scale" button to switch between display modes

### Code Changes

#### New Methods Added
- `double_click_zoom_in(event)`: Handles double-click zoom in
- `double_click_zoom_out(event)`: Handles Ctrl+double-click zoom out  
- `_perform_centered_zoom(event, zoom_factor)`: Core zoom logic with centering

#### Canvas Bindings Added
```python
self.canvas.bind("<Double-Button-1>", self.double_click_zoom_in)
self.canvas.bind("<Control-Double-Button-1>", self.double_click_zoom_out)
```

### Benefits
1. **Improved Workflow**: Faster access to detailed inspection of image regions
2. **Intuitive Interface**: Natural double-click behavior that users expect
3. **Precise Control**: Zoom exactly where you need to see more detail
4. **Consistent Experience**: Integrates smoothly with existing zoom controls
5. **Professional Feel**: Modern application behavior for enhanced user experience

### Compatibility
- Works on Windows with Python 3.9+
- Compatible with all existing image formats and features
- No impact on performance or memory usage
- Backward compatible with all existing functionality

This enhancement makes the image inspection workflow significantly more efficient and user-friendly.