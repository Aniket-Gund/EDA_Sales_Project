# app.py
"""
Sales EDA — Final (with robust export fallbacks)

Behavior:
- Loads /mnt/data/sales_dataset.xlsx (no uploader)
- Renders charts with Plotly
- Tries to export PNG using kaleido
- If kaleido fails (Chrome/Chromium missing), falls back to:
    * Download interactive HTML of the selected chart
    * Create a PDF containing a simple text summary (always works)
- Also provides dataset download
"""

import io
import os
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

# PDF helper
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Sales EDA (Export-safe)", layout="wide")
st.title("📈 Sales EDA Dashboard by Aniket Gund")

# -------------------------
# Load dataset (no uploader)
# -------------------------
DATA_PATH = "sales_dataset.xlsx"
if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at: {DATA_PATH}")
    st.stop()

try:
    df = pd.read_excel(DATA_PATH)
except Exception as e:
    st.error(f"Error reading dataset: {e}")
    st.stop()

df.columns = [c.strip() for c in df.columns]

# Download original dataset
st.subheader("📁 Download Original Dataset")
try:
    with open(DATA_PATH, "rb") as f:
        st.download_button(
            label="⬇️ Download sales_dataset.xlsx",
            data=f,
            file_name=os.path.basename(DATA_PATH),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
except Exception:
    st.info("Unable to provide direct dataset download in this environment.")

# Preprocessing
if "Date" in df.columns:
    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except Exception:
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
    products = sorted(df["Product"].dropna().unique().tolist())
    selected_products = st.sidebar.multiselect("Products (filter)", options=products, default=products[:6])
else:
    selected_products = None

bins = st.sidebar.slider("Histogram bins (Sales)", 5, 60, 20)
show_profit_margin = st.sidebar.checkbox("Show profit margin histogram", value=True)

# Apply filters
df_view = df.copy()
if date_range and len(date_range) == 2 and "Date" in df_view.columns:
    s, e = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_view = df_view[(df_view["Date"] >= s) & (df_view["Date"] <= e)]

if selected_products and "Product" in df_view.columns:
    df_view = df_view[df_view["Product"].isin(selected_products)]

# Top metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df_view):,}")
total_sales = df_view["Sales"].sum() if "Sales" in df_view.columns else None
total_profit = df_view["Profit"].sum() if "Profit" in df_view.columns else None
total_qty = int(df_view["Quantity"].sum()) if "Quantity" in df_view.columns else None
c2.metric("Total Sales", f"{total_sales:,.2f}" if total_sales is not None else "n/a")
c3.metric("Total Profit", f"{total_profit:,.2f}" if total_profit is not None else "n/a")
c4.metric("Total Quantity", f"{total_qty:,}" if total_qty is not None else "n/a")

st.markdown("---")

# Charts (same as your app)
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

# 3) Sales vs Profit with trendline (try)
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    st.subheader("📊 Sales vs Profit (OLS Trendline)")
    color_arg = "Product" if "Product" in df_view.columns else None
    try:
        fig_sp = px.scatter(df_view, x="Sales", y="Profit", trendline="ols", color=color_arg, title="Sales vs Profit")
    except Exception:
        fig_sp = px.scatter(df_view, x="Sales", y="Profit", color=color_arg, title="Sales vs Profit (no trendline)")
    st.plotly_chart(fig_sp, use_container_width=True)

# Treemap (aggregated) — advanced with profit & margin
fig_treemap = None
if "Category" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("🗂️ Advanced Treemap — Sales, Profit & Margin")

    # aggregate
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

    cd = np.stack((df_agg["Profit"].fillna(0).to_numpy(), df_agg["Profit_Margin"].to_numpy()), axis=-1)
    fig_treemap.update_traces(
        customdata=cd,
        texttemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>Profit: ₹%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.1%}<br>Share: %{percentParent:.1%}",
        hovertemplate="<b>%{label}</b><br>Sales: ₹%{value:,.0f}<br>Profit: ₹%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.2%}<br>Share: %{percentParent:.2%}<extra></extra>",
        textposition="middle center",
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

# Profit margin histogram
if show_profit_margin and "Profit" in df_view.columns and "Sales" in df_view.columns:
    st.subheader("📉 Profit Margin Distribution")
    df_view = df_view.assign(Profit_Margin=np.where(df_view["Sales"] == 0, 0.0, df_view["Profit"] / df_view["Sales"]))
    fig_margin = px.histogram(df_view, x="Profit_Margin", nbins=40, title="Profit Margin Distribution")
    st.plotly_chart(fig_margin, use_container_width=True)

# Top customers
fig_top_cust = None
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

# Sales distribution and category pie
fig_sales_hist = None
fig_cat_pie = None
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

# Statistical summary
st.markdown("---")
st.subheader("📊 Statistical Summary")
summary = df_view.describe().T
st.dataframe(summary)

# Insights
st.subheader("📝 Insights Summary:")
insights = []
if "Sales" in df_view.columns and "Profit" in df_view.columns:
    corr_sp = df_view["Sales"].corr(df_view["Profit"])
    if corr_sp > 0.4:
        insights.append("Sales and Profit show a strong positive relationship — higher sales generally produce higher profit.")
    elif corr_sp < -0.3:
        insights.append("Sales and Profit are negatively correlated — check discounts or low-margin items.")
    else:
        insights.append("Sales and Profit show a weak correlation; margins differ by product/category.")
if "Category" in df_view.columns:
    top_cat = df_view["Category"].value_counts().idxmax()
    insights.append(f"Category **{top_cat}** is the most frequent and contributes substantially to total sales.")
if "Profit" in df_view.columns and "Sales" in df_view.columns:
    skew = df_view.assign(Profit_Margin=np.where(df_view["Sales"] == 0, 0.0, df_view["Profit"] / df_view["Sales"]))["Profit_Margin"].skew()
    insights.append("Profit margins are skewed." if skew > 1 else "Profit margins are fairly balanced.")
if "Customer" in df_view.columns and "Sales" in df_view.columns:
    top_customer = df_view.groupby("Customer")["Sales"].sum().idxmax()
    insights.append(f"Top customer: **{top_customer}**.")
if "Quantity" in df_view.columns and "Date" in df_view.columns:
    insights.append("Quantity varies over time; investigate seasonality or promotions.")
for it in insights:
    st.write("✔", it)

# -------------------------
# EXPORT LOGIC (robust)
# -------------------------
st.markdown("---")
st.subheader("📤 Export / Download")

# Choose representative figure for export priority
export_fig = fig_treemap or fig_sp or fig_sales_hist or fig_profit_prod if 'fig_profit_prod' in locals() else (fig_sp if 'fig_sp' in locals() else None)

def fig_to_png_bytes_safe(fig_obj, width=1200, height=800, scale=1):
    """
    Safely try to convert Plotly figure to PNG bytes via kaleido.
    Raises a RuntimeError with the original message on failure.
    """
    try:
        img_bytes = pio.to_image(fig_obj, format="png", width=width, height=height, scale=scale)
        return img_bytes
    except Exception as e:
        raise RuntimeError(str(e))

def make_pdf_bytes_with_image(title_text, png_bytes):
    """
    Create a PDF in-memory that embeds the given PNG bytes.
    """
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=(595, 842))  # A4-ish
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 800, title_text)
    c.setFont("Helvetica", 9)
    c.drawString(40, 785, f"Generated: {datetime.utcnow().isoformat()} UTC")
    # Image
    try:
        img_reader = ImageReader(io.BytesIO(png_bytes))
        c.drawImage(img_reader, 40, 350, width=515, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        # fallback: note image could not be embedded
        c.setFont("Helvetica", 10)
        c.drawString(40, 740, "Note: PNG image could not be embedded in this PDF.")
        c.drawString(40, 725, f"Image error: {str(e)[:200]}")
    c.showPage()
    c.save()
    buff.seek(0)
    return buff.read()

def make_pdf_bytes_text_only(title_text, insights_list):
    """
    Create a simple text-only PDF containing title + insights.
    """
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=(595, 842))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, title_text)
    c.setFont("Helvetica", 9)
    c.drawString(40, 785, f"Generated: {datetime.utcnow().isoformat()} UTC")
    y = 750
    c.setFont("Helvetica", 11)
    for line in insights_list:
        # wrap long lines
        wrapped = [line[i:i+100] for i in range(0, len(line), 100)]
        for w in wrapped:
            c.drawString(40, y, w)
            y -= 14
            if y < 100:
                c.showPage()
                y = 800
                c.setFont("Helvetica", 11)
    c.showPage()
    c.save()
    buff.seek(0)
    return buff.read()

# Buttons + fallback behavior
if export_fig is None:
    st.info("No figure available to export as image. You can still download the dataset or PDF text summary below.")
else:
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⬇️ Download PNG Snapshot"):
            try:
                png_bytes = fig_to_png_bytes_safe(export_fig)
                st.download_button("Download PNG", data=png_bytes, file_name="dashboard_snapshot.png", mime="image/png")
            except RuntimeError as e:
                # fallback: offer interactive HTML and show message
                st.error("PNG export failed (Kaleido/Chrome likely missing). Offering interactive HTML instead.")
                html_bytes = export_fig.to_html(full_html=True, include_plotlyjs='cdn').encode("utf-8")
                st.download_button("Download interactive HTML snapshot", data=html_bytes, file_name="dashboard_snapshot.html", mime="text/html")

    with col2:
        if st.button("⬇️ Download PDF Snapshot (with image if possible)"):
            try:
                png_bytes = fig_to_png_bytes_safe(export_fig)
                pdf_bytes = make_pdf_bytes_with_image("Sales EDA — Snapshot", png_bytes)
                st.download_button("Download PDF (with image)", data=pdf_bytes, file_name="Sales_Report_with_image.pdf", mime="application/pdf")
            except RuntimeError as e:
                # fallback: create text-only PDF using insights
                st.warning("PDF image embedding failed (Kaleido/Chrome likely missing). Generating text-only PDF summary instead.")
                pdf_text_bytes = make_pdf_bytes_text_only("Sales EDA — Summary", insights)
                st.download_button("Download PDF (text summary)", data=pdf_text_bytes, file_name="Sales_Report_summary.pdf", mime="application/pdf")

    with col3:
        # Always offer interactive HTML (works everywhere)
        if st.button("⬇️ Download Interactive HTML"):
            html_bytes = export_fig.to_html(full_html=True, include_plotlyjs='cdn').encode("utf-8")
            st.download_button("Download interactive HTML", data=html_bytes, file_name="dashboard_interactive.html", mime="text/html")

st.markdown("---")
st.caption("Tip: If PNG/PDF export fails due to Kaleido/Chrome, use the interactive HTML or the text-only PDF. To enable PNG exports install Chrome/Chromium in the environment or run `plotly_get_chrome` where supported.")
