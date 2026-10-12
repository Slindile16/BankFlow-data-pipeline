"""End-to-end pipeline output checks."""

import json
import logging

import pandas as pd
import pytest

from bankflow.pipeline import DataPipeline


def test_pipeline_writes_transformed_and_rejected_dataset_outputs(tmp_path, caplog):
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    rejected = tmp_path / "rejected"
    raw.mkdir()

    pd.DataFrame(
        [{"branch_id": "B001", "branch_name": "Central", "city": "Joburg", "province": "gauteng"}]
    ).to_csv(raw / "branches.csv", index=False)
    pd.DataFrame(
        [
            {"customer_id": "C001", "first_name": "Ava", "last_name": "Demo", "province": "gauteng", "join_date": "2025-01-01"},
            {"customer_id": "C002", "first_name": None, "last_name": "Demo", "province": "Gauteng", "join_date": "2025-01-02"},
        ]
    ).to_csv(raw / "customers.csv", index=False)
    pd.DataFrame(
        [{"account_id": "A001", "customer_id": "C001", "branch_id": "B001", "account_type": "Savings", "balance": "100.00", "opened_date": "2025-01-03"}]
    ).to_csv(raw / "accounts.csv", index=False)
    pd.DataFrame(
        [{"transaction_id": "T001", "account_id": "A001", "branch_id": "B001", "transaction_type": "CARD PAYMENT", "amount": "12.50", "transaction_date": "2025-01-04"}]
    ).to_csv(raw / "transactions.csv", index=False)
    pd.DataFrame(
        [{"payment_id": "P001", "account_id": "A001", "payee": "Utilities", "amount": "5.00", "payment_date": "2025-01-05", "status": "COMPLETED"}]
    ).to_json(raw / "payments.json", orient="records")

    with caplog.at_level(logging.INFO):
        results = DataPipeline(raw, processed, rejected).run()

    assert {name: (len(frames["accepted"]), len(frames["rejected"]))
            for name, frames in results.items()} == {
        "branches": (1, 0),
        "customers": (1, 1),
        "accounts": (1, 0),
        "transactions": (1, 0),
        "payments": (1, 0),
    }
    assert set(path.name for path in processed.glob("*.csv")) == {
        "branches.csv", "customers.csv", "accounts.csv", "transactions.csv", "payments.csv"
    }
    assert set(path.name for path in rejected.glob("*.csv")) == {
        "branches.csv", "customers.csv", "accounts.csv", "transactions.csv", "payments.csv"
    }

    transaction_output = pd.read_csv(processed / "transactions.csv")
    assert transaction_output.loc[0, "transaction_type"] == "card_payment"
    assert transaction_output.loc[0, "amount"] == 12.5
    customer_rejections = pd.read_csv(rejected / "customers.csv")
    assert json.loads(customer_rejections.loc[0, "rejection_reasons"]) == [
        "missing_first_name"
    ]

    for dataset, frames in results.items():
        assert (
            f"{dataset}: {len(frames['accepted'])} accepted, "
            f"{len(frames['rejected'])} rejected"
        ) in caplog.text


def test_pipeline_logs_and_reraises_source_read_failure(tmp_path, monkeypatch, caplog):
    pipeline = DataPipeline(
        tmp_path / "raw", tmp_path / "processed", tmp_path / "rejected"
    )

    def fail_to_read_sources():
        raise OSError("source folder is unavailable")

    monkeypatch.setattr(pipeline.ingestor, "load_all_data", fail_to_read_sources)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(OSError, match="source folder is unavailable"):
            pipeline.run()

    assert "Pipeline failed" in caplog.text
    assert "source folder is unavailable" in caplog.text
