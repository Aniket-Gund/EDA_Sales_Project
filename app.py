# app.py
"""
Streamlit EDA Dashboard — Final enhanced version

Features:
- Loads dataset from /mnt/data/sales_dataset.xlsx (NO uploader)
- Charts:
    * Quantity over time
    * Profit by product (bar)
    * Sales vs Profit (scatter with OLS trendline)
    * Treemap (Category -> Product) showing Sales, Profit, Profit Margin, colored by margin
    * Profit margin distribution (histogram)
    * Top 20 customers by Sales (bar)
    * Sales distribution (histogram)
    * Category pie chart
- Statistical summary (df.describe)
- Auto-generated insights (expanded)
- Download original dataset button
- Export PNG and PDF report (treemap snapshot + brief text summary) — in-memory, no temp files
Notes: PDF/PNG export requires kaleido and reportlab in environment. If export fails, app will show an error and a hint to install dependencies.
"""

import io
import os
import math
import textwrap
import tempfile
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

# Optional: reportlab for PDF creation
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Sales EDA (Enhanced)", layout="wide")
st.title("📈 Sales EDA Dashboard by Aniket Gund")

# -------------------------
# Load dataset (no uploader)
# -------------------------
DATA_PATH = "sales_dataset.xlsx"

if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at: {DATA_PATH}\nPlace the Excel file at that path and reload the app.")
    st.stop()

try:
    df = pd.read_excel(DATA_PATH)
except Exception as e:
    st.error(f"Error reading dataset: {e}")
    st.stop()

# Normalize column names
df.columns = [c.strip() for c in df.columns]

# Allow user to download original dataset
st.subheader("📁 Download Original Dataset")
try:
    with open(DATA_PATH, "rb") as f:
        st.download_button(
            label="⬇️ Download sales_dataset.xlsx",
            data=f,
            file_name=os.path.basename(DATA_PATH),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
except Exception as e:
    st.warning(f"Could not create download button: {e}")

# -------------------------
# Preprocessing
# -------------------------
if "Date" in df.columns:
    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except Exception:
        # leave as is if conversion fails
        pass

# Sidebar filters
st.sidebar.header("Filters")

if "Date" in df.columns and np.issubdtype(df["Date"].dtype, np.datetime64):
    min_d = df["Date"].min().date()
    max_d = df["Date"].max().date()
    date_range = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
else:
    date_range = None

if "Product" in df.columns:
    product_options = sorted(df["Product"].dropna().unique().tolist())
    selected_products = st.sidebar.multiselect("Products (filter)", options=product_options, default=product_options[:6])
else:
    selected_products = None

bins = st.sidebar.slider("Histogram bins (Sales)", min_value=5, max_value=100, value=20)
show_profit_margin = st.sidebar.checkbox("Show profit margin histogram", value=True)

# Apply filters
df_view = df.copy()
if date_range and len(date_range) == 2 and "Date" in df_view.columns:
    s, e = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= s) & (df_view["Date"] <= e)]

if selected_products and "Product" in df_view.columns:
    df_view = df_view[df_view["Product"].isin(selected_products)]

# Defensive: ensure numeric columns exist for aggregations
numeric_cols = df_view.select_dtypes(include=[np.number]).columns.tolist()

# -------------------------
# Top metrics
# -------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
total_sales = df_view["Sales"].sum() if "Sales" in df_view.columns else None
total_profit = df_view["Profit"].sum() if "Profit" in df_view.columns else None
total_qty = int(df_view["Quantity"].sum()) if "Quantity" in df_view.columns else None
c2.metric("Total Sales", f"{total_sales:,.2f}" if total_sales is not None else "n/a")
c3.metric("Total Profit", f"{total_profit:,.2f}" if total_profit is not None else "n/a")
c4.metric("Total Quantity", f"{total_qty:,}" if total_qty is not None else "n/a")

st.markdown("---")

# -------------------------
# Charts
# -------------------------

# 1) Quantity over time
if "Date" in df_view.columns and "Quantity" in df_view.columns:
    st.subheader("📅 Quantity Over Time")
    fig_q = px.line(df_view.sort_values("Date"), x="Date", y="Quantity", markers=True, title="Quantity over time")
    st.plotly_chart(fig_q, use_container_width=True)

# 2) Profit by product
if "Product" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("💰 Profit by Product")
    prod_profit = df_view.groupby("Product", dropna=False)["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
    fig_profit_prod = px.bar(prod_profit, x="Product", y="Profit", title="Total Profit by Product")
    st.plotly_chart(fig_profit_prod, use_container_width=True)

# 3) Sales vs Profit (trendline)
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("📊 Sales vs Profit (OLS Trendline)")
    # Keep color by product if available
    color_arg = "Product" if "Product" in df_view.columns else None
    try:
        fig_sp = px.scatter(df_view, x="Sales", y="Profit", trendline="ols", color=color_arg, title="Sales vs Profit")
    except Exception:
        # fallback: no trendline (if statsmodels missing)
        fig_sp = px.scatter(df_view, x="Sales", y="Profit", color=color_arg, title="Sales vs Profit")
    st.plotly_chart(fig_sp, use_container_width=True)

# -------------------------
# OPTION: Treemap (aggregated)
# -------------------------
if "Category" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("🗂️ Advanced Treemap — Sales, Profit & Margin")

    # Aggregate at Category/Product level to ensure values align with treemap nodes
    if "Product" in df_view.columns and "Profit" in df_view.columns:
        agg_cols = ["Category", "Product"]
        df_agg = (
            df_view.groupby(agg_cols, dropna=False)
            .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
            .reset_index()
        )
    elif "Product" in df_view.columns:
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

    # Compute margin safely
    df_agg["Profit_Margin"] = np.where(df_agg["Sales"] != 0, df_agg["Profit"] / df_agg["Sales"], 0.0)

    path = ["Category", "Product"] if "Product" in df_agg.columns else ["Category"]
    fig_treemap = px.treemap(
        df_agg,
        path=path,
        values="Sales",
        color="Profit_Margin",
        color_continuous_scale="RdYlGn",
        title="Sales contribution by Category and Product (colored by profit margin)",
    )

    # Build customdata aligned to df_agg rows
    cd = np.stack((df_agg["Profit"].fillna(0).to_numpy(), df_agg["Profit_Margin"].to_numpy()), axis=-1)
    fig_treemap.update_traces(
        customdata=cd,
        texttemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>Profit: ₹%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.1%}<br>Share: %{percentParent:.1%}",
        hovertemplate="<b>%{label}</b><br>Sales: ₹%{value:,.0f}<br>Profit: ₹%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.2%}<br>Share: %{percentParent:.2%}<extra></extra>",
        textposition="middle center",
    )
    st.plotly_chart(fig_treemap, use_container_width=True)
else:
    fig_treemap = None

# -------------------------
# Profit margin distribution
# -------------------------
if show_profit_margin and "Profit" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("📉 Profit Margin Distribution")
    # avoid division by zero
    df_view = df_view.assign(Profit_Margin=np.where(df_view["Sales"] == 0, 0.0, df_view["Profit"] / df_view["Sales"]))
    fig_margin = px.histogram(df_view, x="Profit_Margin", nbins=40, title="Profit Margin Distribution")
    st.plotly_chart(fig_margin, use_container_width=True)

# -------------------------
# Top customers by sales
# -------------------------
if "Customer" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("🏆 Top Customers by Sales (Top 20)")
    top_customers = (
        df_view.groupby("Customer", dropna=False)["Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )
    fig_top_cust = px.bar(top_customers, x="Customer", y="Sales", title="Top 20 Customers by Sales")
    st.plotly_chart(fig_top_cust, use_container_width=True)

# -------------------------
# Sales distribution + category pie
# -------------------------
if "Sales" in df_view.columns:
    st.subheader("📦 Sales Distribution")
    fig_sales_hist = px.histogram(df_view, x="Sales", nbins=bins, title="Sales distribution")
    st.plotly_chart(fig_sales_hist, use_container_width=True)

if "Category" in df_view.columns:
    st.subheader("🍰 Category Distribution")
    cat_counts = df_view["Category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig_cat_pie = px.pie(cat_counts, values="Count", names="Category", title="Category Distribution")
    st.plotly_chart(fig_cat_pie, use_container_width=True)

# -------------------------
# Statistical summary
# -------------------------
st.markdown("---")
st.subheader("📊 Statistical Summary")
summary = df_view.describe().T
st.dataframe(summary)

# -------------------------
# Insights (descriptive)
# -------------------------
st.subheader("📝 Insights Summary:")
insights = []

# Sales-Profit correlation
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    corr_sp = df_view["Sales"].corr(df_view["Profit"])
    if corr_sp > 0.4:
        insights.append("Sales and Profit show a strong positive relationship — higher sales generally produce higher profit.")
    elif corr_sp < -0.3:
        insights.append("Sales and Profit are negatively correlated — possibly due to discounts, returns, or low-margin items.")
    else:
        insights.append("Sales and Profit show a weak correlation; margins differ by product/category.")

# Treemap insight
if "Category" in df_view.columns:
    top_cat = df_view["Category"].value_counts().idxmax()
    insights.append(f"Category **{top_cat}** is the most frequent and contributes substantially to total sales.")

# Profit margin skewness
if "Profit" in df_view.columns and "Sales" in df_view.columns:
    df_view["Profit_Margin"] = np.where(df_view["Sales"] == 0, 0.0, df_view["Profit"] / df_view["Sales"])
    skew = df_view["Profit_Margin"].skew()
    if skew > 1:
        insights.append("Profit margins are right-skewed — a few transactions/products have very high margins.")
    else:
        insights.append("Profit margins are relatively balanced across transactions.")

# Top customers
if "Customer" in df_view.columns and "Sales" in df_view.columns:
    top_customer = df_view.groupby("Customer")["Sales"].sum().idxmax()
    insights.append(f"Top customer is **{top_customer}**, generating the highest revenue in the selected period.")

# Quantity seasonality
if "Quantity" in df_view.columns and "Date" in df_view.columns:
    insights.append("Quantity shows time-based variation; consider investigating seasonality or promotions.")

for it in insights:
    st.write("✔", it)

# -------------------------
# Export PNG / PDF Report
# -------------------------
st.markdown("---")
st.subheader("📤 Export Report (PNG / PDF)")

def fig_to_png_bytes(fig_obj, width=1200, height=800, scale=1):
    """
    Convert a Plotly figure to PNG bytes using kaleido via plotly.io.to_image/pio.to_image.
    Returns bytes.
    """
    try:
        img_bytes = pio.to_image(fig_obj, format="png", width=width, height=height, scale=scale)
        return img_bytes
    except Exception as e:
        raise RuntimeError(f"Failed to render figure to PNG: {e}")

def make_pdf_bytes(title_text, fig_png_bytes):
    """
    Create a simple PDF in-memory with title text and the PNG image embedded.
    Returns PDF bytes.
    """
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(595, 842))  # A4-ish in points
        # Title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 800, title_text)
        # Date
        c.setFont("Helvetica", 9)
        c.drawString(40, 785, f"Generated: {datetime.utcnow().isoformat()} UTC")
        # Insert image (use ImageReader on PNG bytes)
        img_reader = ImageReader(io.BytesIO(fig_png_bytes))
        # place image at x=40 y=350 with width ~515
        c.drawImage(img_reader, 40, 350, width=515, preserveAspectRatio=True, mask='auto')
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        raise RuntimeError(f"Failed to create PDF: {e}")

# Choose a representative figure for export: prefer treemap, otherwise sales vs profit, otherwise sales hist
export_fig = None
if 'fig_treemap' in locals() and fig_treemap is not None:
    export_fig = fig_treemap
elif 'fig_sp' in locals():
    export_fig = fig_sp
elif 'fig_sales_hist' in locals():
    export_fig = fig_sales_hist

if export_fig is None:
    st.info("No figure available for export.")
else:
    col_png, col_pdf = st.columns(2)
    with col_png:
        if st.button("⬇️ Download Dashboard PNG"):
            try:
                png_bytes = fig_to_png_bytes(export_fig)
                st.download_button("Download PNG", data=png_bytes, file_name="dashboard_snapshot.png", mime="image/png")
            except Exception as e:
                st.error(f"PNG export failed: {e}. Ensure 'kaleido' is installed (add to requirements).")

    with col_pdf:
        if st.button("⬇️ Download Dashboard PDF"):
            try:
                png_bytes = fig_to_png_bytes(export_fig)
                pdf_bytes = make_pdf_bytes("Sales EDA — Snapshot Report", png_bytes)
                st.download_button("Download PDF", data=pdf_bytes, file_name="Sales_Report.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"PDF export failed: {e}. Ensure 'kaleido' and 'reportlab' are installed (add to requirements).")

st.markdown("---")
st.caption("Tip: For best export results install 'kaleido' and 'reportlab' in the environment.")
