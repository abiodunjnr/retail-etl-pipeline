
import pandas as pd
import sqlite3
from pathlib import Path

# Locate project directory
project_folder = Path(__file__).resolve().parent.parent

# Define Silver and database directories
silver_folder = project_folder / "outputs" / "silver"
database_folder = project_folder / "database"

# Ensure database directory exists
database_folder.mkdir(parents=True, exist_ok=True)

# Define database file
database_path = database_folder / "retail_sales.db"

print("Database destination:", database_path)


# Read validated Silver datasets
customers = pd.read_csv(
    silver_folder / "customers_silver.csv",
    dtype={"customer_id": str}
)

products = pd.read_csv(
    silver_folder / "products_silver.csv",
    dtype={"product_id": str}
)

sales = pd.read_csv(
    silver_folder / "sales_silver.csv",
    dtype={
        "transaction_id": str,
        "order_id": str,
        "customer_id": str,
        "product_id": str
    }
)

print("\nSilver datasets loaded successfully")
print("Customers:", len(customers))
print("Products:", len(products))
print("Sales:", len(sales))



# Check customer and product relationships
invalid_customers = ~sales["customer_id"].isin(
    customers["customer_id"]
)

invalid_products = ~sales["product_id"].isin(
    products["product_id"]
)

invalid_references = invalid_customers | invalid_products

print("\nREFERENTIAL INTEGRITY CHECK")
print("Unknown customer references:", invalid_customers.sum())
print("Unknown product references:", invalid_products.sum())
print("Sales with invalid references:", invalid_references.sum())

# Stop loading if invalid references exist
if invalid_references.any():
    raise ValueError(
        "Sales contain invalid customer or product references. "
        "Investigate and quarantine these records before loading."
    )

print("Referential integrity validated")


# Establish database connection
connection = sqlite3.connect(database_path)

try:
    # Enable foreign key enforcement
    connection.execute("PRAGMA foreign_keys = ON")

    # Load validated DataFrames into SQLite
    customers.to_sql(
        "customers",
        connection,
        if_exists="replace",
        index=False
    )

    products.to_sql(
        "products",
        connection,
        if_exists="replace",
        index=False
    )

    sales.to_sql(
        "sales_transactions",
        connection,
        if_exists="replace",
        index=False
    )

    print("\nSilver datasets loaded into SQLite")

    # Reconcile database row counts
    for table in ["customers", "products", "sales_transactions"]:
        result = pd.read_sql_query(
            f"SELECT COUNT(*) AS total FROM {table}",
            connection
        )
        print(f"{table}: {result['total'].iloc[0]} records")

finally:
    connection.close()

print("\nDATABASE LOAD COMPLETED")
