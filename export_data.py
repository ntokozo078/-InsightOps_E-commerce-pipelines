"""
InsightOps – Data Export Script
Runs once at build time to pre-compute all dashboard data as JSON.
This avoids hitting the SQLite DB at request time on Render.
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from analytics.kpi_calculator import KPICalculator
from analytics.insights_engine import InsightsEngine

OUTPUT_FILE = Path(__file__).parent / "dashboard" / "data" / "dashboard_data.json"


def export():
    print("[InsightOps] Exporting dashboard data to JSON...")

    kpi = KPICalculator()
    engine = InsightsEngine()

    # ── Executive KPIs ──────────────────────────────────────────────────────
    exec_kpis = kpi.get_executive_kpis()

    # ── Monthly Trends ───────────────────────────────────────────────────────
    trends_df = kpi.get_monthly_trends()
    trends = {
        "year_month": trends_df["year_month"].tolist(),
        "revenue": trends_df["total_revenue"].tolist(),
        "profit": trends_df["total_profit"].tolist(),
        "orders": trends_df["order_count"].tolist(),
    }

    # ── Category Performance ─────────────────────────────────────────────────
    cat_df = kpi.get_category_performance()
    categories = {
        "category": cat_df["category"].tolist(),
        "revenue": cat_df["total_revenue"].tolist(),
        "profit": cat_df["total_profit"].tolist(),
        "margin": cat_df["profit_margin_pct"].tolist(),
        "orders": cat_df["order_count"].tolist(),
    }

    # ── Customer Segments ─────────────────────────────────────────────────────
    seg_df = kpi.get_customer_segments()
    segments = {
        "segment": seg_df["segment"].tolist(),
        "customer_count": seg_df["customer_count"].tolist(),
        "order_count": seg_df["order_count"].tolist(),
        "revenue": seg_df["total_revenue"].tolist(),
        "avg_order_value": seg_df["avg_order_value"].tolist(),
    }

    # ── Top Customers ─────────────────────────────────────────────────────────
    top_customers_df = kpi.get_top_customers(10)
    top_customers = top_customers_df.to_dict(orient="records")

    # ── Channel Performance ───────────────────────────────────────────────────
    ch_df = kpi.get_channel_performance()
    channels = {
        "channel": ch_df["channel"].tolist(),
        "total_orders": ch_df["total_orders"].tolist(),
        "successful_orders": ch_df["successful_orders"].tolist(),
        "revenue": ch_df["revenue"].tolist(),
        "failure_rate": ch_df["failure_rate_pct"].tolist(),
    }

    # ── Automated Insights ────────────────────────────────────────────────────
    insights = engine.generate_all_insights()

    # ── Bundle everything ─────────────────────────────────────────────────────
    payload = {
        "kpis": {
            "total_revenue": exec_kpis["total_revenue"],
            "total_profit": exec_kpis["total_profit"],
            "profit_margin": exec_kpis["profit_margin"],
            "order_success_rate": exec_kpis["order_success_rate"],
            "total_orders": exec_kpis["total_orders"],
            "successful_orders": exec_kpis["successful_orders"],
        },
        "trends": trends,
        "categories": categories,
        "segments": segments,
        "top_customers": top_customers,
        "channels": channels,
        "insights": insights,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(payload, f, default=str)

    print(f"[OK] Data exported -> {OUTPUT_FILE}")
    print(f"   KPIs: revenue=${exec_kpis['total_revenue']:,.0f}, margin={exec_kpis['profit_margin']:.1f}%")
    print(f"   Insights: {len(insights)} generated")


if __name__ == "__main__":
    export()
