"""Standardize accepted customer and branch records for downstream use."""

from datetime import date, datetime

import pandas as pd


class DataTransformer:
    """Return cleaned copies of accepted source DataFrames."""

    CUSTOMER_COLUMNS = (
        "customer_id", "first_name", "last_name", "province", "join_date"
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
