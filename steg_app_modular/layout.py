from pathlib import Path
import streamlit as st


THEME_CSS_PATH = Path(__file__).with_name("theme.css")


def apply_page_theme():
    """Configure base page settings and inject the shared CSS theme."""
    st.set_page_config(
        page_title="Universal Steg Analyzer",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.markdown("""
        <style>
        .stApp {
            background-color: #0d1117 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if THEME_CSS_PATH.exists():
        css = THEME_CSS_PATH.read_text()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_sidebar(username: str, logout_callback):
    """Render the navigation sidebar and handle page switching."""
    with st.sidebar:
        if 'text_image_tab' not in st.session_state:
            st.session_state.text_image_tab = 'Text/Image'
        
        st.markdown("""
            <div class="sidebar-logo">
                <div class="sidebar-logo-icon">&#x1F512;</div>
                <div class="sidebar-logo-text">StegAnalyzer</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"**👤 Logged in as:** `{username}`")
        st.markdown("---")
        
        st.markdown("### Navigation")
        if st.button(f"Text in Image ({st.session_state.text_image_tab})", key="nav_text_image", use_container_width=True):
            st.session_state.current_page = 'Text in Image'
            st.rerun()
        if st.button("Text Steg (Text/Text)", key="nav_textsteg", use_container_width=True):
            st.session_state.current_page = 'Text Steg'
            st.rerun()
        if st.button("Image in Image", key="nav_imageinimage", use_container_width=True):
            st.session_state.current_page = 'Image in Image'
            st.rerun()
        
        st.markdown("### ℹ️ Info")
        if st.button("About", key="nav_About", use_container_width=True):
            st.session_state.current_page = 'About'
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🛠️ Detection Methods")
        st.markdown("**Extraction Tools:**")
        st.markdown('<span class="status-dot"></span> Zsteg (PNG)', unsafe_allow_html=True)
        st.markdown('<span class="status-dot"></span> Steghide (JPEG)', unsafe_allow_html=True)
        st.markdown('<span class="status-dot"></span> OutGuess', unsafe_allow_html=True)
        st.markdown('<span class="status-dot"></span> OpenStego', unsafe_allow_html=True)
        
        st.markdown("**Statistical Analysis:**")
        st.markdown('<span class="status-dot"></span> StegExpose', unsafe_allow_html=True)
        st.markdown('<span class="status-dot"></span> Chi-Square', unsafe_allow_html=True)
        st.markdown('<span class="status-dot"></span> DCT Analysis', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💬 AI Assistant")
        if st.button("Chat", key="nav_Chat", use_container_width=True):
            st.session_state.current_page = 'Chat'
            st.rerun()
        
        st.markdown("---")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
            logout_callback()


def render_header():
    """Display the animated header banner."""
    st.markdown("""
        <div class="app-header">
            <div class="header-content">
                <h1 class="header-title">Universal Steg Analyzer</h1>
                <p class="header-subtitle">Advanced Multi-Tool Steganography Detection & Analysis Platform</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
