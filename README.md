# Portfolio

A collection of **Engineering Leadership resources**, **Data Architecture designs**, and technical data science projects.

Built and maintained by Jimmy Pang.

---

## 🚀 Engineering Leadership & Strategy

### 👥 [Building High-Performing BI Teams](leadership/team-building-framework.md)
**A comprehensive framework for building and scaling analytics teams.**
- **Recruitment & Onboarding:** Structured 12-week onboarding roadmap and interview rubrics.
- **Culture & Operations:** Agile ceremonies, code review norms, and career development tracks.
- **Strategy:** Defining mission, values, and KPIs for data organizations.

## 🏗️ Data Architecture

### ❄️ [Modern Data Stack Design](architecture/modern-data-stack-design.md)
**Production-grade architecture patterns for scaling from 0 to 200+ consumers.**
- **Stack:** Fivetran (Ingest) -> Snowflake (Warehousing) -> dbt (Transform) -> Airflow (Orchestrate).
- **Patterns:** Layered modeling (Raw -> Staging -> Marts), Data Quality framework (Elementary), and RBAC governance.
- **Performance:** Clustering strategies and materialization rules for large-scale datasets.

---

## 🛠️ Technical Projects (Hands-on)

### 📊 [Data Wrangling Exercise](projects/data_wragling_exercise/)
**Overview:** Data wrangling and analysis using Hayes ad unit performance data across multiple years (2014-2017) and geographic regions.
**Key Skills:** Data import/aggregation, Time-series analysis.

### 🏠 [Housing Price Prediction](projects/housing_price/)
**Overview:** Exploratory data analysis and machine learning model development for housing price prediction.
**Key Skills:** Feature engineering, Regression modeling.

### 🎵 [Spotify Analysis](projects/spotify/)
**Overview:** Data analysis project for Spotify music streaming data.
**Key Skills:** API integration, Statistical exploration.

### 🪟 [Windows Store Apps Analysis](projects/windows_store_apps/)
**Overview:** Analysis of Microsoft Store application data including ratings, pricing, and categories.
**Key Features:** Data cleaning (currency/missing values), Unit testing validation.

### 🧪 [Testing & Utilities](projects/tests/)
**Overview:** Unit tests and data validation utilities.
**Files:** `test_msft_csv.py` - Structure validation for Windows Store Apps data.

### 📓 [Data World Experimentation](projects/test_dataworld/)
**Overview:** Exploratory notebook for testing data connections and API integrations.

---

## Repository Structure

```
portfolio/
├── architecture/             # Architecture designs & diagrams
├── leadership/               # Team building & management frameworks
├── projects/                 # Coding & Data Science projects
│   ├── spotify/
│   ├── windows_store_apps/
│   ├── housing_price/
│   └── ...
├── README.md
└── LICENSE
```

## Technologies & Tools
- **Leadership:** Team Building, Recruitment, Agile Management
- **Architecture:** dbt, Snowflake, Airflow, Data Governance
- **Tech:** Python, Pandas, Jupyter, Unit Testing

## License
© Jimmy Pang 2025. All rights reserved.
See [LICENSE](LICENSE) file for details.
