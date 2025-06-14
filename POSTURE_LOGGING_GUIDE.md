# Posture Logging System Guide

## Overview

The enhanced `main_webcam.py` now includes a comprehensive posture logging system that continuously monitors and records your posture data. This system provides detailed analytics and helps you track your posture habits over time.

## Features

### 🎯 Core Functionality
- **Continuous Monitoring**: Captures posture status every 3 seconds
- **Rolling Window Analysis**: Maintains a 2-minute sliding window of data
- **Dual Logging System**: 
  - **Detailed Log** (`posture_log.json`): Complete data with all individual readings
  - **Summary Log** (`posture_summary.json`): Clean window summaries only
- **Real-time Statistics**: Displays current window stats on screen
- **Background Processing**: Logging runs independently of display

### 📊 Data Collection
- **Individual Readings**: Every 3 seconds
  - Timestamp and datetime
  - Good posture vs slouching classification
  - Posture ratio (nose-to-shoulder distance relative to shoulder width)
  - Additional metrics (FPS, landmark positions, distances)

- **Window Aggregates**: Every 2 minutes
  - Total readings in window
  - Count of good posture vs slouching instances
  - Percentages and averages
  - Complete history of individual readings

## How to Use

### 1. Running the System
```bash
python main_webcam.py
```

### 2. Keyboard Controls
- `q` - Quit application
- `s` - Show/hide landmark positions
- `r` - Reset pose detector
- `p` - Toggle posture detection
- `l` - **Toggle logging on/off**

### 3. On-Screen Information
The system displays:
- Current posture status (GOOD POSTURE / SLOUCHING)
- Logging status (ON/OFF)
- 2-minute window summary (e.g., "5G/2S" = 5 good, 2 slouching)
- Good posture percentage for current window

## Log File Structure

### `posture_log.json` Format
```json
{
  "metadata": {
    "created": "2024-01-15T10:30:00.000000",
    "log_interval_seconds": 3.0,
    "window_duration_seconds": 120.0,
    "description": "Continuous posture monitoring log"
  },
  "logs": [
    {
      "window_end_time": "2024-01-15T10:32:00.000000",
      "window_duration_minutes": 2.0,
      "total_readings": 40,
      "good_posture_count": 32,
      "slouching_count": 8,
      "good_posture_percentage": 80.0,
      "slouching_percentage": 20.0,
      "average_posture_ratio": 0.542,
      "readings": [
        {
          "timestamp": 1705312320.123,
          "datetime": "2024-01-15T10:32:00.123000",
          "is_good_posture": true,
          "posture_status": "good",
          "posture_ratio": 0.567,
          "additional_data": {
            "fps": 28,
            "shoulder_width": 145,
            "posture_distance": 82.3,
            "nose_position": [320, 180],
            "left_shoulder": [250, 220],
            "right_shoulder": [395, 215]
          }
        }
      ]
    }
  ]
}
```

## Data Analysis

### Using the Analysis Tools

**For Summary Analysis (Recommended)**:
```bash
python analyze_posture_summary.py
```

**For Detailed Analysis**:
```bash
python analyze_posture_log.py
```

The summary analysis tool provides:
- **Overall Statistics**: Total readings, percentages, trends
- **Best/Worst Windows**: Identifies your best and worst 2-minute periods
- **Recent Trends**: Shows patterns in your last 10 windows
- **Hourly Breakdown**: Posture patterns by hour (if enough data)
- **Recommendations**: Personalized feedback based on your data
- **CSV Export**: Export data for external analysis
- **Performance**: Fast analysis without loading individual readings

### Sample Analysis Output
```
📊 POSTURE LOG ANALYSIS
==================================================
📋 Log Information:
   - Created: 2024-01-15T10:30:00.000000
   - Log Interval: 3.0 seconds
   - Window Duration: 120.0 seconds

📈 Found 15 2-minute window entries

🎯 OVERALL STATISTICS:
   - Total Readings: 600
   - Good Posture: 480 (80.0%)
   - Slouching: 120 (20.0%)

✅ BEST 2-MINUTE WINDOW:
   - Time: 2024-01-15T11:15:00.000000
   - Good Posture: 95.0%
   - Readings: 38G/2S

❌ WORST 2-MINUTE WINDOW:
   - Time: 2024-01-15T11:45:00.000000
   - Good Posture: 45.0%
   - Readings: 18G/22S

💡 RECOMMENDATIONS:
   👍 Good posture overall, but there's room for improvement.
```

## Configuration Options

### Customizing Logging Parameters
You can modify these settings in `main_webcam.py`:

```python
# Initialize posture logger
posture_logger = PostureLogger(
    log_interval=3.0,      # Log every 3 seconds (can be 2-4 seconds)
    window_duration=120.0,  # 2-minute rolling window (120 seconds)
    log_file="posture_log.json"  # Custom log file name
)
```

### Posture Detection Sensitivity
```python
posture_threshold_percentage = 0.45  # Adjust sensitivity (0.3-0.6 typical range)
```

## Technical Implementation

### PostureLogger Class Features
- **Rolling Buffer**: Uses `collections.deque` for efficient window management
- **Automatic Cleanup**: Removes old readings outside the time window
- **Graceful Error Handling**: Continues logging even if file I/O fails
- **Structured Data**: Maintains consistent JSON format
- **Memory Efficient**: Only keeps current window data in memory

### Integration Points
1. **Initialization**: Logger created alongside pose detector
2. **Detection Loop**: Logging triggered based on timing intervals
3. **Data Collection**: Captures comprehensive posture metrics
4. **Real-time Display**: Shows current statistics on video feed
5. **User Control**: Toggle logging with keyboard shortcut

## Troubleshooting

### Common Issues
1. **Log File Not Created**
   - Ensure write permissions in the directory
   - Check if disk space is available

2. **Missing Data**
   - Verify logging is enabled (press 'l' to toggle)
   - Check that posture detection is active (press 'p' to toggle)

3. **Analysis Script Errors**
   - Ensure `posture_log.json` exists and has data
   - Run the webcam system for at least 2 minutes to generate logs

### File Locations
- **Main Application**: `main_webcam.py`
- **Detailed Log**: `posture_log.json` (complete data with individual readings)
- **Summary Log**: `posture_summary.json` (clean window summaries only)
- **Detailed Analysis Tool**: `analyze_posture_log.py`
- **Summary Analysis Tool**: `analyze_posture_summary.py` (recommended)

## Best Practices

### For Accurate Logging
1. **Consistent Position**: Maintain similar distance from camera
2. **Good Lighting**: Ensure face and shoulders are clearly visible
3. **Stable Setup**: Minimize camera movement during sessions
4. **Regular Analysis**: Review your data weekly to identify patterns

### For Long-term Tracking
1. **Daily Sessions**: Run 30-60 minute sessions for meaningful data
2. **Backup Logs**: Periodically save your `posture_log.json` files
3. **Trend Analysis**: Compare weekly/monthly averages
4. **Environment Notes**: Consider factors like chair, desk height, time of day

## Data Privacy

- **Local Storage**: All data remains on your device
- **No Network**: No data transmitted over internet
- **User Control**: Complete control over data collection and deletion
- **Transparency**: Open source implementation for full visibility

---

*This logging system provides valuable insights into your posture habits and helps you maintain better ergonomic practices throughout your day.* 