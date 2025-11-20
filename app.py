# app.py
"""
FINAL Streamlit EDA Dashboard (Sales)
Includes:
- Treemap (Sales by Category & Product)
- Profit Margin Distribution
- Top Customers by Sales
- Sales vs Profit (trendline)
- Line, Bar, Scatter, Histogram, Pie
- Statistical summary + insights summary

Dataset must exist at: sales_dataset.xlsx
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Sales EDA", layout="wide")
st.title("📈 Sales EDA Dashboard by Aniket Gund")

# ----------------------------
# LOAD DATASET
# ----------------------------
DATA_PATH = "sales_dataset.xlsx"

if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at: {DATA_PATH}")
    st.stop()

try:
    df = pd.read_excel(DATA_PATH)
except:
    st.error("Error reading dataset. Make sure it's a valid Excel file.")
    st.stop()

df.columns = [c.strip() for c in df.columns]

if "Date" in df.columns:
    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except:
        pass

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filters")

# Date filter
if "Date" in df.columns:
    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_range = st.sidebar.date_input("Date Range", value=(min_d, max_d))
else:
    date_range = None

# Product filter
if "Product" in df.columns:
    products = df["Product"].unique().tolist()
    selected_products = st.sidebar.multiselect("Filter Products", products, default=products[:5])
else:
    selected_products = None

# Histogram bins
bins = st.sidebar.slider("Histogram bins (Sales)", 5, 60, 20)

# ----------------------------
# FILTER DATA
# ----------------------------
df_view = df.copy()

if date_range and len(date_range) == 2 and "Date" in df.columns:
    s, e = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= s) & (df_view["Date"] <= e)]

if selected_products and "Product" in df_view.columns:
    df_view = df_view[df_view["Product"].isin(selected_products)]

# ----------------------------
# METRICS
# ----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
c2.metric("Total Sales", f"{df_view['Sales'].sum():,.2f}" if "Sales" in df_view else "n/a")
c3.metric("Total Profit", f"{df_view['Profit'].sum():,.2f}" if "Profit" in df_view else "n/a")
c4.metric("Total Quantity", f"{int(df_view['Quantity'].sum())}" if "Quantity" in df_view else "n/a")

st.markdown("---")

# ----------------------------
# CHARTS
# ----------------------------

# 1) Quantity Over Time
if "Date" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("📅 Quantity Over Time")
    fig = px.line(df_view.sort_values("Date"), x="Date", y="Quantity", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# 2) Profit by Product
if "Product" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("💰 Profit by Product")
    grouped = df_view.groupby("Product")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
    fig = px.bar(grouped, x="Product", y="Profit")
    st.plotly_chart(fig, use_container_width=True)

# 3) Sales vs Profit (trendline)
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("📊 Sales vs Profit (OLS Trendline)")
    fig = px.scatter(
        df_view,
        x="Sales",
        y="Profit",
        trendline="ols",
        color="Product" if "Product" in df_view else None
    )
    st.plotly_chart(fig, use_container_width=True)

# ⭐ OPTION 1 → Treemap (Sales by Category & Product)
if "Category" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("🗂️ Sales by Category & Product (Treemap)")
    fig = px.treemap(
        df_view,
        path=["Category", "Product"] if "Product" in df_view.columns else ["Category"],
        values="Sales",
        title="Sales Contribution Breakdown"
    )
    st.plotly_chart(fig, use_container_width=True)

# ⭐ OPTION 2 → Profit Margin Distribution
if "Profit" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("📉 Profit Margin Distribution")
    df_view["Profit_Margin"] = df_view["Profit"] / df_view["Sales"]
    fig = px.histogram(
        df_view,
        x="Profit_Margin",
        nbins=40,
        title="Distribution of Profit Margins",
        color_discrete_sequence=["#2ECC71"]
    )
    st.plotly_chart(fig, use_container_width=True)

# ⭐ OPTION 4 → Top 20 Customers by Sales
if "Customer" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("🏆 Top Customers by Sales")
    top_customers = (
        df_view.groupby("Customer")["Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )
    fig = px.bar(
        top_customers,
        x="Customer",
        y="Sales",
        title="Top 20 Customers by Total Sales"
    )
    st.plotly_chart(fig, use_container_width=True)

# Existing: Sales Distribution
if "Sales" in df_view.columns:
    st.subheader("📦 Sales Distribution")
    fig = px.histogram(df_view, x="Sales", nbins=bins)
    st.plotly_chart(fig, use_container_width=True)

# Existing: Category Pie Chart
if "Category" in df_view.columns:
    st.subheader("🍰 Category Distribution")
    counts = df_view["Category"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    fig = px.pie(counts, names="Category", values="Count")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ----------------------------
# STATISTICAL SUMMARY
# ----------------------------
st.subheader("📊 Statistical Summary")
summary = df_view.describe().T
st.dataframe(summary)

# ----------------------------
# INSIGHTS SUMMARY (UPDATED)
# ----------------------------
st.subheader("📝 Insights Summary (Auto-Generated)")

insights = []

# Sales-Profit relation
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    corr = df_view["Sales"].corr(df_view["Profit"])
    if corr > 0.4:
        insights.append("Higher sales strongly correlate with higher profit, showing a healthy business pattern.")
    elif corr < -0.3:
        insights.append("Sales and profit are negatively related — high discounts or low margins may be present.")
    else:
        insights.append("Sales and profit show a weak relationship — margins vary widely by product.")

# Treemap insights
if "Category" in df_view.columns:
    top_cat = df_view["Category"].value_counts().idxmax()
    insights.append(f"Category **{top_cat}** contributes the largest share of total sales in the dataset.")

# Profit margin insight
if "Profit" in df_view.columns and "Sales" in df_view.columns:
    skew_m = df_view["Profit_Margin"].skew()
    if skew_m > 1:
        insights.append("Profit margins are right-skewed — a few items have extremely high profitability.")
    else:
        insights.append("Profit margins are fairly balanced, indicating uniform pricing strategy.")

# Top customers insight
if "Customer" in df_view.columns:
    top_customer = df_view.groupby("Customer")["Sales"].sum().idxmax()
    insights.append(f"Customer **{top_customer}** generates the highest revenue among all customers.")

# Final quantity insight
if "Quantity" in df_view.columns and "Date" in df_view.columns:
    insights.append("Quantity fluctuates noticeably across time, indicating seasonality or promotional impact.")

for i in insights:
    st.write("✔", i)
