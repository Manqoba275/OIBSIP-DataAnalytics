import json
from pathlib import Path

project = Path(__file__).resolve().parents[1]


def markdown(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.strip().splitlines(keepends=True),
    }


def code(text):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip().splitlines(keepends=True),
    }

cells = [
    markdown("""
# Retail Sales Data: Exploratory Analysis

**OASIS INFOBYTE Data Analytics - Level 1, Task 1**

This notebook checks a retail transaction sample, summarizes what is recorded, compares sales over time and across categories and demographics, and turns the observed patterns into practical next steps.

**Questions:** Which complete month and product category have the highest revenue? How are transactions distributed by age and recorded gender? What data-quality and interpretation limits should affect the recommendations?
"""),
    markdown("""
## Dataset and scope

The 1,000-row file is the Retail Sales Dataset attributed to `mohammadtalib786` on Kaggle. The publisher describes it as a sample/crafted dataset, so it is not treated as audited company performance. The currency is unspecified. The repository includes the CSV and source notes so this notebook can be run without credentials.

A transaction row is the unit of analysis. The file has product categories rather than product names/SKUs, and the customer labels do not establish repeat purchase history. Those limitations rule out product-level rankings and customer lifetime value estimates.
"""),
    code("""
from pathlib import Path
import sys

import pandas as pd

try:
    from IPython.display import display
except ImportError:
    display = print

working_directory = Path.cwd()
candidates = [working_directory, working_directory / "DataAnalytics-L1-EDARetailSales"]
candidates.extend(working_directory.parents)
project_root = next(
    (candidate for candidate in candidates if (candidate / "src" / "retail_eda.py").exists()),
    None,
)
if project_root is None:
    raise FileNotFoundError("Open this notebook from the project folder or the repository root.")
sys.path.insert(0, str(project_root / "src"))

from retail_eda import (
    category_sales,
    create_visualizations,
    demographic_sales,
    descriptive_statistics,
    load_sales_data,
    monthly_sales,
    summarize_sales,
    write_findings_report,
)

raw, sales, quality = load_sales_data(project_root / "data" / "retail_sales_dataset.csv")
print(f"Loaded {len(raw):,} source rows and retained {len(sales):,} valid transactions.")
"""),
    markdown("""
## 1. Inspect structure and quality

Check dimensions, data types, missing values and duplicate records before interpreting totals. The cleaning function keeps rows with missing demographic labels by marking them unknown, removes duplicate transaction IDs after keeping the first record, parses dates, and excludes sales rows with invalid dates or non-positive quantity/price.
"""),
    code("""
print("Raw shape:", raw.shape)
print("Raw dtypes:")
display(raw.dtypes.rename("dtype").to_frame())
print("Missing values by source column:")
display(raw.isna().sum().rename("missing").to_frame())
print("Cleaning decisions:")
display(pd.Series(quality["cleaning"], name="count").to_frame())
"""),
    markdown("""
The supplied file is clean on these checks; the cleaning steps remain explicit so the workflow can handle a later export with malformed or duplicate rows. The amount reconciliation check compares `Total Amount` with `Quantity × Price per Unit` and reports mismatches instead of silently rewriting the source field.
"""),
    markdown("## 2. Descriptive statistics and sales overview"),
    code("""
summary = summarize_sales(sales)
print(f"Date coverage: {summary['date_start']:%Y-%m-%d} to {summary['date_end']:%Y-%m-%d}")
print(f"Transactions: {summary['transactions']:,} | Customer labels: {summary['customers']:,}")
print(f"Total revenue: {summary['revenue']:,.0f} dataset units")
print(f"Average / median transaction: {summary['average_transaction']:,.2f} / {summary['median_transaction']:,.2f}")
display(descriptive_statistics(sales).round(2))
"""),
    markdown("## 3. Monthly and quarterly sales movement"),
    code("""
monthly = monthly_sales(sales)
quarterly = sales.groupby("quarter", as_index=False).agg(
    revenue=("total_amount", "sum"), transactions=("transaction_id", "nunique")
)
display(monthly.assign(month=monthly["month"].dt.strftime("%b %Y")).round(2))
display(quarterly.round(2))
"""),
    markdown("""
The first and last month may be partial observation periods. The findings report compares full months separately and flags the edge months rather than declaring them seasonal highs or lows.
"""),
    markdown("## 4. Customer demographics"),
    code("""
gender_sales, age_sales = demographic_sales(sales)
display(gender_sales.round(2))
display(age_sales.round(2))
"""),
    markdown("""
Age and recorded gender are descriptive dimensions in a constructed sample. Differences should not be treated as causal and should not alone drive targeting decisions.
"""),
    markdown("## 5. Category sales and top category"),
    code("""
categories = category_sales(sales)
display(categories.round(2))
"""),
    markdown("""
The dataset has no item-level product name or SKU, so category totals are the most detailed valid product comparison. A top-ten SKU chart would be misleading for this file.
"""),
    markdown("## 6. Relationships and unusual values"),
    code("""
correlation = sales[["age", "quantity", "price_per_unit", "total_amount"]].corr(numeric_only=True)
display(correlation.round(3))
print("Amount checks:", quality["cleaning"]["amount_mismatches"], "rows differ from quantity x price.")
print("Weekday revenue:")
display(sales.groupby("weekday")["total_amount"].sum().sort_values(ascending=False).rename("revenue").to_frame())
"""),
    markdown("""
`Total Amount` is calculated from quantity and unit price in this sample. Correlations involving those fields partly reflect that arithmetic relationship and should not be presented as independent drivers. The boxplot flags unusual values for review; it does not automatically remove legitimate large transactions.
"""),
    markdown("## 7. Charts"),
    code("""
chart_paths = create_visualizations(sales, project_root / "screenshots")
print(f"Exported {len(chart_paths)} charts:")
for path in chart_paths:
    print(path.relative_to(project_root))
"""),
    markdown("""
### Monthly revenue

![Monthly revenue](../screenshots/monthly_sales.svg)

### Category revenue

![Revenue by product category](../screenshots/category_revenue.svg)

### Age-group revenue

![Revenue by age group](../screenshots/age_group_revenue.svg)

### Correlation matrix

![Numeric correlation heatmap](../screenshots/correlation_heatmap.svg)
"""),
    markdown("## 8. Written findings and recommendations"),
    code("""
report_path = write_findings_report(sales, quality, project_root / "reports" / "findings.md")
print(report_path.read_text(encoding="utf-8"))
"""),
    markdown("""
## Conclusion

Use a weak full-month result as a reason to investigate, then test a limited promotion against a comparable baseline. Review category contribution together with margin and returns before changing inventory. For future analysis, collect documented currency, stable repeat-customer keys and product-level identifiers. This dataset supports a learning exercise and descriptive sample analysis, not claims about a named retailer or its customers.
"""),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
(project / "notebooks" / "EDA_Retail_Sales.ipynb").write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
)
