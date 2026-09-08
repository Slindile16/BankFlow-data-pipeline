# BankFlow 

BankFlow is a data engineering project that will transform messy, fictional banking data into clean, validated, analysis-ready datasets.

The platform will ingest data from multiple file formats, enforce data quality rules, standardise records, load trusted data into PostgreSQL, and support analysis through SQL queries and summary tables.

 **Status:** Planning and initial setup. The features below describe the planned implementation.

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

## Planned Pipeline

```text
Raw Data (CSV / JSON)
        |
        v
     Ingestion
        |
        v
     Validation ------> Rejected Records + Rejection Reasons
        |
        v
Cleaning & Transformation
        |
        v
    PostgreSQL
        |
        v
SQL Analytics & Summary Tables
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

The pipeline will check:

- Required fields and identifiers.
- Duplicate records and transactions.
- Date formats and validity.
- Numeric values and transaction amounts.
- Account references and relationships between records.

Rejected records will be stored separately with reasons for rejection.

Accepted records will be transformed to standardise dates, province names, account types and transaction categories before loading into PostgreSQL.

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

## Roadmap

- [X] Create the repository, project structure and fictional datasets.
- [ ] Implement CSV and JSON ingestion.
- [ ] Add validation, duplicate detection and rejected-record handling.
- [ ] Implement cleaning and transformation rules.
- [ ] Design the PostgreSQL schema and load validated data.
- [ ] Create analytical SQL queries and summary tables.
- [ ] Add tests, logging and stronger error handling.
- [ ] Schedule the pipeline and containerise the application.
- [ ] Add an optional reporting layer and complete documentation.

## Getting Started

The project is currently being set up. Installation instructions, environment configuration and pipeline execution commands will be added as the implementation becomes available.

## Planned Demonstration

The demonstration will follow data through the full pipeline:

1. Inspect fictional raw data containing intentional quality issues.
2. Run ingestion, validation and transformation.
3. Review rejected records and their rejection reasons.
4. Inspect clean, related tables in PostgreSQL.
5. Run analytical SQL queries.
6. Present summaries or an optional dashboard.

## Skills Demonstrated

ETL development, data quality validation, Python data processing, relational modelling, SQL, PostgreSQL, automated testing, logging, error handling, orchestration and preparation of data for downstream analytics.

## Data Privacy

This project uses fictional banking data for educational and portfolio purposes. Real customer information, banking credentials and sensitive financial records must not be committed to the repository.
