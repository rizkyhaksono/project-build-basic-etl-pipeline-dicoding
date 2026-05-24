"""Transform stage: clean and convert the scraped product data."""

import pandas as pd

# Invalid values that must be removed during cleaning (per the rubric).
DIRTY_PATTERNS = {
    "Title": ["Unknown Product"],
    "Rating": ["Invalid Rating / 5", "Not Rated"],
    "Price": ["Price Unavailable", None],
}


def transform_to_dataframe(data):
    """Convert a list of product dicts into a pandas DataFrame."""
    try:
        return pd.DataFrame(data)
    except (ValueError, TypeError) as error:
        print(f"Error building DataFrame: {error}")
        return pd.DataFrame()


def transform_data(df, exchange_rate=16000):
    """Clean the raw DataFrame and convert column types.

    Steps (order matters: drop dirty rows before casting types):
      - Drop invalid Title ("Unknown Product").
      - Drop unavailable Price, convert "$xxx" to rupiah float.
      - Drop invalid Rating, convert to float.
      - Convert Colors to int, strip "Size: " / "Gender: " prefixes.
      - Drop nulls and duplicates.
    Returns the cleaned DataFrame; on failure returns the input unchanged.
    """
    try:
        df = df.copy()

        # --- Title ---
        df = df[~df["Title"].isin(DIRTY_PATTERNS["Title"])]

        # --- Price: drop unavailable, then "$102.15" -> 102.15 * rate ---
        df = df[~df["Price"].isin(DIRTY_PATTERNS["Price"])]
        df = df.dropna(subset=["Price"])
        df["Price"] = (
            df["Price"].str.replace("$", "", regex=False).astype(float) * exchange_rate
        )

        # --- Rating: drop invalid, then extract the numeric value ---
        df = df[~df["Rating"].astype(str).str.contains("Invalid Rating|Not Rated", na=False)]
        df["Rating"] = df["Rating"].str.extract(r"(\d+\.?\d*)").astype(float)

        # --- Colors: "3 Colors" -> 3 ---
        df["Colors"] = df["Colors"].str.extract(r"(\d+)").astype("int64")

        # --- Size / Gender: drop the leading label ---
        df["Size"] = df["Size"].str.replace("Size: ", "", regex=False).str.strip()
        df["Gender"] = df["Gender"].str.replace("Gender: ", "", regex=False).str.strip()

        # --- Drop nulls and duplicates (index intentionally NOT reset) ---
        df = df.dropna()
        df = df.drop_duplicates()

        return df
    except (KeyError, ValueError, AttributeError) as error:
        print(f"Error transforming data: {error}")
        return df
