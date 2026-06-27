import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
from streamlit_option_menu import option_menu

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Walmart Dashboard",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# DB CONNECTION
# =====================================================
@st.cache_resource
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="walmart_db"
    )

conn = get_connection()

# =====================================================
# FILTERS
# =====================================================
st.sidebar.header("🎯 Filters")

cities = pd.read_sql("SELECT DISTINCT city FROM walmart", conn)["city"].tolist()
payments = pd.read_sql("SELECT DISTINCT payment_method FROM walmart", conn)["payment_method"].tolist()

years = pd.read_sql("""
    SELECT DISTINCT YEAR(STR_TO_DATE(date,'%d/%m/%Y')) AS year
    FROM walmart
    ORDER BY year
""", conn)["year"].dropna().astype(int).tolist()

city_filter = st.sidebar.selectbox("City", ["All"] + cities)
payment_filter = st.sidebar.selectbox("Payment Method", ["All"] + payments)
year_filter = st.sidebar.selectbox("Year", ["All"] + years)

def build_where():
    conditions = []

    if city_filter != "All":
        conditions.append(f"city = '{city_filter}'")

    if payment_filter != "All":
        conditions.append(f"payment_method = '{payment_filter}'")

    if year_filter != "All":
        conditions.append(f"YEAR(STR_TO_DATE(date,'%d/%m/%Y')) = {year_filter}")

    return "WHERE " + " AND ".join(conditions) if conditions else ""

filter_sql = build_where()

# =====================================================
# NAVIGATION
# =====================================================
with st.sidebar:
    page = option_menu(
        "Walmart Dashboard",
        ["KPIs", "EDA Charts", "SQL Explorer", "Project Summary"],
        icons=["speedometer2", "bar-chart", "database", "info-circle"],
        default_index=0
    )

# =====================================================
# KPIs PAGE (UPDATED WITH DESCRIPTION)
# =====================================================
if page == "KPIs":

    st.title("📊 Walmart Sales Overview")

   

    kpi = pd.read_sql(f"""
        SELECT 
            COUNT(*) AS total_txn,
            SUM(total) AS revenue,
            SUM(quantity) AS total_qty,
            AVG(rating) AS avg_rating,
            COUNT(DISTINCT branch) AS branches
        FROM walmart
        {filter_sql}
    """, conn)

    revenue_m = kpi["revenue"][0] / 1_000_000

    st.markdown("### 📈 Key Performance Indicators")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Transactions", int(kpi["total_txn"][0]))
    c2.metric("Revenue", f"$ {revenue_m:.2f}M")
    c3.metric("Quantity Sold", int(kpi["total_qty"][0]))
    c4.metric("Avg Rating", round(kpi["avg_rating"][0], 2))
    c5.metric("Branches", int(kpi["branches"][0]))

    st.markdown("""
    ### 📌 What this KPI section shows?

    This section provides a quick business snapshot of Walmart’s performance.

    It helps us understand:
    - Overall sales performance
    - Customer transaction volume
    - Product quantity movement
    - Customer satisfaction (ratings)
    - Branch coverage across locations

    These KPIs are useful for executives and decision-makers to quickly evaluate business health without going into detailed analysis.
    """)

# =====================================================
# EDA CHARTS PAGE
# =====================================================
elif page == "EDA Charts":

    st.title("📊 Walmart Data Analysis Dashboard")

    df = pd.read_sql(f"""
        SELECT payment_method,
               COUNT(*) transactions,
               SUM(quantity) total_quantity
        FROM walmart
        {filter_sql}
        GROUP BY payment_method
    """, conn)

    st.subheader("💳 Payment Method Analysis")
    fig = px.bar(df, x="payment_method", y="transactions", text="total_quantity")
    st.plotly_chart(fig, use_container_width=True)

    df = pd.read_sql(f"""
        SELECT category,
               SUM(total) revenue
        FROM walmart
        {filter_sql}
        GROUP BY category
    """, conn)

    st.subheader("💰 Revenue by Category")
    fig = px.bar(df, x="category", y="revenue", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    df = pd.read_sql(f"""
        SELECT category,
               SUM(unit_price * quantity * profit_margin) profit
        FROM walmart
        {filter_sql}
        GROUP BY category
    """, conn)

    st.subheader("📈 Profit by Category")
    fig = px.bar(df, x="category", y="profit", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    df = pd.read_sql(f"""
        SELECT city, AVG(rating) avg_rating
        FROM walmart
        {filter_sql}
        GROUP BY city
    """, conn)

    st.subheader("⭐ Customer Rating by City")
    fig = px.bar(df, x="city", y="avg_rating", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    df = pd.read_sql(f"""
        SELECT 
            CASE 
                WHEN HOUR(TIME(time)) < 12 THEN 'Morning'
                WHEN HOUR(TIME(time)) < 17 THEN 'Afternoon'
                ELSE 'Evening'
            END shift,
            COUNT(*) transactions
        FROM walmart
        {filter_sql}
        GROUP BY shift
    """, conn)

    st.subheader("⏰ Sales by Shift")
    fig = px.pie(df, names="shift", values="transactions")
    st.plotly_chart(fig, use_container_width=True)

    df = pd.read_sql(f"""
        SELECT category,
               SUM(quantity) total_units
        FROM walmart
        {filter_sql}
        GROUP BY category
    """, conn)

    st.subheader("📦 Top Selling Categories")
    fig = px.bar(df, x="category", y="total_units", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    df = pd.read_sql(f"""
        SELECT payment_method,
               AVG(total) avg_bill
        FROM walmart
        {filter_sql}
        GROUP BY payment_method
    """, conn)

    st.subheader("🧾 Average Bill Value")
    fig = px.bar(df, x="payment_method", y="avg_bill", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# SQL EXPLORER PAGE
# =====================================================
elif page == "SQL Explorer":

    st.title("🗄️ SQL Query Explorer")

    queries = {

        "Total Records":
            "SELECT COUNT(*) AS total_records FROM walmart",

        "Payment Methods":
            "SELECT payment_method, COUNT(*) FROM walmart GROUP BY payment_method",

        "Distinct Branches":
            "SELECT COUNT(DISTINCT branch) FROM walmart",

        "Minimum Quantity":
            "SELECT MIN(quantity) FROM walmart",

        "Payment + Quantity Analysis":
            """
            SELECT payment_method,
                   COUNT(*) no_payments,
                   SUM(quantity) no_qty_sold
            FROM walmart
            GROUP BY payment_method
            """,

        "Highest Rated Category per Branch":
            """
            SELECT branch, category, avg_rating
            FROM (
                SELECT branch, category,
                       AVG(rating) avg_rating,
                       RANK() OVER(PARTITION BY branch ORDER BY AVG(rating) DESC) r
                FROM walmart
                GROUP BY branch, category
            ) t WHERE r = 1
            """,

        "Busiest Day per Branch":
            """
            SELECT branch, day_name, no_transactions
            FROM (
                SELECT branch,
                       DAYNAME(STR_TO_DATE(date,'%d/%m/%Y')) day_name,
                       COUNT(*) no_transactions,
                       RANK() OVER(PARTITION BY branch ORDER BY COUNT(*) DESC) r
                FROM walmart
                GROUP BY branch, day_name
            ) t WHERE r = 1
            """,

        "Total Quantity by Payment Method":
            """
            SELECT payment_method, SUM(quantity) total_quantity
            FROM walmart
            GROUP BY payment_method
            """,

        "City Rating Analysis":
            """
            SELECT city, category,
                   MIN(rating), MAX(rating), AVG(rating)
            FROM walmart
            GROUP BY city, category
            """,

        "Profit by Category":
            """
            SELECT category,
                   SUM(unit_price * quantity * profit_margin) profit
            FROM walmart
            GROUP BY category
            """,

        "Preferred Payment Method per Branch":
            """
            WITH cte AS (
                SELECT branch, payment_method,
                       COUNT(*) total_trans,
                       RANK() OVER(PARTITION BY branch ORDER BY COUNT(*) DESC) r
                FROM walmart
                GROUP BY branch, payment_method
            )
            SELECT branch, payment_method
            FROM cte
            WHERE r = 1
            """,

        "Shift Analysis":
            """
            SELECT branch,
                   CASE
                       WHEN HOUR(TIME(time)) < 12 THEN 'Morning'
                       WHEN HOUR(TIME(time)) < 17 THEN 'Afternoon'
                       ELSE 'Evening'
                   END shift,
                   COUNT(*) transactions
            FROM walmart
            GROUP BY branch, shift
            """,

        "Revenue Drop Analysis (2022 vs 2023)":
            """
            WITH r1 AS (
                SELECT branch, SUM(total) rev
                FROM walmart
                WHERE YEAR(STR_TO_DATE(date,'%d/%m/%Y')) = 2022
                GROUP BY branch
            ),
            r2 AS (
                SELECT branch, SUM(total) rev
                FROM walmart
                WHERE YEAR(STR_TO_DATE(date,'%d/%m/%Y')) = 2023
                GROUP BY branch
            )
            SELECT r1.branch,
                   r1.rev last_year,
                   r2.rev current_year,
                   ROUND(((r1.rev - r2.rev)/r1.rev)*100,2) drop_ratio
            FROM r1 JOIN r2 ON r1.branch = r2.branch
            WHERE r1.rev > r2.rev
            ORDER BY drop_ratio DESC
            LIMIT 5
            """,

        
    }

    choice = st.selectbox("Select Query", list(queries.keys()))
    df = pd.read_sql(queries[choice], conn)
    st.dataframe(df, use_container_width=True)

# =====================================================
# PROJECT SUMMARY PAGE
# =====================================================
elif page == "Project Summary":

    st.title("📌 Project Summary & Insights")

    st.markdown("---")

    st.info("""
This dashboard was built to analyze Walmart sales data and convert raw transactional records into meaningful business insights.

The goal of this project is to understand:
- Customer purchasing behavior
- Revenue and profit distribution
- Branch and city performance
- Payment method preferences
- Sales patterns across time (Morning, Afternoon, Evening)

Using SQL queries, we extracted business-level insights such as top-performing categories, busiest days, and revenue trends.

With Streamlit, we visualized these insights in an interactive dashboard with filters for city, payment method, and year, making the analysis dynamic and user-friendly.

Overall, this project demonstrates how raw retail data can be transformed into actionable business intelligence for better decision-making.
""")

    st.success("📊 This project simulates real-world retail analytics similar to Power BI dashboards used in industry.")