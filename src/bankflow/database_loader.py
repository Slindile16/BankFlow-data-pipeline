"""Load accepted, transformed CSV datasets into PostgreSQL."""

import csv
import getpass
import os
from pathlib import Path


DATASET_COLUMNS = {
    "branches": ("branch_id", "branch_name", "city", "province"),
    "customers": (
        "customer_id", "first_name", "last_name", "province", "join_date"
    ),
    "accounts": (
        "account_id", "customer_id", "branch_id", "account_type", "balance",
        "opened_date",
    ),
    "transactions": (
        "transaction_id", "account_id", "branch_id", "transaction_type", "amount",
        "transaction_date",
    ),
    "payments": (
        "payment_id", "account_id", "payee", "amount", "payment_date", "status"
    ),
}
PRIMARY_KEYS = {
    "branches": "branch_id",
    "customers": "customer_id",
    "accounts": "account_id",
    "transactions": "transaction_id",
    "payments": "payment_id",
}
LOAD_ORDER = ("branches", "customers", "accounts", "transactions", "payments")


class PostgresLoader:
    """Upsert processed CSV files in a single PostgreSQL transaction."""

    def __init__(self, connection_parameters):
        self.connection_parameters = dict(connection_parameters)

    @staticmethod
    def _read_rows(path, required_columns):
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            missing_columns = set(required_columns) - set(reader.fieldnames or ())
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(f"{path.name} is missing columns: {missing}")
            return [
                tuple(row[column] for column in required_columns)
                for row in reader
            ]

    @staticmethod
    def _insert_statement(dataset):
        columns = DATASET_COLUMNS[dataset]
        primary_key = PRIMARY_KEYS[dataset]
        column_sql = ", ".join(columns)
        placeholders = ", ".join("%s" for _ in columns)
        updates = ", ".join(
            f"{column} = EXCLUDED.{column}"
            for column in columns
            if column != primary_key
        )
        return (
            f"INSERT INTO {dataset} ({column_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT ({primary_key}) DO UPDATE SET {updates}"
        )

    def load_processed_data(self, processed_folder):
        """Upsert each processed dataset and return its loaded row count.

        Files are preflighted before connecting. The database operations run in
        foreign-key order and commit together, so a failed dataset rolls back
        the complete load.
        """
        processed_folder = Path(processed_folder)
        paths = {
            dataset: processed_folder / f"{dataset}.csv"
            for dataset in LOAD_ORDER
        }
        for path in paths.values():
            if not path.is_file():
                raise FileNotFoundError(f"Processed dataset file not found: {path}")

        rows_by_dataset = {
            dataset: self._read_rows(paths[dataset], DATASET_COLUMNS[dataset])
            for dataset in LOAD_ORDER
        }

        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError(
                'PostgreSQL loading requires the optional dependency; install it '
                'with "python -m pip install -e .[database]".'
            ) from error

        with psycopg.connect(**self.connection_parameters) as connection:
            with connection.cursor() as cursor:
                for dataset in LOAD_ORDER:
                    rows = rows_by_dataset[dataset]
                    if rows:
                        cursor.executemany(self._insert_statement(dataset), rows)

        return {dataset: len(rows_by_dataset[dataset]) for dataset in LOAD_ORDER}


def main():
    """Load repository processed files using local PostgreSQL defaults."""
    project_root = Path(__file__).resolve().parents[2]
    connection_parameters = {
        "host": os.getenv("BANKFLOW_DB_HOST", "localhost"),
        "port": int(os.getenv("BANKFLOW_DB_PORT", "5432")),
        "dbname": os.getenv("BANKFLOW_DB_NAME", "bankflow"),
        "user": os.getenv("BANKFLOW_DB_USER", "postgres"),
        "password": getpass.getpass("PostgreSQL password: "),
    }
    loaded = PostgresLoader(connection_parameters).load_processed_data(
        project_root / "data" / "processed"
    )
    for dataset, count in loaded.items():
        print(f"{dataset}: {count} rows loaded")


if __name__ == "__main__":
    main()
