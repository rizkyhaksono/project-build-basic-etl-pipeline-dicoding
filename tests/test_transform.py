"""Unit tests for utils.transform."""

import unittest

import pandas as pd

from utils.transform import transform_data, transform_to_dataframe


def sample_raw_data():
    """A mix of clean rows and every dirty pattern from the rubric."""
    return [
        # Clean row
        {
            "Title": "T-shirt 2",
            "Price": "$102.15",
            "Rating": "⭐ 3.9 / 5",
            "Colors": "3 Colors",
            "Size": "Size: M",
            "Gender": "Gender: Women",
            "timestamp": "2025-02-10T13:54:32",
        },
        # Invalid Title
        {
            "Title": "Unknown Product",
            "Price": "$100.00",
            "Rating": "⭐ Invalid Rating / 5",
            "Colors": "5 Colors",
            "Size": "Size: M",
            "Gender": "Gender: Men",
            "timestamp": "2025-02-10T13:54:32",
        },
        # Unavailable Price + Not Rated
        {
            "Title": "Pants 46",
            "Price": "Price Unavailable",
            "Rating": "Not Rated",
            "Colors": "8 Colors",
            "Size": "Size: S",
            "Gender": "Gender: Men",
            "timestamp": "2025-02-10T13:54:32",
        },
        # Duplicate of the first clean row
        {
            "Title": "T-shirt 2",
            "Price": "$102.15",
            "Rating": "⭐ 3.9 / 5",
            "Colors": "3 Colors",
            "Size": "Size: M",
            "Gender": "Gender: Women",
            "timestamp": "2025-02-10T13:54:32",
        },
        # Another clean, unique row
        {
            "Title": "Hoodie 3",
            "Price": "$496.88",
            "Rating": "⭐ 4.8 / 5",
            "Colors": "3 Colors",
            "Size": "Size: L",
            "Gender": "Gender: Unisex",
            "timestamp": "2025-02-10T13:54:32",
        },
    ]


class TestTransformToDataFrame(unittest.TestCase):
    def test_returns_dataframe(self):
        df = transform_to_dataframe(sample_raw_data())
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 5)

    def test_invalid_input_returns_empty(self):
        df = transform_to_dataframe(123)  # not list-like
        self.assertTrue(df.empty)


class TestTransformData(unittest.TestCase):
    def setUp(self):
        self.df = transform_data(transform_to_dataframe(sample_raw_data()))

    def test_removes_dirty_and_duplicate_rows(self):
        # 5 raw -> drop Unknown Product, drop Price Unavailable, drop 1 duplicate = 2
        self.assertEqual(len(self.df), 2)
        self.assertNotIn("Unknown Product", self.df["Title"].values)
        self.assertNotIn("Price Unavailable", self.df["Price"].values)

    def test_price_converted_to_rupiah(self):
        # 102.15 * 16000 = 1634400.0
        row = self.df[self.df["Title"] == "T-shirt 2"].iloc[0]
        self.assertAlmostEqual(row["Price"], 1634400.0)

    def test_column_dtypes(self):
        self.assertEqual(self.df["Title"].dtype, object)
        self.assertEqual(self.df["Price"].dtype, "float64")
        self.assertEqual(self.df["Rating"].dtype, "float64")
        self.assertEqual(self.df["Colors"].dtype, "int64")
        self.assertEqual(self.df["Size"].dtype, object)
        self.assertEqual(self.df["Gender"].dtype, object)

    def test_size_and_gender_stripped(self):
        values = set(self.df["Size"].values)
        self.assertTrue(all("Size:" not in v for v in values))
        genders = set(self.df["Gender"].values)
        self.assertTrue(all("Gender:" not in g for g in genders))

    def test_no_nulls(self):
        self.assertFalse(self.df.isnull().any().any())

    def test_rating_is_float_value(self):
        row = self.df[self.df["Title"] == "Hoodie 3"].iloc[0]
        self.assertAlmostEqual(row["Rating"], 4.8)

    def test_error_handling_missing_column(self):
        # A DataFrame without the expected columns should not raise.
        broken = pd.DataFrame({"foo": [1, 2]})
        result = transform_data(broken)
        self.assertIsInstance(result, pd.DataFrame)


if __name__ == "__main__":
    unittest.main()
