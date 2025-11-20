# app.py
"""
Streamlit EDA Dashboard (Updated)
- No upload section
- Loads only from /mnt/data/sales_dataset.xlsx
- Added Sales vs Profit plot
- Removed data preview
- Added statistical summary instead
- Added short insights summary
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Sales EDA", layout="wide")
st.title("📈 Sales EDA Dashboard by Aniket Gund")

# ---------------------------------------
# LOAD DATASET (NO UPLOAD ALLOWED)
# ---------------------------------------
DATA_PATH = "sales_dataset.xlsx"

if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at: {DATA_PATH}")
    st.stop()

try:
    df = pd.read_excel(DATA_PATH)
except:
    st.error("Error reading the dataset. Ensure it is a valid Excel file.")
    st.stop()

# Clean column names
df.columns = [c.strip() for c in df.columns]

# Convert Date column if present
if "Date" in df.columns:
    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except:
        pass

# ---------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------
st.sidebar.header("Filters")

# Date filter
if "Date" in df.columns:
    min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
    date_range = st.sidebar.date_input("Date range", value=(min_date, max_date))
else:
    date_range = None

# Product filter
if "Product" in df.columns:
    products = df["Product"].unique().tolist()
    selected_products = st.sidebar.multiselect(
        "Filter Products", products, default=products[:5]
    )
else:
    selected_products = None

# Sales histogram bins
bins = st.sidebar.slider("Histogram bins (Sales)", 5, 60, 20)

# ---------------------------------------
# FILTER DATA
# ---------------------------------------
df_view = df.copy()

if date_range and len(date_range) == 2 and "Date" in df_view.columns:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= start) & (df_view["Date"] <= end)]

if selected_products and "Product" in df_view.columns:
    df_view = df_view[df_view["Product"].isin(selected_products)]

# ---------------------------------------
# TOP METRICS
# ---------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
c2.metric("Total Sales", f"{df_view['Sales'].sum():,.2f}" if "Sales" in df_view.columns else "n/a")
c3.metric("Total Profit", f"{df_view['Profit'].sum():,.2f}" if "Profit" in df_view.columns else "n/a")
c4.metric("Total Quantity", f"{int(df_view['Quantity'].sum())}" if "Quantity" in df_view.columns else "n/a")

st.markdown("---")

# ---------------------------------------
# CHARTS SECTION
# ---------------------------------------

# 1) Line chart (Quantity over time)
if "Date" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("📅 Quantity Over Time")
    fig = px.line(df_view.sort_values("Date"), x="Date", y="Quantity", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# 2) Bar chart (Profit by Product)
if "Product" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("💰 Profit by Product")
    grouped = df_view.groupby("Product")["Profit"].sum().reset_index()
    fig = px.bar(grouped, x="Product", y="Profit")
    st.plotly_chart(fig, use_container_width=True)

# ⭐ 3) NEW CHART: Sales vs Profit
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("📊 Sales vs Profit (Added Chart)")
    fig = px.scatter(df_view, x="Sales", y="Profit", trendline="ols",
                     title="Sales vs Profit Relationship", color="Product" if "Product" in df_view.columns else None)
    st.plotly_chart(fig, use_container_width=True)

# 4) Scatter (Customers vs Quantity)
if "Customer" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("👥 Customers vs Quantity")
    fig = px.scatter(df_view, x="Customer", y="Quantity")
    st.plotly_chart(fig, use_container_width=True)

# 5) Histogram (Sales)
if "Sales" in df_view.columns:
    st.subheader("📦 Sales Distribution")
    fig = px.histogram(df_view, x="Sales", nbins=bins)
    st.plotly_chart(fig, use_container_width=True)

# 6) Boxplot (Quantity)
if "Quantity" in df_view.columns:
    st.subheader("📦 Quantity Boxplot")
    fig = px.box(df_view, y="Quantity")
    st.plotly_chart(fig, use_container_width=True)

# 7) Pie Chart (Category)
if "Category" in df_view.columns:
    st.subheader("🍰 Category Distribution")
    counts = df_view["Category"].value_counts().reset_index()
    counts.columns = ["Category", "Count"]
    fig = px.pie(counts, names="Category", values="Count")
    st.plotly_chart(fig, use_container_width=True)

# 8) Correlation Heatmap
num_cols = df_view.select_dtypes(include=[np.number]).columns
if len(num_cols) >= 2:
    st.subheader("🔗 Correlation Heatmap")
    corr = df_view[num_cols].corr()
    fig = px.imshow(corr, text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# ✨ STATISTICAL SUMMARY
# ---------------------------------------
st.markdown("---")
st.subheader("📊 Statistical Summary")
summary_df = df_view.describe().T
st.dataframe(summary_df)

# ---------------------------------------
# ✨ AUTO SUMMARY SECTION
# ---------------------------------------
st.subheader("📝 Insights Summary (Auto-Generated)")

insights = []

# Insight 1: Sales-Profit Relation
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    corr_val = df_view["Sales"].corr(df_view["Profit"])
    if corr_val > 0.4:
        insights.append("Sales and Profit have a clear positive relationship.")
    elif corr_val < -0.3:
        insights.append("Sales and Profit are negatively related.")
    else:
        insights.append("No strong relationship between Sales and Profit.")

# Insight 2: Category distribution
if "Category" in df_view.columns:
    top_cat = df_view["Category"].value_counts().idxmax()
    insights.append(f"The most common category is **{top_cat}**.")

# Insight 3: Quantity trend
if "Quantity" in df_view.columns:
    insights.append("Quantity shows noticeable variation over time.")

# Insight 4: Sales skew
if "Sales" in df_view.columns:
    if df_view["Sales"].skew() > 1:
        insights.append("Sales distribution is right-skewed.")
    else:
        insights.append("Sales distribution is fairly balanced.")

for point in insights:
    st.write("✔", point)
