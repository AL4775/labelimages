# Barcode Detection Logging

## Overview
The Image Label Tool now automatically logs all barcode detection activity to help you monitor and analyze the classification process.

## Log File Location
- **Directory**: `logs/` folder in the same directory as the application
- **Filename Format**: `barcode_detection_YYYYMMDD_HHMMSS.log`
- **Encoding**: UTF-8

## What Gets Logged

### 1. Session Information
- Session start/end markers
- Log file location
- Total images processed

### 2. Individual Image Processing
For each image, the log captures:
- **Filename**: Which image is being processed
- **Image dimensions**: Width x Height in pixels
- **Detection methods**: Results from both detection algorithms
- **Final result**: Total barcode count detected
- **Classification decision**: Whether classified as "no code" or "no read"

### 3. Auto-Classification Sessions
- Start time and summary statistics
- Progress through image batches
- Final counts (no code vs no read classifications)
- Session completion summaries

## Log Levels
- **INFO**: Normal operation (image processing, results, summaries)
- **DEBUG**: Detailed technical information (contour analysis, pattern detection)
- **WARNING**: Issues that don't prevent processing (unreadable images)
- **ERROR**: Serious problems that prevent detection

## Sample Log Entry
```
2025-09-17 21:02:36,758 - INFO - Starting barcode detection for: image001.jpg
2025-09-17 21:02:36,758 - INFO - Image dimensions: 1920x1080 pixels
2025-09-17 21:02:36,758 - INFO - Method 1 (Pattern Detection) found: 0 barcodes
2025-09-17 21:02:36,760 - INFO - Method 2 (Gradient Detection) found: 2 barcodes
2025-09-17 21:02:36,760 - INFO - ✓ DETECTION SUCCESS: 2 barcode(s) detected in image001.jpg
2025-09-17 21:02:36,761 - INFO - CLASSIFIED: image001.jpg → no read (barcode count: 2)
```

## Using the Logs
1. **Monitor Progress**: Watch real-time detection results during auto-classification
2. **Analyze Performance**: Review which images were detected vs missed
3. **Debug Issues**: Check detailed technical information for problematic images
4. **Audit Trail**: Complete record of all classification decisions

## Log File Management
- New log file created each time the application starts
- Log files are never automatically deleted
- You can safely delete old log files if needed
- Each log file is self-contained with complete session information

## Technical Details
- **Detection Method 1**: Morphological pattern analysis looking for rectangular barcode shapes
- **Detection Method 2**: Gradient-based edge detection for line patterns
- **Classification Logic**: 0 barcodes = "no code", 1+ barcodes = "no read"