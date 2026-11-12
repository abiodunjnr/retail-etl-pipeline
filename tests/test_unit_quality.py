
import pandas as pd
import pytest


# Reusable synthetic customer records
@pytest.fixture
def sample_customers():
    return pd.DataFrame({
        "customer_id": ["CUST001", "CUST002", "CUST003"],
        "customer_name": ["John", "Mary", "James"]
    })


# Reusable synthetic sales records
@pytest.fixture
def sample_sales():
    return pd.DataFrame({
        "transaction_id": ["TXN001", "TXN002", "TXN003"],
        "customer_id": ["CUST001", "CUST002", "CUST003"],
        "quantity": [2, 5, 3]
    })


def test_customer_ids_are_unique(sample_customers):
    """Ensure customer IDs are unique."""

    assert sample_customers["customer_id"].is_unique


def test_sales_have_valid_customer_references(
    sample_customers, sample_sales
):
    """Ensure all sales reference existing customers."""

    valid_customers = set(sample_customers["customer_id"])

    assert sample_sales["customer_id"].notna().all()

    assert sample_sales["customer_id"].isin(
        valid_customers
    ).all()


def test_sales_have_positive_quantities(sample_sales):
    """Ensure sales quantities are greater than zero."""

    assert sample_sales["quantity"].notna().all()

    assert (sample_sales["quantity"] > 0).all()


def test_invalid_customer_reference_is_detected(
    sample_customers, sample_sales
):
    """Verify that an unknown customer reference is detected."""

    invalid_sales = sample_sales.copy()

    invalid_sales.loc[0, "customer_id"] = "CUST999"

    valid_customers = set(sample_customers["customer_id"])

    assert not invalid_sales["customer_id"].isin(
        valid_customers
    ).all()
