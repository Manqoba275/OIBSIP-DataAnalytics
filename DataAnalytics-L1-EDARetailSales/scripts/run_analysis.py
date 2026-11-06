from __future__ import annotations

import argparse
from pathlib import Path
import sys

def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root / "src"))
    from retail_eda import create_visualizations, load_sales_data, write_findings_report

    parser = argparse.ArgumentParser(description="Run the retail sales EDA and export its charts and report.")
    parser.add_argument("--data", type=Path, default=project_root / "data" / "retail_sales_dataset.csv")
    parser.add_argument("--output", type=Path, default=project_root / "screenshots")
    parser.add_argument("--report", type=Path, default=project_root / "reports" / "findings.md")
    args = parser.parse_args()

    _, data, quality = load_sales_data(args.data)
    charts = create_visualizations(data, args.output)
    report = write_findings_report(data, quality, args.report)
    print(f"Loaded {quality['profile']['rows']:,} records; retained {len(data):,} valid transactions.")
    print(f"Removed {quality['cleaning']['duplicate_transaction_ids_removed']} duplicate transaction IDs and excluded {quality['cleaning']['invalid_transactions_excluded']} invalid rows.")
    print(f"Saved {len(charts)} charts to {args.output}")
    print(f"Saved findings to {report}")


if __name__ == "__main__":
    main()
