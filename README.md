# BankFlow

BankFlow is a Python and Pandas data engineering project that ingests fictional banking data, validates records, and standardises accepted data for downstream use.

The repository includes CSV and JSON ingestion, record validation, transformations for all five datasets, an end-to-end command that writes processed and rejected CSV files, a command for loading processed data into PostgreSQL, PostgreSQL analytical views, scheduling, Docker support, and runtime logging.

**Status:** Ingestion, validation, transformation, processed/rejected CSV output, optional PostgreSQL loading, analytical views, scheduling, containers, and runtime logging are implemented. The test suite passes, and the sample data has been loaded and verified in PostgreSQL.

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

BankFlow addresses these issues through explicit validation and transformation rules, helping prevent invalid records from entering trusted datasets.

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
Optional reporting layer (planned)
```

## Data Sources

All data used in this project is fictional.

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
Analytical summary views are defined in [sql/analytics.sql](sql/analytics.sql).

## Analytics

The analytical views answer questions such as:

- How many transactions occur each day and by transaction type?
- Which branches process the highest transaction volumes?
- How does customer growth change over time?
- Where are customers located?
Rejected rows and their reasons are written to CSV files; they are not included
in the PostgreSQL analytical views. Anomaly detection is not implemented. The
large T011 deposit is valid sample data and must not be automatically rejected.

Apply the analytics views after creating the database tables. The
platform-specific commands are listed in the Windows and Linux setup sections
under Getting Started.

The script can be applied again safely. It creates or replaces these views:

| View | Summary |
| --- | --- |
| `daily_transaction_summary` | Transaction count, distinct accounts, and amounts by date and type |
| `branch_transaction_summary` | Transaction volume and amounts by branch, including branches with no transactions |
| `monthly_customer_growth` | New signups and cumulative customer count by month |
| `customer_province_summary` | Customer counts and percentage by province |
| `monthly_payment_summary` | Payment counts and amounts by month and status |

For example, query a summary with the platform-specific commands in the
Getting Started section.

These are views rather than stored summary tables, so they stay in sync with the
underlying tables whenever the loader adds or updates records. Rejected records
are kept in CSV files and are not included in these database summaries.

## Technology Stack

| Area | Technology |
| --- | --- |
| Programming | Python |
| Data processing | Pandas |
| Database | PostgreSQL |
| Analytics | SQL |
| Testing | pytest |
| Scheduling and orchestration | APScheduler daily cron job |
| Containers | Docker |
| Version control | Git and GitHub |
| Optional reporting | Planned |

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
|   |-- data_dictionary.md    # Source fields, rules and fixture cases
|   `-- operations.md         # Runtime configuration and troubleshooting
|-- logs/                    # Generated runtime logs (ignored by Git)
|-- sql/
|   |-- schema.sql            # PostgreSQL tables and integrity constraints
|   `-- analytics.sql         # Analytical summary views
|-- src/
|   `-- bankflow/
|       |-- __init__.py
|       |-- logging_config.py # Shared console and rotating-file logging setup
|       |-- data_ingestor.py  # CSV and JSON ingestion
|       |-- data_validator.py # Validation and rejection reasons
|       |-- data_transformer.py # Standardisation of accepted records
|       |-- database_loader.py # Load processed CSVs into PostgreSQL
|       |-- scheduler.py       # Daily scheduled pipeline runner
|       `-- pipeline.py       # End-to-end run and CSV output writing
|-- tests/
|   |-- conftest.py
|   |-- test_data_ingestor.py
|   |-- test_data_validator.py
|   |-- test_data_transformer.py
|   |-- test_pipeline.py
|   `-- test_database_loader.py
|-- .gitignore
|-- .dockerignore
|-- Dockerfile
|-- compose.yaml
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
- [X] Create analytical SQL queries and summary views.
- [X] Add tests for ingestion, validation, transformation, and pipeline outputs.
- [X] Add logging and stronger runtime error handling.
- [X] Schedule the pipeline and containerise the application.
- [X] Complete project documentation.

## Getting Started

Inspect the five fictional source files in data/raw/ and the
[data dictionary](docs/data_dictionary.md), which documents fields, relationships,
validation rules, normalisation cases and intentional invalid records. The
[operations guide](docs/operations.md) covers configuration, scheduling, logging,
outputs and troubleshooting. The fixtures contain 68 records.

PostgreSQL is optional. The core pipeline and tests run without a database;
they read data/raw/ and write CSVs to data/processed/ and data/rejected/.
Use the platform-specific PostgreSQL steps only if you want to store processed
data in PostgreSQL.

## Windows (PowerShell)

#### 1. Create the Python environment

Run from the project root:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
~~~

The project requires Python 3.12 or newer. If PowerShell blocks activation,
run commands with .\.venv\Scripts\python.exe instead of python.

#### 2. Configure the schedule (optional)

Set another daily run time before starting Docker Compose:

~~~powershell
$env:BANKFLOW_SCHEDULE_HOUR = "3"
$env:BANKFLOW_SCHEDULE_MINUTE = "30"
$env:BANKFLOW_SCHEDULE_TIMEZONE = "Africa/Johannesburg"
docker compose up --build -d
~~~

#### 3. Optional: install and start PostgreSQL

Download the Windows x86-64 installer from the
[official PostgreSQL Windows page](https://www.postgresql.org/download/windows/).
The commands below assume PostgreSQL 18 is installed in its default location.
If your version differs, update 18 in the paths and service name.

~~~powershell
$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$pgData = "C:\Program Files\PostgreSQL\18\data"
Get-Service -Name postgresql-x64-18
~~~

If the service is stopped, open PowerShell as administrator and start it:

~~~powershell
Start-Service -Name postgresql-x64-18
Get-Service -Name postgresql-x64-18
~~~

If the installer initialized the data directory but did not register the
service, register it once from administrator PowerShell, then start it:

~~~powershell
& "$pgBin\pg_ctl.exe" register -N "postgresql-x64-18" -U "NT AUTHORITY\NetworkService" -D $pgData -w
Start-Service -Name postgresql-x64-18
~~~

If Windows blocks pg_ctl.exe with an application-control policy message, keep
your security settings on and skip local database setup unless you choose a
trusted, approved way to run PostgreSQL. The pipeline and tests work without a
database.

#### 4. Create the database and tables

Create the bankflow database once; skip this if it already exists:

~~~powershell
& "$pgBin\createdb.exe" -U postgres bankflow
~~~

Apply the table schema and check that the tables exist:

~~~powershell
& "$pgBin\psql.exe" -U postgres -d bankflow -f ".\sql\schema.sql"
& "$pgBin\psql.exe" -U postgres -d bankflow -c "\dt"
~~~

Apply or update the analytical views:

~~~powershell
& "$pgBin\psql.exe" -U postgres -d bankflow -f ".\sql\analytics.sql"
& "$pgBin\psql.exe" -U postgres -d bankflow -c "SELECT * FROM daily_transaction_summary ORDER BY transaction_date, transaction_type;"
~~~

#### 5. Load and verify the data

Install the database extra, generate the CSV files, then load them into
PostgreSQL. The loader prompts for the password without displaying it. It loads
parent tables before dependent tables in one transaction; rerunning it updates
rows with matching IDs.

~~~powershell
python -m pip install -e ".[dev,database]"
python -m bankflow.pipeline
python -m bankflow.database_loader
~~~

The default connection is localhost:5432, database bankflow, user postgres.
Override the connection in the current PowerShell session if needed:

~~~powershell
$env:BANKFLOW_DB_HOST = "localhost"
$env:BANKFLOW_DB_PORT = "5432"
$env:BANKFLOW_DB_NAME = "bankflow"
$env:BANKFLOW_DB_USER = "postgres"
~~~

Check the accepted sample-record counts:

~~~powershell
& "$pgBin\psql.exe" -U postgres -d bankflow -c "SELECT 'branches' AS dataset, COUNT(*) FROM branches UNION ALL SELECT 'customers', COUNT(*) FROM customers UNION ALL SELECT 'accounts', COUNT(*) FROM accounts UNION ALL SELECT 'transactions', COUNT(*) FROM transactions UNION ALL SELECT 'payments', COUNT(*) FROM payments;"
~~~

Expected counts are 5 branches, 10 customers, 10 accounts, 12 transactions,
and 5 payments. Rejected records remain in data/rejected/; the loader imports
only accepted data from data/processed/.

## Linux (Bash)

#### 1. Create the Python environment

Run from the repository root:

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
~~~

The project requires Python 3.12 or newer. If you do not activate the
environment, use ./.venv/bin/python instead of python.

#### 2. Configure the schedule (optional)

Set another daily run time before starting Docker Compose:

~~~bash
export BANKFLOW_SCHEDULE_HOUR=3
export BANKFLOW_SCHEDULE_MINUTE=30
export BANKFLOW_SCHEDULE_TIMEZONE=Africa/Johannesburg
docker compose up --build -d
~~~

#### 3. Optional: install and start PostgreSQL

For Ubuntu or Debian, install PostgreSQL and its command-line tools, then start
the service:

~~~bash
sudo apt update
sudo apt install postgresql postgresql-client
sudo systemctl enable --now postgresql
sudo systemctl status postgresql
~~~

For other Linux distributions, install and start PostgreSQL using the
distribution's package manager and service manager.

Set a password for the postgres database user by opening its interactive prompt:

~~~bash
sudo -u postgres psql
~~~

At the psql prompt, run \password postgres and follow the prompts.

#### 4. Create the database and tables

Create the bankflow database once:

~~~bash
sudo -u postgres createdb bankflow
~~~

Apply the schema and check that the tables exist:

~~~bash
sudo -u postgres psql -d bankflow -f sql/schema.sql
sudo -u postgres psql -d bankflow -c "\dt"
~~~

Apply or update the analytical views:

~~~bash
sudo -u postgres psql -d bankflow -f sql/analytics.sql
sudo -u postgres psql -d bankflow -c "SELECT * FROM daily_transaction_summary ORDER BY transaction_date, transaction_type;"
~~~

#### 5. Load and verify the data

Install the database extra, generate the CSV files, then load them into
PostgreSQL. The loader prompts for the password without displaying it.

~~~bash
python -m pip install -e ".[dev,database]"
python -m bankflow.pipeline
python -m bankflow.database_loader
~~~

The default connection is localhost:5432, database bankflow, user postgres.
Set or override the connection variables in the current Bash session if needed:

~~~bash
export BANKFLOW_DB_HOST=localhost
export BANKFLOW_DB_PORT=5432
export BANKFLOW_DB_NAME=bankflow
export BANKFLOW_DB_USER=postgres
~~~

Check the accepted sample-record counts:

~~~bash
psql -U postgres -d bankflow -c "SELECT 'branches' AS dataset, COUNT(*) FROM branches UNION ALL SELECT 'customers', COUNT(*) FROM customers UNION ALL SELECT 'accounts', COUNT(*) FROM accounts UNION ALL SELECT 'transactions', COUNT(*) FROM transactions UNION ALL SELECT 'payments', COUNT(*) FROM payments;"
~~~

Expected counts are 5 branches, 10 customers, 10 accounts, 12 transactions,
and 5 payments. Rejected records remain in data/rejected/; the loader imports
only accepted data from data/processed/.

tests/conftest.py creates a fresh temporary folder for each test run and cleans
it up afterward. Pytest caching is disabled in pyproject.toml to avoid shared
folder permission issues encountered on Windows.

## Commands shared by Windows and Linux

After completing the platform-specific setup above and activating the project
environment, these commands work in either PowerShell or Bash.

Run the CSV pipeline once:

~~~sh
python -m bankflow.pipeline
~~~

Start the local daily scheduler (default: 02:00 UTC):

~~~sh
python -m bankflow.scheduler
~~~

Build and start the scheduled Docker service:

~~~sh
docker compose up --build -d
docker compose ps
docker compose logs -f bankflow
~~~

Run the pipeline immediately in a one-off container, then stop the scheduler:

~~~sh
docker compose run --rm bankflow python -m bankflow.pipeline
docker compose down
~~~

The container persists processed files, rejected files, and logs in the project
folders. It runs the CSV pipeline and does not connect to PostgreSQL. The
scheduler waits for its next scheduled time after startup.

Run the same compile, packaging, and test checks used in CI:

~~~sh
python -m compileall -q src
python -m pip install build
python -m build
python -m pytest -v
~~~

The build creates a source archive and wheel in dist/.

## Planned Demonstration

The planned demonstration will follow data through the full pipeline:

1. Inspect fictional raw data containing intentional quality issues.
2. Run `python -m bankflow.pipeline` to ingest, validate, transform, and write outputs.
3. Review rejected records and their rejection reasons.
4. Inspect clean, related tables in PostgreSQL.
5. Run analytical SQL queries.
6. Present summaries, with an optional reporting layer as future work.

## Skills Demonstrated

ETL development, data quality validation, Python data processing, relational modelling, SQL, PostgreSQL, automated testing, logging, error handling, orchestration and preparation of data for downstream analytics.

## Data Privacy

This project uses fictional banking data for educational and portfolio purposes. Real customer information, banking credentials and sensitive financial records must not be committed to the repository.
