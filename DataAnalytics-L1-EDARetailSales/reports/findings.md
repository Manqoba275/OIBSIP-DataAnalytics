# Retail sales analysis: findings and recommendations

## Scope and data quality

This exploratory project uses a 1,000-row Kaggle sample dataset. The dataset is described by its publisher as sample/crafted data; results below describe only this file and are not verified company performance. Monetary units are not specified by the source, so values are shown as dataset units. Transaction rows are the unit of analysis.

- Rows loaded: 1,000
- Rows after cleaning: 1,000
- Duplicate transaction IDs removed: 0
- Invalid transaction rows excluded: 0
- Missing ages set to unknown: 0
- Quantity x unit-price mismatches: 0
- Total recorded revenue: 456,000 dataset units

The source contains product categories, not product names/SKUs. The analysis therefore compares categories and does not claim a top-ten product ranking. Customer identifiers in this file are transaction-level sample labels; they do not provide reliable repeat-purchase history or customer lifetime value.

## Findings

1. **Monthly movement:** Among the comparable full months, May 2023 is highest at 53,150 dataset units, while September 2023 is lowest at 23,620. The first and last months (2023-01, 2024-01) are excluded from this comparison because their coverage may be partial.
2. **Category mix:** Electronics leads the supplied categories with 156,905 dataset units (34.4% of revenue). This is a small gap within a constructed sample, not evidence of a persistent market advantage.
3. **Demographics:** The gender and age charts describe the distribution in the sample only. They should not be treated as causal evidence or used alone to target real customers.
4. **Transaction mechanics:** Recorded amount is designed to equal quantity multiplied by unit price in this dataset. The quantity-to-amount correlation is 0.37; the age-to-amount correlation is -0.06. These relationships are descriptive and the amount calculation creates a built-in relationship with its inputs.
5. **Weekday pattern:** Saturday has the largest total in the supplied records and Thursday the smallest. The synthetic sample size and time coverage limit how confidently this can guide staffing.

## Recommendations

- **Test offers in the weakest complete month:** Use a small, time-limited promotion and compare it with a baseline period before scaling. Avoid interpreting an incomplete month as a seasonal decline.
- **Review category contribution with margin data:** Electronics has the largest observed revenue total, but price, discount, cost and return data are absent. Compare gross margin before shifting inventory or marketing spend.
- **Collect better repeat-customer and product data:** Use stable, privacy-conscious customer keys and product-level identifiers in a future dataset. That would make repeat-purchase, product ranking and customer-value analysis possible.
- **Treat demographic differences as hypotheses:** Validate any age- or gender-based marketing idea with a larger, representative dataset and an appropriate fairness review; this sample alone does not justify segmentation.

## Limitations

The dataset is a small, constructed sample rather than an audited retailer export. It has no documented currency, cost/margin, discount, inventory, return or product-SKU fields. Descriptive patterns do not establish causation, and one year of sample dates is not enough to confirm seasonality.
