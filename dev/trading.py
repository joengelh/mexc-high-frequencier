import requests
import time
import hmac
import hashlib
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
    live_trading = to_bool(env("LIVE_TRADING", default="False"))

    # Validate API keys
    api_key = env("API_KEY", required=True)
    api_secret = env("API_SECRET", required=True)

    # Validate PostgreSQL database settings
    postgres_host = env("POSTGRES_HOST", required=True)
    postgres_port = int(env("POSTGRES_PORT", default="5432"))  # Cast to int
    postgres_name = env("POSTGRES_NAME", required=True)
    postgres_user = env("POSTGRES_USER", required=True)
    postgres_password = env("POSTGRES_PASSWORD", required=True)

except Exception as e:
    print(f"Error: {e}")


class MexcSpotTrading:
    def __init__(self, api_key, api_secret):
        self.api_base = "https://api.mexc.com/api/v3"
        self.api_key = api_key
        self.api_secret = api_secret

    def _generate_signature(self, params):
        query_string = '&'.join(
            f"{key}={value}" for key, value in sorted(params.items()))
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _headers(self):
        return {
            "X-MEXC-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }

    def get_spot_market_data(self):
        url = f"{self.api_base}/ticker/24hr"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching market data: {e}")
            return None

    def get_account_balance(self):
        """
        Retrieves account balances for all assets.
        """
        url = f"{self.api_base}/account"
        timestamp = int(time.time() * 1000)
        params = {"timestamp": timestamp}
        params["signature"] = self._generate_signature(params)

        try:
            response = requests.get(
                url, headers=self._headers(), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching account balance: {e}")
            return None

    def calculate_trade_quantity(self, symbol, usdt_allocation):
        """
        Calculates the quantity to trade based on the available USDT.
        :param symbol: The trading pair (e.g., BTCUSDT)
        :param usdt_allocation: Amount of USDT to use for the trade
        """
        market_data = self.get_spot_market_data()
        for data in market_data:
            if data["symbol"] == symbol:
                price = float(data["lastPrice"])
                return usdt_allocation / price
        return None

    def place_order(self, symbol, side, usdt_allocation, price=None, order_type="LIMIT"):
        """
        Places an order using 50% of available USDT.
        :param symbol: Trading pair (e.g., BTCUSDT)
        :param side: "BUY" or "SELL"
        :param usdt_allocation: USDT amount to allocate
        :param price: Price for LIMIT orders; None for MARKET orders
        :param order_type: "LIMIT" or "MARKET"
        """
        quantity = self.calculate_trade_quantity(symbol, usdt_allocation)
        if not quantity:
            print("Error: Unable to calculate trade quantity.")
            return None

        url = f"{self.api_base}/order"
        timestamp = int(time.time() * 1000)
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": round(quantity, 6),
            "timestamp": timestamp
        }
        if order_type == "LIMIT" and price:
            params["price"] = price

        params["signature"] = self._generate_signature(params)

        try:
            response = requests.post(
                url, headers=self._headers(), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error placing order: {e}")
            return None


# Test Suite
if __name__ == "__main__":
    trading_bot = MexcSpotTrading(API_KEY, API_SECRET)

    # Fetch account balance
    account_balance = trading_bot.get_account_balance()
    if account_balance:
        usdt_balance = next(
            (item for item in account_balance["balances"] if item["asset"] == "USDT"), None)
        if usdt_balance:
            available_usdt = float(usdt_balance["free"])
            usdt_to_use = available_usdt * 0.5
            print("Available USDT: " + str(available_usdt) +
                  "Allocating 50%: " + str(usdt_to_use))

            # Place a buy order using 50% of available USDT
            buy_order = trading_bot.place_order(
                symbol="BTCUSDT",
                side="BUY",
                usdt_allocation=usdt_to_use,
                price=30000,  # Example price
                order_type="LIMIT"
            )
            print("Buy Order Response:", buy_order)
        else:
            print("No USDT balance found.")
    else:
        print("Failed to retrieve account balance.")
