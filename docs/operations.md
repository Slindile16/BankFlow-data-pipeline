# Runtime and operations guide

This guide describes how the implemented pipeline runs, where it writes files,
how to configure the scheduler and database loader, and how to diagnose common
problems. For field definitions, validation rules and the intentional fixture
errors, see the [data dictionary](data_dictionary.md). For installation and
platform-specific commands, see the [README](../README.md).

## Pipeline behavior

Run the pipeline from the repository checkout with:

```sh
python -m bankflow.pipeline
```

The pipeline reads the five files from the raw data directory in dependency
order: branches and customers, accounts, transactions, then payments. It
validates records without changing their source values, transforms accepted
records, and writes one processed and one rejected CSV per dataset. A normal
run overwrites the previous CSV outputs. Rejection reason lists are serialized
as JSON strings in the rejected CSVs.

The processed outputs can be loaded into PostgreSQL separately. The pipeline
does not require PostgreSQL and does not load data into the database by itself.

## Commands

| Purpose | Command |
| --- | --- |
| Run the CSV pipeline once | `python -m bankflow.pipeline` |
| Load processed CSVs into PostgreSQL | `python -m bankflow.database_loader` |
| Start the daily scheduler | `python -m bankflow.scheduler` |
| Run the test suite | `python -m pytest -v` |
| Compile source files | `python -m compileall -q src` |
| Build source and wheel distributions | `python -m build` |

The database loader expects the five processed CSVs to exist and prompts for
the PostgreSQL password. It loads parent tables before child tables in one
transaction and upserts rows with matching primary keys. The database tables
must already exist; apply `sql/schema.sql` before the first load. Apply
`sql/analytics.sql` after creating the tables to create the analytical views.

## Environment variables

| Variable | Used by | Default | Description |
| --- | --- | --- | --- |
| `BANKFLOW_DATA_ROOT` | Pipeline | `data/` under the project root | Directory containing `raw/`, `processed/`, and `rejected/` subdirectories |
| `BANKFLOW_LOG_FILE` | Pipeline and scheduler | `logs/bankflow.log` | Log file path |
| `BANKFLOW_SCHEDULE_HOUR` | Scheduler | `2` | Daily run hour, from `0` through `23` |
| `BANKFLOW_SCHEDULE_MINUTE` | Scheduler | `0` | Run minute, from `0` through `59` |
| `BANKFLOW_SCHEDULE_TIMEZONE` | Scheduler | `UTC` | Timezone name used to interpret the daily schedule, such as `Africa/Johannesburg` |
| `BANKFLOW_DB_HOST` | Database loader | `localhost` | PostgreSQL server hostname |
| `BANKFLOW_DB_PORT` | Database loader | `5432` | PostgreSQL server port |
| `BANKFLOW_DB_NAME` | Database loader | `bankflow` | Database name |
| `BANKFLOW_DB_USER` | Database loader | `postgres` | PostgreSQL database user |

The database loader prompts for the password without echoing it. It does not
read a password environment variable. Do not put database credentials in
source control.

`BANKFLOW_DATA_ROOT` is the data directory itself, not the repository root. For
example, setting it to `/srv/bankflow/data` makes the pipeline read from
`/srv/bankflow/data/raw` and write to the sibling `processed` and `rejected`
directories.

## Scheduling

The scheduler runs the pipeline once per day at 02:00 UTC by default. It starts
and waits for the next scheduled time; starting it does not trigger an immediate
run. Set the schedule variables above to choose another time and timezone.

Only one scheduled pipeline run may execute at once. If the scheduler is down
at a run time, a missed run may start after recovery only if it is no more than
one hour late. Multiple missed runs are coalesced into one. The schedule is
in-memory, so the next run is recalculated when the process restarts.

Docker Compose runs this scheduler as a restartable service. It mounts
`data/raw/` read-only and persists processed CSVs, rejected CSVs, and logs in
the corresponding host folders. Use `docker compose logs -f bankflow` to watch
the service and `docker compose down` to stop it.

## Logging

The pipeline and database loader log INFO-level and higher messages to the
console and to `logs/bankflow.log`. The file rotates at 1 MB and retains up to
three older files. Pipeline failures are logged with a traceback and re-raised
to the caller. Log files are runtime output and are ignored by Git.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `ModuleNotFoundError: bankflow` | Activate the project virtual environment and install the project from the repository root with `python -m pip install -e ".[dev]"`. |
| A source file cannot be found | Confirm the five fixture files are under `data/raw/`, or set `BANKFLOW_DATA_ROOT` to a directory containing a `raw/` subdirectory. |
| The scheduler starts but no files appear | It waits for the next daily schedule. Run `python -m bankflow.pipeline` for an immediate run and check the scheduler logs. |
| PostgreSQL connection is refused | Confirm the PostgreSQL service is running and check the host, port, database, and user settings. The loader prompts for the password. |
| The loader reports missing processed files | Run the pipeline first and confirm all five CSV files are in `data/processed/`. |
| An analytical view is missing | Apply `sql/schema.sql`, load the processed data, then apply `sql/analytics.sql`. |
| Database loading fails on a duplicate key | Inspect the source rows with the same ID. Exact repeated rows are filtered; different rows with the same ID are upserted in file order, so the later row can replace earlier values. |

## Current limitations

- Rejected records stay in CSV files and are not included in PostgreSQL summary
  views.
- Duplicate validation detects exact duplicate rows. It does not report
  conflicting rows that share an ID; inspect IDs before loading.
- Transactions are sample activity records rather than double-entry ledger
  entries. Transfers do not identify a destination account.
- The sample data and summary rules are educational examples, not banking
  controls, financial advice, or fraud detection.
