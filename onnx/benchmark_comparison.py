#!/usr/bin/env python3
"""
Benchmark script to compare MediaPipe vs Qualcomm NPU performance
"""

import cv2
import time
import numpy as np
from typing import List, Tuple, Dict
import os

# Import implementations
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️  MediaPipe not available")

try:
    from main_qualcomm_npu import QualcommPoseDetector
    QUALCOMM_AVAILABLE = True
except ImportError:
    QUALCOMM_AVAILABLE = False
    print("⚠️  Qualcomm NPU implementation not available")

class MediaPipePoseDetector:
    """Standard MediaPipe implementation for comparison"""
    
    def __init__(self):
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe not available")
        
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.results = None
    
    def findPose(self, img: np.ndarray, draw: bool = True) -> np.ndarray:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(
                    img, 
                    self.results.pose_landmarks, 
                    self.mpPose.POSE_CONNECTIONS
                )
        return img
    
    def findPosition(self, img: np.ndarray, draw: bool = False) -> List[List[int]]:
        lmList = []
        if self.results and self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
                
                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 0), cv2.FILLED)
        return lmList

class PerformanceBenchmark:
    """Performance benchmark utility"""
    
    def __init__(self, test_duration: int = 30):
        self.test_duration = test_duration
        self.results = {}
    
    def create_test_images(self, count: int = 100) -> List[np.ndarray]:
        """Create test images for benchmarking"""
        images = []
        
        # Create various test images
        for i in range(count):
            if i % 4 == 0:
                # Black image
                img = np.zeros((480, 640, 3), dtype=np.uint8)
            elif i % 4 == 1:
                # White image
                img = np.ones((480, 640, 3), dtype=np.uint8) * 255
            elif i % 4 == 2:
                # Random noise
                img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            else:
                # Gradient image
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                for y in range(480):
                    for x in range(640):
                        img[y, x] = [x % 255, y % 255, (x + y) % 255]
            
            images.append(img)
        
        return images
    
    def benchmark_detector(self, detector, detector_name: str, test_images: List[np.ndarray]) -> Dict:
        """Benchmark a pose detector"""
        print(f"\n🏃 Benchmarking {detector_name}...")
        
        frame_times = []
        total_landmarks = 0
        successful_detections = 0
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while time.time() - start_time < self.test_duration:
                for img in test_images:
                    if time.time() - start_time >= self.test_duration:
                        break
                    
                    frame_start = time.time()
                    
                    # Detect pose
                    result_img = detector.findPose(img, draw=False)
                    landmarks = detector.findPosition(img, draw=False)
                    
                    frame_end = time.time()
                    frame_time = frame_end - frame_start
                    frame_times.append(frame_time)
                    
                    if len(landmarks) > 0:
                        successful_detections += 1
                        total_landmarks += len(landmarks)
                    
                    frame_count += 1
                    
                    # Print progress
                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        fps = frame_count / elapsed
                        print(f"   Processed {frame_count} frames, {fps:.1f} FPS")
        
        except Exception as e:
            print(f"❌ Error during {detector_name} benchmark: {e}")
            return None
        
        # Calculate statistics
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time
        avg_frame_time = np.mean(frame_times)
        min_frame_time = np.min(frame_times)
        max_frame_time = np.max(frame_times)
        detection_rate = (successful_detections / frame_count) * 100
        
        results = {
            'detector_name': detector_name,
            'total_frames': frame_count,
            'total_time': total_time,
            'avg_fps': avg_fps,
            'avg_frame_time_ms': avg_frame_time * 1000,
            'min_frame_time_ms': min_frame_time * 1000,
            'max_frame_time_ms': max_frame_time * 1000,
            'successful_detections': successful_detections,
            'detection_rate_percent': detection_rate,
            'avg_landmarks_per_detection': total_landmarks / max(successful_detections, 1)
        }
        
        return results
    
    def print_results(self, results: Dict):
        """Print benchmark results"""
        if not results:
            return
        
        print(f"\n📊 {results['detector_name']} Results:")
        print(f"   Total Frames: {results['total_frames']}")
        print(f"   Total Time: {results['total_time']:.2f}s")
        print(f"   Average FPS: {results['avg_fps']:.2f}")
        print(f"   Average Frame Time: {results['avg_frame_time_ms']:.2f}ms")
        print(f"   Min Frame Time: {results['min_frame_time_ms']:.2f}ms")
        print(f"   Max Frame Time: {results['max_frame_time_ms']:.2f}ms")
        print(f"   Successful Detections: {results['successful_detections']}")
        print(f"   Detection Rate: {results['detection_rate_percent']:.1f}%")
        print(f"   Avg Landmarks per Detection: {results['avg_landmarks_per_detection']:.1f}")
    
    def compare_results(self, results_list: List[Dict]):
        """Compare multiple benchmark results"""
        if len(results_list) < 2:
            return
        
        print("\n🔍 Performance Comparison:")
        print("=" * 60)
        
        # Sort by FPS (descending)
        sorted_results = sorted(results_list, key=lambda x: x['avg_fps'], reverse=True)
        
        baseline = sorted_results[-1]  # Slowest as baseline
        
        for i, result in enumerate(sorted_results):
            if i == 0:
                print(f"🥇 Fastest: {result['detector_name']}")
            elif i == len(sorted_results) - 1:
                print(f"🐌 Baseline: {result['detector_name']}")
            else:
                print(f"📈 {result['detector_name']}")
            
            speedup = result['avg_fps'] / baseline['avg_fps']
            print(f"   FPS: {result['avg_fps']:.2f} ({speedup:.2f}x speedup)")
            print(f"   Frame Time: {result['avg_frame_time_ms']:.2f}ms")
            print()

def main():
    """Main benchmark function"""
    print("🚀 Pose Detection Performance Benchmark")
    print("=" * 50)
    
    # Check availability
    if not MEDIAPIPE_AVAILABLE and not QUALCOMM_AVAILABLE:
        print("❌ No pose detection implementations available!")
        return
    
    # Create benchmark
    benchmark = PerformanceBenchmark(test_duration=30)
    
    # Create test images
    print("🖼️  Creating test images...")
    test_images = benchmark.create_test_images(50)
    print(f"✅ Created {len(test_images)} test images")
    
    results_list = []
    
    # Benchmark MediaPipe
    if MEDIAPIPE_AVAILABLE:
        try:
            mp_detector = MediaPipePoseDetector()
            mp_results = benchmark.benchmark_detector(mp_detector, "MediaPipe", test_images)
            if mp_results:
                results_list.append(mp_results)
                benchmark.print_results(mp_results)
        except Exception as e:
            print(f"❌ MediaPipe benchmark failed: {e}")
    
    # Benchmark Qualcomm NPU
    if QUALCOMM_AVAILABLE:
        # Check if models exist
        if os.path.exists("models/mediapipe_pose-posedetector.onnx") and \
           os.path.exists("models/mediapipe_pose-poselandmarkdetector.onnx"):
            
            try:
                # Test with NPU enabled
                qc_detector_npu = QualcommPoseDetector(enable_npu=True)
                qc_results_npu = benchmark.benchmark_detector(qc_detector_npu, "Qualcomm NPU", test_images)
                if qc_results_npu:
                    results_list.append(qc_results_npu)
                    benchmark.print_results(qc_results_npu)
            except Exception as e:
                print(f"❌ Qualcomm NPU benchmark failed: {e}")
            
            try:
                # Test with CPU fallback
                qc_detector_cpu = QualcommPoseDetector(enable_npu=False)
                qc_results_cpu = benchmark.benchmark_detector(qc_detector_cpu, "Qualcomm CPU", test_images)
                if qc_results_cpu:
                    results_list.append(qc_results_cpu)
                    benchmark.print_results(qc_results_cpu)
            except Exception as e:
                print(f"❌ Qualcomm CPU benchmark failed: {e}")
        else:
            print("❌ Qualcomm ONNX models not found in models/ directory")
    
    # Compare results
    if len(results_list) > 1:
        benchmark.compare_results(results_list)
    
    print("\n🎯 Benchmark completed!")
    print("Note: Results may vary based on hardware, system load, and other factors.")

if __name__ == "__main__":
    main() 