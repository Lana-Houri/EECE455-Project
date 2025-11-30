import os
import tempfile
import streamlit as st

from encode_tools import encode_openstego, encode_steghide


def render_encode_page():
    st.markdown('<h2 class="section-header">🔒 Steganography Encoding</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>Encoding Mode:</strong> Hide secret data within an image using steganography.
                The output image will look identical to the original but contain hidden data.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📷 Upload Cover Image")
        cover_image = st.file_uploader("Cover image", type=["png", "jpg", "jpeg"], key="encode_cover")
    
    with col2:
        st.markdown("#### 📝 Secret Data")
        secret_data = st.text_area("Enter secret message", height=150, placeholder="Type your secret message here...")
    
    st.markdown("#### ⚙️ Encoding Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        encoding_method = st.selectbox("Encoding method", ["Steghide", "OpenStego"])
    with col2:
        encode_password = st.text_input("Password (optional)", type="password", key="encode_password")
    
    if not (cover_image and secret_data):
        return
    
    if not st.button("🔒 Embed Data", use_container_width=True):
        return
    
    with st.spinner("Embedding data..."):
        temp_cover = os.path.join(tempfile.gettempdir(), cover_image.name)
        with open(temp_cover, "wb") as f:
            f.write(cover_image.getbuffer())
        
        if encoding_method == "Steghide":
            result = encode_steghide(temp_cover, secret_data, encode_password)
        else:
            result = encode_openstego(temp_cover, secret_data, encode_password)
        
        if result['success']:
            st.markdown("""
                <div class="alert-box alert-weak">
                    <span class="alert-icon">✓</span>
                    <div><strong>Success:</strong> Data embedded successfully.</div>
                </div>
            """, unsafe_allow_html=True)
            
            with open(result['output_path'], 'rb') as f:
                st.download_button(
                    "📥 Download Steganographic Image",
                    f,
                    file_name=os.path.basename(result['output_path']),
                    mime="image/png",
                    use_container_width=True
                )
        else:
            st.markdown(f"""
                <div class="alert-box alert-strong">
                    <span class="alert-icon">✗</span>
                    <div><strong>Error:</strong> {result.get('error', 'Unknown error')}</div>
                </div>
            """, unsafe_allow_html=True)
