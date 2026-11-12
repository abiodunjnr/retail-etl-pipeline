import pandas as pd
from pathlib import Path

# Locate the project data directory
project_folder = Path(__file__).resolve().parent.parent
data_folder = project_folder / "data"

# Extract source CSV datasets
customers = pd.read_csv(data_folder / "customers.csv")
products = pd.read_csv(data_folder / "products.csv")
sales = pd.read_csv(data_folder / "sales_transactions.csv")

# Verify extraction
print("DATA EXTRACTION COMPLETED")

print("\nCustomers:", len(customers))
print("Products:", len(products))
print("Sales Transactions:", len(sales))

# Inspect source schemas
print("\nCUSTOMER COLUMNS")
print(customers.columns.tolist())

print("\nPRODUCT COLUMNS")
print(products.columns.tolist())

print("\nSALES COLUMNS")
print(sales.columns.tolist())