"""Transformation contracts for customers, branches, accounts and activity."""

from decimal import Decimal

import pandas as pd
import pytest

from bankflow.data_transformer import DataTransformer


@pytest.fixture
def transformer():
    return DataTransformer()


def test_transform_customer_trims_text_normalizes_province_and_date(transformer):
    source = pd.DataFrame(
        [
            {
                "customer_id": " C008 ",
                "first_name": " Zola ",
                "last_name": " Sample ",
                "province": " kZn ",
                "join_date": "15/03/2025",
            }
        ],
        index=[8],
    )

    result = transformer.transform_customers(source)

    expected = pd.DataFrame(
        [
            {
                "customer_id": "C008",
                "first_name": "Zola",
                "last_name": "Sample",
                "province": "KwaZulu-Natal",
                "join_date": "2025-03-15",
            }
        ],
        index=[8],
    )
    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    "join_date",
    ["2025-04-02", "02/04/2025", "2025/04/02"],
)
def test_transform_customer_standardizes_supported_date_formats(transformer, join_date):
    source = pd.DataFrame(
        [{
            "customer_id": "C007",
            "first_name": "Ethan",
            "last_name": "Demo",
            "province": "western cape",
            "join_date": join_date,
        }]
    )

    result = transformer.transform_customers(source)

    assert result.loc[0, "join_date"] == "2025-04-02"
    assert result.loc[0, "province"] == "Western Cape"


def test_transform_branches_trims_text_and_normalizes_province(transformer):
    source = pd.DataFrame(
        [{
            "branch_id": " B003 ",
            "branch_name": " BankFlow Durban ",
            "city": " Durban ",
            "province": " KZN ",
        }]
    )

    result = transformer.transform_branches(source)

    assert result.iloc[0].to_dict() == {
        "branch_id": "B003",
        "branch_name": "BankFlow Durban",
        "city": "Durban",
        "province": "KwaZulu-Natal",
    }


@pytest.mark.parametrize("province", ["Atlantis", "", "Unknown Province"])
def test_transform_rejects_unknown_customer_province(transformer, province):
    source = pd.DataFrame(
        [{
            "customer_id": "C001",
            "first_name": "Amahle",
            "last_name": "Demo",
            "province": province,
            "join_date": "2025-01-05",
        }]
    )

    with pytest.raises(ValueError, match="Unknown South African province"):
        transformer.transform_customers(source)


def test_transform_rejects_invalid_customer_date(transformer):
    source = pd.DataFrame(
        [{
            "customer_id": "C001",
            "first_name": "Amahle",
            "last_name": "Demo",
            "province": "Gauteng",
            "join_date": "2025-02-30",
        }]
    )

    with pytest.raises(ValueError, match="Invalid date in join_date"):
        transformer.transform_customers(source)


def test_transforms_do_not_mutate_source_data(transformer):
    customers = pd.DataFrame(
        [{
            "customer_id": " C001 ",
            "first_name": " Amahle ",
            "last_name": " Demo ",
            "province": " gauteng ",
            "join_date": "05/01/2025",
        }]
    )
    branches = pd.DataFrame(
        [{"branch_id": " B001 ", "branch_name": " Demo ", "city": " Joburg ", "province": " Gauteng "}]
    )
    customer_original = customers.copy(deep=True)
    branch_original = branches.copy(deep=True)

    transformer.transform_customers(customers)
    transformer.transform_branches(branches)

    pd.testing.assert_frame_equal(customers, customer_original)
    pd.testing.assert_frame_equal(branches, branch_original)


def test_empty_customer_and_branch_frames_keep_their_columns(transformer):
    customers = pd.DataFrame(
        columns=["customer_id", "first_name", "last_name", "province", "join_date"]
    )
    branches = pd.DataFrame(columns=["branch_id", "branch_name", "city", "province"])

    pd.testing.assert_frame_equal(transformer.transform_customers(customers), customers)
    pd.testing.assert_frame_equal(transformer.transform_branches(branches), branches)


@pytest.fixture
def valid_account():
    return {
        "account_id": " A006 ",
        "customer_id": " C006 ",
        "branch_id": " B001 ",
        "account_type": " Savings ",
        "balance": "1800.00",
        "opened_date": "16/03/2025",
    }


@pytest.fixture
def valid_transaction():
    return {
        "transaction_id": " T007 ",
        "account_id": " A007 ",
        "branch_id": " B002 ",
        "transaction_type": " CARD PAYMENT ",
        "amount": "125.75",
        "transaction_date": "2025/06/04",
    }


@pytest.fixture
def valid_payment():
    return {
        "payment_id": " P004 ",
        "account_id": " A004 ",
        "payee": " Demo Services ",
        "amount": "80.00",
        "payment_date": "14/06/2025",
        "status": " COMPLETED ",
    }


def test_transform_account_standardizes_text_category_balance_and_date(transformer, valid_account):
    source = pd.DataFrame([valid_account], index=[6])

    result = transformer.transform_accounts(source)

    expected = pd.DataFrame(
        [
            {
                "account_id": "A006",
                "customer_id": "C006",
                "branch_id": "B001",
                "account_type": "savings",
                "balance": Decimal("1800.00"),
                "opened_date": "2025-03-16",
            }
        ],
        index=[6],
    )
    pd.testing.assert_frame_equal(result, expected)


def test_transform_transaction_standardizes_type_amount_and_date(transformer, valid_transaction):
    source = pd.DataFrame([valid_transaction])

    result = transformer.transform_transactions(source)

    assert result.iloc[0].to_dict() == {
        "transaction_id": "T007",
        "account_id": "A007",
        "branch_id": "B002",
        "transaction_type": "card_payment",
        "amount": Decimal("125.75"),
        "transaction_date": "2025-06-04",
    }


def test_transform_payment_standardizes_status_amount_and_date(transformer, valid_payment):
    source = pd.DataFrame([valid_payment])

    result = transformer.transform_payments(source)

    assert result.iloc[0].to_dict() == {
        "payment_id": "P004",
        "account_id": "A004",
        "payee": "Demo Services",
        "amount": Decimal("80.00"),
        "payment_date": "2025-06-14",
        "status": "completed",
    }


def test_account_transaction_and_payment_transforms_do_not_mutate_inputs(
    transformer, valid_account, valid_transaction, valid_payment
):
    accounts = pd.DataFrame([valid_account])
    transactions = pd.DataFrame([valid_transaction])
    payments = pd.DataFrame([valid_payment])
    originals = [frame.copy(deep=True) for frame in (accounts, transactions, payments)]

    transformer.transform_accounts(accounts)
    transformer.transform_transactions(transactions)
    transformer.transform_payments(payments)

    for frame, original in zip((accounts, transactions, payments), originals):
        pd.testing.assert_frame_equal(frame, original)
