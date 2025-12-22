-- InsightOps KPI Queries
-- SQL queries for calculating key performance indicators
-- ============================================
-- EXECUTIVE KPIs
-- ============================================
-- Total Revenue
SELECT SUM(revenue) as total_revenue,
    SUM(profit) as total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(revenue), 2) as profit_margin_pct
FROM fact_orders
WHERE payment_status = 'Success';
-- Order Success Rate
SELECT COUNT(*) as total_orders,
    SUM(
        CASE
            WHEN payment_status = 'Success' THEN 1
            ELSE 0
        END
    ) as successful_orders,
    ROUND(
        SUM(
            CASE
                WHEN payment_status = 'Success' THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) as success_rate_pct
FROM fact_orders;
-- Customer Retention Rate (Month over Month)
WITH monthly_customers AS (
    SELECT d.year,
        d.month,
        f.customer_key,
        COUNT(DISTINCT f.order_id) as order_count
    FROM fact_orders f
        JOIN dim_date d ON f.order_date_key = d.date_key
    WHERE f.payment_status = 'Success'
    GROUP BY d.year,
        d.month,
        f.customer_key
),
retention AS (
    SELECT curr.year,
        curr.month,
        COUNT(DISTINCT curr.customer_key) as current_customers,
        COUNT(DISTINCT prev.customer_key) as retained_customers
    FROM monthly_customers curr
        LEFT JOIN monthly_customers prev ON curr.customer_key = prev.customer_key
        AND curr.year = prev.year
        AND curr.month = prev.month + 1
    GROUP BY curr.year,
        curr.month
)
SELECT year,
    month,
    current_customers,
    retained_customers,
    ROUND(
        retained_customers * 100.0 / NULLIF(current_customers, 0),
        2
    ) as retention_rate_pct
FROM retention
ORDER BY year,
    month;
-- ============================================
-- OPERATIONAL KPIs
-- ============================================
-- Failed Payment Percentage
SELECT channel,
    COUNT(*) as total_orders,
    SUM(
        CASE
            WHEN payment_status = 'Failed' THEN 1
            ELSE 0
        END
    ) as failed_orders,
    ROUND(
        SUM(
            CASE
                WHEN payment_status = 'Failed' THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) as failed_payment_pct
FROM fact_orders
GROUP BY channel
ORDER BY failed_payment_pct DESC;
-- Average Order Value
SELECT ROUND(AVG(revenue), 2) as avg_order_value,
    ROUND(MIN(revenue), 2) as min_order_value,
    ROUND(MAX(revenue), 2) as max_order_value
FROM fact_orders
WHERE payment_status = 'Success';
-- Revenue per Customer
SELECT c.segment,
    COUNT(DISTINCT f.customer_key) as customer_count,
    ROUND(SUM(f.revenue), 2) as total_revenue,
    ROUND(AVG(f.revenue), 2) as avg_revenue_per_order,
    ROUND(
        SUM(f.revenue) / COUNT(DISTINCT f.customer_key),
        2
    ) as revenue_per_customer
FROM fact_orders f
    JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE f.payment_status = 'Success'
GROUP BY c.segment
ORDER BY revenue_per_customer DESC;
-- Revenue by Category
SELECT p.category,
    COUNT(*) as order_count,
    ROUND(SUM(f.revenue), 2) as total_revenue,
    ROUND(SUM(f.profit), 2) as total_profit,
    ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct
FROM fact_orders f
    JOIN dim_product p ON f.product_key = p.product_key
WHERE f.payment_status = 'Success'
GROUP BY p.category
ORDER BY total_revenue DESC
LIMIT 10;
-- ============================================
-- TREND ANALYSIS
-- ============================================
-- Monthly Revenue and Profit Trends
SELECT d.year,
    d.month,
    COUNT(DISTINCT f.order_id) as order_count,
    ROUND(SUM(f.revenue), 2) as total_revenue,
    ROUND(SUM(f.profit), 2) as total_profit,
    ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct
FROM fact_orders f
    JOIN dim_date d ON f.order_date_key = d.date_key
WHERE f.payment_status = 'Success'
GROUP BY d.year,
    d.month
ORDER BY d.year,
    d.month;
-- Channel Performance Over Time
SELECT d.year,
    d.month,
    f.channel,
    COUNT(*) as order_count,
    ROUND(SUM(f.revenue), 2) as revenue,
    ROUND(
        SUM(
            CASE
                WHEN f.payment_status = 'Failed' THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) as failed_pct
FROM fact_orders f
    JOIN dim_date d ON f.order_date_key = d.date_key
GROUP BY d.year,
    d.month,
    f.channel
ORDER BY d.year,
    d.month,
    f.channel;