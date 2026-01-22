"""
Analyze Mode UI - Modern Professional Design
แยก 2 Steps: Process PDFs / Analyze Data
"""

import streamlit as st
from pathlib import Path
import time
import json
import traceback

# Safe imports with error handling
try:
    from services.processing_service import ProcessingService
    from config.settings import DIRECTORIES
except Exception as e:
    st.error(f"Import error: {e}")
    DIRECTORIES = {}


def show_analyze_mode():
    """แสดง UI สำหรับโหมด Analyze (Modern Design)"""
    
    # Custom CSS สำหรับ Modern UI
    st.markdown("""
    <style>
    /* Card สำหรับ sections */
    .status-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .step-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #e2e8f0;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .step-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 20px rgba(102,126,234,0.2);
        transition: all 0.3s ease;
    }
    
    /* Metrics */
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2d3748;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #718096;
        margin-top: 0.5rem;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    h2 {
        color: #2d3748;
        font-weight: 700;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #4a5568;
        font-weight: 600;
    }
    
    /* Info boxes */
    .stInfo {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border-left: 4px solid #0284c7;
        border-radius: 8px;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #059669;
        border-radius: 8px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
    }
    
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #dc2626;
        border-radius: 8px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("🔬 Contract Analysis System")
    
    # Back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
    
    st.markdown("---")
    
    # Initialize session state
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''
    
    # Main sections
    try:
        show_status_dashboard()
        st.markdown("---")
        show_step1_section()
        st.markdown("---")
        show_step2_section()
        st.markdown("---")
        show_results_section()
    except Exception as e:
        st.error(f"Error rendering UI: {e}")
        st.code(traceback.format_exc())


def show_status_dashboard():
    """แสดง Dashboard สถานะไฟล์"""
    
    st.markdown("### 📊 System Status")
    
    # Get directories safely
    try:
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / 'data'
        
        pdf_folder = data_dir / 'agreements'
        json_folder = data_dir / 'tta_summaries'
        ap_folder = data_dir / 'ap'
        ar_folder = data_dir / 'ar'
        
        # Create folders if not exist
        json_folder.mkdir(parents=True, exist_ok=True)
        
        # Count files
        pdf_count = len(list(pdf_folder.glob('*.pdf'))) if pdf_folder.exists() else 0
        json_count = len(list(json_folder.glob('*.json'))) if json_folder.exists() else 0
        ap_count = len(list(ap_folder.glob('*.csv'))) if ap_folder.exists() else 0
        ar_count = len(list(ar_folder.glob('*.csv'))) if ar_folder.exists() else 0
        
    except Exception as e:
        st.error(f"Error reading directories: {e}")
        pdf_count = json_count = ap_count = ar_count = 0
    
    # Display in modern cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "✅" if pdf_count > 0 else "❌"
        st.markdown(f"""
        <div class="metric-container">
            <div style="font-size: 2rem;">{status}</div>
            <div class="metric-value">{pdf_count}</div>
            <div class="metric-label">📄 PDF Files</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        status = "✅" if json_count > 0 else "⚠️"
        st.markdown(f"""
        <div class="metric-container">
            <div style="font-size: 2rem;">{status}</div>
            <div class="metric-value">{json_count}</div>
            <div class="metric-label">📋 Processed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        status = "✅" if ap_count > 0 else "❌"
        st.markdown(f"""
        <div class="metric-container">
            <div style="font-size: 2rem;">{status}</div>
            <div class="metric-value">{ap_count}</div>
            <div class="metric-label">💰 AP Files</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status = "✅" if ar_count > 0 else "❌"
        st.markdown(f"""
        <div class="metric-container">
            <div style="font-size: 2rem;">{status}</div>
            <div class="metric-value">{ar_count}</div>
            <div class="metric-label">📊 AR Files</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Progress indicator
    if pdf_count > 0 and json_count > 0:
        progress = json_count / pdf_count
        st.progress(progress, text=f"Processing: {json_count}/{pdf_count} files ({progress*100:.0f}%)")


def show_step1_section():
    """STEP 1: Process PDFs"""
    
    with st.expander("📂 **STEP 1: Process PDF Files**", expanded=False):
        
        st.info("""
        **One-Time Setup**
        
        This step extracts contract information from PDF files using AI. You only need to do this once, or when you have new PDF files.
        
        ⏱️ **Time:** ~30 seconds per file  
        🤖 **AI:** Gemini 2.5 Flash
        """)
        
        # Check API Key
        api_key = check_api_key()
        if not api_key:
            return
        
        # Get file counts
        try:
            base_dir = Path(__file__).parent.parent
            data_dir = base_dir / 'data'
            pdf_folder = data_dir / 'agreements'
            json_folder = data_dir / 'tta_summaries'
            json_folder.mkdir(parents=True, exist_ok=True)
            
            pdf_files = list(pdf_folder.glob('*.pdf')) if pdf_folder.exists() else []
            json_files = list(json_folder.glob('*.json')) if json_folder.exists() else []
            
        except Exception as e:
            st.error(f"Error: {e}")
            return
        
        if not pdf_files:
            st.error("❌ No PDF files found in `data/agreements/`")
            return
        
        # Status
        col1, col2, col3 = st.columns(3)
        col1.metric("📄 PDF Files", len(pdf_files))
        col2.metric("📋 Processed", len(json_files))
        col3.metric("⏳ Remaining", max(0, len(pdf_files) - len(json_files)))
        
        if len(json_files) >= len(pdf_files):
            st.success("✅ All PDFs have been processed!")
            st.info("💡 You can skip to **STEP 2** to analyze the data")
        else:
            st.warning(f"⚠️ {len(pdf_files) - len(json_files)} files need processing")
        
        # Options
        st.markdown("#### ⚙️ Processing Options")
        col1, col2 = st.columns(2)
        with col1:
            show_images = st.checkbox("Show images during processing", value=False)
        with col2:
            delay_seconds = st.number_input("Delay between files (seconds)", 
                                           min_value=0, max_value=60, value=30,
                                           help="Time to wait between API calls to avoid rate limits")
        
        # Process button
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            run_pdf_processing(
                pdf_files=[str(f) for f in pdf_files],
                api_key=api_key,
                show_images=show_images,
                delay_seconds=delay_seconds
            )


def show_step2_section():
    """STEP 2: Analyze Data"""
    
    st.markdown("### 📊 STEP 2: Analyze Data")
    
    st.info("""
    **Fast Analysis** (Can be repeated)
    
    This step loads the processed data and performs calculations. You can run this as many times as you want, even with different AP/AR files.
    
    ⏱️ **Time:** ~30-60 seconds  
    ♻️ **Repeatable:** Yes!
    """)
    
    # Check files
    try:
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / 'data'
        
        json_folder = data_dir / 'tta_summaries'
        ap_folder = data_dir / 'ap'
        ar_folder = data_dir / 'ar'
        
        json_folder.mkdir(parents=True, exist_ok=True)
        
        json_files = list(json_folder.glob('*.json')) if json_folder.exists() else []
        ap_files = list(ap_folder.glob('*.csv')) if ap_folder.exists() else []
        ar_files = list(ar_folder.glob('*.csv')) if ar_folder.exists() else []
        
    except Exception as e:
        st.error(f"Error reading files: {e}")
        return
    
    # Validation
    if not json_files:
        st.error("❌ No processed data found. Please complete **STEP 1** first.")
        st.info("💡 Click on **STEP 1** above to process your PDF files")
        return
    
    if not ap_files:
        st.error("❌ No AP files found in `data/ap/`")
        return
    
    if not ar_files:
        st.error("❌ No AR files found in `data/ar/`")
        return
    
    # Show metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Contracts", len(json_files))
    col2.metric("💰 AP Files", len(ap_files))
    col3.metric("📊 AR Files", len(ar_files))
    
    # Options
    st.markdown("#### ⚙️ Analysis Options")
    use_llm_validation = st.checkbox(
        "🤖 Use AI to validate AR data",
        value=True,
        help="Uses LLM to check and correct REF_TYPE in AR data"
    )
    
    # Analyze button
    if st.button("🔍 Analyze Now", type="primary", use_container_width=True, key="analyze_btn"):
        run_analysis(
            json_folder=json_folder,
            ap_file=str(ap_files[0]),
            ar_file=str(ar_files[0]),
            use_llm_validation=use_llm_validation
        )


def check_api_key():
    """ตรวจสอบ API Key"""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ Gemini API Key is configured")
            return api_key
        else:
            st.error("❌ Gemini API Key not found in Secrets")
            st.info("""
            **Setup Instructions:**
            1. Go to Streamlit Cloud → Settings → Secrets
            2. Add: `GEMINI_API_KEY = "your-api-key-here"`
            3. Save and reboot the app
            """)
            return None
    except Exception as e:
        st.error(f"❌ Error reading API Key: {e}")
        return None


def run_pdf_processing(pdf_files, api_key, show_images, delay_seconds):
    """รันประมวลผล PDF"""
    
    try:
        service = ProcessingService(api_key)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total, filename):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"📄 Processing: {filename} ({current}/{total})")
        
        # Process
        status_text.text("🔄 Starting PDF processing...")
        success, fail = service.process_contracts(
            pdf_files=pdf_files,
            show_images=show_images,
            delay_seconds=delay_seconds,
            progress_callback=update_progress
        )
        
        # Complete
        progress_bar.progress(1.0)
        status_text.empty()
        
        st.success(f"""
        ✅ **PDF Processing Complete!**
        
        - ✅ Success: {success} files
        - ❌ Failed: {fail} files
        
        💡 **Next step:** Go to STEP 2 to analyze the data!
        """)
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during processing: {e}")
        st.code(traceback.format_exc())


def run_analysis(json_folder, ap_file, ar_file, use_llm_validation):
    """รันการวิเคราะห์"""
    
    try:
        # Check API Key
        api_key = st.session_state.get('api_key', '')
        if not api_key:
            api_key = check_api_key()
            if not api_key:
                return
        
        service = ProcessingService(api_key)
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(stage, progress_value=None):
            if progress_value is not None:
                progress_bar.progress(progress_value)
            status_text.text(f"⚙️ {stage}")
        
        # Load TTA from JSON
        update_progress("📋 Loading processed data...", 0.1)
        
        json_files = list(json_folder.glob('*.json'))
        
        # Debug: Show what we found
        st.write(f"🔍 Debug: Found {len(json_files)} JSON files in {json_folder}")
        if json_files:
            st.write(f"📂 Sample files: {[f.name for f in json_files[:3]]}")
        
        tta_data = {}
        loaded_count = 0
        error_count = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Support both uppercase and lowercase keys
                    vendor_key = data.get('vendor_code', '')
                    div_code = data.get('division_code', data.get('Division_code', ''))
                    dept_code = data.get('department_code', data.get('Department_code', ''))
                    
                    # Debug first file
                    if loaded_count == 0:
                        st.write(f"📋 First file structure:")
                        st.write(f"   - vendor_code: {vendor_key}")
                        st.write(f"   - division_code: {div_code}")
                        st.write(f"   - department_code: {dept_code}")
                    
                    if vendor_key and div_code and dept_code:
                        tta_key = f"{vendor_key}_{div_code}_{dept_code}"
                        tta_data[tta_key] = data
                        loaded_count += 1
                    else:
                        error_count += 1
                        if error_count <= 3:  # Show first 3 errors
                            st.warning(f"⚠️ {json_file.name}: Missing keys (vendor={vendor_key}, div={div_code}, dept={dept_code})")
                        
            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    st.warning(f"⚠️ Could not load {json_file.name}: {e}")
        
        st.write(f"✅ Loaded: {loaded_count}/{len(json_files)} files")
        
        if not tta_data:
            st.error("❌ Could not load any JSON files")
            st.info(f"""
            **Debug Info:**
            - Found {len(json_files)} JSON files
            - Successfully loaded: {loaded_count}
            - Errors: {error_count}
            - Required fields: vendor_code, division_code (or Division_code), department_code (or Department_code)
            """)
            
            # Show sample JSON structure
            if json_files:
                with st.expander("🔍 View sample JSON"):
                    try:
                        with open(json_files[0], 'r', encoding='utf-8') as f:
                            sample = json.load(f)
                            st.json(sample)
                    except Exception as e:
                        st.error(f"Could not read sample: {e}")
            return
        
        update_progress(f"✅ Loaded {len(tta_data)} contracts", 0.2)
        time.sleep(0.5)
        
        # Set TTA data
        service.recon_system.tta_data = tta_data
        
        # Load AP
        update_progress("💰 Loading AP data...", 0.3)
        ap_loaded = service.recon_system.load_ap_data(ap_file)
        if not ap_loaded:
            st.error("❌ Could not load AP data")
            return
        
        # Load AR
        update_progress("📊 Loading AR data...", 0.4)
        ar_loaded = service.recon_system.load_ar_data(ar_file)
        
        # Calculate allowances
        update_progress("🧮 Calculating allowances...", 0.6)
        calculated = service.recon_system.calculate_allowances()
        if calculated is None:
            st.error("❌ Could not calculate allowances")
            return
        
        # Reconcile with AR
        if ar_loaded:
            if use_llm_validation:
                update_progress("🤖 AI validating AR data...", 0.7)
                service.recon_system.validate_ar_with_llm(service.analyzer)
            
            update_progress("🔄 Reconciling with AR...", 0.8)
            reconciliation = service.recon_system.reconcile_with_ar()
            results = reconciliation
        else:
            st.warning("⚠️ No AR data - showing calculated allowances only")
            results = calculated
        
        # Export
        update_progress("💾 Exporting results...", 0.9)
        output_file = service.recon_system.export_results()
        
        # Save session
        session_name = service.save_session()
        
        # Complete
        progress_bar.progress(1.0)
        status_text.empty()
        
        # Store results
        st.session_state.processing_results = results
        st.session_state.processing_summary = service.get_processing_summary()
        st.session_state.session_name = session_name
        
        st.success(f"""
        ✅ **Analysis Complete!**
        
        - 📊 Records: {len(results) if results is not None else 0}
        - 💾 Report: {output_file}
        
        💡 **View results below or go to "For Auditor" for the dashboard!**
        """)
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {e}")
        st.code(traceback.format_exc())


def show_results_section():
    """แสดงผลลัพธ์"""
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        return
    
    st.markdown("### 🎯 Analysis Results")
    
    results = st.session_state.processing_results
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total Records", len(results))
    
    with col2:
        vendors = results['vendor_code'].nunique() if len(results) > 0 else 0
        st.metric("🏢 Unique Vendors", vendors)
    
    with col3:
        if 'should_collect' in results.columns:
            total = results['should_collect'].sum()
            st.metric("💰 Total Amount", f"฿{total:,.0f}")
    
    # Data preview
    st.markdown("#### 📋 Data Preview (First 20 rows)")
    st.dataframe(
        results.head(20),
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    if len(results) > 0:
        csv = results.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download Full Results (CSV)",
            data=csv,
            file_name=f"analysis_results_{st.session_state.get('session_name', 'export')}.csv",
            mime="text/csv",
            use_container_width=True
        )
