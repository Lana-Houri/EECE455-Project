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

# Import from parsers module
from parsers import classify_result, is_printable_text


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
        
        rows = []
        if raw_output:
            lines = raw_output.split("\n")
            suspicious_tags = []
            
            for line in lines:
                line_lower = line.lower()
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
            lines = raw_output.split("\n")
            embedded_files = []
            
            for line in lines:
                if "DECIMAL" in line or "-------" in line or not line.strip():
                    continue
                
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
    """Manual check for data after end markers."""
    try:
        with open(path, 'rb') as f:
            data = f.read()
        
        trailer_data = None
        marker_name = ""
        
        if fmt == "PNG":
            iend_marker = b'IEND\xae\x42\x60\x82'
            iend_pos = data.rfind(iend_marker)
            
            if iend_pos != -1 and iend_pos + len(iend_marker) < len(data):
                trailer_data = data[iend_pos + len(iend_marker):]
                marker_name = "IEND"
        
        elif fmt in ("JPG", "JPEG"):
            eoi_marker = b'\xff\xd9'
            eoi_pos = data.rfind(eoi_marker)
            
            if eoi_pos != -1 and eoi_pos + 2 < len(data):
                trailer_data = data[eoi_pos + 2:]
                marker_name = "EOI"
        
        rows = []
        if trailer_data and len(trailer_data) > 10:
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