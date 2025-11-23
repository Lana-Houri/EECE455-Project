import streamlit as st
import subprocess
import tempfile
import os
import re
import pandas as pd
import math
import numpy as np
from datetime import datetime
from collections import Counter
from PIL import Image

# =====================================
# Page Configuration & Theming
# =====================================
st.set_page_config(
    page_title="Universal Steg Analyzer",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Light/Dark friendly CSS with subtle glass UI
st.markdown(
    """
    <style>
      :root {
        --grad-1: linear-gradient(135deg, #6366f1 0%, #8b5cf6 40%, #ec4899 100%);
        --card-bg: rgba(255,255,255,0.7);
        --shadow: 0 6px 20px rgba(0,0,0,.08);
      }
      @media (prefers-color-scheme: dark) {
        :root{
          --card-bg: rgba(17,24,39,0.5);
        }
      }

      .container-narrow { max-width: 1200px; margin: 0 auto; }

      /* Header */
      .hero {
        padding: 18px 22px; border-radius: 16px; color: white;
        background: var(--grad-1); box-shadow: var(--shadow);
        display:flex; align-items:center; justify-content:space-between;
      }
      .hero-title { margin:0; font-size: 28px; font-weight: 800; letter-spacing:.2px; }
      .hero-sub { margin:6px 0 0; opacity:.95; font-size: 14px; }
      .hero-right { display:flex; gap:8px; }
      .chip { background: rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.25);
              padding:6px 10px; border-radius:999px; font-size:12px; backdrop-filter: blur(6px); }

      /* Card */
      .card { background: var(--card-bg); border:1px solid rgba(0,0,0,.05);
              border-radius: 14px; padding: 14px; box-shadow: var(--shadow); }

      /* Section Title */
      .section-title { font-size: 16px; font-weight: 700; margin: 2px 0 10px; }

      /* Metrics */
      .metrics { display:grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
      .metric { background: var(--card-bg); border:1px solid rgba(0,0,0,.05); border-radius: 12px;
                padding: 10px; text-align:center; }
      .metric .label { font-size: 12px; opacity: .7; }
      .metric .value { font-size: 22px; font-weight: 800; margin-top: 2px; }

      /* Signal banners */
      .signal {
        border-left-width: 6px; border-left-style: solid; border-radius: 12px;
        padding: 12px; margin: 8px 0; box-shadow: var(--shadow);
      }
      .s-strong { border-left-color: #ef4444; background: rgba(239,68,68,.06); }
      .s-medium { border-left-color: #f59e0b; background: rgba(245,158,11,.06); }
      .s-weak { border-left-color: #10b981; background: rgba(16,185,129,.06); }

      /* Table tweaks */
      .stDataFrame { border-radius: 10px; overflow: hidden; }

      /* Footer */
      .footer { text-align:center; opacity:.65; padding: 14px 0; font-size: 13px; }
      
      /* Info box */
      .info-box { 
        background: rgba(59, 130, 246, 0.08); 
        border-left: 4px solid #3b82f6; 
        padding: 12px; 
        border-radius: 8px; 
        margin: 8px 0;
        font-size: 14px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================
# Statistical Analysis for Suspicion Detection
# =====================================

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
            # Convert RGBA to RGB by removing alpha channel
            img = img.convert('RGB')
        elif img.mode in ('L', 'LA', 'P', '1'):
            # Convert grayscale/palette to RGB
            img = img.convert('RGB')
        elif img.mode not in ('RGB', 'YCbCr'):
            # Try to convert any other mode to RGB
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
        
        # 1. LSB Analysis - Check if LSB bits are too uniform
        red_lsb = img_array[:,:,0] & 1
        green_lsb = img_array[:,:,1] & 1
        blue_lsb = img_array[:,:,2] & 1
        
        # Calculate LSB entropy (should be close to 1.0 for natural images)
        from collections import Counter
        
        for lsb_data, name in [(red_lsb, "Red"), (green_lsb, "Green"), (blue_lsb, "Blue")]:
            flat_lsb = lsb_data.flatten()
            counts = Counter(flat_lsb)
            total = len(flat_lsb)
            
            # Calculate ratio of 0s to 1s
            zeros = counts.get(0, 0)
            ones = counts.get(1, 0)
            ratio = zeros / ones if ones > 0 else 0
            
            # Suspicious if ratio is too close to 1.0 (too uniform)
            if 0.98 < ratio < 1.02:
                results["indicators"].append(f"{name} channel LSB suspiciously uniform")
                results["suspicion_score"] += 15
                results["details"][f"{name}_LSB_ratio"] = f"{ratio:.4f} (suspicious)"
            else:
                results["details"][f"{name}_LSB_ratio"] = f"{ratio:.4f} (normal)"
        
        # 2. Byte Value Distribution - Check for unusual patterns
        flat_img = img_array.flatten()
        value_counts = Counter(flat_img)
        
        # Check if certain values appear with suspicious frequency
        most_common = value_counts.most_common(10)
        total_pixels = len(flat_img)
        
        suspicious_peaks = 0
        for value, count in most_common:
            percentage = (count / total_pixels) * 100
            if percentage > 15:  # More than 15% of pixels have same value
                suspicious_peaks += 1
        
        if suspicious_peaks >= 3:
            results["indicators"].append(f"Unusual byte value distribution ({suspicious_peaks} peaks)")
            results["suspicion_score"] += 10
            results["details"]["value_distribution"] = f"{suspicious_peaks} suspicious peaks"
        else:
            results["details"]["value_distribution"] = "Normal"
        
        # 3. Chunk Analysis for PNG
        if fmt == "PNG":
            try:
                with open(path, 'rb') as f:
                    data = f.read()
                
                # Count PNG chunks
                chunk_types = []
                pos = 8  # Skip PNG signature
                
                while pos < len(data) - 12:
                    try:
                        chunk_length = int.from_bytes(data[pos:pos+4], 'big')
                        chunk_type = data[pos+4:pos+8].decode('ascii', errors='ignore')
                        chunk_types.append(chunk_type)
                        pos += 12 + chunk_length  # length + type + data + crc
                    except:
                        break
                
                # Check for unusual chunks
                unusual_chunks = [c for c in chunk_types if c not in ['IHDR', 'PLTE', 'IDAT', 'IEND', 'tRNS', 'gAMA', 'cHRM', 'sRGB', 'pHYs', 'tIME']]
                
                if unusual_chunks:
                    results["indicators"].append(f"Unusual PNG chunks detected: {', '.join(set(unusual_chunks))}")
                    results["suspicion_score"] += 20
                    results["details"]["unusual_chunks"] = ', '.join(set(unusual_chunks))
                else:
                    results["details"]["unusual_chunks"] = "None"
                
                # Check for excessive IDAT chunks (common in stego)
                idat_count = chunk_types.count('IDAT')
                if idat_count > 50:
                    results["indicators"].append(f"Excessive IDAT chunks ({idat_count})")
                    results["suspicion_score"] += 10
                    results["details"]["idat_chunks"] = f"{idat_count} (suspicious)"
                else:
                    results["details"]["idat_chunks"] = f"{idat_count} (normal)"
                    
            except Exception as e:
                results["details"]["png_analysis"] = f"Failed: {str(e)}"
        
        # 4. File Size vs Resolution Analysis
        file_size = os.path.getsize(path)
        width, height = img.size
        expected_size = width * height * 3  # RGB
        
        # PNG/BMP should compress, JPEG even more
        if fmt == "PNG":
            # PNG should be 20-70% of uncompressed
            compression_ratio = file_size / expected_size
            if compression_ratio > 0.8:
                results["indicators"].append("Poor compression ratio (possible hidden data)")
                results["suspicion_score"] += 15
                results["details"]["compression_ratio"] = f"{compression_ratio:.2%} (suspicious)"
            else:
                results["details"]["compression_ratio"] = f"{compression_ratio:.2%} (normal)"
        
        # 5. Sequential Pattern Detection (Pairs Analysis)
        # Sample 10000 random pixels to check for sequential patterns
        sample_size = min(10000, len(flat_img) - 1)
        if sample_size > 0:
            sample_indices = np.random.choice(len(flat_img) - 1, sample_size, replace=False)
            
            pairs_close = 0
            for idx in sample_indices:
                if abs(int(flat_img[idx]) - int(flat_img[idx + 1])) <= 1:
                    pairs_close += 1
            
            pairs_ratio = pairs_close / sample_size
            
            # Natural images should have ~40-60% close pairs
            if pairs_ratio < 0.35 or pairs_ratio > 0.70:
                results["indicators"].append(f"Unusual sequential pattern ratio ({pairs_ratio:.2%})")
                results["suspicion_score"] += 15
                results["details"]["pairs_analysis"] = f"{pairs_ratio:.2%} (suspicious)"
            else:
                results["details"]["pairs_analysis"] = f"{pairs_ratio:.2%} (normal)"
        else:
            results["details"]["pairs_analysis"] = "Skipped (image too small)"
        
        # 6. Color Channel Correlation
        # Natural images have correlated RGB channels
        r_channel = img_array[:,:,0].flatten()
        g_channel = img_array[:,:,1].flatten()
        b_channel = img_array[:,:,2].flatten()
        
        # Sample for speed
        sample_size = min(10000, len(r_channel))
        if sample_size > 1:
            sample_idx = np.random.choice(len(r_channel), sample_size, replace=False)
            
            r_sample = r_channel[sample_idx].astype(float)
            g_sample = g_channel[sample_idx].astype(float)
            b_sample = b_channel[sample_idx].astype(float)
            
            # Calculate correlation
            try:
                rg_corr = np.corrcoef(r_sample, g_sample)[0,1]
                rb_corr = np.corrcoef(r_sample, b_sample)[0,1]
                gb_corr = np.corrcoef(g_sample, b_sample)[0,1]
                
                avg_corr = (rg_corr + rb_corr + gb_corr) / 3
                
                # Natural images should have correlation > 0.7
                if avg_corr < 0.6:
                    results["indicators"].append(f"Low channel correlation ({avg_corr:.2f})")
                    results["suspicion_score"] += 10
                    results["details"]["channel_correlation"] = f"{avg_corr:.2f} (suspicious)"
                else:
                    results["details"]["channel_correlation"] = f"{avg_corr:.2f} (normal)"
            except:
                results["details"]["channel_correlation"] = "Failed to calculate"
        else:
            results["details"]["channel_correlation"] = "Skipped (image too small)"
        
        # Determine overall suspicion level
        score = results["suspicion_score"]
        if score >= 50:
            results["level"] = "HIGH"
            results["message"] = "⚠️ High suspicion of steganography detected"
        elif score >= 25:
            results["level"] = "MEDIUM"
            results["message"] = "⚡ Medium suspicion - possible steganography"
        elif score >= 10:
            results["level"] = "LOW"
            results["message"] = "◐ Low suspicion - likely clean"
        else:
            results["level"] = "CLEAN"
            results["message"] = "✓ Very low suspicion - appears clean"
        
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

def run_exiftool(path: str):
    """Extract metadata using exiftool."""
    try:
        result = subprocess.run(
            ["exiftool", path],
            capture_output=True,
            text=True,
            timeout=40,
        )
        raw_output = (result.stdout or "").strip()
        
        # Parse interesting metadata
        rows = []
        if raw_output:
            # Look for suspicious or unusual metadata
            lines = raw_output.split("\n")
            suspicious_tags = []
            
            for line in lines:
                line_lower = line.lower()
                # Check for comment fields, user comments, descriptions
                if any(tag in line_lower for tag in ["comment", "description", "user comment", 
                                                       "image description", "software", "artist",
                                                       "copyright", "gps"]):
                    suspicious_tags.append(line.strip())
            
            if suspicious_tags:
                payload = "\n".join(suspicious_tags)
                confidence, interpretation = classify_result(payload)
                
                if confidence != "None":
                    rows.append({
                        "Tool": "ExifTool",
                        "Layer": "Metadata/EXIF",
                        "Payload": payload[:500] + ("..." if len(payload) > 500 else ""),
                        "Full_Payload": payload,
                        "Confidence": confidence,
                        "Interpretation": interpretation,
                    })
        
        return raw_output, rows
        
    except FileNotFoundError:
        return "", []
    except subprocess.TimeoutExpired:
        return "", []


def run_binwalk(path: str):
    """Detect hidden/appended files using binwalk."""
    try:
        result = subprocess.run(
            ["binwalk", "-B", path],
            capture_output=True,
            text=True,
            timeout=40,
        )
        raw_output = (result.stdout or "").strip()
        
        rows = []
        if raw_output:
            # Parse binwalk output for embedded files
            lines = raw_output.split("\n")
            embedded_files = []
            
            for line in lines:
                # Skip header lines
                if "DECIMAL" in line or "-------" in line or not line.strip():
                    continue
                
                # Look for file signatures
                if any(sig in line.lower() for sig in ["compressed", "archive", "image", 
                                                         "zlib", "gzip", "jpeg", "png",
                                                         "certificate", "encrypted"]):
                    embedded_files.append(line.strip())
            
            if embedded_files:
                payload = "\n".join(embedded_files)
                
                rows.append({
                    "Tool": "Binwalk",
                    "Layer": "Embedded Files/Trailer",
                    "Payload": payload[:500] + ("..." if len(payload) > 500 else ""),
                    "Full_Payload": payload,
                    "Confidence": "Medium",
                    "Interpretation": "Embedded/appended file signatures detected",
                })
        
        return raw_output, rows
        
    except FileNotFoundError:
        return "", []
    except subprocess.TimeoutExpired:
        return "", []


def check_trailer_manual(path: str, fmt: str):
    """Manual check for data after end markers (PNG IEND, JPEG EOI)."""
    try:
        with open(path, 'rb') as f:
            data = f.read()
        
        trailer_data = None
        marker_name = ""
        
        if fmt == "PNG":
            # PNG IEND chunk: IEND + CRC (4 bytes)
            iend_marker = b'IEND\xae\x42\x60\x82'
            iend_pos = data.rfind(iend_marker)
            
            if iend_pos != -1 and iend_pos + len(iend_marker) < len(data):
                trailer_data = data[iend_pos + len(iend_marker):]
                marker_name = "IEND"
        
        elif fmt in ("JPG", "JPEG"):
            # JPEG EOI marker
            eoi_marker = b'\xff\xd9'
            eoi_pos = data.rfind(eoi_marker)
            
            if eoi_pos != -1 and eoi_pos + 2 < len(data):
                trailer_data = data[eoi_pos + 2:]
                marker_name = "EOI"
        
        rows = []
        if trailer_data and len(trailer_data) > 10:  # Ignore tiny trailing bytes
            # Try to decode as text
            try:
                text_data = trailer_data.decode('utf-8', errors='ignore')
                if is_printable_text(text_data, threshold=0.5):
                    payload = text_data
                else:
                    payload = f"<Binary data: {len(trailer_data)} bytes>"
            except:
                payload = f"<Binary data: {len(trailer_data)} bytes>"
            
            rows.append({
                "Tool": "Manual Check",
                "Layer": f"Trailer after {marker_name}",
                "Payload": payload[:500] + ("..." if len(payload) > 500 else ""),
                "Full_Payload": payload,
                "Confidence": "Strong",
                "Interpretation": f"Data found after {marker_name} marker ({len(trailer_data)} bytes)",
            })
        
        return rows
        
    except Exception as e:
        return []


# =====================================
# Helpers — Classification & Parsing
# =====================================

def is_printable_text(text: str, threshold: float = 0.7) -> bool:
    """
    Check if text is mostly printable/readable ASCII.
    Returns True if >= threshold of characters are printable.
    """
    if not text:
        return False
    
    printable_count = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
    return (printable_count / len(text)) >= threshold


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of text (0-8 bits for byte data)."""
    if not text:
        return 0.0
    
    byte_counts = Counter(text.encode('utf-8', errors='ignore'))
    total = sum(byte_counts.values())
    
    entropy = 0.0
    for count in byte_counts.values():
        probability = count / total
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy


def is_error_or_status_message(text: str) -> bool:
    """Check if text is an error/status message rather than extracted data."""
    if not text:
        return True
    
    # Common error/status patterns
    error_patterns = [
        r"could not extract",
        r"steghide:",
        r"error",
        r"failed",
        r"unable to",
        r"passphrase",
        r"^wrote extracted data",
        r"^reading",
        r"^extracting",
        r"usage:",
        r"no data found",
    ]
    
    text_lower = text.lower()
    
    # Check for error patterns
    for pattern in error_patterns:
        if re.search(pattern, text_lower):
            return True
    
    # If text is very short and looks like a status message
    if len(text) < 30 and any(word in text_lower for word in ["wrote", "reading", "done", "success"]):
        return True
    
    return False


def classify_result(text: str):
    """Assign confidence levels based on extracted text patterns."""
    text = (text or "").strip()

    if not text or text == "..":
        return "None", "No signal detected"
    
    # Check if this is an error/status message
    if is_error_or_status_message(text):
        return "None", "Status message (not extracted data)"

    text_len = len(text)
    
    # Check if it's mostly printable/readable text
    is_readable = is_printable_text(text, threshold=0.75)
    
    # Calculate entropy (high entropy suggests encrypted/compressed data)
    entropy = calculate_entropy(text)
    
    # Count readable words (sequences of 3+ letters)
    readable_words = len(re.findall(r'[A-Za-z]{3,}', text))
    
    # Strong: Readable plain text with low-medium entropy
    if is_readable and entropy < 6.0 and readable_words > 5:
        return "Strong", "Readable plaintext detected"
    
    # Strong: High entropy binary data (likely encrypted/compressed)
    if entropy > 7.0 and text_len > 100:
        return "Strong", "Binary/encrypted data detected (high entropy)"
    
    # Strong: Contains clear structured text
    if readable_words > 10 and text_len > 50:
        return "Strong", "Structured text with readable content"
    
    # Medium: Binary data with medium entropy
    if not is_readable and entropy > 5.0 and text_len > 50:
        return "Medium", "Binary data detected (possible encoding/compression)"
    
    # Medium: Some readable content but mixed with binary
    if readable_words >= 3 and text_len > 30:
        return "Medium", "Mixed readable and binary content"
    
    # Medium: Repeated patterns
    if len(set(text)) < len(text) * 0.1 and text_len > 50:
        return "Medium", "Repeated byte patterns detected"
    
    # Weak: Short content with some letters
    if readable_words > 0 and text_len < 50:
        return "Weak", "Short content with limited readable text"
    
    # Weak: File signature keywords
    if "file:" in text.lower():
        return "Weak", "File signature (possibly false positive)"
    
    # Weak: Very short or ambiguous
    if text_len < 20:
        return "Weak", "Very short payload - likely noise"
    
    return "Weak", "Ambiguous signal"


def parse_tool_output(raw: str, tool_name: str):
    """Generic parser for tool outputs."""
    rows = []
    
    if tool_name == "zsteg":
        lines = (raw or "").split("\n")
        for line in lines:
            if "text:" in line or "file:" in line or ".." in line:
                parts = line.split("..")
                try:
                    layer = parts[0].strip()
                    payload = parts[1].strip() if len(parts) > 1 else ""
                except Exception:
                    continue

                confidence, interpretation = classify_result(payload)
                
                # Skip if no signal
                if confidence == "None":
                    continue
                
                rows.append({
                    "Tool": "Zsteg",
                    "Layer": layer,
                    "Payload": payload[:500] + ("..." if len(payload) > 500 else ""),
                    "Full_Payload": payload,
                    "Confidence": confidence,
                    "Interpretation": interpretation,
                })
    
    elif tool_name in ["outguess", "jsteg", "steghide", "f5", "openstego"]:
        if not raw:
            return []
        
        low = raw.lower()
        
        # Check for no data cases - expanded list
        no_data_indicators = [
            "no data found",
            "extracted datalen: 0",
            "could not extract",
            "steghide: could not extract",
            "the file format of the file",
            "is not supported",
        ]
        
        if any(x in low for x in no_data_indicators):
            return []
        
        # Check for help/usage text
        if any(x in low for x in ["usage:", "[options]", "outguess 0.2"]):
            if "--- extracted data ---" not in low:
                return []
        
        # Extract payload
        payload = ""
        if "--- extracted data ---" in low:
            parts = raw.split("--- Extracted Data")
            if len(parts) > 1:
                # Remove the byte count header if present
                payload = re.sub(r'\(\d+ bytes\) ---\n?', '', parts[1], count=1).strip()
        else:
            # Don't use status messages as payload
            if not is_error_or_status_message(raw):
                payload = raw.strip()
        
        if payload:
            confidence, interpretation = classify_result(payload)
            
            # Skip if no signal
            if confidence == "None":
                return []
            
            rows.append({
                "Tool": tool_name.capitalize(),
                "Layer": f"{tool_name} extraction",
                "Payload": payload[:500] + ("..." if len(payload) > 500 else ""),
                "Full_Payload": payload,
                "Confidence": confidence,
                "Interpretation": interpretation,
            })
    
    return rows


# =====================================
# Tool Runner Functions - DECODE
# =====================================

def run_zsteg(path: str):
    """Run zsteg and return raw_output and parsed rows."""
    try:
        result = subprocess.run(
            ["zsteg", path],
            capture_output=True,
            text=True,
            timeout=40,
        )
        raw_output = (result.stdout or "") + (result.stderr or "")
    except FileNotFoundError:
        raw_output = ""
        st.error("❌ `zsteg` not found. Install: `sudo gem install zsteg`")
    except subprocess.TimeoutExpired:
        raw_output = ""
        st.error("⏱️ zsteg timed out.")

    rows = parse_tool_output(raw_output, "zsteg")
    return raw_output, rows


def run_outguess(path: str):
    """Run OutGuess in retrieve mode."""
    temp_output = os.path.join(tempfile.gettempdir(), f"outguess_extracted_{os.getpid()}.txt")
    
    try:
        result = subprocess.run(
            ["outguess", "-r", path, temp_output],
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        extracted_data = ""
        data_bytes = b""
        
        if os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            try:
                with open(temp_output, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_data = f.read()
            except:
                pass
            
            with open(temp_output, "rb") as f:
                data_bytes = f.read()
        
        status_msg = (result.stderr or "").strip()
        
        if extracted_data or data_bytes:
            byte_count = len(data_bytes)
            raw_output = f"{status_msg}\n\n--- Extracted Data ({byte_count} bytes) ---\n{extracted_data}".strip()
        else:
            raw_output = status_msg or (result.stdout or "").strip()
        
    except FileNotFoundError:
        raw_output = ""
        st.error("❌ `outguess` not found.")
    except subprocess.TimeoutExpired:
        raw_output = ""
        st.error("⏱️ OutGuess timed out.")
    finally:
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass

    rows = parse_tool_output(raw_output, "outguess")
    return raw_output, rows


def run_openstego(path: str, password: str = ""):
    """Run OpenStego extraction."""
    temp_output_dir = os.path.join(tempfile.gettempdir(), f"openstego_out_{os.getpid()}")
    os.makedirs(temp_output_dir, exist_ok=True)
    
    try:
        cmd = ["openstego", "extract", "-sf", path, "-xd", temp_output_dir]
        if password:
            cmd.extend(["-p", password])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        extracted_data = ""
        
        # Check if any files were extracted
        extracted_files = []
        if os.path.exists(temp_output_dir):
            extracted_files = os.listdir(temp_output_dir)
        
        if extracted_files:
            # Read the first extracted file
            first_file = os.path.join(temp_output_dir, extracted_files[0])
            try:
                with open(first_file, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_data = f.read()
            except:
                with open(first_file, "rb") as f:
                    extracted_data = f.read().decode("utf-8", errors="ignore")
        
        status_msg = (result.stderr or "").strip() + "\n" + (result.stdout or "").strip()
        
        if extracted_data:
            byte_count = len(extracted_data.encode('utf-8'))
            raw_output = f"{status_msg}\n\n--- Extracted Data ({byte_count} bytes) ---\n{extracted_data}".strip()
        else:
            raw_output = status_msg
        
    except FileNotFoundError:
        raw_output = ""
        st.error("❌ `openstego` not found. Install from https://www.openstego.com/")
    except subprocess.TimeoutExpired:
        raw_output = ""
        st.error("⏱️ OpenStego timed out.")
    finally:
        # Cleanup extracted files
        if os.path.exists(temp_output_dir):
            try:
                import shutil
                shutil.rmtree(temp_output_dir)
            except:
                pass

    rows = parse_tool_output(raw_output, "openstego")
    return raw_output, rows


def run_steghide(path: str, password: str = ""):
    """Run Steghide extraction."""
    temp_output = os.path.join(tempfile.gettempdir(), f"steghide_extracted_{os.getpid()}.txt")
    
    try:
        cmd = ["steghide", "extract", "-sf", path, "-xf", temp_output, "-f"]
        if password:
            cmd.extend(["-p", password])
        else:
            cmd.extend(["-p", ""])  # Empty password
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        extracted_data = ""
        data_bytes = b""
        
        if os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            try:
                with open(temp_output, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_data = f.read()
            except:
                pass
            
            with open(temp_output, "rb") as f:
                data_bytes = f.read()
        
        # Get status messages (stderr contains the "wrote extracted data" message)
        status_msg = (result.stderr or "").strip()
        stdout_msg = (result.stdout or "").strip()
        
        # Combine status messages but filter out the "wrote extracted data" line
        status_lines = []
        for line in (status_msg + "\n" + stdout_msg).split("\n"):
            if line.strip() and not re.match(r'^wrote extracted data to', line.lower()):
                status_lines.append(line)
        
        combined_status = "\n".join(status_lines).strip()
        
        if extracted_data or data_bytes:
            byte_count = len(data_bytes)
            raw_output = f"{combined_status}\n\n--- Extracted Data ({byte_count} bytes) ---\n{extracted_data}".strip()
        else:
            raw_output = combined_status
        
    except FileNotFoundError:
        raw_output = ""
        st.error("❌ `steghide` not found. Install: `sudo apt install steghide`")
    except subprocess.TimeoutExpired:
        raw_output = ""
        st.error("⏱️ Steghide timed out.")
    finally:
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass

    rows = parse_tool_output(raw_output, "steghide")
    return raw_output, rows


def run_jsteg(path: str):
    """Run Jsteg reveal."""
    temp_output = os.path.join(tempfile.gettempdir(), f"jsteg_extracted_{os.getpid()}.txt")
    
    try:
        result = subprocess.run(
            ["jsteg", "reveal", path, temp_output],
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        extracted_data = ""
        
        if os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            with open(temp_output, "r", encoding="utf-8", errors="ignore") as f:
                extracted_data = f.read()
        
        status_msg = (result.stderr or "").strip() + "\n" + (result.stdout or "").strip()
        
        if extracted_data:
            byte_count = len(extracted_data.encode('utf-8'))
            raw_output = f"{status_msg}\n\n--- Extracted Data ({byte_count} bytes) ---\n{extracted_data}".strip()
        else:
            raw_output = status_msg
        
    except FileNotFoundError:
        raw_output = ""
        st.error("❌ `jsteg` not found.")
    except subprocess.TimeoutExpired:
        raw_output = ""
        st.error("⏱️ Jsteg timed out.")
    finally:
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass

    rows = parse_tool_output(raw_output, "jsteg")
    return raw_output, rows


def run_f5(path: str, password: str = "abc123"):
    """Run F5 extraction."""
    temp_output = os.path.join(tempfile.gettempdir(), f"f5_extracted_{os.getpid()}.txt")
    
    try:
        result = subprocess.run(
            ["f5extract", "-e", temp_output, "-p", password, path],
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        extracted_data = ""
        
        if os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            with open(temp_output, "r", encoding="utf-8", errors="ignore") as f:
                extracted_data = f.read()
        
        status_msg = (result.stderr or "").strip() + "\n" + (result.stdout or "").strip()
        
        if extracted_data:
            byte_count = len(extracted_data.encode('utf-8'))
            raw_output = f"{status_msg}\n\n--- Extracted Data ({byte_count} bytes) ---\n{extracted_data}".strip()
        else:
            raw_output = status_msg
        
    except FileNotFoundError:
        raw_output = ""
        st.error("❌ `f5extract` not found.")
    except subprocess.TimeoutExpired:
        raw_output = ""
        st.error("⏱️ F5 timed out.")
    finally:
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass

    rows = parse_tool_output(raw_output, "f5")
    return raw_output, rows


# =====================================
# Tool Runner Functions - ENCODE
# =====================================

def encode_openstego(image_path: str, message: str, output_path: str, password: str = ""):
    """Encode message into PNG using OpenStego (Java-based)."""
    try:
        # Create a temporary file for the message
        temp_msg = os.path.join(tempfile.gettempdir(), f"openstego_msg_{os.getpid()}.txt")
        with open(temp_msg, "w", encoding="utf-8") as f:
            f.write(message)
        
        # Build OpenStego command
        cmd = ["openstego", "embed", "-mf", temp_msg, "-cf", image_path, "-sf", output_path]
        if password:
            cmd.extend(["-p", password])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        os.remove(temp_msg)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True, "Successfully encoded message into image"
        else:
            return False, (result.stderr or result.stdout or "Encoding failed")
    except FileNotFoundError:
        return False, "OpenStego not found. Install: Download from https://www.openstego.com/"
    except subprocess.TimeoutExpired:
        return False, "OpenStego timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


def encode_steghide(image_path: str, message: str, output_path: str, password: str = ""):
    """Encode message into JPG/BMP using steghide."""
    try:
        # Create a temporary file for the message
        temp_msg = os.path.join(tempfile.gettempdir(), f"steghide_msg_{os.getpid()}.txt")
        with open(temp_msg, "w", encoding="utf-8") as f:
            f.write(message)
        
        cmd = ["steghide", "embed", "-cf", image_path, "-ef", temp_msg, "-sf", output_path, "-f"]
        if password:
            cmd.extend(["-p", password])
        else:
            cmd.extend(["-p", ""])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40,
        )
        
        os.remove(temp_msg)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True, "Successfully encoded message into image"
        else:
            return False, (result.stderr or result.stdout or "Encoding failed")
    except FileNotFoundError:
        return False, "steghide not found. Install: sudo apt install steghide"
    except subprocess.TimeoutExpired:
        return False, "steghide timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


# =====================================
# Header
# =====================================
st.markdown('<div class="container-narrow">', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero">
      <div>
        <h1 class="hero-title">🕵️‍♂️ Universal Steganalysis Scanner</h1>
        <p class="hero-sub">
          <strong>Statistical Analysis · LSB Detection · Metadata Extraction · Embedded Files</strong>
        </p>
      </div>
      <div class="hero-right">
        <span class="chip">v4.0 Statistical Analysis</span>
        <span class="chip">{datetime.now().strftime('%b %d, %Y')}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================
# Mode Selection & Upload Zone Card
# =====================================
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Mode Selection</div>", unsafe_allow_html=True)
    
    mode = st.radio(
        "Choose operation mode:",
        ["🔍 Decode (Extract hidden data)", "🔒 Encode (Hide data in image)"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    is_encode_mode = "Encode" in mode
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.expander("📖 How it works", expanded=False):
        if is_encode_mode:
            st.markdown("""
            **Encoding (Hiding Data):**
            
            - **OpenStego** → PNG encoding with LSB steganography (optional password)
            - **Steghide** → JPG/BMP encoding with password support
            
            **Steps:**
            1. Upload a cover image
            2. Enter the message/data to hide
            3. Set a password (optional)
            4. Download the encoded image
            
            **Note:** PNG uses OpenStego, JPG/JPEG uses Steghide, BMP uses Steghide
            """)
        else:
            st.markdown("""
            **Decoding (Extracting Data):**
            
            **LSB-Based Detection:**
            - **Zsteg** → PNG analysis (LSB, color channels, metadata) - detection only
            - **OpenStego** → PNG extraction with password support (RandomLSB)
            - **Steghide** → JPG/BMP extraction with password support (DCT-based)
            
            **Advanced Detection:**
            - **ExifTool** → Metadata/EXIF extraction (comments, GPS, hidden tags)
            - **Binwalk** → File signature scanning (embedded/appended files)
            - **Trailer Check** → Manual detection of data after PNG IEND or JPEG EOI markers
            
            **Features:**
            - Auto-detection based on file format
            - Password support for OpenStego and Steghide
            - Entropy analysis for encrypted data
            - Smart filtering of status messages
            - Export results as CSV or text
            
            **Coverage:** ~90% of common steganography methods
            """)

    uploaded = st.file_uploader(
        "Drop an image (PNG/JPG/BMP)",
        type=["png", "jpg", "jpeg", "bmp"],
        label_visibility="collapsed",
        accept_multiple_files=False,
    )

# =====================================
# Early Exit: No file
# =====================================
if not uploaded:
    st.markdown("""
    <div class="card">
      <div class="section-title">Ready when you are</div>
      <p>Upload an image to begin. In <strong>Decode</strong> mode, the tool will extract hidden data. In <strong>Encode</strong> mode, you can hide your own data.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="footer">AUB Capstone Project · Universal Steganography Detection Platform</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================
# File Info + Preview
# =====================================
temp_path = os.path.join(tempfile.gettempdir(), uploaded.name)
with open(temp_path, "wb") as f:
    f.write(uploaded.read())

file_size_kb = os.path.getsize(temp_path) / 1024
fmt = uploaded.type.split("/")[-1].upper()
is_png = fmt == "PNG"
is_jpeg = fmt in ("JPG", "JPEG")
is_bmp = fmt == "BMP"

# =====================================
# ENCODE MODE
# =====================================
if is_encode_mode:
    colA, colB = st.columns([1, 1])
    
    with colA:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Cover Image</div>", unsafe_allow_html=True)
        st.image(temp_path, use_container_width=True)
        st.markdown(
            f"""
            <div style='display:grid;grid-template-columns:120px 1fr;gap:6px 10px;margin-top:10px;'>
              <div style='opacity:.7;'>Filename</div><div><code>{uploaded.name}</code></div>
              <div style='opacity:.7;'>Format</div><div><code>{fmt}</code></div>
              <div style='opacity:.7;'>Size</div><div><code>{file_size_kb:.2f} KB</code></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    with colB:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Message to Hide</div>", unsafe_allow_html=True)
        
        message = st.text_area(
            "Enter your secret message:",
            height=150,
            placeholder="Type your message here...",
            label_visibility="collapsed"
        )
        
        # Password support for all formats
        password = st.text_input(
            "Password (optional):",
            type="password",
            help="Leave empty for no password protection"
        )
        
        encode_button = st.button("🔒 Encode Message", type="primary", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if encode_button:
            if not message.strip():
                st.error("❌ Please enter a message to hide.")
            else:
                with st.spinner("Encoding message..."):
                    output_path = os.path.join(tempfile.gettempdir(), f"encoded_{uploaded.name}")
                    
                    if is_png:
                        success, msg = encode_openstego(temp_path, message, output_path, password)
                        tool_used = "OpenStego"
                    elif is_jpeg or is_bmp:
                        success, msg = encode_steghide(temp_path, message, output_path, password)
                        tool_used = "Steghide"
                    else:
                        success = False
                        msg = "Unsupported format"
                        tool_used = "None"
                    
                    if success:
                        st.success(f"✅ {msg} using {tool_used}")
                        
                        st.markdown("---")
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<div class='section-title'>Download Encoded Image</div>", unsafe_allow_html=True)
                        
                        with open(output_path, "rb") as f:
                            st.download_button(
                                "📥 Download Encoded Image",
                                f.read(),
                                file_name=f"encoded_{uploaded.name}",
                                mime=uploaded.type,
                                use_container_width=True
                            )
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Cleanup
                        try:
                            os.remove(output_path)
                        except:
                            pass
                    else:
                        st.error(f"❌ Encoding failed: {msg}")
    
    # Cleanup
    try:
        os.remove(temp_path)
    except:
        pass
    
    st.markdown('<div class="footer">AUB Capstone Project · Universal Steganography Detection Platform</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================
# DECODE MODE (Original functionality)
# =====================================

colA, colB, colC = st.columns([1.2, 2, 1])

with colA:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>File Information</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style='display:grid;grid-template-columns:120px 1fr;gap:6px 10px;'>
          <div style='opacity:.7;'>Filename</div><div><code>{uploaded.name}</code></div>
          <div style='opacity:.7;'>Format</div><div><code>{fmt}</code></div>
          <div style='opacity:.7;'>Size</div><div><code>{file_size_kb:.2f} KB</code></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        "📥 Download File",
        data=open(temp_path, "rb").read(),
        file_name=uploaded.name,
        mime=uploaded.type,
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with colB:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Preview</div>", unsafe_allow_html=True)
    st.image(temp_path, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with colC:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Detection Tool</div>", unsafe_allow_html=True)
    
    # Tool selection based on format
    if is_png:
        # For PNG, offer both Zsteg and OpenStego
        selected_tool = st.radio(
            "Select tool:",
            ["Zsteg (detection)", "OpenStego (extraction)"],
            help="Zsteg detects various LSB patterns, OpenStego extracts password-protected data"
        )
        selected_tool = "Zsteg" if "Zsteg" in selected_tool else "OpenStego"
        
        # Password for OpenStego
        if selected_tool == "OpenStego":
            st.markdown("---")
            openstego_pass = st.text_input(
                "OpenStego password (optional):",
                type="password",
                key="openstego_pass",
                help="Leave empty to try no password"
            )
        else:
            openstego_pass = ""
    elif is_jpeg:
        selected_tool = "Steghide"
        st.info("🔧 Using **Steghide** for JPG/JPEG analysis")
        st.markdown("---")
        steghide_pass = st.text_input(
            "Steghide password (optional):",
            type="password",
            key="steghide_pass",
            help="Leave empty to try no password"
        )
        openstego_pass = ""
    elif is_bmp:
        selected_tool = "Steghide"
        st.info("🔧 Using **Steghide** for BMP analysis")
        st.markdown("---")
        steghide_pass = st.text_input(
            "Steghide password (optional):",
            type="password",
            key="steghide_pass",
            help="Leave empty to try no password"
        )
        openstego_pass = ""
    else:
        selected_tool = "Zsteg"
        st.info("🔧 Using **Zsteg** by default")
        steghide_pass = ""
        openstego_pass = ""
    
    # Set steghide_pass for PNG if not already set
    if is_png:
        steghide_pass = ""
    
    # Advanced detection options
    st.markdown("---")
    st.markdown("<div style='font-size:14px; font-weight:600; margin-bottom:8px;'>Advanced Detection</div>", unsafe_allow_html=True)
    
    run_exiftool_check = st.checkbox(
        "📝 Metadata/EXIF Analysis (ExifTool)",
        value=True,
        help="Extract and analyze metadata tags (comments, GPS, software info)"
    )
    
    run_binwalk_check = st.checkbox(
        "🔍 Embedded Files Detection (Binwalk)",
        value=True,
        help="Scan for hidden/appended files using file signatures"
    )
    
    run_trailer_check = st.checkbox(
        "📎 Trailer Data Check (Manual)",
        value=True,
        help=f"Check for data after {'IEND (PNG)' if is_png else 'EOI (JPG)'} marker"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================
# Statistical Suspicion Analysis
# =====================================
st.markdown("---")
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📊 Statistical Suspicion Analysis</div>", unsafe_allow_html=True)

with st.spinner("Analyzing image for statistical anomalies..."):
    suspicion_results = analyze_image_suspicion(temp_path, fmt)

# Display suspicion level with color coding
if suspicion_results["level"] == "HIGH":
    st.markdown(f"""
    <div class="signal s-strong">
      <strong>{suspicion_results["message"]}</strong><br/>
      Suspicion Score: <strong>{suspicion_results["suspicion_score"]}/100</strong>
    </div>
    """, unsafe_allow_html=True)
elif suspicion_results["level"] == "MEDIUM":
    st.markdown(f"""
    <div class="signal s-medium">
      <strong>{suspicion_results["message"]}</strong><br/>
      Suspicion Score: <strong>{suspicion_results["suspicion_score"]}/100</strong>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="signal s-weak">
      <strong>{suspicion_results["message"]}</strong><br/>
      Suspicion Score: <strong>{suspicion_results["suspicion_score"]}/100</strong>
    </div>
    """, unsafe_allow_html=True)

# Show indicators if any
if suspicion_results["indicators"]:
    with st.expander("🔍 Suspicion Indicators", expanded=True):
        for indicator in suspicion_results["indicators"]:
            # Filter out repeated characters (more than 10 times)
            if not any(char * 10 in indicator for char in set(indicator)):
                st.markdown(f"- {indicator}")

# Show technical details
if suspicion_results["details"]:
    with st.expander("📈 Technical Details", expanded=False):
        details_df = pd.DataFrame([
            {"Metric": k, "Value": v} 
            for k, v in suspicion_results["details"].items()
        ])
        st.dataframe(details_df, use_container_width=True, hide_index=True)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================
# Run Selected Tool + Advanced Checks
# =====================================
all_rows = []
all_raw_outputs = {}

with st.spinner(f"Running {selected_tool}..."):
    if selected_tool == "Zsteg":
        raw, rows = run_zsteg(temp_path)
        all_raw_outputs["Zsteg"] = raw
        all_rows.extend(rows)
    
    elif selected_tool == "OpenStego":
        raw, rows = run_openstego(temp_path, openstego_pass)
        all_raw_outputs["OpenStego"] = raw
        all_rows.extend(rows)
    
    elif selected_tool == "Steghide":
        raw, rows = run_steghide(temp_path, steghide_pass)
        all_raw_outputs["Steghide"] = raw
        all_rows.extend(rows)

# Run advanced detection methods if selected
if run_exiftool_check:
    with st.spinner("Running ExifTool metadata analysis..."):
        raw, rows = run_exiftool(temp_path)
        if raw:
            all_raw_outputs["ExifTool"] = raw
        all_rows.extend(rows)

if run_binwalk_check:
    with st.spinner("Running Binwalk file signature scan..."):
        raw, rows = run_binwalk(temp_path)
        if raw:
            all_raw_outputs["Binwalk"] = raw
        all_rows.extend(rows)

if run_trailer_check:
    with st.spinner("Checking for trailer data..."):
        rows = check_trailer_manual(temp_path, fmt)
        all_rows.extend(rows)

# DataFrame
display_cols = ["Tool", "Layer", "Payload", "Confidence", "Interpretation"]
df = pd.DataFrame(all_rows)[display_cols] if all_rows else pd.DataFrame(columns=display_cols)
df_full = pd.DataFrame(all_rows) if all_rows else pd.DataFrame(columns=display_cols + ["Full_Payload"])

strong = df[df["Confidence"] == "Strong"] if not df.empty else df
medium = df[df["Confidence"] == "Medium"] if not df.empty else df
weak = df[df["Confidence"] == "Weak"] if not df.empty else df

# =====================================
# Overview — Banners + Metrics
# =====================================
st.markdown("---")

if df.empty:
    st.markdown("""
    <div class="signal s-weak">
      <strong>✓ Clean Image</strong><br/>
      No steganographic signals detected.
    </div>
    """, unsafe_allow_html=True)
else:
    if len(strong) > 0:
        st.markdown("""
        <div class="signal s-strong">
          <strong>⚠️ Strong Indicators Detected</strong><br/>
          Embedded data found. This may be plaintext, encrypted, or compressed data. Review details below.
        </div>
        """, unsafe_allow_html=True)
        
        if any("Binary/encrypted" in row["Interpretation"] or "high entropy" in row["Interpretation"] 
               for row in all_rows if row["Confidence"] == "Strong"):
            st.markdown("""
            <div class="info-box">
              <strong>ℹ️ Binary/Encrypted Data Detected</strong><br/>
              The extracted data appears to be encrypted, compressed, or binary encoded. 
              You may need a decryption key or decompression tool to read the actual content.
            </div>
            """, unsafe_allow_html=True)
            
    elif len(medium) > 0:
        st.markdown("""
        <div class="signal s-medium">
          <strong>⚡ Medium Indicators Detected</strong><br/>
          Suspicious patterns found. Manual verification recommended.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="signal s-weak">
          <strong>◐ Low Indicators</strong><br/>
          Only weak/ambiguous signals detected. Likely false positives.
        </div>
        """, unsafe_allow_html=True)

# Metrics row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Signals", int(len(df)))
with m2:
    st.metric("Strong", int(len(strong)))
with m3:
    st.metric("Medium", int(len(medium)))
with m4:
    st.metric("Weak", int(len(weak)))

# =====================================
# Tabs — Details / Table / Raw
# =====================================
tab1, tab2, tab3 = st.tabs(["🔎 Signal Details", "📋 Results Table", "🧾 Raw Outputs"]) 

with tab1:
    if df.empty:
        st.info("No signals detected.")
    else:
        if len(strong) > 0:
            with st.expander(f"🔴 Strong Signals ({len(strong)})", expanded=True):
                for idx, row in strong.iterrows():
                    full_row = df_full.iloc[idx]
                    st.markdown(f"**Tool**: `{row['Tool']}` | **Layer**: `{row['Layer']}`")
                    st.caption(row['Interpretation'])
                    
                    st.code(row['Payload'] or "(empty)", language="text")
                    
                    if len(full_row.get('Full_Payload', '')) > 500:
                        st.download_button(
                            "💾 Download Full Payload",
                            full_row['Full_Payload'],
                            file_name=f"{row['Tool']}_payload_{idx}.txt",
                            mime="text/plain",
                            key=f"full_strong_{idx}",
                        )
                    
                    st.divider()
                    
        if len(medium) > 0:
            with st.expander(f"🟡 Medium Signals ({len(medium)})", expanded=False):
                for idx, row in medium.iterrows():
                    full_row = df_full.iloc[idx]
                    st.markdown(f"**Tool**: `{row['Tool']}` | **Layer**: `{row['Layer']}`")
                    st.caption(row['Interpretation'])
                    st.code(row['Payload'] or "(empty)", language="text")
                    
                    if len(full_row.get('Full_Payload', '')) > 500:
                        st.download_button(
                            "💾 Download Full Payload",
                            full_row['Full_Payload'],
                            file_name=f"{row['Tool']}_payload_{idx}.txt",
                            mime="text/plain",
                            key=f"full_medium_{idx}",
                        )
                    
                    st.divider()
                    
        if len(weak) > 0:
            with st.expander(f"🟢 Weak Signals ({len(weak)})", expanded=False):
                for idx, row in weak.iterrows():
                    full_row = df_full.iloc[idx]
                    st.markdown(f"**Tool**: `{row['Tool']}` | **Layer**: `{row['Layer']}`")
                    st.caption(row['Interpretation'])
                    st.code(row['Payload'] or "(empty)", language="text")
                    
                    if len(full_row.get('Full_Payload', '')) > 500:
                        st.download_button(
                            "💾 Download Full Payload",
                            full_row['Full_Payload'],
                            file_name=f"{row['Tool']}_payload_{idx}.txt",
                            mime="text/plain",
                            key=f"full_weak_{idx}",
                        )
                    
                    st.divider()

with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if df.empty:
        st.info("No results available.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True, height=300)
        colx, coly = st.columns([1,1])
        with colx:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download CSV",
                csv_bytes,
                file_name=f"steg_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with coly:
            payload_text = "\n\n=== PAYLOAD ===\n\n".join(
                df_full["Full_Payload"].fillna("").tolist() if "Full_Payload" in df_full.columns 
                else df["Payload"].fillna("").tolist()
            )
            st.download_button(
                "📥 Download All Payloads",
                payload_text,
                file_name=f"payloads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if not all_raw_outputs:
        st.info("No raw outputs captured.")
    else:
        for tool_name, raw_output in all_raw_outputs.items():
            with st.expander(f"📄 {tool_name} Raw Output", expanded=False):
                if raw_output.strip():
                    st.code(raw_output, language="text")
                    st.download_button(
                        f"💾 Download {tool_name} Output",
                        raw_output,
                        file_name=f"{tool_name.lower()}_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key=f"raw_{tool_name}",
                    )
                else:
                    st.info(f"No output from {tool_name}")
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================
# Cleanup & Footer
# =====================================
try:
    os.remove(temp_path)
except Exception:
    pass

st.markdown(f'<div class="footer">AUB Capstone Project · Universal Steganography Detection Platform · Tool: {selected_tool}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)