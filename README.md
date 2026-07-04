# StreamCore Revenue Analytics

Revenue analysis project for a fictional SaaS company (StreamCore). The goal was to figure out why monthly recurring revenue growth slowed down over the last two quarters and what to do about it.

## Background

StreamCore is a subscription streaming service with four plans (Basic, Standard, Premium, Family) and customers across 10 countries, split into Consumer, SMB and Enterprise segments. Revenue kept growing but the growth rate dropped from about 4.2% per month in the first half of 2025 to about 2.2% in the second half.

## What's in this repo

- `data/` - script that generates the dataset (customers and monthly subscription records), plus the CSV output
- `sql/` - SQL queries used for the main analysis (revenue overview, MRR movement, cohort retention, LTV, churn)
- `analysis/` - Python script for charts and a simple forecast
- `dashboard/` - HTML mockup of what the final dashboard should look like (built as a reference for a Tableau version)
- `insights.md` - summary of findings and recommendations

## Data

The dataset is synthetic (generated with a Python script, not real company data) but built to behave like a real SaaS business: signups grow with seasonality, churn depends on plan and tenure, customers occasionally upgrade or downgrade. About 106,000 customers and 1.1 million subscription-month records over 3 years.

## Main finding

The slowdown is mostly a churn problem, not an acquisition problem. New signups held up fine. Churn rate went from about 3.8% to 4.4% per month, and most of that increase came from one plan and one segment specifically: Basic plan churn jumped from 5.65% to 6.58%, and Consumer segment churn rose from 4.29% to 4.89%. Enterprise customers barely moved (2.11% to 2.28%). Churn increased fairly evenly across countries, so it does not look like a regional issue - more likely something about the product or pricing at the entry tier.

Cohort retention held steady across signup months, so new customers are not lower quality than before. It is an existing-customer problem, not an acquisition problem.

See `insights.md` for the full breakdown and recommendations.

## Tools used

SQL (SQLite), Python (pandas, matplotlib, seaborn, statsmodels for the forecast), HTML/CSS/Chart.js for the dashboard mockup.

## How to run

```
cd data
python generate_data.py
```

This creates `customers.csv` and `subscriptions_monthly.csv`. To run the SQL queries, load both CSVs into a SQLite database:

```python
import sqlite3, pandas as pd
conn = sqlite3.connect("streamcore.db")
pd.read_csv("data/customers.csv").to_sql("customers", conn, index=False)
pd.read_csv("data/subscriptions_monthly.csv").to_sql("subscriptions_monthly", conn, index=False)
```

Then run the queries in `sql/queries.sql` against that database, or run `analysis/analysis.py` directly on the CSVs to get the charts.
