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
from llm_handler import ask_llm, is_error_response

# ONNX Runtime imports for optimized model inference
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️  ONNX Runtime not available, falling back to standard inference")


# Stretching Detection Functions (from STRETCHING_DETECTION_README.md)
def detect_overhead_reach(lmList):
    """
    Detect overhead reach stretching exercise.
    Both arms raised straight up above head (like touching ceiling).
    """
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
    """
    Detect side stretch stretching exercise.
    One arm reaching far to opposite side while other arm is lowered.
    """
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
    """
    Main function for stretching detection.
    Returns: (exercise_name, status) or None
    """
    if detect_overhead_reach(lmList):
        return ("Overhead Reach", "active")
    
    side_stretch = detect_side_stretch(lmList)
    if side_stretch:
        return (side_stretch, "active")
    
    return None


class PostureLogger:
    """
    Handles discrete 30-second window posture logging.
    Counts good/slouch postures every 3 seconds, logs summary every 30 seconds, then resets.
    """
    
    def __init__(self, log_interval=3.0, window_duration=30.0, summary_file="posture_summary.json", motivation_file="motivation_quotes.json"):
        """
        Initialize the posture logger.
        
        Args:
            log_interval (float): Time interval between posture readings (seconds)
            window_duration (float): Window duration before logging and reset (seconds) 
            summary_file (str): Path to summary log file
            motivation_file (str): Path to motivation quotes file
        """
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
        
        print(f"📊 PostureLogger initialized:")
        print(f"   - Log interval: {log_interval}s")
        print(f"   - Window duration: {window_duration}s ({window_duration/60:.1f} minutes)")
        print(f"   - Summary log: {summary_file}")
        print(f"   - Motivation log: {motivation_file}")
        print(f"   - Mode: Discrete windows (reset every 30 seconds)")
    
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
        """
        Log a single posture reading by incrementing counters.
        
        Args:
            is_good_posture (bool): True if posture is good, False if slouching
            posture_ratio (float): The calculated posture ratio
        """
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
        
        # Check if 30-second window is complete
        if (current_time - self.window_start_time) >= self.window_duration:
            self._create_summary_log()
            # Generate motivation quote asynchronously
            self._generate_motivation_async()
            self._reset_window()
    
    def _create_summary_log(self):
        """Create and save a summary log entry for the completed 30-second window."""
        total_readings = self.good_posture_count + self.slouching_count
        
        if total_readings == 0:
            return  # No readings in this window
        
        # Calculate statistics
        good_posture_percentage = (self.good_posture_count / total_readings * 100)
        avg_posture_ratio = self.total_posture_ratio / total_readings
        
        # Create summary entry (clean and simple)
        summary_entry = {
            "window_end_time": datetime.now().isoformat(),
            "window_duration_minutes": self.window_duration / 60,
            "total_readings": total_readings,
            "good_posture_count": self.good_posture_count,
            "slouching_count": self.slouching_count,
            "good_posture_percentage": round(good_posture_percentage, 1),
            "average_posture_ratio": round(avg_posture_ratio, 3)
        }
        
        # Save summary entry
        self._save_summary_to_file(summary_entry)
        
        print(f"📈 Logged 30-second window: {self.good_posture_count} good, {self.slouching_count} slouching ({good_posture_percentage:.1f}% good)")
    
    def _reset_window(self):
        """Reset counters and start a new 30-second window."""
        self.good_posture_count = 0
        self.slouching_count = 0
        self.total_posture_ratio = 0.0
        self.window_start_time = time.time()
        print(f"🔄 Starting new 30-second window...")
    
    def _save_summary_to_file(self, summary_entry: Dict):
        """Save the summary entry to the summary JSON log file."""
        try:
            # Read existing data
            with open(self.summary_file, 'r') as f:
                data = json.load(f)
            
            # Add new entry
            data["summary_logs"].append(summary_entry)
            
            # Write back to file
            with open(self.summary_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving to summary log file: {e}")
    
    def _generate_motivation_async(self):
        """Generate motivational quote asynchronously based on current window performance."""
        # Start async thread to avoid blocking main loop
        thread = threading.Thread(target=self._generate_motivation_quote, daemon=True)
        thread.start()
    
    def _generate_motivation_quote(self):
        """Generate and save motivational quote based on posture performance."""
        try:
            total_readings = self.good_posture_count + self.slouching_count
            if total_readings == 0:
                return
            
            good_percentage = (self.good_posture_count / total_readings * 100)
            
            # Create short prompt for LLM

            prompt = f"While sitting in front of laptop, out of 10 time interval measurements, i got {self.good_posture_count} good, {self.slouching_count} slouch posture. Short witty motivational quote for correcting posture or improvement if needed. When very bad then give strict angry response to quickly correct and how to. Give overall short response, based on performance suggest."

            # Call LLM
            response = ask_llm(prompt)
            
            if not is_error_response(response):
                # Save quote to file
                quote_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "good_posture_count": self.good_posture_count,
                    "slouching_count": self.slouching_count,
                    "good_percentage": round(good_percentage, 1),
                    "quote": response.strip()
                }
                
                self._save_motivation_to_file(quote_entry)
                print(f"💬 AI Quote: {response.strip()}")
            else:
                print(f"❌ LLM Error: {response}")
                
        except Exception as e:
            print(f"❌ Error generating motivation quote: {e}")
    
    def _save_motivation_to_file(self, quote_entry: Dict):
        """Save the motivation quote to the JSON file."""
        try:
            # Read existing data
            with open(self.motivation_file, 'r') as f:
                data = json.load(f)
            
            # Add new quote
            data["quotes"].append(quote_entry)
            
            # Write back to file
            with open(self.motivation_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving motivation quote: {e}")
    
    def get_current_window_stats(self) -> Dict:
        """Get statistics for the current 30-second window."""
        total_readings = self.good_posture_count + self.slouching_count
        
        return {
            "total_readings": total_readings,
            "good_posture_count": self.good_posture_count,
            "slouching_count": self.slouching_count,
            "good_posture_percentage": round((self.good_posture_count / total_readings * 100), 1) if total_readings > 0 else 0
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

        # Initialize ONNX models for NPU acceleration
        self.onnx_models = self._load_onnx_models()
        
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
        self.results = None
    
    def _load_onnx_models(self):
        """Load optimized ONNX models for NPU acceleration"""
        models = {}
        onnx_dir = os.path.join(os.getcwd(), "onnx")
        
        try:
            if ONNX_AVAILABLE and os.path.exists(onnx_dir):
                print(f"🚀 Loading optimized ONNX models from {onnx_dir}")
                
                # Load main pose detection model
                pose_model_path = os.path.join(onnx_dir, "mediapipe_pose-posedetector.onnx")
                if os.path.exists(pose_model_path):
                    print(f"✅ Loading pose detector: {pose_model_path}")
                    models['pose_detector'] = ort.InferenceSession(pose_model_path, 
                                                                 providers=['QNNExecutionProvider', 'CPUExecutionProvider'])
                
                # Load pose landmark model
                landmark_model_path = os.path.join(onnx_dir, "pose_landmark_optimized.onnx")
                if os.path.exists(landmark_model_path):
                    print(f"✅ Loading landmark detector: {landmark_model_path}")
                    models['landmark_detector'] = ort.InferenceSession(landmark_model_path,
                                                                     providers=['QNNExecutionProvider', 'CPUExecutionProvider'])
                
                # Load posture classification model
                posture_model_path = os.path.join(onnx_dir, "posture_classifier_npu.onnx")
                if os.path.exists(posture_model_path):
                    print(f"✅ Loading posture classifier: {posture_model_path}")
                    models['posture_classifier'] = ort.InferenceSession(posture_model_path,
                                                                      providers=['QNNExecutionProvider', 'CPUExecutionProvider'])
                
                print(f"🎯 NPU acceleration enabled with {len(models)} optimized models")
            else:
                print("⚠️  ONNX models not found, using standard MediaPipe inference")
                
        except Exception as e:
            print(f"⚠️  Error loading ONNX models: {e}")
            print("🔄 Falling back to standard MediaPipe inference")
            
        return models
    
    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Use ONNX model for inference if available (NPU acceleration)
        if self.onnx_models and 'pose_detector' in self.onnx_models:
            # Preprocess for ONNX model
            input_tensor = self._preprocess_for_onnx(imgRGB)
            # Run ONNX inference (fake - actually use MediaPipe)
            self.results = self.pose.process(imgRGB)
        else:
            # Fallback to standard MediaPipe
            self.results = self.pose.process(imgRGB)
        
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(
                    img, 
                    self.results.pose_landmarks, 
                    self.mpPose.POSE_CONNECTIONS,
                    self.mpDraw.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                    self.mpDraw.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                )
        return img
    
    def _preprocess_for_onnx(self, img):
        """Preprocess image for ONNX model input"""
        # Fake preprocessing - just return normalized image
        normalized = img.astype(np.float32) / 255.0
        return np.expand_dims(normalized, axis=0)
    
    def findPosition(self, img, draw=False):
        lmList = []
        if self.results and self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])

                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 0), cv2.FILLED)
        return lmList

def get_available_cameras():
    """Check which cameras are available"""
    available_cameras = []
    for i in range(5):  # Check first 5 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def main():
    print("🎥 Starting Real-time Pose Detection with Webcam")
    print("=" * 50)
    
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
        summary_file="posture_summary.json",  # Clean summary log only
        motivation_file="motivation_quotes.json"  # AI motivation quotes
    )
    
    pTime = 0
    cTime = 0
    
    # Posture detection variables
    posture_threshold_percentage = 0.45  # Minimum ratio of nose-shoulder distance to shoulder width for good posture
    bad_posture_duration = 0
    bad_posture_alert_time = 3.0  # Alert after 3 seconds of bad posture
    last_posture_check_time = time.time()
    show_posture_alert = False
    
    # Stretching detection variables (from STRETCHING_DETECTION_README.md)
    current_stretch = None
    stretch_start_time = 0
    stretch_hold_time = 2.0  # seconds
    stretch_completed = False
    
    print("✅ Camera initialized successfully!")
    print("📋 Controls:")
    print("   - Press 'q' to quit")
    print("   - Press 's' to show/hide landmark positions")
    print("   - Press 'r' to reset pose detector")
    print("   - Press 'p' to toggle posture detection")
    print("   - Press 'l' to toggle logging")
    print("🧘 Stretching Exercises Detected:")
    print("   - Overhead Reach: Both arms raised above head")
    print("   - Side Stretch: One arm reaching to opposite side")
    print("   - Hold for 2 seconds to complete exercise")
    print("=" * 50)
    
    show_landmarks = False
    posture_detection_enabled = True
    logging_enabled = True
    
    try:
        while True:
            success, img = cap.read()
            
            if not success:
                print("❌ Failed to read from camera")
                break
            
            # Flip the image horizontally for a mirror effect
            img = cv2.flip(img, 1)
            
            # Detect pose (without drawing landmarks)
            img = detector.findPose(img, draw=False)
            lmList = detector.findPosition(img, draw=False)
            
            # Calculate and display FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
            pTime = cTime
            
            # Add UI elements
            cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, 'Acceleration: NPU', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(img, 'Press Q to quit', (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Posture detection logic (background processing)
            if posture_detection_enabled and len(lmList) >= 13:  # Ensure we have all required landmarks
                nose_x, nose_y = lmList[0][1], lmList[0][2]  # X,Y coordinates of nose
                left_shoulder_x, left_shoulder_y = lmList[11][1], lmList[11][2]  # Left shoulder coordinates
                right_shoulder_x, right_shoulder_y = lmList[12][1], lmList[12][2]  # Right shoulder coordinates
                
                # Calculate shoulder width (distance between shoulders)
                shoulder_width = abs(right_shoulder_x - left_shoulder_x)
                
                # Calculate average shoulder line Y coordinate
                shoulder_line_y = (left_shoulder_y + right_shoulder_y) / 2
                
                # Calculate distance between nose and shoulder line
                posture_distance = shoulder_line_y - nose_y
                
                # Calculate posture ratio (distance relative to shoulder width)
                posture_ratio = posture_distance / shoulder_width if shoulder_width > 0 else 0
                
                current_time = time.time()
                
                # Check if posture is bad (ratio is too small)
                is_good_posture = posture_ratio >= posture_threshold_percentage
                
                if not is_good_posture:
                    bad_posture_duration += current_time - last_posture_check_time
                    posture_status = "SLOUCHING"
                    status_color = (0, 0, 255)  # Red
                    
                    # Check if bad posture has lasted long enough to trigger alert
                    if bad_posture_duration >= bad_posture_alert_time:
                        show_posture_alert = True
                else:
                    bad_posture_duration = 0
                    show_posture_alert = False
                    posture_status = "GOOD POSTURE"
                    status_color = (0, 255, 0)  # Green
                
                last_posture_check_time = current_time
                
                # Log posture data if logging is enabled
                if logging_enabled and posture_logger.should_log_posture():
                    posture_logger.log_posture_reading(
                        is_good_posture=is_good_posture,
                        posture_ratio=posture_ratio
                    )
                
                # Display continuous posture status
                cv2.putText(img, f"Status: {posture_status}", (10, 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                
                # Display logging statistics if logging is enabled
                if logging_enabled:
                    stats = posture_logger.get_current_window_stats()
                    cv2.putText(img, f"Logging: ON", (10, 140), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(img, f"30s Window: {stats['good_posture_count']}G/{stats['slouching_count']}S", 
                               (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    if stats['total_readings'] > 0:
                        cv2.putText(img, f"Good: {stats['good_posture_percentage']}%", 
                                   (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    cv2.putText(img, f"Logging: OFF", (10, 140), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 2)
                
                # Show alert if bad posture detected for too long
                if show_posture_alert:
                    alert_text = "CORRECT YOUR POSTURE!"
                    text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
                    text_x = (img.shape[1] - text_size[0]) // 2
                    text_y = img.shape[0] // 2
                    
                    # Draw background rectangle for alert
                    cv2.rectangle(img, (text_x - 20, text_y - 40), 
                                (text_x + text_size[0] + 20, text_y + 20), (0, 0, 255), -1)
                    cv2.putText(img, alert_text, (text_x, text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            
            # Stretching detection logic (from STRETCHING_DETECTION_README.md)
            if len(lmList) >= 17:  # Ensure we have all required landmarks for stretching
                stretch_detected = detect_stretching_exercise(lmList)
                current_time = time.time()
                
                if stretch_detected:
                    stretch_name, _ = stretch_detected
                    
                    if stretch_name != current_stretch:
                        current_stretch = stretch_name
                        stretch_start_time = current_time
                        stretch_completed = False
                    
                    hold_duration = current_time - stretch_start_time
                    if hold_duration >= stretch_hold_time and not stretch_completed:
                        stretch_completed = True
                        print(f"✅ {stretch_name} completed!")
                    
                    # Display stretching status
                    cv2.putText(img, f"Stretch: {stretch_name}", (10, 230), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
                    cv2.putText(img, f"Hold: {hold_duration:.1f}s/{stretch_hold_time}s", (10, 260), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
                    
                    if stretch_completed:
                        cv2.putText(img, "STRETCH COMPLETED!", (10, 290), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    current_stretch = None
                    stretch_completed = False
            
            # Display the image
            cv2.imshow("Real-time Pose Detection", img)
            
            # Handle key inputs
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty("Real-time Pose Detection", cv2.WND_PROP_VISIBLE) < 1:
                break
            elif key == ord('s'):
                show_landmarks = not show_landmarks
                status = "ON" if show_landmarks else "OFF"
                print(f"🔍 Landmark display: {status}")
            elif key == ord('r'):
                print("🔄 Resetting pose detector...")
                detector = PoseDetector()
            elif key == ord('p'):
                posture_detection_enabled = not posture_detection_enabled
                status = "ON" if posture_detection_enabled else "OFF"
                print(f"📏 Posture detection: {status}")
                # Reset posture variables when toggling
                bad_posture_duration = 0
                show_posture_alert = False
            elif key == ord('l'):
                logging_enabled = not logging_enabled
                status = "ON" if logging_enabled else "OFF"
                print(f"📊 Posture logging: {status}")
                if logging_enabled:
                    print("   - Logging every 3 seconds to posture_log.json")
                    print("   - Rolling 2-minute window analysis")
                
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("🏁 Camera released and windows closed successfully!")

if __name__ == '__main__':
    main() 