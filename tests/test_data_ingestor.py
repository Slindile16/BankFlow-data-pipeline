"""Tests for reading source files before validation and transformation."""

from pathlib import Path

import pandas as pd
import pytest

from bankflow.data_ingestor import DataIngestor


RAW_DATA = Path(__file__).resolve().parents[1] / "data" / "raw"


def test_read_csv_loads_columns_and_records(tmp_path):
    source = tmp_path / "customers.csv"
    source.write_text(
        'customer_id,first_name,last_name\nC001,Amahle,Demo\n'
        'C002,Léo,"Sample, Jr"\n',
        encoding="utf-8",
    )

    result = DataIngestor(tmp_path).read_csv(source.name)

    expected = pd.DataFrame(
        {
            "customer_id": ["C001", "C002"],
            "first_name": ["Amahle", "Léo"],
            "last_name": ["Demo", "Sample, Jr"],
        }
    )
    pd.testing.assert_frame_equal(result, expected, check_dtype=False)


def test_read_json_loads_records_and_missing_values(tmp_path):
    source = tmp_path / "payments.json"
    source.write_text(
        '[{"payment_id":"P001","account_id":"A001"},'
        '{"payment_id":null,"account_id":"A002"}]',
        encoding="utf-8",
    )

    result = DataIngestor(tmp_path).read_json(source.name)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["payment_id", "account_id"]
    assert result["account_id"].tolist() == ["A001", "A002"]
    assert result.loc[0, "payment_id"] == "P001"
    assert pd.isna(result.loc[1, "payment_id"])


@pytest.mark.parametrize(
    "method,filename",
    [("read_csv", "missing.csv"), ("read_json", "missing.json")],
)
def test_missing_source_raises_file_not_found(tmp_path, method, filename):
    ingestor = DataIngestor(tmp_path)

    with pytest.raises(FileNotFoundError):
        getattr(ingestor, method)(filename)


def test_malformed_csv_raises_parser_error(tmp_path):
    source = tmp_path / "broken.csv"
    source.write_text('customer_id,name\nC001,"unfinished', encoding="utf-8")

    with pytest.raises(pd.errors.ParserError):
        DataIngestor(tmp_path).read_csv(source.name)


def test_malformed_json_raises_value_error(tmp_path):
    source = tmp_path / "broken.json"
    source.write_text('[{"payment_id":', encoding="utf-8")

    with pytest.raises(ValueError):
        DataIngestor(tmp_path).read_json(source.name)


def test_load_all_data_reads_every_fixture():
    datasets = DataIngestor(RAW_DATA).load_all_data()

    expected_counts = {
        "branches": 5,
        "customers": 14,
        "accounts": 16,
        "transactions": 22,
        "payments": 11,
    }
    id_columns = {
        "branches": "branch_id",
        "customers": "customer_id",
        "accounts": "account_id",
        "transactions": "transaction_id",
        "payments": "payment_id",
    }
    assert set(datasets) == set(expected_counts)
    for name, expected_count in expected_counts.items():
        assert isinstance(datasets[name], pd.DataFrame)
        assert len(datasets[name]) == expected_count, name
        assert id_columns[name] in datasets[name].columns


def test_csv_ingestion_preserves_quality_issues():
    customers = DataIngestor(RAW_DATA).read_csv("customers.csv")

    assert customers["customer_id"].eq("C002").sum() == 2
    assert customers["customer_id"].isna().sum() == 1
    assert customers.loc[5, "province"] == " gauteng "
    assert customers.loc[5, "join_date"] == "15/03/2025"
    assert customers.loc[13, "join_date"] == "2025-02-30"


def test_json_ingestion_preserves_quality_issues():
    payments = DataIngestor(RAW_DATA).read_json("payments.json")

    assert payments["payment_id"].eq("P002").sum() == 2
    assert payments["payment_id"].isna().sum() == 1
    assert payments.loc[3, "status"] == " COMPLETED "
    assert payments.loc[6, "account_id"] == "A999"
    assert payments.loc[8, "amount"] == "invalid"
    assert payments.loc[9, "payment_date"] == "2025-06-31"
