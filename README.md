# BankFlow

An end-to-end ETL pipeline that turns fictional banking data into validated,
standardised datasets for SQL analysis.

Banking source files can contain missing identifiers, duplicate records, invalid
amounts and broken relationships. BankFlow checks these records, separates
rejected rows with clear reasons, and prepares accepted data for CSV output and
optional PostgreSQL loading.

**Status:** The core pipeline is implemented, including SQL analytics, automated
tests, daily scheduling, Docker support and runtime logging. A reporting
dashboard is optional future work.

## Video demonstration

The BankFlow video walkthrough explains the project and demonstrates the pipeline,
accepted and rejected records, SQL schema and Docker scheduling.

[Watch the BankFlow project demonstration on YouTube](https://youtu.be/mK56ikMALH4).

## How it works

```text
Raw CSV / JSON
      |
      v
   Ingest
      |
      v
   Validate ------> Rejected CSVs + rejection reasons
      |
      v
   Transform
      |
      v
Processed CSVs
      |
      v
PostgreSQL loading (separate command, optional)
      |
      v
SQL summary views
```

The pipeline processes branches and customers before accounts, then transactions
and payments, so it can validate references against accepted parent records.
It standardises dates, province names, account types, transaction categories,
payment statuses and monetary values.

## Quick start

You need **Python 3.12 or newer**. Run these commands from the repository root.
PostgreSQL and Docker are not required for this quick start.

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m bankflow.pipeline
.\.venv\Scripts\python.exe -m pytest -q
```

### Linux (Bash)

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
./.venv/bin/python -m bankflow.pipeline
./.venv/bin/python -m pytest -q
```

Each pipeline run writes one CSV per dataset into both `data/processed/` and
`data/rejected/`. Rejected rows preserve source values and include a
`rejection_reasons` column. Runs overwrite previous CSV outputs. Runtime logs
are written to `logs/bankflow.log`.

## Sample data and expected results

The five source files contain **68 fictional records**, including intentional
quality issues. The supplied fixtures produce **42 accepted records**:

| Dataset | Source file | Accepted records |
| --- | --- | ---: |
| Branches | `branches.csv` | 5 |
| Customers | `customers.csv` | 10 |
| Accounts | `accounts.csv` | 10 |
| Transactions | `transactions.csv` | 12 |
| Payments | `payments.json` | 5 |

Source files live in `data/raw/`. See the [data dictionary](docs/data_dictionary.md)
for fields, validation rules and intentional invalid records.

## PostgreSQL and analytics

The optional database loader imports processed CSVs in dependency order within
one transaction. Rerunning it updates rows with matching primary keys. Rejected
records remain in CSV files.

The [database schema](sql/schema.sql) defines the five related tables. The
[analytics script](sql/analytics.sql) creates these summary views:

| View | What it shows |
| --- | --- |
| `daily_transaction_summary` | Daily transaction counts and amounts by type |
| `branch_transaction_summary` | Transaction activity by branch |
| `monthly_customer_growth` | Monthly signups and cumulative customer count |
| `customer_province_summary` | Customer distribution by province |
| `monthly_payment_summary` | Payment counts and amounts by month and status |

Follow the [setup guide](docs/setup.md) to create the database, apply the SQL
scripts, load processed data and query the results.

## Scheduling and Docker

The scheduler runs the CSV pipeline daily at **02:00 UTC** by default. It waits
for the next scheduled time when started. After installing and activating the
project environment, start it locally with:

```sh
python -m bankflow.scheduler
```

Or build and start the scheduled Docker service:

```sh
docker compose up --build -d
docker compose logs -f bankflow
```

The container persists processed files, rejected files and logs in the project
folders. PostgreSQL loading is a separate step. See the
[operations guide](docs/operations.md) for schedule settings, environment
variables and troubleshooting.

## Project structure

```text
BankFlow-data-pipeline/
|-- data/
|   |-- raw/                  # Fictional CSV and JSON source files
|   |-- processed/            # Generated accepted records
|   `-- rejected/             # Generated rejected records and reasons
|-- docs/
|   |-- setup.md              # Windows, Linux and PostgreSQL setup
|   |-- data_dictionary.md    # Fields, validation rules and fixture cases
|   `-- operations.md         # Configuration and troubleshooting
|-- sql/
|   |-- schema.sql            # Tables and integrity constraints
|   `-- analytics.sql         # Analytical summary views
|-- src/bankflow/
|   |-- data_ingestor.py      # CSV and JSON reading
|   |-- data_validator.py     # Record and relationship checks
|   |-- data_transformer.py   # Standardisation of accepted records
|   |-- pipeline.py           # Orchestration and CSV output
|   |-- database_loader.py    # PostgreSQL loading
|   |-- scheduler.py          # Daily scheduled runs
|   `-- logging_config.py    # Console and rotating-file logging
|-- tests/                    # Ingestion, validation, transformation and loading tests
|-- .github/workflows/        # Windows and Linux CI checks
|-- Dockerfile
|-- compose.yaml
|-- pyproject.toml            # Packaging, dependencies and pytest configuration
`-- README.md
```

## Technology and verification

Built with Python, Pandas, PostgreSQL, SQL, pytest, APScheduler and Docker.
GitHub Actions compiles the source, builds the package and runs tests on Windows
and Linux. To run the test suite in an activated project environment:

```sh
python -m pytest -q
```

The [setup guide](docs/setup.md#commands-shared-by-windows-and-linux) includes
packaging checks and additional runtime commands.

## Scope and future work

BankFlow is an educational and portfolio project using fictional data. It
implements ingestion, validation, transformation, CSV output, PostgreSQL loading,
SQL summary views, scheduling, containers and logging.

A visual reporting dashboard is future work. Anomaly detection is not implemented,
and rejected records are not included in the SQL views. Transactions represent
sample activity rather than a double-entry ledger; transfers have no destination
account. Payment and transaction totals should be analysed separately.

WTC-4FDZJBMT
