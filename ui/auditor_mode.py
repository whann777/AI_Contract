"""
Auditor Dashboard - Single Page PRA Framework
Problem → Reason → Action in one view
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO


def show_auditor_mode():
    """Single Page PRA Dashboard"""
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("Contract Audit Dashboard")
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
    
    # Load data
    if not load_dashboard_data():
        show_no_data_message()
        return
    
    df = st.session_state.dashboard_results.copy()
    
    # Sidebar Filters
    df_filtered = show_filters(df)
    
    # Get calc data
    calc_df = get_calculation_data()
    
    # Single Page Layout
    build_single_page_dashboard(df_filtered, calc_df)


def load_dashboard_data():
    """โหลดข้อมูล"""
    if 'processing_results' in st.session_state and st.session_state.processing_results is not None:
        st.session_state.dashboard_results = st.session_state.processing_results
        return True
    
    if 'saved_sessions' in st.session_state and st.session_state.saved_sessions:
        sessions = st.session_state.saved_sessions
        latest_key = list(sessions.keys())[-1]
        latest_session = sessions[latest_key]
        if 'results' in latest_session:
            st.session_state.dashboard_results = latest_session['results']
            return True
    
    return False


def show_no_data_message():
    """ไม่มีข้อมูล"""
    st.warning("No data available")
    st.info("Go to Analyze → Run Analysis → Return here")


def show_filters(df):
    """Filters"""
    st.sidebar.markdown("### Filters")
    
    # Vendor
    if 'vendor_code' in df.columns:
        vendors = ['All'] + sorted(df['vendor_code'].unique().tolist())
        selected = st.sidebar.multiselect("Vendor", vendors, ['All'])
        if 'All' not in selected and selected:
            df = df[df['vendor_code'].isin(selected)]
    
    # Category
    if 'category_code' in df.columns:
        cats = ['All'] + sorted(df['category_code'].unique().tolist())
        selected = st.sidebar.multiselect("Category", cats, ['All'])
        if 'All' not in selected and selected:
            df = df[df['category_code'].isin(selected)]
    
    # Status
    if 'status' in df.columns:
        statuses = ['All'] + sorted(df['status'].unique().tolist())
        selected = st.sidebar.multiselect("Status", statuses, ['All'])
        if 'All' not in selected and selected:
            df = df[df['status'].isin(selected)]
    
    st.sidebar.metric("Records", len(df))
    
    return df


def get_calculation_data():
    """ดึงข้อมูล calculation"""
    if hasattr(st.session_state, 'service'):
        try:
            return st.session_state.service.recon_system.calculated_allowances
        except:
            pass
    return None


def build_single_page_dashboard(df, calc_df):
    """Single Page Dashboard"""
    
    # ========== PROBLEM ==========
    st.markdown("## 🚨 PROBLEM")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    total_expected = df['should_collect'].sum() if 'should_collect' in df.columns else 0
    total_actual = df['actually_collected'].sum() if 'actually_collected' in df.columns else 0
    total_diff = df['difference'].sum() if 'difference' in df.columns else 0
    vendors_risk = len(df[df['difference'] < -1]['vendor_code'].unique()) if 'difference' in df.columns and 'vendor_code' in df.columns else 0
    
    col1.metric("Expected", f"฿{total_expected:,.0f}")
    col2.metric("Actual", f"฿{total_actual:,.0f}")
    col3.metric("Difference", f"฿{total_diff:,.0f}", delta=f"{(total_diff/total_expected*100):.1f}%" if total_expected > 0 else "0%")
    col4.metric("Vendors at Risk", vendors_risk)
    
    st.markdown("---")
    
    # Charts Row 1: PROBLEM
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top 10 Under-Collected Vendors**")
        if 'vendor_code' in df.columns and 'difference' in df.columns:
            under_vendors = df[df['difference'] < 0].groupby('vendor_code')['difference'].sum().sort_values().head(10)
            
            if len(under_vendors) > 0:
                fig = go.Figure(go.Bar(
                    x=under_vendors.values,
                    y=under_vendors.index,
                    orientation='h',
                    marker_color='#90EE90',  # UNDER = Green
                    text=[f"฿{abs(x):,.0f}" for x in under_vendors.values],
                    textposition='outside'
                ))
                fig.update_layout(
                    xaxis_title="Amount Under-Collected (฿)",
                    yaxis_title="",
                    height=350,
                    showlegend=False,
                    margin=dict(l=100, r=50, t=30, b=50)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No under-collected vendors")
    
    with col2:
        st.markdown("**Status Distribution**")
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            status_amounts = df.groupby('status')['should_collect'].sum() if 'should_collect' in df.columns else status_counts
            
            # Color mapping
            color_map = {'MATCH': '#FFD700', 'UNDER': '#90EE90', 'OVER': '#FF6B6B'}
            colors = [color_map.get(s, '#CCCCCC') for s in status_amounts.index]
            
            fig = go.Figure(data=[go.Bar(
                x=status_amounts.index,
                y=status_amounts.values,
                marker_color=colors,
                text=[f"฿{x:,.0f}" for x in status_amounts.values],
                textposition='outside'
            )])
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Amount (฿)",
                height=350,
                showlegend=False,
                margin=dict(l=50, r=50, t=30, b=50)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========== REASON ==========
    st.markdown("## 🔍 REASON")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Category Breakdown**")
        if 'category_code' in df.columns and 'should_collect' in df.columns:
            cat_summary = df.groupby('category_code')['should_collect'].sum().sort_values(ascending=False).head(10)
            
            fig = px.bar(
                x=cat_summary.values,
                y=cat_summary.index,
                orientation='h',
                labels={'x': 'Amount (฿)', 'y': ''},
                color=cat_summary.values,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=350, showlegend=False, margin=dict(l=80, r=50, t=30, b=50))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Calculation Type**")
        if calc_df is not None and 'calculation_type' in calc_df.columns:
            calc_counts = calc_df['calculation_type'].value_counts().head(10)
            
            fig = go.Figure(data=[go.Bar(
                x=calc_counts.index,
                y=calc_counts.values,
                marker_color='#764ba2'
            )])
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Count",
                height=350,
                showlegend=False,
                margin=dict(l=50, r=50, t=30, b=80),
                xaxis={'tickangle': -45}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run analysis to see calculation types")
    
    st.markdown("---")
    
    # ========== ACTION ==========
    st.markdown("## ✅ ACTION")
    
    # Priority Settings
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        high_threshold = st.number_input("HIGH (฿)", value=10000, step=1000)
    with col2:
        med_threshold = st.number_input("MED (฿)", value=5000, step=1000)
    
    # Calculate Priority
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
        
        # Priority counts
        high_count = len(df_action[df_action['priority'] == 'HIGH'])
        med_count = len(df_action[df_action['priority'] == 'MEDIUM'])
        low_count = len(df_action[df_action['priority'] == 'LOW'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("HIGH", high_count, delta="Urgent", delta_color="inverse")
        col2.metric("MEDIUM", med_count)
        col3.metric("LOW", low_count)
    
    st.markdown("---")
    
    # Action Table
    st.markdown("**Action List**")
    
    display_cols = []
    for col in ['priority', 'vendor_code', 'vendor_name', 'category_code', 
                'should_collect', 'actually_collected', 'difference', 'status']:
        if col in df_action.columns:
            display_cols.append(col)
    
    if display_cols and 'abs_diff' in df_action.columns:
        df_display = df_action.sort_values('abs_diff', ascending=False)[display_cols].head(50)
        
        # Style
        def style_row(row):
            styles = [''] * len(row)
            
            # Priority column
            if 'priority' in row.index:
                pri = row['priority']
                if pri == 'HIGH':
                    styles[row.index.get_loc('priority')] = 'background-color: #FF6B6B; color: white; font-weight: bold'
                elif pri == 'MEDIUM':
                    styles[row.index.get_loc('priority')] = 'background-color: #FFD700; color: black; font-weight: bold'
                elif pri == 'LOW':
                    styles[row.index.get_loc('priority')] = 'background-color: #90EE90; color: black; font-weight: bold'
            
            # Status column
            if 'status' in row.index:
                status = row['status']
                if status == 'MATCH':
                    styles[row.index.get_loc('status')] = 'background-color: #FFD700; color: black'
                elif status == 'UNDER':
                    styles[row.index.get_loc('status')] = 'background-color: #90EE90; color: black'
                elif status == 'OVER':
                    styles[row.index.get_loc('status')] = 'background-color: #FF6B6B; color: white'
            
            return styles
        
        styled_df = df_display.style.apply(style_row, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Download
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        csv = df_action[display_cols].to_csv(index=False).encode('utf-8-sig')
        st.download_button("📄 CSV", csv, "action_list.csv", "text/csv", use_container_width=True)
    
    with col2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_action[display_cols].to_excel(writer, index=False)
        output.seek(0)
        st.download_button("📊 Excel", output, "action_list.xlsx", use_container_width=True)
