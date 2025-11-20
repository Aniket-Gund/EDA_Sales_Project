# app.py
"""
Sales EDA — HTML-only export version

Behavior:
- Loads /mnt/data/sales_dataset.xlsx (no uploader)
- Renders charts with Plotly
- Provides:
    * Download original dataset
    * Download interactive HTML snapshot containing ALL charts shown in the app
- Removed PNG and PDF export options
"""

import io
import os
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Sales EDA (HTML export)", layout="wide")
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

# Charts (same as before) — we keep references to each fig variable so we can collect them later
fig_q = fig_profit_prod = fig_sp = fig_treemap = fig_margin = fig_top_cust = fig_sales_hist = fig_cat_pie = None

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
# EXPORT LOGIC (HTML only)
# -------------------------
st.markdown("---")
st.subheader("📤 Download Interactive HTML Snapshot (all charts)")

# collect figures in display order
figures = []
fig_names = []
# maintain order consistent with UI
order = [
    ("Quantity Over Time", "fig_q"),
    ("Profit by Product", "fig_profit_prod"),
    ("Sales vs Profit", "fig_sp"),
    ("Treemap", "fig_treemap"),
    ("Profit Margin Distribution", "fig_margin"),
    ("Top Customers", "fig_top_cust"),
    ("Sales Distribution", "fig_sales_hist"),
    ("Category Pie", "fig_cat_pie"),
]
for label, varname in order:
    if varname in locals() and locals()[varname] is not None:
        figures.append(locals()[varname])
        fig_names.append(label)

if len(figures) == 0:
    st.info("No charts available to include in HTML snapshot.")
else:
    if st.button("⬇️ Download Interactive HTML"):
        # Build combined HTML: include plotlyjs only once (cdn), then include each figure fragment
        html_parts = []
        first = True
        for fig in figures:
            # for first fig include full_html=False with include_plotlyjs='cdn' so script included once
            if first:
                html_parts.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                first = False
            else:
                html_parts.append(fig.to_html(full_html=False, include_plotlyjs=False))
        # Wrap into a minimal HTML page with a header & generation timestamp
        header_html = f"<h1>Sales EDA Snapshot</h1><p>Generated: {datetime.utcnow().isoformat()} UTC</p><hr>"
        combined_html = "<html><head><meta charset='utf-8'></head><body>" + header_html + "".join(html_parts) + "</body></html>"
        html_bytes = combined_html.encode("utf-8")
        st.download_button("Download HTML file", data=html_bytes, file_name="dashboard_snapshot.html", mime="text/html")

st.markdown("---")
st.caption("This HTML file includes all interactive Plotly charts shown in the dashboard.")
