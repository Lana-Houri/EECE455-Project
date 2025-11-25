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
from parsers import parse_tool_output


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
        
        extracted_files = []
        if os.path.exists(temp_output_dir):
            extracted_files = os.listdir(temp_output_dir)
        
        if extracted_files:
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
            cmd.extend(["-p", ""])
        
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
        
        status_msg = (result.stderr or "").strip()
        stdout_msg = (result.stdout or "").strip()
        
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