### 1. 🟠 `read failure` (Highest Priority) 

- **Example**: Session has 10 "no label" images → Session = "no label"
- **Logic**: Physical/quality issues make the session unusable
- **Result**: **Entire session** = "unlabeled"
### 1. 🟠 `read failure` (Highest Priority) 
- **Trigger**: If **ANY** image is "read failure"
- **Result**: **Entire session** = "read failure"
- **Logic**: Processing issues
- **Example**: Session has 8 "no label", 2 "read failure" → Session = "read failure"

### 2. 🟢 `no label` (Second Priority)
- **Trigger**: If **ALL** images are "no label"
- **Result**: **Entire session** = "no label"
- **Logic**: Missing or blank labels but otherwise readable
- **Example**: Session has 10 "no label" images → Session = "no label"

### 3. 🔴 `unreadable` (Third Priority)
- **Trigger**: If **ANY** image in the session is classified as "unreadable" or "incomplete" and **NO** image is classified as "read failure"
- **Result**: **Entire session** = "unreadable" 
- **Logic**: Physical/quality issues make the session unusable
- **Example**: Session has 10 images - 9 are "no label", 1 is "incomplete" → Session = "unreadable"

### 4. ⚪ `unlabeled` (Default/Lowest Priority)
- **Trigger**: If **NO** images have been classified yet
- **Result**: **Entire session** = "unlabeled"
- **Logic**: Session hasn't been processed/reviewed yet
- **Example**: Session has 12 unclassified images → Session = "unlabeled"