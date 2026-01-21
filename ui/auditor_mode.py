"""
Auditor Mode - Problem-Reason-Action Dashboard
แสดงกราฟและวิเคราะห์ตามหลัก Problem → Reason → Action
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show_auditor_mode():
    """แสดง Dashboard สำหรับ Auditor"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0;">👨‍💼 Auditor Dashboard</h1>
        <p style="color: #e0e0e0; margin: 5px 0 0 0;">Problem → Reason → Action Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Back to Home"):
        st.session_state.mode = None
        st.rerun()
    
    st.markdown("---")
    
    # Load session
    if not load_session():
        show_no_session_message()
        return
    
    # Main Dashboard
    show_dashboard()


def load_session():
    """โหลด session data"""
    
    # เช็ค processing_results จาก Analyze mode
    if 'processing_results' in st.session_state and st.session_state.processing_results is not None:
        st.session_state.dashboard_results = st.session_state.processing_results
        return True
    
    # เช็ค saved_sessions
    if 'saved_sessions' in st.session_state and st.session_state.saved_sessions:
        sessions = st.session_state.saved_sessions
        
        # ใช้ session ล่าสุด
        latest_session = list(sessions.values())[-1]
        st.session_state.dashboard_results = latest_session.get('results')
        return True
    
    return False


def show_no_session_message():
    """แสดงข้อความเมื่อไม่มี session"""
    st.warning("⚠️ No data available")
    st.info("""
    💡 **How to get started:**
    1. Go to "For Analyze" mode
    2. Run processing
    3. Come back here to view dashboard
    """)


def show_dashboard():
    """แสดง Dashboard หลัก"""
    
    results = st.session_state.dashboard_results
    
    if results is None or len(results) == 0:
        st.error("❌ No results data")
        return
    
    # Executive Summary
    show_executive_summary(results)
    
    st.markdown("---")
    
    # Problem-Reason-Action Framework
    tabs = st.tabs([
        "🔴 PROBLEM: Issues Overview",
        "🔍 REASON: Root Cause Analysis", 
        "✅ ACTION: Recommendations"
    ])
    
    with tabs[0]:
        show_problem_section(results)
    
    with tabs[1]:
        show_reason_section(results)
    
    with tabs[2]:
        show_action_section(results)


def show_executive_summary(results):
    """แสดงสรุปผู้บริหาร"""
    
    st.markdown("### 📊 Executive Summary")
    
    # คำนวณตัวเลขสำคัญ
    total_should = results['should_collect'].sum() if 'should_collect' in results.columns else 0
    total_actual = results['actually_collected'].sum() if 'actually_collected' in results.columns else 0
    total_diff = results['difference'].sum() if 'difference' in results.columns else 0
    
    # นับ status
    status_counts = results['status'].value_counts().to_dict() if 'status' in results.columns else {}
    match_count = status_counts.get('MATCH', 0)
    over_count = status_counts.get('OVER', 0)
    under_count = status_counts.get('UNDER', 0)
    
    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric(
        "💰 Should Collect",
        f"{total_should:,.0f}",
        help="Total amount should be collected"
    )
    
    col2.metric(
        "💵 Actually Collected", 
        f"{total_actual:,.0f}",
        delta=f"{total_diff:,.0f}",
        delta_color="normal" if total_diff >= 0 else "inverse"
    )
    
    col3.metric(
        "📊 Total Items",
        f"{len(results)}",
        help="Total allowance items"
    )
    
    col4.metric(
        "🏢 Vendors",
        f"{results['vendor_code'].nunique()}" if 'vendor_code' in results.columns else "0"
    )
    
    # Overall Status
    if abs(total_diff) < 1000:
        overall_status = "🟡 MATCHED"
        status_color = "#FFD700"
    elif total_diff > 0:
        overall_status = "🔴 OVER-COLLECTED"
        status_color = "#FF6B6B"
    else:
        overall_status = "🟢 UNDER-COLLECTED"
        status_color = "#4ECDC4"
    
    col5.markdown(f"""
    <div style="padding: 10px; background: {status_color}; border-radius: 8px; text-align: center;">
        <p style="margin: 0; font-size: 12px; color: white;">Overall Status</p>
        <p style="margin: 5px 0 0 0; font-size: 18px; font-weight: bold; color: white;">{overall_status.split()[1]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Status Distribution
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Pie Chart
        fig = go.Figure(data=[go.Pie(
            labels=['MATCH', 'OVER', 'UNDER'],
            values=[match_count, over_count, under_count],
            marker=dict(colors=['#FFD700', '#FF6B6B', '#4ECDC4']),
            hole=0.4,
            textinfo='label+percent+value',
            textfont=dict(size=14)
        )])
        
        fig.update_layout(
            title="Status Distribution",
            height=300,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Status Summary:**")
        st.metric("✅ MATCH", f"{match_count} ({match_count/len(results)*100:.1f}%)")
        st.metric("⚠️ OVER", f"{over_count} ({over_count/len(results)*100:.1f}%)")
        st.metric("❌ UNDER", f"{under_count} ({under_count/len(results)*100:.1f}%)")


def show_problem_section(results):
    """🔴 PROBLEM: แสดงปัญหาที่พบ"""
    
    st.markdown("## 🔴 PROBLEM: Issues Overview")
    st.markdown("**ปัญหาที่พบในการเรียกเก็บเงิน**")
    
    # 1. Top Issues by Amount
    st.markdown("### 1️⃣ Top Issues by Variance Amount")
    
    # เรียงตาม difference (absolute value)
    top_issues = results.copy()
    top_issues['abs_diff'] = top_issues['difference'].abs()
    top_issues = top_issues.nlargest(10, 'abs_diff')
    
    # Bar chart
    fig = go.Figure()
    
    colors = []
    for status in top_issues['status']:
        if status == 'MATCH':
            colors.append('#FFD700')
        elif status == 'OVER':
            colors.append('#FF6B6B')
        else:
            colors.append('#4ECDC4')
    
    fig.add_trace(go.Bar(
        x=top_issues['difference'],
        y=top_issues['category_name'] + ' (' + top_issues['vendor_name'].str[:20] + '...)',
        orientation='h',
        marker=dict(color=colors),
        text=top_issues['difference'].apply(lambda x: f"{x:,.0f}"),
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Top 10 Issues by Variance Amount",
        xaxis_title="Difference (Baht)",
        yaxis_title="",
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Issues by Vendor
    st.markdown("### 2️⃣ Issues by Vendor")
    
    vendor_summary = results.groupby('vendor_name').agg({
        'difference': 'sum',
        'status': lambda x: (x == 'UNDER').sum()  # Count UNDER items
    }).reset_index()
    
    vendor_summary.columns = ['vendor_name', 'total_diff', 'under_count']
    vendor_summary = vendor_summary.sort_values('total_diff', ascending=True).head(10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=vendor_summary['total_diff'],
        y=vendor_summary['vendor_name'].str[:30],
        orientation='h',
        marker=dict(
            color=vendor_summary['total_diff'],
            colorscale='RdYlGn',
            showscale=True
        ),
        text=vendor_summary['total_diff'].apply(lambda x: f"{x:,.0f}"),
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Top 10 Vendors with Variance",
        xaxis_title="Total Difference (Baht)",
        yaxis_title="",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Issues by Category
    st.markdown("### 3️⃣ Issues by Allowance Category")
    
    category_summary = results.groupby('category_code').agg({
        'difference': 'sum',
        'category_name': 'first',
        'status': 'count'
    }).reset_index()
    
    category_summary.columns = ['category_code', 'total_diff', 'category_name', 'count']
    category_summary = category_summary.sort_values('total_diff', key=abs, ascending=False).head(10)
    
    fig = px.bar(
        category_summary,
        x='category_code',
        y='total_diff',
        color='total_diff',
        color_continuous_scale='RdYlGn',
        text='total_diff',
        hover_data=['category_name', 'count']
    )
    
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(
        title="Top 10 Categories with Variance",
        xaxis_title="Category Code",
        yaxis_title="Total Difference (Baht)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_reason_section(results):
    """🔍 REASON: วิเคราะห์สาเหตุ"""
    
    st.markdown("## 🔍 REASON: Root Cause Analysis")
    st.markdown("**วิเคราะห์สาเหตุของปัญหา**")
    
    # 1. Variance Distribution
    st.markdown("### 1️⃣ Variance Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram
        fig = px.histogram(
            results,
            x='variance_pct',
            nbins=50,
            color='status',
            color_discrete_map={
                'MATCH': '#FFD700',
                'OVER': '#FF6B6B',
                'UNDER': '#4ECDC4'
            },
            title="Distribution of Variance %"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Box plot
        fig = px.box(
            results,
            x='status',
            y='variance_pct',
            color='status',
            color_discrete_map={
                'MATCH': '#FFD700',
                'OVER': '#FF6B6B',
                'UNDER': '#4ECDC4'
            },
            title="Variance % by Status"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # 2. Pattern Analysis
    st.markdown("### 2️⃣ Pattern Analysis")
    
    # Scatter plot: Should vs Actually
    fig = px.scatter(
        results,
        x='should_collect',
        y='actually_collected',
        color='status',
        size='difference',
        hover_data=['vendor_name', 'category_name'],
        color_discrete_map={
            'MATCH': '#FFD700',
            'OVER': '#FF6B6B',
            'UNDER': '#4ECDC4'
        },
        title="Should Collect vs Actually Collected"
    )
    
    # เพิ่มเส้น y=x
    max_val = max(results['should_collect'].max(), results['actually_collected'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(dash='dash', color='gray'),
        name='Perfect Match',
        showlegend=True
    ))
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Root Cause Summary
    st.markdown("### 3️⃣ Identified Root Causes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 OVER-COLLECTED (เกิน):**")
        over_items = results[results['status'] == 'OVER']
        if len(over_items) > 0:
            st.info(f"""
            - จำนวน: {len(over_items)} รายการ
            - ยอดรวมที่เกิน: {over_items['difference'].sum():,.0f} บาท
            - เฉลี่ย % ที่เกิน: {over_items['variance_pct'].mean():.2f}%
            
            **สาเหตุที่เป็นไปได้:**
            - เรียกเก็บซ้ำซ้อน
            - คำนวณอัตราผิด
            - ไม่ปรับลดตาม credit note
            """)
        else:
            st.success("ไม่พบการเรียกเก็บเกิน")
    
    with col2:
        st.markdown("**🟢 UNDER-COLLECTED (ขาด):**")
        under_items = results[results['status'] == 'UNDER']
        if len(under_items) > 0:
            st.warning(f"""
            - จำนวน: {len(under_items)} รายการ
            - ยอดรวมที่ขาด: {abs(under_items['difference'].sum()):,.0f} บาท
            - เฉลี่ย % ที่ขาด: {abs(under_items['variance_pct'].mean()):.2f}%
            
            **สาเหตุที่เป็นไปได้:**
            - ยังไม่เรียกเก็บครบ
            - มีส่วนลดที่ยังไม่นำมาคิด
            - ข้อมูลยังไม่อัปเดต
            """)
        else:
            st.success("ไม่พบการเรียกเก็บขาด")


def show_action_section(results):
    """✅ ACTION: แนะนำการแก้ไข"""
    
    st.markdown("## ✅ ACTION: Recommended Actions")
    st.markdown("**แนวทางแก้ไขและติดตาม**")
    
    # 1. Priority Actions
    st.markdown("### 1️⃣ Priority Actions (High Impact)")
    
    # หารายการที่มี impact สูง
    high_impact = results.copy()
    high_impact['abs_diff'] = high_impact['difference'].abs()
    high_impact = high_impact[high_impact['abs_diff'] > 10000]  # มากกว่า 10K
    high_impact = high_impact.sort_values('abs_diff', ascending=False)
    
    if len(high_impact) > 0:
        st.error(f"⚠️ พบ {len(high_impact)} รายการที่ต้องดำเนินการด่วน (ส่วนต่าง > 10,000 บาท)")
        
        # แสดงตาราง
        action_table = high_impact[['vendor_name', 'category_name', 'difference', 'status']].head(10).copy()
        action_table['action'] = action_table.apply(
            lambda row: '🔴 ตรวจสอบด่วน' if row['status'] == 'OVER' else '🟢 ติดตามเรียกเก็บ',
            axis=1
        )
        action_table.columns = ['Vendor', 'Category', 'Variance', 'Status', 'Action Required']
        
        st.dataframe(action_table, use_container_width=True, hide_index=True)
    else:
        st.success("✅ ไม่พบรายการที่ต้องดำเนินการด่วน")
    
    # 2. Follow-up by Vendor
    st.markdown("### 2️⃣ Vendor Follow-up Plan")
    
    vendor_action = results.groupby('vendor_name').agg({
        'difference': ['sum', 'count'],
        'status': lambda x: (x == 'UNDER').sum()
    }).reset_index()
    
    vendor_action.columns = ['vendor_name', 'total_diff', 'item_count', 'under_count']
    vendor_action = vendor_action[vendor_action['total_diff'].abs() > 5000]
    vendor_action = vendor_action.sort_values('total_diff', key=abs, ascending=False)
    
    if len(vendor_action) > 0:
        for idx, row in vendor_action.head(5).iterrows():
            vendor = row['vendor_name']
            diff = row['total_diff']
            items = row['item_count']
            under = row['under_count']
            
            if diff > 0:
                action_type = "🔴 OVER-COLLECTED"
                action = f"ตรวจสอบและออก Credit Note {diff:,.0f} บาท"
                color = "#ffe6e6"
            else:
                action_type = "🟢 UNDER-COLLECTED"
                action = f"ออกใบแจ้งหนี้เพิ่ม {abs(diff):,.0f} บาท"
                color = "#e6f7ff"
            
            st.markdown(f"""
            <div style="padding: 15px; background: {color}; border-radius: 8px; margin-bottom: 10px;">
                <strong>{action_type}: {vendor[:50]}</strong><br>
                📊 รายการ: {items} รายการ | ส่วนต่าง: {diff:,.0f} บาท<br>
                ✅ <strong>Action:</strong> {action}
            </div>
            """, unsafe_allow_html=True)
    
    # 3. Action Timeline
    st.markdown("### 3️⃣ Recommended Timeline")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🔴 Immediate (0-7 days)**")
        immediate = results[results['difference'].abs() > 50000]
        st.metric("Items to review", len(immediate))
        st.caption("Variance > 50K baht")
    
    with col2:
        st.markdown("**🟡 Short-term (1-4 weeks)**")
        short_term = results[
            (results['difference'].abs() > 10000) & 
            (results['difference'].abs() <= 50000)
        ]
        st.metric("Items to follow up", len(short_term))
        st.caption("Variance 10K-50K baht")
    
    with col3:
        st.markdown("**🟢 Long-term (1-3 months)**")
        long_term = results[results['difference'].abs() <= 10000]
        st.metric("Items to monitor", len(long_term))
        st.caption("Variance < 10K baht")
    
    # 4. Export Actions
    st.markdown("---")
    st.markdown("### 📥 Export Action Plan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export high priority items
        if len(high_impact) > 0:
            csv = high_impact[['vendor_name', 'category_name', 'difference', 'status']].to_csv(index=False)
            st.download_button(
                "📥 Download Priority Actions (CSV)",
                data=csv.encode('utf-8-sig'),
                file_name="priority_actions.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        # Export vendor follow-up
        if len(vendor_action) > 0:
            csv = vendor_action.to_csv(index=False)
            st.download_button(
                "📥 Download Vendor Follow-up Plan (CSV)",
                data=csv.encode('utf-8-sig'),
                file_name="vendor_followup.csv",
                mime="text/csv",
                use_container_width=True
            )
