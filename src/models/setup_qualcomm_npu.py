#!/usr/bin/env python3
"""
Setup script for Qualcomm NPU Pose Detection
Helps configure the environment and check system compatibility.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_platform():
    """Check if platform is supported"""
    print("🖥️  Checking platform...")
    system = platform.system()
    machine = platform.machine()
    
    print(f"   System: {system}")
    print(f"   Architecture: {machine}")
    
    if system == "Windows" and machine.lower() in ["arm64", "aarch64"]:
        print("✅ Windows ARM64 detected - Qualcomm NPU supported")
        return True, "windows_arm64"
    elif system == "Windows" and machine.lower() in ["x86_64", "amd64"]:
        print("⚠️  Windows x64 detected - Can be used for model quantization only")
        return True, "windows_x64"
    elif system == "Linux" and machine.lower() in ["arm64", "aarch64"]:
        print("✅ Linux ARM64 detected - Qualcomm NPU supported")
        return True, "linux_arm64"
    else:
        print(f"❌ Platform {system}/{machine} may not support Qualcomm NPU")
        return False, "unsupported"

def check_onnxruntime_qnn():
    """Check if ONNX Runtime QNN is installed"""
    print("📦 Checking ONNX Runtime QNN installation...")
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        
        print(f"   Available providers: {providers}")
        
        if 'QNNExecutionProvider' in providers:
            print("✅ QNN Execution Provider is available")
            return True
        else:
            print("❌ QNN Execution Provider not found")
            print("   Please install: pip install onnxruntime-qnn")
            return False
            
    except ImportError:
        print("❌ ONNX Runtime not installed")
        print("   Please install: pip install onnxruntime-qnn")
        return False

def check_models():
    """Check if ONNX models are available"""
    print("🤖 Checking ONNX models...")
    
    models_dir = Path("models")
    detector_path = models_dir / "mediapipe_pose-posedetector.onnx"
    landmark_path = models_dir / "mediapipe_pose-poselandmarkdetector.onnx"
    
    if not models_dir.exists():
        print("❌ Models directory not found")
        return False
    
    missing_models = []
    if not detector_path.exists():
        missing_models.append(str(detector_path))
    else:
        print(f"✅ Found: {detector_path}")
    
    if not landmark_path.exists():
        missing_models.append(str(landmark_path))
    else:
        print(f"✅ Found: {landmark_path}")
    
    if missing_models:
        print(f"❌ Missing models: {missing_models}")
        print("   Please download from Qualcomm AI Hub")
        return False
    
    return True

def install_requirements():
    """Install required packages"""
    print("📥 Installing requirements...")
    
    requirements_file = "requirements_qualcomm.txt"
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("🧪 Testing basic functionality...")
    
    try:
        import cv2
        import numpy as np
        import onnxruntime as ort
        
        print("✅ Basic imports successful")
        
        # Test OpenCV
        print("   Testing OpenCV...")
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.putText(test_img, "Test", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        print("   ✅ OpenCV working")
        
        # Test ONNX Runtime
        print("   Testing ONNX Runtime...")
        providers = ort.get_available_providers()
        print(f"   Available providers: {providers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def create_test_script():
    """Create a simple test script"""
    print("📝 Creating test script...")
    
    test_script = """#!/usr/bin/env python3
'''
Simple test script for Qualcomm NPU Pose Detection
'''

import cv2
import numpy as np
try:
    from main_qualcomm_npu import QualcommPoseDetector
except ImportError:
    print("❌ Could not import QualcommPoseDetector")
    print("   Make sure main_qualcomm_npu.py is available")
    exit(1)

def test_detector():
    try:
        detector = QualcommPoseDetector(enable_npu=True)
        print("✅ Detector initialized successfully")
        
        # Create test image
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test pose detection
        result = detector.findPose(test_img, draw=False)
        landmarks = detector.findPosition(test_img)
        
        print(f"✅ Pose detection test completed")
        print(f"   Result shape: {result.shape}")
        print(f"   Landmarks found: {len(landmarks)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🧪 Running Qualcomm NPU Pose Detection Test")
    test_detector()
"""
    
    with open("test_qualcomm_npu.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("✅ Test script created: test_qualcomm_npu.py")

def main():
    """Main setup function"""
    print("🚀 Qualcomm NPU Pose Detection Setup")
    print("=" * 50)
    
    # Check system compatibility
    if not check_python_version():
        return False
    
    supported, platform_type = check_platform()
    if not supported:
        print("⚠️  Your platform may not support Qualcomm NPU acceleration")
        print("   You can still use CPU inference")
    
    # Install requirements
    install_choice = input("\n📥 Install requirements? (y/n): ").lower().strip()
    if install_choice in ['y', 'yes']:
        if not install_requirements():
            return False
    
    # Check installations
    print("\n🔍 Checking installations...")
    ort_ok = check_onnxruntime_qnn()
    models_ok = check_models()
    
    if not ort_ok:
        print("\n💡 To install ONNX Runtime QNN:")
        if platform_type in ["windows_arm64", "linux_arm64"]:
            print("   pip install onnxruntime-qnn")
        else:
            print("   pip install onnxruntime-qnn  # For model quantization")
    
    if not models_ok:
        print("\n💡 To get the ONNX models:")
        print("   1. Visit: https://aihub.qualcomm.com/models/mediapipe_pose")
        print("   2. Download the ONNX models")
        print("   3. Place them in the models/ directory")
    
    # Test functionality
    if ort_ok:
        test_basic_functionality()
    
    # Create test script
    create_test_script()
    
    print("\n🎯 Setup completed!")
    print("\nNext steps:")
    print("1. Ensure ONNX models are in models/ directory")
    print("2. Run: python main_qualcomm_npu.py")
    print("3. Or test with: python test_qualcomm_npu.py")
    
    return True

if __name__ == "__main__":
    main() 