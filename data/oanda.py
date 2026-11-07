import requests
import pandas as pd

OANDA_INSTRUMENTS = {
    "XAU_USD":"Gold / US Dollar", "EUR_USD":"Euro / US Dollar",
    "GBP_USD":"British Pound / US Dollar", "USD_JPY":"US Dollar / Japanese Yen",
    "AUD_USD":"Australian Dollar / US Dollar", "USD_CAD":"US Dollar / Canadian Dollar",
    "USD_CHF":"US Dollar / Swiss Franc", "NZD_USD":"New Zealand Dollar / US Dollar",
    "EUR_GBP":"Euro / British Pound", "EUR_JPY":"Euro / Japanese Yen",
    "GBP_JPY":"British Pound / Japanese Yen"
}
BASE_URLS = {
    "practice":"https://api-fxpractice.oanda.com",
    "live":"https://api-fxtrade.oanda.com"
}
GRANULARITIES = {"M1","M2","M5","M15","M30","H1","H4"}

class OandaClient:
    def __init__(self, token, environment="practice", timeout=20):
        if not token:
            raise ValueError("OANDA API token is required.")
        if environment not in BASE_URLS:
            raise ValueError("Environment must be practice or live.")
        self.base_url = BASE_URLS[environment]
        self.session = requests.Session()
        self.session.headers.update({"Authorization":f"Bearer {token}", "Accept":"application/json"})
        self.timeout = timeout

    def get_candles(self, instrument, granularity="M1", count=500):
        if instrument not in OANDA_INSTRUMENTS:
            raise ValueError(f"Unsupported OANDA instrument: {instrument}")
        if granularity not in GRANULARITIES:
            raise ValueError(f"Unsupported granularity: {granularity}")
        url = f"{self.base_url}/v3/instruments/{instrument}/candles"
        response = self.session.get(url, params={
            "granularity":granularity, "count":max(10,min(int(count),5000)),
            "price":"M", "smooth":"false"
        }, timeout=self.timeout)
        if response.status_code == 401:
            raise RuntimeError("OANDA rejected the token (401). Check token and practice/live environment.")
        if response.status_code == 403:
            raise RuntimeError("OANDA denied access (403). Check REST v20 eligibility for your account.")
        response.raise_for_status()
        rows = []
        for candle in response.json().get("candles", []):
            if not candle.get("complete", False):
                continue
            mid = candle.get("mid")
            if mid:
                rows.append({
                    "time":candle["time"], "open":float(mid["o"]),
                    "high":float(mid["h"]), "low":float(mid["l"]),
                    "close":float(mid["c"]), "volume":float(candle.get("volume",0))
                })
        if not rows:
            raise RuntimeError(f"No completed candles returned for {instrument}.")
        df = pd.DataFrame(rows)
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df.attrs["source"] = "OANDA REST v20 completed midpoint candles"
        df.attrs["volume_note"] = "Tick count, not consolidated exchange volume."
        return df.sort_values("time").reset_index(drop=True)

def scan_instruments(client, instruments, granularity="M1", count=300, risk_pct=0.5):
    from agents.engine import run_desk
    output = []
    for instrument in instruments:
        try:
            candles = client.get_candles(instrument, granularity, count)
            result = run_desk(candles, instrument, granularity, risk_pct)
            output.append({
                "Instrument":instrument, "Market":OANDA_INSTRUMENTS[instrument],
                "Decision":result["decision"], "Votes":f'{result["votes"]}/4',
                "Risk":result["risk_status"], "Last close":float(candles.iloc[-1].close),
                "Candle time UTC":str(candles.iloc[-1].time), "Reason":result["summary"]
            })
        except Exception as exc:
            output.append({"Instrument":instrument,"Market":OANDA_INSTRUMENTS.get(instrument,instrument),
                "Decision":"ERROR","Votes":"—","Risk":"—","Last close":None,
                "Candle time UTC":"—","Reason":str(exc)})
    return output
