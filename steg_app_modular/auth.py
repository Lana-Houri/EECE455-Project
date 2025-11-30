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
    if 'auth_notices' not in st.session_state:
        st.session_state.auth_notices = []

    def _notify(message: str, success: bool = True):
        icon = "✅" if success else "⚠️"
        st.session_state.auth_notices.append((message, success, icon))
        try:
            st.toast(message, icon=icon)
        except Exception:
            pass

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🔐 StegAnalyzer")
    with col2:
        if st.session_state.auth_page_mode == "login":
            if st.button("Register", key="header_register_btn"):
                st.session_state.auth_page_mode = 'register'
                st.rerun()
        else:
            if st.button("Login", key="header_login_btn"):
                st.session_state.auth_page_mode = 'login'
                st.rerun()

    if st.session_state.auth_notices:
        for msg, success, icon in st.session_state.auth_notices[-3:]:
            tone = "auth-toast-success" if success else "auth-toast-error"
            st.markdown(f"""
                <div class="card" style="background: rgba(15,23,42,0.6); border-left: 4px solid {'#10b981' if success else '#f97316'}; margin-top: 0.5rem;">
                    <strong>{icon} {msg}</strong>
                </div>
            """, unsafe_allow_html=True)
        st.session_state.auth_notices.clear()

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="card" style="padding:2rem;">', unsafe_allow_html=True)
        if st.session_state.auth_page_mode == "register":
            st.markdown("#### Create New Account")
            with st.form("register_form"):
                u = st.text_input("Username")
                e = st.text_input("Email (optional)")
                p = st.text_input("Password", type="password")
                c = st.text_input("Confirm Password", type="password")
                s = st.form_submit_button("Register")

                if s:
                    if p != c:
                        st.error("Passwords do not match")
                        _notify("Passwords do not match", success=False)
                    else:
                        ok, msg = register_user(u, p, e)
                        if ok:
                            st.success(msg)
                            _notify("Registration successful! Welcome aboard.", success=True)
                        else:
                            st.error(msg)
                            _notify(msg, success=False)

        else:
            st.markdown("#### Login to StegAnalyzer")
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
                        _notify(f"Welcome back, {u}!", success=True)
                        st.rerun()
                    else:
                        st.error(msg)
                        _notify(msg, success=False)
        st.markdown('</div>', unsafe_allow_html=True)

def require_auth(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper
