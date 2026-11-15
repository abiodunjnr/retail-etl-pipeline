
import sqlite3
from pathlib import Path

import pandas as pd

# Locate SQLite database
project_folder = Path(__file__).resolve().parent.parent
database_path = project_folder / "database" / "retail_sales.db"

if not database_path.is_file():
    raise FileNotFoundError(f"Database not found: {database_path}")

with sqlite3.connect(database_path) as connection:

    # Compare source revenue with Gold revenue
    query = """
    SELECT
        (SELECT COUNT(*)
         FROM sales_transactions) AS silver_transactions,

        (SELECT SUM(total_transactions)
         FROM gold_category_sales) AS gold_transactions,

        (SELECT ROUND(SUM(line_total_gbp), 2)
         FROM sales_transactions) AS silver_revenue,

        (SELECT ROUND(SUM(total_revenue_gbp), 2)
         FROM gold_category_sales) AS gold_revenue;
    """

    results = pd.read_sql_query(query, connection)

    print("\nGOLD VALIDATION RESULTS")
    print(results.to_string(index=False))

    silver_count = results.loc[0, "silver_transactions"]
    gold_count = results.loc[0, "gold_transactions"]

    silver_revenue = results.loc[0, "silver_revenue"]
    gold_revenue = results.loc[0, "gold_revenue"]

    # Validate transaction reconciliation
    assert silver_count == gold_count, (
        "Transaction reconciliation failed"
    )

    # Validate revenue reconciliation
    assert abs(silver_revenue - gold_revenue) <= 0.01, (
        "Revenue reconciliation failed"
    )

    print("\nSUCCESS: Gold reconciliation passed")
