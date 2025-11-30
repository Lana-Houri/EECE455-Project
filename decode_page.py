import os
import tempfile
import streamlit as st
from PIL import Image

from decode_tools import (
    run_zsteg,
    run_outguess,
    run_openstego,
    run_steghide,
    run_jsteg,
    run_f5,
)
from external_tools import run_exiftool, run_binwalk, check_trailer_manual


def _display_organized_signals(results_data):
    strong_signals = [r for r in results_data if r['Confidence'] == 'Strong']
    medium_signals = [r for r in results_data if r['Confidence'] == 'Medium']
    weak_signals = [r for r in results_data if r['Confidence'] == 'Weak']
    
    if strong_signals:
        st.markdown(f"""
            <div class="signal-section">
                <div class="signal-header">
                    <div class="signal-title">🚨 Strong Signals</div>
                    <div class="signal-count">{len(strong_signals)}</div>
                </div>
                <div class="signal-body">
        """, unsafe_allow_html=True)
        
        for signal in strong_signals:
            st.markdown(f"""
                <div class="signal-item strong">
                    <div class="signal-meta">
                        <span class="signal-tool">{signal['Tool']}</span>
                        <span class="signal-layer">{signal['Layer']}</span>
                        <span class="signal-confidence strong">STRONG</span>
                    </div>
                    <div class="signal-interpretation">{signal['Interpretation']}</div>
                    <div class="signal-payload-preview">{signal['Payload']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"View Full Payload - {signal['Tool']}"):
                st.code(signal['Full_Payload'], language="text")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    if medium_signals:
        st.markdown(f"""
            <div class="signal-section">
                <div class="signal-header">
                    <div class="signal-title">⚠️ Medium Signals</div>
                    <div class="signal-count">{len(medium_signals)}</div>
                </div>
                <div class="signal-body">
        """, unsafe_allow_html=True)
        
        for signal in medium_signals:
            st.markdown(f"""
                <div class="signal-item medium">
                    <div class="signal-meta">
                        <span class="signal-tool">{signal['Tool']}</span>
                        <span class="signal-layer">{signal['Layer']}</span>
                        <span class="signal-confidence medium">MEDIUM</span>
                    </div>
                    <div class="signal-interpretation">{signal['Interpretation']}</div>
                    <div class="signal-payload-preview">{signal['Payload']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"View Full Payload - {signal['Tool']}"):
                st.code(signal['Full_Payload'], language="text")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    if weak_signals:
        with st.expander(f"🔍 Weak Signals ({len(weak_signals)}) - Click to expand"):
            for signal in weak_signals:
                st.markdown(f"""
                    <div class="signal-item weak">
                        <div class="signal-meta">
                            <span class="signal-tool">{signal['Tool']}</span>
                            <span class="signal-layer">{signal['Layer']}</span>
                            <span class="signal-confidence weak">WEAK</span>
                        </div>
                        <div class="signal-interpretation">{signal['Interpretation']}</div>
                        <div class="signal-payload-preview">{signal['Payload']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"View Full Payload - {signal['Tool']}"):
                    st.code(signal['Full_Payload'], language="text")


def render_decode_page():
    st.markdown('<h2 class="section-header">🔓 Steganography Extraction</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>Extraction Mode:</strong> Attempt to extract hidden data using multiple steganography tools.
                Use manual inspection tools to examine metadata and embedded files separately.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload an image to extract data from",
        type=["png", "jpg", "jpeg"],
        help="Upload a steganographic image",
        key="decode_upload"
    )
    
    if not uploaded_file:
        return
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📷 Image Preview")
        st.image(Image.open(uploaded_file), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Extraction Settings")
        
        password = st.text_input("Password (if required)", type="password", placeholder="Leave empty if no password")
        
        tool_selection = st.multiselect(
            "Select extraction tools",
            ["Zsteg", "Steghide", "OutGuess", "OpenStego", "Jsteg", "F5"],
            default=["Zsteg", "Steghide"]
        )
        
        st.markdown("---")
        st.markdown("#### 🔍 Manual Inspection Tools")
        st.markdown("*These tools inspect file structure but are not counted as signals*")
        
        inspect_exif = st.checkbox("ExifTool (Metadata)", value=True)
        inspect_binwalk = st.checkbox("Binwalk (Embedded Files)", value=True)
        inspect_trailer = st.checkbox("Trailer Analysis", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.button("🔓 Extract Data", use_container_width=True):
        return
    
    with st.spinner("Running extraction tools..."):
        temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        image = Image.open(temp_path)
        fmt = image.format or "Unknown"
        
        all_results = []
        progress = st.progress(0)
        total_tools = len(tool_selection) + sum([inspect_exif, inspect_binwalk, inspect_trailer])
        current = 0
        
        for tool in tool_selection:
            current += 1
            progress.progress(current / total_tools)
            
            if tool == "Zsteg":
                raw, rows = run_zsteg(temp_path)
                all_results.extend(rows)
            elif tool == "Steghide":
                raw, rows = run_steghide(temp_path, password)
                all_results.extend(rows)
            elif tool == "OutGuess":
                raw, rows = run_outguess(temp_path)
                all_results.extend(rows)
            elif tool == "OpenStego":
                raw, rows = run_openstego(temp_path, password)
                all_results.extend(rows)
            elif tool == "Jsteg":
                raw, rows = run_jsteg(temp_path)
                all_results.extend(rows)
            elif tool == "F5":
                raw, rows = run_f5(temp_path, password if password else "abc123")
                all_results.extend(rows)
        
        progress.progress(1.0)
        
        st.markdown('<h3 class="section-header">📤 Extraction Results</h3>', unsafe_allow_html=True)
        
        if all_results:
            _display_organized_signals(all_results)
        else:
            st.markdown("""
                <div class="alert-box alert-weak">
                    <span class="alert-icon">✓</span>
                    <div><strong>No hidden data found</strong> with the selected extraction tools.</div>
                </div>
            """, unsafe_allow_html=True)
        
        if inspect_exif or inspect_binwalk or inspect_trailer:
            st.markdown('<h3 class="section-header">🔍 Manual Inspection</h3>', unsafe_allow_html=True)
            
            if inspect_exif:
                raw_exif, _ = run_exiftool(temp_path)
                with st.expander("📋 ExifTool Metadata"):
                    if raw_exif:
                        st.code(raw_exif, language="text")
                    else:
                        st.info("No metadata found or ExifTool not available.")
            
            if inspect_binwalk:
                raw_binwalk, binwalk_rows = run_binwalk(temp_path)
                with st.expander("📦 Binwalk Analysis"):
                    if raw_binwalk:
                        st.code(raw_binwalk, language="text")
                        if binwalk_rows:
                            st.warning("Embedded files detected!")
                    else:
                        st.info("No embedded files found or Binwalk not available.")
            
            if inspect_trailer:
                trailer_rows = check_trailer_manual(temp_path, fmt)
                with st.expander("📄 Trailer Analysis"):
                    if trailer_rows:
                        for row in trailer_rows:
                            st.warning(f"Data found: {row['Interpretation']}")
                            st.code(row['Payload'], language="text")
                    else:
                        st.info("No trailer data found.")
