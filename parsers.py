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


def is_printable_text(text: str, threshold: float = 0.7) -> bool:
    """Check if text is mostly printable/readable ASCII."""
    if not text:
        return False
    
    printable_count = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
    return (printable_count / len(text)) >= threshold



def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of text."""
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
    """Check if text is an error/status message."""
    if not text:
        return True
    
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
    
    for pattern in error_patterns:
        if re.search(pattern, text_lower):
            return True
    
    if len(text) < 30 and any(word in text_lower for word in ["wrote", "reading", "done", "success"]):
        return True
    
    return False



def classify_result(text: str):
    """Assign confidence levels based on extracted text patterns."""
    text = (text or "").strip()

    if not text or text == "..":
        return "None", "No signal detected"
    
    if is_error_or_status_message(text):
        return "None", "Status message (not extracted data)"

    text_len = len(text)
    is_readable = is_printable_text(text, threshold=0.75)
    entropy = calculate_entropy(text)
    readable_words = len(re.findall(r'[A-Za-z]{3,}', text))
    
    if is_readable and entropy < 6.0 and readable_words > 5:
        return "Strong", "Readable plaintext detected"
    
    if entropy > 7.0 and text_len > 100:
        return "Strong", "Binary/encrypted data detected (high entropy)"
    
    if readable_words > 10 and text_len > 50:
        return "Strong", "Structured text with readable content"
    
    if not is_readable and entropy > 5.0 and text_len > 50:
        return "Medium", "Binary data detected (possible encoding/compression)"
    
    if readable_words >= 3 and text_len > 30:
        return "Medium", "Mixed readable and binary content"
    
    if len(set(text)) < len(text) * 0.1 and text_len > 50:
        return "Medium", "Repeated byte patterns detected"
    
    if readable_words > 0 and text_len < 50:
        return "Weak", "Short content with limited readable text"
    
    if "file:" in text.lower():
        return "Weak", "File signature (possibly false positive)"
    
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

                # Check if layer contains B1, B2, B3, B4, etc (LSB channels)
                # These are VERY strong indicators of steganography
                is_lsb_channel = bool(re.search(r'\bB[1-4]\b', layer, re.IGNORECASE))
                
                if is_lsb_channel:
                    # LSB channels (B1, B2, B3, B4) are extremely strong signals
                    confidence = "Strong"
                    interpretation = "LSB channel data detected - very high confidence steganography"
                else:
                    # Normal classification for other layers
                    confidence, interpretation = classify_result(payload)
                
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
        
        if any(x in low for x in ["usage:", "[options]", "outguess 0.2"]):
            if "--- extracted data ---" not in low:
                return []
        
        payload = ""
        if "--- extracted data ---" in low:
            parts = raw.split("--- Extracted Data")
            if len(parts) > 1:
                payload = re.sub(r'\(\d+ bytes\) ---\n?', '', parts[1], count=1).strip()
        else:
            if not is_error_or_status_message(raw):
                payload = raw.strip()
        
        if payload:
            confidence, interpretation = classify_result(payload)
            
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