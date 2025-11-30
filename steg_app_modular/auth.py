"""
Authentication Module for Streamlit Steganography App
=====================================================
Handles user registration, login, and session management.
"""

import streamlit as st
import hashlib
import json
import os
from datetime import datetime

# User database file
USER_DB_FILE = "users.json"

def init_user_database():
    """Initialize user database file if it doesn't exist."""
    if not os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'w') as f:
            json.dump({}, f)

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> dict:
    """Load users from database file."""
    init_user_database()
    try:
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users: dict):
    """Save users to database file."""
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def register_user(username: str, password: str, email: str = ""):
    """Register a new user."""
    users = load_users()

    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if not username.isalnum():
        return False, "Username can only contain letters and numbers"

    if username in users:
        return False, "Username already exists"

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long"

    users[username] = {
        "password_hash": hash_password(password),
        "email": email,
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }

    save_users(users)
    return True, "Registration successful! You can now login."

def authenticate_user(username: str, password: str):
    """Authenticate a user."""
    users = load_users()

    if username not in users:
        return False, "Invalid username or password"

    user = users[username]
    password_hash = hash_password(password)

    if user["password_hash"] != password_hash:
        return False, "Invalid username or password"

    user["last_login"] = datetime.now().isoformat()
    save_users(users)

    return True, "Login successful!"

def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)

def get_current_username() -> str:
    return st.session_state.get("username", "")

def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

def show_login_page():
    """Display login/register page with improved UI."""

    if 'auth_page_mode' not in st.session_state:
        st.session_state.auth_page_mode = 'login'
    if 'auth_notices' not in st.session_state:
        st.session_state.auth_notices = []

    def _notify(message: str, success: bool = True):
        icon = "✓" if success else "✗"
        st.session_state.auth_notices.append((message, success, icon))
        try:
            st.toast(message, icon=icon)
        except Exception:
            pass

    # Custom CSS for auth page
    st.markdown("""
        <style>
        .auth-container {
            max-width: 450px;
            margin: 2rem auto;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .auth-header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #58a6ff 0%, #3fb950 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .auth-form-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2.5rem;
            box-shadow: var(--shadow-lg);
        }
        .auth-message {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid;
            animation: slideIn 0.3s ease-out;
        }
        .auth-message.success {
            background: rgba(63, 185, 80, 0.1);
            border-left-color: var(--accent-success);
            color: var(--accent-success);
        }
        .auth-message.error {
            background: rgba(248, 81, 73, 0.1);
            border-left-color: var(--accent-error);
            color: var(--accent-error);
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .auth-footer {
            text-align: center;
            margin-top: 2rem;
            color: var(--text-tertiary);
            font-size: 0.85rem;
        }
        /* Hide empty Streamlit containers */
        .element-container:empty,
        div[data-testid="stVerticalBlock"]:empty {
            display: none !important;
        }
        /* Ensure auth message only shows when content exists */
        .auth-message:empty {
            display: none !important;
        }
        /* Remove empty tab container spacing */
        section[data-testid="stTabs"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        section[data-testid="stTabs"] > div {
            margin: 0 !important;
            padding: 0 !important;
        }
        /* Remove padding from tab panels */
        div[role="tabpanel"] {
            padding-top: 1rem !important;
        }
        /* Hide empty column containers */
        div[data-testid="column"] {
            padding: 0 !important;
        }
        /* Remove gap between header and tabs */
        .auth-header {
            margin-bottom: 1.5rem !important;
        }
        /* COMPLETELY REMOVE ALL RED BORDERS - Only blue border */
        .stTextInput,
        .stPasswordInput,
        .stTextInput > div,
        .stPasswordInput > div,
        .stTextInput > div > div,
        .stPasswordInput > div > div,
        .stTextInput > div > div > div,
        .stPasswordInput > div > div > div {
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }
        /* Remove red borders from all nested elements */
        .stTextInput *,
        .stPasswordInput * {
            border-color: transparent !important;
            box-shadow: none !important;
        }
        /* Input field - only blue border - same size for both */
        .stTextInput > div > div > input,
        .stPasswordInput > div > div > input {
            border: 1px solid rgba(88, 166, 255, 0.35) !important;
            outline: none !important;
            box-shadow: none !important;
            width: 100% !important;
            height: 2.5rem !important;
            padding: 0.5rem 0.75rem !important;
            box-sizing: border-box !important;
        }
        /* Ensure containers have same width and layout */
        .stTextInput,
        .stPasswordInput {
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }
        .stTextInput > div,
        .stPasswordInput > div {
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }
        .stTextInput > div > div,
        .stPasswordInput > div > div {
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            display: flex !important;
            align-items: center !important;
        }
        /* Make password input wrapper match username width */
        .stPasswordInput > div > div {
            position: relative !important;
        }
        /* Force both inputs to exact same container width */
        .stTextInput > div > div,
        .stPasswordInput > div > div {
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }
        /* Adjust password input to account for eye icon */
        .stPasswordInput > div > div > input {
            padding-right: 2.5rem !important;
            flex: 1 !important;
        }
        /* Make username input match the same visual width */
        .stTextInput > div > div > input {
            padding-right: 0.75rem !important;
            flex: 1 !important;
        }
        /* Ensure both form elements take same space */
        form .stTextInput,
        form .stPasswordInput {
            flex: 1 1 auto !important;
            width: 100% !important;
        }
        /* Input field on focus - single blue border only */
        .stTextInput > div > div > input:focus,
        .stTextInput > div > div > input:focus-visible,
        .stPasswordInput > div > div > input:focus,
        .stPasswordInput > div > div > input:focus-visible {
            border: 2px solid #58a6ff !important;
            outline: none !important;
            box-shadow: none !important;
        }
        /* Remove any red error states */
        .stTextInput > div > div > input:invalid,
        .stPasswordInput > div > div > input:invalid {
            border-color: #58a6ff !important;
            outline: none !important;
            box-shadow: none !important;
        }
        /* Remove borders from button/icon containers */
        .stTextInput button,
        .stPasswordInput button,
        .stTextInput [data-baseweb="button"],
        .stPasswordInput [data-baseweb="button"] {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Centered container
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    
    with col_center:
        # Header
        st.markdown("""
            <div class="auth-header">
                <h1>🔐 StegAnalyzer</h1>
                <p style="color: var(--text-tertiary); margin-top: 0.5rem;">
                    Advanced Steganography Detection & Analysis Platform
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Tabs
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

        # Login Tab
        with tab1:
            # Display notifications
            if st.session_state.auth_notices:
                for msg, success, icon in st.session_state.auth_notices[-1:]:  # Show only latest
                    msg_class = "success" if success else "error"
                    st.markdown(f"""
                        <div class="auth-message {msg_class}">
                            <strong>{icon}</strong> {msg}
                        </div>
                    """, unsafe_allow_html=True)
                # Keep only the latest 3 notifications
                st.session_state.auth_notices = st.session_state.auth_notices[-3:]
            
            st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
            st.markdown("### Welcome Back")
            st.markdown('<p style="color: var(--text-tertiary); margin-bottom: 1.5rem;">Sign in to access the steganography lab</p>', unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "👤 Username",
                    placeholder="Enter your username",
                    key="login_username"
                )
                password = st.text_input(
                    "🔒 Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )
                
                submit_login = st.form_submit_button(
                    "🚀 Login",
                    use_container_width=True,
                    type="primary"
                )

                if submit_login:
                    if not username or not password:
                        _notify("Please fill in all fields", success=False)
                    else:
                        ok, msg = authenticate_user(username, password)
                        if ok:
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            _notify(f"Welcome back, {username}!", success=True)
                            st.rerun()
                        else:
                            _notify(msg, success=False)
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Register Tab
        with tab2:
            # Display notifications
            if st.session_state.auth_notices:
                for msg, success, icon in st.session_state.auth_notices[-1:]:  # Show only latest
                    msg_class = "success" if success else "error"
                    st.markdown(f"""
                        <div class="auth-message {msg_class}">
                            <strong>{icon}</strong> {msg}
                        </div>
                    """, unsafe_allow_html=True)
                # Keep only the latest 3 notifications
                st.session_state.auth_notices = st.session_state.auth_notices[-3:]
            
            st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
            st.markdown("### Create Account")
            st.markdown('<p style="color: var(--text-tertiary); margin-bottom: 1.5rem;">Join StegAnalyzer and start analyzing</p>', unsafe_allow_html=True)
            
            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input(
                    "👤 Username",
                    placeholder="3+ characters, letters and numbers only",
                    key="reg_username"
                )
                reg_email = st.text_input(
                    "📧 Email (Optional)",
                    placeholder="your.email@example.com",
                    key="reg_email"
                )
                reg_password = st.text_input(
                    "🔒 Password",
                    type="password",
                    placeholder="6+ characters",
                    key="reg_password"
                )
                reg_confirm = st.text_input(
                    "🔒 Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_confirm"
                )
                
                submit_register = st.form_submit_button(
                    "✨ Create Account",
                    use_container_width=True,
                    type="primary"
                )

                if submit_register:
                    if not reg_username or not reg_password or not reg_confirm:
                        _notify("Please fill in all required fields", success=False)
                    elif reg_password != reg_confirm:
                        _notify("Passwords do not match", success=False)
                    else:
                        ok, msg = register_user(reg_username, reg_password, reg_email)
                        if ok:
                            _notify("Registration successful! Please login.", success=True)
                            # Switch to login tab after successful registration
                            st.session_state.auth_page_mode = 'login'
                            st.rerun()
                        else:
                            _notify(msg, success=False)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
            <div class="auth-footer">
                <p>Universal Steg Analyzer v4.0</p>
            </div>
        """, unsafe_allow_html=True)

def require_auth(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper
