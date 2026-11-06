from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "transaction_id",
    "date",
    "customer_id",
    "gender",
    "age",
    "product_category",
    "quantity",
    "price_per_unit",
    "total_amount",
}
COLUMN_MAP = {
    "Transaction ID": "transaction_id",
    "Date": "date",
    "Customer ID": "customer_id",
    "Gender": "gender",
    "Age": "age",
    "Product Category": "product_category",
    "Quantity": "quantity",
    "Price per Unit": "price_per_unit",
    "Total Amount": "total_amount",
}
NUMERIC_COLUMNS = ["age", "quantity", "price_per_unit", "total_amount"]
AGE_LABELS = ["Under 25", "25-34", "35-44", "45-54", "55+"]
AGE_BINS = [0, 25, 35, 45, 55, 101]


def inspect_raw_data(raw: pd.DataFrame) -> dict[str, Any]:
    """Capture quality checks before any transformations are applied."""
    return {
        "rows": int(len(raw)),
        "columns": int(raw.shape[1]),
        "duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_transaction_ids": int(raw["Transaction ID"].duplicated().sum())
        if "Transaction ID" in raw else 0,
        "missing_by_column": raw.isna().sum().astype(int).to_dict(),
        "dtypes": raw.dtypes.astype(str).to_dict(),
    }


def prepare_sales_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Standardize fields, remove duplicate transactions and document exclusions."""
    data = raw.rename(columns=COLUMN_MAP).copy()
    missing_columns = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing_columns:
        raise ValueError(f"Required dataset columns are missing: {missing_columns}")

    starting_rows = len(data)
    data["transaction_id"] = data["transaction_id"].astype("string").str.strip()
    duplicate_ids = int(data["transaction_id"].duplicated(keep="first").sum())
    data = data.drop_duplicates(subset="transaction_id", keep="first").copy()

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    invalid_dates = int(data["date"].isna().sum())
    data["age"] = pd.to_numeric(data["age"], errors="coerce")
    for column in ["quantity", "price_per_unit", "total_amount"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    # Invalid ages are kept as unknown rather than losing otherwise useful purchases.
    outside_age_range = ~data["age"].between(0, 100)
    invalid_age_count = int(outside_age_range.sum())
    data.loc[outside_age_range, "age"] = np.nan

    data["gender"] = data["gender"].astype("string").str.strip().str.title()
    data["gender"] = data["gender"].replace({"": pd.NA, "Nan": pd.NA}).fillna("Unknown")
    data["product_category"] = (
        data["product_category"].astype("string").str.strip().str.title()
        .replace({"": pd.NA, "Nan": pd.NA}).fillna("Unspecified")
    )
    data["customer_id"] = (
        data["customer_id"].astype("string").str.strip()
        .replace({"": pd.NA, "Nan": pd.NA}).fillna("Unknown")
    )

    calculated_amount = data["quantity"] * data["price_per_unit"]
    amount_mismatches = int(
        (data["total_amount"].notna() & calculated_amount.notna()
         & ~np.isclose(data["total_amount"], calculated_amount, rtol=0.001, atol=0.01)).sum()
    )
    invalid_transaction = (
        data["date"].isna()
        | data["quantity"].isna()
        | data["price_per_unit"].isna()
        | data["total_amount"].isna()
        | (data["quantity"] <= 0)
        | (data["price_per_unit"] <= 0)
        | (data["total_amount"] < 0)
    )
    excluded_transactions = int(invalid_transaction.sum())
    data = data.loc[~invalid_transaction].copy()

    data["month"] = data["date"].dt.to_period("M").dt.to_timestamp()
    data["quarter"] = data["date"].dt.to_period("Q").astype(str)
    data["weekday"] = data["date"].dt.day_name()
    data["age_group"] = pd.cut(
        data["age"], bins=AGE_BINS, labels=AGE_LABELS, right=False
    ).astype("string").fillna("Unknown")

    report = {
        "starting_rows": int(starting_rows),
        "duplicate_transaction_ids_removed": duplicate_ids,
        "invalid_dates_found": invalid_dates,
        "invalid_ages_set_unknown": invalid_age_count,
        "amount_mismatches": amount_mismatches,
        "invalid_transactions_excluded": excluded_transactions,
        "clean_rows": int(len(data)),
        "missing_after_cleaning": data[list(REQUIRED_COLUMNS)].isna().sum().astype(int).to_dict(),
    }
    return data.reset_index(drop=True), report


def load_sales_data(csv_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    raw = pd.read_csv(csv_path)
    profile = inspect_raw_data(raw)
    cleaned, cleaning = prepare_sales_data(raw)
    return raw, cleaned, {"profile": profile, "cleaning": cleaning}


def descriptive_statistics(data: pd.DataFrame) -> pd.DataFrame:
    stats = data[NUMERIC_COLUMNS].describe().T
    stats["median"] = data[NUMERIC_COLUMNS].median()
    stats["mode"] = data[NUMERIC_COLUMNS].mode().iloc[0]
    stats["sample_std"] = data[NUMERIC_COLUMNS].std(ddof=1)
    return stats[["count", "mean", "median", "mode", "sample_std", "min", "max"]]


def summarize_sales(data: pd.DataFrame) -> dict[str, Any]:
    return {
        "transactions": int(len(data)),
        "customers": int(data["customer_id"].nunique()),
        "revenue": float(data["total_amount"].sum()),
        "average_transaction": float(data["total_amount"].mean()),
        "median_transaction": float(data["total_amount"].median()),
        "date_start": data["date"].min(),
        "date_end": data["date"].max(),
    }


def monthly_sales(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby("month", as_index=False).agg(
        revenue=("total_amount", "sum"), transactions=("transaction_id", "nunique")
    ).sort_values("month")


def category_sales(data: pd.DataFrame) -> pd.DataFrame:
    result = data.groupby("product_category", as_index=False).agg(
        revenue=("total_amount", "sum"),
        average_transaction=("total_amount", "mean"),
        transactions=("transaction_id", "nunique"),
        units=("quantity", "sum"),
    )
    result["revenue_share_pct"] = result["revenue"] / result["revenue"].sum() * 100
    return result.sort_values("revenue", ascending=False)


def demographic_sales(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    gender = data.groupby("gender", as_index=False).agg(
        revenue=("total_amount", "sum"), transactions=("transaction_id", "nunique")
    )
    gender["revenue_share_pct"] = gender["revenue"] / gender["revenue"].sum() * 100
    age = data.groupby("age_group", observed=False, as_index=False).agg(
        revenue=("total_amount", "sum"), transactions=("transaction_id", "nunique")
    )
    age["revenue_share_pct"] = age["revenue"] / age["revenue"].sum() * 100
    return gender.sort_values("revenue", ascending=False), age


def create_visualizations(data: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        from svg_charts import create_svg_visualizations

        return create_svg_visualizations(data, output_dir)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")
    created: list[Path] = []

    def save(name: str) -> None:
        target = output / name
        plt.tight_layout()
        plt.savefig(target, dpi=160, bbox_inches="tight")
        plt.close()
        created.append(target)

    monthly = monthly_sales(data)
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=monthly, x="month", y="revenue", marker="o", linewidth=2.3)
    plt.title("Monthly sales revenue")
    plt.xlabel("Month")
    plt.ylabel("Revenue (dataset units)")
    plt.xticks(rotation=45)
    save("monthly_sales.svg")

    plt.figure(figsize=(8, 5))
    sns.barplot(data=category_sales(data), x="product_category", y="revenue")
    plt.title("Revenue by product category")
    plt.xlabel("Product category")
    plt.ylabel("Revenue (dataset units)")
    save("category_revenue.svg")

    plt.figure(figsize=(8, 5))
    sns.histplot(data=data, x="age", bins=12, kde=True, color="#4472C4")
    plt.title("Customer age distribution")
    plt.xlabel("Age (years)")
    plt.ylabel("Transactions")
    save("age_distribution.svg")

    gender, _ = demographic_sales(data)
    plt.figure(figsize=(7, 5))
    plt.pie(gender["revenue"], labels=gender["gender"], autopct="%1.1f%%", startangle=90)
    plt.title("Revenue share by recorded gender")
    save("gender_revenue_share.svg")

    plt.figure(figsize=(8, 5))
    sns.barplot(data=demographic_sales(data)[1], x="age_group", y="revenue", order=AGE_LABELS + ["Unknown"])
    plt.title("Revenue by customer age group")
    plt.xlabel("Age group")
    plt.ylabel("Revenue (dataset units)")
    save("age_group_revenue.svg")

    correlation = data[NUMERIC_COLUMNS].corr(numeric_only=True)
    plt.figure(figsize=(7, 5.5))
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="vlag", center=0, square=True)
    plt.title("Correlation between numeric fields")
    save("correlation_heatmap.svg")

    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=data, x="price_per_unit", y="total_amount", hue="product_category", alpha=0.75)
    plt.title("Unit price and transaction amount")
    plt.xlabel("Price per unit (dataset units)")
    plt.ylabel("Transaction amount (dataset units)")
    save("price_vs_amount.svg")

    plt.figure(figsize=(8, 4.5))
    sns.boxplot(data=data, x="total_amount", color="#70AD47")
    plt.title("Transaction amount spread and potential outliers")
    plt.xlabel("Transaction amount (dataset units)")
    save("transaction_amount_boxplot.svg")

    plt.figure(figsize=(9, 5))
    sns.barplot(data=data.groupby("weekday", as_index=False)["total_amount"].sum(),
                x="weekday", y="total_amount",
                order=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    plt.title("Revenue by weekday")
    plt.xlabel("Weekday")
    plt.ylabel("Revenue (dataset units)")
    plt.xticks(rotation=30)
    save("weekday_revenue.svg")

    return created


def build_findings(data: pd.DataFrame) -> dict[str, Any]:
    monthly = monthly_sales(data)
    # Keep partial first/last months out of the full-month comparison.
    first_month = data["date"].min().to_period("M")
    last_month = data["date"].max().to_period("M")
    complete_months = monthly[~monthly["month"].dt.to_period("M").isin([first_month, last_month])]
    comparable = complete_months if not complete_months.empty else monthly
    categories = category_sales(data)
    gender, ages = demographic_sales(data)
    correlations = data[NUMERIC_COLUMNS].corr(numeric_only=True)
    weekday = data.groupby("weekday")["total_amount"].sum().sort_values(ascending=False)
    return {
        "summary": summarize_sales(data),
        "top_month": comparable.loc[comparable["revenue"].idxmax()],
        "low_month": comparable.loc[comparable["revenue"].idxmin()],
        "partial_months_excluded": [str(first_month), str(last_month)],
        "top_category": categories.iloc[0],
        "bottom_category": categories.iloc[-1],
        "gender": gender,
        "age_groups": ages,
        "correlations": correlations,
        "weekday_top": weekday.index[0],
        "weekday_low": weekday.index[-1],
        "monthly": monthly,
        "categories": categories,
    }


def write_findings_report(data: pd.DataFrame, quality: dict[str, Any], output_path: str | Path) -> Path:
    findings = build_findings(data)
    top_month = findings["top_month"]
    low_month = findings["low_month"]
    top_category = findings["top_category"]
    quantity_correlation = findings["correlations"].loc["quantity", "total_amount"]
    age_correlation = findings["correlations"].loc["age", "total_amount"]
    amount_check = quality["cleaning"]["amount_mismatches"]
    total = findings["summary"]["revenue"]
    text = f"""# Retail sales analysis: findings and recommendations

## Scope and data quality

This exploratory project uses a 1,000-row Kaggle sample dataset. The dataset is described by its publisher as sample/crafted data; results below describe only this file and are not verified company performance. Monetary units are not specified by the source, so values are shown as dataset units. Transaction rows are the unit of analysis.

- Rows loaded: {quality['profile']['rows']:,}
- Rows after cleaning: {quality['cleaning']['clean_rows']:,}
- Duplicate transaction IDs removed: {quality['cleaning']['duplicate_transaction_ids_removed']:,}
- Invalid transaction rows excluded: {quality['cleaning']['invalid_transactions_excluded']:,}
- Missing ages set to unknown: {quality['cleaning']['invalid_ages_set_unknown']:,}
- Quantity x unit-price mismatches: {amount_check:,}
- Total recorded revenue: {total:,.0f} dataset units

The source contains product categories, not product names/SKUs. The analysis therefore compares categories and does not claim a top-ten product ranking. Customer identifiers in this file are transaction-level sample labels; they do not provide reliable repeat-purchase history or customer lifetime value.

## Findings

1. **Monthly movement:** Among the comparable full months, {top_month['month']:%B %Y} is highest at {top_month['revenue']:,.0f} dataset units, while {low_month['month']:%B %Y} is lowest at {low_month['revenue']:,.0f}. The first and last months ({', '.join(findings['partial_months_excluded'])}) are excluded from this comparison because their coverage may be partial.
2. **Category mix:** {top_category['product_category']} leads the supplied categories with {top_category['revenue']:,.0f} dataset units ({top_category['revenue_share_pct']:.1f}% of revenue). This is a small gap within a constructed sample, not evidence of a persistent market advantage.
3. **Demographics:** The gender and age charts describe the distribution in the sample only. They should not be treated as causal evidence or used alone to target real customers.
4. **Transaction mechanics:** Recorded amount is designed to equal quantity multiplied by unit price in this dataset. The quantity-to-amount correlation is {quantity_correlation:.2f}; the age-to-amount correlation is {age_correlation:.2f}. These relationships are descriptive and the amount calculation creates a built-in relationship with its inputs.
5. **Weekday pattern:** {findings['weekday_top']} has the largest total in the supplied records and {findings['weekday_low']} the smallest. The synthetic sample size and time coverage limit how confidently this can guide staffing.

## Recommendations

- **Test offers in the weakest complete month:** Use a small, time-limited promotion and compare it with a baseline period before scaling. Avoid interpreting an incomplete month as a seasonal decline.
- **Review category contribution with margin data:** {top_category['product_category']} has the largest observed revenue total, but price, discount, cost and return data are absent. Compare gross margin before shifting inventory or marketing spend.
- **Collect better repeat-customer and product data:** Use stable, privacy-conscious customer keys and product-level identifiers in a future dataset. That would make repeat-purchase, product ranking and customer-value analysis possible.
- **Treat demographic differences as hypotheses:** Validate any age- or gender-based marketing idea with a larger, representative dataset and an appropriate fairness review; this sample alone does not justify segmentation.

## Limitations

The dataset is a small, constructed sample rather than an audited retailer export. It has no documented currency, cost/margin, discount, inventory, return or product-SKU fields. Descriptive patterns do not establish causation, and one year of sample dates is not enough to confirm seasonality.
"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
