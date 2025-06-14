# Pose Detection with OpenCV and MediaPipe

## Overview

This repository contains multiple implementations for real-time pose detection:

1. **Standard MediaPipe Implementation** (`main.py`, `main_webcam.py`) - Uses Google's MediaPipe library
2. **Qualcomm NPU Optimized Implementation** (`main_qualcomm_npu.py`) - Uses Qualcomm's optimized ONNX models with NPU acceleration

## Requirements

### Standard MediaPipe Implementation
- Python 3.x
- OpenCV
- MediaPipe

Install the required libraries using:

```bash
pip install opencv-python
pip install mediapipe
```

### Qualcomm NPU Implementation
- Python 3.8+
- OpenCV
- ONNX Runtime with QNN Execution Provider
- Qualcomm Snapdragon X Elite device (for NPU acceleration)

Install using:

```bash
pip install -r requirements_qualcomm.txt
```

Or manually:

```bash
pip install opencv-python>=4.8.0
pip install onnxruntime-qnn>=1.18.0
pip install numpy>=1.24.0
```

## Usage

1. Clone the repository or download the script.

```bash
git clone https://github.com/devDurgeshK/poseEstimationModule.git
cd poseEstimationModule
```

### Standard MediaPipe Implementation

2. Run the script:

```bash
python main.py
```

3. Press 'q' to exit the program.

### Qualcomm NPU Implementation

2. Set up the Qualcomm NPU environment:

```bash
python setup_qualcomm_npu.py
```

3. Ensure ONNX models are in the `models/` directory:
   - `mediapipe_pose-posedetector.onnx`
   - `mediapipe_pose-poselandmarkdetector.onnx`

4. Run the Qualcomm NPU optimized version:

```bash
python main_qualcomm_npu.py
```

5. Press 'q' to exit, 'n' to toggle NPU/CPU mode.

## Configuration

The `PoseDetector` class can be configured by adjusting the initialization parameters in the script:

- `staticImageMode`: Set to `True` for static image mode.
- `modelComplexity`: Model complexity parameter (default: 1).
- `smoothLandmarks`: Enable smoothing of landmark points.
- `enableSegmentation`: Enable segmentation (not used in this script).
- `smoothSegmentation`: Enable smoothing of segmentation masks.
- `minDetectionConfidence`: Minimum confidence threshold for detection (default: 0.5).
- `minTrackingConfidence`: Minimum confidence threshold for tracking (default: 0.5).

### Functionality:

1. **Initialization:**
    
    - The class is initialized with various configuration parameters related to pose detection.
2. **MediaPipe Setup:**
    
    - It initializes instances of the `drawing_utils` and `pose` modules from the `mediapipe` library.
3. **`findPose` Method:**
    
    - This method takes an image (`img`) as input and detects the pose using the MediaPipe Pose model.
    - If the `draw` parameter is True, it draws landmarks on the image.
    - Returns the modified image.
4. **`findPosition` Method:**
    
    - This method takes an image (`img`) as input and extracts the positions of pose landmarks.
    - If the `draw` parameter is True, it draws circles around the landmarks on the image.
    - Returns a list (`lmList`) containing landmark positions [id, x, y].

### Note:

- The `PoseDetector` class encapsulates the functionality related to pose detection using the MediaPipe library.
- It provides methods for detecting poses in images and extracting pose landmark positions.
- The class is designed to be reusable and configurable with various parameters.

## Qualcomm NPU Implementation Details

The Qualcomm NPU implementation (`main_qualcomm_npu.py`) offers several advantages:

### Performance Benefits
- **NPU Acceleration**: Leverages Qualcomm's Hexagon NPU for efficient pose detection
- **Optimized Models**: Uses Qualcomm's optimized MediaPipe ONNX models
- **Lower Power Consumption**: NPU inference is more power-efficient than CPU/GPU
- **Better FPS**: Can achieve higher frame rates on Qualcomm devices

### Key Features
- **QNN Execution Provider**: Uses ONNX Runtime with Qualcomm Neural Network (QNN) backend
- **HTP Backend**: Utilizes Hexagon Tensor Processor for acceleration
- **Fallback Support**: Automatically falls back to CPU if NPU is unavailable
- **Compatible API**: Maintains similar interface to original MediaPipe implementation

### Configuration Options
The `QualcommPoseDetector` class supports various configuration options:

```python
detector = QualcommPoseDetector(
    detector_model_path="models/mediapipe_pose-posedetector.onnx",
    landmark_model_path="models/mediapipe_pose-poselandmarkdetector.onnx",
    min_detection_confidence=0.5,
    enable_npu=True  # Enable NPU acceleration
)
```

### Model Requirements
- **Pose Detector Model**: `mediapipe_pose-posedetector.onnx` (3.2MB)
- **Landmark Detector Model**: `mediapipe_pose-poselandmarkdetector.onnx` (13MB)

Download these models from [Qualcomm AI Hub](https://aihub.qualcomm.com/models/mediapipe_pose) and place them in the `models/` directory.

### System Requirements
- **OS**: Windows 11 ARM64 or Linux ARM64
- **Hardware**: Qualcomm Snapdragon X Elite or compatible NPU-enabled device
- **Python**: 3.8 or higher
- **ONNX Runtime**: 1.18.0 or higher with QNN support

## Contributing

Feel free to contribute to the project by submitting issues or pull requests. Your feedback and enhancements are welcomed!

### Qualcomm NPU Development
If you're interested in improving the Qualcomm NPU implementation:
1. Check the [Qualcomm QNN documentation](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html)
2. Review the [AI Hub models repository](https://github.com/quic/ai-hub-models)
3. Test on actual Qualcomm hardware for optimal results

Below is the functionality of the `findPose` and `findPosition` methods in the `PoseDetector` class:

### `findPose` Method:

```python
def findPose(self, img, draw=True):
    """
    Detects the pose in the given image and optionally draws the pose landmarks.

    Parameters:
    - img: The input image.
    - draw: If True, draw the pose landmarks on the image.

    Returns:
    - img: The image with or without drawn landmarks.
    """
    # Convert image to RGB format
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Process image with MediaPipe Pose model
    self.results = self.pose.process(imgRGB)
    
    # Draw landmarks on the image if detected
    if self.results.pose_landmarks and draw:
        self.mpDraw.draw_landmarks(img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS)

    return img
```

#### Functionality:

1. **Image Conversion:**
   - Converts the input image (`img`) from BGR format to RGB format, as required by the MediaPipe Pose model.

2. **Pose Detection:**
   - Processes the RGB image using the MediaPipe Pose model (`self.pose.process()`).
   - The results are stored in the `self.results` attribute.

3. **Drawing Landmarks:**
   - If the pose landmarks are detected (`self.results.pose_landmarks`) and the `draw` parameter is True, it draws the landmarks on the image using the `draw_landmarks` method from `mediapipe`.

4. **Return:**
   - Returns the modified image (`img`) with or without drawn landmarks.

### `findPosition` Method:

```python
def findPosition(self, img, draw=False):
    """
    Finds the positions of pose landmarks in the given image and optionally draws circles around them.

    Parameters:
    - img: The input image.
    - draw: If True, draw circles around the pose landmarks.

    Returns:
    - lmList: A list containing landmark positions [id, x, y].
    """
    lmList = []
    for id, lm in enumerate(self.results.pose_landmarks.landmark):
        # Get image dimensions
        h, w, c = img.shape
        # Convert normalized landmark coordinates to pixel values
        cx, cy = int(lm.x * w), int(lm.y * h)

        # Append landmark information to the list
        lmList.append([id, cx, cy])

        # Draw a circle around the landmark if required
        if draw:
            cv2.circle(img, (cx, cy), 7, (255, 0, 0), cv2.FILLED)

    return lmList
```

#### Functionality:

1. **Landmark Iteration:**
   - Iterates through the pose landmarks obtained from the MediaPipe results (`self.results.pose_landmarks`).

2. **Coordinate Conversion:**
   - Converts the normalized landmark coordinates to pixel values using the dimensions of the input image.

3. **Landmark List:**
   - Appends the landmark information to the `lmList` list in the format [id, x, y].

4. **Drawing Circles:**
   - If the `draw` parameter is True, it draws circles around the landmarks on the input image.

5. **Return:**
   - Returns the `lmList` containing landmark positions.

### Note:
- `findPose` is responsible for detecting the overall pose in the image and drawing landmarks if required.
- `findPosition` extracts and returns the positions of individual pose landmarks, and optionally draws circles around them on the image.
- Both methods utilize the results obtained from the MediaPipe Pose model during the pose detection process.
## Example Usage

```python
from PoseDetector import PoseDetector
import cv2

# Create PoseDetector instance
detector = PoseDetector()

# Open video capture
cap = cv2.VideoCapture('path/to/your/video.mp4')

while True:
    success, img = cap.read()

    # Detect and draw pose
    img = detector.findPose(img)
    
    # Find and print pose landmarks
    lmList = detector.findPosition(img)
    if len(lmList) != 0:
        print(lmList)

    # Display frame with FPS
    cv2.imshow("Pose Detection", img)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close all windows
cap.release()
cv2.destroyAllWindows()
