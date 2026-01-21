"""
Analyze Mode UI - ส่วนที่ 1: สำหรับประมวลผลและวิเคราะห์
ไฟล์ทั้งหมดอยู่ใน GitHub แล้ว ไม่ต้องอัปโหลด
"""

import streamlit as st
import os
from pathlib import Path
import time

from services.processing_service import ProcessingService
from config.settings import DIRECTORIES


def show_analyze_mode():
    """
    แสดง UI สำหรับโหมด Analyze (ส่วนที่ 1)
    """
    st.title("🔬 For Analyze: ประมวลผลสัญญาและข้อมูล")
    
    # Back button
    if st.button("← กลับหน้าแรก"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Initialize session state
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    
    # Main sections
    show_file_status_section()
    show_processing_section()
    show_results_section()


def show_file_status_section():
    """แสดงสถานะไฟล์ที่มีอยู่"""
    st.markdown("### 📁 สถานะไฟล์ข้อมูล")
    
    st.info("""
    ℹ️ **ไฟล์ทั้งหมดถูกเก็บไว้ที่ GitHub แล้ว**
    
    ระบบจะอ่านไฟล์จาก:
    - `data/agreements/` - ไฟล์สัญญา PDF
    - `data/ap/` - ไฟล์ Account Payable (CSV)
    - `data/ar/` - ไฟล์ Account Receivable (CSV)
    """)
    
    col1, col2, col3 = st.columns(3)
    
    # Check PDF files
    with col1:
        pdf_folder = DIRECTORIES['agreements']
        pdf_files = list(pdf_folder.glob('*.pdf'))
        
        st.markdown("#### 📄 ไฟล์ PDF")
        if pdf_files:
            st.success(f"✅ พบ {len(pdf_files)} ไฟล์")
            with st.expander("📋 รายการ"):
                for idx, f in enumerate(pdf_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์ PDF")
    
    # Check AP files
    with col2:
        ap_folder = DIRECTORIES['ap']
        ap_files = list(ap_folder.glob('*.csv'))
        
        st.markdown("#### 💰 ไฟล์ AP")
        if ap_files:
            st.success(f"✅ พบ {len(ap_files)} ไฟล์")
            with st.expander("📋 รายการ"):
                for idx, f in enumerate(ap_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์ AP")
    
    # Check AR files
    with col3:
        ar_folder = DIRECTORIES['ar']
        ar_files = list(ar_folder.glob('*.csv'))
        
        st.markdown("#### 📊 ไฟล์ AR")
        if ar_files:
            st.success(f"✅ พบ {len(ar_files)} ไฟล์")
            with st.expander("📋 รายการ"):
                for idx, f in enumerate(ar_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์ AR")
    
    st.markdown("---")


def show_processing_section():
    """ส่วนตั้งค่าและรันประมวลผล"""
    st.markdown("### ⚙️ ตั้งค่าและรันประมวลผล")
    
    # ดึง API Key จาก Streamlit Secrets (วิธีที่ถูกต้อง!)
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""
    
    # เก็บใน session_state
    if 'api_key' not in st.session_state:
        st.session_state.api_key = api_key
    
    # แสดงสถานะ API Key
    if st.session_state.api_key:
        st.success("✅ Gemini API Key พร้อมใช้งาน (จาก Secrets)")
    else:
        st.error("❌ ไม่พบ Gemini API Key - กรุณาตั้งค่าใน Secrets")
        st.info("""
        💡 **วิธีตั้งค่า API Key:**
        1. ไปที่ Streamlit Cloud → Settings
        2. เลือก Secrets
        3. เพิ่ม: `GEMINI_API_KEY = "your-api-key-here"`
        4. Save & Reboot
        """)
        return
    
    # Processing options
    col1, col2 = st.columns(2)
    
    with col1:
        use_llm_validation = st.checkbox(
            "ใช้ AI ตรวจสอบความถูกต้อง",
            value=True,
            help="ใช้ LLM ตรวจสอบความถูกต้องของข้อมูล"
        )
    
    with col2:
        show_images = st.checkbox(
            "แสดงภาพระหว่างประมวลผล",
            value=False,
            help="แสดงภาพจาก PDF ระหว่างประมวลผล (อาจทำให้ช้า)"
        )
    
    st.markdown("---")
    
    # Check if files exist
    pdf_files = list(DIRECTORIES['agreements'].glob('*.pdf'))
    ap_files = list(DIRECTORIES['ap'].glob('*.csv'))
    ar_files = list(DIRECTORIES['ar'].glob('*.csv'))
    
    if not pdf_files:
        st.error("❌ ไม่พบไฟล์ PDF ใน data/agreements/")
        return
    
    if not ap_files:
        st.error("❌ ไม่พบไฟล์ AP ใน data/ap/")
        return
    
    if not ar_files:
        st.error("❌ ไม่พบไฟล์ AR ใน data/ar/")
        return
    
    # Run processing button
    if st.button("🚀 รันประมวลผล", type="primary"):
        run_processing(
            pdf_files=[str(f) for f in pdf_files],
            ap_file=str(ap_files[0]),  # ใช้ไฟล์แรก
            ar_file=str(ar_files[0]),  # ใช้ไฟล์แรก
            api_key=st.session_state.api_key,
            use_llm_validation=use_llm_validation,
            show_images=show_images
        )


def run_processing(pdf_files, ap_file, ar_file, api_key, use_llm_validation, show_images):
    """รันการประมวลผล"""
    
    # Initialize service
    service = ProcessingService(api_key)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_pdf_progress(current, total, filename):
        progress = current / total * 0.6  # PDF processing = 60%
        progress_bar.progress(progress)
        status_text.text(f"กำลังประมวลผล PDF: {filename} ({current}/{total})")
    
    def update_analysis_progress(stage, progress_value):
        progress = 0.6 + (progress_value * 0.4)  # Analysis = 40%
        progress_bar.progress(progress)
        status_text.text(f"กำลังวิเคราะห์: {stage}")
    
    # Process PDFs
    status_text.text("🔄 เริ่มประมวลผล PDF...")
    success, fail = service.process_contracts(
        pdf_files=pdf_files,
        show_images=show_images,
        delay_seconds=30,
        progress_callback=update_pdf_progress
    )
    
    # Run analysis
    status_text.text("🔄 เริ่มวิเคราะห์และเปรียบเทียบข้อมูล...")
    results = service.run_full_analysis(
        ap_file=ap_file,
        ar_file=ar_file,
        use_llm_validation=use_llm_validation,
        progress_callback=update_analysis_progress
    )
    
    # Save session
    session_name = service.save_session()
    
    # 🔍 DEBUG: แสดงข้อมูล session ที่บันทึก
    st.write("---")
    st.write("🔍 Debug: Session Information")
    st.write(f"- Session name: {session_name}")
    st.write(f"- มี 'saved_sessions'? {('saved_sessions' in st.session_state)}")
    if 'saved_sessions' in st.session_state:
        st.write(f"- จำนวน sessions: {len(st.session_state.saved_sessions)}")
        st.write(f"- Session keys: {list(st.session_state.saved_sessions.keys())}")
        
        # แสดงข้อมูลใน session
        if session_name in st.session_state.saved_sessions:
            session_data = st.session_state.saved_sessions[session_name]
            st.write(f"- Results shape: {session_data['results'].shape if session_data.get('results') is not None else 'None'}")
    st.write("---")
    
    # Complete
    progress_bar.progress(1.0)
    status_text.text("✅ ประมวลผลเสร็จสิ้น!")
    
    # Store results in session state
    st.session_state.processing_results = results
    st.session_state.processing_summary = service.get_processing_summary()
    st.session_state.session_name = session_name
    
    # Show success message
    st.success(f"""
    ✅ **ประมวลผลสำเร็จ!**
    
    - PDF สำเร็จ: {success} ไฟล์
    - PDF ล้มเหลว: {fail} ไฟล์
    - จำนวนรายการ: {len(results) if results is not None else 0}
    
    💡 **ตอนนี้สามารถไปหน้า "For Auditor" เพื่อดู Dashboard ได้แล้ว!**
    """)
    
    time.sleep(2)
    st.rerun()


def show_results_section():
    """แสดงผลลัพธ์"""
    st.markdown("### 📊 ผลลัพธ์")
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        st.info("ℹ️ ยังไม่มีผลลัพธ์ กรุณารันประมวลผลก่อน")
        return
    
    results = st.session_state.processing_results
    summary = st.session_state.get('processing_summary', {})
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("PDF สำเร็จ", summary.get('success', 0))
    col2.metric("PDF ล้มเหลว", summary.get('failed', 0))
    col3.metric("จำนวนรายการ", len(results))
    col4.metric("Vendors", results['vendor_code'].nunique() if len(results) > 0 else 0)
    
    # Show results table
    st.markdown("#### 📋 ตารางผลลัพธ์")
    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    if len(results) > 0:
        csv = results.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลด CSV",
            data=csv,
            file_name=f"results_{st.session_state.get('session_name', 'export')}.csv",
            mime="text/csv"
        )
