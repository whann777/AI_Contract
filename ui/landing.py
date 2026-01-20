"""
Landing Page - หน้าแรกของระบบ
แสดงตัวเลือก 2 ทาง: For Analyze และ For Auditor
"""

import streamlit as st


def show_landing_page():
    """
    แสดงหน้า Landing Page พร้อมปุ่มเลือก 2 ทาง
    
    Returns:
        str: 'analyze' หรือ 'auditor' หรือ None
    """
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #366092; font-size: 3rem; margin-bottom: 0.5rem;">
            📊 Contract Audit System
        </h1>
        <p style="font-size: 1.2rem; color: #666;">
            ระบบตรวจสอบสัญญาการค้าด้วย AI
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Introduction
    st.markdown("""
    ### ยินดีต้อนรับสู่ระบบตรวจสอบสัญญาอัตโนมัติ
    
    ระบบนี้ช่วยให้คุณ:
    - 📄 **วิเคราะห์สัญญา PDF** ด้วย AI (Google Gemini)
    - 💰 **คำนวณยอด Allowance** ที่ควรได้อัตโนมัติ
    - 🔍 **เปรียบเทียบกับยอดจริง** จาก AR
    - 📊 **สร้างรายงานตรวจสอบ** ครบถ้วน
    """)
    
    st.markdown("")
    
    # Main selection
    st.markdown("### เลือกโหมดการทำงาน:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            height: 300px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <h2 style="color: white; margin-bottom: 1rem;">🔬 For Analyze</h2>
            <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
                สำหรับประมวลผลสัญญาและข้อมูล
            </p>
            <ul style="text-align: left; font-size: 0.95rem; margin: 0 auto; max-width: 250px;">
                <li>อัปโหลด PDF สัญญา</li>
                <li>อัปโหลดข้อมูล AP/AR</li>
                <li>รัน AI วิเคราะห์</li>
                <li>คำนวณและเปรียบเทียบ</li>
                <li>บันทึกผลลัพธ์</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        if st.button("🚀 เริ่มประมวลผล", key="btn_analyze", use_container_width=True):
            return 'analyze'
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            height: 300px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <h2 style="color: white; margin-bottom: 1rem;">👨‍💼 For Auditor</h2>
            <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
                สำหรับตรวจสอบและดูรายงาน
            </p>
            <ul style="text-align: left; font-size: 0.95rem; margin: 0 auto; max-width: 250px;">
                <li>ดูผลลัพธ์ที่บันทึกไว้</li>
                <li>กรองข้อมูลตาม Vendor</li>
                <li>ดูสถานะการเก็บเงิน</li>
                <li>Drill-down รายละเอียด</li>
                <li>Export รายงาน</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        if st.button("📊 ดูรายงาน", key="btn_auditor", use_container_width=True):
            return 'auditor'
    
    # Features section
    st.markdown("---")
    st.markdown("### ✨ คุณสมบัติของระบบ")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🤖 AI-Powered**
        - ใช้ Google Gemini
        - วิเคราะห์สัญญาอัตโนมัติ
        - ครอบคลุม 21 ประเภท Allowance
        """)
    
    with col2:
        st.markdown("""
        **⚡ รวดเร็ว & แม่นยำ**
        - ประมวลผลแบบ Batch
        - จับคู่ข้อมูลอัตโนมัติ
        - คำนวณตามสูตรที่กำหนด
        """)
    
    with col3:
        st.markdown("""
        **📈 รายงานครบถ้วน**
        - Export Excel/CSV
        - กราฟและตาราง
        - Dashboard แบบ Real-time
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9rem; padding: 1rem 0;">
        Contract Audit System v1.0 | Powered by Google Gemini AI
    </div>
    """, unsafe_allow_html=True)
    
    return None


def show_info_sidebar():
    """แสดงข้อมูลใน sidebar"""
    with st.sidebar:
        st.markdown("### ℹ️ ข้อมูลระบบ")
        
        st.markdown("""
        **ประเภท Allowance ที่รองรับ:**
        - ARB - Unconditional Rebate
        - CRB - Conditional Rebate
        - BRO - Brochure Fee
        - MMF - Marketing Fund
        - ANI - Anniversary
        - และอีก 16 ประเภท
        """)
        
        st.markdown("---")
        
        st.markdown("""
        **ข้อมูลที่ต้องเตรียม:**
        
        สำหรับ **For Analyze**:
        - ✅ ไฟล์ PDF สัญญา
        - ✅ ไฟล์ AP CSV (ยอดซื้อ)
        - ✅ ไฟล์ AR CSV (ยอดเรียกเก็บ)
        - ✅ Gemini API Key
        
        สำหรับ **For Auditor**:
        - ✅ Session ที่บันทึกไว้
        """)
        
        st.markdown("---")
        
        st.markdown("""
        **💡 Tips:**
        - ตรวจสอบให้แน่ใจว่า CSV encoding เป็น UTF-8
        - PDF ควรเป็นไฟล์ที่อ่านได้ (ไม่ใช่รูปภาพ scan)
        - API Key ต้องมีสิทธิ์ใช้ Gemini 2.5 Flash
        """)
