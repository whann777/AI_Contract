# คัดลอกไฟล์นี้ไปแทนที่ ui/auditor_mode.py ใน repo จริงของคุณ

"""
Auditor Dashboard - PRA Framework (Problem → Reason → Action)
Dashboard สำหรับผู้ตรวจสอบตามกรอบ PRA
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO


def show_auditor_mode():
    """แสดง Dashboard แบบ PRA Framework"""
    
    st.title("👨‍💼 Auditor Dashboard")
    st.markdown("**Problem → Reason → Action Framework**")
    
    # Back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
    
    st.markdown("---")
    
    # Load data
    if not load_dashboard_data():
        show_no_data_message()
        return
    
    # Get data
    df = st.session_state.dashboard_results.copy()
    
    # Filters in sidebar
    df_filtered = show_filters(df)
    
    # PRA Tabs
    tab1, tab2, tab3 = st.tabs(["🚨 PROBLEM", "🔍 REASON", "✅ ACTION"])
    
    with tab1:
        build_problem_tab(df_filtered)
    
    with tab2:
        build_reason_tab(df_filtered)
    
    with tab3:
        build_action_tab(df_filtered)


def load_dashboard_data():
    """โหลดข้อมูลจาก session_state"""
    
    # Check from Analyze mode
    if 'processing_results' in st.session_state and st.session_state.processing_results is not None:
        st.session_state.dashboard_results = st.session_state.processing_results
        return True
    
    # Check saved sessions
    if 'saved_sessions' in st.session_state and st.session_state.saved_sessions:
        sessions = st.session_state.saved_sessions
        latest_key = list(sessions.keys())[-1]
        latest_session = sessions[latest_key]
        
        if 'results' in latest_session and latest_session['results'] is not None:
            st.session_state.dashboard_results = latest_session['results']
            return True
    
    return False


def show_no_data_message():
    """แสดงข้อความเมื่อไม่มีข้อมูล"""
    st.warning("⚠️ No data available for dashboard")
    st.info("""
    **How to get started:**
    1. Go to "For Analyze" mode
    2. Process your PDF files (if not done)
    3. Click "Analyze" to generate results
    4. Return here to view the dashboard
    """)


def show_filters(df):
    """แสดง Filters ใน Sidebar"""
    
    st.sidebar.markdown("## 🎛️ Filters")
    
    # Vendor filter
    if 'vendor_code' in df.columns:
        vendors = ['All'] + sorted(df['vendor_code'].unique().tolist())
        selected_vendors = st.sidebar.multiselect(
            "Vendors",
            options=vendors,
            default=['All']
        )
        
        if 'All' not in selected_vendors and selected_vendors:
            df = df[df['vendor_code'].isin(selected_vendors)]
    
    # Category filter
    if 'category_code' in df.columns:
        categories = ['All'] + sorted(df['category_code'].unique().tolist())
        selected_categories = st.sidebar.multiselect(
            "Categories",
            options=categories,
            default=['All']
        )
        
        if 'All' not in selected_categories and selected_categories:
            df = df[df['category_code'].isin(selected_categories)]
    
    # Status filter
    if 'status' in df.columns:
        statuses = ['All'] + sorted(df['status'].unique().tolist())
        selected_status = st.sidebar.multiselect(
            "Status",
            options=statuses,
            default=['All']
        )
        
        if 'All' not in selected_status and selected_status:
            df = df[df['status'].isin(selected_status)]
    
    st.sidebar.markdown("---")
    st.sidebar.metric("Filtered Records", len(df))
    
    return df


def build_problem_tab(df):
    """Tab 1: PROBLEM - What is wrong?"""
    
    st.markdown("### 🚨 PROBLEM: What is wrong?")
    st.markdown("Overview of discrepancies and revenue leakage risks")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Expected
    if 'should_collect' in df.columns:
        total_expected = df['should_collect'].sum()
        col1.metric(
            "💰 Total Expected",
            f"฿{total_expected:,.0f}"
        )
    
    # Total Actual
    if 'actually_collected' in df.columns:
        total_actual = df['actually_collected'].sum()
        col2.metric(
            "💵 Total Actual",
            f"฿{total_actual:,.0f}"
        )
    
    # Total Difference
    if 'difference' in df.columns:
        total_diff = df['difference'].sum()
        col3.metric(
            "📊 Total Difference",
            f"฿{total_diff:,.0f}",
            delta=f"{(total_diff/total_expected*100):.1f}%" if total_expected > 0 else "0%"
        )
    
    # Vendors at Risk
    if 'vendor_code' in df.columns and 'difference' in df.columns:
        vendors_at_risk = len(df[df['difference'] < -1]['vendor_code'].unique())
        col4.metric(
            "⚠️ Vendors at Risk",
            vendors_at_risk
        )
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Expected Support by Vendor (Top 10)")
        if 'vendor_code' in df.columns and 'should_collect' in df.columns:
            vendor_summary = df.groupby('vendor_code')['should_collect'].sum().sort_values(ascending=False).head(10)
            
            fig = px.bar(
                x=vendor_summary.values,
                y=vendor_summary.index,
                orientation='h',
                labels={'x': 'Amount (฿)', 'y': 'Vendor'},
                color=vendor_summary.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data not available")
    
    with col2:
        st.markdown("#### Difference by Vendor (Top 10)")
        if 'vendor_code' in df.columns and 'difference' in df.columns:
            diff_summary = df.groupby('vendor_code')['difference'].sum().sort_values().head(10)
            
            # Color: red if negative, green if positive
            colors = ['#FF6B6B' if x < 0 else '#90EE90' for x in diff_summary.values]
            
            fig = go.Figure(go.Bar(
                x=diff_summary.values,
                y=diff_summary.index,
                orientation='h',
                marker_color=colors
            ))
            fig.update_layout(
                xaxis_title='Difference (฿)',
                yaxis_title='Vendor',
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data not available")
    
    # Revenue Leakage Risk
    st.markdown("---")
    st.markdown("#### 🔴 Revenue Leakage Risk")
    
    if 'difference' in df.columns:
        # Calculate risk (negative difference = under-collected)
        df_risk = df[df['difference'] < -1].copy()
        risk_amount = abs(df_risk['difference'].sum())
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Amount", f"฿{risk_amount:,.0f}")
        col2.metric("Affected Records", len(df_risk))
        col3.metric("% of Total", f"{(risk_amount/total_expected*100):.1f}%" if total_expected > 0 else "0%")
        
        # Top risk vendors
        if 'vendor_code' in df_risk.columns:
            st.markdown("**Top 5 Vendors by Risk:**")
            top_risk = df_risk.groupby('vendor_code')['difference'].sum().sort_values().head(5)
            
            risk_df = pd.DataFrame({
                'Vendor': top_risk.index,
                'Risk Amount': [f"฿{abs(x):,.0f}" for x in top_risk.values]
            })
            st.dataframe(risk_df, use_container_width=True, hide_index=True)


def build_reason_tab(df):
    """Tab 2: REASON - Why it happens?"""
    
    st.markdown("### 🔍 REASON: Why it happens?")
    st.markdown("Root cause analysis - ทำไมถึงเกิดปัญหานี้")
    
    st.markdown("---")
    st.markdown("#### 🎯 Key Questions to Answer")
    
    questions = [
        "**Support แบบไหนคำนวณยาก?** - เห็น complexity ของแต่ละ category",
        "**เป็น % หรือ Fix amount?** - ส่งผลต่อวิธีการตรวจสอบ",
        "**ผูกกับ Purchase amount หรือไม่?** - ถ้าผูก ต้องเช็ค AP ให้ถูก",
        "**Payment term (annual/other) ทำให้ delay หรือไม่?** - Annual เสี่ยงลืมเคลม"
    ]
    
    for q in questions:
        st.markdown(f"- {q}")
    
    st.markdown("---")
    
    # Detect calculation type from data
    df_analysis = df.copy()
    
    # Try to get calculation type from service (if available)
    calc_type_available = False
    if hasattr(st.session_state, 'service'):
        try:
            service = st.session_state.service
            calculated_df = service.recon_system.calculated_allowances
            
            if calculated_df is not None and 'calculation_type' in calculated_df.columns:
                # Merge calculation_type into df_analysis
                merge_cols = ['vendor_code', 'category_code']
                if all(col in df_analysis.columns and col in calculated_df.columns for col in merge_cols):
                    calc_type_df = calculated_df[merge_cols + ['calculation_type', 'rate_percent', 
                                                                'fix_amount', 'payment_terms']].drop_duplicates()
                    df_analysis = df_analysis.merge(calc_type_df, on=merge_cols, how='left')
                    calc_type_available = True
        except Exception as e:
            st.warning(f"Could not load calculation details: {str(e)}")
    
    # Charts Row 1
    st.markdown("#### 📊 Category Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Expected Support by Category")
        if 'category_code' in df_analysis.columns and 'should_collect' in df_analysis.columns:
            cat_summary = df_analysis.groupby('category_code')['should_collect'].sum().sort_values(ascending=False)
            
            # Bar chart (better than pie for many categories)
            fig = px.bar(
                x=cat_summary.values,
                y=cat_summary.index,
                orientation='h',
                labels={'x': 'Total Expected (฿)', 'y': 'Category'},
                color=cat_summary.values,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Insight
            top_cat = cat_summary.index[0] if len(cat_summary) > 0 else 'N/A'
            top_pct = (cat_summary.iloc[0] / cat_summary.sum() * 100) if len(cat_summary) > 0 else 0
            st.info(f"💡 **Top Category:** {top_cat} ({top_pct:.1f}% of total)")
        else:
            st.info("Data not available")
    
    with col2:
        st.markdown("##### Calculation Type Distribution")
        if calc_type_available and 'calculation_type' in df_analysis.columns:
            calc_counts = df_analysis['calculation_type'].value_counts()
            
            # Bar chart (better than donut when there are many types)
            fig = go.Figure(data=[go.Bar(
                x=calc_counts.index,
                y=calc_counts.values,
                marker_color=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe'][:len(calc_counts)]
            )])
            fig.update_layout(
                xaxis_title='Calculation Type',
                yaxis_title='Count',
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Insight
            pct_based = df_analysis[df_analysis['calculation_type'].str.contains('%', na=False)]
            pct_count = len(pct_based)
            pct_pct = (pct_count / len(df_analysis) * 100) if len(df_analysis) > 0 else 0
            st.info(f"💡 **Percentage-based:** {pct_count} records ({pct_pct:.1f}%)")
        else:
            st.warning("⚠️ Calculation type not available - need to run analysis first")
    
    # Charts Row 2: Treemap
    st.markdown("---")
    st.markdown("#### 🗺️ Category Treemap (Visual Hierarchy)")
    
    if 'category_code' in df_analysis.columns and 'should_collect' in df_analysis.columns:
        # Prepare data for treemap
        treemap_data = df_analysis.groupby(['category_code']).agg({
            'should_collect': 'sum'
        }).reset_index()
        
        if len(treemap_data) > 0:
            fig = px.treemap(
                treemap_data,
                path=['category_code'],
                values='should_collect',
                color='should_collect',
                color_continuous_scale='RdYlGn',
                labels={'should_collect': 'Expected (฿)'}
            )
            fig.update_traces(textinfo="label+value+percent parent")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption("💡 **ขนาดของกล่อง** = ยอดเงิน Expected | **สี** = ความเสี่ยง (แดง=สูง, เขียว=ต่ำ)")
    
    # Support Logic Breakdown Table
    st.markdown("---")
    st.markdown("#### 📋 Support Logic Breakdown")
    st.caption("🎯 **นี่คือจุดที่ IS project ดูเทพ** - เห็นรายละเอียดทุก category ว่าคำนวณยังไง")
    
    # Build comprehensive table
    table_cols = ['category_code', 'category_name']
    
    if calc_type_available:
        for col in ['calculation_type', 'rate_percent', 'fix_amount', 'payment_terms']:
            if col in df_analysis.columns:
                table_cols.append(col)
    
    # Add financial columns
    for col in ['should_collect', 'actually_collected', 'difference', 'status']:
        if col in df_analysis.columns:
            table_cols.append(col)
    
    if len(table_cols) > 2:
        # Group by category for summary view
        display_df = df_analysis[table_cols].copy()
        
        # Format numbers for display
        for col in ['rate_percent', 'fix_amount', 'should_collect', 'actually_collected', 'difference']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:,.2f}" if x is not None and str(x) != 'nan' else ""
                )
        
        st.dataframe(
            display_df.head(50),  # Show first 50 for performance
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        st.caption(f"📊 Showing first 50 of {len(display_df)} records")
    else:
        st.info("⚠️ Need to run analysis first to see full breakdown")
    
    # Insights Section
    st.markdown("---")
    st.markdown("#### 💡 Key Insights for Auditor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Calculation Complexity:**")
        
        if calc_type_available and 'calculation_type' in df_analysis.columns:
            # Percentage-based
            pct_based = df_analysis[df_analysis['calculation_type'].str.contains('%', na=False)]
            pct_count = len(pct_based)
            pct_amount = pct_based['should_collect'].sum() if 'should_collect' in pct_based.columns else 0
            
            st.markdown(f"- **อันไหนเป็น %:** {pct_count} records (฿{pct_amount:,.0f})")
            st.markdown("  → ต้องพึ่ง AP (purchase amount ต้องถูก)")
            
            # Fixed-based
            fix_based = df_analysis[df_analysis['calculation_type'].str.contains('Fix|fix|FIX', na=False)]
            fix_count = len(fix_based)
            fix_amount = fix_based['should_collect'].sum() if 'should_collect' in fix_based.columns else 0
            
            st.markdown(f"- **อันไหน Fix:** {fix_count} records (฿{fix_amount:,.0f})")
            st.markdown("  → ต้องเช็คสัญญา (ตามที่ระบุใน TTA)")
        else:
            st.markdown("- ข้อมูล calculation type ไม่พร้อม")
    
    with col2:
        st.markdown("**⏰ Payment Terms Risk:**")
        
        if calc_type_available and 'payment_terms' in df_analysis.columns:
            # Annual terms
            annual_df = df_analysis[df_analysis['payment_terms'].str.contains('annual|Annual|ANNUAL|yearly|Yearly', na=False)]
            annual_count = len(annual_df)
            annual_amount = annual_df['should_collect'].sum() if 'should_collect' in annual_df.columns else 0
            
            st.markdown(f"- **Annual terms:** {annual_count} records (฿{annual_amount:,.0f})")
            st.markdown("  → เสี่ยงลืมเคลม (ปีละครั้ง)")
            
            # Quarterly/Monthly
            frequent_df = df_analysis[df_analysis['payment_terms'].str.contains('quarter|Quarter|monthly|Monthly', na=False)]
            frequent_count = len(frequent_df)
            
            st.markdown(f"- **Quarterly/Monthly:** {frequent_count} records")
            st.markdown("  → เคลมบ่อย (ติดตามง่ายกว่า)")
        else:
            st.markdown("- ข้อมูล payment terms ไม่พร้อม")
    
    # Summary explanation
    st.markdown("---")
    st.markdown("#### 🔍 Why Manual Audit Takes So Long?")
    
    if calc_type_available:
        total_types = df_analysis['calculation_type'].nunique() if 'calculation_type' in df_analysis.columns else 0
        total_cats = df_analysis['category_code'].nunique() if 'category_code' in df_analysis.columns else 0
        
        reasons = [
            f"**{total_cats} categories** แต่ละ category คำนวณคนละแบบ",
            f"**{total_types} calculation types** ต้องเข้าใจ logic แต่ละแบบ",
            "**Mix ระหว่าง % และ Fix amount** - ต้องเช็คทั้ง AP และสัญญา",
            "**Payment terms ต่างกัน** - Annual/Quarterly/Monthly ต้องจำวันที่เคลม",
            "**Manual reconciliation** ต้องเทียบทีละรายการ (no automation)"
        ]
        
        for reason in reasons:
            st.markdown(f"✗ {reason}")
        
        st.success("✅ **AI-powered system แก้ปัญหานี้** โดยอัตโนมัติ - ทำใน 30 วินาที แทน 3 วัน!")
    else:
        st.info("💡 ต้องรัน analysis ก่อนเพื่อแสดง insights เต็มรูปแบบ")


def build_action_tab(df):
    """Tab 3: ACTION - What should we do next?"""
    
    st.markdown("### ✅ ACTION: What should we do next?")
    st.markdown("Prioritized action list with recommendations")
    
    # Priority thresholds
    col1, col2, col3 = st.columns(3)
    with col1:
        high_threshold = st.number_input(
            "HIGH Priority (฿)",
            min_value=0,
            value=10000,
            step=1000
        )
    with col2:
        med_threshold = st.number_input(
            "MEDIUM Priority (฿)",
            min_value=0,
            value=5000,
            step=1000
        )
    
    st.markdown("---")
    
    # Calculate priority
    df_action = df.copy()
    
    if 'difference' in df_action.columns:
        df_action['abs_diff'] = abs(df_action['difference'])
        
        def get_priority(diff):
            abs_diff = abs(diff)
            if abs_diff >= high_threshold:
                return 'HIGH'
            elif abs_diff >= med_threshold:
                return 'MEDIUM'
            else:
                return 'LOW'
        
        df_action['priority'] = df_action['difference'].apply(get_priority)
    else:
        df_action['priority'] = 'UNKNOWN'
    
    # Priority summary
    col1, col2, col3 = st.columns(3)
    
    if 'priority' in df_action.columns:
        high_count = len(df_action[df_action['priority'] == 'HIGH'])
        med_count = len(df_action[df_action['priority'] == 'MEDIUM'])
        low_count = len(df_action[df_action['priority'] == 'LOW'])
        
        col1.metric("🔴 HIGH Priority", high_count)
        col2.metric("🟡 MEDIUM Priority", med_count)
        col3.metric("🟢 LOW Priority", low_count)
    
    st.markdown("---")
    
    # Action Table
    st.markdown("#### 📋 Action List")
    
    # Select display columns
    display_cols = []
    for col in ['priority', 'vendor_code', 'vendor_name', 'category_code', 'category_name',
                'should_collect', 'actually_collected', 'difference', 'status']:
        if col in df_action.columns:
            display_cols.append(col)
    
    if display_cols:
        # Sort by priority and difference
        df_action_sorted = df_action[display_cols].copy()
        if 'abs_diff' in df_action.columns:
            df_action_sorted = df_action.sort_values('abs_diff', ascending=False)
        
        # Color priority column
        def color_priority(val):
            if val == 'HIGH':
                return 'background-color: #FF6B6B; color: white; font-weight: bold'
            elif val == 'MEDIUM':
                return 'background-color: #FFD700; color: black; font-weight: bold'
            elif val == 'LOW':
                return 'background-color: #90EE90; color: black; font-weight: bold'
            return ''
        
        if 'priority' in df_action_sorted.columns:
            styled = df_action_sorted.style.applymap(color_priority, subset=['priority'])
            st.dataframe(
                styled,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        else:
            st.dataframe(
                df_action_sorted,
                use_container_width=True,
                hide_index=True,
                height=400
            )
    
    # Download buttons
    st.markdown("---")
    st.markdown("#### 📥 Export Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download
        csv = df_action[display_cols].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📄 Download as CSV",
            data=csv,
            file_name="action_list.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Excel download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_action[display_cols].to_excel(writer, sheet_name='Action List', index=False)
        output.seek(0)
        
        st.download_button(
            label="📊 Download as Excel",
            data=output,
            file_name="action_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Audit Next Steps
    st.markdown("---")
    st.markdown("#### 🎯 Audit Next Steps")
    
    next_steps = []
    
    # High priority vendors
    if 'priority' in df_action.columns and 'vendor_code' in df_action.columns:
        high_vendors = df_action[df_action['priority'] == 'HIGH']['vendor_code'].unique()
        if len(high_vendors) > 0:
            next_steps.append(f"**Start with HIGH priority vendors:** {', '.join(high_vendors[:5].tolist())}")
    
    # Verification steps
    next_steps.append("**Verify AP totals** against purchase orders and invoices")
    next_steps.append("**Confirm claim conditions** per contract terms")
    next_steps.append("**Prepare claim memo** with supporting documents")
    next_steps.append("**Follow up** on pending claims (UNDER status)")
    next_steps.append("**Investigate** over-billed items (OVER status)")
    
    for i, step in enumerate(next_steps, 1):
        st.markdown(f"{i}. {step}")
