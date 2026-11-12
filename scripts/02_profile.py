from pathlib import Path
import pandas as pd

# Identify the project directory
project_folder = Path(__file__).resolve().parent.parent
data_folder = project_folder / "data"

# Read source datasets
customers = pd.read_csv(data_folder / "customers.csv")
products = pd.read_csv(data_folder / "products.csv")
sales = pd.read_csv(data_folder / "sales_transactions.csv")

# Inspect missing values and duplicate primary keys
datasets = {
    "Customers": (customers, "customer_id"),
    "Products": (products, "product_id"),
    "Sales": (sales, "transaction_id")
}

for name, (df, primary_key) in datasets.items():
    print(f"\n--- {name.upper()} DATA QUALITY ---")
    print("Total records:", len(df))
    print("Missing values:")
    print(df.isna().sum().to_string())
    print("Duplicate primary keys:", df[primary_key].duplicated().sum())
    print("Data types:")
    print(df.dtypes.to_string())



# Investigate duplicate transaction identifiers

duplicate_transactions = sales[
    sales.duplicated(subset=["transaction_id"], keep=False)
].sort_values("transaction_id")

print("\nDUPLICATE TRANSACTION INVESTIGATION")
print(duplicate_transactions.to_string(index=False))

print("\nExact duplicate rows:")
print(sales.duplicated().sum())

print("\nConflicting duplicate groups:")

for transaction_id, group in duplicate_transactions.groupby("transaction_id"):
    if len(group.drop_duplicates()) > 1:
        print(f"Transaction {transaction_id}: conflicting records")




# Investigate transactions with missing dates

missing_dates = sales[
    sales["transaction_date"].isna()
]

print("\nTRANSACTIONS WITH MISSING DATES")
print(missing_dates.to_string(index=False))

print("\nOrder status distribution:")
print(missing_dates["order_status"].value_counts(dropna=False))
