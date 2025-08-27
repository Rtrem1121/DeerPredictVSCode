import streamlit as st
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple password protection for deer hunting app
def check_password():
    """Returns True if the user entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Get password from environment variable for security
        correct_password = os.getenv("APP_PASSWORD", "DefaultPassword123!")
        
        if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == hashlib.sha256(correct_password.encode()).hexdigest():
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown("# 🦌 Deer Hunting App Access")
        st.markdown("### Enter password to access professional hunting intelligence:")
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.markdown("---")
        st.markdown("*Professional deer prediction system with 89.1% accuracy*")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.markdown("# 🦌 Deer Hunting App Access")
        st.markdown("### Enter password to access professional hunting intelligence:")
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😞 Password incorrect. Please try again.")
        return False
    else:
        # Password correct
        return True

# Usage in your main app file:
if check_password():
    # Your existing app code goes here
    st.title("🦌 Professional Deer Hunting Intelligence")
    # ... rest of your app
else:
    st.stop()  # Don't run the rest of the app
