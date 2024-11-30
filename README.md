# mexc-high-frequencier

This repository can be used to store price data from mexc to a postgres database

currently used storage:
/dev/sda1 38G 26G 11G 72% /

# read dotenv

export $(cat .env | xargs)

# .env file

LIVE_TRADING=False
API_KEY=
API_SECRET=
POSTGRES_HOST=postgresdb
POSTGRES_PORT=5432
POSTGRES_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
