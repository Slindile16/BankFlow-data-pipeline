from pathlib import Path

import pandas as pd


class DataIngestor:

    def __init__(self, raw_data_folder):
        self.raw_data_folder = Path(raw_data_folder)

    def read_csv(self, filename):
        file_path = self.raw_data_folder / filename
        return pd.read_csv(file_path)

    def read_json(self, filename):
        file_path = self.raw_data_folder / filename
        return pd.read_json(file_path)

    def load_all_data(self):
        return {
            "branches": self.read_csv("branches.csv"),
            "customers": self.read_csv("customers.csv"),
            "accounts": self.read_csv("accounts.csv"),
            "transactions": self.read_csv("transactions.csv"),
            "payments": self.read_json("payments.json"),
        }


if __name__ == "__main__":
    ingestor = DataIngestor("data/raw")
    datasets = ingestor.load_all_data()

    for name, data in datasets.items():
        print(f"\n{name.upper()}")
        print(data.head())