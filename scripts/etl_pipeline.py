"""
InsightOps ETL Pipeline
Extracts, transforms, and loads Olist e-commerce data into star schema format
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for config import
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    RAW_DATA_FILES, CLEAN_DATA_DIR, BRL_TO_USD_RATE,
    CUSTOMER_SEGMENTS, BUSINESS_RULES
)


class ETLPipeline:
    """Main ETL Pipeline for InsightOps"""
    
    def __init__(self):
        self.orders = None
        self.order_items = None
        self.customers = None
        self.products = None
        self.payments = None
        self.category_translation = None
        
        # Ensure clean data directory exists
        CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def extract(self):
        """Extract data from raw CSV files"""
        print("=" * 60)
        print("EXTRACTION PHASE")
        print("=" * 60)
        
        print("\n📥 Loading raw data files...")
        self.orders = pd.read_csv(RAW_DATA_FILES['orders'])
        self.order_items = pd.read_csv(RAW_DATA_FILES['order_items'])
        self.customers = pd.read_csv(RAW_DATA_FILES['customers'])
        self.products = pd.read_csv(RAW_DATA_FILES['products'])
        self.payments = pd.read_csv(RAW_DATA_FILES['payments'])
        self.category_translation = pd.read_csv(RAW_DATA_FILES['category_translation'])
        
        print(f"✓ Orders: {len(self.orders):,} rows")
        print(f"✓ Order Items: {len(self.order_items):,} rows")
        print(f"✓ Customers: {len(self.customers):,} rows")
        print(f"✓ Products: {len(self.products):,} rows")
        print(f"✓ Payments: {len(self.payments):,} rows")
        print(f"✓ Category Translations: {len(self.category_translation):,} rows")
    
    def transform(self):
        """Transform and clean data"""
        print("\n" + "=" * 60)
        print("TRANSFORMATION PHASE")
        print("=" * 60)
        
        # 1. Build Fact Table: fact_orders
        print("\n🔄 Building fact_orders table...")
        fact_orders = self._build_fact_orders()
        
        # 2. Build Dimension Tables
        print("\n🔄 Building dim_customer table...")
        dim_customer = self._build_dim_customer()
        
        print("\n🔄 Building dim_product table...")
        dim_product = self._build_dim_product()
        
        print("\n🔄 Building dim_date table...")
        dim_date = self._build_dim_date()
        
        return fact_orders, dim_customer, dim_product, dim_date
    
    def _build_fact_orders(self):
        """Build fact_orders table from orders, order_items, and payments"""
        
        # Merge orders with order_items
        fact = self.order_items.merge(
            self.orders[['order_id', 'customer_id', 'order_purchase_timestamp', 'order_status']],
            on='order_id',
            how='left'
        )
        
        # Merge with payments to get payment status
        payments_agg = self.payments.groupby('order_id').agg({
            'payment_type': 'first',
            'payment_value': 'sum'
        }).reset_index()
        
        fact = fact.merge(payments_agg, on='order_id', how='left')
        
        # Data cleaning and transformation
        print("  ├─ Removing duplicates...")
        initial_count = len(fact)
        fact = fact.drop_duplicates(subset=['order_id', 'order_item_id'])
        print(f"     Removed {initial_count - len(fact):,} duplicates")
        
        print("  ├─ Standardizing dates...")
        fact['order_date'] = pd.to_datetime(fact['order_purchase_timestamp']).dt.date
        
        print("  ├─ Converting currency (BRL → USD)...")
        fact['revenue'] = (fact['price'] * BRL_TO_USD_RATE).round(2)
        fact['cost'] = (fact['price'] * 0.6 * BRL_TO_USD_RATE).round(2)  # Assume 60% cost ratio
        fact['profit'] = (fact['revenue'] - fact['cost']).round(2)
        
        print("  ├─ Handling missing values...")
        fact['quantity'] = 1  # Each order_item is 1 unit in Olist data
        fact['payment_status'] = fact['order_status'].apply(
            lambda x: 'Success' if x == 'delivered' else 'Failed'
        )
        
        print("  ├─ Deriving channel from payment type...")
        fact['channel'] = fact['payment_type'].apply(self._map_payment_to_channel)
        
        # Select and rename columns for final fact table
        fact_orders = fact[[
            'order_id', 'order_date', 'customer_id', 'product_id',
            'quantity', 'revenue', 'cost', 'profit', 'payment_status', 'channel'
        ]].copy()
        
        # Remove orders with missing critical data
        print("  ├─ Removing rows with missing critical data...")
        before = len(fact_orders)
        fact_orders = fact_orders.dropna(subset=['order_date', 'customer_id', 'product_id'])
        print(f"     Removed {before - len(fact_orders):,} rows with missing data")
        
        # Filter for valid orders only (positive revenue)
        fact_orders = fact_orders[fact_orders['revenue'] > 0]
        
        print(f"  └─ ✓ Final fact_orders: {len(fact_orders):,} rows")
        
        return fact_orders
    
    def _build_dim_customer(self):
        """Build dim_customer dimension table"""
        
        # Get unique customers
        dim_customer = self.customers[['customer_id', 'customer_unique_id', 
                                       'customer_city', 'customer_state']].copy()
        
        print("  ├─ Removing duplicate customers...")
        dim_customer = dim_customer.drop_duplicates(subset=['customer_id'])
        
        # Rename for clarity
        dim_customer = dim_customer.rename(columns={
            'customer_state': 'country',  # Using state as country proxy
            'customer_unique_id': 'customer_unique_id'
        })
        
        # Get first order date as signup_date
        first_orders = self.orders.groupby('customer_id')['order_purchase_timestamp'].min().reset_index()
        first_orders['signup_date'] = pd.to_datetime(first_orders['order_purchase_timestamp']).dt.date
        
        dim_customer = dim_customer.merge(
            first_orders[['customer_id', 'signup_date']], 
            on='customer_id', 
            how='left'
        )
        
        # Calculate customer segment based on order count
        print("  ├─ Calculating customer segments...")
        order_counts = self.orders.groupby('customer_id').size().reset_index(name='order_count')
        dim_customer = dim_customer.merge(order_counts, on='customer_id', how='left')
        
        def assign_segment(count):
            if pd.isna(count) or count <= CUSTOMER_SEGMENTS['new']:
                return 'New'
            elif count <= CUSTOMER_SEGMENTS['returning'][1]:
                return 'Returning'
            else:
                return 'VIP'
        
        dim_customer['segment'] = dim_customer['order_count'].apply(assign_segment)
        
        # Create surrogate key
        dim_customer['customer_key'] = range(1, len(dim_customer) + 1)
        
        # Final columns
        dim_customer = dim_customer[[
            'customer_key', 'customer_id', 'country', 'signup_date', 'segment'
        ]]
        
        print(f"  └─ ✓ Final dim_customer: {len(dim_customer):,} rows")
        print(f"     Segments: New={len(dim_customer[dim_customer['segment']=='New'])}, "
              f"Returning={len(dim_customer[dim_customer['segment']=='Returning'])}, "
              f"VIP={len(dim_customer[dim_customer['segment']=='VIP'])}")
        
        return dim_customer
    
    def _build_dim_product(self):
        """Build dim_product dimension table"""
        
        dim_product = self.products[['product_id', 'product_category_name']].copy()
        
        print("  ├─ Removing duplicate products...")
        dim_product = dim_product.drop_duplicates(subset=['product_id'])
        
        # Translate category names to English
        print("  ├─ Translating category names...")
        dim_product = dim_product.merge(
            self.category_translation,
            on='product_category_name',
            how='left'
        )
        
        # Handle missing categories
        dim_product['product_category_name_english'] = dim_product['product_category_name_english'].fillna('Other')
        
        # Rename columns
        dim_product = dim_product.rename(columns={
            'product_category_name_english': 'category'
        })
        
        # Add placeholder brand (not in Olist data)
        dim_product['brand'] = 'Generic'
        
        # Calculate unit cost and price from order_items
        print("  ├─ Calculating average unit costs and prices...")
        product_prices = self.order_items.groupby('product_id').agg({
            'price': 'mean'
        }).reset_index()
        
        dim_product = dim_product.merge(product_prices, on='product_id', how='left')
        
        dim_product['unit_price'] = (dim_product['price'] * BRL_TO_USD_RATE).round(2)
        dim_product['unit_cost'] = (dim_product['unit_price'] * 0.6).round(2)  # 60% cost ratio
        
        # Create surrogate key
        dim_product['product_key'] = range(1, len(dim_product) + 1)
        
        # Final columns
        dim_product = dim_product[[
            'product_key', 'product_id', 'category', 'brand', 'unit_cost', 'unit_price'
        ]]
        
        print(f"  └─ ✓ Final dim_product: {len(dim_product):,} rows")
        print(f"     Categories: {dim_product['category'].nunique()} unique")
        
        return dim_product
    
    def _build_dim_date(self):
        """Build dim_date dimension table"""
        
        # Get all unique dates from orders
        all_dates = pd.to_datetime(self.orders['order_purchase_timestamp']).dt.date.unique()
        
        dim_date = pd.DataFrame({'date': sorted(all_dates)})
        dim_date['date'] = pd.to_datetime(dim_date['date'])
        
        # Extract date components
        print("  ├─ Extracting date components...")
        dim_date['year'] = dim_date['date'].dt.year
        dim_date['month'] = dim_date['date'].dt.month
        dim_date['quarter'] = dim_date['date'].dt.quarter
        dim_date['weekday'] = dim_date['date'].dt.day_name()
        
        # Create date_key (YYYYMMDD format)
        dim_date['date_key'] = dim_date['date'].dt.strftime('%Y%m%d').astype(int)
        
        # Reorder columns
        dim_date = dim_date[['date_key', 'date', 'year', 'month', 'quarter', 'weekday']]
        
        print(f"  └─ ✓ Final dim_date: {len(dim_date):,} rows")
        print(f"     Date range: {dim_date['date'].min()} to {dim_date['date'].max()}")
        
        return dim_date
    
    def _map_payment_to_channel(self, payment_type):
        """Map payment type to sales channel"""
        if pd.isna(payment_type):
            return 'Unknown'
        elif payment_type == 'credit_card':
            return 'Web'
        elif payment_type == 'boleto':
            return 'Mobile'
        else:
            return 'Other'
    
    def load(self, fact_orders, dim_customer, dim_product, dim_date):
        """Load cleaned data to CSV files"""
        print("\n" + "=" * 60)
        print("LOAD PHASE")
        print("=" * 60)
        
        print("\n💾 Saving cleaned data to CSV files...")
        
        fact_orders.to_csv(CLEAN_DATA_DIR / 'fact_orders.csv', index=False)
        print(f"  ✓ Saved: fact_orders.csv ({len(fact_orders):,} rows)")
        
        dim_customer.to_csv(CLEAN_DATA_DIR / 'dim_customer.csv', index=False)
        print(f"  ✓ Saved: dim_customer.csv ({len(dim_customer):,} rows)")
        
        dim_product.to_csv(CLEAN_DATA_DIR / 'dim_product.csv', index=False)
        print(f"  ✓ Saved: dim_product.csv ({len(dim_product):,} rows)")
        
        dim_date.to_csv(CLEAN_DATA_DIR / 'dim_date.csv', index=False)
        print(f"  ✓ Saved: dim_date.csv ({len(dim_date):,} rows)")
        
        print("\n✅ ETL Pipeline completed successfully!")
        print(f"   Clean data saved to: {CLEAN_DATA_DIR}")
    
    def run(self):
        """Execute full ETL pipeline"""
        print("\n🚀 Starting InsightOps ETL Pipeline")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        try:
            # Extract
            self.extract()
            
            # Transform
            fact_orders, dim_customer, dim_product, dim_date = self.transform()
            
            # Load
            self.load(fact_orders, dim_customer, dim_product, dim_date)
            
            return True
            
        except Exception as e:
            print(f"\n❌ ETL Pipeline failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    pipeline = ETLPipeline()
    success = pipeline.run()
    sys.exit(0 if success else 1)
