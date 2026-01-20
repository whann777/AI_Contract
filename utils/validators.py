"""
Validation utilities
"""

import pandas as pd
from typing import Tuple, Optional


def validate_ap_csv(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    ตรวจสอบความถูกต้องของ AP CSV
    
    Args:
        df: DataFrame to validate
        
    Returns:
        (is_valid, error_message)
    """
    required_columns = ['VndCode', 'VNDNAME', 'DEPT_CODE', 'INVPAYAMT']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"ขาดคอลัมน์: {', '.join(missing_columns)}"
    
    return True, None


def validate_ar_csv(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    ตรวจสอบความถูกต้องของ AR CSV
    
    Args:
        df: DataFrame to validate
        
    Returns:
        (is_valid, error_message)
    """
    required_columns = ['SUP_CODE', 'CUSTNAME', 'DPTNBR', 'EXTENDED_AMOUNT']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"ขาดคอลัมน์: {', '.join(missing_columns)}"
    
    return True, None


def validate_api_key(api_key: str) -> bool:
    """
    ตรวจสอบรูปแบบ API key
    
    Args:
        api_key: API key string
        
    Returns:
        bool: True if valid format
    """
    if not api_key:
        return False
    
    # Basic validation - Gemini API keys typically start with "AIza"
    if not api_key.startswith("AIza"):
        return False
    
    # Check length (typical: 39 characters)
    if len(api_key) < 30:
        return False
    
    return True
