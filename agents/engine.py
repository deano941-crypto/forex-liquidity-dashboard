from datetime import datetime, timezone
from agents.indicators import enrich

def report(name, stance, finding, evidence):
    return {"name":name,"stance":stance,"finding":finding,"evidence":evidence}

def run_desk(df, symbol="XAU_USD", timeframe="M1", risk_pct=0.5):
    x = enrich(df).dropna(subset=["close","ema20","ema50","atr","range_high","range_low"])
    if len(x) < 25:
        raise ValueError("At least 50 completed candles are recommended.")
    last = x.iloc[-1]
    price, atr = float(last.close), float(last.atr)
    agents = []
    trend = "BUY" if last.ema20 > last.ema50 else "SELL" if last.ema20 < last.ema50 else "WAIT"
    agents.append(report("1 · Market Scanner",trend,f"EMA regime is {trend.lower()}.",f"Close {price:.5f}; EMA20 {last.ema20:.5f}; EMA50 {last.ema50:.5f}; ATR {atr:.5f}."))
    tech = "BUY" if price > last.ema20 and last.rsi >= 52 else "SELL" if price < last.ema20 and last.rsi <= 48 else "WAIT"
    agents.append(report("2 · Technical Analyst",tech,f"Momentum assessment: {tech.lower()}.",f"RSI14 {last.rsi:.1f}; price relative to EMA20."))
    candle_range = max(float(last.high-last.low),1e-12)
    location = (price-float(last.low))/candle_range
    flow = "BUY" if price>last.open and location>0.7 else "SELL" if price<last.open and location<0.3 else "WAIT"
    agents.append(report("3 · Order Flow Analyst",flow,f"Candle-pressure proxy suggests {flow.lower()}.",f"Close location {location:.2f}; OANDA volume is tick count, not exchange footprint/delta/iceberg data."))
    swept_high = float(last.high)>float(last.range_high) and price<float(last.range_high)
    swept_low = float(last.low)<float(last.range_low) and price>float(last.range_low)
    inst = "SELL" if swept_high else "BUY" if swept_low else "WAIT"
    agents.append(report("4 · Institutional Analyst",inst,"Possible prior-range sweep." if inst!="WAIT" else "No prior-range sweep confirmed.",f"Prior range high {last.range_high:.5f}; low {last.range_low:.5f}. OHLC proxy only."))
    risk_ok = atr>0 and 0<risk_pct<=2
    risk = "PASS" if risk_ok else "VETO"
    agents.append(report("5 · Risk Manager","NEUTRAL" if risk_ok else "WAIT","Basic risk validation passed." if risk_ok else "Risk veto.",f"ATR {atr:.5f}; risk reference {risk_pct:.2f}%. Not broker-aware position sizing."))
    votes=[a["stance"] for a in agents[:4]]
    buys,sells=votes.count("BUY"),votes.count("SELL")
    decision="BUY" if risk_ok and buys>=3 and buys>sells else "SELL" if risk_ok and sells>=3 and sells>buys else "WAIT"
    summary=f"{buys} bullish, {sells} bearish and {votes.count('WAIT')} neutral votes. Risk gate: {risk}."
    agents.append(report("6 · Chief Trading Agent",decision,f"Final desk decision: {decision}.",summary))
    levels=None
    if decision in ("BUY","SELL"):
        distance=1.5*atr
        levels={"entry":price,"stop":price-distance if decision=="BUY" else price+distance,
                "tp1":price+distance if decision=="BUY" else price-distance,
                "tp2":price+2*distance if decision=="BUY" else price-2*distance}
    return {"decision":decision,"votes":max(buys,sells),"risk_status":risk,"summary":summary,
            "agents":agents,"levels":levels,"symbol":symbol,"timeframe":timeframe,
            "generated_at":datetime.now(timezone.utc).isoformat()}
