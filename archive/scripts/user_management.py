# Advanced user management for deer hunting app
import streamlit as st
import json
import hashlib
from datetime import datetime, timedelta

class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.load_users()
    
    def load_users(self):
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        except FileNotFoundError:
            # Default admin user
            self.users = {
                "admin": {
                    "password_hash": self.hash_password("DeerHunter2025!"),
                    "email": "your-email@domain.com",
                    "created": datetime.now().isoformat(),
                    "last_login": None,
                    "role": "admin"
                }
            }
            self.save_users()
    
    def save_users(self):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def hash_password(self, password):
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), b'deer_hunting_salt', 100000).hex()
    
    def verify_password(self, username, password):
        """Verify user credentials"""
        if username in self.users:
            return self.users[username]["password_hash"] == self.hash_password(password)
        return False
    
    def login_user(self, username):
        """Update last login time"""
        if username in self.users:
            self.users[username]["last_login"] = datetime.now().isoformat()
            self.save_users()

def login_form():
    """Display login form"""
    st.markdown("# 🦌 Professional Deer Hunting Intelligence")
    st.markdown("### Secure Access Portal")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Access Hunting App")
        
        if submit:
            user_manager = UserManager()
            if user_manager.verify_password(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                user_manager.login_user(username)
                st.success("🎯 Access granted! Loading hunting intelligence...")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Access denied.")

def check_authentication():
    """Check if user is authenticated"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        login_form()
        return False
    
    # Add logout button in sidebar
    with st.sidebar:
        st.markdown(f"👤 **User:** {st.session_state.get('username', 'Unknown')}")
        if st.button("🚪 Logout"):
            st.session_state["authenticated"] = False
            st.session_state.clear()
            st.rerun()
    
    return True

# Usage:
# if check_authentication():
#     # Your deer hunting app code here
#     pass
