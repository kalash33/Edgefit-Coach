#!/usr/bin/env python3
"""
Enhanced Video Streamer with Pose Detection for Edgefit-Coach
Combines OpenCV video streaming with full pose detection, posture monitoring, and stretching detection.
"""

import cv2
import mediapipe as mp
import threading
import time
import os
import signal
import sys
from typing import Optional, Dict, List
import numpy as np
import queue
import json
from datetime import datetime
from collections import deque
import pickle

# Import pose detection functions from main file
try:
    from main_webcam_headless1 import (
        detect_overhead_reach, detect_side_stretch, detect_stretching_exercise,
        PostureLogger, PoseDetector
    )
    POSE_DETECTION_AVAILABLE = True
except ImportError:
    print("⚠️ Pose detection modules not available, using basic streaming")
    POSE_DETECTION_AVAILABLE = False

class PoseVideoStreamer:
    """
    Enhanced video streamer with pose detection, posture monitoring, and stretching detection.
    """
    
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap: Optional[cv2.VideoCapture] = None
        self.streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        
        # Video settings
        self.width = 640
        self.height = 480
        self.fps = 30
        
        # Frame buffer for streaming
        self.frame_queue = queue.Queue(maxsize=2)
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Pose detection components
        if POSE_DETECTION_AVAILABLE:
            self.detector = PoseDetector()
            self.posture_logger = PostureLogger(
                log_interval=3.0,
                window_duration=30.0,
                summary_file="posture_summary.json",
                motivation_file="motivation_quotes.json"
            )
        else:
            self.detector = None
            self.posture_logger = None
        
        # Posture detection variables
        self.posture_threshold_percentage = 0.45
        self.bad_posture_duration = 0
        self.bad_posture_alert_time = 3.0
        self.last_posture_check_time = time.time()
        self.show_posture_alert = False
        
        # Stretching detection variables
        self.current_stretch = None
        self.stretch_start_time = 0
        self.stretch_hold_time = 2.0
        self.stretch_completed = False
        
        # FPS tracking
        self.pTime = 0
        self.cTime = 0
        self.frame_count = 0
        self.start_time = time.time()
        
    def start_stream(self) -> bool:
        """Start the video stream with pose detection."""
        try:
            # Initialize camera with different backends
            backends_to_try = [
                cv2.CAP_DSHOW,  # DirectShow (Windows) - this worked!
                cv2.CAP_MSMF,   # Microsoft Media Foundation
                cv2.CAP_ANY     # Any available backend
            ]
            
            self.cap = None
            for backend in backends_to_try:
                print(f"🔍 Trying camera backend: {backend}")
                test_cap = cv2.VideoCapture(self.camera_id, backend)
                if test_cap.isOpened():
                    # Test if we can actually read frames
                    ret, test_frame = test_cap.read()
                    if ret and test_frame is not None:
                        print(f"✅ Camera working with backend {backend}")
                        self.cap = test_cap
                        break
                    else:
                        test_cap.release()
                else:
                    test_cap.release()
            
            if not self.cap or not self.cap.isOpened():
                print("❌ Error: Could not open camera with any backend")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Get actual camera properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"✅ Camera initialized - Resolution: {actual_width}x{actual_height}, FPS: {actual_fps}")
            
            # Update dimensions to actual values
            self.width = actual_width
            self.height = actual_height
            
            # Start streaming thread
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            
            print(f"🎥 Enhanced video stream with pose detection started")
            if POSE_DETECTION_AVAILABLE:
                print("🧘 Pose detection, posture monitoring, and stretching detection active")
            return True
            
        except Exception as e:
            print(f"❌ Error starting video stream: {e}")
            return False
    
    def _stream_loop(self):
        """Main streaming loop with pose detection and analysis."""
        self.frame_count = 0
        self.start_time = time.time()
        
        while self.streaming and self.cap and self.cap.isOpened():
            try:
                ret, img = self.cap.read()
                if not ret or img is None:
                    print("❌ Failed to read frame from camera")
                    break
                
                # Flip frame horizontally for mirror effect
                img = cv2.flip(img, 1)
                
                # Pose detection and analysis
                if POSE_DETECTION_AVAILABLE and self.detector:
                    img = self._process_pose_detection(img)
                
                # Add FPS and status overlays
                img = self._add_overlays(img)
                
                # Update current frame with thread safety
                with self.frame_lock:
                    self.current_frame = img.copy()
                
                # Save current frame for API access
                cv2.imwrite("current_frame.jpg", img)
                
                # Also save frame data as pickle for API server
                try:
                    with open("current_frame.pkl", "wb") as f:
                        pickle.dump(img, f)
                except:
                    pass  # Silently fail
                
                # Update frame queue for streaming (non-blocking)
                try:
                    if not self.frame_queue.full():
                        self.frame_queue.put(img, block=False)
                except queue.Full:
                    pass  # Skip frame if queue is full
                
                self.frame_count += 1
                
                # Print FPS every 30 frames
                if self.frame_count % 30 == 0:
                    elapsed = time.time() - self.start_time
                    fps = self.frame_count / elapsed if elapsed > 0 else 0
                    print(f"📹 Streaming FPS: {fps:.1f}")
                    self.frame_count = 0
                    self.start_time = time.time()
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                print(f"❌ Error in streaming loop: {e}")
                break
        
        print("🛑 Streaming loop ended")
    
    def _process_pose_detection(self, img):
        """Process pose detection, posture analysis, and stretching detection."""
        # Detect pose (without drawing landmarks to keep it clean)
        img = self.detector.findPose(img, draw=False)
        lmList = self.detector.findPosition(img, draw=False)
        
        # Posture detection logic
        if len(lmList) >= 13:  # Ensure we have all required landmarks
            img = self._analyze_posture(img, lmList)
        
        # Stretching detection logic
        if len(lmList) >= 17:  # Ensure we have all required landmarks for stretching
            img = self._analyze_stretching(img, lmList)
        
        return img
    
    def _analyze_posture(self, img, lmList):
        """Analyze posture and add status overlays."""
        nose_x, nose_y = lmList[0][1], lmList[0][2]
        left_shoulder_x, left_shoulder_y = lmList[11][1], lmList[11][2]
        right_shoulder_x, right_shoulder_y = lmList[12][1], lmList[12][2]
        
        # Calculate shoulder width and posture ratio
        shoulder_width = abs(right_shoulder_x - left_shoulder_x)
        shoulder_line_y = (left_shoulder_y + right_shoulder_y) / 2
        posture_distance = shoulder_line_y - nose_y
        posture_ratio = posture_distance / shoulder_width if shoulder_width > 0 else 0
        
        current_time = time.time()
        is_good_posture = posture_ratio >= self.posture_threshold_percentage
        
        if not is_good_posture:
            self.bad_posture_duration += current_time - self.last_posture_check_time
            posture_status = "SLOUCHING"
            status_color = (0, 0, 255)  # Red
            
            if self.bad_posture_duration >= self.bad_posture_alert_time:
                self.show_posture_alert = True
        else:
            self.bad_posture_duration = 0
            self.show_posture_alert = False
            posture_status = "GOOD POSTURE"
            status_color = (0, 255, 0)  # Green
        
        self.last_posture_check_time = current_time
        
        # Log posture data
        if self.posture_logger and self.posture_logger.should_log_posture():
            self.posture_logger.log_posture_reading(
                is_good_posture=is_good_posture,
                posture_ratio=posture_ratio
            )
            
            # Console output for monitoring
            stats = self.posture_logger.get_current_window_stats()
            print(f"📊 Status: {posture_status} | Window: {stats['good_posture_count']}G/{stats['slouching_count']}S ({stats['good_posture_percentage']}%)")
        
        # Add posture status overlay
        cv2.putText(img, f"Status: {posture_status}", (10, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Add logging statistics
        if self.posture_logger:
            stats = self.posture_logger.get_current_window_stats()
            cv2.putText(img, f"30s Window: {stats['good_posture_count']}G/{stats['slouching_count']}S", 
                       (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            if stats['total_readings'] > 0:
                cv2.putText(img, f"Good: {stats['good_posture_percentage']}%", 
                           (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Show posture alert if needed
        if self.show_posture_alert:
            alert_text = "CORRECT YOUR POSTURE!"
            text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            text_x = (img.shape[1] - text_size[0]) // 2
            text_y = img.shape[0] // 2
            
            # Draw background rectangle for alert
            cv2.rectangle(img, (text_x - 20, text_y - 40), 
                        (text_x + text_size[0] + 20, text_y + 20), (0, 0, 255), -1)
            cv2.putText(img, alert_text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        return img
    
    def _analyze_stretching(self, img, lmList):
        """Analyze stretching exercises and add status overlays."""
        stretch_detected = detect_stretching_exercise(lmList)
        current_time = time.time()
        
        if stretch_detected:
            stretch_name, _ = stretch_detected
            
            if stretch_name != self.current_stretch:
                self.current_stretch = stretch_name
                self.stretch_start_time = current_time
                self.stretch_completed = False
            
            hold_duration = current_time - self.stretch_start_time
            if hold_duration >= self.stretch_hold_time and not self.stretch_completed:
                self.stretch_completed = True
                print(f"✅ {stretch_name} completed!")
            
            # Display stretching status
            cv2.putText(img, f"Stretch: {stretch_name}", (10, 200), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
            cv2.putText(img, f"Hold: {hold_duration:.1f}s/{self.stretch_hold_time}s", (10, 230), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
            
            if self.stretch_completed:
                cv2.putText(img, "STRETCH COMPLETED!", (10, 260), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            self.current_stretch = None
            self.stretch_completed = False
        
        return img
    
    def _add_overlays(self, img):
        """Add FPS and system status overlays."""
        # Calculate and display FPS
        self.cTime = time.time()
        fps = 1 / (self.cTime - self.pTime) if (self.cTime - self.pTime) > 0 else 0
        self.pTime = self.cTime
        
        cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img, 'Acceleration: NPU', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return img
    
    def get_frame(self):
        """Get the current frame for MJPEG streaming."""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            else:
                # Return a placeholder frame
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Waiting for camera...", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                return placeholder
    
    def generate_frames(self):
        """Generator for MJPEG streaming."""
        while self.streaming:
            frame = self.get_frame()
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1.0 / self.fps)  # Control streaming rate
    
    def stop_stream(self):
        """Stop the video stream."""
        print("🛑 Stopping enhanced video stream...")
        
        self.streaming = False
        
        # Wait for streaming thread to finish
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=5)
        
        # Close camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear frame buffer
        with self.frame_lock:
            self.current_frame = None
        
        print("✅ Enhanced video stream stopped")
    
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self.streaming and self.stream_thread and self.stream_thread.is_alive()
    
    def get_stream_url(self) -> str:
        """Get the stream URL for frontend consumption."""
        return "http://localhost:8000/video/stream"


# Global streamer instance
pose_streamer = PoseVideoStreamer()

def start_pose_streaming(camera_id: int = 0) -> bool:
    """Start pose detection video streaming."""
    return pose_streamer.start_stream()

def stop_pose_streaming():
    """Stop pose detection video streaming."""
    pose_streamer.stop_stream()

def is_pose_streaming() -> bool:
    """Check if streaming is active."""
    return pose_streamer.is_streaming()

def get_pose_stream_url() -> str:
    """Get stream URL."""
    return pose_streamer.get_stream_url()

def get_pose_frame_generator():
    """Get frame generator for MJPEG streaming."""
    return pose_streamer.generate_frames()


if __name__ == "__main__":
    # Test the pose detection video streamer
    print("🎥 Testing Enhanced Video Streamer with Pose Detection")
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, stopping...")
        stop_pose_streaming()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if start_pose_streaming():
        print("✅ Enhanced video streaming with pose detection started successfully")
        print("📹 MJPEG Stream URL: http://localhost:8000/video/stream")
        print("🧘 Features: Pose detection, posture monitoring, stretching detection")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("❌ Failed to start enhanced video streaming")
    
    stop_pose_streaming() 