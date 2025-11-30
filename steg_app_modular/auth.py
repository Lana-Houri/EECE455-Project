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
        st.session_state.auth_notices.append((message, success))
        try:
            st.toast(message)
        except Exception:
            pass

    st.markdown("""
        <style>
        .auth-shell {
            max-width: 720px;
            margin: 0 auto;
            padding: 1.5rem 0 3rem;
        }
        .auth-hero {
            position: relative;
            padding: 2.25rem 2.5rem;
            border-radius: 18px;
            border: 1px solid rgba(88, 166, 255, 0.35);
            background: radial-gradient(circle at 20% 20%, rgba(88, 166, 255, 0.18), transparent 50%),
                        linear-gradient(135deg, rgba(88,166,255,0.06), rgba(63,185,80,0.05));
            box-shadow: var(--shadow-md);
            overflow: hidden;
            animation: floatIn 0.6s ease forwards;
        }
        .auth-hero .eyebrow {
            letter-spacing: 0.2em;
            text-transform: uppercase;
            font-size: 0.75rem;
            color: var(--text-tertiary);
            margin-bottom: 0.85rem;
        }
        .auth-hero h1 {
            font-size: 2.35rem;
            margin: 0;
            color: var(--text-primary);
            position: relative;
            z-index: 1;
        }
        .auth-hero p {
            color: var(--text-secondary);
            margin-top: 0.5rem;
            position: relative;
            z-index: 1;
        }
        .auth-intro {
            margin-top: 1.5rem;
        }
        .auth-tabs {
            margin-top: 1.5rem;
        }
        .auth-tabs [data-baseweb="tab-list"] {
            gap: 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .auth-tabs [data-baseweb="tab-list"] button {
            border-radius: 999px;
            border: 1px solid transparent;
            color: var(--text-tertiary);
            font-weight: 500;
            padding: 0.45rem 1.35rem;
            transition: all 0.2s ease;
        }
        .auth-tabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: var(--text-primary);
            border-color: rgba(88, 166, 255, 0.45);
            background: rgba(88, 166, 255, 0.12);
            box-shadow: 0 0 18px rgba(88, 166, 255, 0.15);
        }
        .auth-shell div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2.25rem;
            box-shadow: var(--shadow-lg);
            margin-top: 1.25rem;
            animation: fadeUp 0.35s ease forwards;
        }
        .auth-shell div[data-testid="stForm"] h3 {
            margin-bottom: 0.35rem;
        }
        .auth-shell div[data-testid="stForm"] p {
            color: var(--text-tertiary);
            margin-bottom: 1.5rem;
        }
        .help-text {
            color: var(--text-tertiary);
            margin-bottom: 1.5rem;
        }
        .auth-message {
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
            padding: 0.85rem 1rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            background: rgba(15, 23, 42, 0.75);
            margin-bottom: 1rem;
            animation: fadeUp 0.3s ease forwards;
        }
        .auth-message .status-dot {
            width: 0.65rem;
            height: 0.65rem;
            border-radius: 999px;
            margin-top: 0.2rem;
            flex-shrink: 0;
            background: var(--accent-info);
            box-shadow: 0 0 12px rgba(88, 166, 255, 0.45);
        }
        .auth-message.success {
            border-color: rgba(63, 185, 80, 0.4);
            background: rgba(63, 185, 80, 0.08);
        }
        .auth-message.success .status-dot {
            background: var(--accent-success);
            box-shadow: 0 0 12px rgba(63, 185, 80, 0.5);
        }
        .auth-message.error {
            border-color: rgba(248, 81, 73, 0.4);
            background: rgba(248, 81, 73, 0.08);
        }
        .auth-message.error .status-dot {
            background: var(--accent-error);
            box-shadow: 0 0 12px rgba(248, 81, 73, 0.5);
        }
        .auth-footer {
            text-align: center;
            margin-top: 2.5rem;
            color: var(--text-tertiary);
            font-size: 0.9rem;
        }
        @keyframes floatIn {
            from {opacity: 0; transform: translateY(-10px);}
            to {opacity: 1; transform: translateY(0);}
        }
        @keyframes fadeUp {
            from {opacity: 0; transform: translateY(12px);}
            to {opacity: 1; transform: translateY(0);}
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
    st.markdown("""
        <div class="auth-hero">
            <p class="eyebrow">Secure Access</p>
            <h1>StegAnalyzer</h1>
            <p>Advanced Steganography Detection & Analysis Platform</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="alert-box alert-info auth-intro">
            <span class="alert-icon">i</span>
            <div>
                <strong>Encrypted workspace:</strong> Sign in to orchestrate encoders, launch detectors, and continue your investigations.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-tabs">', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Register"])
    st.markdown('</div>', unsafe_allow_html=True)

    with tab1:
        if st.session_state.auth_notices:
            for msg, success in st.session_state.auth_notices[-1:]:
                msg_class = "success" if success else "error"
                st.markdown(f"""
                    <div class="auth-message {msg_class}">
                        <span class="status-dot"></span>
                        <div>{msg}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.session_state.auth_notices = st.session_state.auth_notices[-3:]

        with st.form("login_form", clear_on_submit=False):
            st.markdown("#### Welcome Back")
            st.markdown('<p class="help-text">Sign in to access your personalized steganography lab.</p>', unsafe_allow_html=True)
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )

            submit_login = st.form_submit_button(
                "Login",
                use_container_width=True,
                type="primary"
            )

            if submit_login:
                if not username or not password:
                    _notify("Please fill in all fields.", success=False)
                else:
                    ok, msg = authenticate_user(username, password)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        _notify(f"Welcome back, {username}.", success=True)
                        st.rerun()
                    else:
                        _notify(msg, success=False)

    with tab2:
        if st.session_state.auth_notices:
            for msg, success in st.session_state.auth_notices[-1:]:
                msg_class = "success" if success else "error"
                st.markdown(f"""
                    <div class="auth-message {msg_class}">
                        <span class="status-dot"></span>
                        <div>{msg}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.session_state.auth_notices = st.session_state.auth_notices[-3:]

        with st.form("register_form", clear_on_submit=False):
            st.markdown("#### Create Account")
            st.markdown('<p class="help-text">Provision secure credentials and start encoding in minutes.</p>', unsafe_allow_html=True)
            reg_username = st.text_input(
                "Username",
                placeholder="3+ characters, letters and numbers only",
                key="reg_username"
            )
            reg_email = st.text_input(
                "Email (optional)",
                placeholder="your.email@example.com",
                key="reg_email"
            )
            reg_password = st.text_input(
                "Password",
                type="password",
                placeholder="6+ characters",
                key="reg_password"
            )
            reg_confirm = st.text_input(
                "Confirm password",
                type="password",
                placeholder="Re-enter your password",
                key="reg_confirm"
            )

            submit_register = st.form_submit_button(
                "Create Account",
                use_container_width=True,
                type="primary"
            )

            if submit_register:
                if not reg_username or not reg_password or not reg_confirm:
                    _notify("Please fill in all required fields.", success=False)
                elif reg_password != reg_confirm:
                    _notify("Passwords do not match.", success=False)
                else:
                    ok, msg = register_user(reg_username, reg_password, reg_email)
                    if ok:
                        _notify("Registration successful. Please log in.", success=True)
                        st.session_state.auth_page_mode = 'login'
                        st.rerun()
                    else:
                        _notify(msg, success=False)

    st.markdown("""
        <div class="auth-footer">
            <p>Universal Steg Analyzer v4.0</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def require_auth(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper
