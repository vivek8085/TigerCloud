
# Tiger Cloud Real-Time Financial Data Pipeline

## Overview
A Python data ingestion pipeline that streams financial
price events from Twelve Data into Tiger Cloud (TimescaleDB).

## Technologies
- Python
- Twelve Data WebSocket API
- PostgreSQL
- TimescaleDB hypertable

## Database
The `stocks_real_time` hypertable stores:
- Timestamp
- Stock symbol
- Price
- Daily volume

## Setup
1. Install dependencies from requirements.txt.
2. Configure the required environment variables locally.
3. Create the `stocks_real_time` hypertable in Tiger Cloud.
4. Run `python pipeline.py`.

## Verify data
SELECT time, symbol, price, day_volume
FROM stocks_real_time
ORDER BY time DESC
LIMIT 20;
