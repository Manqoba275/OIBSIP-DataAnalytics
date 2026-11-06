import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from retail_eda import (  # noqa: E402
    build_findings,
    create_visualizations,
    load_sales_data,
    prepare_sales_data,
    summarize_sales,
    write_findings_report,
)


class RetailAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.data, cls.quality = load_sales_data(
            PROJECT_ROOT / "data" / "retail_sales_dataset.csv"
        )

    def test_source_dataset_has_expected_size_and_columns(self):
        self.assertEqual(self.raw.shape, (1000, 9))
        self.assertIn("product_category", self.data.columns)
        self.assertIn("age_group", self.data.columns)

    def test_source_rows_are_valid_and_amounts_reconcile(self):
        self.assertEqual(len(self.data), 1000)
        self.assertEqual(self.quality["cleaning"]["amount_mismatches"], 0)
        self.assertTrue((self.data["quantity"] > 0).all())
        self.assertTrue((self.data["price_per_unit"] > 0).all())

    def test_cleaning_keeps_unknown_demographics_and_removes_bad_rows(self):
        dirty = pd.DataFrame([
            [1, "2023-01-02", "C1", " female ", 30, " clothing ", 2, 5, 10],
            [1, "2023-01-02", "C1", "female", 30, "clothing", 2, 5, 10],
            [2, "2023-01-03", None, None, None, None, 1, 5, 5],
            [3, "not-a-date", "C3", "Male", 40, "Beauty", 1, 5, 5],
        ], columns=self.raw.columns)
        cleaned, report = prepare_sales_data(dirty)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(cleaned.iloc[0]["gender"], "Female")
        self.assertEqual(cleaned.iloc[1]["gender"], "Unknown")
        self.assertEqual(cleaned.iloc[1]["age_group"], "Unknown")
        self.assertEqual(report["duplicate_transaction_ids_removed"], 1)
        self.assertEqual(report["invalid_transactions_excluded"], 1)

    def test_summary_and_recommendation_fields_are_derived(self):
        summary = summarize_sales(self.data)
        findings = build_findings(self.data)
        self.assertEqual(summary["transactions"], 1000)
        self.assertGreater(summary["revenue"], 0)
        self.assertIn(findings["top_category"]["product_category"], self.data["product_category"].unique())
        self.assertIn("partial_months_excluded", findings)

    def test_report_states_dataset_limits(self):
        target = PROJECT_ROOT / "reports" / "test_findings.md"
        write_findings_report(self.data, self.quality, target)
        text = target.read_text(encoding="utf-8")
        self.assertIn("constructed sample", text)
        self.assertIn("not specified", text)
        self.assertIn("Recommendations", text)
        target.unlink()

    def test_chart_export_produces_all_required_figures(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            charts = create_visualizations(self.data, temp_dir)
            self.assertEqual(len(charts), 9)
            self.assertTrue(all(path.suffix == ".svg" and path.stat().st_size > 500 for path in charts))
            self.assertIn("<svg", charts[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
