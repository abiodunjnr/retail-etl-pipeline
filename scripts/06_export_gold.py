
import csv
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "retail_sales.db"
EXPORT_DIR = PROJECT_ROOT / "outputs" / "powerbi"
EXPORT_PATH = EXPORT_DIR / "gold_category_sales.csv"


def export_gold():
    """Export the validated Gold category table for Power BI."""

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Retail database not found: {DB_PATH}"
        )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("""
            SELECT
                product_category,
                total_transactions,
                units_sold,
                total_revenue_gbp,
                average_selling_price_gbp
            FROM gold_category_sales
            ORDER BY total_revenue_gbp DESC
        """)

        columns = [column[0] for column in cursor.description]
        records = cursor.fetchall()

    if not records:
        raise ValueError("Gold table is empty. Export cancelled.")

    with EXPORT_PATH.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(records)

    print(f"Power BI export completed: {EXPORT_PATH}")
    print(f"Categories exported: {len(records)}")


if __name__ == "__main__":
    export_gold()
