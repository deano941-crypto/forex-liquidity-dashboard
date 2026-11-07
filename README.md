# APEX AI Trading Desk — OANDA Edition

Six-agent Python/Streamlit market intelligence for OANDA gold and Forex. Analysis and signals only; no trade execution.

## Run locally
Python 3.10+:
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, add your own API token, then:
```bash
streamlit run app.py
```
Use `source .venv/bin/activate` on macOS/Linux.

## Credentials
Generate a personal access token in your OANDA account API access settings. Treat it like a password. Never commit `.streamlit/secrets.toml` to GitHub. The app supports `practice` and `live`; start with practice.

OANDA REST v20 documentation: https://developer.oanda.com/rest-live-v20/introduction/
Token help: https://help.oanda.com/us/en/faqs/rest-v20-api-troubleshooting-guide.htm

Your account must support REST v20. Some OANDA divisions/account types are not supported. The app requests midpoint candles from `/v3/instruments/{instrument}/candles` and filters incomplete candles.

## Included instruments
XAU_USD, EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CAD, USD_CHF, NZD_USD, EUR_GBP, EUR_JPY, GBP_JPY.
Timeframes: M1, M2, M5, M15, M30, H1, H4.

## Agent limitations
- Market Scanner: EMA20/EMA50.
- Technical Analyst: RSI and EMA momentum.
- Order Flow Analyst: candle-pressure proxy only. OANDA candle volume is tick count, not consolidated exchange volume, footprint delta, iceberg orders or full order book.
- Institutional Analyst: OHLC prior-range sweep proxy, not institutional positioning.
- Risk Manager: basic input validation, not account-aware position sizing.
- Chief Trading Agent: requires 3-of-4 directional agreement and a passing risk gate.

The scanner runs when the user presses the scan button; this starter is not a permanent background process. ATR levels are illustrative, not guaranteed fills or broker-ready orders. Backtest and paper trade before relying on signals.

## Streamlit Cloud
Push to GitHub, deploy `app.py`, and add `OANDA_API_TOKEN` and `OANDA_ACCOUNT_ID` under App Settings → Secrets. Do not expose your token in code or public repos.
