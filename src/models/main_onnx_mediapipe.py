import cv2
import numpy as np
import time
import onnxruntime as ort
import os

# MediaPipe pose connections (same as MediaPipe's POSE_CONNECTIONS)
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32)
]

class DrawingSpec:
    def __init__(self, color=(255, 255, 255), thickness=2, circle_radius=2):
        self.color = color
        self.thickness = thickness
        self.circle_radius = circle_radius

class LandmarkPoint:
    def __init__(self, x, y, z, visibility=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

class PoseLandmarks:
    def __init__(self):
        self.landmark = []

class PoseResults:
    def __init__(self):
        self.pose_landmarks = None

class PoseDetector():
    def __init__(self, staticImageMode=False, modelComplexity=1, smoothLandmarks=True, enableSegmentation=False, smoothSegmentation=True, minDetectionConfidence=0.5, minTrackingConfidence=0.5):
        self.staticImageMode = staticImageMode
        self.modelComplexity = modelComplexity
        self.smoothLandmarks = smoothLandmarks
        self.enableSegmentation = enableSegmentation
        self.smoothSegmentation = smoothSegmentation
        self.minDetectionConfidence = minDetectionConfidence
        self.minTrackingConfidence = minTrackingConfidence

        # Initialize ONNX Runtime sessions
        self.pose_detector_session = None
        self.landmark_detector_session = None
        self.results = PoseResults()
        
        self._load_models()
    
    def _load_models(self):
        """Load ONNX models"""
        try:
            model_dir = "models"
            detector_path = os.path.join(model_dir, "mediapipe_pose-posedetector.onnx")
            landmark_path = os.path.join(model_dir, "mediapipe_pose-poselandmarkdetector.onnx")
            
            if not os.path.exists(detector_path):
                raise FileNotFoundError(f"Pose detector model not found: {detector_path}")
            if not os.path.exists(landmark_path):
                raise FileNotFoundError(f"Landmark detector model not found: {landmark_path}")
            
            print("🔄 Loading ONNX models...")
            
            # Create CPU-based sessions with optimized settings
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.pose_detector_session = ort.InferenceSession(
                detector_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            self.landmark_detector_session = ort.InferenceSession(
                landmark_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            print("✅ ONNX models loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading ONNX models: {e}")
            raise
    
    def _preprocess_image(self, img, target_size):
        """Preprocess image for ONNX model input"""
        # Resize image
        resized = cv2.resize(img, target_size)
        
        # Normalize to [0,1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Convert to NCHW format (batch, channels, height, width)
        input_tensor = np.transpose(normalized, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)
        
        return input_tensor
    
    def findPose(self, img, draw=True):
        """Find pose in image - main detection method (MediaPipe compatible)"""
        # Convert BGR to RGB for processing (like MediaPipe)
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Reset results
        self.results.pose_landmarks = None
        
        try:
            # Step 1: Run pose detection
            input_tensor = self._preprocess_image(imgRGB, (128, 128))
            inputs = {self.pose_detector_session.get_inputs()[0].name: input_tensor}
            outputs = self.pose_detector_session.run(None, inputs)
            
            # outputs[0] = box_coords [1,896,12], outputs[1] = box_scores [1,896,1]
            box_scores = outputs[1][0]  # [896, 1]
            best_score = np.max(box_scores)
            
            if best_score > self.minDetectionConfidence:
                # Step 2: Run landmark detection on full image
                landmark_input = self._preprocess_image(imgRGB, (256, 256))
                landmark_inputs = {self.landmark_detector_session.get_inputs()[0].name: landmark_input}
                landmark_outputs = self.landmark_detector_session.run(None, landmark_inputs)
                
                # outputs[0] = scores [1], outputs[1] = landmarks [1,31,4]
                landmark_score = landmark_outputs[0][0]
                landmarks = landmark_outputs[1][0]  # [31, 4] where each point is [x, y, z, visibility]
                
                if landmark_score > self.minTrackingConfidence:
                    # Convert to MediaPipe format
                    self.results.pose_landmarks = self._convert_landmarks_to_mediapipe_format(landmarks, img.shape)
                    
                    # Draw landmarks if requested (same as MediaPipe)
                    if draw and self.results.pose_landmarks:
                        self._draw_landmarks(
                            img, 
                            self.results.pose_landmarks, 
                            POSE_CONNECTIONS,
                            DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                            DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                        )
            
        except Exception as e:
            print(f"❌ Error in pose detection: {e}")
        
        return img
    
    def _convert_landmarks_to_mediapipe_format(self, landmarks, img_shape):
        """Convert ONNX landmarks to MediaPipe-compatible format"""
        pose_landmarks = PoseLandmarks()
        mediapipe_landmarks = []
        
        # Create 33 landmarks (MediaPipe standard)
        for i in range(33):
            if i < len(landmarks):
                x, y, z, visibility = landmarks[i]
                
                # Ensure coordinates are in [0,1] range
                x = max(0.0, min(1.0, x))
                y = max(0.0, min(1.0, y))
                
                landmark = LandmarkPoint(
                    x=x,
                    y=y,
                    z=z,
                    visibility=visibility
                )
            else:
                # Default landmark for missing points
                landmark = LandmarkPoint(x=0.5, y=0.5, z=0.0, visibility=0.0)
            
            mediapipe_landmarks.append(landmark)
        
        pose_landmarks.landmark = mediapipe_landmarks
        return pose_landmarks
    
    def _draw_landmarks(self, img, pose_landmarks, connections, landmark_drawing_spec, connection_drawing_spec):
        """Draw pose landmarks and connections (MediaPipe compatible)"""
        if not pose_landmarks or not pose_landmarks.landmark:
            return
        
        h, w = img.shape[:2]
        
        # Draw connections first (like MediaPipe)
        if connections:
            for connection in connections:
                start_idx, end_idx = connection
                if (start_idx < len(pose_landmarks.landmark) and 
                    end_idx < len(pose_landmarks.landmark)):
                    
                    start_landmark = pose_landmarks.landmark[start_idx]
                    end_landmark = pose_landmarks.landmark[end_idx]
                    
                    # Only draw if both landmarks are visible
                    if (start_landmark.visibility > 0.1 and 
                        end_landmark.visibility > 0.1):
                        
                        start_x = int(start_landmark.x * w)
                        start_y = int(start_landmark.y * h)
                        end_x = int(end_landmark.x * w)
                        end_y = int(end_landmark.y * h)
                        
                        cv2.line(img, (start_x, start_y), (end_x, end_y), 
                                connection_drawing_spec.color, 
                                connection_drawing_spec.thickness)
        
        # Draw landmark points (like MediaPipe)
        for i, landmark in enumerate(pose_landmarks.landmark):
            if landmark.visibility > 0.1:  # Lower threshold for visibility
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                
                cv2.circle(img, (x, y), 
                          landmark_drawing_spec.circle_radius, 
                          landmark_drawing_spec.color, 
                          landmark_drawing_spec.thickness)
    
    def findPosition(self, img, draw=False):
        """Get landmark positions in pixel coordinates (MediaPipe compatible)"""
        lmList = []
        
        if self.results and self.results.pose_landmarks:
            h, w, c = img.shape
            
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                if lm.visibility > 0.1:  # Lower threshold for visibility
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
    print("🎥 Starting Real-time Pose Detection with ONNX Models")
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
    
    # Initialize pose detector first
    try:
        print("🔄 Initializing pose detector...")
        detector = PoseDetector()
        print("✅ ONNX Pose Detector initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize pose detector: {e}")
        return
    
    # Initialize camera after detector
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera!")
        return
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Wait a moment for camera to initialize
    time.sleep(1)
    
    pTime = 0
    cTime = 0
    
    print("📋 Controls:")
    print("   - Press 'q' to quit")
    print("   - Press 's' to show/hide landmark positions")
    print("   - Press 'r' to reset pose detector")
    print("=" * 50)
    
    show_landmarks = False
    frame_count = 0
    
    try:
        while True:
            success, img = cap.read()
            
            if not success:
                print(f"❌ Failed to read from camera (frame {frame_count})")
                # Try to reinitialize camera
                cap.release()
                time.sleep(0.1)
                cap = cv2.VideoCapture(camera_id)
                if not cap.isOpened():
                    break
                continue
            
            frame_count += 1
            
            # Flip the image horizontally for a mirror effect
            img = cv2.flip(img, 1)
            
            # Detect pose (same as MediaPipe)
            img = detector.findPose(img)
            lmList = detector.findPosition(img, draw=show_landmarks)
            
            # Calculate and display FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
            pTime = cTime
            
            # Add UI elements (same as original)
            cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, f'Landmarks: {len(lmList)}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(img, 'ONNX Mode', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(img, 'Press Q to quit', (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show specific landmark points if detected (same as original)
            if len(lmList) != 0:
                # Highlight specific important landmarks
                # Nose (0), Left shoulder (11), Right shoulder (12), Left hip (23), Right hip (24)
                important_landmarks = [0, 11, 12, 23, 24]
                for landmark_id in important_landmarks:
                    if landmark_id < len(lmList):
                        cv2.circle(img, (lmList[landmark_id][1], lmList[landmark_id][2]), 10, (0, 255, 255), cv2.FILLED)
            
            # Display the image (same window name as original)
            cv2.imshow("Real-time Pose Detection", img)
            
            # Handle key inputs (same as original)
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