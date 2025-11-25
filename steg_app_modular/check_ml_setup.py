#!/usr/bin/env python3
"""
Quick diagnostic script to check if Machine Learning is properly configured
for the steganalysis application.
"""

import sys
import os

print("=" * 60)
print("Machine Learning Setup Diagnostic")
print("=" * 60)
print()

# Check 1: PyTorch installation
print("1. Checking PyTorch installation...")
try:
    import torch
    print(f"   ✅ PyTorch {torch.__version__} is installed")
    print(f"   ✅ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   ✅ CUDA device: {torch.cuda.get_device_name(0)}")
    pytorch_installed = True
except ImportError:
    print("   ❌ PyTorch is NOT installed")
    print("   → Install with: pip install torch torchvision")
    pytorch_installed = False
print()

# Check 2: Model file existence
print("2. Checking for pre-trained model...")
model_path = os.path.expanduser("~/steg_models/srnet.pth")
model_dir = os.path.expanduser("~/steg_models")

if os.path.exists(model_dir):
    print(f"   ✅ Model directory exists: {model_dir}")
else:
    print(f"   ⚠️  Model directory does not exist: {model_dir}")

if os.path.exists(model_path):
    size = os.path.getsize(model_path) / (1024 * 1024)  # MB
    print(f"   ✅ Model file found: {model_path}")
    print(f"   ✅ Model size: {size:.2f} MB")
    model_exists = True
else:
    print(f"   ❌ Model file NOT found: {model_path}")
    print("   → You need to download/place srnet.pth at this location")
    model_exists = False
print()

# Check 3: Test actual ML function
print("3. Testing run_deep_steganalysis() function...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from statistical_tools import run_deep_steganalysis
    from PIL import Image
    import tempfile
    
    # Create a test image
    test_img = Image.new('RGB', (256, 256), color='blue')
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        test_img.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        result = run_deep_steganalysis(tmp_path)
        
        print(f"   Method used: {result.get('method_type', 'Unknown')}")
        print(f"   Success: {result.get('success', False)}")
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            if 'Deep Learning' in result.get('method_type', ''):
                print(f"   ✅ REAL MACHINE LEARNING is being used!")
            else:
                print(f"   ⚠️  Falling back to statistical methods (not ML)")
        
        print(f"   Confidence: {result.get('confidence', 0):.1f}%")
    finally:
        os.unlink(tmp_path)
        
except Exception as e:
    print(f"   ❌ Error testing function: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Summary")
print("=" * 60)

if pytorch_installed and model_exists:
    print("✅ Machine Learning setup is COMPLETE")
    print("   The app will use real ML (SRNet CNN) for JPEG steganalysis")
elif pytorch_installed and not model_exists:
    print("⚠️  PyTorch is installed but model file is missing")
    print("   The app will fall back to statistical methods")
    print("   To enable ML: Download srnet.pth to ~/steg_models/")
elif not pytorch_installed and model_exists:
    print("⚠️  Model file exists but PyTorch is not installed")
    print("   The app will fall back to statistical methods")
    print("   To enable ML: Install PyTorch with: pip install torch torchvision")
else:
    print("❌ Machine Learning is NOT configured")
    print("   The app will use traditional statistical methods only")
    print("   To enable ML:")
    print("   1. Install PyTorch: pip install torch torchvision")
    print("   2. Download model: Place srnet.pth at ~/steg_models/")

print()

