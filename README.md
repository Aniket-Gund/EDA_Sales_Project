# 📈 Retail Sales Exploratory Data Analysis & Analytics App

[![GitHub Stars](https://img.shields.io/github/stars/Aniket-Gund/EDA_Sales_Project?style=for-the-badge&color=blue)](https://github.com/Aniket-Gund/EDA_Sales_Project/stargazers)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

An exploratory data analysis and interactive Streamlit web dashboard analyzing retail sales datasets. Features sales trend forecasting, regional demand patterns, customer demographics, and product revenue contributions.

---

## 🌟 Key Features

- **📊 Comprehensive Visual Reports**: Time-series sales trend curves, profit margins across product categories, and regional revenue maps.
- **📄 Interactive HTML Profiling**: Includes `sales_eda_snapshot.html` for offline interactive exploration.
- **🌐 Streamlit Application**: Live web dashboard for dynamic filtering by date range, product line, and sales region.
- **📓 Jupyter Notebook**: Step-by-step EDA methodology documented in `EDA_Project_Sales.ipynb`.

---

## 🏗️ Data Architecture

```mermaid
flowchart LR
    A[sales_dataset.xlsx Raw Data] --> B[Data Cleaning & Missing Value Treatment]
    B --> C[Jupyter Analysis: EDA_Project_Sales.ipynb]
    C --> D[HTML Profile Report: sales_eda_snapshot.html]
    B --> E[Streamlit Dashboard: app.py]
    E --> F[Interactive KPI Metrics & Revenue Charts]
```

---

## 📂 Repository Structure

```
EDA_Sales_Project/
│
├── EDA_Project_Sales.ipynb  # Interactive Jupyter notebook with statistical figures
├── app.py                   # Streamlit web analytics dashboard
├── eda_project_sales.py     # Standalone data analysis script
├── sales_dataset.xlsx       # Primary Excel sales transaction records
├── sales_eda_snapshot.html  # Standalone interactive HTML profiling report
├── requirements.txt         # Dependencies
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

```bash
git clone https://github.com/Aniket-Gund/EDA_Sales_Project.git
cd EDA_Sales_Project

python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
streamlit run app.py
```

---

## 👨‍💻 Author

**Aniket Gund**
- GitHub: [@Aniket-Gund](https://github.com/Aniket-Gund)
- LinkedIn: [Aniket Gund](https://www.linkedin.com/in/aniket-gund/)

---

## 📄 License

Distributed under the [MIT License](LICENSE).
