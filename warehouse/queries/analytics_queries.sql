-- InsightOps Analytics Queries
-- SQL queries to answer key business questions
-- ============================================
-- QUESTION 1: Which products generate high revenue but low profit?
-- ============================================
SELECT p.product_id,
    p.category,
    COUNT(DISTINCT f.order_id) as order_count,
    ROUND(SUM(f.revenue), 2) as total_revenue,
    ROUND(SUM(f.profit), 2) as total_profit,
    ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct,
    CASE
        WHEN SUM(f.profit) * 100.0 / SUM(f.revenue) < 10 THEN '🚨 LOW MARGIN'
        WHEN SUM(f.profit) * 100.0 / SUM(f.revenue) < 20 THEN '⚠️  MEDIUM MARGIN'
        ELSE '✅ HEALTHY MARGIN'
    END as margin_status
FROM fact_orders f
    JOIN dim_product p ON f.product_key = p.product_key
WHERE f.payment_status = 'Success'
GROUP BY p.product_id,
    p.category
HAVING SUM(f.revenue) > 100 -- Only products with significant revenue
ORDER BY total_revenue DESC,
    profit_margin_pct ASC
LIMIT 20;
-- ============================================
-- QUESTION 2: Which customer segments churn fastest?
-- ============================================
WITH customer_orders AS (
    SELECT c.customer_key,
        c.segment,
        MIN(d.date) as first_order_date,
        MAX(d.date) as last_order_date,
        COUNT(DISTINCT f.order_id) as total_orders,
        JULIANDAY(MAX(d.date)) - JULIANDAY(MIN(d.date)) as days_active
    FROM fact_orders f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        JOIN dim_date d ON f.order_date_key = d.date_key
    WHERE f.payment_status = 'Success'
    GROUP BY c.customer_key,
        c.segment
),
segment_analysis AS (
    SELECT segment,
        COUNT(*) as customer_count,
        ROUND(AVG(total_orders), 2) as avg_orders_per_customer,
        ROUND(AVG(days_active), 0) as avg_days_active,
        COUNT(
            CASE
                WHEN total_orders = 1 THEN 1
            END
        ) as one_time_customers,
        ROUND(
            COUNT(
                CASE
                    WHEN total_orders = 1 THEN 1
                END
            ) * 100.0 / COUNT(*),
            2
        ) as churn_rate_pct
    FROM customer_orders
    GROUP BY segment
)
SELECT segment,
    customer_count,
    avg_orders_per_customer,
    avg_days_active,
    one_time_customers,
    churn_rate_pct,
    CASE
        WHEN churn_rate_pct > 70 THEN '🚨 HIGH CHURN'
        WHEN churn_rate_pct > 50 THEN '⚠️  MODERATE CHURN'
        ELSE '✅ LOW CHURN'
    END as churn_status
FROM segment_analysis
ORDER BY churn_rate_pct DESC;
-- ============================================
-- QUESTION 3: Which channels produce orders but fail payments?
-- ============================================
SELECT f.channel,
    COUNT(*) as total_orders,
    SUM(
        CASE
            WHEN f.payment_status = 'Success' THEN 1
            ELSE 0
        END
    ) as successful_orders,
    SUM(
        CASE
            WHEN f.payment_status = 'Failed' THEN 1
            ELSE 0
        END
    ) as failed_orders,
    ROUND(
        SUM(
            CASE
                WHEN f.payment_status = 'Failed' THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) as failure_rate_pct,
    ROUND(
        SUM(
            CASE
                WHEN f.payment_status = 'Success' THEN f.revenue
                ELSE 0
            END
        ),
        2
    ) as successful_revenue,
    ROUND(
        SUM(
            CASE
                WHEN f.payment_status = 'Failed' THEN f.revenue
                ELSE 0
            END
        ),
        2
    ) as lost_revenue,
    CASE
        WHEN SUM(
            CASE
                WHEN f.payment_status = 'Failed' THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*) > 5 THEN '🚨 HIGH FAILURE'
        WHEN SUM(
            CASE
                WHEN f.payment_status = 'Failed' THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*) > 2 THEN '⚠️  MODERATE FAILURE'
        ELSE '✅ LOW FAILURE'
    END as failure_status
FROM fact_orders f
GROUP BY f.channel
ORDER BY failure_rate_pct DESC;
-- ============================================
-- QUESTION 4: Which categories should be discontinued?
-- ============================================
WITH category_performance AS (
    SELECT p.category,
        COUNT(DISTINCT f.order_id) as order_count,
        ROUND(SUM(f.revenue), 2) as total_revenue,
        ROUND(SUM(f.profit), 2) as total_profit,
        ROUND(SUM(f.profit) * 100.0 / SUM(f.revenue), 2) as profit_margin_pct,
        ROUND(SUM(f.revenue) / COUNT(DISTINCT f.order_id), 2) as avg_order_value
    FROM fact_orders f
        JOIN dim_product p ON f.product_key = p.product_key
    WHERE f.payment_status = 'Success'
    GROUP BY p.category
),
category_ranking AS (
    SELECT *,
        PERCENT_RANK() OVER (
            ORDER BY total_revenue DESC
        ) as revenue_percentile,
        PERCENT_RANK() OVER (
            ORDER BY profit_margin_pct DESC
        ) as margin_percentile
    FROM category_performance
)
SELECT category,
    order_count,
    total_revenue,
    total_profit,
    profit_margin_pct,
    avg_order_value,
    CASE
        WHEN profit_margin_pct < 10
        AND revenue_percentile > 0.7 THEN '🚨 DISCONTINUE - Low margin, low revenue'
        WHEN profit_margin_pct < 15 THEN '⚠️  REVIEW - Low margin'
        WHEN revenue_percentile > 0.8 THEN '⚠️  REVIEW - Low revenue'
        ELSE '✅ KEEP'
    END as recommendation
FROM category_ranking
ORDER BY CASE
        WHEN profit_margin_pct < 10
        AND revenue_percentile > 0.7 THEN 1
        WHEN profit_margin_pct < 15 THEN 2
        WHEN revenue_percentile > 0.8 THEN 3
        ELSE 4
    END,
    total_revenue DESC;
-- ============================================
-- ADDITIONAL INSIGHTS
-- ============================================
-- Top 10 Customers by Revenue
SELECT c.customer_id,
    c.segment,
    c.country,
    COUNT(DISTINCT f.order_id) as order_count,
    ROUND(SUM(f.revenue), 2) as total_revenue,
    ROUND(SUM(f.profit), 2) as total_profit,
    ROUND(AVG(f.revenue), 2) as avg_order_value
FROM fact_orders f
    JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE f.payment_status = 'Success'
GROUP BY c.customer_id,
    c.segment,
    c.country
ORDER BY total_revenue DESC
LIMIT 10;
-- Product Category Mix
SELECT p.category,
    COUNT(DISTINCT p.product_id) as product_count,
    COUNT(DISTINCT f.order_id) as order_count,
    ROUND(SUM(f.revenue), 2) as total_revenue,
    ROUND(
        COUNT(DISTINCT f.order_id) * 100.0 / (
            SELECT COUNT(DISTINCT order_id)
            FROM fact_orders
            WHERE payment_status = 'Success'
        ),
        2
    ) as order_share_pct,
    ROUND(
        SUM(f.revenue) * 100.0 / (
            SELECT SUM(revenue)
            FROM fact_orders
            WHERE payment_status = 'Success'
        ),
        2
    ) as revenue_share_pct
FROM fact_orders f
    JOIN dim_product p ON f.product_key = p.product_key
WHERE f.payment_status = 'Success'
GROUP BY p.category
ORDER BY total_revenue DESC;