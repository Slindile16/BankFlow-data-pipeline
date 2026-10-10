"""Standardize accepted banking records for downstream use."""

from datetime import date, datetime
from decimal import Decimal

import pandas as pd


class DataTransformer:
    """Return cleaned copies of accepted source DataFrames."""

    CUSTOMER_COLUMNS = (
        "customer_id", "first_name", "last_name", "province", "join_date"
    )
    BRANCH_COLUMNS = ("branch_id", "branch_name", "city", "province")
    ACCOUNT_COLUMNS = (
        "account_id", "customer_id", "branch_id", "account_type", "balance", "opened_date"
    )
    DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d")
    PROVINCES = {
        "eastern cape": "Eastern Cape",
        "free state": "Free State",
        "gauteng": "Gauteng",
        "kwazulu-natal": "KwaZulu-Natal",
        "limpopo": "Limpopo",
        "mpumalanga": "Mpumalanga",
        "north west": "North West",
        "northern cape": "Northern Cape",
        "western cape": "Western Cape",
    }

    @classmethod
    def _normalize_province(cls, value):
        if not isinstance(value, str):
            raise ValueError(f"Unknown South African province: {value!r}")
        province = " ".join(value.strip().casefold().split())
        if province == "kzn":
            province = "kwazulu-natal"
        try:
            return cls.PROVINCES[province]
        except KeyError as error:
            raise ValueError(f"Unknown South African province: {value!r}") from error

    @classmethod
    def _normalize_date(cls, value, field):
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if not isinstance(value, str):
            raise ValueError(f"Invalid date in {field}: {value!r}")

        value = value.strip()
        for date_format in cls.DATE_FORMATS:
            try:
                parsed = datetime.strptime(value, date_format)
            except ValueError:
                continue
            if parsed.strftime(date_format) == value:
                return parsed.date().isoformat()
        raise ValueError(f"Invalid date in {field}: {value!r}")

    @classmethod
    def _prepare(cls, frame, required_columns, dataset_name):
        missing = set(required_columns) - set(frame.columns)
        if missing:
            raise ValueError(
                f"Missing {dataset_name} columns: {', '.join(sorted(missing))}"
            )

        result = frame.copy()
        for column in result.columns:
            result[column] = result[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
        return result

    def transform_customers(self, customers):
        """Trim customer text, canonicalize provinces, and standardize join dates."""
        result = self._prepare(customers, self.CUSTOMER_COLUMNS, "customer")
        result["province"] = result["province"].map(self._normalize_province)
        result["join_date"] = result["join_date"].map(
            lambda value: self._normalize_date(value, "join_date")
        )
        return result

    def transform_branches(self, branches):
        """Trim branch text and canonicalize province names."""
        result = self._prepare(branches, self.BRANCH_COLUMNS, "branch")
        result["province"] = result["province"].map(self._normalize_province)
        return result

    def transform_accounts(self, accounts):
        """Trim account fields, normalize account types, balances, and dates."""
        result = self._prepare(accounts, self.ACCOUNT_COLUMNS, "account")
        result["account_type"] = result["account_type"].map(
            lambda value: str(value).casefold()
        )
        result["balance"] = result["balance"].map(lambda value: Decimal(str(value)))
        result["opened_date"] = result["opened_date"].map(
            lambda value: self._normalize_date(value, "opened_date")
        )
        return result
