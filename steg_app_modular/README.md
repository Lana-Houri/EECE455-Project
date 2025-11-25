# Updated Modular Steganalysis App - Quick Start

## ✅ What Changed

**Inspect Mode now only uses:**
1. **StegExpose** - Statistical fusion for LSB detection (PNG)
2. **Deep Learning** - CNN-based detection for JPEG steganography

**Removed from Inspect Mode:**
- ❌ Chi-Square Analysis
- ❌ RS Analysis  
- ❌ Sample Pair Analysis

These methods were removed as StegExpose already combines them (fusion technique) and they don't work well for modern adaptive steganography.

## 📦 Files in This Package

```
updated_modular/
├── __init__.py                    # Package initialization
├── app.py                         # Main Streamlit application
├── decode_tools.py                # Extraction tools (zsteg, steghide, etc.)
├── encode_tools.py                # Encoding tools (openstego, steghide)
├── external_tools.py              # ExifTool, Binwalk, trailer checks
├── parsers.py                     # Output parsers and classifiers
├── statistical_tools.py           # ✨ UPDATED - Only StegExpose + Deep Learning
├── suspicion.py                   # Statistical anomaly detection
├── srnet_model.py                 # SRNet CNN model implementation
└── DEEP_LEARNING_SETUP.md         # Comprehensive setup guide

```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /mnt/user-data/outputs/updated_modular

# Basic dependencies
pip install streamlit pandas numpy pillow --break-system-packages

# For deep learning (optional but recommended)
pip install torch torchvision --break-system-packages
```

### 2. Setup StegExpose (Already Working)

StegExpose is already configured and should work if you have:
- Java installed
- StegExpose.jar in `~/StegExpose/`

Test it:
```bash
java -jar ~/StegExpose/StegExpose.jar --help
```

### 3. Setup Deep Learning (Optional)

**Quick Option:** Skip for now - the app will still work with StegExpose only

**Full Setup:** Follow `DEEP_LEARNING_SETUP.md` to install:
- PyTorch
- SRNet model
- Pre-trained weights

### 4. Run the Application

```bash
streamlit run app.py
```

## 🔬 How Inspect Mode Works Now

### Before (5 methods):
```
1. Chi-Square Analysis    ❌ Removed
2. RS Analysis            ❌ Removed  
3. Sample Pair Analysis   ❌ Removed
4. StegExpose             ✅ Kept
5. Deep Learning          ✅ Kept (improved)
```

### After (2 methods):
```
1. StegExpose (50% weight)
   - Statistical fusion combining 4 methods
   - Best for LSB detection in PNG
   - Fast and reliable
   
2. Deep Learning (50% weight)
   - CNN-based detection (SRNet)
   - Best for JPEG steganography
   - Detects J-UNIWARD, nsF5, UERD
```

### Detection Flow

1. **Upload Image** → Inspect Mode
2. **StegExpose** runs (if enabled)
   - Analyzes LSB patterns
   - Returns confidence score 0-100%
3. **Deep Learning** runs (if enabled and installed)
   - CNN inference on image
   - Returns confidence score 0-100%
4. **Overall Confidence** = Weighted average
   - ≥70% = HIGH (🚨)
   - ≥40% = MEDIUM (⚠️)
   - ≥20% = LOW (◐)
   - <20% = CLEAN (✓)

## 📊 Comparison: StegExpose vs Deep Learning

| Feature | StegExpose | Deep Learning (SRNet) |
|---------|------------|----------------------|
| **Best for** | PNG with LSB | JPEG with adaptive stego |
| **Methods** | Chi-Square, RS, Sample Pairs, Primary Sets | CNN-based pattern recognition |
| **Speed** | ~1-2 seconds | ~0.1s (GPU) / ~1s (CPU) |
| **Setup** | Easy (Java JAR) | Complex (PyTorch + model) |
| **Accuracy (LSB)** | ~90% | ~85% |
| **Accuracy (J-UNIWARD)** | ~50% (not designed for it) | ~98% |
| **False Positives** | Low | Very low |

## 🎯 When to Use What

### Use StegExpose When:
- Analyzing PNG images
- Looking for LSB steganography
- Want fast, simple detection
- Don't have GPU/PyTorch installed

### Use Deep Learning When:
- Analyzing JPEG images
- Looking for adaptive steganography (J-UNIWARD, nsF5, UERD)
- Have PyTorch installed
- Need highest accuracy for JPEG

### Use Both (Recommended):
- Get comprehensive coverage
- Combine statistical and CNN approaches
- Best overall detection rate

## 🔧 Troubleshooting

### "StegExpose not found"
```bash
# Download StegExpose
wget https://github.com/b3dk7/StegExpose/releases/download/0.1/StegExpose.jar -O ~/StegExpose/StegExpose.jar

# Test it
java -jar ~/StegExpose/StegExpose.jar --help
```

### "PyTorch not installed"
```bash
# Install PyTorch (CPU version)
pip install torch torchvision --break-system-packages

# Or install PyTorch (GPU version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 --break-system-packages
```

### "Model directory not found"
```bash
# Create model directory
mkdir -p ~/steg_models

# Copy SRNet model file (see DEEP_LEARNING_SETUP.md for how to get it)
# cp /path/to/srnet.pth ~/steg_models/
```

### Deep Learning Not Working
The app will still work fine with just StegExpose! Deep learning is optional for enhanced JPEG detection.

## 📈 Testing the Changes

### Test 1: PNG with LSB
```bash
# Create test image with steghide
echo "secret message" > /tmp/message.txt
steghide embed -cf test_clean.png -ef /tmp/message.txt -sf /tmp/test_stego.png -p ""

# Upload /tmp/test_stego.png to app in Inspect Mode
# Expected: StegExpose should detect it (high confidence)
```

### Test 2: Clean JPEG
```bash
# Upload any normal JPEG photo
# Expected: Both methods should show low confidence (clean)
```

### Test 3: JPEG with J-UNIWARD
```bash
# Need J-UNIWARD tool to create test image
# If you have it, create stego JPEG
# Expected: Deep Learning (if installed) should detect it
```

## 📚 Next Steps

1. **Run the app:** Test with PNG and JPEG images
2. **Optional:** Setup deep learning following DEEP_LEARNING_SETUP.md
3. **Optional:** Get pre-trained SRNet weights for JPEG detection

## 💡 Why This Approach is Better

**Old Approach (5 methods):**
- ❌ Chi-Square, RS, Sample Pairs redundant (already in StegExpose)
- ❌ Only worked on LSB (not adaptive steganography)
- ❌ High false positive rate for some methods
- ❌ Slow (running 5 separate analyses)

**New Approach (2 methods):**
- ✅ StegExpose combines 4 statistical methods (fusion)
- ✅ Deep learning handles adaptive steganography
- ✅ Covers both PNG (LSB) and JPEG (J-UNIWARD, etc.)
- ✅ Faster and more accurate
- ✅ Lower false positive rate

## 🎓 Learn More

- **StegExpose Paper:** https://github.com/b3dk7/StegExpose
- **SRNet Paper:** https://arxiv.org/abs/1904.07841
- **JPEG Steganography:** https://en.wikipedia.org/wiki/J-UNIWARD
- **Deep Learning Setup:** See DEEP_LEARNING_SETUP.md

---

**Questions?** Check DEEP_LEARNING_SETUP.md for detailed installation instructions.

**Status:** ✅ Ready to use with StegExpose (Deep Learning optional)
