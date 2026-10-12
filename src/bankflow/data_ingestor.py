import logging
from pathlib import Path

import pandas as pd
from bankflow.logging_config import configure_logging

logger = logging.getLogger(__name__)


class DataIngestor:

    def __init__(self, raw_data_folder):
        self.raw_data_folder = Path(raw_data_folder)

    def read_csv(self, filename):
        file_path = self.raw_data_folder / filename
        try:
            data = pd.read_csv(file_path)
        except Exception:
            logger.exception("Failed to read CSV file %s", file_path)
            raise
        logger.info("Loaded CSV file %s: %d rows", file_path.name, len(data))
        return data

    def read_json(self, filename):
        file_path = self.raw_data_folder / filename
        try:
            data = pd.read_json(file_path)
        except Exception:
            logger.exception("Failed to read JSON file %s", file_path)
            raise
        logger.info("Loaded JSON file %s: %d rows", file_path.name, len(data))
        return data

    def load_all_data(self):
        return {
            "branches": self.read_csv("branches.csv"),
            "customers": self.read_csv("customers.csv"),
            "accounts": self.read_csv("accounts.csv"),
            "transactions": self.read_csv("transactions.csv"),
            "payments": self.read_json("payments.json"),
        }


if __name__ == "__main__":
    configure_logging()
    ingestor = DataIngestor("data/raw")
    datasets = ingestor.load_all_data()

    for name, data in datasets.items():
        print(f"\n{name.upper()}")
        print(data.head())
