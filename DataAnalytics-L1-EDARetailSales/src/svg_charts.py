from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd

PALETTE = ["#4472C4", "#ED7D31", "#70AD47", "#A5A5A5", "#FFC000", "#5B9BD5"]
WIDTH, HEIGHT = 900, 520
LEFT, RIGHT, TOP, BOTTOM = 85, 35, 76, 105


def _start(title: str, subtitle: str = "") -> list[str]:
    sub = f'<text x="{WIDTH / 2}" y="48" class="subtitle">{escape(subtitle)}</text>' if subtitle else ""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}">',
        "<style>text{font-family:Arial,sans-serif;fill:#27364b}.title{font-size:25px;font-weight:700}.subtitle{font-size:14px;text-anchor:middle;fill:#5c6775}.label{font-size:13px}.small{font-size:11px;fill:#5c6775}.grid{stroke:#dfe5ec;stroke-width:1}.axis{stroke:#6b7788;stroke-width:1.4}</style>",
        f'<text x="{WIDTH / 2}" y="32" text-anchor="middle" class="title">{escape(title)}</text>',
        sub,
    ]


def _save(path: Path, parts: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")
    return path


def _bar(path: Path, title: str, labels: list[str], values: list[float], ylabel: str) -> Path:
    parts = _start(title, ylabel)
    x0, y0 = LEFT, HEIGHT - BOTTOM
    chart_w, chart_h = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM
    maximum = max(values, default=1) or 1
    for fraction in [0, .25, .5, .75, 1]:
        y = y0 - chart_h * fraction
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + chart_w}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4:.1f}" text-anchor="end" class="small">{maximum * fraction:,.0f}</text>')
    slot = chart_w / max(len(values), 1)
    bar_w = min(52, slot * .62)
    for index, (label, value) in enumerate(zip(labels, values)):
        height = chart_h * value / maximum
        x = x0 + slot * index + (slot - bar_w) / 2
        y = y0 - height
        color = PALETTE[index % len(PALETTE)]
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{height:.1f}" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="small">{value:,.0f}</text>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y0 + 24}" text-anchor="middle" class="label">{escape(str(label))}</text>')
    parts.extend([f'<line x1="{x0}" y1="{y0}" x2="{x0 + chart_w}" y2="{y0}" class="axis"/>',
                  f'<line x1="{x0}" y1="{TOP}" x2="{x0}" y2="{y0}" class="axis"/>'])
    return _save(path, parts)


def _line(path: Path, title: str, labels: list[str], values: list[float]) -> Path:
    parts = _start(title, "Revenue in dataset units")
    x0, y0 = LEFT, HEIGHT - BOTTOM
    chart_w, chart_h = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM
    maximum = max(values, default=1) or 1
    for fraction in [0, .25, .5, .75, 1]:
        y = y0 - chart_h * fraction
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + chart_w}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4:.1f}" text-anchor="end" class="small">{maximum * fraction:,.0f}</text>')
    points = []
    for i, value in enumerate(values):
        x = x0 + chart_w * i / max(len(values) - 1, 1)
        y = y0 - chart_h * value / maximum
        points.append((x, y))
    coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    parts.append(f'<polyline points="{coords}" fill="none" stroke="{PALETTE[0]}" stroke-width="3"/>')
    for i, ((x, y), label, value) in enumerate(zip(points, labels, values)):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{PALETTE[0]}"/>')
        parts.append(f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" class="small">{value:,.0f}</text>')
        if i % 2 == 0 or i == len(labels) - 1:
            parts.append(f'<text x="{x:.1f}" y="{y0 + 24}" text-anchor="middle" class="small">{escape(label)}</text>')
    return _save(path, parts)


def _scatter(path: Path, data: pd.DataFrame) -> Path:
    parts = _start("Unit price and transaction amount", "Each dot is one transaction")
    x0, y0 = LEFT, HEIGHT - BOTTOM
    chart_w, chart_h = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM
    xmax = float(data["price_per_unit"].max()) or 1
    ymax = float(data["total_amount"].max()) or 1
    for fraction in [0, .25, .5, .75, 1]:
        x = x0 + chart_w * fraction
        y = y0 - chart_h * fraction
        parts.append(f'<line x1="{x:.1f}" y1="{TOP}" x2="{x:.1f}" y2="{y0}" class="grid"/>')
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + chart_w}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{x:.1f}" y="{y0 + 22}" text-anchor="middle" class="small">{xmax * fraction:.0f}</text>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4:.1f}" text-anchor="end" class="small">{ymax * fraction:.0f}</text>')
    cats = list(data["product_category"].unique())
    color = {cat: PALETTE[i % len(PALETTE)] for i, cat in enumerate(cats)}
    for _, row in data.iterrows():
        x = x0 + chart_w * float(row["price_per_unit"]) / xmax
        y = y0 - chart_h * float(row["total_amount"]) / ymax
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color[row["product_category"]]}" fill-opacity=".6"/>')
    for i, cat in enumerate(cats):
        parts.append(f'<rect x="{WIDTH - 210}" y="{TOP + 18 * i}" width="10" height="10" fill="{color[cat]}"/><text x="{WIDTH - 192}" y="{TOP + 28 + 18 * i}" class="small">{escape(cat)}</text>')
    parts.append(f'<text x="{x0 + chart_w / 2}" y="{HEIGHT - 28}" text-anchor="middle" class="label">Price per unit (dataset units)</text>')
    return _save(path, parts)


def _heatmap(path: Path, data: pd.DataFrame) -> Path:
    columns = ["age", "quantity", "price_per_unit", "total_amount"]
    corr = data[columns].corr(numeric_only=True)
    parts = _start("Correlation between numeric fields", "Pearson correlation; descriptive only")
    x0, y0, cell = 270, 140, 78
    for j, col in enumerate(columns):
        parts.append(f'<text x="{x0 + j * cell + cell / 2}" y="{y0 - 12}" text-anchor="middle" class="small">{escape(col.replace("_", " "))}</text>')
        parts.append(f'<text x="{x0 - 10}" y="{y0 + j * cell + 45}" text-anchor="end" class="small">{escape(col.replace("_", " "))}</text>')
        for i, row in enumerate(columns):
            value = float(corr.loc[row, col])
            shade = int(235 - abs(value) * 150)
            fill = f"rgb({shade},{shade - int(max(value, 0) * 40)},{shade})" if value >= 0 else f"rgb({shade},{shade},{shade - int(abs(value) * 45)} )"
            parts.append(f'<rect x="{x0 + i * cell}" y="{y0 + j * cell}" width="{cell}" height="{cell}" fill="{fill}" stroke="white"/>')
            parts.append(f'<text x="{x0 + i * cell + cell / 2}" y="{y0 + j * cell + 44}" text-anchor="middle" class="label">{value:.2f}</text>')
    return _save(path, parts)


def _boxplot(path: Path, values: pd.Series) -> Path:
    q1, median, q3 = values.quantile([.25, .5, .75]).tolist()
    spread = q3 - q1
    lower_fence, upper_fence = q1 - 1.5 * spread, q3 + 1.5 * spread
    inlier_values = values[(values >= lower_fence) & (values <= upper_fence)]
    low, high = float(inlier_values.min()), float(inlier_values.max())
    x0, x1, y = 110, 850, 265
    scale = lambda v: x0 + (float(v) - low) / (high - low or 1) * (x1 - x0)
    parts = _start("Transaction amount spread", "Box shows the interquartile range; points beyond whiskers need review")
    parts.extend([
        f'<line x1="{scale(low)}" y1="{y}" x2="{scale(high)}" y2="{y}" stroke="#4472C4" stroke-width="3"/>',
        f'<rect x="{scale(q1)}" y="{y - 45}" width="{scale(q3) - scale(q1)}" height="90" fill="#9db7dc" stroke="#4472C4" stroke-width="2"/>',
        f'<line x1="{scale(median)}" y1="{y - 45}" x2="{scale(median)}" y2="{y + 45}" stroke="#27364b" stroke-width="3"/>',
        f'<line x1="{scale(low)}" y1="{y - 25}" x2="{scale(low)}" y2="{y + 25}" stroke="#4472C4" stroke-width="2"/>',
        f'<line x1="{scale(high)}" y1="{y - 25}" x2="{scale(high)}" y2="{y + 25}" stroke="#4472C4" stroke-width="2"/>',
        f'<text x="{scale(q1)}" y="{y + 80}" text-anchor="middle" class="small">Q1 {q1:,.0f}</text>',
        f'<text x="{scale(median)}" y="{y - 58}" text-anchor="middle" class="small">Median {median:,.0f}</text>',
        f'<text x="{scale(q3)}" y="{y + 80}" text-anchor="middle" class="small">Q3 {q3:,.0f}</text>',
    ])
    for value in values[(values < lower_fence) | (values > upper_fence)]:
        parts.append(f'<circle cx="{scale(value)}" cy="{y}" r="4" fill="#ED7D31" stroke="white" stroke-width="1"/>')
    return _save(path, parts)


def create_svg_visualizations(data: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    monthly = data.groupby("month", as_index=False)["total_amount"].sum().sort_values("month")
    categories = data.groupby("product_category")["total_amount"].sum().sort_values(ascending=False)
    ages = data.groupby("age_group", observed=False)["total_amount"].sum()
    genders = data.groupby("gender")["total_amount"].sum().sort_values(ascending=False)
    weekdays = data.groupby("weekday")["total_amount"].sum().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ).dropna()
    charts = [
        _line(output / "monthly_sales.svg", "Monthly sales revenue", monthly["month"].dt.strftime("%b %y").tolist(), monthly["total_amount"].astype(float).tolist()),
        _bar(output / "category_revenue.svg", "Revenue by product category", categories.index.tolist(), categories.values.astype(float).tolist(), "Revenue (dataset units)"),
        _bar(output / "age_distribution.svg", "Customer age distribution", ["Under 25", "25-34", "35-44", "45-54", "55+", "Unknown"], [int((data["age_group"] == label).sum()) for label in ["Under 25", "25-34", "35-44", "45-54", "55+", "Unknown"]], "Transactions by age group"),
        _bar(output / "gender_revenue_share.svg", "Revenue by recorded gender", genders.index.tolist(), genders.values.astype(float).tolist(), "Revenue (dataset units)"),
        _bar(output / "age_group_revenue.svg", "Revenue by customer age group", ages.index.astype(str).tolist(), ages.values.astype(float).tolist(), "Revenue (dataset units)"),
        _heatmap(output / "correlation_heatmap.svg", data),
        _scatter(output / "price_vs_amount.svg", data),
        _boxplot(output / "transaction_amount_boxplot.svg", data["total_amount"]),
        _bar(output / "weekday_revenue.svg", "Revenue by weekday", weekdays.index.tolist(), weekdays.values.astype(float).tolist(), "Revenue (dataset units)"),
    ]
    return charts
