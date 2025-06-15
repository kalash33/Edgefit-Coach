#!/usr/bin/env python3
"""
Headless version of main_webcam.py for API server usage.
Runs posture detection without GUI display.
"""

import cv2
import mediapipe as mp
import time
import os
import numpy as np
import json
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional
import threading
import signal
import sys
from llm_handler import ask_llm, is_error_response

# ONNX Runtime imports for optimized model inference
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️  ONNX Runtime not available, falling back to standard inference")

# Import all the detection functions from main_webcam.py
def detect_overhead_reach(lmList):
    """Detect overhead reach stretching exercise."""
    if len(lmList) < 17:
        return False
    
    l_shoulder = lmList[11]
    r_shoulder = lmList[12]
    l_elbow = lmList[13]
    r_elbow = lmList[14]
    l_wrist = lmList[15]
    r_wrist = lmList[16]
    
    # Calculate reference points
    shoulder_width = abs(r_shoulder[1] - l_shoulder[1])
    avg_shoulder_y = (l_shoulder[2] + r_shoulder[2]) // 2
    shoulder_center_x = (l_shoulder[1] + r_shoulder[1]) // 2
    
    # 6-Point Validation (ALL must be true)
    left_arm_raised = l_wrist[2] < l_shoulder[2] - 150  # 150px above shoulder
    right_arm_raised = r_wrist[2] < r_shoulder[2] - 150  # 150px above shoulder
    arms_symmetric = abs(l_wrist[2] - r_wrist[2]) < 20  # Height difference < 20px
    left_arm_centered = abs(l_wrist[1] - shoulder_center_x) < shoulder_width * 0.8
    right_arm_centered = abs(r_wrist[1] - shoulder_center_x) < shoulder_width * 0.8
    elbows_up = l_elbow[2] < avg_shoulder_y - 50 and r_elbow[2] < avg_shoulder_y - 50
    
    return (left_arm_raised and right_arm_raised and arms_symmetric and 
            left_arm_centered and right_arm_centered and elbows_up)

def detect_side_stretch(lmList):
    """Detect side stretch stretching exercise."""
    if len(lmList) < 17:
        return None
    
    l_shoulder = lmList[11]
    r_shoulder = lmList[12]
    l_elbow = lmList[13]
    r_elbow = lmList[14]
    l_wrist = lmList[15]
    r_wrist = lmList[16]
    
    shoulder_width = abs(r_shoulder[1] - l_shoulder[1])
    
    # Left Side Stretch: Left arm reaching right + right arm down
    left_way_out = l_wrist[1] < l_shoulder[1] - shoulder_width * 1.2
    right_arm_down = r_wrist[2] > r_shoulder[2] + 50
    left_elbow_out = l_elbow[1] < l_shoulder[1] - shoulder_width * 0.5
    
    if left_way_out and right_arm_down and left_elbow_out:
        return "Left Side Stretch"
    
    # Right Side Stretch: Right arm reaching left + left arm down
    right_way_out = r_wrist[1] > r_shoulder[1] + shoulder_width * 1.2
    left_arm_down = l_wrist[2] > l_shoulder[2] + 50
    right_elbow_out = r_elbow[1] > r_shoulder[1] + shoulder_width * 0.5
    
    if right_way_out and left_arm_down and right_elbow_out:
        return "Right Side Stretch"
    
    return None

def detect_stretching_exercise(lmList):
    """Main function for stretching detection."""
    if detect_overhead_reach(lmList):
        return ("Overhead Reach", "active")
    
    side_stretch = detect_side_stretch(lmList)
    if side_stretch:
        return (side_stretch, "active")
    
    return None

class PostureLogger:
    """Handles discrete 30-second window posture logging."""
    
    def __init__(self, log_interval=3.0, window_duration=30.0, summary_file="posture_summary.json", motivation_file="motivation_quotes.json"):
        self.log_interval = log_interval
        self.window_duration = window_duration
        self.summary_file = summary_file
        self.motivation_file = motivation_file
        
        # Simple counters for current window
        self.good_posture_count = 0
        self.slouching_count = 0
        self.total_posture_ratio = 0.0
        
        # Timing variables
        self.last_log_time = time.time()
        self.window_start_time = time.time()
        
        # Initialize summary log file
        self._initialize_summary_file()
        self._initialize_motivation_file()
        
        print(f"📊 PostureLogger initialized (headless mode):")
        print(f"   - Log interval: {log_interval}s")
        print(f"   - Window duration: {window_duration}s")
        print(f"   - Summary log: {summary_file}")
        print(f"   - Motivation log: {motivation_file}")
    
    def _initialize_summary_file(self):
        """Initialize the summary log file with proper structure."""
        if not os.path.exists(self.summary_file):
            initial_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "log_interval_seconds": self.log_interval,
                    "window_duration_seconds": self.window_duration,
                    "description": "Posture monitoring summary log - one entry per 30-second window"
                },
                "summary_logs": []
            }
            with open(self.summary_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
            print(f"✅ Created new summary log file: {self.summary_file}")
    
    def _initialize_motivation_file(self):
        """Initialize the motivation quotes file with proper structure."""
        if not os.path.exists(self.motivation_file):
            initial_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "description": "AI-generated motivational quotes based on posture performance"
                },
                "quotes": []
            }
            with open(self.motivation_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
            print(f"✅ Created new motivation file: {self.motivation_file}")
    
    def should_log_posture(self) -> bool:
        """Check if it's time to log a new posture reading."""
        current_time = time.time()
        return (current_time - self.last_log_time) >= self.log_interval
    
    def log_posture_reading(self, is_good_posture: bool, posture_ratio: float):
        """Log a single posture reading by incrementing counters."""
        current_time = time.time()
        
        # Increment appropriate counter
        if is_good_posture:
            self.good_posture_count += 1
        else:
            self.slouching_count += 1
        
        # Add to running total for average calculation
        self.total_posture_ratio += posture_ratio
        
        # Update last log time
        self.last_log_time = current_time
        
        # Check if window duration has elapsed
        if (current_time - self.window_start_time) >= self.window_duration:
            self._create_summary_log()
            self._reset_window()
    
    def _create_summary_log(self):
        """Create and save a summary log entry for the current window."""
        current_time = time.time()
        total_readings = self.good_posture_count + self.slouching_count
        
        if total_readings == 0:
            return  # No data to log
        
        # Calculate percentages
        good_posture_percentage = round((self.good_posture_count / total_readings) * 100, 1)
        slouching_percentage = round((self.slouching_count / total_readings) * 100, 1)
        average_posture_ratio = round(self.total_posture_ratio / total_readings, 3)
        
        # Create summary entry
        summary_entry = {
            "timestamp": datetime.now().isoformat(),
            "window_start": datetime.fromtimestamp(self.window_start_time).isoformat(),
            "window_end": datetime.fromtimestamp(current_time).isoformat(),
            "window_duration_seconds": round(current_time - self.window_start_time, 1),
            "total_readings": total_readings,
            "good_posture_count": self.good_posture_count,
            "slouching_count": self.slouching_count,
            "good_posture_percentage": good_posture_percentage,
            "slouching_percentage": slouching_percentage,
            "average_posture_ratio": average_posture_ratio
        }
        
        print(f"📊 Window Summary: {good_posture_percentage}% good posture ({self.good_posture_count}G/{self.slouching_count}S)")
        
        # Save to file
        self._save_summary_to_file(summary_entry)
        
        # Generate motivation quote asynchronously
        threading.Thread(target=self._generate_motivation_async, daemon=True).start()
    
    def _reset_window(self):
        """Reset counters for the next window."""
        self.good_posture_count = 0
        self.slouching_count = 0
        self.total_posture_ratio = 0.0
        self.window_start_time = time.time()
    
    def _save_summary_to_file(self, summary_entry: Dict):
        """Save summary entry to the JSON file."""
        try:
            # Read existing data
            with open(self.summary_file, 'r') as f:
                data = json.load(f)
            
            # Add new entry
            data['summary_logs'].append(summary_entry)
            
            # Write back to file
            with open(self.summary_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving summary to file: {e}")
    
    def _generate_motivation_async(self):
        """Generate motivation quote in a separate thread."""
        try:
            self._generate_motivation_quote()
        except Exception as e:
            print(f"❌ Error generating motivation quote: {e}")
    
    def _generate_motivation_quote(self):
        """Generate AI motivation quote based on recent performance."""
        try:
            # Read recent summary data
            with open(self.summary_file, 'r') as f:
                data = json.load(f)
            
            recent_logs = data['summary_logs'][-5:] if len(data['summary_logs']) > 5 else data['summary_logs']
            
            if not recent_logs:
                return
            
            # Calculate recent performance
            total_good = sum(log['good_posture_count'] for log in recent_logs)
            total_readings = sum(log['total_readings'] for log in recent_logs)
            recent_percentage = (total_good / total_readings * 100) if total_readings > 0 else 0
            
            # Create prompt for LLM
            prompt = f"""Generate a short, encouraging motivational quote for someone monitoring their posture. 
            Recent performance: {recent_percentage:.1f}% good posture over {len(recent_logs)} sessions.
            Keep it under 15 words, positive, and health-focused. No quotes around the text."""
            
            # Get motivation from LLM
            motivation_text = ask_llm(prompt)
            
            if not is_error_response(motivation_text):
                quote_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "category": "Motivation",
                    "text": motivation_text.strip(),
                    "performance_context": f"{recent_percentage:.1f}% good posture",
                    "sessions_analyzed": len(recent_logs)
                }
                
                self._save_motivation_to_file(quote_entry)
                print(f"💡 New motivation: {motivation_text.strip()}")
            
        except Exception as e:
            print(f"❌ Error in motivation generation: {e}")
    
    def _save_motivation_to_file(self, quote_entry: Dict):
        """Save motivation quote to the JSON file."""
        try:
            # Read existing data
            with open(self.motivation_file, 'r') as f:
                data = json.load(f)
            
            # Add new quote
            data['quotes'].append(quote_entry)
            
            # Keep only last 50 quotes to prevent file from growing too large
            if len(data['quotes']) > 50:
                data['quotes'] = data['quotes'][-50:]
            
            # Write back to file
            with open(self.motivation_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving motivation to file: {e}")
    
    def get_current_window_stats(self) -> Dict:
        """Get current window statistics."""
        total_readings = self.good_posture_count + self.slouching_count
        good_posture_percentage = round((self.good_posture_count / total_readings) * 100, 1) if total_readings > 0 else 0
        
        return {
            "good_posture_count": self.good_posture_count,
            "slouching_count": self.slouching_count,
            "total_readings": total_readings,
            "good_posture_percentage": good_posture_percentage
        }

class PoseDetector():
    def __init__(self, staticImageMode=False, modelComplexity=1, smoothLandmarks=True, enableSegmentation=False, smoothSegmentation=True, minDetectionConfidence=0.5, minTrackingConfidence=0.5):
        self.staticImageMode = staticImageMode
        self.modelComplexity = modelComplexity
        self.smoothLandmarks = smoothLandmarks
        self.enableSegmentation = enableSegmentation
        self.smoothSegmentation = smoothSegmentation
        self.minDetectionConfidence = minDetectionConfidence
        self.minTrackingConfidence = minTrackingConfidence
        
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(
            static_image_mode=self.staticImageMode,
            model_complexity=self.modelComplexity,
            smooth_landmarks=self.smoothLandmarks,
            enable_segmentation=self.enableSegmentation,
            smooth_segmentation=self.smoothSegmentation,
            min_detection_confidence=self.minDetectionConfidence,
            min_tracking_confidence=self.minTrackingConfidence
        )
    
    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        return img
    
    def findPosition(self, img, draw=False):
        self.lmList = []
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
        return self.lmList

def get_available_cameras():
    """Check for available cameras."""
    available_cameras = []
    for i in range(5):  # Check first 5 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    running = False

def main():
    global running
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🎥 Starting Headless Pose Detection")
    print("=" * 50)
    print("🔇 Running in headless mode (no GUI)")
    print("🛑 To stop: Send SIGTERM or SIGINT signal")
    
    # Check available cameras
    available_cameras = get_available_cameras()
    print(f"Available cameras: {available_cameras}")
    
    if not available_cameras:
        print("❌ No cameras found! Please check your camera connection.")
        return
    
    # Try to use the first available camera
    camera_id = available_cameras[0]
    print(f"🎯 Using camera {camera_id}")
    
    # Initialize camera
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera!")
        return
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Initialize pose detector
    detector = PoseDetector()
    
    # Initialize posture logger
    posture_logger = PostureLogger(
        log_interval=3.0,      # Log every 3 seconds
        window_duration=30.0,  # 30-second window
        summary_file="posture_summary.json",
        motivation_file="motivation_quotes.json"
    )
    
    # Posture detection variables
    posture_threshold_percentage = 0.45
    bad_posture_duration = 0
    bad_posture_alert_time = 3.0
    last_posture_check_time = time.time()
    
    # Stretching detection variables
    current_stretch = None
    stretch_start_time = 0
    stretch_hold_time = 2.0
    stretch_completed = False
    
    print("✅ Camera initialized successfully!")
    print("📊 Logging enabled - monitoring posture every 3 seconds")
    print("🧘 Stretching detection active")
    print("=" * 50)
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while running:
            success, img = cap.read()
            
            if not success:
                print("❌ Failed to read from camera")
                break
            
            frame_count += 1
            
            # Flip the image horizontally for a mirror effect
            img = cv2.flip(img, 1)
            
            # Detect pose
            img = detector.findPose(img, draw=False)
            lmList = detector.findPosition(img, draw=False)
            
            # Calculate FPS every 30 frames
            if frame_count % 30 == 0:
                current_time = time.time()
                fps = 30 / (current_time - start_time) if (current_time - start_time) > 0 else 0
                print(f"📹 FPS: {fps:.1f} | Frames processed: {frame_count}")
                start_time = current_time
            
            # Posture detection logic
            if len(lmList) >= 13:
                nose_x, nose_y = lmList[0][1], lmList[0][2]
                left_shoulder_x, left_shoulder_y = lmList[11][1], lmList[11][2]
                right_shoulder_x, right_shoulder_y = lmList[12][1], lmList[12][2]
                
                shoulder_width = abs(right_shoulder_x - left_shoulder_x)
                shoulder_line_y = (left_shoulder_y + right_shoulder_y) / 2
                posture_distance = shoulder_line_y - nose_y
                posture_ratio = posture_distance / shoulder_width if shoulder_width > 0 else 0
                
                current_time = time.time()
                is_good_posture = posture_ratio >= posture_threshold_percentage
                
                if not is_good_posture:
                    bad_posture_duration += current_time - last_posture_check_time
                    if bad_posture_duration >= bad_posture_alert_time:
                        if frame_count % 90 == 0:  # Print alert every 3 seconds
                            print("⚠️  POSTURE ALERT: Please correct your posture!")
                else:
                    bad_posture_duration = 0
                
                last_posture_check_time = current_time
                
                # Log posture data
                if posture_logger.should_log_posture():
                    posture_logger.log_posture_reading(
                        is_good_posture=is_good_posture,
                        posture_ratio=posture_ratio
                    )
                    
                    # Print status every log interval
                    stats = posture_logger.get_current_window_stats()
                    status = "GOOD" if is_good_posture else "SLOUCHING"
                    print(f"📊 Status: {status} | Window: {stats['good_posture_count']}G/{stats['slouching_count']}S ({stats['good_posture_percentage']}%)")
            
            # Stretching detection logic
            if len(lmList) >= 17:
                stretch_detected = detect_stretching_exercise(lmList)
                current_time = time.time()
                
                if stretch_detected:
                    stretch_name, _ = stretch_detected
                    
                    if stretch_name != current_stretch:
                        current_stretch = stretch_name
                        stretch_start_time = current_time
                        stretch_completed = False
                        print(f"🧘 Stretch detected: {stretch_name}")
                    
                    hold_duration = current_time - stretch_start_time
                    if hold_duration >= stretch_hold_time and not stretch_completed:
                        stretch_completed = True
                        print(f"✅ {stretch_name} completed! ({hold_duration:.1f}s)")
                else:
                    if current_stretch:
                        print(f"🧘 {current_stretch} ended")
                    current_stretch = None
                    stretch_completed = False
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        # Clean up
        running = False
        cap.release()
        print("🏁 Camera released successfully!")
        print(f"📊 Total frames processed: {frame_count}")

if __name__ == '__main__':
    main() 