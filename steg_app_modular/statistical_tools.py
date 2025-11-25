"""
Enhanced Statistical Steganalysis Tools
======================================
Includes:
- StegExpose: LSB detection for PNG
- Deep Learning (SRNet/EfficientNet): JPEG steganalysis
- Chi-Square Attack: Statistical analysis for LSB
- RS Analysis: LSB detection through dual statistics
- DCT Analysis: JPEG coefficient analysis
- Histogram Analysis: Pixel distribution anomalies
- Aletheia: Comprehensive steganalysis toolbox
"""

import os
import subprocess
import re
import shutil
import math
import numpy as np
from PIL import Image
from collections import Counter

# =====================================================
# StegExpose - LSB Detection for PNG
# =====================================================

def run_stegexpose(image_path: str):
    """
    Run StegExpose for LSB detection with fusion techniques.
    Best for: PNG images with LSB steganography
    """
    try:
        # StegExpose requires DIRECTORY path, not file path
        temp_dir = f"/tmp/stegexpose_analysis_{os.getpid()}"
        os.makedirs(temp_dir, exist_ok=True)
        
        image_filename = os.path.basename(image_path)
        temp_image_path = os.path.join(temp_dir, image_filename)
        shutil.copy2(image_path, temp_image_path)
        
        try:
            result = subprocess.run(
                ["java", "-jar", os.path.expanduser("~/StegExpose/StegExpose.jar"), temp_dir],
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            output = result.stdout + result.stderr
            detection_score = None
            is_stego = False
            estimated_bytes = None

            suspicious_match = re.search(r'is suspicious.*?(\d+)\s*bytes', output, re.IGNORECASE)
            if suspicious_match:
                is_stego = True
                estimated_bytes = int(suspicious_match.group(1))
                detection_score = 85.0
            
            lines = output.split('\n')
            for line in lines:
                if image_filename in line or temp_dir in line:
                    asterisk_count = line.count('*')
                    if asterisk_count >= 3:
                        detection_score = 90.0
                        is_stego = True
                    elif asterisk_count >= 2:
                        detection_score = 70.0
                        is_stego = True
                    elif asterisk_count >= 1:
                        detection_score = 50.0
                        is_stego = True
                    break
            
            if detection_score is None and not is_stego:
                if 'Exception' not in output and 'Error' not in output:
                    detection_score = 10.0
                    is_stego = False
            
            if detection_score is None:
                detection_score = 5.0 if not is_stego else 60.0
            
            confidence = detection_score

            if is_stego and estimated_bytes:
                interpretation = f"LSB steganography detected. Estimated: {estimated_bytes} bytes"
            elif is_stego:
                interpretation = f"LSB steganography detected (confidence: {detection_score:.1f}%)"
            else:
                interpretation = "No LSB steganography detected"
            
            return {
                "success": True,
                "detection_score": detection_score,
                "is_stego": is_stego,
                "estimated_bytes": estimated_bytes,
                "confidence": confidence,
                "raw_output": output,
                "interpretation": interpretation,
                "method_type": "Statistical Fusion (LSB)"
            }
        
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            
    except FileNotFoundError:
        return {
            "success": False,
            "error": "StegExpose not found. Install: Download from https://github.com/b3dk7/StegExpose",
            "confidence": 0
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False, 
            "error": "StegExpose timed out (>60s)",
            "confidence": 0
        }
    except Exception as e:
        return {
            "success": False, 
            "error": f"StegExpose error: {str(e)}", 
            "confidence": 0
        }


# =====================================================
# Deep Learning Steganalysis - JPEG Detection
# =====================================================

def run_deep_steganalysis(image_path: str):
    """
    Deep learning-based steganalysis for JPEG images.
    Uses SRNet or falls back to statistical methods.
    
    Detects: J-UNIWARD, nsF5, UERD, Steghide, OutGuess
    """
    img_ext = os.path.splitext(image_path)[1].lower()
    is_jpeg = img_ext in ['.jpg', '.jpeg']
    
    # Try PyTorch-based deep learning first
    try:
        import torch
        import torchvision.transforms as transforms
        
        model_path = os.path.expanduser("~/steg_models/srnet.pth")
        
        if os.path.exists(model_path):
            return _run_srnet_detection(image_path, model_path)
        else:
            # No pre-trained model, use statistical fallback
            return _run_statistical_jpeg_analysis(image_path) if is_jpeg else _run_lsb_analysis(image_path)
            
    except ImportError:
        # PyTorch not installed, use statistical methods
        if is_jpeg:
            return _run_statistical_jpeg_analysis(image_path)
        else:
            return _run_lsb_analysis(image_path)
    except Exception as e:
        return {
            "success": False,
            "error": f"Deep learning error: {str(e)}",
            "confidence": 0
        }


def _run_srnet_detection(image_path: str, model_path: str):
    """Run SRNet CNN model for steganalysis."""
    try:
        import torch
        import torchvision.transforms as transforms
        import sys
        
        sys.path.append(os.path.expanduser("~/steg_models"))
        
        try:
            from srnet_model import load_srnet
            model = load_srnet(model_path)
        except ImportError:
            # Create simple model inline if srnet_model.py doesn't exist
            model = _create_simple_cnn()
            model.load_state_dict(torch.load(model_path, map_location='cpu'))
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        model.eval()
        
        # Preprocess image
        img = Image.open(image_path).convert('L')
        transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])
        ])
        img_tensor = transform(img).unsqueeze(0).to(device)
        
        # Run inference
        with torch.no_grad():
            output = model(img_tensor)
            if isinstance(output, tuple):
                output = output[0]
            probs = torch.softmax(output, dim=1).cpu().numpy()[0]
            stego_prob = probs[1] * 100 if len(probs) > 1 else probs[0] * 100
        
        confidence = stego_prob
        is_stego = confidence >= 50
        
        if confidence >= 70:
            interpretation = f"🚨 JPEG steganography detected (CNN: {confidence:.1f}%)"
        elif confidence >= 40:
            interpretation = f"⚠️ Possible JPEG steganography (CNN: {confidence:.1f}%)"
        else:
            interpretation = f"✓ Clean image (CNN: {100-confidence:.1f}%)"
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "raw_output": f"Cover: {100-stego_prob:.2f}%, Stego: {stego_prob:.2f}%",
            "interpretation": interpretation,
            "method_type": "Deep Learning (SRNet)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"SRNet error: {str(e)}",
            "confidence": 0
        }


def _create_simple_cnn():
    """Create a simple CNN for fallback (requires trained weights)."""
    import torch
    import torch.nn as nn
    
    class SimpleStegoNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(1, 32, 3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(64, 128, 3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d(1)
            )
            self.classifier = nn.Sequential(
                nn.Flatten(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Dropout(0.5),
                nn.Linear(64, 2)
            )
        
        def forward(self, x):
            x = self.features(x)
            return self.classifier(x)
    
    return SimpleStegoNet()


# =====================================================
# Statistical JPEG Analysis (Chi-Square + DCT)
# =====================================================

def _run_statistical_jpeg_analysis(image_path: str):
    """
    Statistical analysis specifically for JPEG images.
    Combines Chi-Square, DCT analysis, and histogram analysis.
    """
    try:
        results = {
            "chi_square": _chi_square_attack(image_path),
            "dct_analysis": _analyze_dct_coefficients(image_path),
            "histogram": _analyze_histogram(image_path)
        }
        
        # Combine scores
        scores = []
        interpretations = []
        
        for method, result in results.items():
            if result.get("success"):
                scores.append(result.get("confidence", 0))
                if result.get("is_stego"):
                    interpretations.append(f"{method}: detected")
        
        if scores:
            confidence = sum(scores) / len(scores)
        else:
            confidence = 20.0
        
        is_stego = confidence >= 50
        
        if confidence >= 70:
            interpretation = f"🚨 High probability of JPEG steganography ({confidence:.1f}%)"
        elif confidence >= 40:
            interpretation = f"⚠️ Possible JPEG steganography ({confidence:.1f}%)"
        else:
            interpretation = f"✓ No steganography indicators ({confidence:.1f}%)"
        
        raw_output = "\n".join([
            f"Chi-Square: {results['chi_square'].get('raw_output', 'N/A')}",
            f"DCT Analysis: {results['dct_analysis'].get('raw_output', 'N/A')}",
            f"Histogram: {results['histogram'].get('raw_output', 'N/A')}"
        ])
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "raw_output": raw_output,
            "interpretation": interpretation,
            "method_type": "Statistical JPEG Analysis",
            "details": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"JPEG analysis error: {str(e)}",
            "confidence": 0
        }


def _chi_square_attack(image_path: str):
    """
    Chi-Square Attack for detecting LSB steganography.
    Analyzes pairs of values (2i, 2i+1) in pixel data.
    """
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = np.array(img).flatten()
        
        # Group into pairs of values (PoVs)
        pairs = {}
        for val in pixels:
            pair_key = val // 2
            if pair_key not in pairs:
                pairs[pair_key] = [0, 0]
            pairs[pair_key][val % 2] += 1
        
        # Calculate chi-square statistic
        chi_square = 0
        degrees_of_freedom = 0
        
        for pair_key, counts in pairs.items():
            expected = (counts[0] + counts[1]) / 2
            if expected > 0:
                chi_square += ((counts[0] - expected) ** 2) / expected
                chi_square += ((counts[1] - expected) ** 2) / expected
                degrees_of_freedom += 1
        
        # Normalize chi-square
        if degrees_of_freedom > 0:
            normalized_chi = chi_square / degrees_of_freedom
        else:
            normalized_chi = 0
        
        # High chi-square indicates natural image (unequal PoV distribution)
        # Low chi-square indicates possible LSB embedding (equalized PoVs)
        # Threshold: chi < 1.0 is suspicious
        
        if normalized_chi < 0.5:
            confidence = 90.0
            is_stego = True
            interpretation = "Strong LSB embedding signature"
        elif normalized_chi < 1.0:
            confidence = 70.0
            is_stego = True
            interpretation = "Moderate LSB embedding signature"
        elif normalized_chi < 1.5:
            confidence = 40.0
            is_stego = False
            interpretation = "Weak indicators"
        else:
            confidence = 15.0
            is_stego = False
            interpretation = "Natural distribution"
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "chi_square": normalized_chi,
            "raw_output": f"χ² = {normalized_chi:.4f} (df={degrees_of_freedom})",
            "interpretation": interpretation
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0
        }


def _analyze_dct_coefficients(image_path: str):
    """
    Analyze DCT coefficients for JPEG steganography detection.
    Looks for anomalies in AC coefficient distribution.
    """
    try:
        # Try to use jpegio for DCT analysis
        try:
            import jpegio
            jpeg = jpegio.read(image_path)
            dct_coeffs = jpeg.coef_arrays[0].flatten()
            
            # Analyze histogram of DCT coefficients
            hist = Counter(dct_coeffs)
            
            # Check for anomalies in coefficient distribution
            # F5 and nsF5 create specific patterns
            zeros = hist.get(0, 0)
            ones = hist.get(1, 0) + hist.get(-1, 0)
            twos = hist.get(2, 0) + hist.get(-2, 0)
            
            total = len(dct_coeffs)
            zero_ratio = zeros / total if total > 0 else 0
            
            # Normal JPEG has ~60-70% zeros
            # F5 increases zeros (shrinkage)
            # J-UNIWARD has more uniform distribution
            
            if zero_ratio > 0.75:
                confidence = 75.0
                is_stego = True
                interpretation = "F5 shrinkage pattern detected"
            elif zero_ratio < 0.55:
                confidence = 65.0
                is_stego = True
                interpretation = "Unusual DCT distribution"
            else:
                confidence = 20.0
                is_stego = False
                interpretation = "Normal DCT distribution"
            
            return {
                "success": True,
                "confidence": confidence,
                "is_stego": is_stego,
                "raw_output": f"Zero ratio: {zero_ratio:.2%}, Non-zero AC: {total - zeros}",
                "interpretation": interpretation
            }
            
        except ImportError:
            # Fall back to PIL-based analysis
            return _analyze_dct_with_pil(image_path)
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0
        }


def _analyze_dct_with_pil(image_path: str):
    """Fallback DCT analysis using PIL."""
    try:
        from scipy.fftpack import dct
        
        img = Image.open(image_path).convert('L')
        img_array = np.array(img, dtype=np.float64)
        
        # Apply 2D DCT
        dct_coeffs = dct(dct(img_array.T, norm='ortho').T, norm='ortho')
        
        # Analyze coefficient distribution
        flat_coeffs = dct_coeffs.flatten()
        
        # Calculate entropy of coefficients
        hist, _ = np.histogram(flat_coeffs, bins=256)
        hist = hist[hist > 0]
        prob = hist / hist.sum()
        entropy = -np.sum(prob * np.log2(prob))
        
        # High entropy suggests modification
        if entropy > 7.5:
            confidence = 70.0
            is_stego = True
            interpretation = "High DCT entropy (possible modification)"
        elif entropy > 6.5:
            confidence = 40.0
            is_stego = False
            interpretation = "Moderate DCT entropy"
        else:
            confidence = 20.0
            is_stego = False
            interpretation = "Normal DCT entropy"
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "raw_output": f"DCT entropy: {entropy:.2f} bits",
            "interpretation": interpretation
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "scipy not installed for DCT analysis",
            "confidence": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0
        }


def _analyze_histogram(image_path: str):
    """Analyze pixel histogram for steganography indicators."""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get histogram for each channel
        r, g, b = img.split()
        
        anomalies = []
        
        for channel, name in [(r, 'R'), (g, 'G'), (b, 'B')]:
            hist = channel.histogram()
            
            # Check for PoV anomalies (pairs of values)
            pov_diff = 0
            for i in range(0, 256, 2):
                if hist[i] + hist[i+1] > 100:  # Only count significant pairs
                    ratio = min(hist[i], hist[i+1]) / max(hist[i], hist[i+1]) if max(hist[i], hist[i+1]) > 0 else 0
                    if ratio > 0.9:  # Very balanced pairs
                        pov_diff += 1
            
            if pov_diff > 100:
                anomalies.append(f"{name}: {pov_diff} balanced PoVs")
        
        if len(anomalies) >= 2:
            confidence = 75.0
            is_stego = True
            interpretation = "Multiple channels show PoV balancing"
        elif len(anomalies) == 1:
            confidence = 50.0
            is_stego = True
            interpretation = "Single channel shows PoV anomaly"
        else:
            confidence = 15.0
            is_stego = False
            interpretation = "Normal histogram distribution"
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "raw_output": ", ".join(anomalies) if anomalies else "No anomalies",
            "interpretation": interpretation
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0
        }


# =====================================================
# RS Analysis - LSB Detection
# =====================================================

def run_rs_analysis(image_path: str):
    """
    RS (Regular/Singular) Analysis for LSB detection.
    Analyzes groups of pixels using flipping masks.
    """
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = np.array(img)
        height, width, channels = pixels.shape
        
        results = []
        
        for c in range(channels):
            channel = pixels[:, :, c].astype(np.int32)
            
            # Define discrimination function (sum of differences)
            def discrimination(group):
                return np.sum(np.abs(np.diff(group)))
            
            # Apply flipping masks
            R_m = 0  # Regular groups after positive flip
            S_m = 0  # Singular groups after positive flip
            R_minus_m = 0  # Regular groups after negative flip
            S_minus_m = 0  # Singular groups after negative flip
            
            mask = np.array([0, 1, 1, 0])  # Flipping mask
            
            for i in range(0, height - 1, 2):
                for j in range(0, width - 3, 4):
                    group = channel[i, j:j+4].copy()
                    original_d = discrimination(group)
                    
                    # Positive flip (F1): flip LSB where mask=1
                    flipped = group.copy()
                    flipped[mask == 1] = flipped[mask == 1] ^ 1
                    flipped_d = discrimination(flipped)
                    
                    if flipped_d > original_d:
                        R_m += 1
                    elif flipped_d < original_d:
                        S_m += 1
                    
                    # Negative flip (F-1): flip LSB for all, then apply mask
                    neg_flipped = (group ^ 1).copy()
                    neg_flipped[mask == 1] = neg_flipped[mask == 1] ^ 1
                    neg_flipped_d = discrimination(neg_flipped)
                    
                    if neg_flipped_d > original_d:
                        R_minus_m += 1
                    elif neg_flipped_d < original_d:
                        S_minus_m += 1
            
            # Calculate embedding rate estimate
            total = R_m + S_m + R_minus_m + S_minus_m
            if total > 0:
                # Simplified RS estimation
                d0 = R_m - S_m
                d1 = R_minus_m - S_minus_m
                
                if abs(d0 + d1) > 0:
                    p = (d0 - d1) / (d0 + d1)
                    embedding_rate = max(0, min(1, (1 - p) / 2))
                else:
                    embedding_rate = 0
            else:
                embedding_rate = 0
            
            results.append({
                "channel": ["R", "G", "B"][c],
                "R_m": R_m,
                "S_m": S_m,
                "R_-m": R_minus_m,
                "S_-m": S_minus_m,
                "embedding_rate": embedding_rate
            })
        
        # Average embedding rate across channels
        avg_rate = np.mean([r["embedding_rate"] for r in results])
        
        if avg_rate > 0.3:
            confidence = 85.0
            is_stego = True
            interpretation = f"Strong LSB embedding ({avg_rate:.1%} estimated)"
        elif avg_rate > 0.15:
            confidence = 65.0
            is_stego = True
            interpretation = f"Moderate LSB embedding ({avg_rate:.1%} estimated)"
        elif avg_rate > 0.05:
            confidence = 40.0
            is_stego = False
            interpretation = f"Weak indicators ({avg_rate:.1%})"
        else:
            confidence = 15.0
            is_stego = False
            interpretation = "Clean image"
        
        raw_output = "\n".join([
            f"{r['channel']}: R_m={r['R_m']}, S_m={r['S_m']}, embed={r['embedding_rate']:.2%}"
            for r in results
        ])
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "embedding_rate": avg_rate,
            "raw_output": raw_output,
            "interpretation": interpretation,
            "method_type": "RS Analysis",
            "channel_results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"RS Analysis error: {str(e)}",
            "confidence": 0
        }


# =====================================================
# LSB Analysis (Stegano fallback)
# =====================================================

def _run_lsb_analysis(image_path: str):
    """LSB analysis using Stegano library or pure Python."""
    try:
        from stegano import lsb
        
        try:
            secret = lsb.reveal(image_path)
            
            if secret and len(secret.strip()) > 0:
                data_length = len(secret)
                confidence = min(90.0, 70 + (data_length / 100))
                interpretation = f"LSB data found ({data_length} characters)"
                is_stego = True
                raw_output = f"Detected {data_length} characters of hidden data"
            else:
                confidence = 20.0
                interpretation = "No LSB steganography detected"
                is_stego = False
                raw_output = "No hidden data found"
                
        except Exception:
            confidence = 15.0
            interpretation = "No LSB steganography detected"
            is_stego = False
            raw_output = "LSB analysis found no hidden data"
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "raw_output": raw_output,
            "interpretation": interpretation,
            "method_type": "LSB Analysis"
        }
        
    except ImportError:
        # Pure Python LSB check
        return _pure_python_lsb_check(image_path)


def _pure_python_lsb_check(image_path: str):
    """Pure Python LSB analysis without external libraries."""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = np.array(img)
        
        # Extract LSBs
        lsb_bits = pixels & 1
        
        # Calculate entropy of LSB plane
        flat_lsb = lsb_bits.flatten()
        ones = np.sum(flat_lsb)
        zeros = len(flat_lsb) - ones
        total = len(flat_lsb)
        
        # Perfect 50/50 split is suspicious
        ratio = ones / total if total > 0 else 0
        
        if 0.48 < ratio < 0.52:
            confidence = 75.0
            is_stego = True
            interpretation = "LSB plane shows suspiciously uniform distribution"
        elif 0.45 < ratio < 0.55:
            confidence = 45.0
            is_stego = False
            interpretation = "LSB distribution slightly unusual"
        else:
            confidence = 15.0
            is_stego = False
            interpretation = "Normal LSB distribution"
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "raw_output": f"LSB ratio: {ratio:.4f} (ones/total)",
            "interpretation": interpretation,
            "method_type": "Pure LSB Analysis"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0
        }


# =====================================================
# Sample Pairs Analysis (SPA) - Advanced LSB Detection
# =====================================================

def run_spa_analysis(image_path: str):
    """
    Sample Pairs Analysis for LSB steganalysis.
    More robust than Chi-Square for detecting LSB embedding.
    """
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = np.array(img).flatten()
        n = len(pixels)
        
        # Count sample pairs
        P = {}  # (u, v) pairs
        
        for i in range(0, n - 1, 2):
            u, v = pixels[i], pixels[i + 1]
            key = (u, v)
            P[key] = P.get(key, 0) + 1
        
        # Calculate beta (embedding rate estimate)
        X = 0  # Close pairs
        Y = 0  # Matching pairs
        Z = 0  # Other pairs
        
        for (u, v), count in P.items():
            if u == v:
                Y += count
            elif abs(u - v) == 1:
                X += count
            else:
                Z += count
        
        total_pairs = X + Y + Z
        
        if total_pairs > 0 and (X + Y) > 0:
            beta = (X - Y) / (X + Y)
            embedding_rate = max(0, min(1, (1 - beta) / 2))
        else:
            embedding_rate = 0
        
        if embedding_rate > 0.25:
            confidence = 80.0
            is_stego = True
            interpretation = f"SPA detected LSB embedding (~{embedding_rate:.1%})"
        elif embedding_rate > 0.1:
            confidence = 55.0
            is_stego = True
            interpretation = f"SPA found weak embedding indicators ({embedding_rate:.1%})"
        else:
            confidence = 20.0
            is_stego = False
            interpretation = "SPA: Clean image"
        
        return {
            "success": True,
            "confidence": confidence,
            "is_stego": is_stego,
            "embedding_rate": embedding_rate,
            "raw_output": f"X={X}, Y={Y}, Z={Z}, β={beta if 'beta' in dir() else 'N/A':.4f}",
            "interpretation": interpretation,
            "method_type": "Sample Pairs Analysis"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0
        }


# =====================================================
# Overall Confidence Calculation
# =====================================================

def calculate_overall_detection_confidence(results: dict):
    """
    Calculate overall detection confidence from multiple methods.
    
    Weights:
    - StegExpose (40%): Statistical fusion for LSB detection (PNG)
    - Deep Learning/Statistical (40%): CNN or statistical JPEG analysis
    - RS Analysis (20%): Additional LSB verification
    """
    
    weights = {
        "stegexpose": 0.40,
        "deep_learning": 0.40,
        "rs_analysis": 0.20,
    }
    
    weighted_sum = 0
    total_weight = 0
    
    for method, weight in weights.items():
        if method in results and results[method].get("success"):
            conf = results[method].get("confidence", 0)
            weighted_sum += conf * weight
            total_weight += weight
    
    overall_conf = weighted_sum / total_weight if total_weight > 0 else 0
    
    # Determine confidence level
    if overall_conf >= 70:
        level = "HIGH"
        msg = "🚨 High confidence of steganography detected"
        color = "strong"
    elif overall_conf >= 40:
        level = "MEDIUM"
        msg = "⚠️ Medium confidence - possible steganography"
        color = "medium"
    elif overall_conf >= 20:
        level = "LOW"
        msg = "◐ Low confidence - weak indicators"
        color = "weak"
    else:
        level = "CLEAN"
        msg = "✓ Very low confidence - likely clean"
        color = "weak"
    
    return {
        "overall_confidence": overall_conf,
        "level": level,
        "message": msg,
        "color": color,
        "methods_used": sum(1 for m in weights if m in results and results[m].get("success"))
    }


# =====================================================
# Comprehensive Analysis Runner
# =====================================================

def run_comprehensive_analysis(image_path: str):
    """
    Run all available statistical analysis methods.
    Returns combined results for UI display.
    """
    img_ext = os.path.splitext(image_path)[1].lower()
    is_jpeg = img_ext in ['.jpg', '.jpeg']
    
    results = {}
    
    # StegExpose (PNG focus)
    results["stegexpose"] = run_stegexpose(image_path)
    
    # Deep Learning / Statistical Analysis
    results["deep_learning"] = run_deep_steganalysis(image_path)
    
    # RS Analysis
    results["rs_analysis"] = run_rs_analysis(image_path)
    
    # SPA Analysis
    results["spa_analysis"] = run_spa_analysis(image_path)
    
    # JPEG-specific analysis
    if is_jpeg:
        results["chi_square"] = _chi_square_attack(image_path)
        results["dct_analysis"] = _analyze_dct_coefficients(image_path)
    
    # Overall confidence
    results["overall"] = calculate_overall_detection_confidence(results)
    
    return results


# =====================================================
# Aletheia Integration - Comprehensive Steganalysis
# =====================================================

def run_aletheia_detection(image_path: str, method: str = "auto"):
    """
    Run Aletheia steganalysis on an image.
    
    Aletheia is a comprehensive steganalysis toolbox that combines
    multiple detection methods including statistical and deep learning approaches.
    
    Methods available:
    - 'auto': Automatically selects the best method
    - 'spa': Sample Pairs Analysis (LSB detection)
    - 'chi': Chi-Square Attack (LSB detection)
    - 'rs': RS Analysis (Regular/Singular groups)
    - 'dct': DCT-based detection (JPEG)
    - 'deep': Deep learning models (if available)
    
    Args:
        image_path: Path to the image file
        method: Detection method to use (default: 'auto')
    
    Returns:
        dict with detection results:
        {
            "success": bool,
            "is_stego": bool,
            "confidence": float (0-100),
            "raw_output": str,
            "method_type": str,
            "interpretation": str
        }
    """
    # Try multiple possible paths for Aletheia
    possible_paths = [
        os.path.expanduser("~/aletheia/aletheia.py"),
        os.path.expanduser("~/aletheia/aletheia"),
        "/usr/local/bin/aletheia.py",
        "/usr/bin/aletheia.py",
        "aletheia.py",  # If in PATH
        "aletheia"     # If in PATH
    ]
    
    aletheia_path = None
    for path in possible_paths:
        if os.path.exists(path):
            aletheia_path = path
            break
    
    if not aletheia_path:
        # Check if it's executable in PATH
        try:
            result = subprocess.run(
                ["which", "aletheia.py"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                aletheia_path = result.stdout.strip()
        except:
            pass
    
    if not aletheia_path:
        return {
            "success": False,
            "error": "Aletheia not found. Install from: https://github.com/daniellerch/aletheia\n"
                     "Clone the repo and ensure aletheia.py is executable.",
            "confidence": 0,
            "is_stego": False,
            "method_type": "Aletheia (not installed)"
        }
    
    try:
        # Run Aletheia
        result = subprocess.run(
            [aletheia_path, method, image_path],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes timeout
            cwd=os.path.dirname(aletheia_path) if os.path.dirname(aletheia_path) else None
        )
        
        output = result.stdout + result.stderr
        
        # Parse Aletheia output
        is_stego = False
        confidence = 0.0
        embedding_rate = None
        interpretation = ""
        
        # Check for steganography indicators in output
        output_lower = output.lower()
        
        # Look for positive detection keywords
        positive_keywords = [
            "stego", "hidden", "detected", "positive", "suspicious",
            "embedding", "probability", "likely"
        ]
        
        # Look for negative detection keywords
        negative_keywords = [
            "clean", "no stego", "not detected", "negative", "cover"
        ]
        
        has_positive = any(keyword in output_lower for keyword in positive_keywords)
        has_negative = any(keyword in output_lower for keyword in negative_keywords)
        
        # Determine if steganography is detected
        if has_positive and not has_negative:
            is_stego = True
        elif has_negative and not has_positive:
            is_stego = False
        else:
            # Ambiguous - check for probability/confidence values
            is_stego = has_positive
        
        # Extract confidence/probability values
        # Look for patterns like "probability: 0.85" or "confidence: 85%"
        prob_patterns = [
            r'probability[:\s]+([\d.]+)',
            r'confidence[:\s]+([\d.]+)',
            r'p\s*=\s*([\d.]+)',
            r'([\d.]+)\s*%',
            r'([\d.]+)\s*probability'
        ]
        
        for pattern in prob_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    # Normalize to 0-100 range
                    if val <= 1.0:
                        confidence = val * 100
                    else:
                        confidence = min(100, val)
                    break
                except:
                    continue
        
        # Extract embedding rate if available
        embed_patterns = [
            r'embedding[_\s]*rate[:\s]+([\d.]+)',
            r'embed[:\s]+([\d.]+)',
            r'rate[:\s]+([\d.]+)'
        ]
        
        for pattern in embed_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    embedding_rate = float(match.group(1))
                    break
                except:
                    continue
        
        # Set default confidence if not found
        if confidence == 0.0:
            if is_stego:
                # High confidence if multiple indicators
                confidence = 75.0 if has_positive else 50.0
            else:
                confidence = 20.0
        
        # Create interpretation
        if is_stego:
            if confidence >= 70:
                interpretation = f"🚨 Aletheia detected steganography with high confidence ({confidence:.1f}%)"
            elif confidence >= 50:
                interpretation = f"⚠️ Aletheia detected possible steganography ({confidence:.1f}%)"
            else:
                interpretation = f"◐ Aletheia found weak indicators ({confidence:.1f}%)"
        else:
            interpretation = f"✓ Aletheia: No steganography detected ({100-confidence:.1f}% confidence)"
        
        if embedding_rate:
            interpretation += f" (embedding rate: {embedding_rate:.2%})"
        
        return {
            "success": True,
            "is_stego": is_stego,
            "confidence": confidence,
            "raw_output": output,
            "method_type": f"Aletheia ({method})",
            "interpretation": interpretation,
            "embedding_rate": embedding_rate
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Aletheia timed out (>120s). Image may be too large or method too slow.",
            "confidence": 0,
            "is_stego": False,
            "method_type": f"Aletheia ({method})"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Aletheia script not found at: {aletheia_path}",
            "confidence": 0,
            "is_stego": False,
            "method_type": "Aletheia (not found)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Aletheia error: {str(e)}",
            "confidence": 0,
            "is_stego": False,
            "method_type": f"Aletheia ({method})"
        }