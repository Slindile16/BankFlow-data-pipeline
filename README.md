# BankFlow

BankFlow is a Python and Pandas data engineering project that ingests fictional banking data, validates records, and standardises accepted data for downstream use.

The repository includes CSV and JSON ingestion, record validation, transformations for all five datasets, an end-to-end command that writes processed and rejected CSV files, and a command for loading processed data into PostgreSQL. Analytics are planned next.

**Status:** Ingestion, validation, transformation, and processed/rejected CSV output are implemented. PostgreSQL schema creation and loading are optional and implemented. The test suite passes, and the sample data has been loaded and verified in PostgreSQL.

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
 PostgreSQL loading (implemented)
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

Rejected records are returned separately with rejection reasons and written to `data/rejected/` as CSV files. Accepted and transformed records are written to `data/processed/`, with one output file per dataset.

Accepted records can be transformed to standardise dates, province names, account types, transaction categories, payment statuses, and monetary values before downstream use.

## PostgreSQL Database Model

| Table | Purpose | Key Relationships |
| --- | --- | --- |
| `customers` | Stores clean customer records | `customer_id` as the primary key |
| `accounts` | Stores account details | References `customers` through `customer_id` |
| `branches` | Stores branch details | Referenced by accounts and transactions through `branch_id` |
| `transactions` | Stores transaction records | References `accounts` and `branches` |
| `payments` | Stores payment records | References `accounts` through `account_id` |

The PostgreSQL table definitions and integrity constraints are in [sql/schema.sql](sql/schema.sql).

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
|   |-- processed/           # Generated accepted and transformed outputs
|   `-- rejected/            # Generated rejected outputs with reasons
|-- docs/
|   `-- data_dictionary.md
|-- logs/                    # Future runtime logs (generated files ignored)
|-- sql/
|   `-- schema.sql            # PostgreSQL tables and integrity constraints
|-- src/
|   `-- bankflow/
|       |-- __init__.py
|       |-- data_ingestor.py  # CSV and JSON ingestion
|       |-- data_validator.py # Validation and rejection reasons
|       |-- data_transformer.py # Standardisation of accepted records
|       |-- database_loader.py # Load processed CSVs into PostgreSQL
|       `-- pipeline.py       # End-to-end run and CSV output writing
|-- tests/
|   |-- conftest.py
|   |-- test_data_ingestor.py
|   |-- test_data_validator.py
|   |-- test_data_transformer.py
|   |-- test_pipeline.py
|   `-- test_database_loader.py
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
- [X] Design the PostgreSQL schema.
- [X] Implement loading processed data into PostgreSQL.
- [X] Load and verify the sample datasets in PostgreSQL.
- [ ] Create analytical SQL queries and summary tables.
- [X] Add tests for ingestion, validation, transformation, and pipeline outputs.
- [ ] Add logging and stronger runtime error handling.
- [ ] Schedule the pipeline and containerise the application.
- [ ] Add an optional reporting layer and complete documentation.

## Getting Started

Inspect the five fictional source files in `data/raw/` and the
[data dictionary](docs/data_dictionary.md), which documents fields, relationships,
normalisation cases and intentional invalid records. The fixtures contain 68 records.

PostgreSQL is optional. The core pipeline and tests run without installing or
starting a database; they read the fictional files in `data/raw/` and write CSVs
to `data/processed/` and `data/rejected/`. Follow steps 2–5 only if you want to
store the processed data in PostgreSQL. BankFlow does not require users to turn
off Windows security settings.

### 1. Create the Python environment

Run these commands from the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

The project requires Python 3.12 or newer. The `dev` extra installs pytest.
If PowerShell blocks the activation script, skip activation and use
`.\.venv\Scripts\python.exe` instead of `python` for the commands below.

### Core CSV pipeline (no database required)

Run the pipeline and test suite without installing PostgreSQL:

```powershell
python -m bankflow.pipeline
python -m pytest -v
```

The pipeline writes processed and rejected CSV files. Creating and querying
PostgreSQL tables requires access to a PostgreSQL server, either local or hosted.

### 2. Optional: Install and start PostgreSQL on Windows

Download the Windows x86-64 interactive installer from the
[official PostgreSQL Windows page](https://www.postgresql.org/download/windows/).
Keep PostgreSQL Server, Command Line Tools, and pgAdmin selected. The commands
below assume PostgreSQL 18 was installed in its default location. If your
installed version differs, update `18` in `$pgBin`, `$pgData`, and the service
name in the commands.

```powershell
$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$pgData = "C:\Program Files\PostgreSQL\18\data"
Get-Service -Name postgresql-x64-18
```

If the service is stopped, open PowerShell as administrator (Start, search for
PowerShell, right-click it, and select **Run as administrator**) and start it:

```powershell
Start-Service -Name postgresql-x64-18
Get-Service -Name postgresql-x64-18
```

The service status should show `Running`. If the installer initialized the data
directory but did not register the service, register it once from administrator
PowerShell, then start it:

```powershell
& "$pgBin\pg_ctl.exe" register -N "postgresql-x64-18" -U "NT AUTHORITY\NetworkService" -D $pgData -w
Start-Service -Name postgresql-x64-18
```

If Windows blocks `pg_ctl.exe` with an application-control policy message, keep
your security settings on and skip the local database setup unless you choose a
trusted, approved way to run PostgreSQL. You can still run the BankFlow pipeline
and tests without a database.

### 3. Create the database and tables

From the repository root, create the `bankflow` database once. If it already
exists, skip this command. Enter the PostgreSQL `postgres` user's password when
prompted:

```powershell
& "$pgBin\createdb.exe" -U postgres bankflow
```

Apply the schema. It creates the five tables and their keys and constraints:

```powershell
& "$pgBin\psql.exe" -U postgres -d bankflow -f ".\sql\schema.sql"
```

Check that the tables exist:

```powershell
& "$pgBin\psql.exe" -U postgres -d bankflow -c "\dt"
```

### 4. Process and optionally load the data

Generate accepted, transformed CSVs and rejected CSVs with rejection reasons:

```powershell
python -m bankflow.pipeline
```

Load the accepted, transformed CSVs into PostgreSQL. The loader prompts for the
password without displaying it. It loads parent tables before dependent tables
in one transaction; rerunning it updates rows with matching IDs.

```powershell
python -m pip install -e ".[dev,database]"
python -m bankflow.database_loader
```

The default connection is `localhost:5432`, database `bankflow`, user `postgres`.
Override the connection settings in the current PowerShell session if needed:

```powershell
$env:BANKFLOW_DB_HOST = "localhost"
$env:BANKFLOW_DB_PORT = "5432"
$env:BANKFLOW_DB_NAME = "bankflow"
$env:BANKFLOW_DB_USER = "postgres"
```

### 5. Verify the database rows

List the tables:

```powershell
& "$pgBin\psql.exe" -U postgres -d bankflow -c "\dt"
```

Check the accepted sample-record counts:

```powershell
& "$pgBin\psql.exe" -U postgres -d bankflow -c "SELECT 'branches' AS dataset, COUNT(*) FROM branches UNION ALL SELECT 'customers', COUNT(*) FROM customers UNION ALL SELECT 'accounts', COUNT(*) FROM accounts UNION ALL SELECT 'transactions', COUNT(*) FROM transactions UNION ALL SELECT 'payments', COUNT(*) FROM payments;"
```

Expected counts are 5 branches, 10 customers, 10 accounts, 12 transactions,
and 5 payments. Rejected records remain in `data/rejected/`; the loader imports
only accepted data from `data/processed/`.

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
