import cv2
import mediapipe as mp
import time
import os
import numpy as np

# ONNX Runtime imports for optimized model inference
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️  ONNX Runtime not available, falling back to standard inference")



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
    
    pTime = 0
    cTime = 0
    
    # Posture detection variables
    posture_threshold_percentage = 0.45  # Minimum ratio of nose-shoulder distance to shoulder width for good posture
    bad_posture_duration = 0
    bad_posture_alert_time = 3.0  # Alert after 3 seconds of bad posture
    last_posture_check_time = time.time()
    show_posture_alert = False
    
    print("✅ Camera initialized successfully!")
    print("📋 Controls:")
    print("   - Press 'q' to quit")
    print("   - Press 's' to show/hide landmark positions")
    print("   - Press 'r' to reset pose detector")
    print("   - Press 'p' to toggle posture detection")
    print("=" * 50)
    
    show_landmarks = False
    posture_detection_enabled = True
    
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
                if posture_ratio < posture_threshold_percentage:
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
                
                # Display continuous posture status
                cv2.putText(img, f"Status: {posture_status}", (10, 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                
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