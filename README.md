# InsightOps – E-commerce BI System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3-green.svg)](https://www.sqlite.org/)

> **A production-grade Business Intelligence system demonstrating real-world BI workflows: star schema data warehousing, ETL pipelines, KPI tracking, and automated insights.**

---

## 📊 Business Context

An online store is experiencing **revenue stagnation** and **increasing customer churn**. Management lacks clear insight into which products, customers, and channels are driving profit versus loss.

**InsightOps** solves this by providing:
- ✅ Clear visibility into revenue vs profit by product
- ✅ Customer segmentation and retention analysis
- ✅ Channel performance and payment failure tracking
- ✅ Automated alerts for business-critical issues

---

## 🏗️ Architecture

### Data Model: Star Schema

This project implements a **proper star schema** with surrogate keys—the industry standard for BI systems.

```
┌─────────────────┐
│   dim_date      │
│─────────────────│
│ date_key (PK)   │◄────┐
│ date            │     │
│ year, month     │     │
│ quarter         │     │
└─────────────────┘     │
                        │
┌─────────────────┐     │     ┌──────────────────┐
│  dim_customer   │     │     │   fact_orders    │
│─────────────────│     │     │──────────────────│
│ customer_key(PK)│◄────┼─────│ order_id         │
│ customer_id     │     │     │ order_date_key(FK)│
│ country         │     └─────│ customer_key (FK)│
│ segment         │           │ product_key  (FK)│
└─────────────────┘     ┌─────│ quantity         │
                        │     │ revenue          │
┌─────────────────┐     │     │ cost             │
│  dim_product    │     │     │ profit           │
│─────────────────│     │     │ payment_status   │
│ product_key (PK)│◄────┘     │ channel          │
│ product_id      │           └──────────────────┘
│ category        │
│ brand           │
│ unit_cost       │
│ unit_price      │
└─────────────────┘
```

**Why Surrogate Keys?**
- Faster joins (integer vs string)
- Handles slowly changing dimensions
- Decouples warehouse from source systems
- Industry best practice for data warehousing

---

## 🚀 Features

### 1. ETL Pipeline (`scripts/etl_pipeline.py`)
- ✅ Extracts data from Olist Brazilian E-commerce dataset
- ✅ Cleans data: removes duplicates, standardizes dates, handles nulls
- ✅ Transforms: currency conversion (BRL→USD), profit calculation
- ✅ Loads: outputs clean CSVs ready for warehouse

### 2. Data Warehouse (`warehouse/`)
- ✅ SQLite database with star schema
- ✅ Foreign key constraints enforced
- ✅ Indexed for query performance
- ✅ 112,000+ fact records, 99,000+ customers, 32,000+ products

### 3. Analytics Engine (`analytics/`)
- ✅ **KPI Calculator**: Executive & operational metrics
- ✅ **Insights Engine**: Rule-based automated alerts
  - Low profit margin products (< 10%)
  - High payment failure channels (> 5%)
  - Customer retention issues

### 4. Interactive Dashboard (`dashboard/app.py`)

**4 Professional Pages:**

#### 📈 Executive Overview
- Total revenue, profit, margin
- Monthly trends
- Automated insights summary

#### 💰 Product Performance
- Revenue vs profit scatter plot
- Category breakdown
- Low-margin product alerts

#### 👥 Customer Insights
- Segment distribution (New/Returning/VIP)
- Revenue by segment
- Top 10 customers

#### 🔧 Operations
- Channel performance
- Payment failure rates
- Operational alerts

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip

### Quick Start

```bash
# 1. Clone or navigate to project directory
cd InsightOps

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run ETL pipeline (processes raw data)
python scripts/etl_pipeline.py

# 4. Load data warehouse
python warehouse/load_warehouse.py

# 5. Launch dashboard
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `https://ntokozo078--insightops-e-commerce-pipelines-dashboardapp-vbz2ih.streamlit.app/`

---

## 📁 Project Structure

```
InsightOps/
├── config.py                      # Central configuration
├── requirements.txt               # Python dependencies
│
├── scripts/
│   └── etl_pipeline.py           # ETL: Extract, Transform, Load
│
├── warehouse/
│   ├── schema.sql                # Star schema DDL
│   ├── load_warehouse.py         # Warehouse loader
│   ├── insightops.db             # SQLite database (generated)
│   └── queries/
│       ├── kpi_queries.sql       # KPI calculations
│       └── analytics_queries.sql # Business question queries
│
├── analytics/
│   ├── kpi_calculator.py         # KPI calculation engine
│   └── insights_engine.py        # Automated insights
│
├── dashboard/
│   └── app.py                    # Streamlit dashboard (4 pages)
│
├── data/
│   └── clean/                    # Cleaned data (generated)
│       ├── fact_orders.csv
│       ├── dim_customer.csv
│       ├── dim_product.csv
│       └── dim_date.csv
│
└── docs/
    └── DATA_DICTIONARY.md        # Data documentation
```

---

## 📊 Key Performance Indicators (KPIs)

### Executive KPIs
| KPI | Description |
|-----|-------------|
| **Total Revenue** | Sum of all successful order revenue |
| **Total Profit** | Revenue minus cost |
| **Profit Margin** | Profit as % of revenue |
| **Order Success Rate** | % of orders with successful payment |

### Operational KPIs
| KPI | Description |
|-----|-------------|
| **Failed Payment %** | % of failed payments by channel |
| **Avg Order Value** | Average revenue per order |
| **Revenue per Customer** | Total revenue / unique customers |
| **Revenue by Category** | Revenue breakdown by product category |

---

## 🎯 Business Questions Answered

This BI system answers the critical questions management needs:

### 1. Which products generate high revenue but low profit?
→ **Product Performance** page shows revenue vs profit scatter plot with margin color-coding

### 2. Which customer segments churn fastest?
→ **Customer Insights** page shows segment analysis and one-time purchase rates

### 3. Which channels produce orders but fail payments?
→ **Operations** page tracks payment failure rates by channel

### 4. Which categories should be discontinued?
→ **Product Performance** page flags low-margin categories with alerts

---

## 🔍 Automated Insights

The system automatically generates alerts based on business rules:

- 🚨 **High Priority**: Profit margin < 5%, Payment failures > 10%
- ⚠️ **Medium Priority**: Profit margin < 10%, Payment failures > 5%
- ℹ️ **Low Priority**: Category performance recommendations

Example insights:
```
⚠️ Low Margin Alert: Electronics
   Category 'Electronics' has 8.2% margin (below 10% threshold) with $45,230 revenue

🚨 High Failure Rate: Mobile Channel
   Mobile channel has 7.3% payment failure rate, losing $12,450 in revenue
```

---

## 🛠️ Technology Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| **ETL** | Python + Pandas | Industry standard for data transformation |
| **Warehouse** | SQLite | Lightweight, no server setup, easy to share |
| **Analytics** | SQL + Python | SQL for queries, Python for business logic |
| **Dashboard** | Streamlit | Fast, interactive, Python-native |
| **Visualization** | Plotly | Professional, interactive charts |

**Optional Upgrade Path:**
- PostgreSQL (production warehouse)
- dbt (advanced data modeling)
- Power BI (enterprise dashboards)

---

## 📈 Data Pipeline Workflow

```
┌─────────────────┐
│  Raw CSV Data   │  Olist Brazilian E-commerce Dataset
│  (datasets/)    │  • orders, customers, products, payments
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ETL Pipeline   │  scripts/etl_pipeline.py
│                 │  • Remove duplicates
│                 │  • Standardize dates
│                 │  • Convert currency
│                 │  • Calculate profit
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Clean Data     │  data/clean/*.csv
│  (Star Schema)  │  • fact_orders
│                 │  • dim_customer, dim_product, dim_date
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Warehouse  │  warehouse/insightops.db
│  (SQLite)       │  • Star schema with FK constraints
│                 │  • Indexed for performance
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Analytics     │  analytics/*.py
│   & Insights    │  • KPI calculations
│                 │  • Automated alerts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │  dashboard/app.py
│  (Streamlit)    │  • 4 interactive pages
│                 │  • Real-time insights
└─────────────────┘
```

---

## 💼 Why This Project Stands Out

### For Recruiters:
✅ **Real BI workflow** - Not just analysis, but full ETL → Warehouse → Dashboard pipeline  
✅ **Proper data modeling** - Star schema with surrogate keys (industry standard)  
✅ **Production patterns** - Modular code, configuration management, error handling  
✅ **Business impact** - Answers real questions with actionable insights  
✅ **Clean execution** - Professional design, no fluff, focused on value  

### Skills Demonstrated:
- Data Warehousing (star schema, dimensional modeling)
- ETL Development (Python, Pandas)
- SQL (complex queries, window functions, CTEs)
- Data Visualization (Plotly, Streamlit)
- Business Intelligence (KPIs, metrics, insights)
- Software Engineering (modular design, configuration, documentation)

---

## 📝 Dataset

This project uses the **Olist Brazilian E-commerce Dataset** - a real-world dataset with:
- 100K+ orders from 2016-2018
- 99K+ customers
- 32K+ products
- Multiple tables (orders, customers, products, payments, reviews)

**Data Source**: Olist Store (Brazilian e-commerce platform)

---

## 🎓 Learning Outcomes

By building this project, you demonstrate understanding of:

1. **Data Modeling**: Why star schema? When to use surrogate keys?
2. **ETL Design**: How to clean messy data systematically
3. **SQL Mastery**: Complex joins, aggregations, window functions
4. **BI Thinking**: What metrics matter? How to surface insights?
5. **Production Skills**: Code organization, documentation, deployment

---

## 🚀 Next Steps / Enhancements

Want to take this further?

- [ ] Add dbt for advanced data modeling
- [ ] Implement slowly changing dimensions (SCD Type 2)
- [ ] Add data quality tests
- [ ] Deploy to cloud (AWS/Azure/GCP)
- [ ] Add machine learning (churn prediction, demand forecasting)
- [ ] Migrate to PostgreSQL for production scale
- [ ] Add CI/CD pipeline
- [ ] Implement incremental loads

---

## 📧 Contact

**Built by**: [Ntokozo Ntombela]  
**LinkedIn**: [https://www.linkedin.com/in/ntokozo-ntombela-ba662235a/]  
**GitHub**: [https://github.com/ntokozo078]

---

## 📄 License

This project is open source and available for educational and portfolio purposes.

---

**⭐ If this helped you land a BI/Data Analyst role, let me know!**
