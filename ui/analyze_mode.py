"""
Analyze Mode UI - ส่วนที่ 1: สำหรับประมวลผลและวิเคราะห์
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
    
    # Tabs for different steps
    tab1, tab2, tab3 = st.tabs(["📁 อัปโหลดไฟล์", "⚙️ ตั้งค่า & รันระบบ", "📊 ผลลัพธ์"])
    
    with tab1:
        show_file_upload_section()
    
    with tab2:
        show_processing_section()
    
    with tab3:
        show_results_section()


def show_file_upload_section():
    """ส่วนอัปโหลดไฟล์"""
    st.markdown("### 📁 อัปโหลดไฟล์ข้อมูล")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1. ไฟล์สัญญา PDF")
        st.markdown("อัปโหลดไฟล์สัญญา (TTA) ที่ต้องการวิเคราะห์")
        
        uploaded_pdfs = st.file_uploader(
            "เลือกไฟล์ PDF (สามารถเลือกหลายไฟล์)",
            type=['pdf'],
            accept_multiple_files=True,
            key='pdf_uploader'
        )
        
        if uploaded_pdfs:
            st.success(f"✅ เลือกไฟล์แล้ว: {len(uploaded_pdfs)} ไฟล์")
            
            # Save to agreements folder
            agreements_folder = DIRECTORIES['agreements']
            saved_files = []
            
            for pdf_file in uploaded_pdfs:
                file_path = agreements_folder / pdf_file.name
                with open(file_path, 'wb') as f:
                    f.write(pdf_file.getbuffer())
                saved_files.append(str(file_path))
            
            st.session_state.pdf_files = saved_files
            
            # Show file list
            with st.expander("📋 รายการไฟล์"):
                for idx, filename in enumerate([f.name for f in uploaded_pdfs], 1):
                    st.text(f"{idx}. {filename}")
    
    with col2:
        st.markdown("#### 2. ไฟล์ข้อมูล AP")
        st.markdown("อัปโหลดไฟล์ยอดซื้อ (Account Payable)")
        
        uploaded_ap = st.file_uploader(
            "เลือกไฟล์ CSV",
            type=['csv'],
            key='ap_uploader'
        )
        
        if uploaded_ap:
            st.success(f"✅ เลือกไฟล์: {uploaded_ap.name}")
            
            # Save to ap folder
            ap_folder = DIRECTORIES['ap']
            file_path = ap_folder / uploaded_ap.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_ap.getbuffer())
            
            st.session_state.ap_file = str(file_path)
            
            # Show preview
            import pandas as pd
            df = pd.read_csv(file_path, nrows=5)
            with st.expander("👀 ตัวอย่างข้อมูล (5 แถวแรก)"):
                st.dataframe(df)
    
    st.markdown("")
    
    st.markdown("#### 3. ไฟล์ข้อมูล AR")
    st.markdown("อัปโหลดไฟล์ยอดเรียกเก็บ (Account Receivable)")
    
    uploaded_ar = st.file_uploader(
        "เลือกไฟล์ CSV",
        type=['csv'],
        key='ar_uploader'
    )
    
    if uploaded_ar:
        st.success(f"✅ เลือกไฟล์: {uploaded_ar.name}")
        
        # Save to ar folder
        ar_folder = DIRECTORIES['ar']
        file_path = ar_folder / uploaded_ar.name
        with open(file_path, 'wb') as f:
            f.write(uploaded_ar.getbuffer())
        
        st.session_state.ar_file = str(file_path)
        
        # Show preview
        import pandas as pd
        df = pd.read_csv(file_path, nrows=5)
        with st.expander("👀 ตัวอย่างข้อมูล (5 แถวแรก)"):
            st.dataframe(df)
    
    # Summary
    st.markdown("---")
    st.markdown("### 📋 สรุปไฟล์ที่อัปโหลด")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pdf_count = len(st.session_state.get('pdf_files', []))
        st.metric("PDF สัญญา", f"{pdf_count} ไฟล์")
    
    with col2:
        ap_status = "✅" if 'ap_file' in st.session_state else "❌"
        st.metric("AP CSV", ap_status)
    
    with col3:
        ar_status = "✅" if 'ar_file' in st.session_state else "❌"
        st.metric("AR CSV", ar_status)


def show_processing_section():
    """ส่วนตั้งค่าและรันระบบ"""
    st.markdown("### ⚙️ ตั้งค่าและรันระบบ")
    
    # API Key input
    st.markdown("#### 🔑 Gemini API Key")
    api_key = st.text_input(
        "กรอก API Key ของคุณ",
        type="password",
        value=st.session_state.get('api_key', ''),
        help="ได้รับจาก Google AI Studio: https://makersuite.google.com/app/apikey"
    )
    
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ API Key ถูกบันทึกแล้ว")
    
    st.markdown("---")
    
    # Processing options
    st.markdown("#### ⚙️ ตัวเลือกการประมวลผล")
    
    col1, col2 = st.columns(2)
    
    with col1:
        delay_seconds = st.slider(
            "หน่วงเวลาระหว่าง PDF (วินาที)",
            min_value=0,
            max_value=60,
            value=30,
            help="เพื่อป้องกัน API quota limit"
        )
        
        use_llm_validation = st.checkbox(
            "ใช้ LLM ตรวจสอบ REF_TYPE",
            value=True,
            help="ใช้ AI ตรวจสอบความถูกต้องของ category ใน AR"
        )
    
    with col2:
        show_pdf_images = st.checkbox(
            "แสดงภาพ PDF (Debug)",
            value=False,
            help="แสดงภาพตัวอย่างจาก PDF (ใช้เวลานาน)"
        )
    
    st.markdown("---")
    
    # Run button
    st.markdown("#### 🚀 เริ่มประมวลผล")
    
    # Check prerequisites
    can_run = (
        'pdf_files' in st.session_state and len(st.session_state.pdf_files) > 0 and
        'ap_file' in st.session_state and
        'api_key' in st.session_state and st.session_state.api_key
    )
    
    if not can_run:
        st.warning("⚠️ กรุณาอัปโหลดไฟล์และกรอก API Key ให้ครบถ้วน")
        missing = []
        if 'pdf_files' not in st.session_state or len(st.session_state.pdf_files) == 0:
            missing.append("- ไฟล์ PDF สัญญา")
        if 'ap_file' not in st.session_state:
            missing.append("- ไฟล์ AP CSV")
        if 'api_key' not in st.session_state or not st.session_state.api_key:
            missing.append("- Gemini API Key")
        
        if missing:
            st.markdown("**ข้อมูลที่ยังขาด:**")
            for item in missing:
                st.markdown(item)
    
    if st.button("🚀 เริ่มประมวลผล", disabled=not can_run, use_container_width=True):
        run_processing(delay_seconds, show_pdf_images, use_llm_validation)


def run_processing(delay_seconds, show_pdf_images, use_llm_validation):
    """รันกระบวนการประมวลผล"""
    
    # Initialize service
    service = ProcessingService(
        api_key=st.session_state.api_key,
        base_folder=str(DIRECTORIES['agreements'].parent)
    )
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Process PDFs
    status_text.text("📄 กำลังประมวลผล PDF...")
    
    pdf_files = st.session_state.pdf_files
    total_steps = len(pdf_files) + 5  # PDFs + 5 analysis steps
    current_step = 0
    
    def update_progress(current, total, filename):
        nonlocal current_step
        current_step += 1
        progress = current_step / total_steps
        progress_bar.progress(progress)
        status_text.text(f"📄 กำลังประมวลผล: {filename} ({current}/{total})")
    
    success, fail = service.process_contracts(
        pdf_files=pdf_files,
        show_images=show_pdf_images,
        delay_seconds=delay_seconds,
        progress_callback=update_progress
    )
    
    # Step 2: Run full analysis
    current_step += 1
    progress_bar.progress(current_step / total_steps)
    status_text.text("⚙️ กำลังวิเคราะห์และเปรียบเทียบ...")
    
    def update_analysis_progress(message):
        nonlocal current_step
        current_step += 1
        progress = current_step / total_steps
        progress_bar.progress(progress)
        status_text.text(message)
    
    results = service.run_full_analysis(
        ap_file=st.session_state.get('ap_file'),
        ar_file=st.session_state.get('ar_file'),
        use_llm_validation=use_llm_validation,
        progress_callback=update_analysis_progress
    )
    
    # Save session
    session_file = service.save_session()
    
    # Complete
    progress_bar.progress(1.0)
    status_text.text("✅ ประมวลผลเสร็จสิ้น!")
    
    # Store results in session state
    st.session_state.processing_results = results
    st.session_state.processing_summary = service.get_processing_summary()
    st.session_state.session_file = session_file
    
    # Show success message
    st.success(f"""
    ✅ **ประมวลผลสำเร็จ!**
    
    - PDF สำเร็จ: {success} ไฟล์
    - PDF ล้มเหลว: {fail} ไฟล์
    - จำนวนรายการ: {len(results) if results is not None else 0}
    
    กรุณาไปที่แท็บ "📊 ผลลัพธ์" เพื่อดูรายละเอียด
    """)
    
    time.sleep(2)
    st.rerun()


def show_results_section():
    """ส่วนแสดงผลลัพธ์"""
    st.markdown("### 📊 ผลลัพธ์การประมวลผล")
    
    if 'processing_results' not in st.session_state:
        st.info("ℹ️ ยังไม่มีผลลัพธ์ กรุณาประมวลผลข้อมูลก่อน")
        return
    
    results = st.session_state.processing_results
    summary = st.session_state.processing_summary
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "PDF ประมวลผล",
            summary.get('pdfs_processed', 0)
        )
    
    with col2:
        st.metric(
            "จำนวนรายการ",
            summary.get('total_records', 0)
        )
    
    with col3:
        if 'total_should_collect' in summary:
            st.metric(
                "ยอดที่ควรเก็บ",
                f"{summary['total_should_collect']:,.0f} บาท"
            )
    
    with col4:
        if 'total_actually_collected' in summary:
            st.metric(
                "ยอดที่เก็บจริง",
                f"{summary['total_actually_collected']:,.0f} บาท"
            )
    
    st.markdown("---")
    
    # Results table
    st.markdown("#### 📋 รายละเอียดผลลัพธ์")
    
    if results is not None and len(results) > 0:
        # Show data
        st.dataframe(results, use_container_width=True, height=400)
        
        # Export options
        st.markdown("#### 💾 Export รายงาน")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 ดาวน์โหลด Excel", use_container_width=True):
                from services.reporting_service import ReportingService
                reporter = ReportingService()
                
                excel_file = reporter.export_to_excel(
                    results,
                    filename=f"results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                )
                
                with open(excel_file, 'rb') as f:
                    st.download_button(
                        "💾 บันทึกไฟล์ Excel",
                        data=f,
                        file_name=os.path.basename(excel_file),
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
        
        with col2:
            if st.button("📥 ดาวน์โหลด CSV", use_container_width=True):
                csv = results.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "💾 บันทึกไฟล์ CSV",
                    data=csv,
                    file_name=f"results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime='text/csv'
                )
    else:
        st.warning("⚠️ ไม่มีข้อมูลผลลัพธ์")
