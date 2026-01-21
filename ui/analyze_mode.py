"""
Analyze Mode UI - Final Version
3 Sheets: Calculated, Reconciliation, Summary
Status: English with colors only (no icons)
Numbers: 2 decimals with comma separator
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
    
    if st.button("← Back to Home", key="back_btn"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    show_system_status()
    show_processing_controls()
    show_results_section()


def show_system_status():
    """แสดงสถานะระบบ"""
    
    st.markdown("### 📊 System Status")
    
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
            st.warning("⚠️ Gemini API Key required. Configure in Secrets.")
    
    st.markdown("---")
    
    st.markdown("### 📁 Data Sources")
    
    pdf_files = list(DIRECTORIES['agreements'].glob('*.pdf'))
    ap_files = list(DIRECTORIES['ap'].glob('*.csv'))
    ar_files = list(DIRECTORIES['ar'].glob('*.csv'))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📄 Trade Agreements (PDF)**")
        if pdf_files:
            st.info(f"**{len(pdf_files)}** files ready")
            with st.expander("View Files"):
                for idx, f in enumerate(pdf_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("No PDF files")
    
    with col2:
        st.markdown("**💰 Account Payable (CSV)**")
        if ap_files:
            st.info(f"**{len(ap_files)}** file(s) ready")
        else:
            st.error("No AP files")
    
    with col3:
        st.markdown("**📊 Account Receivable (CSV)**")
        if ar_files:
            st.info(f"**{len(ar_files)}** file(s) ready")
        else:
            st.error("No AR files")
    
    st.markdown("---")


def show_processing_controls():
    """ส่วนควบคุม"""
    
    st.markdown("### ⚙️ Processing Configuration")
    
    if not st.session_state.get('api_key'):
        st.error("❌ Cannot proceed without API Key.")
        return
    
    pdf_files = list(DIRECTORIES['agreements'].glob('*.pdf'))
    ap_files = list(DIRECTORIES['ap'].glob('*.csv'))
    ar_files = list(DIRECTORIES['ar'].glob('*.csv'))
    
    if not pdf_files or not ap_files or not ar_files:
        st.error("❌ Missing required files.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Options**")
        use_llm = st.checkbox("Enable AI Validation", value=True)
        show_images = st.checkbox("Show PDF Images", value=False)
    
    with col2:
        st.markdown("**Rate Limiting**")
        delay_seconds = st.slider(
            "AI Request Delay (seconds)",
            min_value=10,
            max_value=60,
            value=30,
            step=5
        )
        st.caption(f"⏱️ **{delay_seconds}s** between requests")
    
    st.markdown("---")
    
    st.info(f"""
    **Processing Plan:**
    - {len(pdf_files)} PDFs → ~{len(pdf_files) * (delay_seconds + 30)}s
    - Reconciliation with AP/AR data
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            run_processing(
                pdf_files=[str(f) for f in pdf_files],
                ap_file=str(ap_files[0]),
                ar_file=str(ar_files[0]),
                api_key=st.session_state.api_key,
                use_llm_validation=use_llm,
                show_images=show_images,
                delay_seconds=delay_seconds
            )


def run_processing(pdf_files, ap_file, ar_file, api_key, use_llm_validation, show_images, delay_seconds):
    """รันการประมวลผล"""
    
    service = ProcessingService(api_key)
    
    st.markdown("---")
    st.markdown("### 🔄 Processing Status")
    
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
        status_text.metric("Status", "Processing")
        time_text.metric("Elapsed", f"{elapsed}s")
        current_file.metric("Progress", f"{current}/{total}")
        detail_box.info(f"📄 {filename}")
    
    def update_analysis_progress(stage, progress_value=0.5):
        progress = 0.7 + (progress_value * 0.3)
        progress_bar.progress(progress)
        elapsed = int(time.time() - start_time)
        status_text.metric("Status", "Analysis")
        time_text.metric("Elapsed", f"{elapsed}s")
        current_file.empty()
        detail_box.info(f"🔍 {stage}")
    
    try:
        success, fail = service.process_contracts(
            pdf_files=pdf_files,
            show_images=show_images,
            delay_seconds=delay_seconds,
            progress_callback=update_pdf_progress
        )
        
        results = service.run_full_analysis(
            ap_file=ap_file,
            ar_file=ar_file,
            use_llm_validation=use_llm_validation,
            progress_callback=update_analysis_progress
        )
        
        progress_bar.progress(0.95)
        session_name = service.save_session()
        
        progress_bar.progress(1.0)
        elapsed_total = int(time.time() - start_time)
        
        status_text.metric("Status", "✅ Done")
        time_text.metric("Time", f"{elapsed_total}s")
        
        # แปลง Status เป็นภาษาอังกฤษ (เอา icon ออก)
        if results is not None and 'status' in results.columns:
            results['status'] = results['status'].str.replace('✅ ', '').str.replace('❌ ', '').str.replace('⚠️ ', '')
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
            'total_time': elapsed_total
        }
        
        detail_box.success(f"✅ Complete! {len(results)} records in {elapsed_total}s")
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        detail_box.error(f"❌ Error: {e}")
        with st.expander("Details"):
            import traceback
            st.code(traceback.format_exc())


def format_number(value):
    """Format number: 2 decimals + comma"""
    try:
        return f"{float(value):,.2f}"
    except:
        return value


def create_calculated_sheet(results):
    """Sheet 1: Calculated - คำนวณจากสัญญา"""
    calc_data = []
    
    for _, row in results.iterrows():
        calc_data.append({
            'vendor_code': row.get('vendor_code', ''),
            'vendor_name': row.get('vendor_name', ''),
            'division': row.get('Division', ''),
            'department': row.get('Department', ''),
            'tta_key': row.get('tta_key', ''),
            'year': row.get('year', 2023),
            'purchase_amount': row.get('purchase_amount', 0),
            'category_code': row.get('category_code', ''),
            'category_name': row.get('category_name', ''),
            'rate_percent': row.get('rate_percent', None),
            'fix_amount': row.get('fix_amount', None),
            'calculated_amount': row.get('should_collect', 0),
            'calculation_type': row.get('calculation_type', ''),
            'description': row.get('description', ''),
            'payment_terms': row.get('payment_terms', '')
        })
    
    df = pd.DataFrame(calc_data)
    
    # Format numbers
    num_cols = ['purchase_amount', 'rate_percent', 'fix_amount', 'calculated_amount']
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{float(x):,.2f}" if pd.notna(x) and x != '' else '')
    
    return df


def create_reconciliation_sheet(results):
    """Sheet 2: Reconciliation - เปรียบเทียบ"""
    recon_data = []
    
    for _, row in results.iterrows():
        recon_data.append({
            'tta_key': row.get('tta_key', ''),
            'vendor_code': row.get('vendor_code', ''),
            'vendor_name': row.get('vendor_name', ''),
            'category_code': row.get('category_code', ''),
            'category_name': row.get('category_name', ''),
            'should_collect': row.get('should_collect', 0),
            'actually_collected': row.get('actually_collected', 0),
            'difference': row.get('difference', 0),
            'status': row.get('status', ''),
            'variance_pct': row.get('variance_pct', 0)
        })
    
    df = pd.DataFrame(recon_data)
    
    # Format numbers
    num_cols = ['should_collect', 'actually_collected', 'difference', 'variance_pct']
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{float(x):,.2f}" if pd.notna(x) else '')
    
    return df


def create_summary_sheet(results):
    """Sheet 3: Summary - สรุปต่อ Vendor"""
    summary_data = []
    
    if 'vendor_code' in results.columns:
        for vendor in results['vendor_code'].unique():
            vendor_data = results[results['vendor_code'] == vendor]
            
            should = vendor_data['should_collect'].sum() if 'should_collect' in vendor_data.columns else 0
            actually = vendor_data['actually_collected'].sum() if 'actually_collected' in vendor_data.columns else 0
            diff = vendor_data['difference'].sum() if 'difference' in vendor_data.columns else 0
            
            # Status
            if diff == 0:
                status = 'MATCH'
            elif diff > 0:
                status = 'OVER'
            else:
                status = 'UNDER'
            
            # Variance %
            variance = (diff / should * 100) if should != 0 else 0
            
            summary_data.append({
                'vendor_code': vendor,
                'vendor_name': vendor_data['vendor_name'].iloc[0] if 'vendor_name' in vendor_data.columns else '',
                'should_collect': should,
                'actually_collected': actually,
                'difference': diff,
                'status': status,
                'variance_pct': variance
            })
    
    df = pd.DataFrame(summary_data)
    
    # Format numbers
    num_cols = ['should_collect', 'actually_collected', 'difference', 'variance_pct']
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{float(x):,.2f}" if pd.notna(x) else '')
    
    return df


def export_excel_3sheets(results):
    """Export Excel 3 sheets ตามรูปแบบไฟล์ตัวอย่าง"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Calculated
        calc_df = create_calculated_sheet(results)
        calc_df.to_excel(writer, sheet_name='Calculated', index=False)
        
        # Sheet 2: Reconciliation
        recon_df = create_reconciliation_sheet(results)
        recon_df.to_excel(writer, sheet_name='Reconciliation', index=False)
        
        # Sheet 3: Summary
        summary_df = create_summary_sheet(results)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return output


def show_results_section():
    """แสดงผลลัพธ์"""
    
    st.markdown("---")
    st.markdown("### 📊 Analysis Results")
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        st.info("ℹ️ No results yet. Run processing first.")
        return
    
    results = st.session_state.processing_results
    stats = st.session_state.get('processing_stats', {})
    
    # Summary Metrics
    st.markdown("#### 📈 Processing Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("📄 Files", stats.get('success', 0))
    
    if stats.get('fail', 0) > 0:
        col2.metric("❌ Failed", stats.get('fail', 0))
    else:
        col2.metric("✅ Success", "100%")
    
    col3.metric("📊 Records", len(results))
    col4.metric("⏱️ Time", f"{stats.get('total_time', 0)}s")
    
    st.markdown("---")
    
    # 3 Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Calculated", "🔍 Reconciliation", "📊 Summary"])
    
    with tab1:
        st.markdown("#### 📋 Calculated (From TTA)")
        calc_df = create_calculated_sheet(results)
        
        if len(calc_df) > 0:
            st.dataframe(calc_df, use_container_width=True, height=500)
        else:
            st.info("No data")
    
    with tab2:
        st.markdown("#### 🔍 Reconciliation (Comparison)")
        recon_df = create_reconciliation_sheet(results)
        
        if len(recon_df) > 0:
            # Color only Status column
            def color_status(val):
                if val == 'MATCH':
                    return 'background-color: #FFD700; color: black'  # Yellow
                elif val == 'OVER':
                    return 'background-color: #FF6B6B; color: white'  # Red
                elif val == 'UNDER':
                    return 'background-color: #4ECDC4; color: white'  # Teal
                return ''
            
            # Apply color to Status column only
            styled_df = recon_df.style.applymap(color_status, subset=['status'])
            
            st.dataframe(styled_df, use_container_width=True, height=500)
        else:
            st.info("No data")
    
    with tab3:
        st.markdown("#### 📊 Summary (By Vendor)")
        summary_df = create_summary_sheet(results)
        
        if len(summary_df) > 0:
            # Color Status column
            def color_status(val):
                if val == 'MATCH':
                    return 'background-color: #FFD700; color: black'
                elif val == 'OVER':
                    return 'background-color: #FF6B6B; color: white'
                elif val == 'UNDER':
                    return 'background-color: #4ECDC4; color: white'
                return ''
            
            styled_summary = summary_df.style.applymap(color_status, subset=['status'])
            
            st.dataframe(styled_summary, use_container_width=True, height=500)
        else:
            st.info("No data")
    
    # Export
    st.markdown("---")
    st.markdown("#### 💾 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = results.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 CSV (Raw)",
            data=csv,
            file_name=f"results_{st.session_state.get('session_name', 'export')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        excel_buffer = export_excel_3sheets(results)
        st.download_button(
            "📊 Excel (3 Sheets)",
            data=excel_buffer,
            file_name=f"TTA_Reconciliation_{st.session_state.get('session_name', 'export')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        if st.button("📋 Dashboard", use_container_width=True):
            st.session_state.mode = 'auditor'
            st.rerun()
