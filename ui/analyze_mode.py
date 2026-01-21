"""
Analyze Mode UI - Professional Version
ออกแบบให้ Formal, มีรายละเอียด, และใช้งานง่าย
"""

import streamlit as st
import os
from pathlib import Path
import time

from services.processing_service import ProcessingService
from config.settings import DIRECTORIES


def show_analyze_mode():
    """แสดง UI สำหรับโหมด Analyze"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0;">🔬 Analysis Mode</h1>
        <p style="color: #e0e0e0; margin: 5px 0 0 0;">Trade Agreement Processing & Reconciliation System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Home", key="back_btn"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Main sections
    show_system_status()
    show_processing_controls()
    show_results_section()


def show_system_status():
    """แสดงสถานะระบบ - Formal Style"""
    
    st.markdown("### 📊 System Status")
    
    # API Status
    api_key = ""
    try:
        if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = api_key
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.session_state.api_key:
            st.success("**AI Engine:** ✅ Connected")
        else:
            st.error("**AI Engine:** ❌ Not Connected")
    
    with col2:
        if not st.session_state.api_key:
            st.warning("⚠️ Gemini API Key is required. Please configure in Streamlit Secrets.")
    
    st.markdown("---")
    
    # Data Sources Status
    st.markdown("### 📁 Data Sources")
    
    pdf_folder = DIRECTORIES['agreements']
    ap_folder = DIRECTORIES['ap']
    ar_folder = DIRECTORIES['ar']
    
    pdf_files = list(pdf_folder.glob('*.pdf'))
    ap_files = list(ap_folder.glob('*.csv'))
    ar_files = list(ar_folder.glob('*.csv'))
    
    # Table format
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📄 Trade Agreements (PDF)**")
        if pdf_files:
            st.info(f"**{len(pdf_files)}** files ready")
            with st.expander("View Files"):
                for idx, f in enumerate(pdf_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("No PDF files found")
    
    with col2:
        st.markdown("**💰 Account Payable (CSV)**")
        if ap_files:
            st.info(f"**{len(ap_files)}** file(s) ready")
            with st.expander("View Files"):
                for idx, f in enumerate(ap_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("No AP files found")
    
    with col3:
        st.markdown("**📊 Account Receivable (CSV)**")
        if ar_files:
            st.info(f"**{len(ar_files)}** file(s) ready")
            with st.expander("View Files"):
                for idx, f in enumerate(ar_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("No AR files found")
    
    st.markdown("---")


def show_processing_controls():
    """ส่วนควบคุมการประมวลผล - มี Slider"""
    
    st.markdown("### ⚙️ Processing Configuration")
    
    # Check API key
    if not st.session_state.get('api_key'):
        st.error("❌ Cannot proceed without API Key. Please check System Status above.")
        return
    
    # Check files
    pdf_files = list(DIRECTORIES['agreements'].glob('*.pdf'))
    ap_files = list(DIRECTORIES['ap'].glob('*.csv'))
    ar_files = list(DIRECTORIES['ar'].glob('*.csv'))
    
    if not pdf_files or not ap_files or not ar_files:
        st.error("❌ Missing required data files. Please check Data Sources above.")
        return
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Processing Options**")
        
        use_llm_validation = st.checkbox(
            "Enable AI Validation",
            value=True,
            help="Use LLM to validate extracted data"
        )
        
        show_images = st.checkbox(
            "Show PDF Images",
            value=False,
            help="Display images during processing (slower)"
        )
    
    with col2:
        st.markdown("**Rate Limiting**")
        
        delay_seconds = st.slider(
            "AI Request Delay (seconds)",
            min_value=10,
            max_value=60,
            value=30,
            step=5,
            help="Delay between AI API calls to avoid rate limits"
        )
        
        st.caption(f"⏱️ Current setting: **{delay_seconds}s** between requests")
    
    st.markdown("---")
    
    # Processing Info
    st.info(f"""
    **Processing Plan:**
    - **{len(pdf_files)}** PDF files will be analyzed
    - Estimated time: ~**{len(pdf_files) * (delay_seconds + 30)}** seconds
    - Results will be reconciled with AP/AR data
    """)
    
    # Run button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            run_processing(
                pdf_files=[str(f) for f in pdf_files],
                ap_file=str(ap_files[0]),
                ar_file=str(ar_files[0]),
                api_key=st.session_state.api_key,
                use_llm_validation=use_llm_validation,
                show_images=show_images,
                delay_seconds=delay_seconds
            )


def run_processing(pdf_files, ap_file, ar_file, api_key, use_llm_validation, show_images, delay_seconds):
    """รันการประมวลผล - Professional Progress Display"""
    
    service = ProcessingService(api_key)
    
    # Create processing container
    st.markdown("---")
    st.markdown("### 🔄 Processing Status")
    
    progress_container = st.container()
    
    with progress_container:
        # Progress elements
        progress_bar = st.progress(0)
        
        col1, col2, col3 = st.columns(3)
        status_text = col1.empty()
        time_text = col2.empty()
        current_file = col3.empty()
        
        detail_box = st.empty()
        
        start_time = time.time()
        
        # PDF progress callback
        def update_pdf_progress(current, total, filename):
            progress = current / total * 0.7
            progress_bar.progress(progress)
            
            elapsed = int(time.time() - start_time)
            
            status_text.metric("Status", "Processing PDFs")
            time_text.metric("Elapsed", f"{elapsed}s")
            current_file.metric("Progress", f"{current}/{total}")
            
            detail_box.info(f"📄 Analyzing: **{filename}**")
        
        # Analysis progress callback
        def update_analysis_progress(stage, progress_value=0.5):
            progress = 0.7 + (progress_value * 0.3)
            progress_bar.progress(progress)
            
            elapsed = int(time.time() - start_time)
            
            status_text.metric("Status", "Analysis")
            time_text.metric("Elapsed", f"{elapsed}s")
            current_file.empty()
            
            detail_box.info(f"🔍 {stage}")
        
        try:
            # Process PDFs
            status_text.info("Initializing...")
            detail_box.info("🔄 Starting PDF processing...")
            
            success, fail = service.process_contracts(
                pdf_files=pdf_files,
                show_images=show_images,
                delay_seconds=delay_seconds,
                progress_callback=update_pdf_progress
            )
            
            # Analysis
            detail_box.info("🔄 Starting reconciliation analysis...")
            
            results = service.run_full_analysis(
                ap_file=ap_file,
                ar_file=ar_file,
                use_llm_validation=use_llm_validation,
                progress_callback=update_analysis_progress
            )
            
            # Save session
            progress_bar.progress(0.95)
            detail_box.info("💾 Saving results...")
            session_name = service.save_session()
            
            # Complete
            progress_bar.progress(1.0)
            elapsed_total = int(time.time() - start_time)
            
            status_text.metric("Status", "✅ Complete")
            time_text.metric("Total Time", f"{elapsed_total}s")
            current_file.empty()
            
            # Store results
            st.session_state.processing_results = results
            st.session_state.processing_summary = service.get_processing_summary()
            st.session_state.session_name = session_name
            st.session_state.processing_stats = {
                'success': success,
                'fail': fail,
                'total_time': elapsed_total,
                'processed_files': success,
                'failed_files': fail
            }
            
            # Success summary
            detail_box.success(f"""
            ✅ **Processing Complete**
            
            - **Processed:** {success} PDF(s)
            - **Failed:** {fail} PDF(s)
            - **Records Generated:** {len(results) if results is not None else 0}
            - **Total Time:** {elapsed_total} seconds
            - **Session ID:** {session_name}
            
            📊 Results are now available in the Results section below.
            """)
            
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            detail_box.error(f"❌ **Processing Error:** {str(e)}")
            
            with st.expander("🔍 Error Details"):
                import traceback
                st.code(traceback.format_exc())


def show_results_section():
    """แสดงผลลัพธ์ - Professional & Detailed"""
    
    st.markdown("---")
    st.markdown("### 📊 Analysis Results")
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        st.info("ℹ️ No results available. Please run processing first.")
        return
    
    results = st.session_state.processing_results
    stats = st.session_state.get('processing_stats', {})
    
    # Summary Header - มีข้อมูลที่สำคัญ
    st.markdown("#### 📈 Processing Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # แสดงเฉพาะที่มีความหมาย
    col1.metric(
        "📄 Processed Files",
        stats.get('processed_files', 0),
        help="Number of PDF files successfully processed"
    )
    
    # แสดง Failed เฉพาะเมื่อมี
    if stats.get('failed_files', 0) > 0:
        col2.metric(
            "❌ Failed",
            stats.get('failed_files', 0),
            delta=f"-{stats.get('failed_files', 0)}",
            delta_color="inverse",
            help="Files that failed processing"
        )
    else:
        col2.metric(
            "✅ Success Rate",
            "100%",
            help="All files processed successfully"
        )
    
    col3.metric(
        "📊 Total Records",
        len(results),
        help="Total allowance records extracted"
    )
    
    if 'vendor_code' in results.columns:
        col4.metric(
            "🏢 Unique Vendors",
            results['vendor_code'].nunique(),
            help="Number of distinct vendors"
        )
    
    col5.metric(
        "⏱️ Processing Time",
        f"{stats.get('total_time', 0)}s",
        help="Total time taken"
    )
    
    st.markdown("---")
    
    # Data Preview & Analysis
    st.markdown("#### 🔍 Detailed Results")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'vendor_code' in results.columns:
            vendors = ['All Vendors'] + sorted(results['vendor_code'].unique().tolist())
            selected_vendor = st.selectbox("Filter by Vendor:", vendors, key="vendor_filter")
        else:
            selected_vendor = 'All Vendors'
    
    with col2:
        if 'status' in results.columns:
            statuses = ['All Status'] + sorted(results['status'].unique().tolist())
            selected_status = st.selectbox("Filter by Status:", statuses, key="status_filter")
        else:
            selected_status = 'All Status'
    
    with col3:
        if 'category_code' in results.columns:
            categories = ['All Categories'] + sorted(results['category_code'].unique().tolist())
            selected_category = st.selectbox("Filter by Category:", categories, key="category_filter")
        else:
            selected_category = 'All Categories'
    
    # Apply filters
    filtered_results = results.copy()
    
    if selected_vendor != 'All Vendors':
        filtered_results = filtered_results[filtered_results['vendor_code'] == selected_vendor]
    
    if selected_status != 'All Status':
        filtered_results = filtered_results[filtered_results['status'] == selected_status]
    
    if selected_category != 'All Categories':
        filtered_results = filtered_results[filtered_results['category_code'] == selected_category]
    
    # Display filtered count
    st.caption(f"Showing **{len(filtered_results)}** of **{len(results)}** records")
    
    # Data table
    st.dataframe(
        filtered_results,
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    # Actions
    st.markdown("---")
    st.markdown("#### 💾 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = filtered_results.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"analysis_results_{st.session_state.get('session_name', 'export')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        excel_buffer = filtered_results.to_excel(index=False, engine='openpyxl')
        st.download_button(
            label="📊 Download as Excel",
            data=excel_buffer,
            file_name=f"analysis_results_{st.session_state.get('session_name', 'export')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            disabled=True,
            help="Excel export coming soon"
        )
    
    with col3:
        if st.button("📋 View in Dashboard", use_container_width=True):
            st.session_state.mode = 'auditor'
            st.rerun()
