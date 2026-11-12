
import sqlite3
from pathlib import Path
import pandas as pd

# Locate the root project directory
project_folder = Path(__file__).resolve().parent.parent

# Locate the SQLite database
database_path = project_folder / "database" / "retail_sales.db"

# Confirm the database exists before connecting
if not database_path.is_file():
    raise FileNotFoundError(f"Database not found: {database_path}")

# Establish a connection
connection = sqlite3.connect(database_path)

print("Connected to Sqlite database successfully")



# Analyse sales revenue by product category
category_sales_query = """
SELECT
    p.category AS product_category,
    COUNT(DISTINCT s.transaction_id) AS total_transactions,
    SUM(s.quantity) AS units_sold,
    ROUND(SUM(s.line_total_gbp), 2) AS total_revenue_gbp,
    ROUND( SUM(s.line_total_gbp) / NULLIF(SUM(s.quantity), 0),2) AS average_selling_price_gbp
FROM sales_transactions AS s
INNER JOIN products AS p
    ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue_gbp DESC;
"""

# Execute the SQL query and return the results
category_sales = pd.read_sql_query(category_sales_query, connection)

print("\nGOLD: REVENUE BY PRODUCT CATEGORY")
print(category_sales.to_string(index=False)) 



# Persist the Gold analytical results into SQLite
category_sales.to_sql(
    "gold_category_sales",
    connection,
    if_exists="replace",
    index=False
)

# Reconcile source and Gold totals
reconciliation_query = """
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

reconciliation = pd.read_sql_query(
    reconciliation_query,
    connection
)

print("\nGOLD RECONCILIATION")
print(reconciliation.to_string(index=False))

# Validate transaction counts
assert (
    reconciliation["silver_transactions"].iloc[0]
    == reconciliation["gold_transactions"].iloc[0]
), "Transaction count mismatch"

# Allow a small rounding difference across categories
revenue_difference = abs(
    reconciliation["silver_revenue"].iloc[0]
    - reconciliation["gold_revenue"].iloc[0]
)

assert revenue_difference <= 0.01, "Revenue mismatch"

print("\nGOLD RECONCILIATION PASSED")
connection.close()