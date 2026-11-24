# TSM TRADER 99

A Streamlit-based educational market analysis dashboard for approved/delayed public feeds.

## Run

```bash
python -m pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Open the forwarded port for port `8501` in Codespaces.

## Secrets

Add these in `.streamlit/secrets.toml` locally or in Streamlit Cloud secrets:

```toml
ADMIN_PASSWORD = "replace-this-admin-password"
USER_PASSWORD = "replace-this-user-password"
```

Do not commit real passwords or API keys.

## Features

- EUR/USD, GBP/USD, USD/JPY, gold futures and Bitcoin data through Yahoo Finance
- 1m, 5m, 15m and 1h chart intervals
- EMA20/50, RSI14, MACD and ATR
- Transparent CALL/PUT/WAIT strategy-agreement score
- Bangladesh, UTC and next-minute clocks
- SQLite signal history
- Manual WIN/LOSS result logging

## Disclaimer

No prediction or confidence value shown here is proof of accuracy. No trade is placed automatically. OTC availability, price feeds and broker execution require proper licensing and an authorized API.
