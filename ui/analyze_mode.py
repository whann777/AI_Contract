"""
Analyze Mode UI - แยก 2 Steps: Process PDFs / Analyze Data
"""

import streamlit as st
import os
from pathlib import Path
import time
import json

from services.processing_service import ProcessingService
from config.settings import DIRECTORIES


def show_analyze_mode():
    """
    แสดง UI สำหรับโหมด Analyze (แยกเป็น 2 ส่วน)
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
    
    # แสดงสถานะไฟล์
    show_file_status_section()
    
    st.markdown("---")
    
    # ════════════════════════════════════════════════
    # STEP 1: Process PDFs (ทำครั้งเดียว)
    # ════════════════════════════════════════════════
    show_step1_process_pdfs()
    
    st.markdown("---")
    
    # ════════════════════════════════════════════════
    # STEP 2: Analyze (ใช้ได้เรื่อยๆ)
    # ════════════════════════════════════════════════
    show_step2_analyze()


def show_file_status_section():
    """แสดงสถานะไฟล์ที่มีอยู่"""
    st.markdown("### 📁 สถานะไฟล์ข้อมูล")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Check PDF files
    with col1:
        pdf_folder = DIRECTORIES['agreements']
        pdf_files = list(pdf_folder.glob('*.pdf'))
        
        st.markdown("#### 📄 PDF")
        if pdf_files:
            st.success(f"✅ {len(pdf_files)} ไฟล์")
        else:
            st.error("❌ ไม่พบ")
    
    # Check JSON files (processed PDFs)
    with col2:
        json_folder = DIRECTORIES.get('tta_summaries', Path('data/tta_summaries'))
        json_files = list(json_folder.glob('*.json'))
        
        st.markdown("#### 📋 JSON")
        if json_files:
            st.success(f"✅ {len(json_files)} ไฟล์")
        else:
            st.warning("⚠️ ยังไม่มี")
    
    # Check AP files
    with col3:
        ap_folder = DIRECTORIES['ap']
        ap_files = list(ap_folder.glob('*.csv'))
        
        st.markdown("#### 💰 AP")
        if ap_files:
            st.success(f"✅ {len(ap_files)} ไฟล์")
        else:
            st.error("❌ ไม่พบ")
    
    # Check AR files
    with col4:
        ar_folder = DIRECTORIES['ar']
        ar_files = list(ar_folder.glob('*.csv'))
        
        st.markdown("#### 📊 AR")
        if ar_files:
            st.success(f"✅ {len(ar_files)} ไฟล์")
        else:
            st.error("❌ ไม่พบ")


def show_step1_process_pdfs():
    """Step 1: ประมวลผล PDF (ทำครั้งเดียว)"""
    
    with st.expander("📂 **STEP 1: Process PDF Files** (One-Time Setup)", expanded=False):
        st.info("""
        ℹ️ **ขั้นตอนนี้ทำครั้งเดียว** หรือเมื่อมีไฟล์ PDF ใหม่
        
        ระบบจะ:
        1. อ่าน PDF ทั้งหมดใน `data/agreements/`
        2. ประมวลผลด้วย AI (Gemini)
        3. บันทึกผลเป็น JSON ใน `data/tta_summaries/`
        
        ⚠️ **ใช้เวลานาน:** ~30 วินาที/ไฟล์
        """)
        
        # Check API Key
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            api_key = ""
        
        if 'api_key' not in st.session_state:
            st.session_state.api_key = api_key
        
        if not st.session_state.api_key:
            st.error("❌ ไม่พบ Gemini API Key")
            st.info("""
            💡 **วิธีตั้งค่า:**
            1. Streamlit Cloud → Settings → Secrets
            2. เพิ่ม: `GEMINI_API_KEY = "your-key"`
            3. Save & Reboot
            """)
            return
        
        st.success("✅ Gemini API Key พร้อมใช้งาน")
        
        # Check files
        pdf_files = list(DIRECTORIES['agreements'].glob('*.pdf'))
        json_folder = DIRECTORIES.get('tta_summaries', Path('data/tta_summaries'))
        json_files = list(json_folder.glob('*.json'))
        
        if not pdf_files:
            st.error("❌ ไม่พบไฟล์ PDF ใน data/agreements/")
            return
        
        # Show status
        col1, col2 = st.columns(2)
        col1.metric("PDF Files", len(pdf_files))
        col2.metric("JSON Files", len(json_files))
        
        if len(json_files) == len(pdf_files):
            st.success(f"✅ ประมวลผล PDF ครบแล้ว ({len(json_files)}/{len(pdf_files)})")
            st.info("💡 สามารถข้ามไป **STEP 2** เพื่อ Analyze ได้เลย")
        else:
            st.warning(f"⚠️ ยังประมวลผลไม่ครบ ({len(json_files)}/{len(pdf_files)})")
        
        # Processing options
        col1, col2 = st.columns(2)
        with col1:
            show_images = st.checkbox("แสดงภาพระหว่างประมวลผล", value=False)
        with col2:
            delay_seconds = st.number_input("Delay (วินาที)", min_value=0, max_value=60, value=30)
        
        # Process button
        if st.button("🚀 Process PDFs", type="primary", key="process_pdfs"):
            run_pdf_processing(
                pdf_files=[str(f) for f in pdf_files],
                api_key=st.session_state.api_key,
                show_images=show_images,
                delay_seconds=delay_seconds
            )


def run_pdf_processing(pdf_files, api_key, show_images, delay_seconds):
    """รันประมวลผล PDF"""
    
    service = ProcessingService(api_key)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(current, total, filename):
        progress = current / total
        progress_bar.progress(progress)
        status_text.text(f"📄 Processing: {filename} ({current}/{total})")
    
    # Process
    status_text.text("🔄 เริ่มประมวลผล PDF...")
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
    ✅ **ประมวลผล PDF เสร็จสิ้น!**
    
    - สำเร็จ: {success} ไฟล์
    - ล้มเหลว: {fail} ไฟล์
    
    💡 **ตอนนี้สามารถไป STEP 2 เพื่อ Analyze ได้แล้ว!**
    """)
    
    time.sleep(2)
    st.rerun()


def show_step2_analyze():
    """Step 2: วิเคราะห์ข้อมูล (ทำได้เรื่อยๆ เร็ว!)"""
    
    st.markdown("### 📊 STEP 2: Analyze Data (Fast - Can Repeat)")
    
    st.info("""
    ℹ️ **ขั้นตอนนี้ทำได้เรื่อยๆ** แม้เปลี่ยน AP/AR ก็ Analyze ใหม่ได้
    
    ระบบจะ:
    1. โหลด JSON จาก `data/tta_summaries/` (เร็ว!)
    2. โหลด AP/AR CSV
    3. คำนวณและเปรียบเทียบ
    4. แสดงผลลัพธ์
    
    ⏱️ **ใช้เวลา:** ~30-60 วินาที
    """)
    
    # Check files
    json_folder = DIRECTORIES.get('tta_summaries', Path('data/tta_summaries'))
    json_files = list(json_folder.glob('*.json'))
    ap_files = list(DIRECTORIES['ap'].glob('*.csv'))
    ar_files = list(DIRECTORIES['ar'].glob('*.csv'))
    
    # Validate
    if not json_files:
        st.error("❌ ไม่พบไฟล์ JSON - กรุณาทำ STEP 1 ก่อน")
        return
    
    if not ap_files:
        st.error("❌ ไม่พบไฟล์ AP ใน data/ap/")
        return
    
    if not ar_files:
        st.error("❌ ไม่พบไฟล์ AR ใน data/ar/")
        return
    
    # Show metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("JSON Files", len(json_files))
    col2.metric("AP Files", len(ap_files))
    col3.metric("AR Files", len(ar_files))
    
    # Options
    use_llm_validation = st.checkbox(
        "ใช้ AI ตรวจสอบความถูกต้อง",
        value=True,
        help="ใช้ LLM ตรวจสอบ AR data"
    )
    
    # Analyze button
    if st.button("🔍 Analyze", type="primary", key="analyze"):
        run_analysis(
            json_folder=json_folder,
            ap_file=str(ap_files[0]),
            ar_file=str(ar_files[0]),
            use_llm_validation=use_llm_validation
        )
    
    # Show results
    show_results_section()


def run_analysis(json_folder, ap_file, ar_file, use_llm_validation):
    """รันการวิเคราะห์"""
    
    # Check API Key
    api_key = st.session_state.get('api_key', '')
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            st.error("❌ ไม่พบ API Key")
            return
    
    service = ProcessingService(api_key)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(stage, progress_value=None):
        if progress_value is not None:
            progress_bar.progress(progress_value)
        status_text.text(f"⚙️ {stage}")
    
    # Load TTA from JSON (fast!)
    status_text.text("📋 Loading JSON files...")
    progress_bar.progress(0.1)
    
    json_files = list(json_folder.glob('*.json'))
    tta_data = {}
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                vendor_key = data.get('vendor_code', '')
                div_code = data.get('division_code', '')
                dept_code = data.get('department_code', '')
                
                if vendor_key and div_code and dept_code:
                    tta_key = f"{vendor_key}_{div_code}_{dept_code}"
                    tta_data[tta_key] = data
        except Exception as e:
            st.warning(f"⚠️ ไม่สามารถโหลด {json_file.name}: {e}")
    
    if not tta_data:
        st.error("❌ ไม่สามารถโหลด JSON ได้")
        return
    
    status_text.text(f"✅ โหลด JSON สำเร็จ: {len(tta_data)} รายการ")
    progress_bar.progress(0.2)
    
    # Set TTA data to service
    service.recon_system.tta_data = tta_data
    
    # Load AP
    update_progress("โหลดข้อมูล AP...", 0.3)
    ap_loaded = service.recon_system.load_ap_data(ap_file)
    if not ap_loaded:
        st.error("❌ ไม่สามารถโหลด AP ได้")
        return
    
    # Load AR
    update_progress("โหลดข้อมูล AR...", 0.4)
    ar_loaded = service.recon_system.load_ar_data(ar_file)
    
    # Calculate allowances
    update_progress("คำนวณ Allowances...", 0.6)
    calculated = service.recon_system.calculate_allowances()
    if calculated is None:
        st.error("❌ ไม่สามารถคำนวณ Allowances ได้")
        return
    
    # Reconcile with AR
    if ar_loaded:
        # Validate AR with LLM (optional)
        if use_llm_validation:
            update_progress("ตรวจสอบ AR ด้วย AI...", 0.7)
            service.recon_system.validate_ar_with_llm(service.analyzer)
        
        # Reconcile
        update_progress("เปรียบเทียบกับ AR...", 0.8)
        reconciliation = service.recon_system.reconcile_with_ar()
        
        # Generate summary
        summary = service.recon_system.generate_summary_report()
        
        results = reconciliation
    else:
        st.warning("⚠️ ไม่มีข้อมูล AR - แสดงเฉพาะ Calculated Allowances")
        results = calculated
    
    # Export
    update_progress("Export รายงาน...", 0.9)
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
    ✅ **วิเคราะห์เสร็จสิ้น!**
    
    - จำนวนรายการ: {len(results) if results is not None else 0}
    - ไฟล์รายงาน: {output_file}
    
    💡 **ตอนนี้สามารถไปหน้า "For Auditor" เพื่อดู Dashboard ได้แล้ว!**
    """)
    
    time.sleep(2)
    st.rerun()


def show_results_section():
    """แสดงผลลัพธ์"""
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        return
    
    st.markdown("---")
    st.markdown("### 📊 ผลลัพธ์")
    
    results = st.session_state.processing_results
    summary = st.session_state.get('processing_summary', {})
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    col1.metric("จำนวนรายการ", len(results))
    col2.metric("Vendors", results['vendor_code'].nunique() if len(results) > 0 else 0)
    
    if 'should_collect' in results.columns:
        total_should = results['should_collect'].sum()
        col3.metric("ยอดรวมที่ควรเรียกเก็บ", f"{total_should:,.0f}")
    
    # Show results table
    st.markdown("#### 📋 ตารางผลลัพธ์ (แสดง 20 แถวแรก)")
    st.dataframe(
        results.head(20),
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
