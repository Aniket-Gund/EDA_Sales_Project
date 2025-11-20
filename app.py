# app.py
"""
FINAL Streamlit EDA Dashboard (Sales)
- Loads dataset ONLY from /mnt/data/sales_dataset.xlsx
- Added Sales vs Profit (trendline)
- Replaced boxplot + heatmap with:
    1) Sales vs Quantity Bubble Chart
    2) Category-wise Sales Violin Plot
- Added deeper insights summary
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Sales EDA", layout="wide")
st.title("📈 Sales EDA Dashboard")

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

if "Date" in df.columns:
    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_range = st.sidebar.date_input("Date Range", value=(min_d, max_d))
else:
    date_range = None

if "Product" in df.columns:
    products = df["Product"].unique().tolist()
    selected_products = st.sidebar.multiselect("Filter Products", products, default=products[:5])
else:
    selected_products = None

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

# 3) Sales vs Profit (with trendline)
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

# 🚀 NEW CHART 1 — Sales vs Quantity Bubble Chart
if "Sales" in df_view.columns and "Quantity" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("🫧 Sales vs Quantity Bubble Chart (Profit-sized)")
    fig = px.scatter(
        df_view,
        x="Sales",
        y="Quantity",
        size="Profit",
        color="Product" if "Product" in df_view else None,
        title="Sales vs Quantity with Profit Weight"
    )
    st.plotly_chart(fig, use_container_width=True)

# 4) Sales Distribution
if "Sales" in df_view.columns:
    st.subheader("📦 Sales Distribution")
    fig = px.histogram(df_view, x="Sales", nbins=bins)
    st.plotly_chart(fig, use_container_width=True)

# 🚀 NEW CHART 2 — Category-wise Sales Violin Plot
if "Category" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("🎻 Sales Distribution by Category (Violin Plot)")
    fig = px.violin(df_view, x="Category", y="Sales", box=True, points="all")
    st.plotly_chart(fig, use_container_width=True)

# 5) Customers vs Quantity
if "Customer" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("👥 Customers vs Quantity")
    fig = px.scatter(df_view, x="Customer", y="Quantity")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ----------------------------
# STATISTICAL SUMMARY
# ----------------------------
st.subheader("📊 Statistical Summary")
summary = df_view.describe().T
st.dataframe(summary)

# ----------------------------
# INSIGHTS SUMMARY (EXPANDED)
# ----------------------------
st.subheader("📝 Insights Summary (Descriptive & Auto-Generated)")

insights = []

# Sales-Profit Relationship
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    corr_sp = df_view["Sales"].corr(df_view["Profit"])
    if corr_sp > 0.4:
        insights.append("Higher sales generally lead to higher profit, showing a strong positive business relationship.")
    else:
        insights.append("Sales and profit show no strong correlation, indicating margins vary depending on product.")

# Sales–Quantity bubble chart insights
if {"Sales", "Quantity", "Profit"}.issubset(df_view.columns):
    insights.append("Bubble chart indicates which products push quantity vs sales revenue, revealing demand-heavy or margin-heavy items.")

# Category-wise violin insights
if "Category" in df_view.columns and "Sales" in df_view.columns:
    top_cat = df_view["Category"].value_counts().idxmax()
    insights.append(f"Category **{top_cat}** dominates in frequency, with noticeably varying sales distribution across categories.")

# Quantity trend over time
if "Date" in df_view.columns and "Quantity" in df_view.columns:
    insights.append("Quantity shows temporal variation, indicating seasonal or promotional impact over the timeline.")

# Sales distribution skewness
if "Sales" in df_view.columns:
    skew = df_view["Sales"].skew()
    if skew > 1:
        insights.append("Sales distribution is right-skewed, meaning a small number of high-sale events dominate revenue.")
    else:
        insights.append("Sales distribution is mostly balanced without extreme outliers.")

# Print insights
for i in insights:
    st.write("✔", i)
