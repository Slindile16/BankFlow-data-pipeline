"""Customer validation contract, written before the validator implementation.

validate_customers(customers) returns (accepted, rejected) DataFrames.
Both retain the source columns and row indices. Rejected rows additionally have
a rejection_reasons column containing a list of reason codes. Accepted rows keep
the source values; standardisation belongs to the transformation stage.
"""

import pandas as pd
import pytest

from bankflow import data_validator


@pytest.fixture
def validator():
    # The module exists but DataValidator is intentionally not implemented yet.
    return data_validator.DataValidator()


@pytest.fixture
def valid_customer():
    return {
        "customer_id": "C001",
        "first_name": "Amahle",
        "last_name": "Demo",
        "province": "Gauteng",
        "join_date": "2025-01-05",
    }


def assert_single_rejection(validator, record, expected_reasons):
    source = pd.DataFrame([record])
    accepted, rejected = validator.validate_customers(source)

    assert isinstance(accepted, pd.DataFrame)
    assert isinstance(rejected, pd.DataFrame)
    assert accepted.empty
    assert len(rejected) == 1
    pd.testing.assert_frame_equal(rejected[source.columns], source)
    reasons = rejected.iloc[0]["rejection_reasons"]
    assert isinstance(reasons, list)
    assert sorted(reasons) == sorted(expected_reasons)


@pytest.mark.parametrize("join_date", ["2025-01-05", "15/03/2025", "2025/04/02"])
def test_valid_customer_is_accepted(validator, valid_customer, join_date):
    valid_customer["join_date"] = join_date
    source = pd.DataFrame([valid_customer])

    accepted, rejected = validator.validate_customers(source)

    pd.testing.assert_frame_equal(accepted, source)
    assert isinstance(rejected, pd.DataFrame)
    assert rejected.empty
    assert "rejection_reasons" in rejected.columns


@pytest.mark.parametrize("missing", [None, float("nan"), pd.NA, "", "   "])
def test_missing_customer_id_is_rejected(validator, valid_customer, missing):
    valid_customer["customer_id"] = missing

    assert_single_rejection(validator, valid_customer, ["missing_customer_id"])


@pytest.mark.parametrize("missing", [None, float("nan"), pd.NA, "", "   "])
def test_missing_first_name_is_rejected(validator, valid_customer, missing):
    valid_customer["first_name"] = missing

    assert_single_rejection(validator, valid_customer, ["missing_first_name"])


@pytest.mark.parametrize("missing", [None, float("nan"), pd.NA, "", "   "])
def test_missing_last_name_is_rejected(validator, valid_customer, missing):
    valid_customer["last_name"] = missing

    assert_single_rejection(validator, valid_customer, ["missing_last_name"])


def test_exact_duplicates_keep_first_occurrence(validator, valid_customer):
    other_customer = {**valid_customer, "customer_id": "C002"}
    source = pd.DataFrame(
        [valid_customer, other_customer, valid_customer, valid_customer],
        index=[10, 20, 30, 40],
    )

    accepted, rejected = validator.validate_customers(source)

    pd.testing.assert_frame_equal(accepted, source.loc[[10, 20]])
    pd.testing.assert_frame_equal(rejected[source.columns], source.loc[[30, 40]])
    assert rejected["rejection_reasons"].tolist() == [
        ["duplicate_customer"],
        ["duplicate_customer"],
    ]


@pytest.mark.parametrize(
    "join_date,reason",
    [
        (None, "missing_join_date"),
        (float("nan"), "missing_join_date"),
        (pd.NA, "missing_join_date"),
        ("", "missing_join_date"),
        ("   ", "missing_join_date"),
        ("not-a-date", "invalid_join_date"),
        ("2025-02-30", "invalid_join_date"),
        ("2025/13/01", "invalid_join_date"),
        ("01-05-2025", "invalid_join_date"),
    ],
)
def test_missing_or_invalid_join_date_is_rejected(
    validator, valid_customer, join_date, reason
):
    valid_customer["join_date"] = join_date

    assert_single_rejection(validator, valid_customer, [reason])


def test_multiple_issues_record_all_reasons(validator, valid_customer):
    valid_customer.update(
        customer_id=None, first_name="", last_name="   ", join_date="2025-02-30"
    )

    assert_single_rejection(
        validator,
        valid_customer,
        ["missing_customer_id", "missing_first_name", "missing_last_name", "invalid_join_date"],
    )


def test_validation_does_not_modify_input(validator, valid_customer):
    invalid_customer = {**valid_customer, "customer_id": None, "join_date": "invalid"}
    source = pd.DataFrame([valid_customer, invalid_customer, valid_customer])
    original = source.copy(deep=True)

    validator.validate_customers(source)

    pd.testing.assert_frame_equal(source, original)
