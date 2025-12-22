"""
InsightOps - E-commerce BI Dashboard
Professional, clean dashboard with 4 pages
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from analytics.kpi_calculator import KPICalculator
from analytics.insights_engine import InsightsEngine
from config import DASHBOARD_CONFIG, COLOR_SCHEME

# Page configuration
st.set_page_config(
    page_title=DASHBOARD_CONFIG['title'],
    page_icon=DASHBOARD_CONFIG['page_icon'],
    layout=DASHBOARD_CONFIG['layout'],
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .insight-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #1a1a1a !important;
    }
    .insight-card strong {
        color: #000 !important;
    }
    .insight-high {
        background-color: #fee;
        border-left: 4px solid #d62728;
    }
    .insight-medium {
        background-color: #fff3cd;
        border-left: 4px solid #ff7f0e;
    }
    .insight-low {
        background-color: #e7f3ff;
        border-left: 4px solid #17becf;
    }
</style>
""", unsafe_allow_html=True)

# Initialize calculators (no caching needed - connections are created per query)
kpi_calc = KPICalculator()
insights_engine = InsightsEngine()

# Sidebar navigation
st.sidebar.title("📊 InsightOps")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["Executive Overview", "Product Performance", "Customer Insights", "Operations"]
)

# ============================================
# PAGE 1: EXECUTIVE OVERVIEW
# ============================================

if page == "Executive Overview":
    st.markdown('<div class="main-header">Executive Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Key metrics and business performance at a glance</div>', unsafe_allow_html=True)
    
    # Get KPIs
    exec_kpis = kpi_calc.get_executive_kpis()
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Revenue",
            value=f"${exec_kpis['total_revenue']:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Profit",
            value=f"${exec_kpis['total_profit']:,.0f}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Profit Margin",
            value=f"{exec_kpis['profit_margin']:.1f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Order Success Rate",
            value=f"{exec_kpis['order_success_rate']:.1f}%",
            delta=None
        )
    
    st.markdown("---")
    
    # Monthly trends
    st.subheader("📈 Revenue & Profit Trends")
    
    monthly_trends = kpi_calc.get_monthly_trends()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=monthly_trends['year_month'],
            y=monthly_trends['total_revenue'],
            name="Revenue",
            line=dict(color=COLOR_SCHEME['primary'], width=3),
            mode='lines+markers'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=monthly_trends['year_month'],
            y=monthly_trends['total_profit'],
            name="Profit",
            line=dict(color=COLOR_SCHEME['success'], width=3),
            mode='lines+markers'
        ),
        secondary_y=False
    )
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Amount ($)", secondary_y=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Automated Insights
    st.markdown("---")
    st.subheader("🔍 Automated Insights")
    
    insights = insights_engine.generate_all_insights()
    
    # Show top 5 insights
    for insight in insights[:5]:
        severity_class = f"insight-{insight['severity']}"
        icon = {'warning': '⚠️', 'alert': '🚨', 'info': 'ℹ️', 'recommendation': '💡', 'success': '✅'}
        
        st.markdown(f"""
        <div class="insight-card {severity_class}">
            <strong>{icon.get(insight['type'], '•')} {insight['title']}</strong><br>
            {insight['message']}
        </div>
        """, unsafe_allow_html=True)

# ============================================
# PAGE 2: PRODUCT PERFORMANCE
# ============================================

elif page == "Product Performance":
    st.markdown('<div class="main-header">Product Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Revenue vs profit analysis by product category</div>', unsafe_allow_html=True)
    
    # Category performance
    category_perf = kpi_calc.get_category_performance()
    
    # Revenue vs Profit scatter
    st.subheader("💰 Revenue vs Profit by Category")
    
    fig = px.scatter(
        category_perf,
        x='total_revenue',
        y='total_profit',
        size='order_count',
        color='profit_margin_pct',
        hover_data=['category', 'order_count'],
        text='category',
        color_continuous_scale='RdYlGn',
        labels={
            'total_revenue': 'Total Revenue ($)',
            'total_profit': 'Total Profit ($)',
            'profit_margin_pct': 'Margin %'
        }
    )
    
    fig.update_traces(textposition='top center', textfont_size=9)
    fig.update_layout(height=500, showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 **Insight**: Categories in the top-right quadrant are high performers. Bottom-right shows high revenue but low profit.")
    
    # Category breakdown
    st.markdown("---")
    st.subheader("📊 Top Categories by Revenue")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            category_perf.head(10),
            x='total_revenue',
            y='category',
            orientation='h',
            color='profit_margin_pct',
            color_continuous_scale='RdYlGn',
            labels={'total_revenue': 'Revenue ($)', 'category': 'Category'}
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Low margin products alert
        low_margin = category_perf[category_perf['profit_margin_pct'] < 10]
        
        if not low_margin.empty:
            st.warning(f"⚠️ **{len(low_margin)} categories** have profit margin below 10%")
            st.dataframe(
                low_margin[['category', 'total_revenue', 'profit_margin_pct']].style.format({
                    'total_revenue': '${:,.0f}',
                    'profit_margin_pct': '{:.1f}%'
                }),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("✅ All categories have healthy profit margins")

# ============================================
# PAGE 3: CUSTOMER INSIGHTS
# ============================================

elif page == "Customer Insights":
    st.markdown('<div class="main-header">Customer Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Customer segmentation and retention analysis</div>', unsafe_allow_html=True)
    
    # Customer segments
    segments = kpi_calc.get_customer_segments()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Customer Segments")
        
        fig = px.pie(
            segments,
            values='customer_count',
            names='segment',
            color='segment',
            color_discrete_map={'New': COLOR_SCHEME['info'], 'Returning': COLOR_SCHEME['primary'], 'VIP': COLOR_SCHEME['success']},
            hole=0.4
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💵 Revenue by Segment")
        
        fig = px.bar(
            segments,
            x='segment',
            y='total_revenue',
            color='segment',
            color_discrete_map={'New': COLOR_SCHEME['info'], 'Returning': COLOR_SCHEME['primary'], 'VIP': COLOR_SCHEME['success']},
            labels={'total_revenue': 'Total Revenue ($)', 'segment': 'Segment'}
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Segment metrics
    st.markdown("---")
    st.subheader("📊 Segment Performance Metrics")
    
    st.dataframe(
        segments.style.format({
            'customer_count': '{:,}',
            'order_count': '{:,}',
            'total_revenue': '${:,.0f}',
            'avg_order_value': '${:.2f}'
        }),
        hide_index=True,
        use_container_width=True
    )
    
    # Top customers
    st.markdown("---")
    st.subheader("🏆 Top 10 Customers by Revenue")
    
    top_customers = kpi_calc.get_top_customers(10)
    
    st.dataframe(
        top_customers.style.format({
            'order_count': '{:,}',
            'total_revenue': '${:,.2f}',
            'avg_order_value': '${:.2f}'
        }),
        hide_index=True,
        use_container_width=True
    )

# ============================================
# PAGE 4: OPERATIONS
# ============================================

elif page == "Operations":
    st.markdown('<div class="main-header">Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Payment failures and channel performance</div>', unsafe_allow_html=True)
    
    # Channel performance
    channel_perf = kpi_calc.get_channel_performance()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📱 Revenue by Channel")
        
        fig = px.bar(
            channel_perf,
            x='channel',
            y='revenue',
            color='channel',
            labels={'revenue': 'Revenue ($)', 'channel': 'Channel'}
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("❌ Payment Failure Rate")
        
        fig = px.bar(
            channel_perf,
            x='channel',
            y='failure_rate_pct',
            color='failure_rate_pct',
            color_continuous_scale='Reds',
            labels={'failure_rate_pct': 'Failure Rate (%)', 'channel': 'Channel'}
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Channel metrics table
    st.markdown("---")
    st.subheader("📊 Channel Performance Metrics")
    
    st.dataframe(
        channel_perf.style.format({
            'total_orders': '{:,}',
            'successful_orders': '{:,}',
            'revenue': '${:,.0f}',
            'failure_rate_pct': '{:.2f}%'
        }),
        hide_index=True,
        use_container_width=True
    )
    
    # Alerts
    st.markdown("---")
    st.subheader("⚠️ Operational Alerts")
    
    high_failure_channels = channel_perf[channel_perf['failure_rate_pct'] > 5]
    
    if not high_failure_channels.empty:
        for _, channel in high_failure_channels.iterrows():
            st.error(f"🚨 **{channel['channel']}** channel has {channel['failure_rate_pct']:.1f}% failure rate (above 5% threshold)")
    else:
        st.success("✅ All channels operating within acceptable failure rates")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About InsightOps")
st.sidebar.info(
    "**InsightOps** is a production-grade BI system demonstrating:\n\n"
    "✓ Star schema data warehouse\n"
    "✓ ETL pipeline with data cleaning\n"
    "✓ Automated insights engine\n"
    "✓ Professional dashboards"
)
