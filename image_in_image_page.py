import os
import tempfile
import streamlit as st
from PIL import Image

from image_in_image_tools import encode_image_in_image, decode_image_from_image


def render_image_in_image_page():
    """Render the Image-in-Image steganography page with encode and decode functionality."""
    st.markdown('<h2 class="section-header">🧩 Image-in-Image Steganography Lab</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>LSB Steganography:</strong> Hide one image inside another using Least Significant Bit (LSB) technique.
                The cover image will look identical to the original, but contains a hidden secret image that can be extracted.
                Works best with PNG images (lossless compression).
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Tab selection for Encode/Decode
    tab_encode, tab_decode = st.tabs(["🔒 Encode Image", "🔓 Decode Image"])
    
    # ============================================
    # ENCODE TAB
    # ============================================
    with tab_encode:
        st.markdown("### Embed Secret Image into Cover Image")
        st.markdown("""
            <div class="card">
                <p><strong>How it works:</strong> The secret image's pixels are embedded into the least significant bits 
                of the cover image's pixels. The more LSBs you use, the better quality the extracted image, but the more 
                visible the changes to the cover image.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 📷 Cover Image")
            cover_image = st.file_uploader(
                "Upload cover image", 
                type=["png", "jpg", "jpeg", "bmp"], 
                key="i2i_cover"
            )
            if cover_image:
                try:
                    cover_img = Image.open(cover_image)
                    st.image(cover_img, caption=f"Cover: {cover_img.size[0]}x{cover_img.size[1]}", use_container_width=True)
                    st.markdown(f"**Format:** {cover_img.format}<br>**Mode:** {cover_img.mode}", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading cover image: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 🔐 Secret Image")
            secret_image = st.file_uploader(
                "Upload secret image to hide", 
                type=["png", "jpg", "jpeg", "bmp"], 
                key="i2i_secret"
            )
            if secret_image:
                try:
                    secret_img = Image.open(secret_image)
                    st.image(secret_img, caption=f"Secret: {secret_img.size[0]}x{secret_img.size[1]}", use_container_width=True)
                    st.markdown(f"**Format:** {secret_img.format}<br>**Mode:** {secret_img.mode}", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading secret image: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Encoding Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            bits_per_channel = st.selectbox(
                "LSBs per channel",
                [1, 2, 3, 4],
                index=0,
                help="Number of least significant bits to use per color channel. 1 = best invisibility, 4 = best quality but more visible",
                key="i2i_bits"
            )
        
        with col2:
            encode_password = st.text_input(
                "Password (optional - for future encryption)",
                type="password",
                key="i2i_encode_password",
                help="Password encryption not yet implemented"
            )
        
        # Calculate capacity if both images are uploaded
        if cover_image and secret_image:
            try:
                cover_img = Image.open(cover_image)
                secret_img = Image.open(secret_image)
                cover_size = cover_img.size[0] * cover_img.size[1]
                secret_size = secret_img.size[0] * secret_img.size[1]
                
                # Calculate capacity
                capacity_pixels = (cover_size * 3 * bits_per_channel) // 24
                fits = secret_size <= capacity_pixels
                
                st.markdown("**📊 Capacity Analysis:**")
                if fits:
                    st.success(f"✓ Secret image will fit! Capacity: {capacity_pixels:,} pixels, Secret: {secret_size:,} pixels")
                else:
                    st.warning(f"⚠ Secret image too large! Capacity: {capacity_pixels:,} pixels, Secret: {secret_size:,} pixels. It will be automatically resized.")
            except:
                pass
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if cover_image and secret_image:
            if st.button("🔒 Embed Secret Image", use_container_width=True, key="i2i_encode_btn"):
                with st.spinner("Embedding secret image into cover image..."):
                    # Save uploaded files temporarily
                    temp_cover = os.path.join(tempfile.gettempdir(), f"i2i_cover_{cover_image.name}")
                    temp_secret = os.path.join(tempfile.gettempdir(), f"i2i_secret_{secret_image.name}")
                    
                    with open(temp_cover, "wb") as f:
                        f.write(cover_image.getbuffer())
                    with open(temp_secret, "wb") as f:
                        f.write(secret_image.getbuffer())
                    
                    # Encode
                    result = encode_image_in_image(temp_cover, temp_secret, encode_password, bits_per_channel)
                    
                    # Cleanup temp files
                    try:
                        os.remove(temp_cover)
                        os.remove(temp_secret)
                    except:
                        pass
                    
                    if result['success']:
                        st.markdown("""
                            <div class="alert-box alert-weak">
                                <span class="alert-icon">✓</span>
                                <div><strong>Success:</strong> {}</div>
                            </div>
                        """.format(result.get('message', 'Image embedded successfully.')), unsafe_allow_html=True)
                        
                        # Display stego image
                        stego_img = Image.open(result['output_path'])
                        st.markdown("#### 🖼️ Steganographic Image")
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.image(stego_img, caption="Stego Image", use_container_width=True)
                        with col2:
                            # Compare with original (reset file pointer)
                            cover_image.seek(0)
                            original_img = Image.open(cover_image)
                            st.image(original_img, caption="Original Cover", use_container_width=True)
                        
                        # Download button
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
    
    # ============================================
    # DECODE TAB
    # ============================================
    with tab_decode:
        st.markdown("### Extract Hidden Image from Stego Image")
        st.markdown("""
            <div class="card">
                <p><strong>How it works:</strong> Extract the hidden image by reading the least significant bits 
                from the stego image. Make sure to use the same number of LSBs that were used during encoding.</p>
            </div>
        """, unsafe_allow_html=True)
        
        stego_file = st.file_uploader(
            "Upload stego image to extract from",
            type=["png", "jpg", "jpeg", "bmp"],
            key="i2i_stego"
        )
        
        if stego_file:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### 📷 Stego Image Preview")
                try:
                    stego_img = Image.open(stego_file)
                    st.image(stego_img, caption=f"Stego: {stego_img.size[0]}x{stego_img.size[1]}", use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading stego image: {e}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### ⚙️ Decoding Settings")
                
                decode_bits = st.selectbox(
                    "LSBs per channel",
                    [1, 2, 3, 4],
                    index=0,
                    help="Number of least significant bits used during encoding",
                    key="i2i_decode_bits"
                )
                
                decode_password = st.text_input(
                    "Password (if used during encoding)",
                    type="password",
                    key="i2i_decode_password",
                    help="Password decryption not yet implemented"
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("🔓 Extract Hidden Image", use_container_width=True, key="i2i_decode_btn"):
                with st.spinner("Extracting hidden image..."):
                    # Save uploaded file temporarily
                    temp_stego = os.path.join(tempfile.gettempdir(), f"i2i_stego_{stego_file.name}")
                    
                    with open(temp_stego, "wb") as f:
                        f.write(stego_file.getbuffer())
                    
                    # Decode
                    result = decode_image_from_image(temp_stego, decode_password, decode_bits)
                    
                    # Cleanup temp file
                    try:
                        os.remove(temp_stego)
                    except:
                        pass
                    
                    if result['success']:
                        st.markdown("""
                            <div class="alert-box alert-weak">
                                <span class="alert-icon">✓</span>
                                <div><strong>Success:</strong> {}</div>
                            </div>
                        """.format(result.get('message', 'Image extracted successfully.')), unsafe_allow_html=True)
                        
                        # Display extracted image
                        extracted_img = Image.open(result['output_path'])
                        st.markdown("#### 🔐 Extracted Secret Image")
                        st.image(extracted_img, caption=f"Extracted: {extracted_img.size[0]}x{extracted_img.size[1]}", use_container_width=True)
                        
                        # Download button
                        with open(result['output_path'], 'rb') as f:
                            st.download_button(
                                "📥 Download Extracted Image",
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
                        
                        st.info("💡 **Tip:** Try adjusting the 'LSBs per channel' value. Common values are 1 or 2.")

