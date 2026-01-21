"""
Analyze Mode UI - ส่วนที่ 1: สำหรับประมวลผลและวิเคราะห์
เวอร์ชันง่ายๆ ไม่ซับซ้อน
"""

import streamlit as st
import os
from pathlib import Path
import time

from services.processing_service import ProcessingService
from config.settings import DIRECTORIES


def show_analyze_mode():
    """แสดง UI สำหรับโหมด Analyze"""
    st.title("🔬 For Analyze: ประมวลผลสัญญาและข้อมูล")
    
    # Back button
    if st.button("← กลับหน้าแรก"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Main sections
    show_file_status_section()
    show_processing_section()
    show_results_section()


def show_file_status_section():
    """แสดงสถานะไฟล์"""
    st.markdown("### 📁 สถานะไฟล์ข้อมูล")
    
    st.info("""
    💡 **ไฟล์ทั้งหมดถูกเก็บไว้ที่ GitHub แล้ว**
    
    - 📄 `data/agreements/` - ไฟล์สัญญา PDF
    - 💰 `data/ap/` - ไฟล์ Account Payable (CSV)
    - 📊 `data/ar/` - ไฟล์ Account Receivable (CSV)
    """)
    
    col1, col2, col3 = st.columns(3)
    
    # PDF files
    with col1:
        pdf_folder = DIRECTORIES['agreements']
        pdf_files = list(pdf_folder.glob('*.pdf'))
        
        st.metric("📄 ไฟล์ PDF", len(pdf_files))
        
        if pdf_files:
            with st.expander("รายการ"):
                for idx, f in enumerate(pdf_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์")
    
    # AP files
    with col2:
        ap_folder = DIRECTORIES['ap']
        ap_files = list(ap_folder.glob('*.csv'))
        
        st.metric("💰 ไฟล์ AP", len(ap_files))
        
        if ap_files:
            with st.expander("รายการ"):
                for idx, f in enumerate(ap_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์")
    
    # AR files
    with col3:
        ar_folder = DIRECTORIES['ar']
        ar_files = list(ar_folder.glob('*.csv'))
        
        st.metric("📊 ไฟล์ AR", len(ar_files))
        
        if ar_files:
            with st.expander("รายการ"):
                for idx, f in enumerate(ar_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์")
    
    st.markdown("---")


def show_processing_section():
    """ส่วนรันประมวลผล"""
    st.markdown("### ⚙️ รันประมวลผล")
    
    # ดึง API Key
    api_key = ""
    try:
        if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = api_key
    
    # แสดงสถานะ API Key
    if st.session_state.api_key:
        st.success("✅ Gemini API Key พร้อมใช้งาน")
    else:
        st.error("❌ ไม่พบ Gemini API Key")
        st.info("กรุณาตั้งค่า GEMINI_API_KEY ใน Secrets")
        return
    
    # Options
    col1, col2 = st.columns(2)
    
    with col1:
        use_llm = st.checkbox("🤖 ใช้ AI ตรวจสอบ", value=True)
    
    with col2:
        show_images = st.checkbox("🖼️ แสดงภาพ", value=False)
    
    st.markdown("---")
    
    # Check files
    pdf_files = list(DIRECTORIES['agreements'].glob('*.pdf'))
    ap_files = list(DIRECTORIES['ap'].glob('*.csv'))
    ar_files = list(DIRECTORIES['ar'].glob('*.csv'))
    
    if not pdf_files or not ap_files or not ar_files:
        st.error("❌ ไม่พบไฟล์ที่จำเป็น")
        return
    
    # Run button
    if st.button("🚀 รันประมวลผล", type="primary", use_container_width=True):
        run_processing(
            pdf_files=[str(f) for f in pdf_files],
            ap_file=str(ap_files[0]),
            ar_file=str(ar_files[0]),
            api_key=st.session_state.api_key,
            use_llm_validation=use_llm,
            show_images=show_images
        )


def run_processing(pdf_files, ap_file, ar_file, api_key, use_llm_validation, show_images):
    """รันการประมวลผล - เวอร์ชันง่ายๆ"""
    
    service = ProcessingService(api_key)
    
    # Progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    start_time = time.time()
    
    # PDF progress callback
    def update_pdf_progress(current, total, filename):
        progress = current / total * 0.6
        progress_bar.progress(progress)
        elapsed = int(time.time() - start_time)
        status_text.text(f"📄 ประมวลผล: {filename} ({current}/{total}) - {elapsed}s")
    
    # Analysis progress callback - แก้ bug!
    def update_analysis_progress(stage, progress_value=0.5):
        progress = 0.6 + (progress_value * 0.4)
        progress_bar.progress(progress)
        elapsed = int(time.time() - start_time)
        status_text.text(f"🔍 วิเคราะห์: {stage} - {elapsed}s")
    
    try:
        # Process PDFs
        status_text.text("🔄 เริ่มประมวลผล PDF...")
        success, fail = service.process_contracts(
            pdf_files=pdf_files,
            show_images=show_images,
            delay_seconds=30,
            progress_callback=update_pdf_progress
        )
        
        # Analysis
        status_text.text("🔄 เริ่มวิเคราะห์...")
        results = service.run_full_analysis(
            ap_file=ap_file,
            ar_file=ar_file,
            use_llm_validation=use_llm_validation,
            progress_callback=update_analysis_progress
        )
        
        # Save session
        progress_bar.progress(0.95)
        status_text.text("💾 บันทึก...")
        session_name = service.save_session()
        
        # Complete
        progress_bar.progress(1.0)
        elapsed_total = int(time.time() - start_time)
        status_text.text(f"✅ เสร็จสิ้น! ({elapsed_total}s)")
        
        # Store results
        st.session_state.processing_results = results
        st.session_state.processing_summary = service.get_processing_summary()
        st.session_state.session_name = session_name
        
        # Success message
        st.success(f"""
        ✅ **ประมวลผลสำเร็จ!**
        
        - PDF สำเร็จ: {success} ไฟล์
        - PDF ล้มเหลว: {fail} ไฟล์
        - รายการ: {len(results) if results is not None else 0}
        - เวลา: {elapsed_total} วินาที
        
        💡 ไปหน้า "For Auditor" เพื่อดู Dashboard
        """)
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        st.code(traceback.format_exc())


def show_results_section():
    """แสดงผลลัพธ์"""
    st.markdown("### 📊 ผลลัพธ์")
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        st.info("ℹ️ ยังไม่มีผลลัพธ์")
        return
    
    results = st.session_state.processing_results
    summary = st.session_state.get('processing_summary', {})
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("✅ สำเร็จ", summary.get('success', 0))
    col2.metric("❌ ล้มเหลว", summary.get('failed', 0))
    col3.metric("📊 รายการ", len(results))
    
    if 'vendor_code' in results.columns:
        col4.metric("🏢 Vendors", results['vendor_code'].nunique())
    
    st.markdown("---")
    
    # Table
    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Download
    if len(results) > 0:
        csv = results.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลด CSV",
            data=csv,
            file_name=f"results_{st.session_state.get('session_name', 'export')}.csv",
            mime="text/csv",
            use_container_width=True
        )
