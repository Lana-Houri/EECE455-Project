#!/bin/bash
#
# Setup Script for Deep Learning Steganalysis
# ============================================
# This script sets up the deep learning components for JPEG steganalysis
#
# Usage: chmod +x setup_deep_learning.sh && ./setup_deep_learning.sh

set -e

echo "========================================"
echo "Deep Learning Steganalysis Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${YELLOW}Step 1: Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Found $PYTHON_VERSION${NC}"
echo ""

# Install core dependencies
echo -e "${YELLOW}Step 2: Installing core dependencies...${NC}"
pip3 install numpy pillow scipy
echo -e "${GREEN}✓ Core dependencies installed${NC}"
echo ""

# Install stegano
echo -e "${YELLOW}Step 3: Installing Stegano library...${NC}"
pip3 install stegano
echo -e "${GREEN}✓ Stegano installed${NC}"
echo ""

# Install PyTorch
echo -e "${YELLOW}Step 4: Installing PyTorch...${NC}"
echo "Choose PyTorch version:"
echo "  1) CPU only (works everywhere)"
echo "  2) CUDA 11.8 (NVIDIA GPU)"
echo "  3) CUDA 12.1 (newer NVIDIA GPU)"
echo "  4) Skip (already installed)"
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo "Installing PyTorch (CPU)..."
        pip3 install torch torchvision 
        ;;
    2)
        echo "Installing PyTorch (CUDA 11.8)..."
        pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118 
        ;;
    3)
        echo "Installing PyTorch (CUDA 12.1)..."
        pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121 
        ;;
    4)
        echo "Skipping PyTorch installation..."
        ;;
    *)
        echo -e "${YELLOW}Invalid choice, installing CPU version...${NC}"
        pip3 install torch torchvision 
        ;;
esac

# Verify PyTorch
python3 -c "import torch; print(f'${GREEN}✓ PyTorch {torch.__version__} installed${NC}')" 2>/dev/null || echo -e "${YELLOW}⚠ PyTorch not installed - will use statistical fallback${NC}"
python3 -c "import torch; print(f'  CUDA available: {torch.cuda.is_available()}')" 2>/dev/null || true
echo ""

# Install jpegio (optional)
echo -e "${YELLOW}Step 5: Installing JPEG DCT analysis tools...${NC}"
pip3 install jpegio  2>/dev/null && echo -e "${GREEN}✓ jpegio installed${NC}" || echo -e "${YELLOW}⚠ jpegio not available - using fallback DCT analysis${NC}"
echo ""

# Create model directory
echo -e "${YELLOW}Step 6: Setting up model directory...${NC}"
mkdir -p ~/steg_models
echo -e "${GREEN}✓ Created ~/steg_models/${NC}"

# Copy model file
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/srnet_model.py" ]; then
    cp "$SCRIPT_DIR/srnet_model.py" ~/steg_models/
    echo -e "${GREEN}✓ Copied srnet_model.py to ~/steg_models/${NC}"
else
    echo -e "${YELLOW}⚠ srnet_model.py not found - copy manually${NC}"
fi
echo ""

# Check for pre-trained weights
echo -e "${YELLOW}Step 7: Checking for pre-trained weights...${NC}"
if [ -f ~/steg_models/srnet.pth ]; then
    size=$(du -h ~/steg_models/srnet.pth | cut -f1)
    echo -e "${GREEN}✓ Found model weights ($size)${NC}"
else
    echo -e "${YELLOW}⚠ No pre-trained weights found${NC}"
    echo ""
    echo "The deep learning detector needs pre-trained weights."
    echo "Without weights, the system will use statistical methods instead."
    echo ""
    echo "To get pre-trained weights:"
    echo "  Option 1: Download from a steganalysis repository"
    echo "  Option 2: Train your own model (see DEEP_LEARNING_SETUP.md)"
    echo ""
    echo "Place the weights file at: ~/steg_models/srnet.pth"
fi
echo ""

# Final verification
echo -e "${YELLOW}Step 8: Running verification...${NC}"
echo ""

python3 << 'EOF'
import sys

print("Checking installed packages:")
print("-" * 40)

packages = [
    ("numpy", "numpy"),
    ("PIL", "pillow"),
    ("scipy", "scipy"),
    ("stegano", "stegano"),
    ("torch", "pytorch"),
    ("torchvision", "torchvision"),
    ("jpegio", "jpegio"),
]

all_good = True
for module, name in packages:
    try:
        __import__(module)
        print(f"✓ {name}")
    except ImportError:
        if name in ["jpegio"]:
            print(f"⚠ {name} (optional)")
        elif name in ["pytorch", "torchvision"]:
            print(f"⚠ {name} (will use statistical fallback)")
            all_good = False
        else:
            print(f"✗ {name} (required)")
            all_good = False

print("-" * 40)

import os
models_dir = os.path.expanduser("~/steg_models")
model_file = os.path.join(models_dir, "srnet_model.py")
weights_file = os.path.join(models_dir, "srnet.pth")

print("\nChecking model files:")
print("-" * 40)
print(f"{'✓' if os.path.exists(models_dir) else '✗'} Model directory: {models_dir}")
print(f"{'✓' if os.path.exists(model_file) else '✗'} SRNet model class: srnet_model.py")
print(f"{'✓' if os.path.exists(weights_file) else '⚠'} Pre-trained weights: srnet.pth {'(found)' if os.path.exists(weights_file) else '(not found - using statistical)'}")

print("-" * 40)

if all_good:
    print("\n✅ Setup complete! Deep learning steganalysis is ready.")
else:
    print("\n⚠ Setup complete with warnings. Statistical analysis will be used as fallback.")
EOF

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Copy statistical_tools.py to your project"
echo "2. Update imports in app.py"
echo "3. Run: streamlit run app.py"
echo ""
echo "For full deep learning support:"
echo "- Add pre-trained weights to ~/steg_models/srnet.pth"
echo ""