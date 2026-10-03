"""Validate source records without changing their original values."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd


class DataValidator:
    """Separate accepted records from records with validation issues."""

    CUSTOMER_COLUMNS = (
        "customer_id", "first_name", "last_name", "province", "join_date"
    )
    ACCOUNT_COLUMNS = (
        "account_id", "customer_id", "branch_id", "account_type", "balance", "opened_date"
    )
    ACCOUNT_TYPES = {"savings", "current"}
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

        if isinstance(branches, pd.DataFrame):
            if "branch_id" not in branches.columns:
                raise ValueError("Missing branch columns: branch_id")
            branch_ids = branches["branch_id"].dropna().astype(str).str.strip()
        else:
            branch_ids = pd.Series([str(value).strip() for value in branches])
        valid_branch_ids = set(branch_ids)

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
