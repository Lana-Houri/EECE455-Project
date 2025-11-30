import os
import tempfile
import streamlit as st
from PIL import Image

from statistical_tools import (
    run_stegexpose,
    run_deep_steganalysis,
    calculate_overall_detection_confidence,
)
from suspicion import analyze_image_suspicion


def render_analyze_page():
    st.markdown('<h2 class="section-header">🔬 Advanced Steganography Detection</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>Enhanced Detection Mode:</strong> This tool uses multiple detection methods including:
                <ul style="margin: 0.5rem 0 0 1rem; padding: 0; list-style-type: disc;">
                    <li><strong>Deep Learning (CNN)</strong> - SRNet for JPEG steganography</li>
                    <li><strong>Chi-Square Attack</strong> - Statistical LSB detection</li>
                    <li><strong>DCT Analysis</strong> - JPEG coefficient inspection</li>
                    <li><strong>StegExpose</strong> - LSB fusion detection (PNG)</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload an image to analyze",
        type=["png", "jpg", "jpeg"],
        help="Supported formats: PNG, JPEG",
    )
    
    if not uploaded_file:
        return
    
    image = Image.open(uploaded_file)
    file_size = len(uploaded_file.getvalue())
    width, height = image.size
    fmt = image.format or "Unknown"
    is_jpeg = fmt.upper() in ['JPEG', 'JPG']
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📷 Image Preview")
        st.image(image, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📋 Image Information")
        
        format_badge = "🖼️ JPEG" if is_jpeg else "🎨 PNG"
        analysis_type = "DCT + Chi-Square + Deep Learning" if is_jpeg else "LSB + StegExpose"
        
        st.markdown(f"""
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Format</div>
                    <div class="metric-value dynamic">{format_badge}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Size (KB)</div>
                    <div class="metric-value dynamic">{file_size / 1024:.1f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Dimensions</div>
                    <div class="metric-value dynamic">{width}x{height}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Analysis</div>
                    <div class="metric-value dynamic" style="font-size: clamp(0.7rem, 1.5vw, 0.85rem);">{analysis_type}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis options
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Analysis Options")
    
    col1, col2 = st.columns(2)
    with col1:
        run_deep = st.checkbox("Deep Learning / Statistical", value=True, 
                               help="CNN-based detection for JPEG, statistical for PNG")

    with col2:
        run_stegexp = st.checkbox("StegExpose", value=True,
                                 help="Statistical fusion LSB detection")
    st.markdown('</div>', unsafe_allow_html=True)
    run_rs = False
    run_spa = False
    
    if not st.button("🚀 Start Comprehensive Analysis", use_container_width=True):
        return
    
    with st.spinner("Analyzing image with multiple detection methods..."):
        temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_results = {}
        
        status_text.text("🔍 Running statistical suspicion analysis...")
        progress_bar.progress(10)
        suspicion_result = analyze_image_suspicion(temp_path, fmt)
        all_results['suspicion'] = suspicion_result
        
        if run_stegexp:
            status_text.text("📊 Running StegExpose LSB detection...")
            progress_bar.progress(25)
            stegexpose_result = run_stegexpose(temp_path)
            all_results['stegexpose'] = stegexpose_result
        
        if run_deep:
            if is_jpeg:
                status_text.text("🧠 Running Deep Learning / JPEG Statistical Analysis...")
            else:
                status_text.text("🔬 Running LSB Analysis...")
            progress_bar.progress(45)
            deep_result = run_deep_steganalysis(temp_path)
            all_results['deep_learning'] = deep_result
        
        status_text.text("📝 Calculating confidence scores...")
        progress_bar.progress(90)
        
        detection_results = {k: v for k, v in all_results.items() if k not in ['suspicion']}
        overall = calculate_overall_detection_confidence(detection_results)
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        st.markdown('<h3 class="section-header">📊 Detection Summary</h3>', unsafe_allow_html=True)
        
        conf_value = overall['overall_confidence']
        conf_level = overall['level']
        conf_color = overall['color']
        
        st.markdown(f"""
            <div class="confidence-meter">
                <div class="confidence-value">{conf_value:.1f}%</div>
                <div class="confidence-label">{conf_level}</div>
                <div class="progress-container" style="margin-top: 1rem;">
                    <div class="progress-bar" style="width: {conf_value}%; transition: width 1s ease;"></div>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-tertiary);">
                    {overall['methods_used']} detection methods used
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        alert_icon = "🚨" if conf_color == 'strong' else "⚠️" if conf_color == 'medium' else "✅"
        st.markdown(f"""
            <div class="alert-box alert-{conf_color}">
                <span class="alert-icon">{alert_icon}</span>
                <div><strong>{overall['message']}</strong></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<h3 class="section-header">🔬 Detection Methods</h3>', unsafe_allow_html=True)
        
        num_methods = sum([
            1,
            1 if run_stegexp else 0,
            1 if run_deep else 0
        ])
        cols = st.columns(min(num_methods, 4))
        col_idx = 0
        
        with cols[col_idx % len(cols)]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 📉 Statistical Suspicion")
            st.metric("Score", f"{suspicion_result['suspicion_score']}")
            st.markdown(f"**Level:** {suspicion_result['level']}")
            st.markdown(f"**Indicators:** {len(suspicion_result['indicators'])}")
            st.markdown('</div>', unsafe_allow_html=True)
        col_idx += 1
        
        if run_stegexp and 'stegexpose' in all_results:
            with cols[col_idx % len(cols)]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### 🔍 StegExpose")
                result = all_results['stegexpose']
                if result.get('success'):
                    st.metric("Confidence", f"{result['confidence']:.1f}%")
                    status = '🔴 Detected' if result.get('is_stego') else '🟢 Clean'
                    st.markdown(f"**Status:** {status}")
                    st.markdown(f"**Type:** {result.get('method_type', 'LSB Fusion')}")
                else:
                    st.warning(result.get('error', 'Not available'))
                st.markdown('</div>', unsafe_allow_html=True)
            col_idx += 1
        
        if run_deep and 'deep_learning' in all_results:
            with cols[col_idx % len(cols)]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                title = "🧠 Deep Learning" if is_jpeg else "🔬 LSB Analysis"
                st.markdown(f"#### {title}")
                result = all_results['deep_learning']
                if result.get('success'):
                    st.metric("Confidence", f"{result['confidence']:.1f}%")
                    status = '🔴 Detected' if result.get('is_stego') else '🟢 Clean'
                    st.markdown(f"**Status:** {status}")
                    st.markdown(f"**Type:** {result.get('method_type', 'N/A')}")
                else:
                    st.warning(result.get('error', 'Not available'))
                st.markdown('</div>', unsafe_allow_html=True)
            col_idx += 1
        
        st.markdown('<h3 class="section-header">📋 Detailed Results</h3>', unsafe_allow_html=True)
        
        with st.expander("📉 Statistical Suspicion Analysis Details"):
            st.markdown(f"**Level:** {suspicion_result['level']}")
            st.markdown(f"**Score:** {suspicion_result['suspicion_score']}")
            
            if suspicion_result['indicators']:
                st.markdown("**Indicators Found:**")
                for indicator in suspicion_result['indicators']:
                    st.markdown(f"- {indicator}")
            
            st.markdown("**Analysis Details:**")
            st.json(suspicion_result.get('details', {}))
        
        if run_stegexp and all_results.get('stegexpose', {}).get('success'):
            with st.expander("🔍 StegExpose Raw Output"):
                result = all_results['stegexpose']
                st.markdown(f"**Interpretation:** {result.get('interpretation', 'N/A')}")
                if result.get('estimated_bytes'):
                    st.markdown(f"**Estimated Hidden Data:** {result['estimated_bytes']} bytes")
                st.code(result.get('raw_output', 'No output'), language="text")
        
        if run_deep and all_results.get('deep_learning', {}).get('success'):
            deep = all_results['deep_learning']
            with st.expander("🧠 Deep Learning / Statistical Analysis Details"):
                st.markdown(f"**Method:** {deep.get('method_type', 'N/A')}")
                st.markdown(f"**Interpretation:** {deep.get('interpretation', 'N/A')}")
                st.code(deep.get('raw_output', 'No output'), language="text")
                
                if deep.get('details'):
                    st.markdown("**Sub-Analysis Results:**")
                    for method, result in deep['details'].items():
                        if isinstance(result, dict):
                            st.markdown(f"- **{method}:** {result.get('interpretation', 'N/A')}")
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📝 Analysis Summary")
        
        if conf_level == "HIGH":
            st.markdown("🚨 **High probability of steganography detected!**")
            st.markdown("Multiple detection methods indicate hidden data is present.")
        elif conf_level == "MEDIUM":
            st.markdown("⚠️ **Possible steganography detected.**")
            st.markdown("Some indicators suggest hidden data may be present.")
        else:
            st.markdown("✅ **Image appears clean.**")
            st.markdown("No significant steganography indicators found.")
        
        st.markdown("")
        st.markdown(f"**Detection Methods Used:** {overall['methods_used']}")
        st.markdown(f"**Overall Confidence:** {conf_value:.1f}%")
        st.markdown(f"**Image Type:** {'JPEG (DCT-based)' if is_jpeg else 'PNG (Lossless)'}")
        st.markdown('</div>', unsafe_allow_html=True)
