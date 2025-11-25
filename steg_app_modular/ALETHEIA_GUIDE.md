# Aletheia Steganography Detection Guide

## What is Aletheia?

Aletheia is an open-source steganalysis toolbox that uses machine learning to detect steganography in images. It's particularly effective for JPEG images and supports multiple detection methods.

## Installation

### Method 1: Clone and Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/daniellerch/aletheia.git
cd aletheia

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x aletheia.py
```

### Method 2: Install via pip (if available)

```bash
pip install aletheia
```

### Required Dependencies

Aletheia typically requires:
- Python 3.6+
- NumPy
- SciPy
- scikit-learn
- scikit-image
- TensorFlow or PyTorch (for deep learning models)
- jpegio (for JPEG DCT analysis)

## Basic Usage

### Command Line Usage

Aletheia is primarily a command-line tool. Here are common commands:

#### 1. Auto Detection (Best Method)
```bash
./aletheia.py auto image.jpg
```
Automatically detects the steganographic method used.

#### 2. Specific Detection Methods

**Sample Pairs Analysis (SPA):**
```bash
./aletheia.py spa image.jpg
```

**Chi-Square Attack:**
```bash
./aletheia.py chi image.jpg
```

**RS Analysis:**
```bash
./aletheia.py rs image.jpg
```

**Deep Learning Detection:**
```bash
./aletheia.py dct image.jpg
```

#### 3. Batch Analysis
```bash
./aletheia.py auto /path/to/images/
```

### Python Integration

Since Aletheia is a CLI tool, you can call it from Python using subprocess:

```python
import subprocess
import os

def run_aletheia(image_path: str, method: str = "auto"):
    """
    Run Aletheia steganalysis on an image.
    
    Args:
        image_path: Path to the image file
        method: Detection method ('auto', 'spa', 'chi', 'rs', 'dct')
    
    Returns:
        dict with detection results
    """
    aletheia_path = os.path.expanduser("~/aletheia/aletheia.py")
    
    if not os.path.exists(aletheia_path):
        return {
            "success": False,
            "error": "Aletheia not found. Install from: https://github.com/daniellerch/aletheia"
        }
    
    try:
        result = subprocess.run(
            [aletheia_path, method, image_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout + result.stderr
        
        # Parse output
        is_stego = "stego" in output.lower() or "hidden" in output.lower()
        confidence = 0.0
        
        # Extract confidence if available
        if "probability" in output.lower():
            import re
            prob_match = re.search(r'probability[:\s]+([\d.]+)', output, re.IGNORECASE)
            if prob_match:
                confidence = float(prob_match.group(1)) * 100
        
        return {
            "success": True,
            "is_stego": is_stego,
            "confidence": confidence if confidence > 0 else (80.0 if is_stego else 20.0),
            "raw_output": output,
            "method": f"Aletheia ({method})"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Aletheia timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## Detection Methods Available

1. **`auto`** - Automatically selects the best method
2. **`spa`** - Sample Pairs Analysis (LSB detection)
3. **`chi`** - Chi-Square Attack (LSB detection)
4. **`rs`** - RS Analysis (Regular/Singular groups)
5. **`dct`** - DCT-based detection (JPEG)
6. **`deep`** - Deep learning models (if available)

## Integration with Your App

The function `run_aletheia_detection()` has been added to `statistical_tools.py` and can be used alongside your existing methods.

### Example Usage in Your App

```python
from statistical_tools import run_aletheia_detection

# Analyze an image
result = run_aletheia_detection("path/to/image.jpg", method="auto")

if result["success"]:
    print(f"Steganography detected: {result['is_stego']}")
    print(f"Confidence: {result['confidence']:.1f}%")
else:
    print(f"Error: {result['error']}")
```

## Advantages of Aletheia

1. **Multiple Methods** - Combines statistical and deep learning approaches
2. **Well-Tested** - Used in research and competitions
3. **JPEG Focus** - Excellent for JPEG steganography detection
4. **Auto Mode** - Automatically selects the best detection method

## Limitations

1. **CLI Tool** - Must be called via subprocess (no direct Python API)
2. **Installation** - Requires cloning the repository
3. **Model Files** - Deep learning models may need to be downloaded separately

## Troubleshooting

### Aletheia Not Found
- Ensure you've cloned the repository
- Check that `aletheia.py` is executable: `chmod +x aletheia.py`
- Verify the path in the code matches your installation

### Import Errors
- Install all dependencies: `pip install -r requirements.txt`
- Ensure Python 3.6+ is being used

### Model Not Found (for deep learning)
- Download pre-trained models from Aletheia's repository
- Place models in the expected directory

## References

- GitHub: https://github.com/daniellerch/aletheia
- Documentation: https://daniellerch.me/stego/aletheia/
- Paper: https://www.theoj.org/joss-papers/joss.05982/10.21105.joss.05982.pdf

