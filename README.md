# Portfolio

A collection of data science and analysis projects showcasing data exploration, cleaning, visualization, and machine learning work. Built and maintained by Jimmy Pang.

## Projects

### 📊 [Data Wrangling Exercise](projects/data_wragling_exercise/)

**Overview:** Data wrangling and analysis using Hayes ad unit performance data across multiple years (2014-2017) and geographic regions.

**Key Skills:**
- Data import and aggregation from multiple CSV sources
- Time-series and geographic data analysis
- Data transformation and exploration

**Data:** Multiple ad unit performance datasets across different Canadian provinces (CD, GZ, NJ) and years.

---

### 🏠 [Housing Price Prediction](projects/housing_price/)

**Overview:** Exploratory data analysis and machine learning model development for housing price prediction.

**Key Skills:**
- Data exploration and visualization
- Feature engineering and analysis
- Regression modeling with structured datasets

**Data:** Training and test datasets for housing price prediction with multiple features.

---

### 🎵 [Spotify Analysis](projects/Spotify/)

**Overview:** Data analysis project for Spotify music streaming data.

**Key Skills:**
- Music streaming data analysis
- Statistical exploration and insights

---

### 🪟 [Windows Store Apps Analysis](projects/Windows_Store_Apps/)

**Overview:** Analysis of Microsoft Store application data including ratings, pricing, and categories.

**Key Features:**
- Data cleaning and preprocessing (handling special characters like ₹, handling "Free" apps)
- Statistical analysis by category
- Price and rating distribution analysis
- Data quality validation through unit tests

**Data:** Microsoft Store app data with columns including Name, Rating, Category, Date, and Price.

**Note:** Includes data cleaning examples dealing with currency symbols and missing values.

---

### 🧪 [Testing & Utilities](projects/tests/)

**Overview:** Unit tests and data validation utilities.

**Files:**
- `test_msft_csv.py` - Tests for Windows Store Apps CSV data structure and integrity

---

### 📓 [Data World Experimentation](projects/test_dataworld/)

**Overview:** Exploratory notebook for testing data connections and API integrations.

---

## Repository Structure

```
portfolio/
├── projects/
│   ├── data_wragling_exercise/   # Data wrangling with Hayes ad data
│   ├── housing_price/            # Housing price prediction
│   ├── Spotify/                  # Spotify data analysis
│   ├── Windows_Store_Apps/       # Microsoft Store apps analysis
│   ├── test_dataworld/           # Data integration experiments
│   └── tests/                    # Testing utilities
├── README.md
├── LICENSE
└── .gitignore
```

## Technologies & Tools

- **Python** - Primary programming language
- **Pandas** - Data manipulation and analysis
- **Jupyter Notebooks** - Interactive data exploration and analysis
- **Unit Testing** - Data validation and quality assurance

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/davnnis2003/portfolio.git
   cd portfolio
   ```

2. Install dependencies:
   ```bash
   pip install pandas jupyter
   ```

3. Open any notebook:
   ```bash
   jupyter notebook projects/<project_name>/<notebook_name>.ipynb
   ```

## License

© Jimmy Pang 2025. All rights reserved.

See [LICENSE](LICENSE) file for details.
