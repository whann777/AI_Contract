"""
Formatting utilities
"""

import pandas as pd


def format_currency(amount: float, currency: str = 'THB') -> str:
    """
    จัดรูปแบบจำนวนเงิน
    
    Args:
        amount: จำนวนเงิน
        currency: สกุลเงิน
        
    Returns:
        str: จำนวนเงินที่จัดรูปแบบแล้ว
    """
    if pd.isna(amount):
        return "N/A"
    
    if currency == 'THB':
        return f"{amount:,.2f} บาท"
    else:
        return f"{currency} {amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    จัดรูปแบบเปอร์เซ็นต์
    
    Args:
        value: ค่าเปอร์เซ็นต์
        decimals: ทศนิยม
        
    Returns:
        str: เปอร์เซ็นต์ที่จัดรูปแบบแล้ว
    """
    if pd.isna(value):
        return "N/A"
    
    return f"{value:.{decimals}f}%"


def format_status(status: str) -> str:
    """
    จัดรูปแบบสถานะพร้อม emoji
    
    Args:
        status: สถานะ
        
    Returns:
        str: สถานะพร้อม emoji
    """
    status_map = {
        'OK': '✅ ครบ',
        'UNDER': '❌ ขาด',
        'OVER': '⚠️ เกิน',
        'ครบ': '✅ ครบ',
        'ขาด': '❌ ขาด',
        'เกิน': '⚠️ เกิน'
    }
    
    return status_map.get(status, status)


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    ตัดข้อความให้สั้นลง
    
    Args:
        text: ข้อความ
        max_length: ความยาวสูงสุด
        
    Returns:
        str: ข้อความที่ตัดแล้ว
    """
    if not text or pd.isna(text):
        return ""
    
    text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."
