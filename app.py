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

# Import with try-except for better error handling
try:
    from config import DISPLAY_SETTINGS
except ImportError as e:
    st.error(f"Error importing config: {e}")
    st.stop()

try:
    from ui import show_landing_page, show_info_sidebar, show_analyze_mode, show_auditor_mode
except ImportError as e:
    st.error(f"Error importing UI modules: {e}")
    st.stop()


def main():
    """Main application entry point"""
    
    # Page config
    st.set_page_config(
        page_title=DISPLAY_SETTINGS.get('page_title', 'Contract Audit System'),
        page_icon=DISPLAY_SETTINGS.get('page_icon', '📊'),
        layout=DISPLAY_SETTINGS.get('layout', 'wide'),
        initial_sidebar_state=DISPLAY_SETTINGS.get('initial_sidebar_state', 'expanded')
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    /* ===== SIDEBAR STYLING ===== */
    
    /* พื้นหลัง Sidebar - สีเข้ม */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c4f7c 100%) !important;
    }
    
    /* ข้อความทั้งหมดใน Sidebar */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Header ใน Sidebar */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Links ใน Sidebar */
    [data-testid="stSidebar"] a {
        color: #90caf9 !important;
    }
    
    [data-testid="stSidebar"] a:hover {
        color: #bbdefb !important;
        text-decoration: underline !important;
    }
    
    /* ปุ่มใน Sidebar */
    [data-testid="stSidebar"] button {
        background-color: #366092 !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: #4a7ab8 !important;
    }
    
    /* Checkbox/Radio ใน Sidebar */
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }
    
    /* Divider ใน Sidebar */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Info/Warning/Success boxes ใน Sidebar */
    [data-testid="stSidebar"] .stAlert {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-left: 4px solid #90caf9 !important;
    }
    
    /* Icon colors ใน Sidebar */
    [data-testid="stSidebar"] svg {
        fill: #ffffff !important;
    }
    
    /* ===== MAIN CONTENT STYLING ===== */
    
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
    try:
        show_info_sidebar()
    except Exception as e:
        st.sidebar.error(f"Error loading sidebar: {e}")
    
    # Main content
    try:
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
    
    except Exception as e:
        st.error(f"Application error: {e}")
        st.error("Please check the logs for more details.")
        
        # Show error details in expander
        with st.expander("🔍 Error Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
