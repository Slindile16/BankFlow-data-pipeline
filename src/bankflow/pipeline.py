"""Run the BankFlow ingestion, validation, and transformation workflow."""

import json
from pathlib import Path

from bankflow.data_ingestor import DataIngestor
from bankflow.data_transformer import DataTransformer
from bankflow.data_validator import DataValidator


class DataPipeline:
    """Process all configured source datasets and write CSV outputs."""

    DATASETS = ("branches", "customers", "accounts", "transactions", "payments")

    def __init__(self, raw_data_folder, processed_data_folder, rejected_data_folder):
        self.ingestor = DataIngestor(raw_data_folder)
        self.processed_data_folder = Path(processed_data_folder)
        self.rejected_data_folder = Path(rejected_data_folder)
        self.validator = DataValidator()
        self.transformer = DataTransformer()

    @staticmethod
    def _write_rejected(frame, path):
        """Store reason lists as JSON strings so they remain readable in CSV."""
        output = frame.copy()
        if "rejection_reasons" in output.columns:
            output["rejection_reasons"] = output["rejection_reasons"].map(
                json.dumps
            )
        output.to_csv(path, index=False)

    def run(self):
        """Validate in dependency order, transform accepted rows, and write outputs.

        Returns a mapping from dataset name to its transformed accepted frame and
        original-value rejected frame.
        """
        source = self.ingestor.load_all_data()

        accepted_branches, rejected_branches = self.validator.validate_branches(
            source["branches"]
        )
        accepted_customers, rejected_customers = self.validator.validate_customers(
            source["customers"]
        )
        accepted_accounts, rejected_accounts = self.validator.validate_accounts(
            source["accounts"], accepted_customers, accepted_branches
        )
        accepted_transactions, rejected_transactions = (
            self.validator.validate_transactions(
                source["transactions"], accepted_accounts, accepted_branches
            )
        )
        accepted_payments, rejected_payments = self.validator.validate_payments(
            source["payments"], accepted_accounts
        )

        accepted = {
            "branches": self.transformer.transform_branches(accepted_branches),
            "customers": self.transformer.transform_customers(accepted_customers),
            "accounts": self.transformer.transform_accounts(accepted_accounts),
            "transactions": self.transformer.transform_transactions(
                accepted_transactions
            ),
            "payments": self.transformer.transform_payments(accepted_payments),
        }
        rejected = {
            "branches": rejected_branches,
            "customers": rejected_customers,
            "accounts": rejected_accounts,
            "transactions": rejected_transactions,
            "payments": rejected_payments,
        }

        self.processed_data_folder.mkdir(parents=True, exist_ok=True)
        self.rejected_data_folder.mkdir(parents=True, exist_ok=True)
        for name in self.DATASETS:
            accepted[name].to_csv(
                self.processed_data_folder / f"{name}.csv", index=False
            )
            self._write_rejected(
                rejected[name], self.rejected_data_folder / f"{name}.csv"
            )

        return {
            name: {"accepted": accepted[name], "rejected": rejected[name]}
            for name in self.DATASETS
        }


def main():
    """Run the pipeline using the repository's standard data folders."""
    project_root = Path(__file__).resolve().parents[2]
    pipeline = DataPipeline(
        raw_data_folder=project_root / "data" / "raw",
        processed_data_folder=project_root / "data" / "processed",
        rejected_data_folder=project_root / "data" / "rejected",
    )
    results = pipeline.run()
    for name, frames in results.items():
        print(
            f"{name}: {len(frames['accepted'])} accepted, "
            f"{len(frames['rejected'])} rejected"
        )


if __name__ == "__main__":
    main()
