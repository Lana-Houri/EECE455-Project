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
    """Display login/register page."""

    if 'auth_page_mode' not in st.session_state:
        st.session_state.auth_page_mode = 'login'

    # Inject CSS
    st.markdown("""
        <style>
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        .stApp { background-color: #0d1117 !important; }

        /* HEADER */
        .auth-logo {
            font-size: 1.4rem;
            font-weight: 700;
            color: #58a6ff;
            padding-top: 10px;
        }

        /* SMALLER TOP BUTTONS */
        .stButton > button[key="header_register_btn"],
        .stButton > button[key="header_login_btn"] {
            padding: 0.3rem 0.8rem !important;
            font-size: 0.85rem !important;
            min-height: 0px !important;
            border-radius: 5px !important;
            background: #1c2128 !important;
            border: 1px solid #30363d !important;
            color: white !important;
        }

        .stButton > button[key="header_register_btn"]:hover,
        .stButton > button[key="header_login_btn"]:hover {
            border-color: #58a6ff !important;
            color: #58a6ff !important;
        }

        .auth-main-content {
            display: flex;
            justify-content: center;
            padding-top: 40px;
        }

        .auth-form-wrapper {
            width: 100%;
            max-width: 430px;
            background: #1c2128;
            padding: 2.2rem;
            border-radius: 12px;
            border: 1px solid #30363d;
        }

        .auth-title {
            text-align: center;
            color: white;
            font-size: 2rem;
            margin-bottom: 1.5rem;
        }

        /* INPUTS */
        .stTextInput > div > div > input {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            color: white !important;
            border-radius: 6px !important;
            transition: border-color 0.2s ease !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #58a6ff !important;
            outline: none !important;
            box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2) !important;
        }

        /* BOTTOM BUTTONS — NOW BLUE */
        .stButton > button:not([key^="header"]) {
            width: 100%;
            background: #58a6ff !important;
            color: white !important;
            border-radius: 6px !important;
            padding: 0.7rem !important;
            font-size: 1rem !important;
            border: none !important;
        }

        .stButton > button:not([key^="header"]):hover {
            background: #4a9eff !important;
            box-shadow: 0 3px 10px rgba(88, 166, 255, 0.3);
        }
        
        /* Center the form submit button */
        form .stButton {
            display: flex;
            justify-content: center;
        }
        
        form .stButton > button {
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="auth-logo">🔐 StegAnalyzer</div>', unsafe_allow_html=True)
    with col2:
        if st.session_state.auth_page_mode == "login":
            if st.button("Register", key="header_register_btn"):
                st.session_state.auth_page_mode = 'register'
                st.rerun()
        else:
            if st.button("Login", key="header_login_btn"):
                st.session_state.auth_page_mode = 'login'
                st.rerun()

    st.markdown("---")

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if st.session_state.auth_page_mode == "register":
            st.markdown('<h1 class="auth-title">Create New Account</h1>', unsafe_allow_html=True)
            with st.form("register_form"):
                u = st.text_input("Username")
                e = st.text_input("Email (optional)")
                p = st.text_input("Password", type="password")
                c = st.text_input("Confirm Password", type="password")
                s = st.form_submit_button("Register")

                if s:
                    if p != c:
                        st.error("Passwords do not match")
                    else:
                        ok, msg = register_user(u, p, e)
                        st.success(msg) if ok else st.error(msg)

        else:
            st.markdown('<h1 class="auth-title">Login to StegAnalyzer</h1>', unsafe_allow_html=True)
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                s = st.form_submit_button("Login")

                if s:
                    ok, msg = authenticate_user(u, p)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.username = u
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

def require_auth(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper
