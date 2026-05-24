"""Unit tests for utils.load."""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from utils.load import store_to_csv, store_to_google_sheets, store_to_postgresql


def sample_df():
    return pd.DataFrame(
        {
            "Title": ["T-shirt 2", "Hoodie 3"],
            "Price": [1634400.0, 7950080.0],
            "Rating": [3.9, 4.8],
            "Colors": [3, 3],
            "Size": ["M", "L"],
            "Gender": ["Women", "Unisex"],
            "timestamp": ["2025-02-10T13:54:32", "2025-02-10T13:54:32"],
        }
    )


class TestStoreToCsv(unittest.TestCase):
    @patch("pandas.DataFrame.to_csv")
    def test_store_to_csv_success(self, mock_to_csv):
        self.assertTrue(store_to_csv(sample_df(), "products.csv"))
        mock_to_csv.assert_called_once_with("products.csv", index=False)

    @patch("pandas.DataFrame.to_csv", side_effect=OSError("disk full"))
    def test_store_to_csv_failure(self, _mock_to_csv):
        self.assertFalse(store_to_csv(sample_df(), "products.csv"))


class TestStoreToPostgreSQL(unittest.TestCase):
    @patch("utils.load.create_engine")
    def test_store_to_postgresql_success(self, mock_create_engine):
        mock_engine = MagicMock()
        # engine.connect() is a context manager
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch("pandas.DataFrame.to_sql") as mock_to_sql:
            ok = store_to_postgresql(sample_df(), "postgresql://x", "fashion_products")
            self.assertTrue(ok)
            mock_to_sql.assert_called_once()

    @patch("utils.load.create_engine", side_effect=Exception("connection refused"))
    def test_store_to_postgresql_failure(self, _mock_create_engine):
        self.assertFalse(store_to_postgresql(sample_df(), "postgresql://x"))


class TestStoreToGoogleSheets(unittest.TestCase):
    @patch("utils.load.build")
    @patch("utils.load.service_account.Credentials.from_service_account_file")
    def test_store_to_google_sheets_success(self, mock_creds, mock_build):
        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        ok = store_to_google_sheets(sample_df(), "sheet-id", "Sheet1!A1", "creds.json")
        self.assertTrue(ok)
        mock_service.spreadsheets.return_value.values.return_value.update.assert_called_once()

    @patch(
        "utils.load.service_account.Credentials.from_service_account_file",
        side_effect=FileNotFoundError("no creds"),
    )
    def test_store_to_google_sheets_failure(self, _mock_creds):
        self.assertFalse(store_to_google_sheets(sample_df(), "sheet-id"))


if __name__ == "__main__":
    unittest.main()
