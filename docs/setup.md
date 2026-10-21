# Installation and setup

Run these commands from the repository root. Python 3.12 or newer is required.
PostgreSQL and Docker are optional; the CSV pipeline runs without either.

For a quick introduction, see the [README](../README.md). For configuration
and troubleshooting, see the [operations guide](operations.md).

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

