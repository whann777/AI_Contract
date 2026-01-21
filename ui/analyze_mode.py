"""
Analyze Mode UI - Professional Version with 3-Sheet Export
"""

import streamlit as st
import os
from pathlib import Path
import time
import pandas as pd
from io import BytesIO

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
    """แสดงสถานะระบบ"""
    
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
    """ส่วนควบคุมการประมวลผล"""
    
    st.markdown("### ⚙️ Processing Configuration")
    
    if not st.session_state.get('api_key'):
        st.error("❌ Cannot proceed without API Key. Please check System Status above.")
        return
    
    pdf_files = list(DIRECTORIES['agreements'].glob('*.pdf'))
    ap_files = list(DIRECTORIES['ap'].glob('*.csv'))
    ar_files = list(DIRECTORIES['ar'].glob('*.csv'))
    
    if not pdf_files or not ap_files or not ar_files:
        st.error("❌ Missing required data files. Please check Data Sources above.")
        return
    
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
    
    st.info(f"""
    **Processing Plan:**
    - **{len(pdf_files)}** PDF files will be analyzed
    - Estimated time: ~**{len(pdf_files) * (delay_seconds + 30)}** seconds
    - Results will be reconciled with AP/AR data
    """)
    
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
    """รันการประมวลผล"""
    
    service = ProcessingService(api_key)
    
    st.markdown("---")
    st.markdown("### 🔄 Processing Status")
    
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        
        col1, col2, col3 = st.columns(3)
        status_text = col1.empty()
        time_text = col2.empty()
        current_file = col3.empty()
        
        detail_box = st.empty()
        
        start_time = time.time()
        
        def update_pdf_progress(current, total, filename):
            progress = current / total * 0.7
            progress_bar.progress(progress)
            
            elapsed = int(time.time() - start_time)
            
            status_text.metric("Status", "Processing PDFs")
            time_text.metric("Elapsed", f"{elapsed}s")
            current_file.metric("Progress", f"{current}/{total}")
            
            detail_box.info(f"📄 Analyzing: **{filename}**")
        
        def update_analysis_progress(stage, progress_value=0.5):
            progress = 0.7 + (progress_value * 0.3)
            progress_bar.progress(progress)
            
            elapsed = int(time.time() - start_time)
            
            status_text.metric("Status", "Analysis")
            time_text.metric("Elapsed", f"{elapsed}s")
            current_file.empty()
            
            detail_box.info(f"🔍 {stage}")
        
        try:
            status_text.info("Initializing...")
            detail_box.info("🔄 Starting PDF processing...")
            
            success, fail = service.process_contracts(
                pdf_files=pdf_files,
                show_images=show_images,
                delay_seconds=delay_seconds,
                progress_callback=update_pdf_progress
            )
            
            detail_box.info("🔄 Starting reconciliation analysis...")
            
            results = service.run_full_analysis(
                ap_file=ap_file,
                ar_file=ar_file,
                use_llm_validation=use_llm_validation,
                progress_callback=update_analysis_progress
            )
            
            progress_bar.progress(0.95)
            detail_box.info("💾 Saving results...")
            session_name = service.save_session()
            
            progress_bar.progress(1.0)
            elapsed_total = int(time.time() - start_time)
            
            status_text.metric("Status", "✅ Complete")
            time_text.metric("Total Time", f"{elapsed_total}s")
            current_file.empty()
            
            # แปลง Status เป็นภาษาอังกฤษ
            if results is not None and 'status' in results.columns:
                results['status'] = results['status'].map({
                    'ครบ': 'MATCH',
                    'เกิน': 'OVER',
                    'ขาด': 'UNDER'
                }).fillna(results['status'])
            
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
            
            detail_box.success(f"""
            ✅ **Processing Complete**
            
            - **Processed:** {success} PDF(s)
            - **Failed:** {fail} PDF(s)
            - **Records Generated:** {len(results) if results is not None else 0}
            - **Total Time:** {elapsed_total} seconds
            - **Session ID:** {session_name}
            
            📊 Results are now available below.
            """)
            
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            detail_box.error(f"❌ **Processing Error:** {str(e)}")
            
            with st.expander("🔍 Error Details"):
                import traceback
                st.code(traceback.format_exc())


def create_summary_sheet(results):
    """สร้าง Sheet 1: Summary - สรุปรายการที่ได้จากเอกสาร"""
    summary_data = []
    
    if 'tta_key' in results.columns:
        # Group by TTA
        for tta_key in results['tta_key'].unique():
            tta_data = results[results['tta_key'] == tta_key]
            
            summary_data.append({
                'TTA Key': tta_key,
                'Vendor Code': tta_data['vendor_code'].iloc[0] if 'vendor_code' in tta_data.columns else '',
                'Vendor Name': tta_data['vendor_name'].iloc[0] if 'vendor_name' in tta_data.columns else '',
                'Total Categories': len(tta_data),
                'Total Should Collect': tta_data['should_collect'].sum() if 'should_collect' in tta_data.columns else 0,
                'Total Actually Collected': tta_data['actually_collected'].sum() if 'actually_collected' in tta_data.columns else 0,
                'Total Difference': tta_data['difference'].sum() if 'difference' in tta_data.columns else 0
            })
    
    return pd.DataFrame(summary_data)


def create_vendor_summary_sheet(results):
    """สร้าง Sheet 3: Vendor Summary - สรุปภาพรวมแต่ละ Vendor"""
    vendor_summary = []
    
    if 'vendor_code' in results.columns:
        for vendor in results['vendor_code'].unique():
            vendor_data = results[results['vendor_code'] == vendor]
            
            should_collect = vendor_data['should_collect'].sum() if 'should_collect' in vendor_data.columns else 0
            actually_collected = vendor_data['actually_collected'].sum() if 'actually_collected' in vendor_data.columns else 0
            difference = vendor_data['difference'].sum() if 'difference' in vendor_data.columns else 0
            
            # นับสถานะ
            status_counts = vendor_data['status'].value_counts().to_dict() if 'status' in vendor_data.columns else {}
            
            vendor_summary.append({
                'Vendor Code': vendor,
                'Vendor Name': vendor_data['vendor_name'].iloc[0] if 'vendor_name' in vendor_data.columns else '',
                'Total Categories': len(vendor_data),
                'Should Collect': should_collect,
                'Actually Collected': actually_collected,
                'Difference': difference,
                'MATCH Count': status_counts.get('MATCH', 0),
                'OVER Count': status_counts.get('OVER', 0),
                'UNDER Count': status_counts.get('UNDER', 0),
                'Overall Status': 'MATCH' if difference == 0 else ('OVER' if difference > 0 else 'UNDER')
            })
    
    return pd.DataFrame(vendor_summary)


def export_to_excel_3sheets(results):
    """Export Excel 3 sheets"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: TTA Summary
        summary_df = create_summary_sheet(results)
        summary_df.to_excel(writer, sheet_name='TTA Summary', index=False)
        
        # Sheet 2: Detailed Results
        results.to_excel(writer, sheet_name='Detailed Results', index=False)
        
        # Sheet 3: Vendor Summary
        vendor_summary_df = create_vendor_summary_sheet(results)
        vendor_summary_df.to_excel(writer, sheet_name='Vendor Summary', index=False)
    
    output.seek(0)
    return output


def show_results_section():
    """แสดงผลลัพธ์"""
    
    st.markdown("---")
    st.markdown("### 📊 Analysis Results")
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        st.info("ℹ️ No results available. Please run processing first.")
        return
    
    results = st.session_state.processing_results
    stats = st.session_state.get('processing_stats', {})
    
    # Summary Header
    st.markdown("#### 📈 Processing Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric(
        "📄 Processed Files",
        stats.get('processed_files', 0),
        help="Number of PDF files successfully processed"
    )
    
    if stats.get('failed_files', 0) > 0:
        col2.metric(
            "❌ Failed",
            stats.get('failed_files', 0),
            delta=f"-{stats.get('failed_files', 0)}",
            delta_color="inverse"
        )
    else:
        col2.metric(
            "✅ Success Rate",
            "100%"
        )
    
    col3.metric(
        "📊 Total Records",
        len(results)
    )
    
    if 'vendor_code' in results.columns:
        col4.metric(
            "🏢 Unique Vendors",
            results['vendor_code'].nunique()
        )
    
    col5.metric(
        "⏱️ Processing Time",
        f"{stats.get('total_time', 0)}s"
    )
    
    st.markdown("---")
    
    # Tabs for 3 sheets
    tab1, tab2, tab3 = st.tabs(["📋 TTA Summary", "📊 Detailed Results", "🏢 Vendor Summary"])
    
    with tab1:
        st.markdown("#### 📋 TTA Summary")
        summary_df = create_summary_sheet(results)
        
        if len(summary_df) > 0:
            st.dataframe(summary_df, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("No summary data available")
    
    with tab2:
        st.markdown("#### 📊 Detailed Results")
        
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
        
        st.caption(f"Showing **{len(filtered_results)}** of **{len(results)}** records")
        
        # Color-code status
        def highlight_status(row):
            if 'status' not in row.index:
                return [''] * len(row)
            
            status = row['status']
            if status == 'MATCH':
                return ['background-color: #FFD700'] * len(row)  # Yellow
            elif status == 'OVER':
                return ['background-color: #FF6B6B'] * len(row)  # Red
            elif status == 'UNDER':
                return ['background-color: #4ECDC4'] * len(row)  # Green/Teal
            return [''] * len(row)
        
        styled_df = filtered_results.style.apply(highlight_status, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=400)
    
    with tab3:
        st.markdown("#### 🏢 Vendor Summary")
        vendor_summary_df = create_vendor_summary_sheet(results)
        
        if len(vendor_summary_df) > 0:
            
            def highlight_vendor_status(row):
                if 'Overall Status' not in row.index:
                    return [''] * len(row)
                
                status = row['Overall Status']
                if status == 'MATCH':
                    return ['background-color: #FFD700'] * len(row)
                elif status == 'OVER':
                    return ['background-color: #FF6B6B'] * len(row)
                elif status == 'UNDER':
                    return ['background-color: #4ECDC4'] * len(row)
                return [''] * len(row)
            
            styled_vendor_df = vendor_summary_df.style.apply(highlight_vendor_status, axis=1)
            st.dataframe(styled_vendor_df, use_container_width=True, hide_index=True, height=400)
        else:
            st.info("No vendor summary available")
    
    # Export Options
    st.markdown("---")
    st.markdown("#### 💾 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = results.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download CSV (Details Only)",
            data=csv,
            file_name=f"analysis_results_{st.session_state.get('session_name', 'export')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        excel_buffer = export_to_excel_3sheets(results)
        st.download_button(
            label="📊 Download Excel (3 Sheets)",
            data=excel_buffer,
            file_name=f"analysis_results_{st.session_state.get('session_name', 'export')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        if st.button("📋 View in Dashboard", use_container_width=True):
            st.session_state.mode = 'auditor'
            st.rerun()
