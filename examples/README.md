# Example Image Naming

This directory would contain example images demonstrating the required naming convention.

## Required Format: `basename_number.extension`

### ✅ Valid Examples:
- `document_1.jpg`
- `page_001.png`
- `scan_25.jpeg`
- `photo_123.bmp`
- `image_999.gif`

### ❌ Invalid Examples:
- `document.jpg` (missing number)
- `page_a.png` (letter instead of number)
- `scan-25.jpeg` (dash instead of underscore)
- `photo_1_2.jpg` (multiple underscores with numbers)

## Parcel Grouping

Images with the same number form a parcel:

**Parcel 1:**
- `document_1.jpg`
- `page_1.png`
- `scan_1.jpeg`

**Parcel 25:**
- `document_25.jpg`
- `page_25.png`

**Parcel 123:**
- `image_123.jpg`
- `photo_123.png`

## To Test the Tool:

1. Create a test folder
2. Add images following the naming convention above
3. Use the Image Label Tool to select this folder
4. Verify that images are properly grouped into parcels