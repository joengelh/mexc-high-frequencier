import psycopg2
from envs import env


def fetch_data_from_table():
    """Connects to the PostgreSQL database on a remote server and fetches data from a table."""
    # Database connection parameters from environment variables or directly provided
    POSTGRES_HOST = "49.13.162.212"  # Remote PostgreSQL server IP
    POSTGRES_PORT = int(env("POSTGRES_PORT", default="5432"))
    POSTGRES_NAME = env("POSTGRES_NAME")
    POSTGRES_USER = env("POSTGRES_USER")
    POSTGRES_PASSWORD = env("POSTGRES_PASSWORD")
    # Table name to fetch data from
    TABLE_NAME = env("TABLE_NAME", default="spot_market_data")

    try:
        # Establish connection to PostgreSQL database
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_NAME,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()

        # Fetch data from the table
        query = f"SELECT * FROM {TABLE_NAME};"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Display the data
        if rows:
            for row in rows:
                print(row)
        else:
            print(f"No data found in table '{TABLE_NAME}'.")

        # Close the cursor and connection
        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    fetch_data_from_table()
