# app.py
"""
Sales EDA — FINAL HTML Export Version (treemap & HTML export fixed)

Features:
- Loads /mnt/data/sales_dataset.xlsx (no uploader)
- Renders charts with Plotly
- Provides:
    * Download dataset
    * Download HTML snapshot (all charts + summary)
- No PNG/PDF export
- Enhanced treemap preserved in UI and exported HTML (values + colors)
"""

import os
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Sales EDA (HTML export)", layout="wide")
st.title("📈 Sales EDA Dashboard by Aniket Gund")

# -------------------------
# Load dataset
# -------------------------
DATA_PATH = "sales_dataset.xlsx"
if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at: {DATA_PATH}")
    st.stop()

df = pd.read_excel(DATA_PATH)
df.columns = [c.strip() for c in df.columns]

if "Date" in df.columns:
    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except:
        pass

# -------------------------
# Download dataset
# -------------------------
st.subheader("📁 Download Original Dataset")
with open(DATA_PATH, "rb") as f:
    st.download_button(
        "⬇️ Download sales_dataset.xlsx",
        data=f,
        file_name="sales_dataset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")

# -------------------------
# Sidebar filters
# -------------------------
st.sidebar.header("Filters")

if "Date" in df.columns:
    min_d = df["Date"].min().date()
    max_d = df["Date"].max().date()
    date_range = st.sidebar.date_input("Date Range", (min_d, max_d))
else:
    date_range = None

if "Product" in df.columns:
    products = sorted(df["Product"].dropna().unique())
    selected_products = st.sidebar.multiselect("Products", products, default=products[:6])
else:
    selected_products = None

bins = st.sidebar.slider("Histogram bins", 5, 60, 20)
show_profit_margin = st.sidebar.checkbox("Show profit margin chart", True)

# Apply filters
df_view = df.copy()

if date_range and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= start) & (df_view["Date"] <= end)]

if selected_products:
    df_view = df_view[df_view["Product"].isin(selected_products)]

# -------------------------
# KPIs
# -------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
c2.metric("Total Sales", f"{df_view['Sales'].sum():,.2f}" if "Sales" in df_view.columns else "n/a")
c3.metric("Total Profit", f"{df_view['Profit'].sum():,.2f}" if "Profit" in df_view.columns else "n/a")
c4.metric("Total Quantity", f"{int(df_view['Quantity'].sum())}" if "Quantity" in df_view.columns else "n/a")

st.markdown("---")

# -------------------------
# Charts
# -------------------------
fig_q = fig_profit_prod = fig_sp = fig_treemap = fig_margin = fig_top_cust = fig_sales_hist = fig_cat_pie = None

# Quantity over time
if "Date" in df_view and "Quantity" in df_view:
    st.subheader("📅 Quantity Over Time")
    fig_q = px.line(df_view.sort_values("Date"), x="Date", y="Quantity", markers=True, template="plotly_white")
    fig_q.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_q, use_container_width=True)

# Profit by product
if "Product" in df_view and "Profit" in df_view:
    st.subheader("💰 Profit by Product")
    prod_profit = df_view.groupby("Product")["Profit"].sum().reset_index()
    fig_profit_prod = px.bar(prod_profit, x="Product", y="Profit", template="plotly_white")
    fig_profit_prod.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_profit_prod, use_container_width=True)

# Sales vs Profit
if "Sales" in df_view and "Profit" in df_view:
    st.subheader("📊 Sales vs Profit (Trendline)")
    try:
        fig_sp = px.scatter(df_view, x="Sales", y="Profit", color="Product" if "Product" in df_view else None, trendline="ols", template="plotly_white")
    except:
        fig_sp = px.scatter(df_view, x="Sales", y="Profit", color="Product" if "Product" in df_view else None, template="plotly_white")
    fig_sp.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_sp, use_container_width=True)

# -------------------------
# ENHANCED TREEMAP (Category -> Product) — super treemap with values & colors
# -------------------------
if "Category" in df_view and "Sales" in df_view:
    st.subheader("🗂️ Advanced Treemap — Sales, Profit & Margin (enhanced)")

    # Aggregate to Category/Product level
    if "Product" in df_view and "Profit" in df_view:
        agg_cols = ["Category", "Product"]
        df_agg = (
            df_view.groupby(agg_cols, dropna=False)
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
        )
    elif "Product" in df_view:
        agg_cols = ["Category", "Product"]
        df_agg = (
            df_view.groupby(agg_cols, dropna=False)
            .agg(Sales=("Sales", "sum"))
            .reset_index()
        )
        df_agg["Profit"] = 0.0
    else:
        agg_cols = ["Category"]
        df_agg = (
            df_view.groupby(agg_cols, dropna=False)
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum") if "Profit" in df_view.columns else ("Sales", "sum"))
            .reset_index()
        )
        if "Profit" not in df_agg.columns:
            df_agg["Profit"] = 0.0

    # Compute margin safely (avoid div by zero)
    df_agg["Profit_Margin"] = np.where(df_agg["Sales"] != 0, df_agg["Profit"] / df_agg["Sales"], 0.0)

    # Create treemap figure
    path = ["Category", "Product"] if "Product" in df_agg.columns else ["Category"]
    fig_treemap = px.treemap(
        df_agg,
        path=path,
        values="Sales",
        color="Profit_Margin",
        color_continuous_scale="RdYlGn",
        labels={"Profit_Margin": "Profit Margin"},
        title="Sales contribution by Category and Product (colored by profit margin)",
        template="plotly_white"
    )

    # customdata must match df_agg order to show Profit and Margin per node
    customdata = np.stack((df_agg["Profit"].fillna(0).to_numpy(), df_agg["Profit_Margin"].to_numpy()), axis=-1)

    # Update traces to show value, profit, margin and percent parent
    fig_treemap.update_traces(
        customdata=customdata,
        texttemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>Profit: ₹%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.1%}<br>Share: %{percentParent:.1%}",
        hovertemplate="<b>%{label}</b><br>Sales: ₹%{value:,.0f}<br>Profit: ₹%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.2%}<br>Share: %{percentParent:.2%}<extra></extra>",
        textposition="middle center",
    )

    # Layout tweaks to keep the same look in UI and exported HTML
    fig_treemap.update_layout(margin=dict(t=50, l=10, r=10, b=10), uniformtext=dict(minsize=10, mode="hide"))

    st.plotly_chart(fig_treemap, use_container_width=True)

# Profit margin histogram
if show_profit_margin and "Profit" in df_view and "Sales" in df_view:
    st.subheader("📉 Profit Margin Distribution")
    df_view["Profit_Margin"] = np.where(df_view["Sales"] == 0, 0.0, df_view["Profit"] / df_view["Sales"])
    fig_margin = px.histogram(df_view, x="Profit_Margin", nbins=40, template="plotly_white")
    fig_margin.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_margin, use_container_width=True)

# Top customers
if "Customer" in df_view:
    st.subheader("🏆 Top Customers by Sales")
    top_customers = (
        df_view.groupby("Customer")["Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )
    fig_top_cust = px.bar(top_customers, x="Customer", y="Sales", template="plotly_white")
    fig_top_cust.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_top_cust, use_container_width=True)

# Sales distribution
st.subheader("📦 Sales Distribution")
fig_sales_hist = px.histogram(df_view, x="Sales", nbins=bins, template="plotly_white")
fig_sales_hist.update_layout(margin=dict(t=40, b=20))
st.plotly_chart(fig_sales_hist, use_container_width=True)

# Category pie
if "Category" in df_view:
    st.subheader("🍰 Category Distribution")
    cat_counts = df_view["Category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig_cat_pie = px.pie(cat_counts, values="Count", names="Category")
    fig_cat_pie.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_cat_pie, use_container_width=True)

# -------------------------
# Statistical Summary 
# -------------------------
st.markdown("---")
st.subheader("📊 Statistical Summary")
summary = df_view.describe().T
st.dataframe(summary)

# -------------------------
# Insights Summary 
# -------------------------
st.subheader("📝 Insights Summary")
insights = []

if "Sales" in df_view and "Profit" in df_view:
    corr_val = df_view["Sales"].corr(df_view["Profit"])
    if corr_val > 0.4:
        insights.append("Sales and Profit show a strong positive relationship.")
    elif corr_val < -0.3:
        insights.append("Sales and Profit are negatively correlated.")
    else:
        insights.append("Sales and Profit have a weak/moderate correlation.")

if "Category" in df_view:
    try:
        top_cat = df_view["Category"].value_counts().idxmax()
        insights.append(f"Category '{top_cat}' contributes the most sales.")
    except Exception:
        pass

if "Product" in df_view and "Sales" in df_view:
    try:
        top_product = df_view.groupby("Product")["Sales"].sum().idxmax()
        insights.append(f"Highest-selling product: {top_product}")
    except Exception:
        pass

if "Customer" in df_view and "Sales" in df_view:
    try:
        top_customer = df_view.groupby("Customer")["Sales"].sum().idxmax()
        insights.append(f"Top customer: {top_customer}")
    except Exception:
        pass

for item in insights:
    st.write("✔", item)

# -------------------------
# HTML Export (ALL charts + summary)
# -------------------------
st.markdown("---")
st.subheader("📤 Download Interactive HTML Snapshot")

figures = [
    fig_q, fig_profit_prod, fig_sp, fig_treemap,
    fig_margin, fig_top_cust, fig_sales_hist, fig_cat_pie
]
figures = [f for f in figures if f is not None]

if st.button("⬇️ Download HTML"):
    html_blocks = []
    first = True
    for fig in figures:
        # include plotlyjs only once to preserve shared behavior & styles
        if first:
            html_blocks.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
            first = False
        else:
            html_blocks.append(fig.to_html(full_html=False, include_plotlyjs=False))

    # Build summary HTML (same insights shown in app)
    summary_html = "<section style='font-family:Arial,Helvetica,sans-serif;'><h2>Insights Summary</h2><ul>"
    for i in insights:
        summary_html += f"<li>{i}</li>"
    summary_html += "</ul></section>"

    final_html = (
        "<html><head><meta charset='utf-8'></head><body>"
        f"<div style='font-family:Arial,Helvetica,sans-serif;padding:16px;'><h1>Sales EDA Snapshot</h1><p>Generated: {datetime.utcnow().isoformat()}</p><hr></div>"
        + "".join(html_blocks)
        + "<div style='padding:16px;'>" + summary_html + "</div>"
        + "</body></html>"
    )

    st.download_button(
        "Download HTML file",
        data=final_html.encode("utf-8"),
        file_name="sales_eda_snapshot.html",
        mime="text/html"
    )
