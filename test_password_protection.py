#!/usr/bin/env python3
"""
Simple test to verify password protection is working locally
"""
import streamlit as st
import hashlib
import sys
import os

def check_password():
    """Returns True if the user entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        correct_password = "DeerHunter2025!"
        
        # Check if password key exists before accessing it
        if "password" in st.session_state:
            if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == hashlib.sha256(correct_password.encode()).hexdigest():
                st.session_state["password_correct"] = True
                del st.session_state["password"]
            else:
                st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("# 🦌 SECURITY TEST")
        st.markdown("### 🔐 Password Protection Active")
        st.text_input(
            "Enter Password:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.info("Expected Password: DeerHunter2025!")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("# 🦌 SECURITY TEST")
        st.markdown("### 🔐 Password Protection Active")
        st.text_input(
            "Enter Password:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("❌ Password incorrect")
        st.info("Expected Password: DeerHunter2025!")
        return False
    else:
        return True

# Test the protection
if not check_password():
    st.stop()

# If we get here, password was correct
st.success("✅ PASSWORD PROTECTION WORKING!")
st.markdown("## 🎯 Security Test Passed")
st.markdown("Password protection is functioning correctly.")
st.balloons()
