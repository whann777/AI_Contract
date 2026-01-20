"""
Application Settings and Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = if os.path.exists('/mount/src'):
    BASE_DIR = Path('/mount/src/ai_contract')
else:
    BASE_DIR = Path(__file__).parent.parent

DATA_DIR = BASE_DIR / 'data'

# Data directories
DIRECTORIES = {
    'agreements': DATA_DIR / 'agreements',
    'ap': DATA_DIR / 'ap',
    'ar': DATA_DIR / 'ar',
    'tta_summaries': DATA_DIR / 'tta_summaries',
    'results': DATA_DIR / 'results'
}

# Create directories if they don't exist
for dir_path in DIRECTORIES.values():
    dir_path.mkdir(parents=True, exist_ok=True)

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_CONFIG = {
    'model': 'gemini-2.5-flash',
    'temperature': 0.0,
    'top_p': 0.95,
    'top_k': 64,
    'max_output_tokens': 8192,
    'response_mime_type': 'application/json'
}

# Processing defaults
PROCESSING_DEFAULTS = {
    'dpi': 200,
    'max_image_width': 800,
    'encoding_attempts': ['utf-8', 'tis-620', 'cp874', 'latin1'],
    'json_file_suffix': '_summary.json'
}

# File patterns for auto-detection
FILE_PATTERNS = {
    'ap': [
        "Account_Payable*.csv",
        "Purchase*.csv",
        "AP*.csv",
        "*payable*.csv"
    ],
    'ar': [
        "Account_Receiveable*.csv",
        "AR_Detail*.csv",
        "AR*.csv",
        "*receivable*.csv"
    ],
    'agreements': ["*.pdf"]
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
    'csv_encoding': 'utf-8-sig',  # For Excel compatibility
    'date_format': '%Y-%m-%d',
    'number_format': '#,##0.00'
}

# Status definitions
STATUS_DEFINITIONS = {
    'OK': {'emoji': '✅', 'color': 'green', 'threshold': 1.0},
    'UNDER': {'emoji': '❌', 'color': 'red', 'description': 'Under-billed'},
    'OVER': {'emoji': '⚠️', 'color': 'orange', 'description': 'Over-billed'}
}

# Validation rules
VALIDATION_RULES = {
    'vendor_code_min_length': 3,
    'division_code_length': 2,
    'department_code_length': 2,
    'amount_tolerance': 1.0,  # THB
}
