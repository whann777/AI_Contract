"""
Debug Script - ตรวจสอบว่าไฟล์ไหนไม่ออกในผลลัพธ์
วางไฟล์นี้ที่ pages/1_debug.py
"""

import streamlit as st
import json
from pathlib import Path
from config.settings import DIRECTORIES

st.title("🔍 Debug: ตรวจสอบไฟล์ที่หาย")

st.markdown("---")

# 1. ตรวจสอบ PDF ที่อัปโหลด
st.markdown("## 📄 Step 1: ไฟล์ PDF ที่มี")
pdf_folder = DIRECTORIES['agreements']
pdf_files = sorted(list(pdf_folder.glob("*.pdf")))

st.info(f"พบ {len(pdf_files)} ไฟล์ PDF")

pdf_names = []
for i, pdf in enumerate(pdf_files, 1):
    st.text(f"{i}. {pdf.name}")
    pdf_names.append(pdf.stem)  # ชื่อไฟล์ไม่มี .pdf

st.markdown("---")

# 2. ตรวจสอบ JSON ที่สร้าง
st.markdown("## 📋 Step 2: ไฟล์ JSON ที่สร้าง")
tta_folder = DIRECTORIES['tta_summaries']
json_files = sorted(list(tta_folder.glob("*_summary.json")))

st.info(f"พบ {len(json_files)} ไฟล์ JSON")

json_data = {}
for i, json_file in enumerate(json_files, 1):
    st.text(f"{i}. {json_file.name}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            json_data[json_file.name] = data
    except Exception as e:
        st.error(f"   ❌ Error: {e}")

# เปรียบเทียบ
if len(pdf_files) != len(json_files):
    st.error(f"⚠️ จำนวนไม่ตรงกัน! PDF: {len(pdf_files)}, JSON: {len(json_files)}")
    
    st.markdown("### 🔍 ไฟล์ PDF ที่ไม่มี JSON:")
    
    # หา PDF ที่ไม่มี JSON
    json_basenames = [j.name.replace('_summary.json', '') for j in json_files]
    
    missing = []
    for pdf_name in pdf_names:
        found = False
        for json_base in json_basenames:
            if pdf_name in json_base:
                found = True
                break
        if not found:
            missing.append(pdf_name)
    
    if missing:
        for m in missing:
            st.error(f"❌ {m}.pdf → ไม่มี JSON!")
    else:
        st.warning("ตรวจสอบด้วยตนเอง - อาจมีชื่อไฟล์ไม่ตรงกัน")
else:
    st.success("✅ จำนวน PDF และ JSON ตรงกัน")

st.markdown("---")

# 3. ตรวจสอบข้อมูลใน JSON
st.markdown("## 📊 Step 3: ข้อมูลใน JSON แต่ละไฟล์")

for json_file, data in json_data.items():
    with st.expander(f"📄 {json_file}"):
        col1, col2, col3 = st.columns(3)
        
        vendor_code = data.get('vendor_code', 'N/A')
        div_code = data.get('Division_code', 'N/A')
        dept_code = data.get('Department_code', 'N/A')
        
        col1.metric("Vendor", vendor_code)
        col2.metric("Division", div_code)
        col3.metric("Department", dept_code)
        
        # ตรวจสอบ error
        if 'error' in data:
            st.error(f"❌ Error: {data['error']}")
        else:
            st.success("✅ ไม่มี error")
        
        # แสดงจำนวน allowances
        allowances = data.get('Trade_allowances', [])
        st.info(f"Allowances: {len(allowances)} รายการ")

st.markdown("---")

# 4. ตรวจสอบผลลัพธ์
st.markdown("## 📈 Step 4: ผลลัพธ์ที่แสดง")

if 'processing_results' in st.session_state:
    results = st.session_state.processing_results
    
    if results is not None and len(results) > 0:
        st.info(f"จำนวนรายการทั้งหมด: {len(results)} แถว")
        
        # ดูว่ามีกี่ vendor
        if 'vendor_code' in results.columns:
            unique_vendors = results['vendor_code'].unique()
            st.success(f"✅ มี {len(unique_vendors)} vendors")
            
            st.markdown("### Vendors ในผลลัพธ์:")
            for i, vendor in enumerate(unique_vendors, 1):
                vendor_data = results[results['vendor_code'] == vendor]
                st.text(f"{i}. {vendor}: {len(vendor_data)} รายการ")
        
        # เปรียบเทียบกับ JSON
        json_vendors = set()
        for data in json_data.values():
            v = data.get('vendor_code')
            if v:
                json_vendors.add(v)
        
        result_vendors = set(unique_vendors)
        
        st.markdown("### 🔍 เปรียบเทียบ:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vendors ใน JSON:**")
            for v in sorted(json_vendors):
                st.text(f"• {v}")
        
        with col2:
            st.markdown("**Vendors ในผลลัพธ์:**")
            for v in sorted(result_vendors):
                st.text(f"• {v}")
        
        # หา vendor ที่หาย
        missing_vendors = json_vendors - result_vendors
        if missing_vendors:
            st.error("❌ Vendors ที่หายไป:")
            for v in missing_vendors:
                st.error(f"   • {v}")
                
                # หาว่า vendor นี้มาจากไฟล์ไหน
                for json_file, data in json_data.items():
                    if data.get('vendor_code') == v:
                        st.warning(f"      → จาก {json_file}")
        else:
            st.success("✅ ไม่มี vendor หาย!")
    
    # แสดงตาราง
    st.markdown("### 📋 ตารางผลลัพธ์:")
    st.dataframe(results, use_container_width=True)
    else:
        st.warning("⚠️ ผลลัพธ์เป็น None หรือว่างเปล่า")
        st.info("💡 สาเหตุ: ไม่มี JSON ไฟล์ใดประมวลผลสำเร็จ")
else:
    st.warning("⚠️ ยังไม่มีผลลัพธ์ในระบบ")
    st.info("กรุณารันประมวลผลก่อน")

st.markdown("---")

# 5. สรุป
st.markdown("## 🎯 Step 5: สรุปปัญหา")

if len(pdf_files) > len(json_files):
    st.error(f"❌ ปัญหา: มี PDF {len(pdf_files)} ไฟล์ แต่สร้าง JSON ได้แค่ {len(json_files)} ไฟล์")
    st.info("💡 สาเหตุ: บาง PDF ประมวลผลล้มเหลว หรือ API error")
    st.markdown("**แนะนำ:** ลองรันใหม่อีกครั้ง หรือเพิ่ม delay ระหว่างไฟล์")
elif 'processing_results' in st.session_state:
    results = st.session_state.processing_results
    if results is not None and 'vendor_code' in results.columns:
        unique_vendors = len(results['vendor_code'].unique())
        if unique_vendors < len(json_files):
            st.error(f"❌ ปัญหา: มี JSON {len(json_files)} ไฟล์ แต่ผลลัพธ์มีแค่ {unique_vendors} vendors")
            st.info("💡 สาเหตุ: บาง vendor ไม่มีข้อมูลใน AP หรือถูกกรองออก")
            st.markdown("**แนะนำ:** ตรวจสอบไฟล์ AP ว่ามีข้อมูลครบทุก vendor หรือไม่")
        else:
            st.success("✅ ไม่พบปัญหา!")
else:
    st.info("ℹ️ กรุณารันประมวลผลก่อนเพื่อดู debug info")

st.markdown("---")

# ปุ่ม refresh
if st.button("🔄 Refresh", use_container_width=True):
    st.rerun()
