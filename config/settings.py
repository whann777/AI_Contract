"""
Configuration settings - FIXED for Streamlit Cloud
"""

import os
from pathlib import Path

# Base directory - STREAMLIT CLOUD COMPATIBLE
if os.path.exists('/mount/src'):
    # Streamlit Cloud environment
    BASE_DIR = Path('/mount/src/ai_contract')
else:
    # Local environment
    BASE_DIR = Path(__file__).parent.parent

# Data directories
DATA_DIR = BASE_DIR / 'data'

# Create directories if they don't exist
DIRECTORIES = {
    'agreements': DATA_DIR / 'agreements',
    'ap': DATA_DIR / 'ap',
    'ar': DATA_DIR / 'ar',
    'tta_summaries': DATA_DIR / 'tta_summaries',
    'results': DATA_DIR / 'results'
}

# Create all directories
for dir_path in DIRECTORIES.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# Gemini API Configuration
GEMINI_CONFIG = {
    'model_name': 'gemini-2.0-flash-exp',
    'generation_config': {
        'temperature': 0,
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 8192,
        'response_mime_type': 'application/json'
    },
    'safety_settings': [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
}

# Processing defaults
PROCESSING_DEFAULTS = {
    'delay_between_pdfs': 30,  # seconds
    'show_pdf_images': False,
    'use_llm_validation': True,
    'max_retries': 3
}

# File patterns
FILE_PATTERNS = {
    'ap': ['Account_Payable*.csv', 'Purchase*.csv', 'AP*.csv'],
    'ar': ['Account_Receiveable*.csv', 'AR_Detail*.csv', 'AR*.csv'],
    'tta': ['*_summary.json']
}

# Status definitions
STATUS_DEFINITIONS = {
    'OK': 'ครบถ้วน - ส่วนต่างน้อยกว่า 1 บาท',
    'UNDER': 'ขาด - เก็บน้อยกว่าที่ควรเป็น',
    'OVER': 'เกิน - เก็บมากกว่าที่ควรเป็น'
}

# Display settings
DISPLAY_SETTINGS = {
    'page_title': 'Contract Audit System',
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Export settings
EXPORT_SETTINGS = {
    'excel_engine': 'openpyxl',
    'csv_encoding': 'utf-8-sig'
}
