import cv2
import numpy as np
import time
import onnxruntime as ort
import os

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
        self.results = None
        self.pose_landmarks = None
        
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
            
            # Create CPU-based sessions
            self.pose_detector_session = ort.InferenceSession(
                detector_path,
                providers=['CPUExecutionProvider']
            )
            
            self.landmark_detector_session = ort.InferenceSession(
                landmark_path,
                providers=['CPUExecutionProvider']
            )
            
            print("✅ ONNX models loaded successfully!")
            
            # Print model info
            print(f"📊 Pose Detector - Input: {self.pose_detector_session.get_inputs()[0].shape}")
            print(f"📊 Landmark Detector - Input: {self.landmark_detector_session.get_inputs()[0].shape}")
            
        except Exception as e:
            print(f"❌ Error loading ONNX models: {e}")
            raise
    
    def _preprocess_image(self, img, target_size):
        """Preprocess image for ONNX model input"""
        # Resize image
        resized = cv2.resize(img, target_size)
        
        # Convert BGR to RGB
        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0,1]
        normalized = rgb_img.astype(np.float32) / 255.0
        
        # Convert to NCHW format (batch, channels, height, width)
        input_tensor = np.transpose(normalized, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)
        
        return input_tensor
    
    def _detect_poses(self, img):
        """Run pose detection"""
        # Preprocess for pose detector (128x128)
        input_tensor = self._preprocess_image(img, (128, 128))
        
        # Run inference
        inputs = {self.pose_detector_session.get_inputs()[0].name: input_tensor}
        outputs = self.pose_detector_session.run(None, inputs)
        
        # outputs[0] = box_coords [1,896,12], outputs[1] = box_scores [1,896,1]
        box_coords = outputs[0][0]  # [896, 12]
        box_scores = outputs[1][0]  # [896, 1]
        
        # Find the best detection
        best_score_idx = np.argmax(box_scores)
        best_score = box_scores[best_score_idx][0]
        
        print(f"🎯 Best detection score: {best_score:.3f}")
        
        if best_score > self.minDetectionConfidence:
            best_box = box_coords[best_score_idx]
            return best_box, best_score
        
        return None, 0.0
    
    def _extract_pose_region(self, img, box_coords):
        """Extract pose region from image based on detection box"""
        h, w = img.shape[:2]
        
        # The box format needs to be interpreted correctly
        # For now, let's use the center region approach
        # This might need adjustment based on the actual box format
        center_x, center_y = w // 2, h // 2
        size = min(w, h)
        
        x1 = max(0, center_x - size // 2)
        y1 = max(0, center_y - size // 2)
        x2 = min(w, center_x + size // 2)
        y2 = min(h, center_y + size // 2)
        
        return img[y1:y2, x1:x2], (x1, y1, x2 - x1, y2 - y1)
    
    def _detect_landmarks(self, pose_region):
        """Run landmark detection on pose region"""
        # Preprocess for landmark detector (256x256)
        input_tensor = self._preprocess_image(pose_region, (256, 256))
        
        # Run inference
        inputs = {self.landmark_detector_session.get_inputs()[0].name: input_tensor}
        outputs = self.landmark_detector_session.run(None, inputs)
        
        # outputs[0] = scores [1], outputs[1] = landmarks [1,31,4]
        landmark_score = outputs[0][0]
        landmarks = outputs[1][0]  # [31, 4] where each point is [x, y, z, visibility]
        
        print(f"🎯 Landmark score: {landmark_score:.3f}")
        print(f"📍 Landmarks shape: {landmarks.shape}")
        
        return landmarks, landmark_score
    
    def _convert_landmarks_to_mediapipe_format(self, landmarks, pose_region_info):
        """Convert ONNX landmarks to MediaPipe-compatible format"""
        # landmarks: [31, 4] with [x, y, z, visibility]
        # pose_region_info: (x_offset, y_offset, width, height)
        
        x_offset, y_offset, region_width, region_height = pose_region_info
        
        # Create MediaPipe-style landmark objects
        class LandmarkPoint:
            def __init__(self, x, y, z, visibility):
                self.x = x
                self.y = y
                self.z = z
                self.visibility = visibility
        
        class PoseLandmarks:
            def __init__(self):
                self.landmark = []
        
        pose_landmarks = PoseLandmarks()
        
        # Map 31 landmarks to MediaPipe's 33 landmarks
        # We'll fill the available ones and set others to default values
        mediapipe_landmarks = [LandmarkPoint(0.5, 0.5, 0.0, 0.0) for _ in range(33)]
        
        for i, lm in enumerate(landmarks):
            if i < 31:  # We have 31 landmarks from ONNX model
                x, y, z, visibility = lm
                
                # Convert from normalized coordinates to image coordinates
                # Then back to normalized coordinates for MediaPipe compatibility
                abs_x = (x * region_width + x_offset)
                abs_y = (y * region_height + y_offset)
                
                # Create landmark point
                if i < 33:  # Only if within MediaPipe's 33 landmarks
                    mediapipe_landmarks[i] = LandmarkPoint(
                        x=abs_x,  # We'll normalize this later
                        y=abs_y,  # We'll normalize this later
                        z=z,
                        visibility=visibility
                    )
        
        pose_landmarks.landmark = mediapipe_landmarks
        return pose_landmarks
    
    def findPose(self, img, draw=True):
        """Find pose in image - main detection method"""
        self.pose_landmarks = None
        
        try:
            # Step 1: Detect pose
            box_coords, detection_score = self._detect_poses(img)
            
            if box_coords is not None:
                # Step 2: Extract pose region
                pose_region, region_info = self._extract_pose_region(img, box_coords)
                
                # Step 3: Detect landmarks
                landmarks, landmark_score = self._detect_landmarks(pose_region)
                
                if landmark_score > self.minTrackingConfidence:
                    # Convert to MediaPipe format
                    self.pose_landmarks = self._convert_landmarks_to_mediapipe_format(landmarks, region_info)
                    
                    # Draw landmarks if requested
                    if draw and self.pose_landmarks:
                        self._draw_landmarks(img, self.pose_landmarks)
            
        except Exception as e:
            print(f"❌ Error in pose detection: {e}")
        
        return img
    
    def _draw_landmarks(self, img, pose_landmarks):
        """Draw pose landmarks on image"""
        h, w = img.shape[:2]
        
        # Draw landmarks
        for i, landmark in enumerate(pose_landmarks.landmark):
            if landmark.visibility > 0.5:  # Only draw visible landmarks
                x = int(landmark.x if landmark.x < 1.0 else landmark.x / w)
                y = int(landmark.y if landmark.y < 1.0 else landmark.y / h)
                
                if landmark.x >= 1.0:  # Already in pixel coordinates
                    x = int(landmark.x)
                    y = int(landmark.y)
                else:  # Normalized coordinates
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                
                # Draw landmark point
                cv2.circle(img, (x, y), 3, (0, 255, 0), -1)
                
                # Draw landmark ID for debugging
                cv2.putText(img, str(i), (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    def findPosition(self, img, draw=False):
        """Get landmark positions in pixel coordinates"""
        lmList = []
        
        if self.pose_landmarks:
            h, w = img.shape[:2]
            
            for id, lm in enumerate(self.pose_landmarks.landmark):
                if lm.visibility > 0.5:  # Only include visible landmarks
                    # Convert to pixel coordinates
                    if lm.x >= 1.0:  # Already in pixel coordinates
                        cx, cy = int(lm.x), int(lm.y)
                    else:  # Normalized coordinates
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
    print("🎥 Starting Real-time Pose Detection with ONNX Models (CPU)")
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
    try:
        detector = PoseDetector()
    except Exception as e:
        print(f"❌ Failed to initialize pose detector: {e}")
        return
    
    pTime = 0
    cTime = 0
    
    print("✅ ONNX Pose Detector initialized successfully!")
    print("📋 Controls:")
    print("   - Press 'q' to quit")
    print("   - Press 's' to show/hide landmark positions")
    print("   - Press 'r' to reset pose detector")
    print("=" * 50)
    
    show_landmarks = False
    
    try:
        while True:
            success, img = cap.read()
            
            if not success:
                print("❌ Failed to read from camera")
                break
            
            # Flip the image horizontally for a mirror effect
            img = cv2.flip(img, 1)
            
            # Detect pose
            img = detector.findPose(img)
            lmList = detector.findPosition(img, draw=show_landmarks)
            
            # Calculate and display FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
            pTime = cTime
            
            # Add UI elements
            cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, f'Landmarks: {len(lmList)}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(img, 'ONNX CPU Mode', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(img, 'Press Q to quit', (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show specific landmark points if detected
            if len(lmList) != 0:
                # Highlight specific important landmarks
                # Nose (0), Left shoulder (11), Right shoulder (12), Left hip (23), Right hip (24)
                important_landmarks = [0, 11, 12, 23, 24]
                for landmark_id in important_landmarks:
                    if landmark_id < len(lmList):
                        cv2.circle(img, (lmList[landmark_id][1], lmList[landmark_id][2]), 10, (0, 255, 255), cv2.FILLED)
            
            # Display the image
            cv2.imshow("ONNX Pose Detection (CPU)", img)
            
            # Handle key inputs
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty("ONNX Pose Detection (CPU)", cv2.WND_PROP_VISIBLE) < 1:
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