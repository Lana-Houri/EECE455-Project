# Deep Learning Steganalysis Setup Guide

## Overview

This guide explains how to install and use CNN-based steganalysis models for detecting JPEG steganography (J-UNIWARD, nsF5, UERD, etc.).

## 📊 Recommended Models for JPEG Detection

### 1. **SRNet** (Spatial Rich Model Network) - ⭐ RECOMMENDED
- **Best for:** JPEG steganography (J-UNIWARD, nsF5, UERD)
- **Accuracy:** State-of-the-art (>98% for 0.4 bpp)
- **Speed:** ~100ms per image on GPU
- **Paper:** "Deep Residual Network for Steganalysis of Digital Images" (2019)
- **Repository:** https://github.com/brijeshiitg/Pytorch-implementation-of-SRNet

### 2. **XuNet** - Good General Purpose
- **Best for:** General steganalysis (works on both spatial and JPEG)
- **Accuracy:** ~95% on BOSSbase
- **Speed:** Fast (~50ms per image)
- **Paper:** "Structural Design of Convolutional Neural Networks for Steganalysis" (2016)
- **Repository:** https://github.com/qunwang6/SteganalysisWithCNN

### 3. **Yedroudj-Net** - Spatial Domain Specialist
- **Best for:** Spatial domain steganography (WOW, S-UNIWARD)
- **Accuracy:** ~97% on BOSSbase
- **Paper:** "Yedroudj-Net: An Efficient CNN for Spatial Steganalysis" (2018)
- **Repository:** https://github.com/yedmed/yedroudj-net

### 4. **ZhuNet** - JPEG Specialist
- **Best for:** JPEG steganography
- **Accuracy:** Excellent for JPEG domain
- **Paper:** "A New CNN-Based Network for Image Steganalysis" (2018)

## 🚀 Quick Start - SRNet Installation

### Step 1: Install PyTorch

```bash
# For CPU only
pip install torch torchvision --break-system-packages

# For GPU (CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 --break-system-packages

# For GPU (CUDA 12.1)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --break-system-packages
```

### Step 2: Clone SRNet Repository

```bash
cd ~
git clone https://github.com/brijeshiitg/Pytorch-implementation-of-SRNet.git
cd Pytorch-implementation-of-SRNet
```

### Step 3: Create Model Directory

```bash
mkdir -p ~/steg_models
```

### Step 4: Download Pre-trained Weights

**Option A: Use Pre-trained Models (if available)**
```bash
# Check the repository for pre-trained weights
# Usually in models/ or weights/ directory
```

**Option B: Train Your Own Model**

You'll need a dataset of clean and stego images:

1. **Download BOSSbase dataset** (10,000 grayscale images)
   ```bash
   wget http://agents.fel.cvut.cz/boss/data/BOSSbase_1.01.zip
   unzip BOSSbase_1.01.zip -d ~/datasets/BOSSbase
   ```

2. **Generate stego images using J-UNIWARD**
   ```bash
   # You'll need MATLAB or Octave with J-UNIWARD implementation
   # https://github.com/daniellerch/stego-retweets/tree/master/J-UNIWARD
   ```

3. **Train the model**
   ```bash
   python train.py --dataset ~/datasets --epochs 100 --batch-size 32
   ```

### Step 5: Copy Trained Model

```bash
# Copy the trained model to ~/steg_models/
cp ~/Pytorch-implementation-of-SRNet/models/srnet_best.pth ~/steg_models/srnet.pth
```

## 📦 Alternative: Alaska2 Pre-trained Models

The Alaska2 Steganalysis Challenge provides excellent pre-trained models:

```bash
# Clone Alaska2 repo
git clone https://github.com/YassineYousfi/alaska2-challenge.git
cd alaska2-challenge

# Download pre-trained weights
# These models are trained on Alaska2 dataset with modern steganography methods
wget https://github.com/YassineYousfi/alaska2-challenge/releases/download/v1.0/efficientnet-b0.pth -O ~/steg_models/efficientnet_steg.pth
```

## 🔧 Integrate with Your Application

### Create SRNet Model Class

Create `~/steg_models/srnet_model.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SRNet(nn.Module):
    def __init__(self):
        super(SRNet, self).__init__()
        
        # Layer 1: Preprocessing
        self.conv1 = nn.Conv2d(1, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        
        # Layer 2-12: Residual blocks
        self.res_blocks = nn.ModuleList([
            self._make_residual_block(64) for _ in range(11)
        ])
        
        # Global average pooling
        self.gap = nn.AdaptiveAvgPool2d(1)
        
        # Fully connected layers
        self.fc1 = nn.Linear(64, 16)
        self.fc2 = nn.Linear(16, 2)  # Binary classification: cover or stego
        
    def _make_residual_block(self, channels):
        return nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(channels)
        )
    
    def forward(self, x):
        # Initial convolution
        x = F.relu(self.bn1(self.conv1(x)))
        
        # Residual blocks
        for block in self.res_blocks:
            identity = x
            x = block(x)
            x = F.relu(x + identity)
        
        # Global average pooling
        x = self.gap(x)
        x = x.view(x.size(0), -1)
        
        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        
        return F.softmax(x, dim=1)

def load_srnet(model_path):
    """Load trained SRNet model."""
    model = SRNet()
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    return model
```

### Update statistical_tools.py

Replace the `run_deep_steganalysis()` function placeholder with:

```python
def run_deep_steganalysis(image_path: str):
    """Deep learning-based steganalysis using SRNet."""
    try:
        import torch
        import torchvision.transforms as transforms
        from PIL import Image
        import sys
        sys.path.append(os.path.expanduser("~/steg_models"))
        from srnet_model import load_srnet
        
        # Load model
        model_path = os.path.expanduser("~/steg_models/srnet.pth")
        if not os.path.exists(model_path):
            return {
                "success": False,
                "error": "SRNet model not found at ~/steg_models/srnet.pth",
                "confidence": 0
            }
        
        model = load_srnet(model_path)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        
        # Preprocess image
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])
        ])
        img_tensor = transform(img).unsqueeze(0).to(device)
        
        # Run inference
        with torch.no_grad():
            output = model(img_tensor)
            probs = output.cpu().numpy()[0]
            
            # probs[0] = probability of cover (clean)
            # probs[1] = probability of stego (contains hidden data)
            stego_prob = probs[1] * 100
            
        # Interpret results
        confidence = stego_prob
        if confidence >= 70:
            interpretation = f"JPEG steganography detected (CNN confidence: {confidence:.1f}%)"
        elif confidence >= 40:
            interpretation = f"Possible JPEG steganography (CNN confidence: {confidence:.1f}%)"
        else:
            interpretation = f"Clean image (CNN confidence: {100-confidence:.1f}%)"
        
        return {
            "success": True,
            "confidence": confidence,
            "interpretation": interpretation,
            "raw_output": f"Cover probability: {probs[0]:.4f}, Stego probability: {probs[1]:.4f}",
            "method_type": "Deep Learning (SRNet)"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Import error: {str(e)}. Install PyTorch: pip install torch torchvision",
            "confidence": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Deep learning error: {str(e)}",
            "confidence": 0
        }
```

## 🎯 Testing the Installation

Create a test script `~/test_srnet.py`:

```python
import torch
from statistical_tools import run_deep_steganalysis

# Test with a sample image
result = run_deep_steganalysis("path/to/test_image.jpg")

if result["success"]:
    print(f"✅ Success!")
    print(f"Confidence: {result['confidence']:.2f}%")
    print(f"Interpretation: {result['interpretation']}")
else:
    print(f"❌ Failed: {result['error']}")
```

Run it:
```bash
python3 ~/test_srnet.py
```

## 📚 Additional Resources

### Research Papers
- **SRNet:** https://arxiv.org/abs/1904.07841
- **XuNet:** https://ieeexplore.ieee.org/document/7937836
- **Yedroudj-Net:** https://arxiv.org/abs/1803.00407
- **Alaska2:** https://arxiv.org/abs/2012.06527

### Datasets for Training
- **BOSSbase 1.01:** http://agents.fel.cvut.cz/boss/BOSSbase/
- **Alaska2:** https://alaska.utt.fr/
- **BOWS2:** http://bows2.ec-lille.fr/

### Steganography Tools (for generating test data)
- **J-UNIWARD:** https://github.com/daniellerch/stego-retweets/tree/master/J-UNIWARD
- **nsF5:** https://github.com/daniellerch/stego-retweets/tree/master/nsF5
- **UERD:** https://github.com/daniellerch/stego-retweets/tree/master/UERD

## 🔍 Comparison: StegExpose vs Deep Learning

| Feature | StegExpose | SRNet (Deep Learning) |
|---------|------------|----------------------|
| **Target** | LSB steganography (PNG) | Adaptive steganography (JPEG) |
| **Methods detected** | LSB, LSB Matching | J-UNIWARD, nsF5, UERD, etc. |
| **Accuracy** | Good for LSB (~90%) | Excellent for JPEG (~98%) |
| **Speed** | Fast (~1s) | Very fast (~0.1s on GPU) |
| **Installation** | Easy (Java JAR) | Complex (PyTorch + models) |
| **False positives** | Low | Very low |
| **Training required** | No (pre-built) | Yes (unless using pre-trained) |

## 💡 Recommendations

1. **For PNG images:** Use StegExpose (already working in your app)
2. **For JPEG images:** Use SRNet or Alaska2 models
3. **For both:** Use the combined approach with 50/50 weighting (already configured)

## 🐛 Troubleshooting

### CUDA Out of Memory
```python
# In srnet_model.py, add:
torch.cuda.empty_cache()

# Or process on CPU:
device = torch.device('cpu')
```

### Model Not Loading
```bash
# Check model file
ls -lh ~/steg_models/srnet.pth

# Verify PyTorch installation
python3 -c "import torch; print(torch.__version__)"
```

### Slow Inference
```bash
# Install with GPU support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify GPU is available
python3 -c "import torch; print(torch.cuda.is_available())"
```

---

**Next Steps:**
1. Install PyTorch
2. Clone SRNet repository
3. Download/train model weights
4. Test with sample images
5. Integrate with your Streamlit app

For questions or issues, refer to the GitHub repositories or research papers linked above.
