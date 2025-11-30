import os
import re
import math
import tempfile
import subprocess
import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime
from PIL import Image
import streamlit as st


def analyze_image_suspicion(path: str, fmt: str):
    """
    Analyze image for statistical anomalies that suggest steganography.
    Returns suspicion score and detailed analysis.
    """
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(path)
        
        # Convert to RGB if needed
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        elif img.mode in ('L', 'LA', 'P', '1'):
            img = img.convert('RGB')
        elif img.mode not in ('RGB', 'YCbCr'):
            try:
                img = img.convert('RGB')
            except:
                return {
                    "suspicion_score": 0,
                    "level": "ERROR",
                    "message": f"Unsupported image mode: {img.mode}",
                    "indicators": [],
                    "details": {}
                }
        
        img_array = np.array(img)
        
        # Verify we have 3 channels
        if len(img_array.shape) != 3 or img_array.shape[2] != 3:
            return {
                "suspicion_score": 0,
                "level": "ERROR",
                "message": f"Image must have 3 color channels (RGB). Got shape: {img_array.shape}",
                "indicators": [],
                "details": {}
            }
        
        results = {
            "suspicion_score": 0,
            "indicators": [],
            "details": {}
        }
        
        # 1. LSB Analysis
        red_lsb = img_array[:,:,0] & 1
        green_lsb = img_array[:,:,1] & 1
        blue_lsb = img_array[:,:,2] & 1
        
        from collections import Counter
        
        for lsb_data, name in [(red_lsb, "Red"), (green_lsb, "Green"), (blue_lsb, "Blue")]:
            flat_lsb = lsb_data.flatten()
            counts = Counter(flat_lsb)
            total = len(flat_lsb)
            
            zeros = counts.get(0, 0)
            ones = counts.get(1, 0)
            ratio = zeros / ones if ones > 0 else 0
            
            if 0.98 < ratio < 1.02:
                results["indicators"].append(f"{name} channel LSB suspiciously uniform")
                results["suspicion_score"] += 15
                results["details"][f"{name}_LSB_ratio"] = f"{ratio:.4f} (suspicious)"
            else:
                results["details"][f"{name}_LSB_ratio"] = f"{ratio:.4f} (normal)"
        
        # 2. Byte Value Distribution
        flat_img = img_array.flatten()
        value_counts = Counter(flat_img)
        
        suspicious_peaks = 0
        for value, count in value_counts.most_common(10):
            percentage = (count / len(flat_img)) * 100
            if percentage > 15:
                suspicious_peaks += 1
        
        if suspicious_peaks >= 3:
            results["indicators"].append(f"Unusual byte value distribution ({suspicious_peaks} peaks)")
            results["suspicion_score"] += 10
            results["details"]["value_distribution"] = f"{suspicious_peaks} suspicious peaks"
        else:
            results["details"]["value_distribution"] = "Normal"
        
        # 3. PNG Chunk Analysis
        if fmt == "PNG":
            try:
                with open(path, 'rb') as f:
                    data = f.read()
                
                chunk_types = []
                pos = 8
                
                while pos < len(data) - 12:
                    try:
                        chunk_length = int.from_bytes(data[pos:pos+4], 'big')
                        chunk_type = data[pos+4:pos+8].decode('ascii', errors='ignore')
                        chunk_types.append(chunk_type)
                        pos += 12 + chunk_length
                    except:
                        break
                
                unusual_chunks = [c for c in chunk_types if c not in ['IHDR', 'PLTE', 'IDAT', 'IEND', 'tRNS', 'gAMA', 'cHRM', 'sRGB', 'pHYs', 'tIME']]
                
                if unusual_chunks:
                    results["indicators"].append(f"Unusual PNG chunks: {', '.join(set(unusual_chunks))}")
                    results["suspicion_score"] += 20
                    results["details"]["unusual_chunks"] = ', '.join(set(unusual_chunks))
                else:
                    results["details"]["unusual_chunks"] = "None"
                
                idat_count = chunk_types.count('IDAT')
                if idat_count > 50:
                    results["indicators"].append(f"Excessive IDAT chunks ({idat_count})")
                    results["suspicion_score"] += 10
                    results["details"]["idat_chunks"] = f"{idat_count} (suspicious)"
                else:
                    results["details"]["idat_chunks"] = f"{idat_count} (normal)"
                    
            except Exception as e:
                results["details"]["png_analysis"] = f"Failed: {str(e)}"
        
        # 4. File Size vs Resolution
        file_size = os.path.getsize(path)
        width, height = img.size
        expected_size = width * height * 3
        
        if fmt == "PNG":
            compression_ratio = file_size / expected_size
            if compression_ratio > 0.8:
                results["indicators"].append("Poor compression ratio")
                results["suspicion_score"] += 15
                results["details"]["compression_ratio"] = f"{compression_ratio:.2%} (suspicious)"
            else:
                results["details"]["compression_ratio"] = f"{compression_ratio:.2%} (normal)"
        
        # 5. Sequential Pattern Detection
        sample_size = min(10000, len(flat_img) - 1)
        if sample_size > 0:
            sample_indices = np.random.choice(len(flat_img) - 1, sample_size, replace=False)
            
            pairs_close = sum(1 for idx in sample_indices if abs(int(flat_img[idx]) - int(flat_img[idx + 1])) <= 1)
            pairs_ratio = pairs_close / sample_size
            
            if pairs_ratio < 0.35 or pairs_ratio > 0.70:
                results["indicators"].append(f"Unusual sequential pattern ({pairs_ratio:.2%})")
                results["suspicion_score"] += 15
                results["details"]["pairs_analysis"] = f"{pairs_ratio:.2%} (suspicious)"
            else:
                results["details"]["pairs_analysis"] = f"{pairs_ratio:.2%} (normal)"
        
        # 6. Color Channel Correlation
        r_channel = img_array[:,:,0].flatten()
        g_channel = img_array[:,:,1].flatten()
        b_channel = img_array[:,:,2].flatten()
        
        sample_size = min(10000, len(r_channel))
        if sample_size > 1:
            sample_idx = np.random.choice(len(r_channel), sample_size, replace=False)
            
            try:
                r_sample = r_channel[sample_idx].astype(float)
                g_sample = g_channel[sample_idx].astype(float)
                b_sample = b_channel[sample_idx].astype(float)
                
                rg_corr = np.corrcoef(r_sample, g_sample)[0,1]
                rb_corr = np.corrcoef(r_sample, b_sample)[0,1]
                gb_corr = np.corrcoef(g_sample, b_sample)[0,1]
                
                avg_corr = (rg_corr + rb_corr + gb_corr) / 3
                
                if avg_corr < 0.6:
                    results["indicators"].append(f"Low channel correlation ({avg_corr:.2f})")
                    results["suspicion_score"] += 10
                    results["details"]["channel_correlation"] = f"{avg_corr:.2f} (suspicious)"
                else:
                    results["details"]["channel_correlation"] = f"{avg_corr:.2f} (normal)"
            except:
                results["details"]["channel_correlation"] = "Failed to calculate"
        
        # Determine level
        score = results["suspicion_score"]
        if score >= 50:
            results["level"] = "HIGH"
            results["message"] = "⚠️ High suspicion of steganography"
        elif score >= 25:
            results["level"] = "MEDIUM"
            results["message"] = "⚡ Medium suspicion"
        elif score >= 10:
            results["level"] = "LOW"
            results["message"] = "◐ Low suspicion"
        else:
            results["level"] = "CLEAN"
            results["message"] = "✓ Very low suspicion"
        
        return results
        
    except Exception as e:
        return {
            "suspicion_score": 0,
            "level": "ERROR",
            "message": f"Analysis failed: {str(e)}",
            "indicators": [],
            "details": {"error": str(e)}
        }


# =====================================
# Additional Detection Methods
# =====================================


