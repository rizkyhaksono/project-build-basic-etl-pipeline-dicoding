"""Main ETL pipeline orchestrator for the Fashion Studio scraping project.

Run with: python3 main.py
"""

from utils.extract import scrape_product
from utils.transform import transform_data, transform_to_dataframe
from utils.load import store_to_csv, store_to_google_sheets, store_to_postgresql

# --- Configuration ---
BASE_URL = "https://fashion-studio.dicoding.dev/"
CSV_PATH = "products.csv"

# PostgreSQL connection string. Adjust user/password/host/db to your instance.
DB_URL = "postgresql+psycopg2://root:rootiniboss123@localhost:5432/fashiondb"

# Google Sheets target. Replace with your own spreadsheet ID.
SPREADSHEET_ID = "1n7iP92FaeTwEodt8jFk4oX1KG8ud133vchCx1Y0d0Js"
SHEET_RANGE = "Sheet1!A1"
GOOGLE_CREDS_FILE = "google-sheets-api.json"

EXCHANGE_RATE = 16000


def main():
    """Run the full Extract -> Transform -> Load pipeline."""
    # --- Extract ---
    print("Starting extraction...")
    raw_data = scrape_product(BASE_URL, start_page=1, end_page=50)
    if not raw_data:
        print("No data extracted. Aborting pipeline.")
        return

    # --- Transform ---
    print(f"\nExtracted {len(raw_data)} raw records. Transforming...")
    df = transform_to_dataframe(raw_data)
    df = transform_data(df, exchange_rate=EXCHANGE_RATE)

    if df.empty:
        print("Transformation produced an empty DataFrame. Aborting load.")
        return

    print(f"\nClean dataset: {len(df)} rows")
    print(df.info())

    # --- Load (three repositories) ---
    print("\nLoading data into repositories...")
    store_to_csv(df, CSV_PATH)
    store_to_postgresql(df, DB_URL)
    store_to_google_sheets(df, SPREADSHEET_ID, SHEET_RANGE, GOOGLE_CREDS_FILE)

    print("\nETL pipeline finished.")


if __name__ == "__main__":
    main()
