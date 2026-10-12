
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from twelvedata import TDClient

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

# Connect to Tiger Cloud
conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    sslmode="require",
)

def insert_price(timestamp, symbol, price, day_volume):
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stocks_real_time
                    (time, symbol, price, day_volume)
                VALUES (%s, %s, %s, %s)
                """,
                (timestamp, symbol, price, day_volume),
            )
        conn.commit()
        print(f"Inserted {symbol}: {price} at {timestamp}")
    except Exception as exc:
        conn.rollback()
        print(f"Database insert failed for {symbol}:", exc)


def on_event(event):
    if event.get("event") != "price":
        print("WebSocket:", event)
        return

    timestamp = datetime.fromtimestamp(
        int(event["timestamp"]), tz=timezone.utc
    )
    insert_price(
        timestamp,
        event["symbol"],
        float(event["price"]),
        event.get("day_volume"),
    )

client = TDClient(
    apikey=os.environ["TWELVE_DATA_API_KEY"]
)

symbols = ["AAPL", "MSFT"]
for symbol in symbols:
    try:
        quote = client.quote(symbol=symbol).as_json()
        insert_price(
            datetime.fromtimestamp(int(quote["timestamp"]), tz=timezone.utc),
            symbol,
            float(quote["close"]),
            float(quote["volume"]) if quote.get("volume") else None,
        )
    except Exception as exc:
        print(f"Could not load initial quote for {symbol}:", exc)

ws = client.websocket(on_event=on_event)
ws.subscribe(symbols)
print("Starting financial data pipeline...")
stop_event = threading.Event()

try:
    ws.connect()
    print("Listening for price events. Press Ctrl+C to stop.")
    stop_event.wait()
except KeyboardInterrupt:
    print("Stopping financial data pipeline...")
finally:
    ws.disconnect()
    conn.close()
