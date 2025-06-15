#!/usr/bin/env python3
"""
Simplified Video Streamer for Edgefit-Coach
Based on the sample code provided - direct OpenCV to HLS streaming
"""

import cv2
import subprocess
import threading
import time
import os
import signal
import sys
from typing import Optional
import numpy as np

class SimpleVideoStreamer:
    """
    Simple video streamer that captures from camera and creates HLS stream.
    """
    
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap: Optional[cv2.VideoCapture] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        
        # Video settings
        self.width = 640
        self.height = 480
        self.fps = 30
        
        # Create output directories
        os.makedirs("data/processed", exist_ok=True)
        
    def start_stream(self) -> bool:
        """Start the video stream."""
        try:
            # Initialize camera with different backends
            backends_to_try = [
                cv2.CAP_DSHOW,  # DirectShow (Windows)
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
            
            print(f"🎥 Video stream started")
            return True
            
        except Exception as e:
            print(f"❌ Error starting video stream: {e}")
            return False
    
    def _stream_loop(self):
        """Main streaming loop - generates frames and creates HLS stream."""
        frame_count = 0
        start_time = time.time()
        
        # Start FFmpeg process for HLS
        ffmpeg_command = [
            'ffmpeg', '-y',  # Overwrite output files
            '-f', 'rawvideo', 
            '-pix_fmt', 'bgr24', 
            '-s', f'{self.width}x{self.height}', 
            '-r', str(self.fps),
            '-i', '-',  # Input from stdin
            '-c:v', 'libx264', 
            '-preset', 'ultrafast', 
            '-tune', 'zerolatency',
            '-g', '30',  # GOP size
            '-keyint_min', '30',
            '-sc_threshold', '0',
            '-b:v', '1000k',
            '-maxrate', '1000k',
            '-bufsize', '1000k',
            '-hls_time', '2',  # 2 second segments
            '-hls_list_size', '5',  # Keep 5 segments
            '-hls_flags', 'delete_segments',
            '-hls_segment_filename', 'data/processed/segment_%03d.ts',
            'data/processed/stream.m3u8'
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_command, 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("✅ FFmpeg HLS process started")
        except Exception as e:
            print(f"❌ Error starting FFmpeg: {e}")
            self.ffmpeg_process = None
        
        while self.streaming and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("❌ Failed to read frame from camera")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Save current frame for MJPEG fallback
                cv2.imwrite("current_frame.jpg", frame)
                
                # Send frame to FFmpeg if available
                if self.ffmpeg_process and self.ffmpeg_process.stdin:
                    try:
                        self.ffmpeg_process.stdin.write(frame.tobytes())
                        self.ffmpeg_process.stdin.flush()
                    except (BrokenPipeError, OSError) as e:
                        print(f"⚠️ FFmpeg pipe error: {e}")
                        break
                
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
        self._cleanup_ffmpeg()
    
    def _cleanup_ffmpeg(self):
        """Clean up FFmpeg process."""
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
            except:
                try:
                    self.ffmpeg_process.kill()
                except:
                    pass
            self.ffmpeg_process = None
    
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
        
        # Clean up FFmpeg
        self._cleanup_ffmpeg()
        
        print("✅ Video stream stopped")
    
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self.streaming and self.stream_thread and self.stream_thread.is_alive()
    
    def get_stream_url(self) -> str:
        """Get the stream URL for frontend consumption."""
        if os.path.exists("data/processed/stream.m3u8"):
            return "http://localhost:8000/hls/stream.m3u8"
        else:
            return "http://localhost:8000/video/stream"


# Global streamer instance
simple_streamer = SimpleVideoStreamer()

def start_simple_streaming(camera_id: int = 0) -> bool:
    """Start simple video streaming."""
    return simple_streamer.start_stream()

def stop_simple_streaming():
    """Stop simple video streaming."""
    simple_streamer.stop_stream()

def is_simple_streaming() -> bool:
    """Check if streaming is active."""
    return simple_streamer.is_streaming()

def get_simple_stream_url() -> str:
    """Get stream URL."""
    return simple_streamer.get_stream_url()


if __name__ == "__main__":
    # Test the simple video streamer
    print("🎥 Testing Simple Video Streamer")
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, stopping...")
        stop_simple_streaming()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if start_simple_streaming():
        print("✅ Simple video streaming started successfully")
        print("🌐 HLS Stream URL: http://localhost:8000/hls/stream.m3u8")
        print("📹 MJPEG fallback: http://localhost:8000/video/stream")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("❌ Failed to start simple video streaming")
    
    stop_simple_streaming() 