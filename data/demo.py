import pandas as pd
import numpy as np

def make_demo_data(symbol="XAU_USD", timeframe="M1", count=300):
    rng=np.random.default_rng(42)
    base=2350.0 if symbol=="XAU_USD" else 1.08
    scale=0.8 if symbol=="XAU_USD" else 0.0007
    close=base+np.cumsum(rng.normal(0,scale,count))
    op=np.r_[close[0],close[:-1]]
    wick=np.abs(rng.normal(scale*.5,scale*.25,count))
    minutes={"M1":1,"M2":2,"M5":5,"M15":15,"M30":30,"H1":60,"H4":240}[timeframe]
    times=pd.date_range(end=pd.Timestamp.now(tz="UTC").floor("min"),periods=count,freq=f"{minutes}min")
    return pd.DataFrame({"time":times,"open":op,"high":np.maximum(op,close)+wick,
        "low":np.minimum(op,close)-wick,"close":close,"volume":rng.integers(10,500,count)})
