"""
Insights Engine
Generates automated, rule-based insights from data
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import DATABASE_PATH, BUSINESS_RULES


class InsightsEngine:
    """Generates automated business insights"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.insights = []
    
    def _get_connection(self):
        """Get a new database connection (thread-safe)"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def analyze_low_margin_products(self):
        """Flag products with profit margin < threshold"""
        threshold = BUSINESS_RULES['low_profit_margin_threshold'] * 100
        conn = self._get_connection()
        
        try:
            query = f"""
            SELECT 
                p.category,
                COUNT(DISTINCT p.product_id) as product_count,
                ROUND(SUM(f.revenue), 2) as total_revenue,
                ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct
            FROM fact_orders f
            JOIN dim_product p ON f.product_key = p.product_key
            WHERE f.payment_status = 'Success'
            GROUP BY p.category
            HAVING profit_margin_pct < {threshold}
            ORDER BY total_revenue DESC
            """
            
            low_margin = pd.read_sql(query, conn)
            
            if not low_margin.empty:
                for _, row in low_margin.iterrows():
                    self.insights.append({
                        'type': 'warning',
                        'category': 'Product Performance',
                        'title': f"Low Margin Alert: {row['category']}",
                        'message': f"Category '{row['category']}' has {row['profit_margin_pct']:.1f}% margin (below {threshold}% threshold) with ${row['total_revenue']:,.0f} revenue",
                        'severity': 'high' if row['profit_margin_pct'] < threshold/2 else 'medium'
                    })
        finally:
            conn.close()
    
    def analyze_failed_payments(self):
        """Alert channels with high payment failure rates"""
        threshold = BUSINESS_RULES['high_failed_payment_threshold'] * 100
        conn = self._get_connection()
        
        try:
            query = f"""
            SELECT 
                channel,
                COUNT(*) as total_orders,
                ROUND(SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate_pct,
                ROUND(SUM(CASE WHEN payment_status = 'Failed' THEN revenue ELSE 0 END), 2) as lost_revenue
            FROM fact_orders
            GROUP BY channel
            HAVING failure_rate_pct > {threshold}
            ORDER BY failure_rate_pct DESC
            """
            
            high_failures = pd.read_sql(query, conn)
            
            if not high_failures.empty:
                for _, row in high_failures.iterrows():
                    self.insights.append({
                        'type': 'alert',
                        'category': 'Payment Operations',
                        'title': f"High Failure Rate: {row['channel']} Channel",
                        'message': f"{row['channel']} channel has {row['failure_rate_pct']:.1f}% payment failure rate, losing ${row['lost_revenue']:,.0f} in revenue",
                        'severity': 'high' if row['failure_rate_pct'] > threshold * 2 else 'medium'
                    })
        finally:
            conn.close()
    
    def analyze_customer_retention(self):
        """Identify segments with retention issues"""
        conn = self._get_connection()
        
        try:
            query = """
            WITH customer_orders AS (
                SELECT 
                    c.segment,
                    c.customer_key,
                    COUNT(DISTINCT f.order_id) as order_count
                FROM dim_customer c
                LEFT JOIN fact_orders f ON c.customer_key = f.customer_key AND f.payment_status = 'Success'
                GROUP BY c.segment, c.customer_key
            )
            SELECT 
                segment,
                COUNT(*) as total_customers,
                SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END) as one_time_customers,
                ROUND(SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as one_time_pct
            FROM customer_orders
            GROUP BY segment
            ORDER BY one_time_pct DESC
            """
            
            retention = pd.read_sql(query, conn)
            
            for _, row in retention.iterrows():
                if row['one_time_pct'] > 70:
                    self.insights.append({
                        'type': 'info',
                        'category': 'Customer Retention',
                        'title': f"Retention Concern: {row['segment']} Segment",
                        'message': f"{row['one_time_pct']:.1f}% of {row['segment']} customers ({row['one_time_customers']:,}) made only one purchase",
                        'severity': 'medium'
                    })
        finally:
            conn.close()
    
    def analyze_category_performance(self):
        """Identify underperforming categories"""
        conn = self._get_connection()
        
        try:
            query = """
            WITH category_stats AS (
                SELECT 
                    p.category,
                    COUNT(DISTINCT f.order_id) as order_count,
                    ROUND(SUM(f.revenue), 2) as total_revenue,
                    ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct
                FROM fact_orders f
                JOIN dim_product p ON f.product_key = p.product_key
                WHERE f.payment_status = 'Success'
                GROUP BY p.category
            ),
            ranked_categories AS (
                SELECT 
                    category,
                    order_count,
                    total_revenue,
                    profit_margin_pct,
                    PERCENT_RANK() OVER (ORDER BY total_revenue) as revenue_percentile
                FROM category_stats
            )
            SELECT 
                category,
                order_count,
                total_revenue,
                profit_margin_pct
            FROM ranked_categories
            WHERE revenue_percentile < 0.2 AND profit_margin_pct < 15
            ORDER BY total_revenue ASC
            LIMIT 5
            """
            
            underperforming = pd.read_sql(query, conn)
            
            if not underperforming.empty:
                categories = ', '.join(underperforming['category'].tolist())
                self.insights.append({
                    'type': 'recommendation',
                    'category': 'Category Management',
                    'title': 'Categories to Review for Discontinuation',
                    'message': f"Consider reviewing these low-revenue, low-margin categories: {categories}",
                    'severity': 'low'
                })
        finally:
            conn.close()
    
    def analyze_top_performers(self):
        """Highlight top performing categories and customers"""
        conn = self._get_connection()
        
        try:
            # Top category
            query = """
            SELECT 
                p.category,
                ROUND(SUM(f.revenue), 2) as total_revenue,
                ROUND(SUM(f.profit), 2) as total_profit
            FROM fact_orders f
            JOIN dim_product p ON f.product_key = p.product_key
            WHERE f.payment_status = 'Success'
            GROUP BY p.category
            ORDER BY total_revenue DESC
            LIMIT 1
            """
            top_category = pd.read_sql(query, conn).iloc[0]
            
            self.insights.append({
                'type': 'success',
                'category': 'Top Performers',
                'title': f"Top Category: {top_category['category']}",
                'message': f"Generated ${top_category['total_revenue']:,.0f} in revenue with ${top_category['total_profit']:,.0f} profit",
                'severity': 'low'
            })
        finally:
            conn.close()
    
    def generate_all_insights(self):
        """Generate all automated insights"""
        self.insights = []
        
        self.analyze_low_margin_products()
        self.analyze_failed_payments()
        self.analyze_customer_retention()
        self.analyze_category_performance()
        self.analyze_top_performers()
        
        return self.insights
    
    def get_insights_summary(self):
        """Get summary of insights by severity"""
        if not self.insights:
            self.generate_all_insights()
        
        summary = {
            'total': len(self.insights),
            'high': len([i for i in self.insights if i['severity'] == 'high']),
            'medium': len([i for i in self.insights if i['severity'] == 'medium']),
            'low': len([i for i in self.insights if i['severity'] == 'low'])
        }
        
        return summary


if __name__ == "__main__":
    engine = InsightsEngine()
    
    insights = engine.generate_all_insights()
    
    print(f"\n🔍 Generated {len(insights)} insights:\n")
    for insight in insights:
        icon = {'warning': '⚠️', 'alert': '🚨', 'info': 'ℹ️', 'recommendation': '💡', 'success': '✅'}
        print(f"{icon.get(insight['type'], '•')} [{insight['category']}] {insight['title']}")
        print(f"   {insight['message']}\n")
