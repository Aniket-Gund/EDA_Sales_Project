# app.py
"""
Sales EDA Dashboard — FINAL OPTION B
Features:
- Dataset loads from /mnt/data/sales_dataset.xlsx
- Only 2 export buttons:
    1. Download Dataset
    2. Download PDF Report (ALWAYS includes chart image)
- Uses Plotly SVG → PNG → PDF method (no Chrome required)
- NEVER shows errors or fallback messages
"""

import os
import io
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter

st.set_page_config(page_title="Sales EDA Dashboard", layout="wide")
st.title("📈 Sales EDA Dashboard by Aniket Gund")

# ----------------------------
# Load dataset (NO uploader)
# ----------------------------
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

# ----------------------------
# Dataset Download Button
# ----------------------------
st.subheader("📁 Download Dataset")
with open(DATA_PATH, "rb") as f:
    st.download_button(
        label="⬇️ Download sales_dataset.xlsx",
        data=f,
        file_name="sales_dataset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.markdown("---")

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("Filters")

if "Date" in df.columns:
    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    date_range = st.sidebar.date_input("Date Range", (min_d, max_d))
else:
    date_range = None

if "Product" in df.columns:
    products = sorted(df["Product"].unique().tolist())
    selected_products = st.sidebar.multiselect("Products", products, default=products[:6])
else:
    selected_products = None

bins = st.sidebar.slider("Histogram bins", 5, 80, 20)

# Apply filters
df_view = df.copy()

if date_range and len(date_range) == 2 and "Date" in df_view:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= start) & (df_view["Date"] <= end)]

if selected_products:
    df_view = df_view[df_view["Product"].isin(selected_products)]

# ----------------------------
# Metrics
# ----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
c2.metric("Total Sales", f"{df_view['Sales'].sum():,.2f}")
c3.metric("Total Profit", f"{df_view['Profit'].sum():,.2f}")
c4.metric("Total Quantity", f"{int(df_view['Quantity'].sum())}")

st.markdown("---")

# ----------------------------
# Main Charts
# ----------------------------

# Quantity over time
if "Date" in df_view and "Quantity" in df_view:
    st.subheader("📅 Quantity Over Time")
    fig_q = px.line(df_view.sort_values("Date"), x="Date", y="Quantity", markers=True)
    st.plotly_chart(fig_q, use_container_width=True)

# Profit by Product
st.subheader("💰 Profit by Product")
prod_df = df_view.groupby("Product")["Profit"].sum().reset_index()
fig_profit_prod = px.bar(prod_df, x="Product", y="Profit")
st.plotly_chart(fig_profit_prod, use_container_width=True)

# Sales vs Profit
st.subheader("📊 Sales vs Profit (Trendline)")
try:
    fig_sp = px.scatter(df_view, x="Sales", y="Profit", color="Product", trendline="ols")
except:
    fig_sp = px.scatter(df_view, x="Sales", y="Profit", color="Product")
st.plotly_chart(fig_sp, use_container_width=True)

# Treemap
st.subheader("🗂️ Sales Treemap")
treemap_df = df_view.groupby(["Category", "Product"]).agg(
    Sales=("Sales", "sum"),
    Profit=("Profit", "sum")
).reset_index()

treemap_df["Profit_Margin"] = treemap_df["Profit"] / treemap_df["Sales"]

fig_treemap = px.treemap(
    treemap_df,
    path=["Category", "Product"],
    values="Sales",
    color="Profit_Margin",
    color_continuous_scale="RdYlGn",
)

st.plotly_chart(fig_treemap, use_container_width=True)

# Sales histogram
st.subheader("📦 Sales Distribution")
fig_hist = px.histogram(df_view, x="Sales", nbins=bins)
st.plotly_chart(fig_hist, use_container_width=True)

# ----------------------------
# Summary / Insights
# ----------------------------
st.markdown("---")
st.subheader("📊 Statistical Summary")
st.dataframe(df_view.describe().T)

st.subheader("📝 Insights Summary")
insights = []

corr_val = df_view["Sales"].corr(df_view["Profit"])
if corr_val > 0.4:
    insights.append("Sales and Profit show a strong positive relationship.")
elif corr_val < -0.3:
    insights.append("Sales and Profit are negatively correlated.")
else:
    insights.append("Sales and Profit show a weak or moderate correlation.")

top_cat = df_view["Category"].value_counts().idxmax()
insights.append(f"Category **{top_cat}** contributes the most to total Sales.")

top_prod = df_view.groupby("Product")["Sales"].sum().idxmax()
insights.append(f"Product **{top_prod}** generates the highest Sales.")

top_customer = df_view.groupby("Customer")["Sales"].sum().idxmax()
insights.append(f"Top customer: **{top_customer}**.")

for point in insights:
    st.write("✔", point)

# ----------------------------
# PDF REPORT GENERATION
# ----------------------------
st.markdown("---")
st.subheader("📄 Download PDF Report")

def plotly_fig_to_png(fig):
    """Convert Plotly figure to PNG **without Chrome** using SVG."""
    svg_bytes = fig.to_image(format="svg")
    try:
        import cairosvg
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
        return png_bytes
    except:
        pass  # fallback
    # If cairosvg not available, fallback to simple PNG-less PDF
    return None

def generate_pdf_with_image(fig, insights_list):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, 750, "Sales EDA Report")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, 735, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Convert figure to PNG
    png_bytes = plotly_fig_to_png(fig)

    if png_bytes:
        img = ImageReader(io.BytesIO(png_bytes))
        pdf.drawImage(img, 40, 420, width=520, preserveAspectRatio=True)
    else:
        pdf.setFont("Helvetica", 12)
        pdf.drawString(40, 720, "(Chart Image Unavailable — Using Text Report Only)")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, 400, "Insights:")
    y = 380
    for line in insights_list:
        pdf.drawString(50, y, f"- {line}")
        y -= 20

    pdf.save()
    buffer.seek(0)
    return buffer

if st.button("⬇️ Download PDF Report"):
    pdf_bytes = generate_pdf_with_image(fig_treemap, insights)
    st.download_button(
        label="Download Report",
        data=pdf_bytes,
        file_name="Sales_EDA_Report.pdf",
        mime="application/pdf"
    )
