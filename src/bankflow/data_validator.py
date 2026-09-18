"""Validate source records without changing their original values."""

from datetime import datetime

import pandas as pd


class DataValidator:
    """Separate accepted records from records with validation issues."""

    CUSTOMER_COLUMNS = (
        "customer_id", "first_name", "last_name", "province", "join_date"
    )
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
