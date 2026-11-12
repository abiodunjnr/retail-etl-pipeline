
import pandas as pd
from pathlib import Path

# Locate the root project folder
project_folder = Path(__file__).resolve().parent.parent

# Define source and destination folders
data_folder = project_folder / "data"
silver_folder = project_folder / "outputs" / "silver"
quarantine_folder = project_folder / "outputs" / "quarantine"

# Extract the three source datasets
customers = pd.read_csv(data_folder / "customers.csv", dtype={"customer_id": str})
products = pd.read_csv(data_folder / "products.csv", dtype={"product_id": str})
sales = pd.read_csv(
    data_folder / "sales_transactions.csv",
    dtype={"transaction_id": str, "order_id": str,
           "customer_id": str, "product_id": str}
)

print("Source datasets loaded successfully")



# Work on a copy of the raw data
customers_clean = customers.copy()

# Standardise text fields
customers_clean["preferred_channel"] = (
    customers_clean["preferred_channel"]
    .astype("string")
    .str.strip()
    .fillna("Unknown")
    .replace("", "Unknown")
)

# Convert registration dates to datetime
customers_clean["registration_date"] = pd.to_datetime(
    customers_clean["registration_date"],
    errors="coerce"
)

# Identify invalid customer records
invalid_customer_id = (
    customers_clean["customer_id"].isna()
    | customers_clean["customer_id"].str.strip().eq("")
)

duplicate_customer_id = customers_clean.duplicated(
    subset=["customer_id"], keep=False
)

invalid_registration_date = customers_clean[
    "registration_date"
].isna()

customer_reasons = pd.DataFrame(index=customers_clean.index)
customer_reasons["missing_customer_id"] = invalid_customer_id
customer_reasons["duplicate_customer_id"] = duplicate_customer_id
customer_reasons["invalid_registration_date"] = invalid_registration_date

customer_reject = customer_reasons.any(axis=1)

customers_quarantine = customers_clean.loc[customer_reject].copy()
customers_silver = customers_clean.loc[~customer_reject].copy()


# Create rejection reasons safely, even if no records fail
customers_quarantine["rejection_reason"] = [
    "; ".join(
        reason for reason, failed in row.items() if failed
    )
    for _, row in customer_reasons.loc[customer_reject].iterrows()
]


print("Customers accepted:", len(customers_silver))
print("Customers quarantined:", len(customers_quarantine))


# Work on a copy of the raw product data
products_clean = products.copy()

# Ensure numerical fields have correct data types
numeric_columns = [
    "unit_price_gbp",
    "unit_cost_gbp",
    "stock_quantity",
    "reorder_level"
]

for column in numeric_columns:
    products_clean[column] = pd.to_numeric(
        products_clean[column],
        errors="coerce"
    )

# Define validation rules
invalid_product_id = (
    products_clean["product_id"].isna()
    | products_clean["product_id"].str.strip().eq("")
)

duplicate_product_id = products_clean.duplicated(
    subset=["product_id"], keep=False
)

invalid_price = (
    products_clean["unit_price_gbp"].isna()
    | products_clean["unit_price_gbp"].le(0)
)

invalid_cost = (
    products_clean["unit_cost_gbp"].isna()
    | products_clean["unit_cost_gbp"].lt(0)
)

invalid_stock = (
    products_clean["stock_quantity"].isna()
    | products_clean["stock_quantity"].lt(0)
    | products_clean["stock_quantity"].mod(1).ne(0)
)

invalid_reorder = (
    products_clean["reorder_level"].isna()
    | products_clean["reorder_level"].lt(0)
    | products_clean["reorder_level"].mod(1).ne(0)
)

product_reasons = pd.DataFrame(index=products_clean.index)
product_reasons["missing_product_id"] = invalid_product_id
product_reasons["duplicate_product_id"] = duplicate_product_id
product_reasons["invalid_price"] = invalid_price
product_reasons["invalid_cost"] = invalid_cost
product_reasons["invalid_stock"] = invalid_stock
product_reasons["invalid_reorder_level"] = invalid_reorder

product_reject = product_reasons.any(axis=1)

products_quarantine = products_clean.loc[product_reject].copy()
products_silver = products_clean.loc[~product_reject].copy()

products_quarantine["rejection_reason"] = [
    "; ".join(
        reason for reason, failed in row.items() if failed
    )
    for _, row in product_reasons.loc[product_reject].iterrows()
]

print("Products accepted:", len(products_silver))
print("Products quarantined:", len(products_quarantine))



#Work on a copy of the raw sales data
sales_clean = sales.copy()

# Standardise missing sales channels
sales_clean["sales_channel"] = (
    sales_clean["sales_channel"]
    .astype("string")
    .str.strip()
    .fillna("Unknown")
    .replace("", "Unknown")
)

# Convert transaction dates
sales_clean["transaction_date"] = pd.to_datetime(
    sales_clean["transaction_date"],
    errors="coerce"
)

# Standardise numeric columns
for column in [
    "quantity", "unit_price_gbp",
    "discount_pct", "line_total_gbp"
]:
    sales_clean[column] = pd.to_numeric(
        sales_clean[column],
        errors="coerce"
    )

# Validate primary keys
invalid_transaction_id = (
    sales_clean["transaction_id"].isna()
    | sales_clean["transaction_id"].str.strip().eq("")
)

duplicate_transaction_id = sales_clean.duplicated(
    subset=["transaction_id"], keep=False
)

# Validate business-critical fields
invalid_date = sales_clean["transaction_date"].isna()

invalid_quantity = (
    sales_clean["quantity"].isna()
    | sales_clean["quantity"].le(0)
    | sales_clean["quantity"].mod(1).ne(0)
)

invalid_price = (
    sales_clean["unit_price_gbp"].isna()
    | sales_clean["unit_price_gbp"].le(0)
)

invalid_discount = (
    sales_clean["discount_pct"].isna()
    | ~sales_clean["discount_pct"].between(0, 1)
)

invalid_total = (
    sales_clean["line_total_gbp"].isna()
    | sales_clean["line_total_gbp"].lt(0)
)

# Check customer and product relationships
invalid_customer_ref = ~sales_clean["customer_id"].isin(
    customers_silver["customer_id"]
)

invalid_product_ref = ~sales_clean["product_id"].isin(
    products_silver["product_id"]
)

# Collect all validation results
sales_reasons = pd.DataFrame(index=sales_clean.index)

sales_reasons["missing_transaction_id"] = invalid_transaction_id
sales_reasons["duplicate_transaction_id"] = duplicate_transaction_id
sales_reasons["invalid_date"] = invalid_date
sales_reasons["invalid_quantity"] = invalid_quantity
sales_reasons["invalid_price"] = invalid_price
sales_reasons["invalid_discount"] = invalid_discount
sales_reasons["invalid_total"] = invalid_total
sales_reasons["invalid_customer_ref"] = invalid_customer_ref
sales_reasons["invalid_product_ref"] = invalid_product_ref

sales_reject = sales_reasons.any(axis=1)

sales_quarantine = sales_clean.loc[sales_reject].copy()
sales_silver = sales_clean.loc[~sales_reject].copy()


sales_quarantine["rejection_reason"] = [
    "; ".join(
        reason for reason, failed in row.items() if failed
    )
    for _, row in sales_reasons.loc[sales_reject].iterrows()
]

print("Sales accepted:", len(sales_silver))
print("Sales quarantined:", len(sales_quarantine))




# Save validated Silver datasets
customers_silver.to_csv(
    silver_folder / "customers_silver.csv",
    index=False
)

products_silver.to_csv(
    silver_folder / "products_silver.csv",
    index=False
)

sales_silver.to_csv(
    silver_folder / "sales_silver.csv",
    index=False
)

# Save quarantined records
customers_quarantine.to_csv(
    quarantine_folder / "customers_quarantine.csv",
    index=False
)

products_quarantine.to_csv(
    quarantine_folder / "products_quarantine.csv",
    index=False
)

sales_quarantine.to_csv(
    quarantine_folder / "sales_quarantine.csv",
    index=False
)

# Reconcile source and output row counts
for name, source, accepted, rejected in [
    ("Customers", customers, customers_silver, customers_quarantine),
    ("Products", products, products_silver, products_quarantine),
    ("Sales", sales, sales_silver, sales_quarantine)
]:
    assert len(source) == len(accepted) + len(rejected)

    print(
        f"{name}: Source={len(source)}, "
        f"Silver={len(accepted)}, "
        f"Quarantine={len(rejected)}"
    )

print("\nSILVER AND QUARANTINE EXPORT COMPLETED")



# STEP 7: SAVE SILVER AND QUARANTINE DATASETS

# Create output directories if they do not exist
silver_folder.mkdir(parents=True, exist_ok=True)
quarantine_folder.mkdir(parents=True, exist_ok=True)

# Save validated Silver datasets
customers_silver.to_csv(
    silver_folder / "customers_silver.csv",
    index=False
)

products_silver.to_csv(
    silver_folder / "products_silver.csv",
    index=False
)

sales_silver.to_csv(
    silver_folder / "sales_silver.csv",
    index=False
)

# Save rejected records for investigation
customers_quarantine.to_csv(
    quarantine_folder / "customers_quarantine.csv",
    index=False
)

products_quarantine.to_csv(
    quarantine_folder / "products_quarantine.csv",
    index=False
)

sales_quarantine.to_csv(
    quarantine_folder / "sales_quarantine.csv",
    index=False
)

print("\nSILVER AND QUARANTINE DATASETS SAVED SUCCESSFULLY")
