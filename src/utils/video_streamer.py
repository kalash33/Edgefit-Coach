#!/usr/bin/env python3
"""
Video Streamer Module for Edgefit-Coach
Uses OpenCV to FFmpeg pipeline for proper web streaming that works in browsers.
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

class VideoStreamer:
    """
    Video streamer that captures from camera and streams via FFmpeg for web compatibility.
    """
    
    def __init__(self, camera_id: int = 0, output_port: int = 8554):
        self.camera_id = camera_id
        self.output_port = output_port
        self.cap: Optional[cv2.VideoCapture] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        
        # Video settings
        self.width = 640
        self.height = 480
        self.fps = 30
        
    def start_stream(self) -> bool:
        """Start the video stream."""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                print(f"❌ Error: Could not open camera {self.camera_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Test camera read
            ret, test_frame = self.cap.read()
            if not ret:
                print("❌ Error: Camera opened but cannot read frames")
                return False
            
            print(f"✅ Camera initialized - Frame shape: {test_frame.shape}")
            
            # Start FFmpeg process for HLS streaming
            self._start_ffmpeg()
            
            # Start streaming thread
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            
            print(f"🎥 Video stream started on port {self.output_port}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting video stream: {e}")
            return False
    
    def _start_ffmpeg(self):
        """Start FFmpeg process for HLS streaming."""
        try:
            # Create output directory
            os.makedirs("stream_output", exist_ok=True)
            
            # FFmpeg command for HLS streaming
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output files
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', f'{self.width}x{self.height}',
                '-r', str(self.fps),
                '-i', '-',  # Input from stdin
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-crf', '23',
                '-f', 'hls',
                '-hls_time', '1',
                '-hls_list_size', '3',
                '-hls_flags', 'delete_segments',
                'stream_output/stream.m3u8'
            ]
            
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("✅ FFmpeg HLS streaming process started")
            
        except Exception as e:
            print(f"❌ Error starting FFmpeg: {e}")
            # Fallback to simple MJPEG if FFmpeg fails
            self._start_simple_stream()
    
    def _start_simple_stream(self):
        """Fallback to simple MJPEG streaming."""
        print("🔄 Falling back to simple MJPEG streaming")
        self.ffmpeg_process = None
    
    def _stream_loop(self):
        """Main streaming loop."""
        frame_count = 0
        start_time = time.time()
        
        while self.streaming and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to read frame from camera")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Save current frame for API access
                cv2.imwrite("current_frame.jpg", frame)
                
                # Stream via FFmpeg if available
                if self.ffmpeg_process and self.ffmpeg_process.stdin:
                    try:
                        self.ffmpeg_process.stdin.write(frame.tobytes())
                        self.ffmpeg_process.stdin.flush()
                    except BrokenPipeError:
                        print("⚠️ FFmpeg pipe broken, restarting...")
                        self._restart_ffmpeg()
                
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
    
    def _restart_ffmpeg(self):
        """Restart FFmpeg process."""
        try:
            if self.ffmpeg_process:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
        except:
            pass
        
        self._start_ffmpeg()
    
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
        
        # Stop FFmpeg
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
        
        print("✅ Video stream stopped")
    
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self.streaming and self.stream_thread and self.stream_thread.is_alive()
    
    def get_stream_url(self) -> str:
        """Get the stream URL for frontend consumption."""
        if os.path.exists("stream_output/stream.m3u8"):
            return f"http://localhost:8000/stream/stream.m3u8"
        else:
            return f"http://localhost:8000/video/stream"


# Global streamer instance
video_streamer = VideoStreamer()

def start_video_streaming(camera_id: int = 0) -> bool:
    """Start video streaming."""
    return video_streamer.start_stream()

def stop_video_streaming():
    """Stop video streaming."""
    video_streamer.stop_stream()

def is_streaming() -> bool:
    """Check if streaming is active."""
    return video_streamer.is_streaming()

def get_stream_url() -> str:
    """Get stream URL."""
    return video_streamer.get_stream_url()


if __name__ == "__main__":
    # Test the video streamer
    print("🎥 Testing Video Streamer")
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, stopping...")
        stop_video_streaming()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if start_video_streaming():
        print("✅ Video streaming started successfully")
        print("🌐 Stream URL: http://localhost:8000/stream/stream.m3u8")
        print("📹 MJPEG fallback: http://localhost:8000/video/stream")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("❌ Failed to start video streaming")
    
    stop_video_streaming() 