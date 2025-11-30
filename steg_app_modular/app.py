import streamlit as st
import importlib
try:
    import importlib.metadata as _stdlib_metadata
    if not hasattr(_stdlib_metadata, "packages_distributions"):
        try:
            import importlib_metadata as _backport_metadata  # type: ignore
            _stdlib_metadata.packages_distributions = _backport_metadata.packages_distributions  # type: ignore
        except Exception:
            def _dummy_packages_distributions():  # type: ignore
                return {}
            _stdlib_metadata.packages_distributions = _dummy_packages_distributions  # type: ignore
except ImportError:
    pass

# =====================================
# Gemini API Configuration
# =====================================
# TODO: Replace "YOUR_GEMINI_API_KEY_HERE" below with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyA_bZnlL9RYCd37WatQAuRru-XFwBVjSu8"

# =====================================
# Imports from modules
# =====================================
from auth import (
    is_authenticated,
    get_current_username,
    show_login_page,
    logout,
)
from layout import apply_page_theme, render_sidebar, render_header
from analyze_page import render_analyze_page
from decode_page import render_decode_page
from encode_page import render_encode_page
from text_page import render_text_page
from automation_page import render_automation_page
from image_in_image_page import render_image_in_image_page

# =====================================
# Page Theme
# =====================================
apply_page_theme()

# =====================================
# Authentication Check
# =====================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# Check authentication - show login page if not authenticated
if not is_authenticated():
    show_login_page()
    st.stop()  # Stop execution here if not authenticated

# =====================================
# Session State Management
# =====================================
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Analyze'
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# =====================================
# Gemini Chatbot Helper Function
# =====================================
def send_to_gemini(message: str, api_key: str = None):
    """Send message to Gemini API for cryptography help."""
    # Use hardcoded API key if not provided
    if api_key is None:
        api_key = GEMINI_API_KEY
    
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        return "Error: Gemini API key not configured. Please set GEMINI_API_KEY in the code or as an environment variable."
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        
        # Try to list available models first, then use a compatible one
        model = None
        last_error = None
        
        try:
            # First, try to list available models to see what's actually available
            available_models = genai.list_models()
            model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            
            # Prefer free models: flash is faster and free
            preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            
            for preferred in preferred_models:
                for full_model_name in model_names:
                    # Extract just the model name (e.g., "models/gemini-1.5-flash" -> "gemini-1.5-flash")
                    model_name = full_model_name.split('/')[-1] if '/' in full_model_name else full_model_name
                    if preferred in model_name.lower():
                        try:
                            model = genai.GenerativeModel(model_name)
                            break
                        except:
                            continue
                if model:
                    break
        except Exception as e:
            # If listing models fails, try common model names directly
            last_error = e
            pass
        
        # If no model found from listing, try direct model names
        if model is None:
            model_names_to_try = [
                'gemini-2.5-flash',
                'gemini-2.5-pro'
            ]
            
            for model_name in model_names_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except Exception as e2:
                    last_error = e2
                    continue
        
        if model is None:
            return f"Error: Could not connect to any Gemini model. Please verify your API key is correct and you have access to Gemini models. Error: {str(last_error)}"
        
        system_prompt = """You are a helpful assistant specializing in steganography and cryptography concepts. 
        You help users understand:
        - Steganography techniques (LSB, DCT, spread spectrum, etc.)
        - Cryptographic algorithms used in this tool
        - How different detection methods work
        - Interpreting analysis results
        
        Keep responses concise, technical, and educational. Focus on explaining concepts related to the Universal Steg Analyzer tool."""
        
        full_prompt = f"{system_prompt}\n\nUser question: {message}"
        
        response = model.generate_content(full_prompt)
        return response.text
    except ImportError:
        return "Gemini library not installed. Run: pip install google-generativeai --break-system-packages"
    except Exception as e:
        return f"Error connecting to Gemini: {str(e)}"

username = get_current_username()
render_sidebar(username, logout)
render_header()

# =====================================
# Page Router
# =====================================
current_page = st.session_state.current_page

# =====================================
# PAGE ROUTER
# =====================================
if current_page == 'Automation':
    render_automation_page()
elif current_page == 'Analyze':
    render_analyze_page()
elif current_page == 'Decode':
    render_decode_page()
elif current_page == 'Encode':
    render_encode_page()
elif current_page == 'Text in Image':
    st.markdown('<h2 class="section-header">🖼️ Text in Image Workflow</h2>', unsafe_allow_html=True)
    st.markdown("""
        <div class="card">
            <p>Select the module you wish to access.</p>
        </div>
    """, unsafe_allow_html=True)
    for label, target in [
        ("⚙️ Automated Pipeline", "Automation"),
        ("🔬 Analyze", "Analyze"),
        ("🔓 Decode", "Decode"),
        ("🔒 Encode", "Encode"),
    ]:
        if st.button(label, use_container_width=True, key=f"text_image_option_{target}"):
            st.session_state.text_image_tab = target
            st.session_state.current_page = target
            st.rerun()
elif current_page == 'Text Steg':
    render_text_page()
elif current_page == 'Image in Image':
    render_image_in_image_page()

# =====================================
# CHAT PAGE
# =====================================
elif current_page == 'Chat':
    st.markdown('<h2 class="section-header">💬 AI Cryptography Assistant</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>AI Assistant:</strong> Ask me about steganography techniques, cryptographic concepts, or how to interpret analysis results.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🤖 Chat with AI Assistant")
    
    # Display chat messages
    if st.session_state.chat_messages:
        st.markdown("---")
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.chat_messages):
                if msg['role'] == 'user':
                    st.markdown(f'<div class="chat-message user"><div class="chat-bubble user">{msg["content"]}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message"><div class="chat-bubble assistant">{msg["content"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
            <p>Start a conversation by asking a question below!</p>
            <p style="margin-top: 1rem; font-size: 0.9rem;">Example: "What is LSB steganography?"</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    user_message = st.text_input("Ask a question...", key="chat_input", placeholder="e.g., What is LSB steganography? How does zsteg work?")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Send", key="send_chat", use_container_width=True):
            if user_message:
                st.session_state.chat_messages.append({"role": "user", "content": user_message})
                response = send_to_gemini(user_message)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()
    with col2:
        if st.button("Clear", key="clear_chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Example questions
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💡 Example Questions")
    st.markdown("""
    - **"What is LSB steganography?"**
    - **"How does zsteg detect hidden data?"**
    - **"What are B1, B2, B3, B4 channels?"**
    - **"Explain DCT-based steganography"**
    - **"What's the difference between Steghide and OpenStego?"**
    - **"How do I interpret strong vs weak signals?"**
    - **"What is Chi-Square attack in steganalysis?"**
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# ABOUT PAGE
# =====================================
elif current_page == 'About':
    st.markdown('<h2 class="section-header">ℹ️ About This Tool</h2>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Purpose")
    st.markdown("Universal Steg Analyzer is a comprehensive steganography detection and analysis platform that combines multiple detection methods, statistical analysis, and deep learning to identify hidden data in images.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔍 Extraction Tools")
        st.markdown("Tools that detect and extract hidden data:")
        st.markdown("""
        - **Zsteg** - PNG LSB analysis with B1-B4 detection
        - **Steghide** - JPG/BMP extraction
        - **OutGuess** - Statistical steganography
        - **OpenStego** - LSB embedding detection
        - **Jsteg** - JPEG steganography
        - **F5** - Advanced JPEG detection
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Statistical Analysis")
        st.markdown("Advanced detection methods:")
        st.markdown("""
        - **StegExpose** - LSB fusion detection
        - **Chi-Square Attack** - PoV statistical analysis
        - **DCT Analysis** - JPEG coefficient inspection
        - **Deep Learning** - CNN-based detection
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🆕 New Features (v4.0)")
    st.markdown("""
    - ✓ **Deep Learning Detection** - SRNet CNN for JPEG steganography
    - ✓ **Chi-Square Attack** - Statistical LSB detection
    - ✓ **DCT Coefficient Analysis** - Detects F5 shrinkage patterns
    - ✓ **Format-Aware Analysis** - Different methods for JPEG vs PNG
    - ✓ **Comprehensive Results** - Detailed per-method breakdown
    - ✓ Enhanced UI with method selection options
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📋 Detection Method Details")
    
    st.markdown("**Chi-Square Attack:**")
    st.markdown("Analyzes pairs of pixel values (2i, 2i+1). Natural images have unequal pair counts; LSB embedding equalizes them.")
    
    st.markdown("**DCT Analysis:**")
    st.markdown("Examines JPEG DCT coefficients. F5 steganography causes 'shrinkage' (more zeros).")
    
    st.markdown("**Deep Learning (SRNet):**")
    st.markdown("12-layer residual CNN that learns steganographic artifacts. Best for J-UNIWARD, nsF5, UERD.")
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# Footer
# =====================================
st.markdown("""
    <div class="custom-footer">
        <p>Universal Steg Analyzer v4.0 | Enhanced with Deep Learning</p>
        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Advanced Steganography Detection & Analysis Platform</p>
    </div>
""", unsafe_allow_html=True)
