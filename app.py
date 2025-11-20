# app.py
"""
Simple Streamlit EDA app for sales dataset.
Place sales_dataset.xlsx in the same folder, or upload it in the UI.
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import plotly.express as px

st.set_page_config(page_title="Sales EDA", layout="wide")
st.title("📈 Sales EDA — Simple View")

# Try an obvious local path first (useful when running on same machine)
DEFAULT_PATH = "/mnt/data/sales_dataset.xlsx"

def load_data_from_filelike(f):
    name = getattr(f, "name", "")
    try:
        if str(name).lower().endswith(".xlsx") or str(name).lower().endswith(".xls"):
            return pd.read_excel(f)
        else:
            return pd.read_csv(f)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return None

# Load data (local path) or ask user to upload
df = None
if os.path.exists(DEFAULT_PATH):
    try:
        df = pd.read_excel(DEFAULT_PATH)
    except Exception:
        try:
            df = pd.read_csv(DEFAULT_PATH)
        except Exception as e:
            st.warning(f"Found file at {DEFAULT_PATH} but couldn't read it: {e}")
            df = None

if df is None:
    uploaded = st.file_uploader("Upload sales_dataset.xlsx (or CSV)", type=["xlsx", "csv"])
    if uploaded is None:
        st.info("App needs a dataset to run. Place sales_dataset.xlsx at /mnt/data/ or upload it here.")
        st.stop()
    df = load_data_from_filelike(uploaded)
    if df is None:
        st.stop()

# Normalize column names
df.columns = [c.strip() for c in df.columns]

# Recommended columns (if they exist the app will use them)
expected = ["Date", "Product", "Profit", "Customer", "Quantity", "Sales", "Category"]
present_expected = [c for c in expected if c in df.columns]

st.sidebar.header("Controls")
# Date filter if Date column exists
if "Date" in df.columns:
    try:
        df["Date"] = pd.to_datetime(df["Date"])
        min_d = df["Date"].min().date()
        max_d = df["Date"].max().date()
        date_range = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    except Exception:
        date_range = None
else:
    date_range = None

# Product filter
products = df["Product"].unique().tolist() if "Product" in df.columns else []
product_sel = st.sidebar.multiselect("Products (filter)", options=products, default=products[:5])

# Histogram bins
bins = st.sidebar.slider("Histogram bins (Sales)", 5, 100, 20)

# Apply filters
df_view = df.copy()
if date_range and len(date_range) == 2 and "Date" in df_view.columns:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= start) & (df_view["Date"] <= end)]
if product_sel and "Product" in df_view.columns:
    df_view = df_view[df_view["Product"].isin(product_sel)]

# Top-line metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
c2.metric("Total Sales", f"{df_view['Sales'].sum():,.2f}" if "Sales" in df_view.columns else "n/a")
c3.metric("Total Profit", f"{df_view['Profit'].sum():,.2f}" if "Profit" in df_view.columns else "n/a")
c4.metric("Total Quantity", f"{int(df_view['Quantity'].sum())}" if "Quantity" in df_view.columns else "n/a")

st.markdown("---")

# 1) Line chart: Quantity over time (if available)
if "Date" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("Trend — Quantity over Time")
    fig = px.line(df_view.sort_values("Date"), x="Date", y="Quantity", markers=True, title="Quantity over time")
    st.plotly_chart(fig, width="stretch")

# 2) Bar: Profit by Product
if "Product" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("Profit by Product")
    prod = df_view.groupby("Product", dropna=False)["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
    fig = px.bar(prod, x="Product", y="Profit", title="Profit by Product")
    st.plotly_chart(fig, width="stretch")

# 3) Scatter: Customer vs Quantity
if "Customer" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("Customers vs Quantity")
    fig = px.scatter(df_view, x="Customer", y="Quantity", title="Customer vs Quantity")
    st.plotly_chart(fig, width="stretch")

# 4) Histogram: Sales
if "Sales" in df_view.columns:
    st.subheader("Sales Distribution")
    fig = px.histogram(df_view, x="Sales", nbins=bins, title="Sales distribution", marginal="box")
    st.plotly_chart(fig, width="stretch")

# 5) Box plot: Quantity
if "Quantity" in df_view.columns:
    st.subheader("Quantity Boxplot")
    fig = px.box(df_view, y="Quantity", title="Quantity boxplot")
    st.plotly_chart(fig, width="stretch")

# 6) Pie: Category distribution
if "Category" in df_view.columns:
    st.subheader("Category distribution")
    cat = df_view["Category"].value_counts().reset_index()
    cat.columns = ["Category", "Count"]
    fig = px.pie(cat, values="Count", names="Category", title="Category distribution")
    st.plotly_chart(fig, width="stretch")

# Correlation heatmap for numeric columns
num_cols = df_view.select_dtypes(include=[np.number]).columns.tolist()
if len(num_cols) >= 2:
    st.subheader("Correlation matrix (numeric features)")
    corr = df_view[num_cols].corr()
    fig = px.imshow(corr, text_auto=True, title="Correlation matrix")
    st.plotly_chart(fig, width="stretch")

st.markdown("---")
st.subheader("Data preview")
st.dataframe(df_view.head(50))

# Download filtered CSV
buf = io.StringIO()
df_view.to_csv(buf, index=False)
st.download_button("Download filtered CSV", data=buf.getvalue().encode("utf-8"),
                   file_name="sales_dataset_filtered.csv", mime="text/csv")
