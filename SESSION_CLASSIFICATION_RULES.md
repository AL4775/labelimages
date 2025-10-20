# Session Classification Decision Rules

## Core Principle: "Worst Case Wins"
The session classification follows a **hierarchical priority system** where the most severe problem determines the entire session's classification.

## Classification Hierarchy (Most to Least Severe)

### 1. 🔴 `unreadable` (Highest Priority)
- **Trigger**: If **ANY** image in the session is classified as "unreadable"
- **Result**: **Entire session** = "unreadable" 
- **Logic**: Physical/quality issues make the session unusable
- **Example**: Session has 10 images - 9 are "no label", 1 is "unreadable" → Session = "unreadable"

### 2. 🟠 `read failure` (Second Priority) 
- **Trigger**: If **ANY** image is "read failure" AND no "unreadable" images exist
- **Result**: **Entire session** = "read failure"
- **Logic**: Technical scanning/processing issues
- **Example**: Session has 8 "no label", 2 "read failure" → Session = "read failure"

### 3. 🟡 `incomplete` (Third Priority)
- **Trigger**: If **ANY** image is "incomplete" AND no worse classifications exist
- **Result**: **Entire session** = "incomplete" 
- **Logic**: Partial data capture issues
- **Example**: Session has 5 "no label", 3 "incomplete" → Session = "incomplete"

### 4. 🟢 `no label` (Fourth Priority)
- **Trigger**: If **ANY** image is "no label" AND no worse classifications exist
- **Result**: **Entire session** = "no label"
- **Logic**: Missing or blank labels but otherwise readable
- **Example**: Session has 10 "no label" images → Session = "no label"

### 5. ⚪ `unlabeled` (Default/Lowest Priority)
- **Trigger**: If **NO** images have been classified yet
- **Result**: **Entire session** = "unlabeled"
- **Logic**: Session hasn't been processed/reviewed yet
- **Example**: Session has 12 unclassified images → Session = "unlabeled"

## Key Decision Logic

### Single Bad Image Rule
- **One bad apple spoils the bunch**: Even if 99 images are perfect and 1 is "unreadable", the entire session becomes "unreadable"

### Priority Override
- Higher priority classifications **always override** lower ones
- No mixing or averaging - it's binary decision making

### Practical Examples

| Images in Session | Session Classification | Reason |
|-------------------|----------------------|---------|
| 5 × "no label" | `no label` | All same category |
| 4 × "no label" + 1 × "incomplete" | `incomplete` | Incomplete overrides no label |
| 3 × "no label" + 2 × "read failure" | `read failure` | Read failure overrides no label |
| 8 × "no label" + 1 × "unreadable" | `unreadable` | Unreadable overrides everything |
| 2 × "incomplete" + 1 × "read failure" + 1 × "unreadable" | `unreadable` | Highest priority wins |
| 10 × unclassified | `unlabeled` | Nothing classified yet |

## Business Logic Reasoning

This hierarchy reflects **operational severity**:
- **Unreadable**: Complete data loss - highest business impact
- **Read Failure**: Technical issues - needs system intervention  
- **Incomplete**: Partial data - some value recoverable
- **No Label**: Readable but missing metadata - lowest impact
- **Unlabeled**: Unknown state - needs review

The system ensures **conservative classification** where any quality issue escalates the entire session to reflect the worst-case scenario for business decisions.
