"""Load stage: persist the cleaned DataFrame to CSV, PostgreSQL, and Google Sheets."""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy import create_engine

GOOGLE_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def store_to_csv(df, path="products.csv"):
    """Save the DataFrame to a CSV file. Returns True on success."""
    try:
        df.to_csv(path, index=False)
        print(f"Data successfully saved to {path}")
        return True
    except (OSError, ValueError) as error:
        print(f"Error saving to CSV: {error}")
        return False


def store_to_postgresql(df, db_url, table_name="fashion_products"):
    """Save the DataFrame to a PostgreSQL table via SQLAlchemy.

    Returns True on success, False on failure.
    """
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            df.to_sql(table_name, con=connection, if_exists="replace", index=False)
        print(f"Data successfully saved to PostgreSQL table '{table_name}'")
        return True
    except Exception as error:  # noqa: BLE001 - surface any DB driver error
        print(f"Error saving to PostgreSQL: {error}")
        return False


def store_to_google_sheets(
    df,
    spreadsheet_id,
    range_name="Sheet1!A1",
    creds_file="google-sheets-api.json",
):
    """Save the DataFrame to a Google Sheet via the Sheets API.

    Returns True on success, False on failure.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            creds_file, scopes=GOOGLE_SHEETS_SCOPES
        )
        service = build("sheets", "v4", credentials=credentials)

        # Header row + data; cast every cell to str so values are JSON-serializable
        # (e.g. the timestamp column and numpy numeric types).
        values = [df.columns.tolist()] + df.astype(str).values.tolist()
        body = {"values": values}

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        print("Data successfully saved to Google Sheets")
        return True
    except Exception as error:  # noqa: BLE001 - surface any API/auth error
        print(f"Error saving to Google Sheets: {error}")
        return False
