# AI-Powered Contract Audit System - Architecture Document

## Executive Summary

This is a production-grade Information Systems application for automated contract auditing in shopping mall supplier agreements. The system leverages Google Gemini AI to analyze contracts, calculate expected support amounts, and reconcile them against accounting data (AP/AR).

## 1. UNDERSTANDING OF EXISTING NOTEBOOK

### 1.1 Core Components Identified

The notebook contains **THREE MAIN CLASSES** that form the business logic:

#### **A. TTADocumentAnalyzer**
- **Purpose**: AI-powered contract document analysis using Google Gemini
- **Key Methods**:
  - `analyze_document()`: Processes PDF contracts, extracts vendor support terms
  - `create_analysis_prompt()`: Constructs sophisticated prompts with examples
  - `display_pdf_images()`: Shows PDF preview (for manual verification)
- **Output**: JSON structure with vendor details and allowances

#### **B. DataPreprocessor**
- **Purpose**: Data cleaning and preparation for AP/AR data
- **Key Methods**:
  - `clean_amount()`: Standardizes currency formats, handles negatives
  - `prepare_ap_data()`: Processes Account Payable (purchase) data
  - `prepare_ar_data()`: Processes Account Receivable (billing) data
- **Features**:
  - Handles multiple encodings (UTF-8, TIS-620, CP874)
  - Creates composite keys for matching (vendor_code + division + department)
  - Converts department codes to division/department structure

#### **C. TTAReconciliationSystem**
- **Purpose**: Orchestrates the entire reconciliation workflow
- **Key Methods**:
  - `load_tta_summaries()`: Loads AI-generated JSON summaries
  - `load_ap_data()`: Loads purchase data from CSV
  - `load_ar_data()`: Loads receivable data from CSV
  - `calculate_allowances()`: Computes expected support amounts
  - `reconcile_with_ar()`: Compares calculated vs actual billing
  - `validate_ar_with_llm()`: Uses AI to validate REF_TYPE mapping
  - `export_to_excel()`: Generates Excel reports

### 1.2 Business Logic Flow

```
1. CONTRACT ANALYSIS (AI)
   ├─ Upload PDF contracts
   ├─ Gemini extracts: vendor info, divisions, departments, allowance terms
   ├─ Output: JSON with category codes, rates, fixed amounts
   └─ Save as: {vendor}_{div}_{dept}_summary.json

2. DATA LOADING
   ├─ Load TTA JSON files (contract summaries)
   ├─ Load AP CSV (purchase amounts by vendor/division/department)
   └─ Load AR CSV (billed amounts by vendor/division/department/category)

3. CALCULATION
   ├─ For each vendor-division-department:
   │  ├─ Get contract terms from TTA
   │  ├─ Get purchase amount from AP
   │  ├─ Calculate expected support:
   │  │  ├─ Rate-based: purchase_amount × rate%
   │  │  └─ Fixed amount: as specified in contract
   │  └─ Store calculated amounts

4. RECONCILIATION
   ├─ Match calculated amounts with AR using REF_TYPE
   ├─ Compare: expected vs actually billed
   ├─ Flag discrepancies:
   │  ├─ ✅ Fully collected (difference < 1 THB)
   │  ├─ ❌ Under-billed (negative difference)
   │  └─ ⚠️ Over-billed (positive difference)
   └─ Generate audit report

5. REPORTING
   └─ Export to Excel with multiple sheets (summary, details, missing items)
```

### 1.3 Key Business Rules

1. **Allowance Categories** (21 types):
   - ARB (Unconditional Rebate), CRB (Conditional Rebate)
   - BRO (Brochure Fee), ADP (Display Fee)
   - MMF (Marketing Fund), COF (Coupon Support)
   - ANI (Anniversary), NST (New Store Opening)
   - And 13 more...

2. **Composite Key Structure**:
   - Format: `{vendor_code}_{division_code}_{department_code}`
   - Division: 2 digits (e.g., "01", "05")
   - Department: 2 digits (e.g., "20", "35")
   - Example: "V12345_01_20"

3. **Calculation Logic**:
   - Rate-based: `calculated = purchase_amount × (rate / 100)`
   - Fixed: `calculated = fix_amount`
   - Annual calculation for periodic payments

4. **Matching Logic**:
   - AP → TTA: By composite key
   - AR → Calculated: By composite key + REF_TYPE (category code)

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   WEB APPLICATION                        │
│                     (Streamlit)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐              ┌──────────────┐         │
│  │  FOR ANALYZE │              │ FOR AUDITOR  │         │
│  │   (Part 1)   │              │   (Part 2)   │         │
│  └──────────────┘              └──────────────┘         │
│                                                          │
└─────────────────────────────────────────────────────────┘
            │                              │
            │                              │
            ▼                              ▼
┌─────────────────────┐      ┌─────────────────────────┐
│  AI PROCESSING      │      │  DASHBOARD & REPORTING  │
│  - Document Upload  │      │  - View Results         │
│  - Gemini Analysis  │      │  - Filter Data          │
│  - Calculation      │      │  - Export Reports       │
│  - Reconciliation   │      │                         │
└─────────────────────┘      └─────────────────────────┘
            │                              │
            │                              │
            ▼                              ▼
┌──────────────────────────────────────────────────────┐
│              DATA PERSISTENCE LAYER                   │
│  - Processed Results (Pickle/Parquet)                │
│  - TTA JSON Summaries                                │
│  - Cached Calculations                               │
└──────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────┐
│              FILE SYSTEM STORAGE                      │
│  /data/                                              │
│    ├── agreements/       (PDF contracts)             │
│    ├── ap/              (Purchase CSV)               │
│    ├── ar/              (Receivable CSV)             │
│    ├── tta_summaries/   (AI outputs JSON)            │
│    └── results/         (Processed results)          │
└──────────────────────────────────────────────────────┘
```

### 2.2 Application Flow

```
┌─────────────────────────────────────────────────┐
│                 LANDING PAGE                     │
│                                                  │
│         [FOR ANALYZE]    [FOR AUDITOR]          │
│                                                  │
└─────────────────────────────────────────────────┘
             │                    │
             │                    │
             ▼                    ▼
┌──────────────────────┐  ┌──────────────────────┐
│   ANALYZE MODE       │  │   AUDITOR MODE       │
│                      │  │                      │
│ 1. Upload PDFs       │  │ 1. Load Results      │
│ 2. Upload AP CSV     │  │ 2. Filter Dashboard  │
│ 3. Upload AR CSV     │  │    - By Vendor       │
│ 4. Run Analysis      │  │    - By Status       │
│    ├─ AI Extract     │  │    - By Division     │
│    ├─ Calculate      │  │ 3. View Details      │
│    └─ Reconcile      │  │ 4. Export            │
│ 5. Save Results      │  │    ├─ Excel          │
│                      │  │    └─ CSV            │
└──────────────────────┘  └──────────────────────┘
```

## 3. PROJECT STRUCTURE

```
contract_audit_system/
│
├── app.py                          # Main Streamlit application (entry point)
│
├── config/
│   ├── __init__.py
│   ├── settings.py                 # Configuration (paths, API keys)
│   └── categories.py               # Allowance categories definition
│
├── core/
│   ├── __init__.py
│   ├── ai_analyzer.py             # TTADocumentAnalyzer (from notebook)
│   ├── data_processor.py          # DataPreprocessor (from notebook)
│   └── reconciliation.py          # TTAReconciliationSystem (from notebook)
│
├── services/
│   ├── __init__.py
│   ├── file_handler.py            # File upload/download operations
│   ├── processing_service.py     # Orchestrates Part 1 workflow
│   └── reporting_service.py      # Excel/CSV export functionality
│
├── ui/
│   ├── __init__.py
│   ├── landing.py                 # Landing page component
│   ├── analyze_mode.py            # Part 1 UI (For Analyze)
│   └── auditor_mode.py            # Part 2 UI (For Auditor)
│
├── utils/
│   ├── __init__.py
│   ├── validators.py              # Data validation utilities
│   └── formatters.py              # Display formatting helpers
│
├── data/                          # Data directory (gitignored)
│   ├── agreements/
│   ├── ap/
│   ├── ar/
│   ├── tta_summaries/
│   └── results/
│
├── requirements.txt               # Python dependencies
├── README.md                      # User documentation
└── .env.example                   # Environment variables template
```

## 4. MAPPING NOTEBOOK → APPLICATION

### 4.1 Core Logic Preservation

| Notebook Component | Application Module | Changes |
|-------------------|-------------------|---------|
| `TTADocumentAnalyzer` | `core/ai_analyzer.py` | ✅ Keep exact logic, adapt for file paths |
| `DataPreprocessor` | `core/data_processor.py` | ✅ Keep exact logic, no changes |
| `TTAReconciliationSystem` | `core/reconciliation.py` | ✅ Keep exact logic, add persistence |
| `ALLOWANCE_CATEGORIES` | `config/categories.py` | ✅ Extract to config |
| Analysis workflow | `services/processing_service.py` | ✅ Orchestrate notebook cells |

### 4.2 Part 1 (For Analyze) Architecture

**Purpose**: Automated contract processing and reconciliation

**Workflow**:
```python
# services/processing_service.py
class ProcessingService:
    def run_full_analysis():
        # 1. Initialize components
        analyzer = TTADocumentAnalyzer(api_key)
        recon = TTAReconciliationSystem(base_folder)
        
        # 2. Process PDFs (replaces notebook Cell 8)
        for pdf in get_pdfs_from_folder():
            result = analyzer.analyze_document(pdf)
            save_json(result)
        
        # 3. Load data (replaces notebook Cells 9-13)
        recon.load_tta_summaries()
        recon.load_ap_data()
        recon.load_ar_data()
        
        # 4. Calculate & Reconcile (replaces notebook Cell 14)
        calculated = recon.calculate_allowances()
        reconciled = recon.reconcile_with_ar()
        
        # 5. Save results for Part 2
        save_results(reconciled)
        
        return reconciled
```

**UI Components** (`ui/analyze_mode.py`):
1. File upload sections (PDFs, AP CSV, AR CSV)
2. API key configuration
3. Progress indicators during processing
4. Results preview
5. Save confirmation

### 4.3 Part 2 (For Auditor) Architecture

**Purpose**: Interactive dashboard for audit results

**Features**:
```python
# ui/auditor_mode.py
class AuditorDashboard:
    def display():
        # 1. Load processed results
        results = load_saved_results()
        
        # 2. Filters
        vendors = filter_by_vendor(results)
        status = filter_by_status(results)  # OK/Under/Over
        divisions = filter_by_division(results)
        
        # 3. Summary metrics
        display_metrics(filtered_results)
        
        # 4. Detailed table
        display_data_table(filtered_results)
        
        # 5. Drill-down view
        if vendor_selected:
            display_vendor_details(vendor)
        
        # 6. Export options
        export_to_excel(filtered_results)
        export_to_csv(filtered_results)
```

**Dashboard Components**:
1. **Summary Cards**:
   - Total vendors processed
   - Total expected amount
   - Total collected amount
   - Collection rate (%)
   
2. **Filter Panel**:
   - Multi-select vendors
   - Status dropdown (All/OK/Under-billed/Over-billed)
   - Division/Department filters
   - Year selector

3. **Results Table**:
   - Sortable columns
   - Color-coded status
   - Expandable rows for details

4. **Export Panel**:
   - Excel (with formatting)
   - CSV (raw data)

## 5. DATA MODELS

### 5.1 TTA Summary (Contract Analysis Output)

```json
{
  "vendor_code": "V12345",
  "Division_code": "01",
  "Division_name": "Food & Beverage",
  "Department_code": "20",
  "Department_name": "Fresh Food",
  "allowances": [
    {
      "category_code": "ARB",
      "category_name": "Unconditional Rebate",
      "rate_percent": 2.5,
      "fix_amount": null,
      "description": "Monthly rebate on purchase",
      "payment_terms": "monthly"
    },
    {
      "category_code": "ANI",
      "category_name": "Anniversary Discount",
      "rate_percent": null,
      "fix_amount": 50000.00,
      "description": "Annual anniversary support",
      "payment_terms": "annually"
    }
  ]
}
```

### 5.2 Reconciliation Result

```python
{
    'vendor_code': str,
    'vendor_name': str,
    'division': str,
    'department': str,
    'tta_key': str,
    'year': int,
    'category_code': str,
    'category_name': str,
    'purchase_amount': float,
    'rate_percent': float | None,
    'fix_amount': float | None,
    'calculated_amount': float,      # Expected
    'actually_collected': float,     # From AR
    'difference': float,              # AR - Expected
    'status': str,                    # 'OK' / 'Under' / 'Over'
    'calculation_type': str,          # '2.5%' / 'Fixed'
    'description': str,
    'payment_terms': str
}
```

## 6. TECHNICAL SPECIFICATIONS

### 6.1 Technology Stack

- **Framework**: Streamlit 1.30+
- **AI**: Google Generative AI (Gemini 2.5 Flash)
- **Data Processing**: Pandas, NumPy
- **PDF Processing**: pdf2image, PyPDF2
- **Export**: OpenPyXL, XlsxWriter
- **Environment**: Python 3.9+

### 6.2 Key Dependencies

```
streamlit>=1.30.0
google-generativeai>=0.3.0
pandas>=2.0.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
pdf2image>=1.16.0
PyPDF2>=3.0.0
pillow>=10.0.0
python-dotenv>=1.0.0
```

### 6.3 Configuration Management

```python
# config/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

DIRECTORIES = {
    'agreements': DATA_DIR / 'agreements',
    'ap': DATA_DIR / 'ap',
    'ar': DATA_DIR / 'ar',
    'tta_summaries': DATA_DIR / 'tta_summaries',
    'results': DATA_DIR / 'results'
}

GEMINI_CONFIG = {
    'model': 'gemini-2.5-flash',
    'temperature': 0.0,
    'top_p': 0.95,
    'top_k': 64,
    'max_output_tokens': 8192
}

PROCESSING_DEFAULTS = {
    'dpi': 200,
    'encoding_attempts': ['utf-8', 'tis-620', 'cp874', 'latin1']
}
```

## 7. SECURITY & PRODUCTION CONSIDERATIONS

### 7.1 API Key Management
- Store in `.env` file (never commit)
- Use `st.secrets` for Streamlit Cloud deployment
- Validate key before processing

### 7.2 Data Privacy
- Process data locally (no external transmission except Gemini API)
- Clear uploaded files option
- No cloud storage of sensitive data

### 7.3 Error Handling
- Graceful degradation for missing files
- Detailed error messages for debugging
- Transaction rollback for failed processing

### 7.4 Performance Optimization
- Cache processed results with `@st.cache_data`
- Batch PDF processing
- Lazy loading for large datasets
- Progress bars for long operations

## 8. DEPLOYMENT STRATEGY

### 8.1 Local Deployment
```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with API key

# Run
streamlit run app.py
```

### 8.2 Docker Deployment
```dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y poppler-utils
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### 8.3 Streamlit Cloud Deployment
- Add secrets in dashboard
- Configure `requirements.txt`
- Set Python version to 3.9+

## 9. TESTING STRATEGY

### 9.1 Unit Tests
- Test data preprocessing functions
- Test calculation logic
- Test matching algorithms

### 9.2 Integration Tests
- End-to-end workflow with sample data
- API integration tests (with mock)

### 9.3 User Acceptance Testing
- Process sample contracts
- Verify calculations manually
- Test export functionality

## 10. FUTURE ENHANCEMENTS

1. **Database Integration**: Replace file-based storage with PostgreSQL
2. **User Authentication**: Add role-based access control
3. **Audit Trail**: Log all user actions
4. **Scheduled Processing**: Automate periodic reconciliation
5. **Email Notifications**: Alert on discrepancies
6. **Advanced Analytics**: Trend analysis, predictive modeling
7. **Multi-language Support**: Thai/English UI

---

## Summary

This architecture preserves 100% of the notebook's core logic while restructuring it into a production-grade IS application. The key principles are:

1. ✅ **Preserve Business Logic**: No changes to AI prompts, calculation formulas, or matching algorithms
2. ✅ **Modular Design**: Separate concerns (AI, processing, UI, persistence)
3. ✅ **Two-Part Workflow**: Clean separation between analysis and audit
4. ✅ **Production-Ready**: Error handling, configuration, security
5. ✅ **Maintainable**: Clear structure, documented, testable

**Next Steps**: Proceed to code implementation following this architecture.
