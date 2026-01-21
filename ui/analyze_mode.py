"""
Analyze Mode UI - ส่วนที่ 1: สำหรับประมวลผลและวิเคราะห์
แก้ไขให้อ่านไฟล์จาก data/ โดยตรง ไม่ต้องอัปโหลด
"""

import streamlit as st
import os
from pathlib import Path
import time
import pandas as pd

from services.processing_service import ProcessingService
from config.settings import DIRECTORIES


def show_analyze_mode():
    """
    แสดง UI สำหรับโหมด Analyze
    อ่านไฟล์จากโฟลเดอร์ data/ โดยตรง
    """
    st.title("🔬 For Analyze: ประมวลผลสัญญาและข้อมูล")
    
    # Back button
    if st.button("← กลับหน้าแรก"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Get API Key from Streamlit Secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception as e:
        st.error("❌ ไม่พบ API Key ใน Streamlit Secrets")
        st.info("💡 กรุณาตั้งค่า GEMINI_API_KEY ใน Settings → Secrets")
        st.code("""
        # ใน Streamlit Cloud:
        # Settings → Secrets → เพิ่ม:
        GEMINI_API_KEY = "your_api_key_here"
        """)
        return
    
    # Check files in data/ folders
    st.markdown("### 📁 ไฟล์ที่พร้อมประมวลผล")
    
    # Check PDF files
    pdf_files = list(DIRECTORIES['agreements'].glob("*.pdf"))
    
    # Check AP files  
    ap_files = []
    for pattern in ['*.csv', '*.CSV']:
        ap_files.extend(list(DIRECTORIES['ap'].glob(pattern)))
    
    # Check AR files
    ar_files = []
    for pattern in ['*.csv', '*.CSV']:
        ar_files.extend(list(DIRECTORIES['ar'].glob(pattern)))
    
    # Display file status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if pdf_files:
            st.success(f"✅ PDF สัญญา: {len(pdf_files)} ไฟล์")
            with st.expander("📋 รายการไฟล์ PDF"):
                for pdf in pdf_files:
                    st.text(f"• {pdf.name}")
        else:
            st.error("❌ ไม่พบไฟล์ PDF")
            st.info("💡 ใส่ไฟล์ PDF ในโฟลเดอร์ `data/agreements/` ใน GitHub")
    
    with col2:
        if ap_files:
            st.success(f"✅ AP CSV: {len(ap_files)} ไฟล์")
            with st.expander("📋 รายการไฟล์ AP"):
                for ap in ap_files:
                    st.text(f"• {ap.name}")
        else:
            st.error("❌ ไม่พบไฟล์ AP")
            st.info("💡 ใส่ไฟล์ CSV ในโฟลเดอร์ `data/ap/` ใน GitHub")
    
    with col3:
        if ar_files:
            st.success(f"✅ AR CSV: {len(ar_files)} ไฟล์")
            with st.expander("📋 รายการไฟล์ AR"):
                for ar in ar_files:
                    st.text(f"• {ar.name}")
        else:
            st.warning("⚠️ ไม่พบไฟล์ AR (ไม่บังคับ)")
    
    st.markdown("---")
    
    # Processing options
    st.markdown("### ⚙️ ตัวเลือกการประมวลผล")
    
    col1, col2 = st.columns(2)
    
    with col1:
        delay_seconds = st.slider(
            "หน่วงเวลาระหว่าง PDF (วินาที)",
            min_value=0,
            max_value=60,
            value=30,
            help="ป้องกัน API quota limit"
        )
        
        use_llm_validation = st.checkbox(
            "ใช้ LLM ตรวจสอบ REF_TYPE",
            value=True,
            help="ใช้ AI ตรวจสอบความถูกต้องของ category"
        )
    
    with col2:
        show_pdf_images = st.checkbox(
            "แสดงภาพ PDF (Debug)",
            value=False,
            help="แสดงภาพตัวอย่างจาก PDF"
        )
    
    st.markdown("---")
    
    # Run button
    st.markdown("### 🚀 เริ่มประมวลผล")
    
    # Check prerequisites
    can_run = len(pdf_files) > 0 and len(ap_files) > 0
    
    if not can_run:
        st.warning("⚠️ กรุณาใส่ไฟล์ให้ครบ")
        missing = []
        if len(pdf_files) == 0:
            missing.append("- PDF สัญญา → `data/agreements/`")
        if len(ap_files) == 0:
            missing.append("- AP CSV → `data/ap/`")
        
        for item in missing:
            st.markdown(item)
    
    if st.button("🚀 เริ่มประมวลผล", disabled=not can_run, use_container_width=True, type="primary"):
        run_processing(
            api_key=api_key,
            pdf_files=[str(f) for f in pdf_files],
            ap_file=str(ap_files[0]) if ap_files else None,
            ar_file=str(ar_files[0]) if ar_files else None,
            delay_seconds=delay_seconds,
            show_pdf_images=show_pdf_images,
            use_llm_validation=use_llm_validation
        )
    
    # Show results if available
    if 'processing_results' in st.session_state:
        show_results_section()


def run_processing(api_key, pdf_files, ap_file, ar_file, delay_seconds, show_pdf_images, use_llm_validation):
    """รันกระบวนการประมวลผล"""
    
    service = ProcessingService(
        api_key=api_key,
        base_folder=str(DIRECTORIES['agreements'].parent)
    )
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_steps = len(pdf_files) + 5
    current_step = 0
    
    def update_progress(current, total, filename):
        nonlocal current_step
        current_step += 1
        progress = current_step / total_steps
        progress_bar.progress(min(progress, 0.95))
        status_text.text(f"📄 {filename} ({current}/{total})")
    
    # Process PDFs
    status_text.text("📄 กำลังประมวลผล PDF...")
    success, fail = service.process_contracts(
        pdf_files=pdf_files,
        show_images=show_pdf_images,
        delay_seconds=delay_seconds,
        progress_callback=update_progress
    )
    
    # Run analysis
    current_step += 1
    progress_bar.progress(min(current_step / total_steps, 0.95))
    status_text.text("⚙️ กำลังวิเคราะห์...")
    
    def update_analysis(message):
        nonlocal current_step
        current_step += 1
        progress_bar.progress(min(current_step / total_steps, 0.98))
        status_text.text(message)
    
    results = service.run_full_analysis(
        ap_file=ap_file,
        ar_file=ar_file,
        use_llm_validation=use_llm_validation,
        progress_callback=update_analysis
    )
    
    progress_bar.progress(1.0)
    status_text.text("✅ เสร็จสิ้น!")
    
    # Store in session state
    st.session_state.processing_results = results
    st.session_state.processing_summary = service.get_processing_summary()
    st.session_state.recon_system = service.recon_system  # เพิ่มบรรทัดนี้!
    
    st.success(f"✅ สำเร็จ! PDF: {success}, รายการ: {len(results) if results is not None else 0}")
    
    time.sleep(1)
    st.rerun()


def show_results_section():
    """แสดงผลลัพธ์"""
    st.markdown("---")
    st.markdown("### 📊 ผลลัพธ์")
    
    results = st.session_state.get('processing_results')
    summary = st.session_state.get('processing_summary', {})
    
    if results is None:
        st.info("ℹ️ ยังไม่มีผลลัพธ์")
        return
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("PDF", summary.get('pdfs_processed', 0))
    col2.metric("รายการ", summary.get('total_records', 0))
    
    if 'total_should_collect' in summary:
        col3.metric("ควรเก็บ", f"{summary['total_should_collect']:,.0f} ฿")
    
    if 'total_actually_collected' in summary:
        col4.metric("เก็บจริง", f"{summary['total_actually_collected']:,.0f} ฿")
    
    st.markdown("---")
    
    # Table
    if len(results) > 0:
        st.dataframe(results, use_container_width=True, height=400)
        
        # Download
        st.markdown("#### 💾 ดาวน์โหลด")
        
        # Import reporting service
        from services.reporting_service import ReportingService
        
        reporter = ReportingService()
        
        # Get data from reconciliation system
        recon_system = st.session_state.get('recon_system')
        
        if recon_system:
            calculated = recon_system.calculated_allowances
            summary = recon_system.generate_summary_report()
        else:
            calculated = None
            summary = None
        
        # Generate Excel file in memory
        excel_bytes = reporter.export_to_excel_bytes(
            reconciliation_df=results,
            calculated_df=calculated,
            summary_df=summary
        )
        
        # Generate filename
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TTA_Reconciliation_{timestamp}.xlsx"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "📥 ดาวน์โหลด Excel",
                data=excel_bytes,
                file_name=filename,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )
        
        with col2:
            csv_bytes = reporter.export_to_csv_bytes(results)
            csv_filename = f"TTA_Reconciliation_{timestamp}.csv"
            
            st.download_button(
                "📥 ดาวน์โหลด CSV",
                data=csv_bytes,
                file_name=csv_filename,
                mime='text/csv',
                use_container_width=True
            )
    else:
        st.warning("⚠️ ไม่มีข้อมูล")
