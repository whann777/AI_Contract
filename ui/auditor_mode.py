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
    
    # ========== KPIs ==========
    col1, col2, col3, col4 = st.columns(4)
    
    total_expected = df['should_collect'].sum() if 'should_collect' in df.columns else 0
    total_actual = df['actually_collected'].sum() if 'actually_collected' in df.columns else 0
    
    # FIX: Difference = Expected - Actual (ไม่ติดลบ)
    total_diff = abs(total_expected - total_actual) if total_expected > 0 else 0
    diff_pct = (total_diff / total_expected * 100) if total_expected > 0 else 0
    
    vendors_risk = len(df[df['difference'] < -1]['vendor_code'].unique()) if 'difference' in df.columns and 'vendor_code' in df.columns else 0
    
    col1.metric("Expected", f"฿{total_expected:,.0f}")
    col2.metric("Actual", f"฿{total_actual:,.0f}")
    col3.metric("Difference", f"฿{total_diff:,.0f}", delta=f"{diff_pct:.1f}%")
    col4.metric("Vendors at Risk", vendors_risk)
    
    st.markdown("---")
    
    # ========== Charts Row 1 ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Leakage by Category**")
        if 'category_code' in df.columns and 'difference' in df.columns:
            # Calculate leakage (negative difference only)
            df_leakage = df[df['difference'] < 0].copy()
            if len(df_leakage) > 0:
                leakage_by_cat = df_leakage.groupby('category_code')['difference'].sum().abs().sort_values(ascending=False)
                
                fig = px.bar(
                    x=leakage_by_cat.values,
                    y=leakage_by_cat.index,
                    orientation='h',
                    labels={'x': 'Leakage Amount (฿)', 'y': 'Category'},
                    color=leakage_by_cat.values,
                    color_continuous_scale='Reds'
                )
                fig.update_layout(
                    height=350,
                    showlegend=False,
                    margin=dict(l=80, r=50, t=30, b=50)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No leakage found")
    
    with col2:
        st.markdown("**Status Distribution**")
        if 'status' in df.columns and 'should_collect' in df.columns:
            # Translate Thai to English first
            df_temp = df.copy()
            status_translation = {
                'ครบ': 'MATCH',
                'ขาด': 'UNDER', 
                'เกิน': 'OVER'
            }
            df_temp['status'] = df_temp['status'].replace(status_translation)
            
            # Group by translated status
            status_amounts = df_temp.groupby('status')['should_collect'].sum()
            
            # Ensure order: MATCH, UNDER, OVER
            status_order = ['MATCH', 'UNDER', 'OVER']
            status_amounts = status_amounts.reindex(status_order, fill_value=0)
            
            # Color mapping (MATCH=Yellow, UNDER=Green, OVER=Red)
            color_map = {'MATCH': '#FFD700', 'UNDER': '#90EE90', 'OVER': '#FF6B6B'}
            colors = [color_map[s] for s in status_amounts.index]
            
            fig = go.Figure(data=[go.Bar(
                x=status_amounts.index,
                y=status_amounts.values,
                marker_color=colors,
                text=[f"฿{x:,.0f}" for x in status_amounts.values],
                textposition='outside',
                showlegend=False
            )])
            
            fig.update_layout(
                xaxis_title="Status",
                yaxis_title="Amount (฿)",
                height=350,
                showlegend=False,
                margin=dict(l=50, r=50, t=30, b=50),
                xaxis=dict(
                    categoryorder='array',
                    categoryarray=status_order
                )
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========== Charts Row 2 ==========
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
        st.markdown("**Diverging Stacked Bar by Category**")
        if 'category_code' in df.columns and 'difference' in df.columns and 'status' in df.columns:
            # Translate status first
            df_temp = df.copy()
            status_translation = {'ครบ': 'MATCH', 'ขาด': 'UNDER', 'เกิน': 'OVER'}
            df_temp['status'] = df_temp['status'].replace(status_translation)
            
            # Group by category and status - sum differences
            cat_status = df_temp.groupby(['category_code', 'status'], as_index=False)['difference'].sum()
            
            # Check if we have data
            if len(cat_status) == 0:
                st.info("No data available")
            else:
                # Pivot to create diverging structure
                pivot = cat_status.pivot_table(
                    index='category_code',
                    columns='status',
                    values='difference',
                    fill_value=0,
                    aggfunc='sum'
                )
                
                # Calculate absolute total per category
                pivot['total_abs'] = pivot.abs().sum(axis=1)
                pivot = pivot.sort_values('total_abs', ascending=True)
                pivot = pivot.tail(10).drop('total_abs', axis=1)
                
                # Create figure
                fig = go.Figure()
                
                # UNDER (left - green)
                if 'UNDER' in pivot.columns:
                    fig.add_trace(go.Bar(
                        name='UNDER',
                        y=pivot.index,
                        x=pivot['UNDER'],
                        orientation='h',
                        marker=dict(color='#90EE90'),
                        text=[f"฿{abs(x):,.0f}" if abs(x) > 100 else "" for x in pivot['UNDER']],
                        textposition='inside',
                        textfont=dict(color='black', size=10)
                    ))
                
                # MATCH (center - yellow)
                if 'MATCH' in pivot.columns:
                    fig.add_trace(go.Bar(
                        name='MATCH',
                        y=pivot.index,
                        x=pivot['MATCH'],
                        orientation='h',
                        marker=dict(color='#FFD700'),
                        text=[f"฿{abs(x):,.0f}" if abs(x) > 100 else "" for x in pivot['MATCH']],
                        textposition='inside',
                        textfont=dict(color='black', size=10)
                    ))
                
                # OVER (right - red)
                if 'OVER' in pivot.columns:
                    fig.add_trace(go.Bar(
                        name='OVER',
                        y=pivot.index,
                        x=pivot['OVER'],
                        orientation='h',
                        marker=dict(color='#FF6B6B'),
                        text=[f"฿{abs(x):,.0f}" if abs(x) > 100 else "" for x in pivot['OVER']],
                        textposition='inside',
                        textfont=dict(color='white', size=10)
                    ))
                
                fig.update_layout(
                    barmode='relative',
                    xaxis_title="Amount (฿)",
                    yaxis_title="Category",
                    height=350,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=100, r=50, t=50, b=50)
                )
                
                # Center line
                fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="white", opacity=0.5)
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need category_code, difference, and status columns")
    
    st.markdown("---")
    
    # ========== ACTION SECTION ==========
    
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
    
    # Summary by Vendor (sorted by leakage)
    st.markdown("**Summary by Vendor**")
    
    if 'vendor_code' in df.columns and 'difference' in df.columns:
        vendor_summary = df.groupby(['vendor_code', 'vendor_name']).agg({
            'should_collect': 'sum',
            'actually_collected': 'sum',
            'difference': 'sum'
        }).reset_index()
        
        # Calculate leakage (only negative difference)
        vendor_summary['leakage'] = vendor_summary['difference'].apply(lambda x: abs(x) if x < 0 else 0)
        
        # Sort by leakage (descending)
        vendor_summary = vendor_summary.sort_values('leakage', ascending=False)
        
        # Add status
        def get_status(diff):
            if abs(diff) < 1:
                return 'MATCH'
            elif diff > 0:
                return 'OVER'
            else:
                return 'UNDER'
        
        vendor_summary['status'] = vendor_summary['difference'].apply(get_status)
        
        # Display columns
        display_df = vendor_summary[['vendor_code', 'vendor_name', 'should_collect', 
                                      'actually_collected', 'leakage', 'status']].head(50)
        
        # Format numbers
        for col in ['should_collect', 'actually_collected', 'leakage']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if x is not None else "")
        
        # Style status column
        def style_status(val):
            if val == 'MATCH':
                return 'background-color: #FFD700; color: black; font-weight: bold'
            elif val == 'UNDER':
                return 'background-color: #90EE90; color: black; font-weight: bold'
            elif val == 'OVER':
                return 'background-color: #FF6B6B; color: white; font-weight: bold'
            return ''
        
        if 'status' in display_df.columns:
            styled = display_df.style.applymap(style_status, subset=['status'])
            st.dataframe(styled, use_container_width=True, height=400, hide_index=True)
        else:
            st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
    
    # Download
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if 'vendor_code' in df.columns:
            csv = vendor_summary.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📄 CSV", csv, "vendor_summary.csv", "text/csv", use_container_width=True)
    
    with col2:
        if 'vendor_code' in df.columns:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                vendor_summary.to_excel(writer, sheet_name='Vendor Summary', index=False)
            output.seek(0)
            st.download_button("📊 Excel", output, "vendor_summary.xlsx", use_container_width=True)
