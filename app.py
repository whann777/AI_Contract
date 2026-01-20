"""
Contract Audit System - Main Application
ระบบตรวจสอบสัญญาการค้าด้วย AI

Entry point สำหรับ Streamlit application
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import DISPLAY_SETTINGS
from ui.landing import show_landing_page, show_info_sidebar
from ui.analyze_mode import show_analyze_mode
from ui.auditor_mode import show_auditor_mode


def main():
    """Main application entry point"""
    
    # Page config
    st.set_page_config(
        page_title=DISPLAY_SETTINGS['page_title'],
        page_icon=DISPLAY_SETTINGS['page_icon'],
        layout=DISPLAY_SETTINGS['layout'],
        initial_sidebar_state=DISPLAY_SETTINGS['initial_sidebar_state']
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    /* Main container */
    .main {
        padding-top: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: 600;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    
    /* Tables */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Headers */
    h1 {
        color: #366092;
    }
    
    h2 {
        color: #4a5568;
    }
    
    h3 {
        color: #2d3748;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f7fafc;
    }
    
    /* Success/Warning/Error boxes */
    .element-container .stAlert {
        border-radius: 5px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #366092;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #f7fafc;
        border-radius: 5px;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'mode' not in st.session_state:
        st.session_state.mode = None
    
    # Sidebar
    show_info_sidebar()
    
    # Main content
    if st.session_state.mode is None:
        # Landing page
        selected_mode = show_landing_page()
        if selected_mode:
            st.session_state.mode = selected_mode
            st.rerun()
    
    elif st.session_state.mode == 'analyze':
        # Analyze mode (Part 1)
        show_analyze_mode()
    
    elif st.session_state.mode == 'auditor':
        # Auditor mode (Part 2)
        show_auditor_mode()


if __name__ == "__main__":
    main()
