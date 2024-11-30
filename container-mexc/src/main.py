import time
import requests
import psycopg2
from envs import env

# Helper function to validate boolean values


def to_bool(value):
    """Converts a string to a boolean."""
    if isinstance(value, bool):
        return value
    value = value.lower()
    if value in ["true", "1", "yes", "y", "on"]:
        return True
    elif value in ["false", "0", "no", "n", "off"]:
        return False
    else:
        raise ValueError(f"Invalid boolean value: {value}")


try:
    # Validate LIVE_TRADING
    live_trading = to_bool(env("LIVE_TRADING"))

    # Validate API keys
    api_key = env("API_KEY")
    api_secret = env("API_SECRET")

    # Validate PostgreSQL database settings
    postgres_host = env("POSTGRES_HOST")
    postgres_port = int(env("POSTGRES_PORT"))  # Cast to int
    postgres_name = env("POSTGRES_NAME")
    postgres_user = env("POSTGRES_USER")
    postgres_password = env("POSTGRES_PASSWORD")

except Exception as e:
    print(f"Error: {e}")
    assert False

# MEXC API URL for spot market data
API_URL = "https://api.mexc.com/api/v3/ticker/24hr"


def ensure_table_exists():
    """Ensures the PostgreSQL table exists before storing data."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS spot_market_data (
        symbol TEXT PRIMARY KEY,
        last_price NUMERIC,
        price_change_percent NUMERIC,
        high_price NUMERIC,
        low_price NUMERIC,
        volume NUMERIC,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            database=postgres_name,
            user=postgres_user,
            password=postgres_password
        )
        cursor = conn.cursor()
        # Execute the create table query
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        print("Table checked/created successfully.")
    except psycopg2.Error as e:
        print(f"Database error during table creation: {e}")


def fetch_spot_data():
    """Fetches spot market data from the MEXC API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching spot market data: {e}")
        return None


def store_data_to_db(data):
    """Stores spot market data into the PostgreSQL database."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            database=postgres_name,
            user=postgres_user,
            password=postgres_password
        )
        cursor = conn.cursor()

        # Insert or update the data
        for item in data:
            cursor.execute("""
                INSERT INTO spot_market_data (symbol, last_price, price_change_percent, high_price, low_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE
                SET last_price = EXCLUDED.last_price,
                    price_change_percent = EXCLUDED.price_change_percent,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    volume = EXCLUDED.volume,
                    timestamp = CURRENT_TIMESTAMP;
            """, (
                item["symbol"],
                float(item["lastPrice"]),
                float(item["priceChangePercent"]),
                float(item["highPrice"]),
                float(item["lowPrice"]),
                float(item["volume"])
            ))

        # Commit changes and close the connection
        conn.commit()
        cursor.close()
        conn.close()
        print("Data successfully stored in the database.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    # Ensure the table exists
    ensure_table_exists()
    while True:
        # Fetch data from the API
        spot_data = fetch_spot_data()
        store_data_to_db(spot_data)
        time.sleep(3)
