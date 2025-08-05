# File: config/api_keys.py

import os

def get_serper_api_key():
    """Fetches the Serper API key from Streamlit secrets or environment variables."""
    # This will be used in the streamlit app
    try:
        import streamlit as st
        return st.secrets["SERPER_API_KEY"]
    except (ImportError, KeyError):
        return os.environ.get("SERPER_API_KEY", "")

def get_gemini_api_key():
    """Fetches the Gemini API key from Streamlit secrets or environment variables."""
    # This will be used in the streamlit app
    try:
        import streamlit as st
        return st.secrets["GEMINI_API_KEY"]
    except (ImportError, KeyError):
        return os.environ.get("GEMINI_API_KEY", "")
