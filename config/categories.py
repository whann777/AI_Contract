"""
Allowance Categories Definition
Extracted from AI_Contract_V2.ipynb - Cell 3
"""

# กำหนด categories ของ allowance (Trade Term Agreement Support Types)
ALLOWANCE_CATEGORIES = {
    "ARB": "Unconditional Rebate",
    "CRB": "Conditional Rebate",
    "BRO": "Brochure Fee",
    "ADP": "Display Fee",
    "MMF": "Merchandise Marketing Fund",
    "SEN": "Seasonal Support",
    "COF": "Cooperate Coupon Support",
    "ANI": "Anniversary Discount",
    "OTS": "Other Promotion Service",
    "OTN": "Other Promotion Support",
    "DTS": "Data Sharing Fee",
    "NRT": "Non Return Discount",
    "HQC": "Hygiene & Quality Control",
    "GCS": "Guarantee GP Compensation",
    "P13": "Training Support",
    "NIT": "New Item Support",
    "NST": "New Store Opening",
    "RST": "Store Renovate",
    "PCM": "PC Missing Fee",
    "WPS": "Vendor Web Portal Service",
    "SPD": "Special Discount",
    "CCS": "Clearance/Markdown"
}

# Category mappings for AR validation
CATEGORY_KEYWORDS = {
    "BRO": ["leaflet", "brochure", "magazine", "ad", "ลงสื่อ"],
    "NST": ["เปิดสาขาใหม่", "grand opening", "new store"],
    "ANI": ["anniversary", "ครบรอบ"],
    "CRB": ["step rebate", "conditional"],
    "COF": ["coupon", "คูปอง"],
}
