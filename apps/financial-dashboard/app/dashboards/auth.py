#!/usr/bin/env python3
"""
Authentication module for the financial dashboard.

Provides simple password-based authentication for the application.
"""

import streamlit as st
from typing import Tuple, Optional

class Auth:
    """Authentication handler for the financial dashboard."""
    
    @staticmethod
    def check_authentication() -> bool:
        """Authenticate user with password protection.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.auth_tried = False
            
        if st.session_state.authenticated:
            return True
            
        st.title("Financial Dashboard Authentication")
        
        # Simple password authentication
        password = st.text_input("Enter Dashboard Password", type="password")
        if st.button("Login"):
            if password == "academy2025":  # Simple password for demonstration
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
                st.session_state.auth_tried = True
                    
        if st.session_state.auth_tried:
            st.warning("Please contact your administrator if you cannot access the dashboard.")
            
        return False
