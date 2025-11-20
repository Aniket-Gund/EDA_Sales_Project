# app.py
"""
FINAL Streamlit EDA Dashboard (Sales)
- Loads dataset ONLY from /mnt/data/sales_dataset.xlsx
- Added Sales vs Profit chart WITH trendline (OLS)
- No upload section
- No data preview
- Adds statistical summary + insights summary
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Sales EDA", layout="wide")
st.title("📈 Sales EDA Dashboard by Aniket Gund")

# ----------------------------
# LOAD DATASET (NO UPLOADS)
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

# Clean column names
df.columns = [c.strip() for c in df.columns]

# Convert Date column
if "Date" in df.columns:
    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except:
        pass

# ---------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------
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

# histogram bins
bins = st.sidebar.slider("Histogram bins (Sales)", 5, 60, 20)

# ---------------------------------------
# APPLY FILTERS
# ---------------------------------------
df_view = df.copy()

if date_range and len(date_range) == 2 and "Date" in df.columns:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= start) & (df_view["Date"] <= end)]

if selected_products and "Product" in df_view.columns:
    df_view = df_view[df_view["Product"].isin(selected_products)]

# ---------------------------------------
# METRICS
# ---------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
c2.metric("Total Sales", f"{df_view['Sales'].sum():,.2f}" if "Sales" in df_view.columns else "n/a")
c3.metric("Total Profit", f"{df_view['Profit'].sum():,.2f}" if "Profit" in df_view.columns else "n/a")
c4.metric("Total Quantity", f"{int(df_view['Quantity'].sum())}" if "Quantity" in df_view.columns else "n/a")

st.markdown("---")

# ---------------------------------------
# CHART 1 — Quantity Over Time
# ---------------------------------------
if "Date" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("📅 Quantity Over Time")
    fig = px.line(df_view.sort_values("Date"), x="Date", y="Quantity", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# CHART 2 — Profit by Product
# ---------------------------------------
if "Product" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("💰 Profit by Product")
    grouped = df_view.groupby("Product")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
    fig = px.bar(grouped, x="Product", y="Profit")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# CHART 3 — Sales vs Profit (WITH TRENDLINE)
# ---------------------------------------
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("📊 Sales vs Profit (OLS Trendline)")
    fig = px.scatter(
        df_view,
        x="Sales",
        y="Profit",
        trendline="ols",
        title="Sales vs Profit Relationship",
        color="Product" if "Product" in df_view.columns else None
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# CHART 4 — Customers vs Quantity
# ---------------------------------------
if "Customer" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("👥 Customers vs Quantity")
    fig = px.scatter(df_view, x="Customer", y="Quantity")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# CHART 5 — Sales Distribution
# ---------------------------------------
if "Sales" in df_view.columns:
    st.subheader("📦 Sales Distribution")
    fig = px.histogram(df_view, x="Sales", nbins=bins)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# CHART 6 — Quantity Boxplot
# ---------------------------------------
if "Quantity" in df_view.columns:
    st.subheader("📦 Quantity Boxplot")
    fig = px.box(df_view, y="Quantity")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# CHART 7 — Category Pie Chart
# ---------------------------------------
if "Category" in df_view.columns:
    st.subheader("🍰 Category Distribution")
    counts = df_view["Category"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    fig = px.pie(counts, names="Category", values="Count")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# CHART 8 — Correlation Heatmap
# ---------------------------------------
num_cols = df_view.select_dtypes(include=[np.number]).columns
if len(num_cols) >= 2:
    st.subheader("🔗 Correlation Heatmap")
    corr = df_view[num_cols].corr()
    fig = px.imshow(corr, text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# STATISTICAL SUMMARY
# ---------------------------------------
st.markdown("---")
st.subheader("📊 Statistical Summary")
summary = df_view.describe().T
st.dataframe(summary)

# ---------------------------------------
# AUTO SUMMARY SECTION
# ---------------------------------------
st.subheader("📝 Insights Summary (Auto-Generated)")

insights = []

# Sales–Profit correlation
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    corr_val = df_view["Sales"].corr(df_view["Profit"])
    if corr_val > 0.4:
        insights.append("Sales and Profit have a strong positive relationship.")
    elif corr_val < -0.3:
        insights.append("Sales and Profit have a negative relationship.")
    else:
        insights.append("Sales and Profit have no strong relationship.")

# Category insight
if "Category" in df_view.columns:
    top_cat = df_view["Category"].value_counts().idxmax()
    insights.append(f"The most common category is **{top_cat}**.")

# Quantity variation
if "Quantity" in df_view.columns:
    insights.append("Quantity varies significantly across the selected period.")

# Sales skewness
if "Sales" in df_view.columns:
    skew = df_view["Sales"].skew()
    if skew > 1:
        insights.append("Sales distribution is right-skewed.")
    else:
        insights.append("Sales distribution is fairly balanced.")

for i in insights:
    st.write("✔", i)
