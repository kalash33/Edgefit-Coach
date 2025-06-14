#!/usr/bin/env python3
"""
Simple script to inspect ONNX models and test basic inference
"""

import numpy as np
import onnxruntime as ort
import cv2

def inspect_model(model_path: str, model_name: str):
    """Inspect ONNX model details"""
    print(f"\n🔍 Inspecting {model_name}: {model_path}")
    
    try:
        # Load with CPU first
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        
        # Get input details
        inputs = session.get_inputs()
        print(f"📥 Inputs ({len(inputs)}):")
        for inp in inputs:
            print(f"   - {inp.name}: {inp.shape} ({inp.type})")
        
        # Get output details
        outputs = session.get_outputs()
        print(f"📤 Outputs ({len(outputs)}):")
        for out in outputs:
            print(f"   - {out.name}: {out.shape} ({out.type})")
        
        return session, inputs, outputs
        
    except Exception as e:
        print(f"❌ Error inspecting {model_name}: {e}")
        return None, None, None

def test_model_inference(session, inputs, outputs, model_name: str):
    """Test basic model inference"""
    print(f"\n🧪 Testing {model_name} inference...")
    
    try:
        # Create dummy input based on model requirements
        input_data = {}
        for inp in inputs:
            shape = inp.shape
            # Handle dynamic shapes
            actual_shape = []
            for dim in shape:
                if isinstance(dim, str) or dim == -1:
                    actual_shape.append(1)  # Use batch size 1 for dynamic dims
                else:
                    actual_shape.append(dim)
            
            # Create random input data
            dummy_data = np.random.rand(*actual_shape).astype(np.float32)
            input_data[inp.name] = dummy_data
            print(f"   Input {inp.name}: {actual_shape}")
        
        # Run inference
        result = session.run(None, input_data)
        
        print(f"✅ Inference successful!")
        for i, (out, res) in enumerate(zip(outputs, result)):
            print(f"   Output {out.name}: {res.shape} (min: {res.min():.4f}, max: {res.max():.4f})")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Error during inference: {e}")
        return False, None

def test_with_real_image(session, inputs, outputs, model_name: str):
    """Test with a real image"""
    print(f"\n📸 Testing {model_name} with real image...")
    
    try:
        # Create a test image
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(test_img, "Test Image", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Get expected input shape
        inp = inputs[0]
        expected_shape = inp.shape
        
        if len(expected_shape) == 4:  # NCHW or NHWC format
            if expected_shape[1] == 3:  # NCHW
                h, w = expected_shape[2], expected_shape[3]
                target_format = "NCHW"
            else:  # NHWC
                h, w = expected_shape[1], expected_shape[2]
                target_format = "NHWC"
        else:
            print(f"⚠️  Unexpected input shape: {expected_shape}")
            return False, None
        
        print(f"   Expected input: {expected_shape} ({target_format})")
        
        # Preprocess image
        rgb_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
        resized_img = cv2.resize(rgb_img, (w, h))
        normalized_img = resized_img.astype(np.float32) / 255.0
        
        if target_format == "NCHW":
            # Convert HWC to CHW and add batch dimension
            input_tensor = np.transpose(normalized_img, (2, 0, 1))
            input_tensor = np.expand_dims(input_tensor, 0)
        else:  # NHWC
            # Add batch dimension
            input_tensor = np.expand_dims(normalized_img, 0)
        
        print(f"   Processed input shape: {input_tensor.shape}")
        
        # Run inference
        input_data = {inp.name: input_tensor}
        result = session.run(None, input_data)
        
        print(f"✅ Real image inference successful!")
        for i, (out, res) in enumerate(zip(outputs, result)):
            print(f"   Output {out.name}: {res.shape}")
            if res.size < 100:  # Print small outputs
                print(f"     Values: {res.flatten()[:10]}...")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Error with real image: {e}")
        return False, None

def main():
    """Main test function"""
    print("🔬 ONNX Model Inspector and Tester")
    print("=" * 50)
    
    # Test both models
    models = [
        ("models/mediapipe_pose-posedetector.onnx", "Pose Detector"),
        ("models/mediapipe_pose-poselandmarkdetector.onnx", "Pose Landmark Detector")
    ]
    
    for model_path, model_name in models:
        # Inspect model
        session, inputs, outputs = inspect_model(model_path, model_name)
        
        if session is not None:
            # Test basic inference
            success, _ = test_model_inference(session, inputs, outputs, model_name)
            
            if success:
                # Test with real image
                test_with_real_image(session, inputs, outputs, model_name)
        
        print("-" * 50)
    
    # Test QNN provider availability
    print(f"\n🎯 Available ONNX Runtime Providers:")
    providers = ort.get_available_providers()
    for provider in providers:
        print(f"   - {provider}")
    
    if 'QNNExecutionProvider' in providers:
        print("✅ QNN Execution Provider is available!")
    else:
        print("❌ QNN Execution Provider not found")

if __name__ == "__main__":
    main() 