#!/usr/bin/env python3
"""
Pure OpenCV Video Streamer for Edgefit-Coach
No FFmpeg required - uses OpenCV for MJPEG streaming that works in browsers.
"""

import cv2
import threading
import time
import os
import signal
import sys
from typing import Optional
import numpy as np
import queue

class OpenCVVideoStreamer:
    """
    Pure OpenCV video streamer that captures from camera and provides MJPEG stream.
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
        
    def start_stream(self) -> bool:
        """Start the video stream."""
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
            
            print(f"🎥 OpenCV video stream started")
            return True
            
        except Exception as e:
            print(f"❌ Error starting video stream: {e}")
            return False
    
    def _stream_loop(self):
        """Main streaming loop - captures frames and updates buffer."""
        frame_count = 0
        start_time = time.time()
        
        while self.streaming and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("❌ Failed to read frame from camera")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Update current frame with thread safety
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Save current frame for API access
                cv2.imwrite("current_frame.jpg", frame)
                
                # Update frame queue for streaming (non-blocking)
                try:
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame, block=False)
                except queue.Full:
                    pass  # Skip frame if queue is full
                
                frame_count += 1
                
                # Print FPS every 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed if elapsed > 0 else 0
                    print(f"📹 Streaming FPS: {fps:.1f}")
                    frame_count = 0
                    start_time = time.time()
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                print(f"❌ Error in streaming loop: {e}")
                break
        
        print("🛑 Streaming loop ended")
    
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
        print("🛑 Stopping video stream...")
        
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
        
        print("✅ Video stream stopped")
    
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self.streaming and self.stream_thread and self.stream_thread.is_alive()
    
    def get_stream_url(self) -> str:
        """Get the stream URL for frontend consumption."""
        return "http://localhost:8000/video/stream"


# Global streamer instance
opencv_streamer = OpenCVVideoStreamer()

def start_opencv_streaming(camera_id: int = 0) -> bool:
    """Start OpenCV video streaming."""
    return opencv_streamer.start_stream()

def stop_opencv_streaming():
    """Stop OpenCV video streaming."""
    opencv_streamer.stop_stream()

def is_opencv_streaming() -> bool:
    """Check if streaming is active."""
    return opencv_streamer.is_streaming()

def get_opencv_stream_url() -> str:
    """Get stream URL."""
    return opencv_streamer.get_stream_url()

def get_opencv_frame_generator():
    """Get frame generator for MJPEG streaming."""
    return opencv_streamer.generate_frames()


if __name__ == "__main__":
    # Test the OpenCV video streamer
    print("🎥 Testing OpenCV Video Streamer")
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, stopping...")
        stop_opencv_streaming()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if start_opencv_streaming():
        print("✅ OpenCV video streaming started successfully")
        print("📹 MJPEG Stream URL: http://localhost:8000/video/stream")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("❌ Failed to start OpenCV video streaming")
    
    stop_opencv_streaming() 