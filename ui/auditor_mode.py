"""
Auditor Mode UI - ส่วนที่ 2: Dashboard สำหรับผู้ตรวจสอบ
"""

import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path

from services.reporting_service import ReportingService
from config.settings import DIRECTORIES, STATUS_DEFINITIONS


def show_auditor_mode():
    """
    แสดง UI สำหรับโหมด Auditor (ส่วนที่ 2)
    """
    st.title("👨‍💼 For Auditor: Dashboard & รายงาน")
    
    # Back button
    if st.button("← กลับหน้าแรก"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Load session
    session_loaded = load_session_selector()
    
    if session_loaded:
        show_dashboard()
    else:
        show_no_session_message()


def load_session_selector():
    """
    แสดงตัวเลือก session และโหลดข้อมูล
    
    Returns:
        bool: True ถ้าโหลดสำเร็จ
    """
    st.markdown("### 📂 เลือก Session")
    
    results_folder = DIRECTORIES['results']
    
    # Find available sessions
    metadata_files = list(results_folder.glob("*_metadata.json"))
    
    if not metadata_files:
        return False
    
    # Create session options
    sessions = []
    for metadata_file in metadata_files:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            sessions.append({
                'name': metadata.get('session_name', 'Unknown'),
                'timestamp': metadata.get('timestamp', ''),
                'file': str(metadata_file),
                'metadata': metadata
            })
    
    # Sort by timestamp (newest first)
    sessions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Session selector
    session_options = [
        f"{s['name']} ({s['timestamp'][:19] if s['timestamp'] else 'Unknown time'})"
        for s in sessions
    ]
    
    selected_idx = st.selectbox(
        "เลือก session ที่ต้องการดู",
        range(len(session_options)),
        format_func=lambda i: session_options[i]
    )
    
    selected_session = sessions[selected_idx]
    
    # Load results
    metadata = selected_session['metadata']
    session_name = selected_session['name']
    
    # Try to load results
    results_file = results_folder / f"{session_name}_results.parquet"
    
    if results_file.exists():
        results_df = pd.read_parquet(results_file)
        st.session_state.current_results = results_df
        st.session_state.current_metadata = metadata
        st.session_state.current_session_name = session_name
        return True
    else:
        st.error(f"❌ ไม่พบไฟล์ผลลัพธ์: {results_file}")
        return False


def show_no_session_message():
    """แสดงข้อความเมื่อไม่มี session"""
    st.info("""
    ℹ️ **ยังไม่มี session ที่บันทึกไว้**
    
    กรุณาไปที่โหมด **For Analyze** เพื่อประมวลผลข้อมูลก่อน
    จากนั้นผลลัพธ์จะถูกบันทึกและแสดงที่นี่
    """)


def show_dashboard():
    """แสดง Dashboard หลัก"""
    
    results_df = st.session_state.current_results
    metadata = st.session_state.current_metadata
    
    # Session info
    with st.expander("ℹ️ ข้อมูล Session"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Session:** {st.session_state.current_session_name}")
            st.markdown(f"**เวลา:** {metadata.get('timestamp', 'N/A')[:19]}")
        
        with col2:
            summary = metadata.get('summary', {})
            st.markdown(f"**PDF ประมวลผล:** {summary.get('pdfs_processed', 0)}")
            st.markdown(f"**จำนวนรายการ:** {summary.get('total_records', 0)}")
    
    st.markdown("---")
    
    # Filters
    show_filters(results_df)
    
    st.markdown("---")
    
    # Apply filters
    filtered_df = apply_filters(results_df)
    
    # Metrics
    show_metrics(filtered_df)
    
    st.markdown("---")
    
    # Data table
    show_data_table(filtered_df)
    
    st.markdown("---")
    
    # Export section
    show_export_section(filtered_df)


def show_filters(df):
    """แสดงตัวกรองข้อมูล"""
    st.markdown("### 🔍 กรองข้อมูล")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Vendor filter
        vendors = ['ทั้งหมด'] + sorted(df['vendor_code'].unique().tolist())
        selected_vendors = st.multiselect(
            "Vendor",
            options=vendors,
            default=['ทั้งหมด']
        )
        st.session_state.filter_vendors = selected_vendors
    
    with col2:
        # Status filter
        if 'status' in df.columns:
            statuses = ['ทั้งหมด'] + sorted(df['status'].unique().tolist())
            selected_status = st.selectbox(
                "สถานะ",
                options=statuses
            )
            st.session_state.filter_status = selected_status
    
    with col3:
        # Division filter
        if 'division' in df.columns:
            divisions = ['ทั้งหมด'] + sorted(df['division'].unique().tolist())
        elif 'tta_key' in df.columns:
            # Extract division from tta_key
            divisions = ['ทั้งหมด'] + sorted(set([
                key.split('_')[1] for key in df['tta_key'].unique()
            ]))
        else:
            divisions = ['ทั้งหมด']
        
        selected_division = st.selectbox(
            "Division",
            options=divisions
        )
        st.session_state.filter_division = selected_division


def apply_filters(df):
    """
    ใช้ตัวกรองกับข้อมูล
    
    Args:
        df: DataFrame ต้นฉบับ
        
    Returns:
        DataFrame ที่กรองแล้ว
    """
    filtered_df = df.copy()
    
    # Vendor filter
    vendors = st.session_state.get('filter_vendors', ['ทั้งหมด'])
    if 'ทั้งหมด' not in vendors:
        filtered_df = filtered_df[filtered_df['vendor_code'].isin(vendors)]
    
    # Status filter
    status = st.session_state.get('filter_status', 'ทั้งหมด')
    if status != 'ทั้งหมด' and 'status' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['status'] == status]
    
    # Division filter
    division = st.session_state.get('filter_division', 'ทั้งหมด')
    if division != 'ทั้งหมด':
        if 'division' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['division'] == division]
        elif 'tta_key' in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df['tta_key'].str.split('_').str[1] == division
            ]
    
    return filtered_df


def show_metrics(df):
    """แสดง Metrics cards"""
    st.markdown("### 📊 สรุปข้อมูล")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        unique_vendors = df['vendor_code'].nunique() if 'vendor_code' in df.columns else 0
        st.metric("จำนวน Vendors", unique_vendors)
    
    with col2:
        total_records = len(df)
        st.metric("จำนวนรายการ", total_records)
    
    with col3:
        if 'should_collect' in df.columns:
            total_should = df['should_collect'].sum()
            st.metric("ควรเรียกเก็บ", f"{total_should:,.0f} บาท")
        else:
            st.metric("ควรเรียกเก็บ", "N/A")
    
    with col4:
        if 'actually_collected' in df.columns:
            total_actual = df['actually_collected'].sum()
            st.metric("เรียกเก็บจริง", f"{total_actual:,.0f} บาท")
            
            # Collection rate
            if 'should_collect' in df.columns and total_should > 0:
                collection_rate = (total_actual / total_should) * 100
                delta_color = "normal" if collection_rate >= 95 else "inverse"
        else:
            st.metric("เรียกเก็บจริง", "N/A")
    
    # Status breakdown
    if 'status' in df.columns:
        st.markdown("")
        st.markdown("#### สถานะการเก็บเงิน")
        
        status_counts = df['status'].value_counts()
        
        cols = st.columns(len(status_counts))
        for idx, (status, count) in enumerate(status_counts.items()):
            with cols[idx]:
                # Get emoji for status
                emoji = "✅" if "ครบ" in status else ("❌" if "ขาด" in status else "⚠️")
                st.metric(f"{emoji} {status}", count)


def show_data_table(df):
    """แสดงตารางข้อมูล"""
    st.markdown("### 📋 รายละเอียดข้อมูล")
    
    # Column selection
    if len(df.columns) > 10:
        with st.expander("⚙️ เลือกคอลัมน์ที่จะแสดง"):
            all_columns = df.columns.tolist()
            default_columns = [
                'vendor_code', 'vendor_name', 'category_code', 'category_name',
                'should_collect', 'actually_collected', 'difference', 'status'
            ]
            default_columns = [col for col in default_columns if col in all_columns]
            
            selected_columns = st.multiselect(
                "เลือกคอลัมน์",
                options=all_columns,
                default=default_columns
            )
            
            if selected_columns:
                display_df = df[selected_columns]
            else:
                display_df = df
    else:
        display_df = df
    
    # Data table with styling
    st.dataframe(
        display_df,
        use_container_width=True,
        height=500
    )
    
    # Vendor drill-down
    if 'vendor_code' in df.columns:
        st.markdown("---")
        st.markdown("#### 🔎 Drill-down: ดูรายละเอียด Vendor")
        
        vendors = sorted(df['vendor_code'].unique().tolist())
        selected_vendor = st.selectbox(
            "เลือก Vendor",
            options=vendors,
            format_func=lambda v: f"{v} - {df[df['vendor_code']==v]['vendor_name'].iloc[0] if 'vendor_name' in df.columns else v}"
        )
        
        if selected_vendor:
            vendor_data = df[df['vendor_code'] == selected_vendor]
            
            # Vendor summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'should_collect' in vendor_data.columns:
                    st.metric("ควรเรียกเก็บ", f"{vendor_data['should_collect'].sum():,.0f}")
            
            with col2:
                if 'actually_collected' in vendor_data.columns:
                    st.metric("เรียกเก็บจริง", f"{vendor_data['actually_collected'].sum():,.0f}")
            
            with col3:
                if 'difference' in vendor_data.columns:
                    diff = vendor_data['difference'].sum()
                    st.metric("ส่วนต่าง", f"{diff:,.0f}", delta_color="inverse" if diff < 0 else "normal")
            
            # Vendor detail table
            st.dataframe(vendor_data, use_container_width=True)


def show_export_section(df):
    """แสดงส่วน Export"""
    st.markdown("### 💾 Export รายงาน")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Excel (จัดรูปแบบ)")
        
        if st.button("📥 สร้างรายงาน Excel", use_container_width=True):
            reporter = ReportingService()
            
            # Create summary
            if 'should_collect' in df.columns:
                summary_df = df.groupby(['vendor_code', 'vendor_name']).agg({
                    'should_collect': 'sum',
                    'actually_collected': 'sum',
                    'difference': 'sum'
                }).reset_index()
            else:
                summary_df = None
            
            # Export
            excel_file = reporter.export_reconciliation_report(
                reconciliation_df=df,
                summary_df=summary_df,
                filename=f"audit_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            # Download button
            with open(excel_file, 'rb') as f:
                st.download_button(
                    "💾 ดาวน์โหลด Excel",
                    data=f,
                    file_name=os.path.basename(excel_file),
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True
                )
    
    with col2:
        st.markdown("#### CSV (ข้อมูลดิบ)")
        
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            "💾 ดาวน์โหลด CSV",
            data=csv,
            file_name=f"audit_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv',
            use_container_width=True
        )
    
    # Export filtered data note
    if 'filter_vendors' in st.session_state or 'filter_status' in st.session_state:
        st.info("ℹ️ การ export จะใช้ข้อมูลที่กรองแล้ว")
