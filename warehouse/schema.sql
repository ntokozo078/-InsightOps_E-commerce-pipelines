-- InsightOps Data Warehouse Schema
-- Star Schema Implementation with Surrogate Keys
-- ============================================
-- DIMENSION TABLES
-- ============================================
-- Date Dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    weekday TEXT NOT NULL
);
-- Customer Dimension
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    country TEXT,
    signup_date DATE,
    segment TEXT CHECK(segment IN ('New', 'Returning', 'VIP'))
);
-- Product Dimension
CREATE TABLE IF NOT EXISTS dim_product (
    product_key INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL UNIQUE,
    category TEXT,
    brand TEXT,
    unit_cost REAL,
    unit_price REAL
);
-- ============================================
-- FACT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id TEXT NOT NULL,
    order_date_key INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    revenue REAL NOT NULL,
    cost REAL NOT NULL,
    profit REAL NOT NULL,
    payment_status TEXT CHECK(payment_status IN ('Success', 'Failed')),
    channel TEXT,
    -- Foreign Key Constraints
    FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    -- Composite Primary Key
    PRIMARY KEY (order_id, product_key)
);
-- ============================================
-- INDEXES FOR QUERY PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON fact_orders(order_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_customer ON fact_orders(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_product ON fact_orders(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_channel ON fact_orders(channel);
CREATE INDEX IF NOT EXISTS idx_fact_orders_payment_status ON fact_orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_dim_customer_segment ON dim_customer(segment);
CREATE INDEX IF NOT EXISTS idx_dim_product_category ON dim_product(category);
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON dim_date(year, month);