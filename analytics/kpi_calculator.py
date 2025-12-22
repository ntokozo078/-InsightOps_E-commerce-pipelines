"""
KPI Calculator
Calculates and returns all key performance indicators
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import DATABASE_PATH


class KPICalculator:
    """Calculates business KPIs from the data warehouse"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    def _get_connection(self):
        """Get a new database connection (thread-safe)"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def get_executive_kpis(self):
        """Calculate executive-level KPIs"""
        
        conn = self._get_connection()
        
        try:
            # Total Revenue, Profit, Margin
            query = """
            SELECT 
                ROUND(SUM(revenue), 2) as total_revenue,
                ROUND(SUM(profit), 2) as total_profit,
                ROUND(SUM(profit) * 100.0 / SUM(revenue), 2) as profit_margin_pct
            FROM fact_orders
            WHERE payment_status = 'Success'
            """
            revenue_metrics = pd.read_sql(query, conn).iloc[0]
            
            # Order Success Rate
            query = """
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END) as successful_orders,
                ROUND(SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate_pct
            FROM fact_orders
            """
            success_metrics = pd.read_sql(query, conn).iloc[0]
            
            return {
                'total_revenue': revenue_metrics['total_revenue'],
                'total_profit': revenue_metrics['total_profit'],
                'profit_margin': revenue_metrics['profit_margin_pct'],
                'total_orders': success_metrics['total_orders'],
                'successful_orders': success_metrics['successful_orders'],
                'order_success_rate': success_metrics['success_rate_pct']
            }
        finally:
            conn.close()
    
    def get_operational_kpis(self):
        """Calculate operational KPIs"""
        
        conn = self._get_connection()
        
        try:
            # Average Order Value
            query = """
            SELECT 
                ROUND(AVG(revenue), 2) as avg_order_value
            FROM fact_orders
            WHERE payment_status = 'Success'
            """
            aov = pd.read_sql(query, conn).iloc[0]['avg_order_value']
            
            # Revenue per Customer by Segment
            query = """
            SELECT 
                c.segment,
                ROUND(SUM(f.revenue) / COUNT(DISTINCT f.customer_key), 2) as revenue_per_customer
            FROM fact_orders f
            JOIN dim_customer c ON f.customer_key = c.customer_key
            WHERE f.payment_status = 'Success'
            GROUP BY c.segment
            """
            revenue_per_customer = pd.read_sql(query, conn)
            
            # Failed Payment Rate by Channel
            query = """
            SELECT 
                channel,
                ROUND(SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failed_payment_pct
            FROM fact_orders
            GROUP BY channel
            """
            failed_payments = pd.read_sql(query, conn)
            
            return {
                'avg_order_value': aov,
                'revenue_per_customer': revenue_per_customer,
                'failed_payments': failed_payments
            }
        finally:
            conn.close()
    
    def get_monthly_trends(self):
        """Get monthly revenue and profit trends"""
        conn = self._get_connection()
        
        try:
            query = """
            SELECT 
                d.year,
                d.month,
                d.year || '-' || PRINTF('%02d', d.month) as year_month,
                COUNT(DISTINCT f.order_id) as order_count,
                ROUND(SUM(f.revenue), 2) as total_revenue,
                ROUND(SUM(f.profit), 2) as total_profit,
                ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct
            FROM fact_orders f
            JOIN dim_date d ON f.order_date_key = d.date_key
            WHERE f.payment_status = 'Success'
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month
            """
            return pd.read_sql(query, conn)
        finally:
            conn.close()
    
    def get_category_performance(self):
        """Get revenue and profit by category"""
        conn = self._get_connection()
        
        try:
            query = """
            SELECT 
                p.category,
                COUNT(*) as order_count,
                ROUND(SUM(f.revenue), 2) as total_revenue,
                ROUND(SUM(f.profit), 2) as total_profit,
                ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct
            FROM fact_orders f
            JOIN dim_product p ON f.product_key = p.product_key
            WHERE f.payment_status = 'Success'
            GROUP BY p.category
            ORDER BY total_revenue DESC
            LIMIT 15
            """
            return pd.read_sql(query, conn)
        finally:
            conn.close()
    
    def get_customer_segments(self):
        """Get customer segment distribution and performance"""
        conn = self._get_connection()
        
        try:
            query = """
            SELECT 
                c.segment,
                COUNT(DISTINCT c.customer_key) as customer_count,
                COUNT(DISTINCT f.order_id) as order_count,
                ROUND(SUM(f.revenue), 2) as total_revenue,
                ROUND(AVG(f.revenue), 2) as avg_order_value
            FROM dim_customer c
            LEFT JOIN fact_orders f ON c.customer_key = f.customer_key AND f.payment_status = 'Success'
            GROUP BY c.segment
            ORDER BY total_revenue DESC
            """
            return pd.read_sql(query, conn)
        finally:
            conn.close()
    
    def get_channel_performance(self):
        """Get performance metrics by channel"""
        conn = self._get_connection()
        
        try:
            query = """
            SELECT 
                f.channel,
                COUNT(*) as total_orders,
                SUM(CASE WHEN f.payment_status = 'Success' THEN 1 ELSE 0 END) as successful_orders,
                ROUND(SUM(CASE WHEN f.payment_status = 'Success' THEN f.revenue ELSE 0 END), 2) as revenue,
                ROUND(SUM(CASE WHEN f.payment_status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate_pct
            FROM fact_orders f
            GROUP BY f.channel
            ORDER BY revenue DESC
            """
            return pd.read_sql(query, conn)
        finally:
            conn.close()
    
    def get_top_customers(self, limit=10):
        """Get top customers by revenue"""
        conn = self._get_connection()
        
        try:
            query = f"""
            SELECT 
                c.customer_id,
                c.segment,
                c.country,
                COUNT(DISTINCT f.order_id) as order_count,
                ROUND(SUM(f.revenue), 2) as total_revenue,
                ROUND(AVG(f.revenue), 2) as avg_order_value
            FROM fact_orders f
            JOIN dim_customer c ON f.customer_key = c.customer_key
            WHERE f.payment_status = 'Success'
            GROUP BY c.customer_id, c.segment, c.country
            ORDER BY total_revenue DESC
            LIMIT {limit}
            """
            return pd.read_sql(query, conn)
        finally:
            conn.close()


if __name__ == "__main__":
    calc = KPICalculator()
    
    print("Executive KPIs:")
    print(calc.get_executive_kpis())
    
    print("\nOperational KPIs:")
    print(calc.get_operational_kpis())
