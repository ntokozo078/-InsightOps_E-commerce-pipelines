"""
InsightOps Configuration
Central configuration for paths, thresholds, and business rules
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT.parent / "datasets"
CLEAN_DATA_DIR = PROJECT_ROOT / "data" / "clean"
WAREHOUSE_DIR = PROJECT_ROOT / "warehouse"

# Database configuration
DATABASE_PATH = WAREHOUSE_DIR / "insightops.db"

# Raw data files (Olist dataset)
RAW_DATA_FILES = {
    'orders': DATA_DIR / 'olist_orders_dataset.csv',
    'order_items': DATA_DIR / 'olist_order_items_dataset.csv',
    'customers': DATA_DIR / 'olist_customers_dataset.csv',
    'products': DATA_DIR / 'olist_products_dataset.csv',
    'payments': DATA_DIR / 'olist_order_payments_dataset.csv',
    'category_translation': DATA_DIR / 'product_category_name_translation.csv'
}

# Clean data output files
CLEAN_DATA_FILES = {
    'fact_orders': CLEAN_DATA_DIR / 'fact_orders.csv',
    'dim_customer': CLEAN_DATA_DIR / 'dim_customer.csv',
    'dim_product': CLEAN_DATA_DIR / 'dim_product.csv',
    'dim_date': CLEAN_DATA_DIR / 'dim_date.csv'
}

# Business Rules & Thresholds for Automated Insights
BUSINESS_RULES = {
    'low_profit_margin_threshold': 0.10,  # Flag products with margin < 10%
    'high_failed_payment_threshold': 0.05,  # Alert if failed payments > 5%
    'retention_drop_threshold': 0.10,  # Alert if retention drops > 10% MoM
    'high_value_customer_threshold': 1000,  # VIP customers with revenue > $1000
    'minimum_order_value': 10,  # Minimum valid order value
}

# Currency conversion (BRL to USD)
BRL_TO_USD_RATE = 0.20  # Approximate conversion rate

# Customer segmentation rules
CUSTOMER_SEGMENTS = {
    'new': 1,  # 1 order
    'returning': (2, 5),  # 2-5 orders
    'vip': 6  # 6+ orders
}

# Date range for analysis
DATE_RANGE = {
    'start_date': '2016-09-01',
    'end_date': '2018-10-01'
}

# Dashboard configuration
DASHBOARD_CONFIG = {
    'title': 'InsightOps – E-commerce BI Dashboard',
    'theme': 'streamlit',
    'page_icon': '📊',
    'layout': 'wide'
}

# Color scheme for visualizations
COLOR_SCHEME = {
    'primary': '#1f77b4',
    'success': '#2ca02c',
    'warning': '#ff7f0e',
    'danger': '#d62728',
    'info': '#17becf',
    'neutral': '#7f7f7f'
}
