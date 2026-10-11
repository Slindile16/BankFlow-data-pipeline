# BankFlow

BankFlow is a Python and Pandas data engineering project that ingests fictional banking data, validates records, and standardises accepted data for downstream use.

The repository includes CSV and JSON ingestion, record validation, transformations for all five datasets, and an end-to-end command that writes processed and rejected CSV files. PostgreSQL loading and analytics are planned next.

**Status:** Ingestion, validation, transformation, and processed/rejected output writing are implemented. The component test suite passes.

## Project Objectives

- Build an end-to-end ETL pipeline using Python and Pandas.
- Ingest banking data from CSV and JSON files.
- Detect invalid, incomplete and duplicate records.
- Quarantine rejected records with clear rejection reasons.
- Standardise data for consistent storage and analysis.
- Preserve relationships between customers, accounts, transactions and branches.
- Produce analytical datasets and data quality summaries.

## The Problem

Banking data can arrive with missing identifiers, duplicate transactions, inconsistent dates, invalid amounts and references to accounts that do not exist.

BankFlow will address these issues through explicit validation and transformation rules, helping prevent invalid records from entering trusted datasets.

## Pipeline Status

```text
Raw Data (CSV / JSON)
        |
        v
     Ingestion (implemented)
        |
        v
     Validation (implemented) ------> Rejected DataFrames + Reasons
        |
        v
Cleaning & Transformation (implemented)
        |
        v
  CSV output writing (implemented)
        |
        v
 PostgreSQL (planned)
        |
        v
Optional Dashboard
```

## Data Sources

All data used in this project will be fictional.

| File | Description |
| --- | --- |
| `customers.csv` | Customer identifiers, names, provinces and join dates |
| `accounts.csv` | Account identifiers, customer relationships, account types and balances |
| `transactions.csv` | Deposits, withdrawals, transfers and card payments |
| `branches.csv` | Branch identifiers, names and locations |
| `payments.json` | Payment records demonstrating JSON ingestion |

## Data Quality and Transformation

The validator checks:

- Required fields and identifiers.
- Duplicate records and transactions.
- Date formats and validity.
- Numeric values and transaction amounts.
- Account references and relationships between records.

Rejected records are returned separately with rejection reasons. Writing them to files is part of the planned pipeline orchestration.

Accepted records can be transformed to standardise dates, province names, account types, transaction categories, payment statuses, and monetary values before downstream use.

## Planned Database Model

| Table | Purpose | Key Relationships |
| --- | --- | --- |
| `customers` | Stores clean customer records | `customer_id` as the primary key |
| `accounts` | Stores account details | References `customers` through `customer_id` |
| `transactions` | Stores transaction records | References `accounts` through `account_id` |
| `branches` | Stores branch details | Referenced by relevant accounts and transactions |

The detailed schema and handling of payment records will be defined during database design.

## Analytics

The project will support questions such as:

- How many transactions occur each day and by transaction type?
- Which branches process the highest transaction volumes?
- How does customer growth change over time?
- Where are customers located?
- How many records are rejected, and what are the most common reasons?

Optional rule-based anomaly flags may highlight unusually large transactions. These will demonstrate basic analytical rules, not real fraud detection.

## Technology Stack

| Area | Planned Technology |
| --- | --- |
| Programming | Python |
| Data processing | Pandas |
| Database | PostgreSQL |
| Analytics | SQL |
| Testing | pytest |
| Scheduling and orchestration | Apache Airflow — later stage |
| Containers | Docker |
| Version control | Git and GitHub |
| Optional reporting | Power BI, Metabase or a simple dashboard |

## Project Structure

```text
BankFlow-data-pipeline/
|-- data/
|   |-- raw/
|   |   |-- accounts.csv
|   |   |-- branches.csv
|   |   |-- customers.csv
|   |   |-- payments.json
|   |   `-- transactions.csv
|   |-- processed/           # Reserved for generated clean outputs
|   `-- rejected/            # Reserved for generated rejected outputs
|-- docs/
|   `-- data_dictionary.md
|-- logs/                    # Future runtime logs (generated files ignored)
|-- sql/                     # Future schema and analytical queries
|-- src/
|   `-- bankflow/
|       |-- __init__.py
|       |-- data_ingestor.py  # CSV and JSON ingestion
|       |-- data_validator.py # Validation and rejection reasons
|       |-- data_transformer.py # Standardisation of accepted records
|       `-- pipeline.py       # End-to-end run and CSV output writing
|-- tests/
|   |-- conftest.py
|   |-- test_data_ingestor.py
|   |-- test_data_validator.py
|   |-- test_data_transformer.py
|   `-- test_pipeline.py
|-- .gitignore
|-- pyproject.toml           # Dependencies, packaging and pytest configuration
`-- README.md
```

## Roadmap

- [X] Create the repository, project structure and fictional datasets.
- [X] Implement CSV and JSON ingestion.
- [X] Validate records, detect duplicates, and return rejected rows with reasons.
- [X] Implement cleaning and transformation rules for all five datasets.
- [X] Add end-to-end orchestration and write processed and rejected outputs.
- [ ] Design the PostgreSQL schema and load validated data.
- [ ] Create analytical SQL queries and summary tables.
- [X] Add tests for ingestion, validation, transformation, and pipeline outputs.
- [ ] Add logging and stronger runtime error handling.
- [ ] Schedule the pipeline and containerise the application.
- [ ] Add an optional reporting layer and complete documentation.

## Getting Started

Inspect the five fictional source files in `data/raw/` and the
[data dictionary](docs/data_dictionary.md), which documents fields, relationships,
normalisation cases and intentional invalid records. The fixtures contain 68 records.

Install the project and development dependencies in a virtual environment:

```powershell
python -m pip install -e ".[dev]"
```

Run the complete pipeline from the project root after installation:

```powershell
python -m bankflow.pipeline
```

The command reads `data/raw/`, writes accepted and transformed records to `data/processed/`, and writes rejected source rows with JSON-formatted reasons to `data/rejected/`. Each folder receives one CSV per dataset.

## Running Tests

From the project root, with your virtual environment active and development
dependencies installed, run the full test suite:

```powershell
python -m pytest -v
```

If the virtual environment is not active, use its Python executable explicitly:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

`tests/conftest.py` creates a fresh temporary folder for each test run and cleans
it up afterward. Pytest caching is disabled in `pyproject.toml` to avoid the
shared-folder permission issues encountered on Windows.

## Planned Demonstration

The planned demonstration will follow data through the full pipeline:

1. Inspect fictional raw data containing intentional quality issues.
2. Run `python -m bankflow.pipeline` to ingest, validate, transform, and write outputs.
3. Review rejected records and their rejection reasons.
4. Inspect clean, related tables in PostgreSQL.
5. Run analytical SQL queries.
6. Present summaries or an optional dashboard.

## Skills Demonstrated

ETL development, data quality validation, Python data processing, relational modelling, SQL, PostgreSQL, automated testing, logging, error handling, orchestration and preparation of data for downstream analytics.

## Data Privacy

This project uses fictional banking data for educational and portfolio purposes. Real customer information, banking credentials and sensitive financial records must not be committed to the repository.
