
# Retail Sales ETL & Data Quality Pipeline

## Project Overview

An end-to-end retail data engineering project built using 
Python, pandas, SQL and SQLite.

The pipeline extracts synthetic retail datasets, applies
data quality and transformation rules, quarantines invalid
records, and loads validated data into a relational database.

SQL is then used to create analytical outputs for retail
revenue and product performance reporting.

## Technology Stack

- Python 3.11
- pandas and NumPy
- SQLite and SQL
- Visual Studio Code
- Git and GitHub

## Data Sources

Three synthetic retail datasets:

1. customers.csv - 500 customer records
2. products.csv - 150 product records
3. sales_transactions.csv - 5,000 sales records

## Pipeline Architecture

Source CSV Files
       |
       v
Python Extraction
       |
       v
Data Profiling & Validation
       |
       v
Transformation & Cleaning
       |
       +----> Quarantine (Rejected Records)
       |
       v
Silver (Validated CSV Files)
       |
       v
Referential Integrity Checks
       |
       v
SQLite Relational Database
       |
       v
SQL Gold Analytical Outputs

## Data Quality

The pipeline includes:

- Missing-value detection
- Duplicate primary-key checks
- Data type validation
- Invalid date handling
- Business-rule validation
- Rejected-record quarantine
- Referential integrity checks
- Source-to-output row-count reconciliation

## Validated Data Results

| Dataset | Source | Accepted | Quarantined |
|---|---:|---:|---:|
| Customers | 500 | 500 | 0 |
| Products | 150 | 148 | 2 |
| Sales | 5,000 | 4,839 | 161 |

## Project Structure

- data/ - Source CSV files
- scripts/ - Python ETL scripts
- outputs/silver/ - Validated datasets
- outputs/quarantine/ - Rejected records
- database/ - SQLite database
- requirements.txt - Python dependencies

## Getting Started

Create a Python virtual environment:

    python3 -m venv .venv

Activate the environment on macOS:

    source .venv/bin/activate

Install dependencies:

    python -m pip install -r requirements.txt

Place the three source CSV files inside the data folder.

Run the pipeline scripts in order:

    python scripts/01_extract.py
    python scripts/02_profile.py
    python scripts/02_transform.py
    python scripts/03_load.py
    python scripts/04_gold.py

## Future Enhancements

- Automated testing using pytest
- GitHub Actions CI/CD workflows
- Git branching and pull request reviews
- Web-based ETL execution and monitoring dashboard
- Pipeline logging and execution history

## Data Disclaimer

All retail datasets used in this project are synthetic and intended for engineering demonstration purposes.
