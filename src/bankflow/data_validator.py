"""Validate source records without changing their original values."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd


class DataValidator:
    """Separate accepted records from records with validation issues."""

    CUSTOMER_COLUMNS = (
        "customer_id", "first_name", "last_name", "province", "join_date"
    )
    BRANCH_COLUMNS = ("branch_id", "branch_name", "city", "province")
    ACCOUNT_COLUMNS = (
        "account_id", "customer_id", "branch_id", "account_type", "balance", "opened_date"
    )
    TRANSACTION_COLUMNS = (
        "transaction_id", "account_id", "branch_id", "transaction_type", "amount",
        "transaction_date",
    )
    PAYMENT_COLUMNS = (
        "payment_id", "account_id", "payee", "amount", "payment_date", "status"
    )
    ACCOUNT_TYPES = {"savings", "current"}
    TRANSACTION_TYPES = {"deposit", "withdrawal", "transfer", "card_payment"}
    PAYMENT_STATUSES = {"completed", "pending", "failed"}
    PROVINCES = {
        "eastern cape", "free state", "gauteng", "kwazulu-natal", "limpopo",
        "mpumalanga", "north west", "northern cape", "western cape",
    }
    DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d")

    @staticmethod
    def _is_missing(value):
        return pd.isna(value) or (isinstance(value, str) and not value.strip())

    @classmethod
    def _is_valid_date(cls, value):
        if not isinstance(value, str):
            return False
        value = value.strip()
        for date_format in cls.DATE_FORMATS:
            try:
                parsed = datetime.strptime(value, date_format)
            except ValueError:
                continue
            if parsed.strftime(date_format) == value:
                return True
        return False

    @classmethod
    def _parse_date(cls, value):
        if not isinstance(value, str):
            return None
        value = value.strip()
        for date_format in cls.DATE_FORMATS:
            try:
                parsed = datetime.strptime(value, date_format)
            except ValueError:
                continue
            if parsed.strftime(date_format) == value:
                return parsed.date()
        return None

    @staticmethod
    def _is_valid_balance(value):
        try:
            amount = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, AttributeError):
            return False
        return amount.is_finite() and amount.as_tuple().exponent >= -2

    @staticmethod
    def _account_open_dates(accepted_accounts):
        required = {"account_id", "opened_date"}
        missing = required - set(accepted_accounts.columns)
        if missing:
            raise ValueError(
                "Missing accepted account columns: "
                f"{', '.join(sorted(missing))}"
            )
        dates = {}
        for _, row in accepted_accounts.iterrows():
            if not DataValidator._is_missing(row["account_id"]):
                dates[str(row["account_id"]).strip()] = DataValidator._parse_date(
                    row["opened_date"]
                )
        return dates

    @staticmethod
    def _branch_ids(branches):
        if isinstance(branches, pd.DataFrame):
            if "branch_id" not in branches.columns:
                raise ValueError("Missing branch columns: branch_id")
            values = branches["branch_id"].dropna().astype(str).str.strip()
        else:
            values = (str(value).strip() for value in branches if not pd.isna(value))
        return {value for value in values if value}

    def validate_branches(self, branches):
        """Return accepted and rejected branches, retaining the original values."""
        missing_columns = set(self.BRANCH_COLUMNS) - set(branches.columns)
        if missing_columns:
            raise ValueError(
                f"Missing branch columns: {', '.join(sorted(missing_columns))}"
            )
        if "rejection_reasons" in branches.columns:
            raise ValueError("Input must not contain the reserved rejection_reasons column")

        duplicates = branches.duplicated(subset=list(self.BRANCH_COLUMNS), keep="first")
        all_reasons = []
        for position, (_, row) in enumerate(branches.iterrows()):
            reasons = []
            for field in self.BRANCH_COLUMNS:
                if self._is_missing(row[field]):
                    reasons.append(f"missing_{field}")

            if not self._is_missing(row["province"]):
                province = " ".join(str(row["province"]).strip().casefold().split())
                if province == "kzn":
                    province = "kwazulu-natal"
                if province not in self.PROVINCES:
                    reasons.append("invalid_province")

            if duplicates.iloc[position]:
                reasons.append("duplicate_branch")
            all_reasons.append(reasons)

        accepted_positions = [i for i, reasons in enumerate(all_reasons) if not reasons]
        rejected_positions = [i for i, reasons in enumerate(all_reasons) if reasons]
        accepted = branches.iloc[accepted_positions].copy()
        rejected = branches.iloc[rejected_positions].copy()
        rejected["rejection_reasons"] = [all_reasons[i] for i in rejected_positions]
        return accepted, rejected

    def validate_customers(self, customers):
        """Return (accepted, rejected), retaining source columns and indices.

        Check required IDs/names, join dates and exact duplicates. Each rejected
        row receives a list of reason codes in ``rejection_reasons``. Province
        validation and conflicting records sharing an ID are not covered yet.
        """
        missing_columns = set(self.CUSTOMER_COLUMNS) - set(customers.columns)
        if missing_columns:
            raise ValueError(f"Missing customer columns: {', '.join(sorted(missing_columns))}")
        if "rejection_reasons" in customers.columns:
            raise ValueError("Input must not contain the reserved rejection_reasons column")

        duplicates = customers.duplicated(subset=list(self.CUSTOMER_COLUMNS), keep="first")
        all_reasons = []
        for position, (_, row) in enumerate(customers.iterrows()):
            reasons = []
            for field in ("customer_id", "first_name", "last_name", "join_date"):
                if self._is_missing(row[field]):
                    reasons.append(f"missing_{field}")

            if not self._is_missing(row["join_date"]) and not self._is_valid_date(row["join_date"]):
                reasons.append("invalid_join_date")
            if duplicates.iloc[position]:
                reasons.append("duplicate_customer")
            all_reasons.append(reasons)

        # Select by position so repeated input index labels remain independent.
        accepted_positions = [i for i, reasons in enumerate(all_reasons) if not reasons]
        rejected_positions = [i for i, reasons in enumerate(all_reasons) if reasons]
        accepted = customers.iloc[accepted_positions].copy()
        rejected = customers.iloc[rejected_positions].copy()
        rejected["rejection_reasons"] = [all_reasons[i] for i in rejected_positions]
        return accepted, rejected

    def validate_accounts(self, accounts, accepted_customers, branches):
        """Return (accepted, rejected) account frames with source values retained.

        ``accepted_customers`` is the accepted output of ``validate_customers``.
        ``branches`` may be a branch DataFrame or an iterable of valid branch IDs.
        Rejected rows include reason codes in ``rejection_reasons``.
        """
        missing_columns = set(self.ACCOUNT_COLUMNS) - set(accounts.columns)
        if missing_columns:
            raise ValueError(f"Missing account columns: {', '.join(sorted(missing_columns))}")
        if "rejection_reasons" in accounts.columns:
            raise ValueError("Input must not contain the reserved rejection_reasons column")
        missing_customer_columns = {"customer_id", "join_date"} - set(accepted_customers.columns)
        if missing_customer_columns:
            raise ValueError(
                "Missing accepted customer columns: "
                f"{', '.join(sorted(missing_customer_columns))}"
            )

        valid_branch_ids = self._branch_ids(branches)

        customer_join_dates = {}
        for _, customer in accepted_customers.iterrows():
            if self._is_missing(customer["customer_id"]):
                continue
            customer_join_dates[str(customer["customer_id"]).strip()] = self._parse_date(
                customer["join_date"]
            )
        valid_customer_ids = set(customer_join_dates)

        duplicates = accounts.duplicated(subset=list(self.ACCOUNT_COLUMNS), keep="first")
        all_reasons = []
        for position, (_, row) in enumerate(accounts.iterrows()):
            reasons = []
            for field in self.ACCOUNT_COLUMNS:
                if self._is_missing(row[field]):
                    reasons.append(f"missing_{field}")

            customer_id = None if self._is_missing(row["customer_id"]) else str(row["customer_id"]).strip()
            branch_id = None if self._is_missing(row["branch_id"]) else str(row["branch_id"]).strip()
            if customer_id is not None and customer_id not in valid_customer_ids:
                reasons.append("unknown_customer_id")
            if branch_id is not None and branch_id not in valid_branch_ids:
                reasons.append("unknown_branch_id")

            if not self._is_missing(row["account_type"]):
                account_type = str(row["account_type"]).strip().casefold()
                if account_type not in self.ACCOUNT_TYPES:
                    reasons.append("invalid_account_type")

            if not self._is_missing(row["balance"]) and not self._is_valid_balance(row["balance"]):
                reasons.append("invalid_balance")

            if not self._is_missing(row["opened_date"]):
                opened_date = self._parse_date(row["opened_date"])
                if opened_date is None:
                    reasons.append("invalid_opened_date")
                elif customer_id in customer_join_dates:
                    join_date = customer_join_dates[customer_id]
                    if join_date is not None and opened_date < join_date:
                        reasons.append("opened_date_before_customer_join_date")

            if duplicates.iloc[position]:
                reasons.append("duplicate_account")
            all_reasons.append(reasons)

        accepted_positions = [i for i, reasons in enumerate(all_reasons) if not reasons]
        rejected_positions = [i for i, reasons in enumerate(all_reasons) if reasons]
        accepted = accounts.iloc[accepted_positions].copy()
        rejected = accounts.iloc[rejected_positions].copy()
        rejected["rejection_reasons"] = [all_reasons[i] for i in rejected_positions]
        return accepted, rejected

    def validate_transactions(self, transactions, accepted_accounts, branches):
        """Separate valid transactions from rejected rows without altering source values."""
        missing_columns = set(self.TRANSACTION_COLUMNS) - set(transactions.columns)
        if missing_columns:
            raise ValueError(
                f"Missing transaction columns: {', '.join(sorted(missing_columns))}"
            )
        if "rejection_reasons" in transactions.columns:
            raise ValueError("Input must not contain the reserved rejection_reasons column")

        account_open_dates = self._account_open_dates(accepted_accounts)
        valid_branch_ids = self._branch_ids(branches)
        duplicates = transactions.duplicated(
            subset=list(self.TRANSACTION_COLUMNS), keep="first"
        )
        all_reasons = []
        for position, (_, row) in enumerate(transactions.iterrows()):
            reasons = []
            for field in self.TRANSACTION_COLUMNS:
                if self._is_missing(row[field]):
                    reasons.append(f"missing_{field}")

            account_id = (
                None if self._is_missing(row["account_id"])
                else str(row["account_id"]).strip()
            )
            branch_id = (
                None if self._is_missing(row["branch_id"])
                else str(row["branch_id"]).strip()
            )
            if account_id is not None and account_id not in account_open_dates:
                reasons.append("unknown_account_id")
            if branch_id is not None and branch_id not in valid_branch_ids:
                reasons.append("unknown_branch_id")

            if not self._is_missing(row["transaction_type"]):
                normalized_type = " ".join(
                    str(row["transaction_type"]).strip().casefold().split()
                )
                if normalized_type == "card payment":
                    normalized_type = "card_payment"
                if normalized_type not in self.TRANSACTION_TYPES:
                    reasons.append("invalid_transaction_type")

            if not self._is_missing(row["amount"]):
                if not self._is_valid_balance(row["amount"]):
                    reasons.append("invalid_amount")
                elif Decimal(str(row["amount"]).strip()) <= 0:
                    reasons.append("nonpositive_amount")

            if not self._is_missing(row["transaction_date"]):
                transaction_date = self._parse_date(row["transaction_date"])
                if transaction_date is None:
                    reasons.append("invalid_transaction_date")
                elif account_id in account_open_dates:
                    opened_date = account_open_dates[account_id]
                    if opened_date is not None and transaction_date < opened_date:
                        reasons.append("transaction_date_before_account_opened_date")

            if duplicates.iloc[position]:
                reasons.append("duplicate_transaction")
            all_reasons.append(reasons)

        accepted_positions = [i for i, reasons in enumerate(all_reasons) if not reasons]
        rejected_positions = [i for i, reasons in enumerate(all_reasons) if reasons]
        accepted = transactions.iloc[accepted_positions].copy()
        rejected = transactions.iloc[rejected_positions].copy()
        rejected["rejection_reasons"] = [all_reasons[i] for i in rejected_positions]
        return accepted, rejected

    def validate_payments(self, payments, accepted_accounts):
        """Separate valid payments from rejected rows without altering source values."""
        missing_columns = set(self.PAYMENT_COLUMNS) - set(payments.columns)
        if missing_columns:
            raise ValueError(f"Missing payment columns: {', '.join(sorted(missing_columns))}")
        if "rejection_reasons" in payments.columns:
            raise ValueError("Input must not contain the reserved rejection_reasons column")

        account_open_dates = self._account_open_dates(accepted_accounts)
        duplicates = payments.duplicated(subset=list(self.PAYMENT_COLUMNS), keep="first")
        all_reasons = []
        for position, (_, row) in enumerate(payments.iterrows()):
            reasons = []
            for field in self.PAYMENT_COLUMNS:
                if self._is_missing(row[field]):
                    reasons.append(f"missing_{field}")

            account_id = (
                None if self._is_missing(row["account_id"])
                else str(row["account_id"]).strip()
            )
            if account_id is not None and account_id not in account_open_dates:
                reasons.append("unknown_account_id")

            if not self._is_missing(row["status"]):
                status = str(row["status"]).strip().casefold()
                if status not in self.PAYMENT_STATUSES:
                    reasons.append("invalid_status")

            if not self._is_missing(row["amount"]):
                if not self._is_valid_balance(row["amount"]):
                    reasons.append("invalid_amount")
                elif Decimal(str(row["amount"]).strip()) <= 0:
                    reasons.append("nonpositive_amount")

            if not self._is_missing(row["payment_date"]):
                payment_date = self._parse_date(row["payment_date"])
                if payment_date is None:
                    reasons.append("invalid_payment_date")
                elif account_id in account_open_dates:
                    opened_date = account_open_dates[account_id]
                    if opened_date is not None and payment_date < opened_date:
                        reasons.append("payment_date_before_account_opened_date")

            if duplicates.iloc[position]:
                reasons.append("duplicate_payment")
            all_reasons.append(reasons)

        accepted_positions = [i for i, reasons in enumerate(all_reasons) if not reasons]
        rejected_positions = [i for i, reasons in enumerate(all_reasons) if reasons]
        accepted = payments.iloc[accepted_positions].copy()
        rejected = payments.iloc[rejected_positions].copy()
        rejected["rejection_reasons"] = [all_reasons[i] for i in rejected_positions]
        return accepted, rejected
