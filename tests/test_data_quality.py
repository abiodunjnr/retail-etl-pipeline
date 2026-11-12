
from pathlib import Path
import pandas as pd

# Locate the project root directory
project_folder = Path(__file__).resolve().parent.parent

# Locate the validated Silver datasets
silver_folder = project_folder / "outputs" / "silver"


def test_silver_files_exist():
    """Check that all expected Silver datasets exist."""

    expected_files = [
        "customers_silver.csv",
        "products_silver.csv",
        "sales_silver.csv"
    ]

    for filename in expected_files:
        assert (silver_folder / filename).exists(), (
            f"Missing Silver dataset: {filename}"
        )


def test_customer_ids_are_unique():
    """Ensure customer primary keys contain no duplicates."""

    customers = pd.read_csv(
        silver_folder / "customers_silver.csv",
        dtype={"customer_id": str}
    )

    assert customers["customer_id"].is_unique, (
        "Duplicate customer IDs detected"
    )


def test_sales_have_valid_customer_references():
    """Ensure every sales customer exists in the customer dataset."""

    customers = pd.read_csv(
        silver_folder / "customers_silver.csv",
        dtype={"customer_id": str}
    )

    sales = pd.read_csv(
        silver_folder / "sales_silver.csv",
        dtype={"customer_id": str}
    )

    valid_customers = set(customers["customer_id"])

    assert sales["customer_id"].notna().all(), (
        "Sales contain missing customer IDs"
    )

    assert sales["customer_id"].isin(valid_customers).all(), (
        "Sales contain unknown customer references"
    )


def test_sales_have_positive_quantities():
    """Ensure sales quantities are greater than zero."""

    sales = pd.read_csv(silver_folder / "sales_silver.csv")

    assert sales["quantity"].notna().all(), (
        "Sales contain missing quantities"
    )

    assert (sales["quantity"] > 0).all(), (
        "Sales contain invalid quantities"
    )
