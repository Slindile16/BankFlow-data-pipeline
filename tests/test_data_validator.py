"""Customer and account validation contract.

validate_customers(customers) returns (accepted, rejected) DataFrames.
Both retain the source columns and row indices. Rejected rows additionally have
a rejection_reasons column containing a list of reason codes. Accepted rows keep
the source values; standardisation belongs to the transformation stage.
"""

from pathlib import Path

import pandas as pd
import pytest

from bankflow import data_validator
from bankflow.data_ingestor import DataIngestor


@pytest.fixture
def validator():
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


def test_empty_customer_data_preserves_columns(validator, valid_customer):
    source = pd.DataFrame([valid_customer]).iloc[:0]

    accepted, rejected = validator.validate_customers(source)

    pd.testing.assert_frame_equal(accepted, source)
    assert rejected.empty
    assert list(rejected.columns) == [*source.columns, "rejection_reasons"]


def test_repeated_index_labels_do_not_mix_rejection_reasons(validator, valid_customer):
    source = pd.DataFrame(
        [valid_customer, {**valid_customer, "customer_id": "C002", "first_name": ""}],
        index=[0, 0],
    )

    accepted, rejected = validator.validate_customers(source)

    pd.testing.assert_frame_equal(accepted, source.iloc[[0]])
    pd.testing.assert_frame_equal(rejected[source.columns], source.iloc[[1]])
    assert rejected["rejection_reasons"].tolist() == [["missing_first_name"]]


def test_missing_customer_column_reports_schema_problem(validator, valid_customer):
    source = pd.DataFrame([valid_customer]).drop(columns="join_date")

    with pytest.raises(ValueError, match="Missing customer columns: join_date"):
        validator.validate_customers(source)


@pytest.fixture
def valid_account():
    return {
        "account_id": "A001",
        "customer_id": "C001",
        "branch_id": "B001",
        "account_type": "savings",
        "balance": 12500.50,
        "opened_date": "2025-01-06",
    }


@pytest.fixture
def accepted_customers():
    return pd.DataFrame(
        [{"customer_id": "C001", "join_date": "2025-01-05"}]
    )


@pytest.fixture
def valid_branches():
    return pd.DataFrame([{"branch_id": "B001"}])


def test_valid_account_is_accepted_and_source_values_are_preserved(
    validator, valid_account, accepted_customers, valid_branches
):
    source = pd.DataFrame([valid_account])

    accepted, rejected = validator.validate_accounts(
        source, accepted_customers, valid_branches
    )

    pd.testing.assert_frame_equal(accepted, source)
    assert rejected.empty
    assert list(rejected.columns) == [*source.columns, "rejection_reasons"]


@pytest.mark.parametrize(
    "field,missing",
    [
        (field, missing)
        for field in (
            "account_id", "customer_id", "branch_id", "account_type", "balance", "opened_date"
        )
        for missing in (None, float("nan"), pd.NA, "", "   ")
    ],
)
def test_missing_required_account_fields_are_rejected(
    validator, valid_account, accepted_customers, valid_branches, field, missing
):
    record = {**valid_account, field: missing}
    accepted, rejected = validator.validate_accounts(
        pd.DataFrame([record]), accepted_customers, valid_branches
    )

    assert accepted.empty
    assert rejected.iloc[0]["rejection_reasons"] == [f"missing_{field}"]


@pytest.mark.parametrize("account_type", ["investment", "unknown"])
def test_unsupported_account_type_is_rejected(
    validator, valid_account, accepted_customers, valid_branches, account_type
):
    valid_account["account_type"] = account_type
    _, rejected = validator.validate_accounts(
        pd.DataFrame([valid_account]), accepted_customers, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_account_type"]


@pytest.mark.parametrize("balance", ["unknown", "1.234", "Infinity", "NaN"])
def test_nonnumeric_or_invalid_precision_balance_is_rejected(
    validator, valid_account, accepted_customers, valid_branches, balance
):
    valid_account["balance"] = balance
    _, rejected = validator.validate_accounts(
        pd.DataFrame([valid_account]), accepted_customers, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_balance"]


@pytest.mark.parametrize("opened_date", ["not-a-date", "2025-02-30", "2025/13/01"])
def test_invalid_opened_date_is_rejected(
    validator, valid_account, accepted_customers, valid_branches, opened_date
):
    valid_account["opened_date"] = opened_date
    _, rejected = validator.validate_accounts(
        pd.DataFrame([valid_account]), accepted_customers, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_opened_date"]


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("customer_id", "C999", "unknown_customer_id"),
        ("branch_id", "B999", "unknown_branch_id"),
    ],
)
def test_unknown_account_references_are_rejected(
    validator, valid_account, accepted_customers, valid_branches, field, value, reason
):
    valid_account[field] = value
    _, rejected = validator.validate_accounts(
        pd.DataFrame([valid_account]), accepted_customers, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == [reason]


@pytest.mark.parametrize("opened_date", ["2025-01-04", "04/01/2025", "2025/01/04"])
def test_account_opened_before_customer_join_date_is_rejected(
    validator, valid_account, accepted_customers, valid_branches, opened_date
):
    valid_account["opened_date"] = opened_date
    _, rejected = validator.validate_accounts(
        pd.DataFrame([valid_account]), accepted_customers, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == [
        "opened_date_before_customer_join_date"
    ]


def test_supported_date_formats_and_account_type_casing_are_valid(
    validator, valid_account, accepted_customers, valid_branches
):
    valid_account.update(account_type=" CURRENT ", opened_date="06/01/2025")
    accepted, rejected = validator.validate_accounts(
        pd.DataFrame([valid_account]), accepted_customers, valid_branches
    )

    assert len(accepted) == 1
    assert rejected.empty


def test_exact_duplicate_accounts_keep_first_occurrence(
    validator, valid_account, accepted_customers, valid_branches
):
    source = pd.DataFrame([valid_account, valid_account], index=[10, 20])

    accepted, rejected = validator.validate_accounts(
        source, accepted_customers, valid_branches
    )

    pd.testing.assert_frame_equal(accepted, source.iloc[[0]])
    pd.testing.assert_frame_equal(rejected[source.columns], source.iloc[[1]])
    assert rejected["rejection_reasons"].tolist() == [["duplicate_account"]]


def test_account_validation_reports_multiple_issues_and_does_not_mutate_input(
    validator, valid_account, accepted_customers, valid_branches
):
    invalid = {**valid_account, "customer_id": "C999", "branch_id": "B999",
               "account_type": "investment", "balance": "unknown",
               "opened_date": "2025-02-30"}
    source = pd.DataFrame([valid_account, invalid])
    original = source.copy(deep=True)

    accepted, rejected = validator.validate_accounts(
        source, accepted_customers, valid_branches
    )

    pd.testing.assert_frame_equal(source, original)
    assert len(accepted) == 1
    assert set(rejected.iloc[0]["rejection_reasons"]) == {
        "unknown_customer_id", "unknown_branch_id", "invalid_account_type",
        "invalid_balance", "invalid_opened_date",
    }


def test_account_validation_handles_repeated_input_indices(
    validator, valid_account, accepted_customers, valid_branches
):
    invalid = {**valid_account, "account_id": "A002", "balance": "bad"}
    source = pd.DataFrame([valid_account, invalid], index=[0, 0])

    accepted, rejected = validator.validate_accounts(
        source, accepted_customers, valid_branches
    )

    pd.testing.assert_frame_equal(accepted, source.iloc[[0]])
    pd.testing.assert_frame_equal(rejected[source.columns], source.iloc[[1]])
    assert rejected["rejection_reasons"].tolist() == [["invalid_balance"]]


def test_account_validation_rejects_missing_schema_and_reserved_reason_column(
    validator, valid_account, accepted_customers, valid_branches
):
    missing_column = pd.DataFrame([valid_account]).drop(columns="opened_date")
    with pytest.raises(ValueError, match="Missing account columns: opened_date"):
        validator.validate_accounts(missing_column, accepted_customers, valid_branches)

    reserved = pd.DataFrame([{**valid_account, "rejection_reasons": []}])
    with pytest.raises(ValueError, match="reserved rejection_reasons"):
        validator.validate_accounts(reserved, accepted_customers, valid_branches)


def test_account_validation_requires_reference_columns(
    validator, valid_account, accepted_customers, valid_branches
):
    with pytest.raises(ValueError, match="Missing accepted customer columns: join_date"):
        validator.validate_accounts(
            pd.DataFrame([valid_account]),
            accepted_customers.drop(columns="join_date"),
            valid_branches,
        )

    with pytest.raises(ValueError, match="Missing branch columns: branch_id"):
        validator.validate_accounts(
            pd.DataFrame([valid_account]), accepted_customers, pd.DataFrame()
        )


def test_empty_account_data_preserves_schema(
    validator, valid_account, accepted_customers, valid_branches
):
    source = pd.DataFrame([valid_account]).iloc[:0]

    accepted, rejected = validator.validate_accounts(
        source, accepted_customers, valid_branches
    )

    pd.testing.assert_frame_equal(accepted, source)
    assert rejected.empty
    assert list(rejected.columns) == [*source.columns, "rejection_reasons"]


def test_account_validation_matches_documented_fixture_quality_cases():
    raw_folder = Path(__file__).resolve().parents[1] / "data" / "raw"
    datasets = DataIngestor(raw_folder).load_all_data()
    validator = data_validator.DataValidator()
    accepted_customers, rejected_customers = validator.validate_customers(
        datasets["customers"]
    )

    accepted, rejected = validator.validate_accounts(
        datasets["accounts"], accepted_customers, datasets["branches"]
    )

    assert (len(accepted), len(rejected)) == (10, 6)
    assert rejected["rejection_reasons"].tolist() == [
        ["duplicate_account"],
        ["unknown_customer_id"],
        ["unknown_branch_id"],
        ["invalid_balance"],
        ["missing_account_id"],
        ["invalid_account_type"],
    ]
    assert len(rejected_customers) == 4


@pytest.fixture
def valid_branch():
    return {
        "branch_id": "B001",
        "branch_name": "BankFlow Demo Johannesburg",
        "city": "Johannesburg",
        "province": "Gauteng",
    }


@pytest.fixture
def accepted_accounts():
    return pd.DataFrame(
        [{"account_id": "A001", "opened_date": "2025-01-06"}]
    )


@pytest.fixture
def valid_transaction():
    return {
        "transaction_id": "T001",
        "account_id": "A001",
        "branch_id": "B001",
        "transaction_type": "deposit",
        "amount": "1500.00",
        "transaction_date": "2025-06-01",
    }


@pytest.fixture
def valid_payment():
    return {
        "payment_id": "P001",
        "account_id": "A001",
        "payee": "Demo Utilities",
        "amount": "450.00",
        "payment_date": "2025-06-01",
        "status": "completed",
    }


def test_valid_branch_is_accepted_and_source_values_are_preserved(validator, valid_branch):
    source = pd.DataFrame([valid_branch])

    accepted, rejected = validator.validate_branches(source)

    pd.testing.assert_frame_equal(accepted, source)
    assert rejected.empty
    assert list(rejected.columns) == [*source.columns, "rejection_reasons"]


@pytest.mark.parametrize(
    "field,missing",
    [
        (field, missing)
        for field in ("branch_id", "branch_name", "city", "province")
        for missing in (None, float("nan"), pd.NA, "", "   ")
    ],
)
def test_missing_required_branch_fields_are_rejected(
    validator, valid_branch, field, missing
):
    valid_branch[field] = missing
    _, rejected = validator.validate_branches(pd.DataFrame([valid_branch]))

    assert rejected.iloc[0]["rejection_reasons"] == [f"missing_{field}"]


@pytest.mark.parametrize("province", [" gauteng ", "WESTERN CAPE", "KZN"])
def test_south_african_province_variants_are_validated(validator, valid_branch, province):
    valid_branch["province"] = province
    accepted, rejected = validator.validate_branches(pd.DataFrame([valid_branch]))

    assert len(accepted) == 1
    assert rejected.empty


def test_unknown_province_is_rejected(validator, valid_branch):
    valid_branch["province"] = "Atlantis"
    _, rejected = validator.validate_branches(pd.DataFrame([valid_branch]))

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_province"]


def test_exact_duplicate_branches_keep_first_occurrence(validator, valid_branch):
    source = pd.DataFrame([valid_branch, valid_branch], index=[10, 20])

    accepted, rejected = validator.validate_branches(source)

    pd.testing.assert_frame_equal(accepted, source.iloc[[0]])
    pd.testing.assert_frame_equal(rejected[source.columns], source.iloc[[1]])
    assert rejected["rejection_reasons"].tolist() == [["duplicate_branch"]]


def test_branch_validation_rejects_missing_schema_and_does_not_mutate_input(
    validator, valid_branch
):
    source = pd.DataFrame([valid_branch])
    original = source.copy(deep=True)
    with pytest.raises(ValueError, match="Missing branch columns: province"):
        validator.validate_branches(source.drop(columns="province"))

    validator.validate_branches(source)
    pd.testing.assert_frame_equal(source, original)


def test_valid_transaction_is_accepted_and_source_values_are_preserved(
    validator, valid_transaction, accepted_accounts, valid_branches
):
    source = pd.DataFrame([valid_transaction])

    accepted, rejected = validator.validate_transactions(
        source, accepted_accounts, valid_branches
    )

    pd.testing.assert_frame_equal(accepted, source)
    assert rejected.empty
    assert list(rejected.columns) == [*source.columns, "rejection_reasons"]


@pytest.mark.parametrize(
    "field,missing",
    [
        (field, missing)
        for field in (
            "transaction_id", "account_id", "branch_id", "transaction_type",
            "amount", "transaction_date",
        )
        for missing in (None, float("nan"), pd.NA, "", "   ")
    ],
)
def test_missing_required_transaction_fields_are_rejected(
    validator, valid_transaction, accepted_accounts, valid_branches, field, missing
):
    valid_transaction[field] = missing
    _, rejected = validator.validate_transactions(
        pd.DataFrame([valid_transaction]), accepted_accounts, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == [f"missing_{field}"]


@pytest.mark.parametrize("transaction_type", ["refund", "cashback", "unknown"])
def test_unsupported_transaction_type_is_rejected(
    validator, valid_transaction, accepted_accounts, valid_branches, transaction_type
):
    valid_transaction["transaction_type"] = transaction_type
    _, rejected = validator.validate_transactions(
        pd.DataFrame([valid_transaction]), accepted_accounts, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_transaction_type"]


@pytest.mark.parametrize("amount", ["invalid", "1.234", "Infinity", "NaN"])
def test_invalid_transaction_amount_is_rejected(
    validator, valid_transaction, accepted_accounts, valid_branches, amount
):
    valid_transaction["amount"] = amount
    _, rejected = validator.validate_transactions(
        pd.DataFrame([valid_transaction]), accepted_accounts, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_amount"]


@pytest.mark.parametrize("amount", ["0.00", "-25.00"])
def test_nonpositive_transaction_amount_is_rejected(
    validator, valid_transaction, accepted_accounts, valid_branches, amount
):
    valid_transaction["amount"] = amount
    _, rejected = validator.validate_transactions(
        pd.DataFrame([valid_transaction]), accepted_accounts, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["nonpositive_amount"]


@pytest.mark.parametrize("transaction_date", ["not-a-date", "2025-02-30", "2025/13/01"])
def test_invalid_transaction_date_is_rejected(
    validator, valid_transaction, accepted_accounts, valid_branches, transaction_date
):
    valid_transaction["transaction_date"] = transaction_date
    _, rejected = validator.validate_transactions(
        pd.DataFrame([valid_transaction]), accepted_accounts, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_transaction_date"]


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("account_id", "A999", "unknown_account_id"),
        ("branch_id", "B999", "unknown_branch_id"),
    ],
)
def test_unknown_transaction_references_are_rejected(
    validator, valid_transaction, accepted_accounts, valid_branches, field, value, reason
):
    valid_transaction[field] = value
    _, rejected = validator.validate_transactions(
        pd.DataFrame([valid_transaction]), accepted_accounts, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == [reason]


@pytest.mark.parametrize("transaction_date", ["2025-01-05", "05/01/2025", "2025/01/05"])
def test_transaction_before_account_opening_is_rejected(
    validator, valid_transaction, accepted_accounts, valid_branches, transaction_date
):
    valid_transaction["transaction_date"] = transaction_date
    _, rejected = validator.validate_transactions(
        pd.DataFrame([valid_transaction]), accepted_accounts, valid_branches
    )

    assert rejected.iloc[0]["rejection_reasons"] == [
        "transaction_date_before_account_opened_date"
    ]


def test_exact_duplicate_transactions_keep_first_occurrence(
    validator, valid_transaction, accepted_accounts, valid_branches
):
    source = pd.DataFrame([valid_transaction, valid_transaction], index=[10, 20])

    accepted, rejected = validator.validate_transactions(
        source, accepted_accounts, valid_branches
    )

    pd.testing.assert_frame_equal(accepted, source.iloc[[0]])
    pd.testing.assert_frame_equal(rejected[source.columns], source.iloc[[1]])
    assert rejected["rejection_reasons"].tolist() == [["duplicate_transaction"]]


def test_valid_payment_is_accepted_and_source_values_are_preserved(
    validator, valid_payment, accepted_accounts
):
    source = pd.DataFrame([valid_payment])

    accepted, rejected = validator.validate_payments(source, accepted_accounts)

    pd.testing.assert_frame_equal(accepted, source)
    assert rejected.empty
    assert list(rejected.columns) == [*source.columns, "rejection_reasons"]


@pytest.mark.parametrize(
    "field,missing",
    [
        (field, missing)
        for field in (
            "payment_id", "account_id", "payee", "amount", "payment_date", "status"
        )
        for missing in (None, float("nan"), pd.NA, "", "   ")
    ],
)
def test_missing_required_payment_fields_are_rejected(
    validator, valid_payment, accepted_accounts, field, missing
):
    valid_payment[field] = missing
    _, rejected = validator.validate_payments(
        pd.DataFrame([valid_payment]), accepted_accounts
    )

    assert rejected.iloc[0]["rejection_reasons"] == [f"missing_{field}"]


@pytest.mark.parametrize("status", ["unknown", "cancelled", "refunded"])
def test_unsupported_payment_status_is_rejected(
    validator, valid_payment, accepted_accounts, status
):
    valid_payment["status"] = status
    _, rejected = validator.validate_payments(
        pd.DataFrame([valid_payment]), accepted_accounts
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_status"]


@pytest.mark.parametrize("amount", ["invalid", "1.234", "Infinity", "NaN"])
def test_invalid_payment_amount_is_rejected(
    validator, valid_payment, accepted_accounts, amount
):
    valid_payment["amount"] = amount
    _, rejected = validator.validate_payments(
        pd.DataFrame([valid_payment]), accepted_accounts
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_amount"]


@pytest.mark.parametrize("amount", ["0.00", "-75.00"])
def test_nonpositive_payment_amount_is_rejected(
    validator, valid_payment, accepted_accounts, amount
):
    valid_payment["amount"] = amount
    _, rejected = validator.validate_payments(
        pd.DataFrame([valid_payment]), accepted_accounts
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["nonpositive_amount"]


@pytest.mark.parametrize("payment_date", ["not-a-date", "2025-02-30", "2025/13/01"])
def test_invalid_payment_date_is_rejected(
    validator, valid_payment, accepted_accounts, payment_date
):
    valid_payment["payment_date"] = payment_date
    _, rejected = validator.validate_payments(
        pd.DataFrame([valid_payment]), accepted_accounts
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["invalid_payment_date"]


def test_unknown_payment_account_is_rejected(validator, valid_payment, accepted_accounts):
    valid_payment["account_id"] = "A999"
    _, rejected = validator.validate_payments(
        pd.DataFrame([valid_payment]), accepted_accounts
    )

    assert rejected.iloc[0]["rejection_reasons"] == ["unknown_account_id"]


@pytest.mark.parametrize("payment_date", ["2025-01-05", "05/01/2025", "2025/01/05"])
def test_payment_before_account_opening_is_rejected(
    validator, valid_payment, accepted_accounts, payment_date
):
    valid_payment["payment_date"] = payment_date
    _, rejected = validator.validate_payments(
        pd.DataFrame([valid_payment]), accepted_accounts
    )

    assert rejected.iloc[0]["rejection_reasons"] == [
        "payment_date_before_account_opened_date"
    ]


def test_exact_duplicate_payments_keep_first_occurrence(
    validator, valid_payment, accepted_accounts
):
    source = pd.DataFrame([valid_payment, valid_payment], index=[10, 20])

    accepted, rejected = validator.validate_payments(source, accepted_accounts)

    pd.testing.assert_frame_equal(accepted, source.iloc[[0]])
    pd.testing.assert_frame_equal(rejected[source.columns], source.iloc[[1]])
    assert rejected["rejection_reasons"].tolist() == [["duplicate_payment"]]
