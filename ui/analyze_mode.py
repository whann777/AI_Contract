"""
Analyze Mode UI - ส่วนที่ 1: สำหรับประมวลผลและวิเคราะห์
ไฟล์ทั้งหมดอยู่ใน GitHub แล้ว ไม่ต้องอัปโหลด
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
    แสดง UI สำหรับโหมด Analyze (ส่วนที่ 1)
    """
    st.title("🔬 For Analyze: ประมวลผลสัญญาและข้อมูล")
    
    # Back button
    if st.button("← กลับหน้าแรก"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Initialize session state
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    
    # Main sections
    show_file_status_section()
    show_processing_section()
    show_results_section()


def show_file_status_section():
    """แสดงสถานะไฟล์ที่มีอยู่ - UI สวย"""
    st.markdown("### 📁 สถานะไฟล์ข้อมูล")
    
    # Info box สวย
    st.info("""
    💡 **ไฟล์ทั้งหมดถูกเก็บไว้ที่ GitHub แล้ว**
    
    ระบบจะอ่านไฟล์จาก:
    - 📄 `data/agreements/` - ไฟล์สัญญา PDF
    - 💰 `data/ap/` - ไฟล์ Account Payable (CSV)
    - 📊 `data/ar/` - ไฟล์ Account Receivable (CSV)
    """)
    
    # Cards แบบสวย
    col1, col2, col3 = st.columns(3)
    
    # Check PDF files
    with col1:
        pdf_folder = DIRECTORIES['agreements']
        pdf_files = list(pdf_folder.glob('*.pdf'))
        
        if pdf_files:
            st.markdown(f"""
            <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
                <h2 style="margin: 0; font-size: 24px;">📄 PDF Files</h2>
                <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold;">{len(pdf_files)}</p>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">ไฟล์พร้อมประมวลผล</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📋 รายการไฟล์ PDF"):
                for idx, f in enumerate(pdf_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์ PDF")
    
    # Check AP files
    with col2:
        ap_folder = DIRECTORIES['ap']
        ap_files = list(ap_folder.glob('*.csv'))
        
        if ap_files:
            st.markdown(f"""
            <div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white;">
                <h2 style="margin: 0; font-size: 24px;">💰 AP Files</h2>
                <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold;">{len(ap_files)}</p>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">ยอดซื้อพร้อมใช้งาน</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📋 รายการไฟล์ AP"):
                for idx, f in enumerate(ap_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์ AP")
    
    # Check AR files
    with col3:
        ar_folder = DIRECTORIES['ar']
        ar_files = list(ar_folder.glob('*.csv'))
        
        if ar_files:
            st.markdown(f"""
            <div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white;">
                <h2 style="margin: 0; font-size: 24px;">📊 AR Files</h2>
                <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold;">{len(ar_files)}</p>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">ยอดขายพร้อมใช้งาน</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📋 รายการไฟล์ AR"):
                for idx, f in enumerate(ar_files, 1):
                    st.text(f"{idx}. {f.name}")
        else:
            st.error("❌ ไม่พบไฟล์ AR")
    
    st.markdown("---")


def show_processing_section():
    """ส่วนตั้งค่าและรันประมวลผล - UI สวย"""
    st.markdown("### ⚙️ ตั้งค่าและรันประมวลผล")
    
    # ดึง API Key จาก Streamlit Secrets
    api_key = ""
    try:
        if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception as e:
        st.error(f"Error reading secrets: {e}")
    
    # เก็บใน session_state
    if 'api_key' not in st.session_state:
        st.session_state.api_key = api_key
    
    # แสดงสถานะ API Key แบบสวย
    if st.session_state.api_key:
        st.markdown("""
        <div style="padding: 15px; background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%); border-radius: 8px; color: white;">
            ✅ <strong>Gemini API Key พร้อมใช้งาน</strong> (จาก Secrets)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("❌ ไม่พบ Gemini API Key - กรุณาตั้งค่าใน Secrets")
        
        with st.expander("💡 วิธีตั้งค่า API Key"):
            st.markdown("""
            **ขั้นตอนการตั้งค่า:**
            1. ไปที่ Streamlit Cloud → ⚙️ Settings
            2. เลือก 🔒 Secrets
            3. เพิ่ม: `GEMINI_API_KEY = "your-api-key-here"`
            4. กด Save & Reboot
            """)
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Processing options แบบสวย
    col1, col2 = st.columns(2)
    
    with col1:
        use_llm_validation = st.checkbox(
            "🤖 ใช้ AI ตรวจสอบความถูกต้อง",
            value=True,
            help="ใช้ LLM ตรวจสอบความถูกต้องของข้อมูล"
        )
    
    with col2:
        show_images = st.checkbox(
            "🖼️ แสดงภาพระหว่างประมวลผล",
            value=False,
            help="แสดงภาพจาก PDF (อาจทำให้ช้า)"
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
    
    # Run button สวย
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 รันประมวลผล", type="primary", use_container_width=True):
            run_processing(
                pdf_files=[str(f) for f in pdf_files],
                ap_file=str(ap_files[0]),
                ar_file=str(ar_files[0]),
                api_key=st.session_state.api_key,
                use_llm_validation=use_llm_validation,
                show_images=show_images
            )


def run_processing(pdf_files, ap_file, ar_file, api_key, use_llm_validation, show_images):
    """รันการประมวลผล - แก้ bug + progress bar สวย"""
    
    # Initialize service
    service = ProcessingService(api_key)
    
    # สร้าง container สำหรับ progress
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 กำลังประมวลผล...")
        
        # Progress bar สวย
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        
        start_time = time.time()
        
        def update_pdf_progress(current, total, filename):
            progress = current / total * 0.6
            progress_bar.progress(progress)
            
            elapsed = time.time() - start_time
            status_text.markdown(f"""
            <div style="padding: 10px; background: #f0f2f6; border-radius: 5px;">
                📄 <strong>ประมวลผล PDF:</strong> {filename}<br>
                📊 <strong>ความคืบหน้า:</strong> {current}/{total} ไฟล์ ({int(progress*100)}%)
            </div>
            """, unsafe_allow_html=True)
            time_text.text(f"⏱️ เวลาที่ใช้: {int(elapsed)} วินาที")
        
        def update_analysis_progress(stage, progress_value=0.5):
            """แก้ bug: ให้ progress_value มีค่า default"""
            progress = 0.6 + (progress_value * 0.4)
            progress_bar.progress(progress)
            
            elapsed = time.time() - start_time
            status_text.markdown(f"""
            <div style="padding: 10px; background: #e3f2fd; border-radius: 5px;">
                🔍 <strong>กำลังวิเคราะห์:</strong> {stage}<br>
                📊 <strong>ความคืบหน้า:</strong> {int(progress*100)}%
            </div>
            """, unsafe_allow_html=True)
            time_text.text(f"⏱️ เวลาที่ใช้: {int(elapsed)} วินาที")
        
        # Process PDFs
        status_text.info("🔄 เริ่มประมวลผล PDF...")
        success, fail = service.process_contracts(
            pdf_files=pdf_files,
            show_images=show_images,
            delay_seconds=30,
            progress_callback=update_pdf_progress
        )
        
        # Run analysis
        status_text.info("🔄 เริ่มวิเคราะห์และเปรียบเทียบข้อมูล...")
        
        try:
            results = service.run_full_analysis(
                ap_file=ap_file,
                ar_file=ar_file,
                use_llm_validation=use_llm_validation,
                progress_callback=update_analysis_progress
            )
        except TypeError as e:
            # แก้ bug: ถ้า callback มีปัญหา ให้รันแบบไม่มี progress
            st.warning(f"⚠️ Progress callback issue: {e}")
            results = service.run_full_analysis(
                ap_file=ap_file,
                ar_file=ar_file,
                use_llm_validation=use_llm_validation,
                progress_callback=None
            )
        
        # Save session
        progress_bar.progress(0.95)
        status_text.info("💾 กำลังบันทึกผลลัพธ์...")
        session_name = service.save_session()
        
        # Complete
        progress_bar.progress(1.0)
        elapsed_total = time.time() - start_time
        
        status_text.markdown(f"""
        <div style="padding: 15px; background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%); border-radius: 8px; color: white;">
            ✅ <strong>ประมวลผลเสร็จสิ้น!</strong><br>
            ⏱️ เวลาทั้งหมด: {int(elapsed_total)} วินาที
        </div>
        """, unsafe_allow_html=True)
        time_text.empty()
    
    # Store results in session state
    st.session_state.processing_results = results
    st.session_state.processing_summary = service.get_processing_summary()
    st.session_state.session_name = session_name
    
    # Success message สวย
    st.balloons()  # Animation!
    
    st.success(f"""
    🎉 **ประมวลผลสำเร็จ!**
    
    - ✅ PDF สำเร็จ: **{success}** ไฟล์
    - ❌ PDF ล้มเหลว: **{fail}** ไฟล์
    - 📊 จำนวนรายการ: **{len(results) if results is not None else 0}** รายการ
    - 💾 Session: **{session_name}**
    
    💡 **ตอนนี้สามารถไปหน้า "For Auditor" เพื่อดู Dashboard ได้แล้ว!**
    """)
    
    # Auto scroll to results
    time.sleep(3)
    st.rerun()


def show_results_section():
    """แสดงผลลัพธ์ - UI สวย"""
    st.markdown("### 📊 ผลลัพธ์")
    
    if 'processing_results' not in st.session_state or st.session_state.processing_results is None:
        st.info("ℹ️ ยังไม่มีผลลัพธ์ กรุณารันประมวลผลก่อน")
        return
    
    results = st.session_state.processing_results
    summary = st.session_state.get('processing_summary', {})
    
    # Summary metrics แบบสวย
    st.markdown("#### 📈 สรุปผลการประมวลผล")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; text-align: center;">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">PDF สำเร็จ</p>
            <p style="margin: 5px 0 0 0; font-size: 36px; font-weight: bold;">{summary.get('success', 0)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="padding: 15px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; text-align: center;">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">PDF ล้มเหลว</p>
            <p style="margin: 5px 0 0 0; font-size: 36px; font-weight: bold;">{summary.get('failed', 0)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="padding: 15px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; text-align: center;">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">จำนวนรายการ</p>
            <p style="margin: 5px 0 0 0; font-size: 36px; font-weight: bold;">{len(results)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        vendors_count = results['vendor_code'].nunique() if len(results) > 0 else 0
        st.markdown(f"""
        <div style="padding: 15px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 10px; color: white; text-align: center;">
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">Vendors</p>
            <p style="margin: 5px 0 0 0; font-size: 36px; font-weight: bold;">{vendors_count}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Show results table
    st.markdown("#### 📋 ตารางผลลัพธ์")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        if 'vendor_code' in results.columns:
            vendors = ['ทั้งหมด'] + sorted(results['vendor_code'].unique().tolist())
            selected_vendor = st.selectbox("🔍 กรอง Vendor:", vendors)
    
    with col2:
        if 'Division' in results.columns:
            divisions = ['ทั้งหมด'] + sorted(results['Division'].unique().tolist())
            selected_division = st.selectbox("🔍 กรอง Division:", divisions)
    
    # Apply filters
    filtered_results = results.copy()
    if selected_vendor != 'ทั้งหมด':
        filtered_results = filtered_results[filtered_results['vendor_code'] == selected_vendor]
    if selected_division != 'ทั้งหมด':
        filtered_results = filtered_results[filtered_results['Division'] == selected_division]
    
    # Show table
    st.dataframe(
        filtered_results,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Download button สวย
    if len(filtered_results) > 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            csv = filtered_results.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ดาวน์โหลด CSV",
                data=csv,
                file_name=f"results_{st.session_state.get('session_name', 'export')}.csv",
                mime="text/csv",
                use_container_width=True
            )
