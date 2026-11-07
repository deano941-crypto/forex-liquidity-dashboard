import pandas as pd

def enrich(df):
    x = df.copy()
    x["ema20"] = x.close.ewm(span=20, adjust=False).mean()
    x["ema50"] = x.close.ewm(span=50, adjust=False).mean()
    delta = x.close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, pd.NA)
    x["rsi"] = 100 - 100/(1+rs)
    prev = x.close.shift(1)
    tr = pd.concat([(x.high-x.low),(x.high-prev).abs(),(x.low-prev).abs()],axis=1).max(axis=1)
    x["atr"] = tr.ewm(alpha=1/14, adjust=False).mean()
    x["range_high"] = x.high.rolling(20).max().shift(1)
    x["range_low"] = x.low.rolling(20).min().shift(1)
    if "volume" not in x: x["volume"] = 0.0
    return x
