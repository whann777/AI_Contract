# Contract Audit System

AI-powered contract auditing system for shopping mall supplier agreements using Google Gemini.

## Overview

This system automates:
1. **Contract Analysis** - Extracts support terms from PDF contracts using AI
2. **Financial Calculation** - Computes expected support amounts based on purchase data
3. **Reconciliation** - Compares calculated vs actual billing to detect discrepancies

## Features

- **Part 1: For Analyze** - Automated processing of contracts and reconciliation
- **Part 2: For Auditor** - Interactive dashboard for reviewing and exporting results
- **21 Support Categories** - Comprehensive coverage of allowance types
- **Multi-format Export** - Excel (formatted) and CSV outputs

## Installation

### Prerequisites
- Python 3.9 or higher
- Poppler (for PDF processing)
- Google Gemini API key

### Setup

1. Clone/extract the project:
```bash
cd contract_audit_system
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. Install system dependencies (Ubuntu/Debian):
```bash
sudo apt-get install -y poppler-utils
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Part 1: For Analyze

1. Select "For Analyze" on the landing page
2. Upload files:
   - PDF contract documents (one or multiple)
   - AP CSV file (Account Payable/Purchase data)
   - AR CSV file (Account Receivable/Billing data)
3. Enter your Gemini API key
4. Click "Run Analysis"
5. Wait for processing to complete
6. Review results and they'll be saved for Part 2

### Part 2: For Auditor

1. Select "For Auditor" on the landing page
2. Choose a previously processed analysis session
3. Use filters to narrow results:
   - Select specific vendors
   - Filter by status (OK, Under-billed, Over-billed)
   - Filter by division/department
4. Review dashboard metrics and detailed tables
5. Export results:
   - Excel (multi-sheet with formatting)
   - CSV (raw data for further analysis)

## Data Structure

### Input Files

**Agreements (PDF)**:
- Place in: `data/agreements/`
- Format: Any PDF contract with support terms

**AP CSV**:
- Place in: `data/ap/`
- Required columns: `VndCode`, `VNDNAME`, `DEPT_CODE`, `INVPAYAMT`, `INV_YEAR`

**AR CSV**:
- Place in: `data/ar/`
- Required columns: `SUP_CODE`, `CUSTNAME`, `DPTNBR`, `EXTENDED_AMOUNT`, `REF_TYPE`

### Output Files

**TTA Summaries**:
- Location: `data/tta_summaries/`
- Format: JSON with extracted contract terms

**Results**:
- Location: `data/results/`
- Format: Parquet/Excel with reconciliation results

## Support Categories

The system recognizes 21 allowance categories:

- ARB - Unconditional Rebate
- CRB - Conditional Rebate
- BRO - Brochure Fee
- ADP - Display Fee
- MMF - Merchandise Marketing Fund
- SEN - Seasonal Support
- COF - Cooperate Coupon Support
- ANI - Anniversary Discount
- ... and 13 more

## Architecture

```
contract_audit_system/
├── app.py                    # Main application entry
├── config/                   # Configuration
├── core/                     # Business logic (from notebook)
├── services/                 # Orchestration
├── ui/                       # User interface components
└── data/                     # Data storage
```

## Troubleshooting

### Common Issues

**API Key Error**:
- Ensure GEMINI_API_KEY is correctly set in .env
- Verify your API key has access to Gemini 2.5 Flash

**PDF Processing Error**:
- Install poppler: `sudo apt-get install poppler-utils`
- Check PDF is not encrypted or corrupted

**Encoding Issues**:
- The system tries multiple encodings (UTF-8, TIS-620, CP874, Latin1)
- Save CSV files with UTF-8-BOM encoding for best compatibility

**Memory Issues**:
- Process large batches in smaller chunks
- Increase system RAM if processing 50+ contracts

## Development

Built with:
- Streamlit for UI
- Google Gemini AI for contract analysis
- Pandas for data processing
- OpenPyXL for Excel export

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact the development team.
