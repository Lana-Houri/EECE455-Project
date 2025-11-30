import streamlit as st

from text_steg import (
    encode_text as text_encode_text,
    try_all_decoders as text_try_all_decoders,
    detect_all as text_detect_all,
    available_methods as text_available_methods,
)


def _render_detection_details(detection_data):
    zero_chars = detection_data.get("zero_width_chars", [])
    whitespace = detection_data.get("whitespace_patterns", {})
    homoglyphs = detection_data.get("homoglyphs")
    
    st.markdown("##### 🔎 Detection Summary")
    st.markdown(f"- Zero-width characters: **{len(zero_chars)}**")
    if zero_chars:
        preview = ''.join(zero_chars[:40])
        st.code(preview, language="text")
    
    st.markdown("- Whitespace anomalies:")
    st.markdown(f"  - Trailing spaces: {'Yes' if whitespace.get('trailing_spaces') else 'No'}")
    st.markdown(f"  - Multiple spaces: {'Yes' if whitespace.get('multiple_spaces') else 'No'}")
    st.markdown(f"  - Tabs detected: {'Yes' if whitespace.get('tabs') else 'No'}")
    
    if homoglyphs is None:
        st.info("Homoglyph detection requires the `confusables` package.")
    elif homoglyphs:
        st.warning(f"Potential homoglyph substitutions: {len(homoglyphs)} characters")
        for original, conf in homoglyphs[:5]:
            sample = ', '.join(conf[:3]) if isinstance(conf, list) else str(conf)
            st.markdown(f"- `{original}` → {sample}")
    else:
        st.success("No homoglyph anomalies detected.")


def render_text_page():
    st.markdown('<h2 class="section-header">📝 Text Steganography Lab</h2>', unsafe_allow_html=True)
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>Zero-width & Unicode Encoding:</strong> Experiment with lightweight text steganography.
                Encode secrets inside copyable text, scan suspicious passages for hidden markers, and run multiple decoder attempts.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    method_options = ["zwsp-py", "pyUnicode", "zwsteg-cli"]
    available_text_methods = text_available_methods()
    
    availability_rows = []
    for method in method_options:
        if method in available_text_methods:
            availability_rows.append(f"<li>✅ <strong>{method}</strong> ready</li>")
        else:
            availability_rows.append(f"<li>⚠️ <strong>{method}</strong> requires optional dependency</li>")
    st.markdown(
        f"""
        <div class="card">
            <h4>⚙️ Encoder Availability</h4>
            <ul>{''.join(availability_rows)}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    encode_col, analyze_col = st.columns(2)
    
    with encode_col:
        st.markdown("#### ✍️ Encode Secret")
        cover_text = st.text_area(
            "",
            height=220,
            key="text_steg_cover",
            placeholder="Cover text",
            label_visibility="collapsed"
        )
        secret_text = st.text_area(
            "",
            height=120,
            key="text_steg_secret",
            placeholder="Secret message",
            label_visibility="collapsed"
        )
        st.markdown("**Encoding method**")
        method_choice = st.selectbox(
            "",
            method_options,
            format_func=lambda m: f"{m} {'(ready)' if m in available_text_methods else '(install required)'}",
            key="text_steg_method",
            label_visibility="collapsed"
        )
        
        if st.button("Embed secret", use_container_width=True, key="text_steg_encode_btn"):
            if not cover_text or not secret_text:
                st.warning("Provide both cover text and a secret message.")
            else:
                try:
                    encoded_text = text_encode_text(method_choice, cover_text, secret_text)
                    st.success("Secret embedded successfully. Copy the text below.")
                    st.code(encoded_text, language="text")
                    
                    detection_data = text_detect_all(encoded_text)
                    _render_detection_details(detection_data)
                    
                    decoded = text_try_all_decoders(encoded_text)
                    if decoded:
                        st.markdown("##### 🔐 Decoder Verification")
                        for decoder_name, payload in decoded.items():
                            st.markdown(f"- {decoder_name}")
                            st.code(payload, language="text")
                    else:
                        st.info("No decoders succeeded (expected if dependencies missing).")
                except ImportError as exc:
                    st.error(f"Dependency missing: {exc}")
                except Exception as exc:
                    st.error(f"Encoding failed: {exc}")
    
    with analyze_col:
        st.markdown("#### 🧪 Analyze / Decode Text")
        suspect_text = st.text_area(
            "",
            height=350,
            placeholder="Paste text that might contain zero-width or homoglyph tricks...",
            key="text_steg_suspect",
            label_visibility="collapsed"
        )
        
        if st.button("Scan & Decode", use_container_width=True, key="text_steg_scan_btn"):
            if not suspect_text:
                st.warning("Paste some text to analyze.")
            else:
                detection_data = text_detect_all(suspect_text)
                _render_detection_details(detection_data)
                
                decoded = text_try_all_decoders(suspect_text)
                if decoded:
                    st.markdown("##### 📥 Payloads Recovered")
                    for decoder_name, payload in decoded.items():
                        st.markdown(f"- {decoder_name}")
                        st.code(payload, language="text")
                else:
                    st.info("No payloads recovered with the currently installed decoders.")
