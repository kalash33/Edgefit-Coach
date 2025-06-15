import cv2
import numpy as np
import onnxruntime as ort
import time
import os
from typing import List, Tuple, Optional

class QualcommPoseDetector:
    """
    Qualcomm NPU-optimized Pose Detector using ONNX Runtime with QNN Execution Provider.
    Replaces MediaPipe with Qualcomm's optimized models for better performance on Snapdragon devices.
    """
    
    def __init__(self, 
                 detector_model_path: str = "models/mediapipe_pose-posedetector.onnx",
                 landmark_model_path: str = "models/mediapipe_pose-poselandmarkdetector.onnx",
                 min_detection_confidence: float = 0.5,
                 enable_npu: bool = True):
        """
        Initialize Qualcomm Pose Detector
        
        Args:
            detector_model_path: Path to pose detector ONNX model
            landmark_model_path: Path to pose landmark detector ONNX model  
            min_detection_confidence: Minimum confidence for pose detection
            enable_npu: Whether to use Qualcomm NPU (HTP backend)
        """
        self.min_detection_confidence = min_detection_confidence
        self.enable_npu = enable_npu
        self.results = None
        
        # Verify model files exist
        if not os.path.exists(detector_model_path):
            raise FileNotFoundError(f"Detector model not found: {detector_model_path}")
        if not os.path.exists(landmark_model_path):
            raise FileNotFoundError(f"Landmark model not found: {landmark_model_path}")
        
        # Initialize ONNX Runtime sessions with QNN Execution Provider
        self.detector_session = self._create_ort_session(detector_model_path, "PoseDetector")
        self.landmark_session = self._create_ort_session(landmark_model_path, "PoseLandmarkDetector")
        
        # MediaPipe pose connections for drawing
        self.pose_connections = [
            (0, 1), (1, 2), (2, 3), (3, 7),  # Face
            (0, 4), (4, 5), (5, 6), (6, 8),  # Face
            (9, 10),  # Mouth
            (11, 12),  # Shoulders
            (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),  # Left arm
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),  # Right arm
            (11, 23), (12, 24), (23, 24),  # Torso
            (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),  # Left leg
            (24, 26), (26, 28), (28, 30), (30, 32), (28, 32)   # Right leg
        ]
        
        print(f"✅ Qualcomm Pose Detector initialized with NPU: {enable_npu}")
    
    def _create_ort_session(self, model_path: str, model_name: str) -> ort.InferenceSession:
        """Create ONNX Runtime session with Qualcomm QNN execution provider"""
        try:
            # Session options
            session_options = ort.SessionOptions()
            session_options.log_severity_level = 3  # Reduce logging
            
            if self.enable_npu:
                # Configure for Qualcomm NPU (HTP backend)
                providers = ['QNNExecutionProvider']
                provider_options = [{
                    'backend_path': 'QnnHtp.dll',  # Windows path - adjust for Linux: libQnnHtp.so
                    'htp_performance_mode': 'high_performance',
                    'enable_htp_fp16_precision': '1',
                    'htp_graph_finalization_optimization_mode': '3'
                }]
                
                # Optionally disable CPU fallback to ensure NPU usage
                session_options.add_session_config_entry("session.disable_cpu_ep_fallback", "0")
                
                print(f"🚀 Creating {model_name} session with Qualcomm NPU acceleration...")
            else:
                # Fallback to CPU
                providers = ['CPUExecutionProvider']
                provider_options = [{}]
                print(f"💻 Creating {model_name} session with CPU...")
            
            session = ort.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=providers,
                provider_options=provider_options
            )
            
            # Print session info
            print(f"✅ {model_name} loaded successfully")
            print(f"   - Providers: {session.get_providers()}")
            print(f"   - Input shapes: {[(inp.name, inp.shape) for inp in session.get_inputs()]}")
            
            return session
            
        except Exception as e:
            print(f"⚠️  Failed to create {model_name} with NPU, falling back to CPU...")
            print(f"   Error: {e}")
            
            # Fallback to CPU
            session_options = ort.SessionOptions()
            session_options.log_severity_level = 3
            
            return ort.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=['CPUExecutionProvider']
            )
    
    def _preprocess_image(self, image: np.ndarray, target_size: Tuple[int, int] = (256, 256)) -> np.ndarray:
        """
        Preprocess image for pose detection
        
        Args:
            image: Input BGR image
            target_size: Target size (width, height)
            
        Returns:
            Preprocessed image tensor in NCHW format
        """
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize to model input size
        resized = cv2.resize(rgb_image, target_size)
        
        # Normalize to [0, 1] and convert to float32
        normalized = resized.astype(np.float32) / 255.0
        
        # Convert from HWC to CHW format
        chw_image = np.transpose(normalized, (2, 0, 1))
        
        # Add batch dimension: (1, C, H, W)
        input_tensor = np.expand_dims(chw_image, axis=0)
        
        return input_tensor
    
    def _detect_pose(self, image: np.ndarray) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Run pose detection on preprocessed image
        
        Args:
            image: Preprocessed image tensor (1, 3, 128, 128)
            
        Returns:
            (box_coords, box_scores) or None if no pose detected
        """
        try:
            # Resize image for detector (128x128)
            detector_input = self._preprocess_image(cv2.resize(
                cv2.cvtColor((image[0].transpose(1,2,0) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), 
                (128, 128)), (128, 128))
            
            # Get input name
            input_name = self.detector_session.get_inputs()[0].name
            
            # Run inference
            outputs = self.detector_session.run(None, {input_name: detector_input})
            
            # Extract outputs: box_coords (1, 896, 12), box_scores (1, 896, 1)
            box_coords = outputs[0]  # Shape: (1, 896, 12)
            box_scores = outputs[1]  # Shape: (1, 896, 1)
            
            # Apply sigmoid to scores to get probabilities (with overflow protection)
            scores = 1.0 / (1.0 + np.exp(-np.clip(box_scores, -500, 500)))
            
            # Check if any detections meet confidence threshold
            max_score = np.max(scores)
            print(f"Debug: Max detection score: {max_score:.4f}, threshold: {self.min_detection_confidence}")
            if max_score > self.min_detection_confidence:
                return box_coords, scores
            
            return None
            
        except Exception as e:
            print(f"❌ Error in pose detection: {e}")
            return None
    
    def _detect_landmarks(self, image: np.ndarray, detection: Tuple[np.ndarray, np.ndarray]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Detect pose landmarks from image region
        
        Args:
            image: Preprocessed image tensor (1, 3, 256, 256)
            detection: (box_coords, box_scores) from pose detector
            
        Returns:
            (scores, landmarks) or None if detection failed
        """
        try:
            # Resize image for landmark detector (256x256)
            landmark_input = self._preprocess_image(cv2.resize(
                cv2.cvtColor((image[0].transpose(1,2,0) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), 
                (256, 256)), (256, 256))
            
            # Get input name
            input_name = self.landmark_session.get_inputs()[0].name
            
            # Run landmark detection
            outputs = self.landmark_session.run(None, {input_name: landmark_input})
            
            # Extract outputs: scores (1,), landmarks (1, 31, 4)
            scores = outputs[0]      # Shape: (1,)
            landmarks = outputs[1]   # Shape: (1, 31, 4) - [x, y, z, visibility]
            
            return scores, landmarks
            
        except Exception as e:
            print(f"❌ Error in landmark detection: {e}")
            return None
    
    def findPose(self, img: np.ndarray, draw: bool = True) -> np.ndarray:
        """
        Find pose in image using Qualcomm NPU acceleration
        
        Args:
            img: Input BGR image
            draw: Whether to draw pose landmarks and connections
            
        Returns:
            Image with or without drawn pose
        """
        try:
            # Store original image dimensions
            h, w = img.shape[:2]
            
            # Preprocess image to (1, 3, 256, 256) for processing
            processed_img = self._preprocess_image(img, (256, 256))
            
            # Step 1: Detect pose
            detection = self._detect_pose(processed_img)
            
            if detection is None:
                self.results = None
                return img
            
            # Step 2: Detect landmarks
            landmark_result = self._detect_landmarks(processed_img, detection)
            
            if landmark_result is None:
                self.results = None
                return img
            
            scores, landmarks = landmark_result
            
            # Store results for findPosition method
            self.results = {
                'landmarks': landmarks,
                'scores': scores,
                'image_shape': (h, w)
            }
            
            # Draw pose if requested
            if draw and landmarks is not None:
                img = self._draw_pose(img, landmarks, (h, w))
            
            return img
            
        except Exception as e:
            print(f"❌ Error in findPose: {e}")
            self.results = None
            return img
    
    def findPosition(self, img: np.ndarray, draw: bool = False) -> List[List[int]]:
        """
        Get pose landmark positions
        
        Args:
            img: Input image
            draw: Whether to draw circles at landmark positions
            
        Returns:
            List of landmark positions [id, x, y]
        """
        lm_list = []
        
        if self.results is None or 'landmarks' not in self.results:
            return lm_list
        
        landmarks = self.results['landmarks']
        h, w = self.results['image_shape']
        
        try:
            # Process landmarks - Shape is (1, 31, 4) for 31 landmarks with x, y, z, visibility
            if landmarks.ndim == 3:
                landmarks = landmarks[0]  # Remove batch dimension: (31, 4)
            
            for id, landmark in enumerate(landmarks):
                if len(landmark) >= 2:  # Ensure we have x, y coordinates
                    # Landmarks are normalized coordinates [0, 1]
                    x = int(landmark[0] * w)
                    y = int(landmark[1] * h)
                    visibility = landmark[3] if len(landmark) > 3 else 1.0
                    
                    # Only add landmarks that are visible enough
                    if visibility > 0.1:
                        lm_list.append([id, x, y])
                        
                        # Draw circle if requested
                        if draw:
                            cv2.circle(img, (x, y), 7, (255, 0, 0), cv2.FILLED)
            
        except Exception as e:
            print(f"❌ Error in findPosition: {e}")
        
        return lm_list
    
    def _draw_pose(self, img: np.ndarray, landmarks: np.ndarray, img_shape: Tuple[int, int]) -> np.ndarray:
        """
        Draw pose landmarks and connections on image
        
        Args:
            img: Input image
            landmarks: Pose landmarks (1, 31, 4)
            img_shape: Image dimensions (height, width)
            
        Returns:
            Image with drawn pose
        """
        h, w = img_shape
        
        try:
            # Process landmarks similar to findPosition
            if landmarks.ndim == 3:
                landmarks = landmarks[0]  # (31, 4)
            
            # Convert to pixel coordinates
            points = []
            for landmark in landmarks:
                if len(landmark) >= 4:
                    x = int(landmark[0] * w)
                    y = int(landmark[1] * h)
                    visibility = landmark[3]
                    
                    # Only draw visible landmarks
                    if visibility > 0.1:
                        points.append((x, y))
                    else:
                        points.append(None)
                else:
                    points.append(None)
            
            # Simplified pose connections for 31 landmarks (MediaPipe pose subset)
            # Main body connections
            pose_connections_31 = [
                # Head/Face (first few landmarks)
                (0, 1), (1, 2), (2, 3), (3, 4),
                # Main body structure
                (5, 6), (5, 7), (6, 8), (7, 9), (8, 10),
                (5, 11), (6, 12), (11, 12),
                (11, 13), (13, 15), (12, 14), (14, 16),
                (11, 23), (12, 24), (23, 24),
                (23, 25), (25, 27), (24, 26), (26, 28),
                (27, 29), (29, 30), (28, 30)
            ]
            
            # Draw connections
            for connection in pose_connections_31:
                start_idx, end_idx = connection
                if (start_idx < len(points) and end_idx < len(points) and 
                    points[start_idx] is not None and points[end_idx] is not None):
                    cv2.line(img, points[start_idx], points[end_idx], (0, 255, 0), 2)
            
            # Draw landmarks
            for i, point in enumerate(points):
                if point is not None:
                    # Use different colors for different landmark types
                    if i < 5:  # Face landmarks
                        color = (255, 255, 0)  # Yellow
                    elif i < 17:  # Upper body
                        color = (0, 255, 255)  # Cyan
                    else:  # Lower body
                        color = (255, 0, 255)  # Magenta
                    
                    cv2.circle(img, point, 4, color, cv2.FILLED)
            
        except Exception as e:
            print(f"❌ Error drawing pose: {e}")
        
        return img


def main():
    """Main function for testing the Qualcomm Pose Detector"""
    
    print("🎯 Qualcomm NPU Pose Detection")
    print("=" * 50)
    
    # Check if models exist
    detector_path = "models/mediapipe_pose-posedetector.onnx"
    landmark_path = "models/mediapipe_pose-poselandmarkdetector.onnx"
    
    if not os.path.exists(detector_path) or not os.path.exists(landmark_path):
        print("❌ Error: ONNX model files not found!")
        print(f"   Expected: {detector_path}")
        print(f"   Expected: {landmark_path}")
        print("\n💡 Please ensure Qualcomm ONNX models are downloaded to the models/ directory")
        return
    
    # Ask user for input source
    print("Choose input source:")
    print("1. Webcam (default)")
    print("2. Video file")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '2':
        cap = cv2.VideoCapture('Videos/V2.mp4')
        print("📹 Using video file: Videos/V2.mp4")
    else:
        cap = cv2.VideoCapture(0)
        print("📷 Using webcam")
    
    if not cap.isOpened():
        print("❌ Error: Could not open video source!")
        return
    
    # Initialize Qualcomm Pose Detector
    try:
        detector = QualcommPoseDetector(
            detector_model_path=detector_path,
            landmark_model_path=landmark_path,
            enable_npu=True  # Enable NPU acceleration
        )
    except Exception as e:
        print(f"❌ Failed to initialize pose detector: {e}")
        return
    
    pTime = 0
    cTime = 0
    target_fps = 30
    wait_key_delay = int(1000 / target_fps)
    
    print("✅ Starting Qualcomm NPU pose detection...")
    print("Press 'q' to quit")
    print("Press 'n' to toggle NPU/CPU")
    
    while True:
        success, img = cap.read()
        
        if not success:
            print("End of video or failed to read frame")
            break
        
        # Flip image if using webcam for mirror effect
        if choice != '2':
            img = cv2.flip(img, 1)
        
        # Detect pose using Qualcomm NPU
        img = detector.findPose(img)
        lm_list = detector.findPosition(img)
        
        # Calculate FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime
        
        # Add UI elements
        cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img, f'Landmarks: {len(lm_list)}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f'NPU: {"ON" if detector.enable_npu else "OFF"}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(img, 'Press Q to quit, N to toggle NPU', (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Qualcomm NPU Pose Detection", img)
        
        # Handle key inputs
        key = cv2.waitKey(wait_key_delay) & 0xFF
        if key == ord('q') or cv2.getWindowProperty("Qualcomm NPU Pose Detection", cv2.WND_PROP_VISIBLE) < 1:
            break
        elif key == ord('n'):
            # Toggle NPU (would require reinitializing sessions in practice)
            print("🔄 NPU toggle requested (restart required for full effect)")
    
    cap.release()
    cv2.destroyAllWindows()
    print("🏁 Qualcomm NPU pose detection completed!")


if __name__ == '__main__':
    main() 