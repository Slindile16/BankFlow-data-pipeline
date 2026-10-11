"""Tests for loading processed CSV datasets into PostgreSQL."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from bankflow.database_loader import PostgresLoader


DATASETS = {
    "branches": {
        "columns": ("branch_id", "branch_name", "city", "province"),
        "row": ("B001", "Central", "Johannesburg", "Gauteng"),
    },
    "customers": {
        "columns": (
            "customer_id", "first_name", "last_name", "province", "join_date"
        ),
        "row": ("C001", "Amahle", "Demo", "Gauteng", "2025-01-05"),
    },
    "accounts": {
        "columns": (
            "account_id", "customer_id", "branch_id", "account_type", "balance",
            "opened_date",
        ),
        "row": ("A001", "C001", "B001", "savings", "100.00", "2025-01-06"),
    },
    "transactions": {
        "columns": (
            "transaction_id", "account_id", "branch_id", "transaction_type",
            "amount", "transaction_date",
        ),
        "row": ("T001", "A001", "B001", "deposit", "25.50", "2025-01-07"),
    },
    "payments": {
        "columns": (
            "payment_id", "account_id", "payee", "amount", "payment_date", "status"
        ),
        "row": ("P001", "A001", "Utilities", "12.00", "2025-01-08", "completed"),
    },
}


def write_processed_files(folder):
    for dataset, definition in DATASETS.items():
        columns = definition["columns"]
        row = definition["row"]
        (folder / f"{dataset}.csv").write_text(
            ",".join(columns) + "\n" + ",".join(row) + "\n",
            encoding="utf-8",
        )


def make_fake_connection():
    connection = MagicMock()
    connection.__enter__.return_value = connection
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection, cursor


def test_loader_upserts_all_processed_datasets_in_foreign_key_order(
    tmp_path, monkeypatch
):
    write_processed_files(tmp_path)
    connection, cursor = make_fake_connection()
    connection_parameters = {
        "host": "localhost",
        "port": 5432,
        "dbname": "bankflow",
        "user": "postgres",
        "password": "test-only-password",
    }
    connect = MagicMock(return_value=connection)
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=connect),
    )

    PostgresLoader(connection_parameters).load_processed_data(tmp_path)

    assert connect.call_args.kwargs == connection_parameters
    assert [call.args[0].split("(")[0].split()[-1] for call in cursor.executemany.call_args_list] == [
        "branches", "customers", "accounts", "transactions", "payments"
    ]
    assert [call.args[1] for call in cursor.executemany.call_args_list] == [
        [definition["row"]] for definition in DATASETS.values()
    ]
    assert all(
        "ON CONFLICT" in call.args[0]
        for call in cursor.executemany.call_args_list
    )


def test_loader_requires_all_processed_dataset_files_before_connecting(tmp_path, monkeypatch):
    connect = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=connect),
    )

    with pytest.raises(FileNotFoundError, match="branches.csv"):
        PostgresLoader({"host": "localhost"}).load_processed_data(tmp_path)

    connect.assert_not_called()
